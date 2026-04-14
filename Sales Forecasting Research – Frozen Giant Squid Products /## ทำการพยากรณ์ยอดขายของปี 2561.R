##พยากรณ์ปี 2561
# ข้อมูลยอดขายรายเดือน (ปี 2557–2560)
sales <- c(
  110.5, 70.3, 95.3, 120.6, 90.5, 75.5, 69.6, 77.2, 99.5, 82.1, 101.2, 103.5, # ปี 2557
  153.9, 89.1, 121, 148.8, 100.1, 95.5, 93.4, 88.9, 120.3, 92.2, 132.4, 121.3, # ปี 2558
  152, 91.9, 111.2, 149.9, 99, 83.3, 109.1, 87.7, 104.1, 75.7, 123.3, 159.5,   # ปี 2559
  141.5, 93.6, 112.1, 152.3, 98.9, 85.5, 110.5, 88.2, 103.5, 76.5, 122.4, 162.2 # ปี 2560
)

# น้ำหนักสำหรับ Weighted Moving Average
weights <- c(0.82, 0.00, 0.00, 0.00, 0.04, 0.00, 0.00, 0.00, 0.00, 0.09, 0.00, 0.05)

# ติดตั้งและโหลดแพ็กเกจที่จำเป็น
if (!require(ggplot2)) install.packages("ggplot2")
if (!require(lubridate)) install.packages("lubridate")
library(ggplot2)
library(lubridate)

# ฟังก์ชัน Weighted Moving Average (WMA)
WMA_forecast <- function(data, weights, forecast_months) {
  n <- length(weights)
  forecast <- numeric(forecast_months)
  full_data <- data
  
  for (i in 1:forecast_months) {
    if (length(full_data) >= n) {
      forecast[i] <- sum(weights * tail(full_data, n))
    } else {
      stop("ข้อมูลไม่เพียงพอสำหรับพยากรณ์")
    }
    full_data <- c(full_data, forecast[i])
  }
  
  return(forecast)
}

# พยากรณ์ข้อมูล 7 เดือนแรกและ 12 เดือน
forecast_2561_7 <- WMA_forecast(sales, weights, forecast_months = 7)
forecast_2561_12 <- WMA_forecast(sales, weights, forecast_months = 12)

# สร้างแกนเวลา
months_7 <- seq.Date(from = as.Date("2014-01-01"), by = "month", length.out = length(sales) + 7)
months_12 <- seq.Date(from = as.Date("2014-01-01"), by = "month", length.out = length(sales) + 12)

# แปลงเวลาเป็นปี พ.ศ.
months_7_buddhist <- months_7 + years(543)
months_12_buddhist <- months_12 + years(543)

# สร้าง DataFrame สำหรับกราฟ
data_7 <- data.frame(
  Month = months_7_buddhist,
  Value = c(sales, forecast_2561_7),
  Type = c(rep("Actual Sales", length(sales)), rep("Forecast", length(forecast_2561_7)))
)

data_12 <- data.frame(
  Month = months_12_buddhist,
  Value = c(sales, forecast_2561_12),
  Type = c(rep("Actual Sales", length(sales)), rep("Forecast", length(forecast_2561_12)))
)

# กราฟ 7 เดือน
ggplot(data_7, aes(x = Month, y = Value, color = Type)) +
  geom_line(size = 1) +
  labs(title = "Actual vs Forecast Sales (2557-2561: 7 months)",
       x = "Month (พ.ศ.)",
       y = "Sales (Units)") +
  scale_color_manual(name = "Legend", values = c("Actual Sales" = "blue", "Forecast" = "red")) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  scale_x_date(date_labels = "%b-%Y", date_breaks = "6 months")

# กราฟ 12 เดือน
ggplot(data_12, aes(x = Month, y = Value, color = Type)) +
  geom_line(size = 1) +
  labs(title = "Actual vs Forecast Sales (2557-2561: 12 months)",
       x = "Month (พ.ศ.)",
       y = "Sales (Units)") +
  scale_color_manual(name = "Legend", values = c("Actual Sales" = "blue", "Forecast" = "red")) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  scale_x_date(date_labels = "%b-%Y", date_breaks = "6 months")

# แสดงผลค่าพยากรณ์
cat("=== Forecast for January-July 2561 ===\n")
print(forecast_2561_7)

cat("\n=== Forecast for Full Year 2561 ===\n")
print(forecast_2561_12)

