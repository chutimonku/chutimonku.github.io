### Exponential Smoothing###

# ข้อมูลยอดขายรายเดือน (ปี 2557–2560)
sales <- c(
  110.5, 70.3, 95.3, 120.6, 90.5, 75.5, 69.6, 77.2, 99.5, 82.1, 101.2, 103.5, # ปี 2557
  153.9, 89.1, 121, 148.8, 100.1, 95.5, 93.4, 88.9, 120.3, 92.2, 132.4, 121.3, # ปี 2558
  152, 91.9, 111.2, 149.9, 99, 83.3, 109.1, 87.7, 104.1, 75.7, 123.3, 159.5,   # ปี 2559
  141.5, 93.6, 112.1, 152.3, 98.9, 85.5, 110.5, 88.2, 103.5, 76.5, 122.4, 162.2 # ปี 2560
)

# ฟังก์ชัน Exponential Smoothing
exponential_smoothing <- function(data, alpha) {
  forecast <- numeric(length(data))
  forecast[1] <- data[1] # ค่าเริ่มต้น
  for (t in 2:length(data)) {
    forecast[t] <- alpha * data[t - 1] + (1 - alpha) * forecast[t - 1]
  }
  return(forecast)
}

# ฟังก์ชันสำหรับคำนวณ MAE, MSE, RMSE, MAPE
calculate_errors <- function(actual, predicted) {
  mae <- mean(abs(actual - predicted), na.rm = TRUE)
  mse <- mean((actual - predicted)^2, na.rm = TRUE)
  rmse <- sqrt(mse)
  mape <- mean(abs((actual - predicted) / actual), na.rm = TRUE) * 100
  return(list(MAE = mae, MSE = mse, RMSE = rmse, MAPE = mape))
}

# กำหนดค่าคงที่ปรับเรียบ
alpha <- 0.1 # สามารถปรับค่าได้

# ระบุช่วงเวลา (3, 6, 9, 12 เดือน)
periods <- c(3, 6, 9, 12)

# ลูปวิเคราะห์ Exponential Smoothing สำหรับแต่ละช่วงเวลา
for (n in periods) {
  cat("\n=== Exponential Smoothing Analysis for Period:", n, "Months ===\n")
  
  # คำนวณค่าพยากรณ์ด้วย Exponential Smoothing
  forecast <- exponential_smoothing(sales, alpha)
  
  # กำหนดค่าจริงและค่าพยากรณ์สำหรับช่วงเวลา
  actual <- tail(sales, -n + 1) # ค่าจริง
  predicted <- tail(forecast, -n + 1) # ค่าพยากรณ์
  
  # คำนวณค่าความคลาดเคลื่อน
  errors <- calculate_errors(actual, predicted)
  
  # แสดงผล
  cat("Alpha:", alpha, "\n")
  cat("MAE:", errors$MAE, "\n")
  cat("MSE:", errors$MSE, "\n")
  cat("RMSE:", errors$RMSE, "\n")
  cat("MAPE:", errors$MAPE, "%\n")
}

