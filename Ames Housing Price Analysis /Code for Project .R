# =========================================================
# Ames Housing Regression Project (OLS + Ridge ONLY)
# - ทำความสะอาดข้อมูล (จัดการ NA)
# - แบ่งข้อมูล Train/Test (70/30)
# - OLS baseline (โมเดลดั้งเดิม)
# - Ridge Regression (glmnet) + 10-fold CV เพื่อหา lambda
# - วัดผล: MSE, RMSE, MAE, R² (ทดสอบบน TEST set)
# - กราฟสำหรับเปเปอร์: CV curve + Predicted vs Actual + OLS diagnostics
# =========================================================

# ------------------------------
# ติดตั้งแพ็กเกจ (รันครั้งเดียว)
# ------------------------------
# install.packages(c("tidyverse", "glmnet"))

# ------------------------------
# โหลดไลบรารี + ล้าง environment
# ------------------------------
rm(list = ls())
library(tidyverse)
library(glmnet)

# ------------------------------
# 1) โหลดข้อมูล Ames
#    - เลือกไฟล์ CSV ของ Ames ที่คุณใช้จริง
#    - ลบคอลัมน์ ID ที่ไม่ช่วยทำนายราคา (ถ้ามี)
# ------------------------------
ames <- read.csv(file.choose())

if ("Order" %in% names(ames)) ames <- ames %>% select(-Order)
if ("PID"   %in% names(ames)) ames <- ames %>% select(-PID)

# ทำให้ชื่อ target เหมือนกัน: SalePrice -> price
if ("SalePrice" %in% names(ames) && !"price" %in% names(ames)) {
  ames <- ames %>% rename(price = SalePrice)
}
stopifnot("price" %in% names(ames))

# ------------------------------
# 2) จัดการ Missing Values (NA)
#    - ตัวแปรแบบ character/factor: NA -> "None"
#    - ตัวแปรแบบ numeric: NA -> median (กัน outlier กระทบมาก)
# ------------------------------
ames <- ames %>%
  mutate(across(where(is.character), ~replace_na(., "None"))) %>%
  mutate(across(where(is.factor),    ~fct_explicit_na(., na_level = "None"))) %>%
  mutate(across(where(is.numeric),   ~ifelse(is.na(.), median(., na.rm = TRUE), .)))

# ------------------------------
# 3) เตรียม X, y สำหรับ glmnet
#    - model.matrix จะทำ dummy variables ให้อัตโนมัติ
#    - ตัด intercept ออก เพราะ glmnet มี intercept ของมันเอง
# ------------------------------
y <- ames$price
x <- model.matrix(price ~ ., data = ames)[, -1]

# ------------------------------
# 4) แบ่ง Train/Test = 70/30 (ให้ทำซ้ำได้เหมือนเดิม)
# ------------------------------
set.seed(123)
n <- nrow(x)
train_id <- sample(seq_len(n), size = floor(0.7 * n))

x_train <- x[train_id, , drop = FALSE]
x_test  <- x[-train_id, , drop = FALSE]
y_train <- y[train_id]
y_test  <- y[-train_id]

ames_train <- ames[train_id, ]
ames_test  <- ames[-train_id, ]

# ------------------------------
# 5) OLS baseline (โมเดลดั้งเดิม)
#    หมายเหตุ: ชื่อคอลัมน์ในไฟล์ Ames บางไฟล์ไม่เหมือนกัน
#    เลยทำตัวช่วยเลือกชื่อที่ "มีอยู่จริง" ในไฟล์ของคุณ
# ------------------------------
pick_first <- function(candidates, cols) {
  hit <- candidates[candidates %in% cols]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
}

cols <- names(ames_train)

# ตัวแปรที่นิยมใช้ใน Ames (เลือกชื่อที่มีอยู่จริง)
v_area  <- pick_first(c("Gr.Liv.Area", "area", "GrLivArea"), cols)
v_qual  <- pick_first(c("Overall.Qual", "OverallQual"), cols)
v_year  <- pick_first(c("Year.Built", "YearBuilt"), cols)
v_bsmt  <- pick_first(c("Total.Bsmt.SF", "TotalBsmtSF"), cols)
v_gar   <- pick_first(c("Garage.Cars", "GarageCars"), cols)
v_nei   <- pick_first(c("Neighborhood"), cols)

# เช็คว่าหาตัวแปรหลักเจอไหม
needed <- c(v_area, v_qual, v_year, v_bsmt, v_gar, v_nei)
if (any(is.na(needed))) {
  stop(
    "หา column สำหรับ OLS ไม่ครบในไฟล์นี้\n",
    "ลองเช็คชื่อคอลัมน์ใน data ของคุณว่าใช้ชื่อไหน เช่น Gr.Liv.Area/Overall.Qual/...\n",
    "หรือส่งชื่อคอลัมน์มา เดี๋ยวผมปรับสูตรให้ตรงกับไฟล์คุณ"
  )
}

ols_formula <- as.formula(
  paste0("price ~ ", paste(needed, collapse = " + "))
)

m_ols_train <- lm(ols_formula, data = ames_train)
ols_pred <- as.numeric(predict(m_ols_train, newdata = ames_test))

# ------------------------------
# 6) Ridge Regression + 10-fold CV
#    - alpha = 0 คือ Ridge
#    - type.measure = "mse" (ตามงานเปเปอร์ที่รายงาน error metrics)
#    - เลือก lambda ที่ดีที่สุดด้วย lambda.min
# ------------------------------
set.seed(123)
cv_ridge <- cv.glmnet(
  x_train, y_train,
  alpha = 0,
  type.measure = "mse",
  nfolds = 10,
  standardize = TRUE
)

ridge_pred <- as.numeric(predict(cv_ridge, s = "lambda.min", newx = x_test))

# แสดงค่า lambda ที่สำคัญ (ใช้เขียนอธิบายในเปเปอร์ได้)
cat("\n===== Ridge lambda from CV =====\n")
cat("lambda.min =", cv_ridge$lambda.min, "\n")
cat("lambda.1se =", cv_ridge$lambda.1se, "\n")
cat("log(lambda.min) =", log(cv_ridge$lambda.min), "\n")
cat("log(lambda.1se) =", log(cv_ridge$lambda.1se), "\n")

# ------------------------------
# 7) ฟังก์ชันวัดผล (Metrics)
#    - วัดบน TEST set เพื่อเทียบกันแบบยุติธรรม
# ------------------------------
reg_metrics <- function(y_true, y_pred) {
  y_pred <- as.numeric(y_pred)
  mse <- mean((y_true - y_pred)^2)
  c(
    MSE  = mse,
    RMSE = sqrt(mse),
    MAE  = mean(abs(y_true - y_pred)),
    R2   = 1 - sum((y_true - y_pred)^2) / sum((y_true - mean(y_true))^2)
  )
}

ols_metrics   <- reg_metrics(y_test, ols_pred)
ridge_metrics <- reg_metrics(y_test, ridge_pred)

results <- rbind(
  OLS_Baseline = ols_metrics,
  Ridge_CV     = ridge_metrics
)

cat("\n===== Test-set Performance (70/30 split) =====\n")
print(round(results, 2))

# ------------------------------
# 8) กราฟ CV Curve (Ridge) แบบอ่านง่าย (ไม่ทับกัน)
#    อธิบาย: แกน X = log(lambda), แกน Y = CV MSE
#    เส้นตั้ง: lambda.min และ lambda.1se
# ------------------------------
plot_cv_clean <- function(cv, title) {
  
  loglam <- log(cv$lambda)
  mse    <- cv$cvm
  se     <- cv$cvsd
  
  plot(
    loglam, mse,
    type = "b",
    pch  = 16,
    col  = "#D7191C",
    ylim = range(mse + se, mse - se),
    xlab = "log(λ)",
    ylab = "Cross-Validated MSE",
    main = "",
    cex  = 0.6,
    cex.axis = 0.8,
    cex.lab  = 0.9
  )
  
  arrows(
    loglam, mse - se,
    loglam, mse + se,
    length = 0.02,
    angle  = 90,
    code   = 3,
    col    = "gray60"
  )
  
  abline(v = log(cv$lambda.min), lty = 2, col = "blue",  lwd = 2)
  abline(v = log(cv$lambda.1se), lty = 3, col = "gray40", lwd = 2)
  
  # ยก title ให้ห่างจากกราฟ
  title(main = title, line = 2, cex.main = 1.0, font.main = 2)
}

par(mfrow = c(1, 1), mar = c(5, 5, 5, 1))
plot_cv_clean(cv_ridge, "Ridge Regression\n10-fold Cross-Validation")

# ------------------------------
# 9) OLS diagnostic plots (ไว้ตรวจสมมติฐานของ OLS)
#    - ใช้เพื่ออธิบายในเปเปอร์ว่า OLS อาจมีปัญหา เช่น heteroscedasticity/outliers
# ------------------------------
par(mfrow = c(2, 2), mar = c(4, 4, 3, 1))
plot(m_ols_train, cex.axis = 0.8, cex.lab = 0.9, cex.main = 0.9)
par(mfrow = c(1, 1))

# ------------------------------
# 10) Predicted vs Actual (Ridge) สำหรับใส่เปเปอร์
#     - จุดควรเกาะใกล้เส้น y=x แปลว่าโมเดลทายใกล้ค่าจริง
# ------------------------------
pred_df <- data.frame(
  Actual = y_test,
  Pred_Ridge = ridge_pred
)

ggplot(pred_df, aes(x = Actual, y = Pred_Ridge)) +
  geom_point(alpha = 0.35, color = "#2C7BB6", size = 1.8) +
  geom_abline(slope = 1, intercept = 0,
              linetype = "dashed", color = "red", linewidth = 1) +
  labs(
    title = "Predicted vs Actual Housing Prices (Ridge Regression)",
    subtitle = "Test set (70/30 split)",
    x = "Actual Sale Price (USD)",
    y = "Predicted Sale Price (USD)"
  ) +
  theme_minimal(base_size = 15) +
  theme(
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(size = 10),
    axis.text = element_text(size = 11)
  )

