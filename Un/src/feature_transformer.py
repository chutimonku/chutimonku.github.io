"""คลาสเตรียมและแปลงฟีเจอร์สำหรับขั้นตอนการฝึกสอนและการติดตั้งใช้งานโมเดลการจัดกลุ่มนักศึกษา."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

# คอลัมน์ผลลัพธ์ปลายทางที่ต้องกักกันไม่ให้นำมาใช้ในการจัดกลุ่มพฤติกรรม
FORBIDDEN_COLUMNS = ["certified", "grade", "incomplete_flag", "explored"]

# รายชื่อฟีเจอร์หลักเชิงพฤติกรรมที่ผ่านการแปลง log
CORE_FEATURES = [
    "log_n_courses",
    "view_rate",
    "log_total_events",
    "log_total_active_days",
    "log_total_chapters",
    "log_total_forum_posts",
    "log_overall_span_days",
    "log_event_intensity",
]

# ฟีเจอร์ทางเลือกเกี่ยวกับการรับชมวิดีโอสำหรับการทดสอบความไว (Sensitivity Analysis)
VIDEO_FEATURES = ["log_total_video_plays", "video_data_available_rate"]


class MoocFeatureEngineer(BaseEstimator, TransformerMixin):
    """คลาสวิศวกรรมฟีเจอร์ที่ปลอดภัยจากการรั่วไหลของข้อมูลผลลัพธ์ พร้อมตัวเลือกวิเคราะห์ความไวของวิดีโอ."""

    def __init__(self, include_video: bool = False):
        """กำหนดค่าเริ่มต้นของคลาสวิศวกรรมฟีเจอร์.

        พารามิเตอร์:
            include_video (bool): ระบุว่าจะรวมฟีเจอร์วิดีโอในการจัดกลุ่มหรือไม่ (ค่าเริ่มต้นคือ False)
        """
        self.include_video = include_video
        self.scaler = StandardScaler()
        self.span_log_median_ = 0.0
        self.video_log_median_ = 0.0

    @property
    def feature_names_(self):
        """รายชื่อฟีเจอร์ทั้งหมดที่ได้หลังการแปลง."""
        return CORE_FEATURES + (VIDEO_FEATURES if self.include_video else [])

    def _assert_no_leakage(self, frame: pd.DataFrame):
        """ตรวจสอบความปลอดภัยเพื่อป้องกันไม่ให้มีคอลัมน์ผลลัพธ์รั่วไหลเข้ามาในข้อมูลฟีเจอร์."""
        leaked = sorted(set(FORBIDDEN_COLUMNS).intersection(frame.columns))
        if leaked:
            raise ValueError(f"ตรวจพบคอลัมน์ผลลัพธ์ปลายทางที่ถูกกักกัน: {leaked}")

    @staticmethod
    def _log_nonnegative(series: pd.Series) -> pd.Series:
        """แปลงข้อมูลตัวเลขที่ไม่ติดลบด้วยฟังก์ชัน log1p (log(1 + x))."""
        return np.log1p(pd.to_numeric(series, errors="coerce").clip(lower=0))

    def _transform_unscaled(self, frame: pd.DataFrame, fitting: bool = False) -> pd.DataFrame:
        """แปลงฟีเจอร์ในระดับสเกลเดิมก่อนเข้าสู่กระบวนการ Standardize."""
        self._assert_no_leakage(frame)
        output = pd.DataFrame(index=frame.index)
        output["log_n_courses"] = self._log_nonnegative(frame["n_courses"])
        output["view_rate"] = pd.to_numeric(frame["view_rate"], errors="coerce").clip(0, 1)
        output["log_total_events"] = self._log_nonnegative(frame["total_events"])
        output["log_total_active_days"] = self._log_nonnegative(frame["total_active_days"])
        output["log_total_chapters"] = self._log_nonnegative(frame["total_chapters"])
        output["log_total_forum_posts"] = self._log_nonnegative(frame["total_forum_posts"])
        output["log_event_intensity"] = self._log_nonnegative(frame["event_intensity"])
        span = self._log_nonnegative(frame["overall_span_days"])

        if fitting:
            observed_median = span.median()
            self.span_log_median_ = (
                float(observed_median) if pd.notna(observed_median) else 0.0
            )

        output["log_overall_span_days"] = span.fillna(
            self.span_log_median_
        )

        if self.include_video:
            video = self._log_nonnegative(frame["total_video_plays"])
            if fitting:
                observed_median = video.median()
                self.video_log_median_ = float(observed_median) if pd.notna(observed_median) else 0.0
            output["log_total_video_plays"] = video.fillna(self.video_log_median_)
            output["video_data_available_rate"] = pd.to_numeric(
                frame["video_data_available_rate"], errors="coerce"
            ).fillna(0).clip(0, 1)

        return output[self.feature_names_]

    def fit(self, X: pd.DataFrame, y=None):
        """คำนวณค่าสถิติจากชุดข้อมูลฝึกสอน (มัธยฐาน, ค่าเฉลี่ย, ส่วนเบี่ยงเบนมาตรฐาน)."""
        transformed = self._transform_unscaled(X, fitting=True)
        if transformed.isna().any().any():
            missing = transformed.columns[transformed.isna().any()].tolist()
            raise ValueError(f"พบค่าสูญหายในฟีเจอร์หลักหลังการแปลง: {missing}")
        self.scaler.fit(transformed)
        return self

    def transform_frame(self, X: pd.DataFrame) -> pd.DataFrame:
        """แปลงฟีเจอร์และปรับสเกลมาตรฐาน (StandardScaler) โดยส่งคืนในรูปแบบ DataFrame."""
        transformed = self._transform_unscaled(X)
        scaled = self.scaler.transform(transformed)
        return pd.DataFrame(scaled, columns=self.feature_names_, index=X.index)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """แปลงฟีเจอร์และส่งคืนในรูปแบบ NumPy ndarray สำหรับส่งต่อให้โมเดล."""
        return self.transform_frame(X).to_numpy()

    def get_feature_names_out(self, input_features=None):
        """คืนค่ารายชื่อฟีเจอร์ผลลัพธ์."""
        return np.asarray(self.feature_names_)
