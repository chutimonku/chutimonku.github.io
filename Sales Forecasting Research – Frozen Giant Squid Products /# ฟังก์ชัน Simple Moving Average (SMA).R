# ติดตั้งแพ็กเกจ (ถ้ายังไม่ได้ติดตั้ง)
install.packages("forecast")
install.packages("Metrics")

# โหลดแพ็กเกจที่ใช้
library(forecast)
library(Metrics)

# ข้อมูลยอดขายรายเดือนปี 2557-2560
sales <- c(
  110.5, 70.3, 95.3, 120.6, 90.5, 75.5, 69.6, 77.2, 99.5, 82.1, 101.2, 103.5, # ปี 2557
  153.9, 89.1, 121, 148.8, 100.1, 95.5, 93.4, 88.9, 120.3, 92.2, 132.4, 121.3, # ปี 2558
  152, 91.9, 111.2, 149.9, 99, 83.3, 109.1, 87.7, 104.1, 75.7, 123.3, 159.5,   # ปี 2559
  141.5, 93.6, 112.1, 152.3, 98.9, 85.5, 110.5, 88.2, 103.5, 76.5, 122.4, 162.2 # ปี 2560
)

# ฟังก์ชัน Simple Moving Average (SMA)
SMA <- function(data, n) {
  stats::filter(data, rep(1 / n, n), sides = 1)
}

# ฟังก์ชันสำหรับคำนวณ MAE, MSE, MAPE, RMSE
calculate_errors <- function(actual, predicted) {
  mae <- mean(abs(actual - predicted), na.rm = TRUE)
  mse <- mean((actual - predicted)^2, na.rm = TRUE)
  rmse <- sqrt(mse)
  mape <- mean(abs((actual - predicted) / actual), na.rm = TRUE) * 100
  return(list(MAE = mae, MSE = mse, RMSE = rmse, MAPE = mape))
}

# ระบุช่วงเวลา (3, 6, 9, 12 เดือน)
periods <- c(3, 6, 9, 12)

# ลูปคำนวณความคลาดเคลื่อนสำหรับแต่ละช่วง
for (n in periods) {
  cat("\n=== SMA Analysis for Period:", n, "Months ===\n")
  
  # คำนวณ SMA
  predicted <- SMA(sales, n)
  
  # ตัดค่า NA ที่เกิดจาก SMA
  actual <- tail(sales, -n + 1)
  predicted <- predicted[n:length(predicted)]
  
  # คำนวณ MAE, MSE, RMSE, MAPE
  errors <- calculate_errors(actual, predicted)
  
  # แสดงผล
  cat("MAE:", errors$MAE, "\n")
  cat("MSE:", errors$MSE, "\n")
  cat("RMSE:", errors$RMSE, "\n")
  cat("MAPE:", errors$MAPE, "%\n")
}
