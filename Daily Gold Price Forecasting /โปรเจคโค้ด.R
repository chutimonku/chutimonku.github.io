# โหลดแพ็กเกจที่ต้องใช้
library(forecast)
library(urca)
library(readxl)
library(TSA)

# อ่านข้อมูล
X4_gold = read_excel("Forceting Final/งานล่าสุด/4. gold.xlsx", 
                     sheet = "gold_model")
#==============================================================================#
# ข้อที่ 1: พล็อตข้อมูล
Price_Gold = ts(X4_gold$price, start = c(2023, 1, 2), frequency = 365)
plot(Price_Gold, main="Gold Price Time Series", ylab="Price_Gold", xlab="Time")
abline(h = mean(Price_Gold), col = "red", lty = 2)

# เช็ค ACF และ PACF
par(mfrow = c(1,2))
acf(Price_Gold)
pacf(Price_Gold)

# ตรวจสอบความเป็น Stationary
summary(ur.df(Price_Gold, type = "trend", selectlags = "AIC"))

#==============================================================================#
# ทำข้อมูลให้เป็น Stationary
pdiff = diff(Price_Gold, lag = 1)
pdiff = ts(pdiff, start = c(2023, 3), frequency = 365)  # ปรับให้ตรงกับข้อมูลที่ต่างกัน

plot(pdiff)
abline(h = mean(pdiff), col = "red", lty = 2)

par(mfrow = c(1,2))
acf(pdiff)
pacf(pdiff)

# ตรวจสอบความเป็น Stationary อีกครั้ง
summary(ur.df(pdiff, type = "none", selectlags = "AIC"))

#==============================================================================#
# ข้อที่ 2
model212 = Arima(pdiff, order = c(2,1,2))  # เลือกโมเดลจากการดู ACF และ PACF
model113 = Arima(pdiff, order = c(1,1,3))  # เลือกโมเดลจากการดู auto.arima

#หาโมเดลที่เหมาสมแบบใช้ auto.arima
auto.arima(pdiff, d = 1,test = "adf", trace = TRUE, seasonal = FALSE, ic = "aic"
           , stepwise = FALSE)
auto.arima(pdiff, d = 1,test = "adf", trace = TRUE, seasonal = FALSE, ic = "bic"
           , stepwise = FALSE)
# aic = 1,1,3 // bic = 1,1,3

#==============================================================================#
# ข้อที่ 3: ตรวจสอบโมเดล 
# ตรวจสอบ Residuals
checkresiduals(model212, 50, test = "LB", plot = TRUE)
checkresiduals(modelc, 50, test = "LB", plot = TRUE)

# คำนวณค่าความผิดพลาด
accuracy(model212)
accuracy(model113)  

#MSE 
MSE212 = 0.938857^2 
MSE113 = 0.9346177^2 
#สรุปเลือกAIC = 1,1,3
#==============================================================================#
# ข้อที่ 4: พยากรณ์ 11 - 20 เม.ย. (ใช้ predict())
predict_10_days = predict(model113, n.ahead = 10)

# คืนค่าพยากรณ์กลับไปยังระดับเดิม
last_value = as.numeric(tail(Price_Gold, 1))  # ค่าล่าสุดของข้อมูลจริง
predict_10_days_original = last_value + cumsum(predict_10_days$pred)
predict_10_days_original
#==============================================================================#
# พยากรณ์ 21 - 30 เม.ย. (ใช้ forecast())
forecast_10_days = forecast(model113, h = 10)

# **ใช้ค่าล่าสุดจากพยากรณ์ 11 - 20 เม.ย.**
forecast_next_10_days_original = tail(predict_10_days_original, 1) + cumsum(forecast_10_days$mean)
forecast_next_10_days_original
#==============================================================================#
# สร้างกราฟ
# เวลาของข้อมูลจริง
time_actual = seq(from = as.Date("2023-01-02"), 
                  by = "day", length.out = length(Price_Gold))
# เวลาของการพยากรณ์ช่วง 11 - 30 เม.ย.
time_forecast_10_days = seq(from = as.Date("2024-04-11"), by = "day", 
                            length.out = length(predict_10_days_original))
time_forecast_next_10_days = seq(from = as.Date("2024-04-21"), by = "day", 
                                 length.out = length(forecast_next_10_days_original))
# พล็อตค่าจริง
plot(time_actual, Price_Gold, type="l", col="blue", lwd=2, xlab="Time", ylab="Gold Price",
     main="Actual vs Forecasted Gold Price",
     ylim = range(c(Price_Gold, predict_10_days_original, forecast_next_10_days_original)))

# พล็อตค่าพยากรณ์ 11 - 20 เม.ย.
lines(time_forecast_10_days, predict_10_days_original, col="red", lwd=2, lty=2)
# พล็อตค่าพยากรณ์ 21 - 30 เม.ย.
lines(time_forecast_next_10_days, forecast_next_10_days_original, col="green", lwd=2, lty=3)
# เพิ่มคำอธิบายในกราฟ
legend("topleft", legend=c("Actual", "Predicted (Apr 11-20)", "Forecasted (Apr 21-30)"),
       col=c("blue", "red", "green"), lty=c(1,2,3), lwd=2, bty="n")


