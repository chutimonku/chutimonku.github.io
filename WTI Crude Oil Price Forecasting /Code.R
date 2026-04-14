###############################################################################
# WTI Crude Oil Price Forecasting (Replication + Extension)
# FINAL (CONNECTED): uses ONE file_path end-to-end
###############################################################################

# ---------------------------
# 0) Libraries
# ---------------------------
suppressPackageStartupMessages({
  library(readr)
  library(lubridate)
  library(dplyr)
  library(tseries)
  library(forecast)
  library(rugarch)
  library(urca)
})

# =========================
# 0) ใส่พาธไฟล์
# =========================
file_path <- "Desktop/Student Now/ปี 3 เทอม 2/statcom/โปรเจคปลายภาค/DCOILWTICO.csv"
if (!file.exists(file_path)) {
  stop(paste0("ไม่พบไฟล์ที่พาธนี้: ", file_path,
              "\nตรวจสอบพาธให้ถูกต้อง หรือใช้ normalizePath() ช่วยได้"))
}

# =========================
# 1) LOAD RAW (อ่านจาก file_path เท่านั้น)
# =========================
raw <- read_csv(file_path, show_col_types = FALSE)

cat("=== RAW DATA ===\n")
cat("Rows (raw): ", nrow(raw), "\n")
cat("Cols (raw): ", ncol(raw), "\n")
cat("\nColumn names:\n")
print(names(raw))

# กันเคสชื่อคอลัมน์ผิด/สะกดไม่ตรง
required_cols <- c("observation_date", "DCOILWTICO")
missing_cols <- setdiff(required_cols, names(raw))
if (length(missing_cols) > 0) {
  stop(paste0("คอลัมน์ไม่ครบ/ชื่อไม่ตรง: ", paste(missing_cols, collapse = ", "),
              "\nกรุณาเช็คชื่อคอลัมน์จากที่ print(names(raw)) แล้วแก้ให้ตรง"))
}

# =========================
# 2) PARSE DATE + CHECK NA
# =========================
raw <- raw %>%
  mutate(
    observation_date = parse_date_time(observation_date, orders = c("ymd", "mdy", "dmy")),
    observation_date = as.Date(observation_date)
  )

na_count <- sum(is.na(raw$DCOILWTICO))

cat("\n=== NA SUMMARY ===\n")
cat("NA in DCOILWTICO: ", na_count, "\n")

# =========================
# 3) CLEAN (ลบแถวที่ราคาเป็น NA)
# =========================
clean <- raw %>% filter(!is.na(DCOILWTICO))

cat("\n=== CLEAN DATA ===\n")
cat("Rows (clean): ", nrow(clean), "\n")
cat("Cols (clean): ", ncol(clean), "\n")
cat("Removed rows: ", nrow(raw) - nrow(clean), "\n")

# =========================
# 4) DATE RANGE + UNIQUE DAYS
# =========================
cat("\n=== DATE RANGE ===\n")
cat("Raw  : ", format(min(raw$observation_date, na.rm=TRUE), "%Y-%m-%d"),
    " to ", format(max(raw$observation_date, na.rm=TRUE), "%Y-%m-%d"), "\n")

cat("Clean: ", format(min(clean$observation_date, na.rm=TRUE), "%Y-%m-%d"),
    " to ", format(max(clean$observation_date, na.rm=TRUE), "%Y-%m-%d"), "\n")

cat("\n=== UNIQUE DAYS ===\n")
cat("Unique days (raw)  : ", n_distinct(raw$observation_date), "\n")
cat("Unique days (clean): ", n_distinct(clean$observation_date), "\n")

# =========================
# 5) OPTIONAL: เช็ค “เดือนหาย” / เดือนที่ทั้งเดือนเป็น NA
# =========================
raw_monthly_check <- raw %>%
  mutate(YearMonth = floor_date(observation_date, "month")) %>%
  group_by(YearMonth) %>%
  summarise(
    n_days_total = n(),
    n_days_na    = sum(is.na(DCOILWTICO)),
    n_days_ok    = sum(!is.na(DCOILWTICO)),
    .groups = "drop"
  )

clean_monthly_check <- clean %>%
  mutate(YearMonth = floor_date(observation_date, "month")) %>%
  group_by(YearMonth) %>%
  summarise(n_days_ok = n(), .groups = "drop")

cat("\n=== MONTHLY COUNTS (CHECK) ===\n")
cat("Months (raw monthly)  : ", nrow(raw_monthly_check), "\n")
cat("Months (clean monthly): ", nrow(clean_monthly_check), "\n")

all_na_months <- raw_monthly_check %>% filter(n_days_ok == 0)
cat("\n=== MONTHS WITH ALL NA (ถ้ามี เดือนจะหายหลัง clean) ===\n")
print(all_na_months)

# ---------------------------
# Helper: metrics
# ---------------------------
calc_metrics <- function(actual, forecast){
  e <- as.numeric(actual) - as.numeric(forecast)
  mse  <- mean(e^2, na.rm = TRUE)
  mae  <- mean(abs(e), na.rm = TRUE)
  rmse <- sqrt(mse)
  mape <- mean(abs(e / as.numeric(actual)), na.rm = TRUE) * 100
  c(MSE=mse, MAE=mae, RMSE=rmse, MAPE=mape)
}

# ---------------------------
# Helper: labels YYYY/MM from last observed month
# ---------------------------
make_ym_labels <- function(last_date, h){
  f_dates <- seq(from = last_date %m+% months(1), by = "1 month", length.out = h)
  format(f_dates, "%Y/%m")
}

# ---------------------------
# Helper: build ARIMA forecast table (with intervals)
# ---------------------------
build_arima_table <- function(fit, last_obs_ym, h, levels=c(80,95)){
  fc <- forecast(fit, h = h, level = levels)
  time_lab <- make_ym_labels(last_obs_ym, h)
  
  out <- data.frame(
    Time     = time_lab,
    forecast = round(as.numeric(fc$mean), 3)
  )
  
  if ("80%" %in% colnames(fc$lower)){
    out$L80 <- round(as.numeric(fc$lower[, "80%"]), 3)
    out$H80 <- round(as.numeric(fc$upper[, "80%"]), 3)
  }
  if ("95%" %in% colnames(fc$lower)){
    out$L95 <- round(as.numeric(fc$lower[, "95%"]), 3)
    out$H95 <- round(as.numeric(fc$upper[, "95%"]), 3)
  }
  out
}

# ---------------------------
# Helper: GARCH level forecast table (Point + Sigma of diff)
# ---------------------------
build_garch_table <- function(fit_garch, last_level, last_obs_ym, h){
  fc <- ugarchforecast(fit_garch, n.ahead = h)
  pred_diff <- as.numeric(fitted(fc))
  sig_diff  <- as.numeric(sigma(fc))
  
  pred_level <- last_level + cumsum(pred_diff)
  time_lab <- make_ym_labels(last_obs_ym, h)
  
  data.frame(
    Time  = time_lab,
    Point = round(pred_level, 3),
    Sigma = round(sig_diff, 3)
  )
}

# =========================
# 6) DAILY -> MONTHLY AVERAGE (ใช้ clean ต่อเลย)
# =========================
oil_monthly <- clean %>%
  mutate(YearMonth = floor_date(observation_date, "month")) %>%
  group_by(YearMonth) %>%
  summarise(Price = mean(DCOILWTICO), .groups = "drop")

cat("\n=== MONTHLY SERIES ===\n")
cat("Months (final monthly): ", nrow(oil_monthly), "\n")
cat("Monthly date range: ",
    format(min(oil_monthly$YearMonth), "%Y-%m"),
    " to ",
    format(max(oil_monthly$YearMonth), "%Y-%m"), "\n")
# monthly ts (กำหนด start จากข้อมูลจริง)
start_year  <- year(min(oil_monthly$YearMonth))
start_month <- month(min(oil_monthly$YearMonth))
oil_ts <- ts(oil_monthly$Price, start = c(start_year, start_month), frequency = 12)

plot(oil_ts, main = "WTI crude oil price (Monthly Average)", xlab = "Time", ylab = "WTI price")
abline(v = 2023, lty = 2)

# =========================
# 7) Train/Test split (ยึดตามงานเดิมของคุณ)
# =========================
train <- window(oil_ts, end = c(2022, 12))
test  <- window(oil_ts, start = c(2023, 1), end = c(2024, 4))

acf(train, lag.max = 30, main = "ACF plot of original sequence")

# =========================
# 8) Stationarity checks (ADF) + differencing
# =========================
cat("\n=== ADF test (tseries::adf.test) ===\n")
print(adf.test(train))
diff_train <- diff(train)
print(adf.test(diff_train))

# ADF table like paper using urca
lags <- 1
x <- as.numeric(train)

adf_trend <- ur.df(x, type = "trend", lags = lags)
adf_drift <- ur.df(x, type = "drift", lags = lags)
adf_none  <- ur.df(x, type = "none",  lags = lags)

get_tau <- function(obj){
  ts <- obj@teststat
  if ("tau3" %in% names(ts)) return(unname(ts["tau3"]))
  if ("tau2" %in% names(ts)) return(unname(ts["tau2"]))
  if ("tau1" %in% names(ts)) return(unname(ts["tau1"]))
  unname(ts[1])
}

table_adf <- data.frame(
  Type         = c("Intercept + time trend", "Intercept only", "No intercept and trend"),
  Dickey_Fuller= round(c(get_tau(adf_trend), get_tau(adf_drift), get_tau(adf_none)), 3),
  Lag_order    = c(lags, lags, lags)
)
cat("\n=== Table: ADF test (urca::ur.df) ===\n")
print(table_adf)

plot(diff_train, main = "First-order differenced series", xlab = "Time", ylab = "diff(price)")
abline(h = 0, lty = 2)

par(mfrow = c(1, 2))
acf(diff_train, lag.max = 30, main = "ACF (diff)")
pacf(diff_train, lag.max = 30, main = "PACF (diff)")
par(mfrow = c(1, 1))

# =========================
# 9) Replication: ARIMA candidates + AIC table
# =========================
m011 <- Arima(train, order = c(0, 1, 1), method = "ML")
m110 <- Arima(train, order = c(1, 1, 0), method = "ML")
m016 <- Arima(train, order = c(0, 1, 6), method = "ML")
m610 <- Arima(train, order = c(6, 1, 0), method = "ML")
m611 <- Arima(train, order = c(6, 1, 1), method = "ML")
m111 <- Arima(train, order = c(1, 1, 1), method = "ML")

table_aic <- data.frame(
  ARIMA_Model = c("(0,1,1)", "(0,1,6)", "(1,1,0)", "(6,1,0)", "(6,1,1)", "(1,1,1)"),
  AIC = round(c(AIC(m011), AIC(m016), AIC(m110), AIC(m610), AIC(m611), AIC(m111)), 3)
)
cat("\n=== Table: Model determination (paper ARIMA candidates) ===\n")
print(table_aic)

# =========================
# 10) Holdout multi-step evaluation
# =========================
fit_110 <- Arima(train, order = c(1,1,0), method = "ML")
fc_110  <- forecast(fit_110, h = length(test))
met_110 <- calc_metrics(test, fc_110$mean)

fit_610 <- Arima(train, order = c(6,1,0), method = "ML")
fc_610  <- forecast(fit_610, h = length(test))
met_610 <- calc_metrics(test, fc_610$mean)

cat("\n=== HOLDOUT multi-step metrics ===\n")
cat("[ARIMA(1,1,0)]\n"); print(met_110)
cat("[ARIMA(6,1,0)]\n"); print(met_610)

plot(fc_110, main = "Holdout multi-step Forecast vs Actual (ARIMA(1,1,0))",
     xlab = "Time", ylab = "WTI price")
lines(test, col = "red")
legend("topleft", legend=c("Forecast","Actual"),
       lty=c(1,1), col=c("blue","red"), bty="n")

# =========================
# 11) Diagnostics + Shapiro-Wilk table
# =========================
res_110 <- residuals(m110)
res_610 <- residuals(m610)

sw_110 <- shapiro.test(as.numeric(res_110))
sw_610 <- shapiro.test(as.numeric(res_610))

table_shapiro <- data.frame(
  Model   = c("ARIMA(1,1,0)", "ARIMA(6,1,0)"),
  W       = round(c(unname(sw_110$statistic), unname(sw_610$statistic)), 4),
  p_value = format(c(sw_110$p.value, sw_610$p.value), scientific = TRUE, digits = 3)
)
cat("\n=== Table: Shapiro-Wilk test ===\n")
print(table_shapiro)

par(mfrow = c(2, 2))
plot(res_110, main = "ARIMA(1,1,0) Residuals", xlab = "Time", ylab = "Residual")
acf(res_110, lag.max = 30, main = "ACF (Residuals)")
pacf(res_110, lag.max = 30, main = "PACF (Residuals)")
qqnorm(res_110, main = "Q-Q plot"); qqline(res_110)
par(mfrow = c(1, 1))

par(mfrow = c(2, 2))
plot(res_610, main = "ARIMA(6,1,0) Residuals", xlab = "Time", ylab = "Residual")
acf(res_610, lag.max = 30, main = "ACF (Residuals)")
pacf(res_610, lag.max = 30, main = "PACF (Residuals)")
qqnorm(res_610, main = "Q-Q plot"); qqline(res_610)
par(mfrow = c(1, 1))

# =========================
# 12) diff^2 and residual^2
# =========================
diff_sq <- as.numeric(diff_train)^2
res_sq  <- as.numeric(res_110)^2

par(mfrow = c(1, 2))
acf(diff_sq, lag.max = 30, main = "ACF (diff^2)")
pacf(diff_sq, lag.max = 30, main = "PACF (diff^2)")
par(mfrow = c(1, 1))

par(mfrow = c(1, 2))
acf(res_sq, lag.max = 30, main = "ACF (ARIMA residual^2)")
pacf(res_sq, lag.max = 30, main = "PACF (ARIMA residual^2)")
par(mfrow = c(1, 1))

# =========================
# 13) Ljung-Box p-values across lags
# =========================
k <- length(coef(m110))
pvals <- sapply(1:30, function(L){
  Box.test(res_110, lag = L, type = "Ljung-Box", fitdf = k)$p.value
})

plot(1:30, pvals, type = "b", pch = 1,
     main = "WTI crude oil price (Ljung-Box p-values)",
     xlab = "Lag", ylab = "P-value")
abline(h = 0.05, lty = 2, col = "red")

# =========================
# 14) Future forecast ARIMA(1,1,0) h=3 and h=6
# =========================
oil_until_2024_04 <- window(oil_ts, end = c(2024, 4))
fit_full_arima_110 <- Arima(oil_until_2024_04, order = c(1,1,0), method="ML")

last_obs_ym <- as.Date(sprintf("%d-%02d-01",
                               end(oil_until_2024_04)[1],
                               end(oil_until_2024_04)[2]))

table_arima_forecast_3m <- build_arima_table(fit_full_arima_110, last_obs_ym, h=3, levels=c(80,95))
cat("\n=== Table: Forecasts from ARIMA(1,1,0) (h=3) ===\n")
print(table_arima_forecast_3m)

plot(forecast(fit_full_arima_110, h=3, level=c(80,95)),
     main = "3-month Forecast (ARIMA(1,1,0))",
     xlab = "Time", ylab = "WTI price")

table_arima_forecast_6m <- build_arima_table(fit_full_arima_110, last_obs_ym, h=6, levels=c(80,95))
cat("\n=== Table: Forecasts from ARIMA(1,1,0) (h=6) ===\n")
print(table_arima_forecast_6m)

plot(forecast(fit_full_arima_110, h=6, level=c(80,95)),
     main = "6-month Forecast (ARIMA(1,1,0))",
     xlab = "Time", ylab = "WTI price")

# =========================
# 15) ARIMA-GARCH (train diffs -> forecast test)
# =========================
spec_A <- ugarchspec(
  variance.model = list(model = "sGARCH", garchOrder = c(1, 1)),
  mean.model     = list(armaOrder = c(1, 0), include.mean = TRUE),
  distribution.model = "norm"
)

dy_train <- diff(as.numeric(train))
fit_garch_train <- ugarchfit(spec_A, data = dy_train, solver = "hybrid")

coef_garch_train <- coef(fit_garch_train)
alpha1 <- unname(coef_garch_train["alpha1"])
beta1  <- unname(coef_garch_train["beta1"])
persistence <- alpha1 + beta1

table_persistence <- data.frame(
  alpha1 = round(alpha1, 6),
  beta1  = round(beta1, 6),
  alpha_plus_beta = round(persistence, 6)
)
cat("\n=== Table: Volatility persistence (TRAIN) ===\n")
print(table_persistence)

h_test <- length(test)
fc_garch_test <- ugarchforecast(fit_garch_train, n.ahead = h_test)
pred_diff_test <- as.numeric(fitted(fc_garch_test))

last_level_train <- as.numeric(tail(train, 1))
pred_level_test <- last_level_train + cumsum(pred_diff_test)

met_garch_holdout <- calc_metrics(test, pred_level_test)
cat("\n=== HOLDOUT multi-step metrics: ARMA(1,0)-GARCH(1,1) on diff(train) ===\n")
print(met_garch_holdout)

pred_level_test_ts <- ts(pred_level_test, start = start(test), frequency = frequency(test))
plot(test, type="l", lwd=2,
     main="Holdout multi-step: Actual vs ARMA(1,0)-GARCH(1,1) (diff-series)",
     xlab="Time", ylab="WTI price")
lines(pred_level_test_ts, lty=2, lwd=2)
legend("topleft", legend=c("Actual","GARCH forecast"),
       lty=c(1,2), lwd=2, bty="n")

# =========================
# 16) Future forecast with GARCH (fit diffs up to 2024-04)
# =========================
dy_full <- diff(as.numeric(oil_until_2024_04))
fit_garch_full <- ugarchfit(spec_A, data = dy_full, solver = "hybrid")

last_level_full <- as.numeric(tail(oil_until_2024_04, 1))

table_garch_forecast_3m <- build_garch_table(fit_garch_full, last_level_full, last_obs_ym, h=3)
cat("\n=== Table: Forecasts from ARIMA(1,1,0)-GARCH(1,1) (h=3) ===\n")
print(table_garch_forecast_3m)

table_garch_forecast_6m <- build_garch_table(fit_garch_full, last_level_full, last_obs_ym, h=6)
cat("\n=== Table: Forecasts from ARIMA(1,1,0)-GARCH(1,1) (h=6) ===\n")
print(table_garch_forecast_6m)

pred_garch_6m <- table_garch_forecast_6m$Point
pred_garch_6m_ts <- ts(pred_garch_6m, start = c(2024, 5), frequency = 12)

plot(oil_until_2024_04, type = "l", lwd = 2,
     main = "6-month Forecast (ARMA(1,0)-GARCH(1,1) on diff-series)",
     xlab = "Time", ylab = "WTI price")
lines(pred_garch_6m_ts, lty = 2, lwd = 2)
legend("topleft",
       legend = c("Actual (until 2024-04)", "Forecast (6 months)"),
       lty = c(1, 2), lwd = 2, bty = "n")

# =========================
# 17) Naive benchmark (Random Walk) holdout multi-step
# =========================
naive_pred <- rep(as.numeric(tail(train, 1)), length(test))
met_naive_holdout <- calc_metrics(test, naive_pred)

cat("\n=== HOLDOUT multi-step metrics: Naive (Random Walk) ===\n")
print(met_naive_holdout)

# =========================
# 18) ARIMA search p,q in [0,8] by AIC (on TRAIN)
# =========================
best_aic <- Inf
best_fit <- NULL
best_order <- c(NA, 1, NA)

for(p in 0:8){
  for(q in 0:8){
    fit <- try(Arima(train, order = c(p, 1, q), method = "ML"), silent = TRUE)
    if(!inherits(fit, "try-error")){
      a <- AIC(fit)
      if(a < best_aic){
        best_aic <- a
        best_fit <- fit
        best_order <- c(p, 1, q)
      }
    }
  }
}

cat("\n=== Best extended ARIMA order by AIC (TRAIN) ===\n")
print(best_order)
cat("Best AIC:", best_aic, "\n")

fc_ext <- forecast(best_fit, h = length(test))
met_ext_holdout <- calc_metrics(test, fc_ext$mean)

cat("\n=== HOLDOUT multi-step metrics: Extended ARIMA(best AIC) ===\n")
print(met_ext_holdout)

plot(fc_ext,
     main = paste0("Holdout multi-step Forecast vs Actual (ARIMA(", paste(best_order, collapse=","), "))"),
     xlab = "Time", ylab = "WTI price")
lines(test, col = "red")

# =========================
# 19) Comparison Plot
# =========================
pred_arima110_ts <- ts(as.numeric(fc_110$mean), start = start(test), frequency = frequency(test))
pred_garch_ts    <- ts(as.numeric(pred_level_test), start = start(test), frequency = frequency(test))
pred_naive_ts    <- ts(as.numeric(naive_pred), start = start(test), frequency = frequency(test))
pred_arima_ext_ts<- ts(as.numeric(fc_ext$mean), start = start(test), frequency = frequency(test))

plot(test, type="l", lwd=2,
     main = paste0("Holdout Multi-step Forecast Comparison (", start(test)[1], "-", end(test)[1], ")"),
     xlab="Time", ylab="WTI price")

lines(pred_naive_ts,     lty=2, lwd=2)
lines(pred_arima110_ts,  lty=3, lwd=2)
lines(pred_garch_ts,     lty=4, lwd=2)
lines(pred_arima_ext_ts, lty=5, lwd=2)

legend("topleft",
       legend = c("Actual",
                  "Naive (RW)",
                  "ARIMA(1,1,0)",
                  "ARMA(1,0)-GARCH(1,1)",
                  paste0("ARIMA(", paste(best_order, collapse=","), ")")),
       lty = c(1,2,3,4,5),
       lwd = c(2,2,2,2,2),
       bty = "n")

# =========================
# 20) Rolling-origin CV (RMSE at horizon 3 and 6)
# =========================
fcast_fun <- function(y, h){
  fit <- try(Arima(y, order = best_order, method = "ML"), silent = TRUE)
  if(inherits(fit, "try-error")){
    pred <- rep(NA_real_, h)
  } else {
    pred <- as.numeric(forecast(fit, h = h)$mean)
  }
  structure(list(mean = pred), class = "forecast")
}

e3 <- forecast::tsCV(train, forecastfunction = fcast_fun, h = 3)
e6 <- forecast::tsCV(train, forecastfunction = fcast_fun, h = 6)

RMSE_cv_3 <- sqrt(mean(e3[,3]^2, na.rm = TRUE))
RMSE_cv_6 <- sqrt(mean(e6[,6]^2, na.rm = TRUE))

cat("\n=== Rolling-origin CV (RMSE at horizon) ===\n")
print(c(RMSE_3m = RMSE_cv_3, RMSE_6m = RMSE_cv_6))

# =========================
# 21) Summary tables
# =========================
table_holdout_compare <- data.frame(
  Model = c("ARIMA(1,1,0) holdout multi-step",
            "ARIMA(6,1,0) holdout multi-step",
            "ARMA(1,0)-GARCH(1,1) on diff(train) holdout multi-step",
            "Naive (Random Walk) holdout multi-step",
            paste0("ARIMA(", paste(best_order, collapse=","), ") holdout multi-step (AIC-best)")
  ),
  rbind(met_110, met_610, met_garch_holdout, met_naive_holdout, met_ext_holdout)
)
cat("\n=== Table: Holdout multi-step comparison (MAIN replication + extensions) ===\n")
print(table_holdout_compare)

table_cv <- data.frame(
  Setting = c("Rolling-origin CV (best ARIMA)"),
  RMSE_3m = RMSE_cv_3,
  RMSE_6m = RMSE_cv_6
)
cat("\n=== Table: Rolling-origin CV summary ===\n")
print(table_cv)

cat("\n=== DONE ===\n")

