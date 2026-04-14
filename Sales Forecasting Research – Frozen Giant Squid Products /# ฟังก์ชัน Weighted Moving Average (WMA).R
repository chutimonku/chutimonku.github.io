# ข้อมูลยอดขายรายเดือน (ปี 2557–2560)
sales <- c(
  110.5, 70.3, 95.3, 120.6, 90.5, 75.5, 69.6, 77.2, 99.5, 82.1, 101.2, 103.5, # ปี 2557
  153.9, 89.1, 121, 148.8, 100.1, 95.5, 93.4, 88.9, 120.3, 92.2, 132.4, 121.3, # ปี 2558
  152, 91.9, 111.2, 149.9, 99, 83.3, 109.1, 87.7, 104.1, 75.7, 123.3, 159.5,   # ปี 2559
  141.5, 93.6, 112.1, 152.3, 98.9, 85.5, 110.5, 88.2, 103.5, 76.5, 122.4, 162.2 # ปี 2560
)

# น้ำหนักที่กำหนด
weights <- c(0.82, 0.00, 0.00, 0.00, 0.04, 0.00, 0.00, 0.00, 0.00, 0.09, 0.00, 0.05)

# ฟังก์ชัน Weighted Moving Average (WMA)
WMA <- function(data, weights) {
  n <- length(weights)
  forecast <- numeric(length(data))
  for (t in (n + 1):length(data)) {
    forecast[t] <- sum(weights * data[(t - n):(t - 1)])
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

# ระบุช่วงเวลา (3, 6, 9, 12 เดือน)
periods <- c(3, 6, 9, 12)

# ลูปวิเคราะห์ Weighted Moving Average สำหรับแต่ละช่วงเวลา
for (n in periods) {
  cat("\n=== Weighted Moving Average Analysis for Period:", n, "Months ===\n")
  
  # ปรับน้ำหนักให้ตรงกับช่วงเวลา
  adjusted_weights <- head(weights, n)
  
  # คำนวณค่าพยากรณ์ด้วย WMA
  forecast <- WMA(sales, adjusted_weights)
  
  # กำหนดค่าจริงและค่าพยากรณ์สำหรับช่วงเวลา
  actual <- tail(sales, -n)
  predicted <- tail(forecast, -n)
  
  # คำนวณค่าความคลาดเคลื่อน
  errors <- calculate_errors(actual, predicted)
  
  # แสดงผล
  cat("MAE:", errors$MAE, "\n")
  cat("MSE:", errors$MSE, "\n")
  cat("RMSE:", errors$RMSE, "\n")
  cat("MAPE:", errors$MAPE, "%\n")
}

