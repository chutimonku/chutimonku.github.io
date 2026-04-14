### Holt-Winter's Additive Method (แบบบวก) ###

# ข้อมูลยอดขายรายเดือน (ปี 2557–2560)
sales <- c(
  110.5, 70.3, 95.3, 120.6, 90.5, 75.5, 69.6, 77.2, 99.5, 82.1, 101.2, 103.5, # ปี 2557
  153.9, 89.1, 121, 148.8, 100.1, 95.5, 93.4, 88.9, 120.3, 92.2, 132.4, 121.3, # ปี 2558
  152, 91.9, 111.2, 149.9, 99, 83.3, 109.1, 87.7, 104.1, 75.7, 123.3, 159.5,   # ปี 2559
  141.5, 93.6, 112.1, 152.3, 98.9, 85.5, 110.5, 88.2, 103.5, 76.5, 122.4, 162.2 # ปี 2560
)

# ระบุช่วงเวลา (3, 6, 9, 12 เดือน)
periods <- c(3, 6, 9, 12)

# ฟังก์ชันสำหรับ Holt-Winter's Additive Method (แบบบวก)
holt_winters <- function(data, alpha, beta, gamma, m) {
  n <- length(data)
  L <- numeric(n)
  T <- numeric(n)
  S <- numeric(n)
  F <- numeric(n + m) # เพิ่มพื้นที่สำหรับค่าพยากรณ์ล่วงหน้า
  
  # ค่าเริ่มต้น
  L[1] <- mean(data[1:m]) # ค่าเฉลี่ยของช่วงฤดูกาลแรก
  T[1] <- (mean(data[(m + 1):(2 * m)]) - mean(data[1:m])) / m
  S[1:m] <- data[1:m] - L[1]
  
  cat("ค่าเริ่มต้นของระดับ (L[1]):", L[1], "\n")
  cat("ค่าเริ่มต้นของแนวโน้ม (T[1]):", T[1], "\n")
  cat("ค่าเริ่มต้นของฤดูกาล (S[1:m]):", S[1:m], "\n")
  
  # Holt-Winter's Calculations
  for (t in (m + 1):n) {
    L[t] <- alpha * (data[t] - S[t - m]) + (1 - alpha) * (L[t - 1] + T[t - 1])
    T[t] <- beta * (L[t] - L[t - 1]) + (1 - beta) * T[t - 1]
    S[t] <- gamma * (data[t] - L[t]) + (1 - gamma) * S[t - m]
    F[t] <- L[t] + T[t] + S[t - m]
  }
  
  # ค่าพยากรณ์
  for (k in 1:m) {
    F[n + k] <- L[n] + k * T[n] + S[n + k - m]
  }
  
  return(F)
}

# ฟังก์ชันสำหรับคำนวณ MAE, MSE, RMSE, MAPE
calculate_errors <- function(actual, predicted) {
  mae <- mean(abs(actual - predicted), na.rm = TRUE)
  mse <- mean((actual - predicted)^2, na.rm = TRUE)
  rmse <- sqrt(mse) # คำนวณ RMSE
  mape <- mean(abs((actual - predicted) / actual), na.rm = TRUE) * 100
  return(list(MAE = mae, MSE = mse, RMSE = rmse, MAPE = mape))
}

# กำหนดค่าพารามิเตอร์
alpha <- 0.5 # ระดับ
beta <- 0.1 # แนวโน้ม
gamma <- 0.5 # ฤดูกาล

# ลูปวิเคราะห์ Holt-Winter's สำหรับแต่ละช่วงเวลา
for (m in periods) {
  cat("\n=== Holt-Winter's Analysis for Period:", m, "Months ===\n")
  
  # คำนวณค่าพยากรณ์
  forecast <- holt_winters(sales, alpha, beta, gamma, m)
  
  # กำหนดค่าจริงและค่าพยากรณ์สำหรับช่วงเวลา
  actual <- tail(sales, -m)
  predicted <- tail(forecast, -m)
  
  # คำนวณค่าความคลาดเคลื่อน
  errors <- calculate_errors(actual, predicted)
  
  # แสดงผล
  cat("MAE:", errors$MAE, "\n")
  cat("MSE:", errors$MSE, "\n")
  cat("RMSE:", errors$RMSE, "\n")
  cat("MAPE:", errors$MAPE, "%\n")
}

