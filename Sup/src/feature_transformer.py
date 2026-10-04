"""โมดูลแปลงฟีเจอร์สำหรับไปป์ไลน์การทำนายความเสี่ยงและโอกาสสำเร็จการศึกษาของนักศึกษา MOOC."""

from __future__ import annotations
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class Log1pTransformer(BaseEstimator, TransformerMixin):
    """คลาสแปลงข้อมูลแบบกำหนดเองสำหรับคำนวณ log1p (log(1 + x)) บนฟีเจอร์ตัวเลขที่ไม่ติดลบ."""

    def fit(self, X, y=None):
        """กำหนดกระบวนการเรียนรู้ (ไม่มีพารามิเตอร์ต้องเรียนรู้ คืนค่าตนเอง)."""
        return self

    def transform(self, X):
        """แปลงข้อมูลโดยใช้ log(1 + max(x, 0)) เพื่อลดความเบ้ของข้อมูลที่มีหางยาว."""
        X = np.asarray(X)
        return np.log1p(np.maximum(X, 0))
