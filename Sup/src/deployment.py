"""คลาสสำหรับการติดตั้งใช้งาน (Deployment) โมเดลทำนายความเสี่ยงและโอกาสสำเร็จการศึกษาของนักศึกษา MOOC."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from src.feature_transformer import Log1pTransformer

# คอลัมน์ผลลัพธ์ปลายทางที่ห้ามนำเข้าสู่กระบวนการทำนาย (ป้องกันข้อมูลรั่วไหล Data Leakage)
FORBIDDEN_OUTCOME_COLUMNS = {"certified", "grade", "incomplete_flag", "explored"}

# ฟีเจอร์ที่ไปป์ไลน์คำนวณอนุพันธ์ขึ้นเองโดยอัตโนมัติจากฟีเจอร์ตั้งต้น
DERIVED_FEATURES = {
    "event_intensity",
    "video_play_ratio",
    "chapter_intensity",
    "has_forum_activity",
    "has_multiple_courses",
}


class DataLeakageSecurityException(ValueError):
    """ข้อผิดพลาดด้านความปลอดภัย: ตรวจพบคอลัมน์ผลลัพธ์ปลายทางในชุดข้อมูลที่ส่งเข้ามาทำนายผล."""


class InputSchemaError(ValueError):
    """ข้อผิดพลาดด้านโครงสร้างข้อมูล: ข้อมูลนำเข้าไม่ตรงตามข้อกำหนดของ Input Schema."""


class MoocStudentRiskPipeline:
    """ไปป์ไลน์สำหรับทำนายโอกาสสำเร็จการศึกษาและจำแนกกลุ่มความเสี่ยงแบบครบวงจร (End-to-End)."""

    def __init__(
        self,
        preprocessor,
        model,
        optimal_threshold: float = 0.50,
        risk_tiers_config: dict | None = None,
        input_features: list[str] | None = None,
        forbidden_outcome_columns: list[str] | None = None,
    ):
        """กำหนดค่าเริ่มต้นสำหรับไปป์ไลน์การทำนาย.

        พารามิเตอร์:
            preprocessor: อ็อบเจกต์ ColumnTransformer ที่ผ่านการฟิตแล้ว
            model: โมเดลการเรียนรู้ที่ผ่านการล็อกแล้ว
            optimal_threshold (float): จุดตัดความน่าจะเป็นที่ปรับจูนเพื่อประสิทธิภาพสูงสุด
            risk_tiers_config (dict): ข้อกำหนดเกณฑ์ระดับความเสี่ยง 3 กลุ่ม
            input_features (list): รายชื่อฟีเจอร์ทั้งหมดที่โมเดลต้องการ
            forbidden_outcome_columns (list): รายชื่อคอลัมน์ผลลัพธ์ที่ต้องห้าม
        """
        self.preprocessor = preprocessor
        self.model = model
        self.optimal_threshold = float(optimal_threshold)
        self.risk_tiers_config = risk_tiers_config or {
            "tier_1": {"min_probability": 0.50, "recommended_action": "การเสริมสร้างศักยภาพขั้นสูง ความเป็นผู้นำการติวเพื่อนร่วมชั้น"},
            "tier_2": {"min_probability": 0.15, "recommended_action": "การติดตามเชิงรุก การจับคู่กลุ่มติว และการแจ้งเตือนงานตามกำหนดเวลา"},
            "tier_3": {"min_probability": 0.00, "recommended_action": "การติดต่อจากที่ปรึกษาอย่างเร่งด่วน การทดสอบวินิจฉัยพื้นฐาน และการปรับพื้นฐานความรู้"},
        }
        self.input_features = input_features or []
        self.forbidden_outcome_columns = set(forbidden_outcome_columns or FORBIDDEN_OUTCOME_COLUMNS)

    @property
    def required_input_features(self) -> list[str]:
        """รายชื่อฟีเจอร์ตั้งต้นที่ผู้ใช้งานต้องจัดเตรียมในไฟล์ข้อมูล (ไม่รวมฟีเจอร์ที่ไปป์ไลน์คำนวณให้อัตโนมัติ)."""
        return [feature for feature in self.input_features if feature not in DERIVED_FEATURES]

    def _reject_outcomes(self, frame: pd.DataFrame):
        """ปฏิเสธข้อมูลทันทีหากพบคอลัมน์ผลลัพธ์ปลายทาง เพื่อป้องกันข้อมูลรั่วไหล."""
        forbidden = getattr(self, "forbidden_outcome_columns", FORBIDDEN_OUTCOME_COLUMNS)
        leaked = sorted(set(forbidden).intersection(frame.columns))
        if leaked:
            raise DataLeakageSecurityException(
                f"ตรวจพบการละเมิดความปลอดภัย: คอลัมน์ผลลัพธ์ปลายทางต้องไม่ปรากฏในข้อมูลนำเข้าการทำนาย: {leaked}"
            )

    @staticmethod
    def _require_columns(frame: pd.DataFrame, required: list[str]):
        """ตรวจสอบว่ามีคอลัมน์ที่จำเป็นครบถ้วนหรือไม่."""
        missing = sorted(set(required).difference(frame.columns))
        if missing:
            raise InputSchemaError(f"คอลัมน์ที่จำเป็นสูญหายในข้อมูลนำเข้า: {missing}")

    @staticmethod
    def _validate_identifier(frame: pd.DataFrame):
        """ตรวจสอบความถูกต้องของรหัสนักศึกษา (userid_DI)."""
        if "userid_DI" not in frame.columns:
            raise InputSchemaError("จำเป็นต้องมีคอลัมน์ 'userid_DI' เพื่อใช้เป็นรหัสประจำตัวนักศึกษา")
        identifiers = frame["userid_DI"]
        if identifiers.isna().any() or identifiers.astype(str).str.strip().eq("").any():
            raise InputSchemaError("รหัส 'userid_DI' ต้องไม่เป็นค่าว่างสำหรับทุกแถวข้อมูล")
        if identifiers.duplicated().any():
            raise InputSchemaError(
                "พบรหัส 'userid_DI' ซ้ำกันในข้อมูลนำเข้า ข้อมูลต้องถูกรวมเป็น 1 แถวต่อนักศึกษา 1 คนเท่านั้น"
            )

    @staticmethod
    def _validate_numeric(frame: pd.DataFrame, columns: list[str]):
        """ตรวจสอบความถูกต้องของฟีเจอร์ประเภทตัวเลข."""
        for col in columns:
            if col in frame.columns:
                if not is_numeric_dtype(frame[col]):
                    raise InputSchemaError(f"คอลัมน์ '{col}' ต้องเป็นข้อมูลตัวเลข แต่พบประเภท {frame[col].dtype}")
                non_finite = np.isinf(frame[col].to_numpy(dtype=float, na_value=np.nan)).any()
                if non_finite:
                    raise InputSchemaError(f"คอลัมน์ '{col}' มีค่าที่เป็นอนันต์หรือไม่ถูกต้อง (Infinite Values)")

    def validate_student_profiles(self, students: pd.DataFrame) -> pd.DataFrame:
        """ตรวจสอบความสมบูรณ์และคำนวณฟีเจอร์อนุพันธ์สำหรับข้อมูลโปรไฟล์นักศึกษา.

        โมเดลได้รับการฝึกสอนจากข้อมูลสรุปพฤติกรรมระดับนักศึกษา ดังนั้นการทำนายจะถูกต้อง
        ก็ต่อเมื่อได้รับข้อมูลโครงสร้างแบบเดียวกัน ข้อมูลที่สูญหายจะไม่ถูกแทนที่ด้วยศูนย์อย่างเงียบๆ
        """
        self._reject_outcomes(students)
        self._require_columns(students, ["userid_DI"])
        self._validate_identifier(students)
        df_ready = students.copy()

        # คำนวณฟีเจอร์อนุพันธ์เชิงกำหนด (Deterministic Derived Features) ใหม่จากฟีเจอร์ตั้งต้น
        # เพื่อป้องกันความคลาดเคลื่อนจากไฟล์ภายนอก
        if {"total_events", "total_active_days"}.issubset(df_ready.columns):
            df_ready["event_intensity"] = df_ready["total_events"] / np.maximum(df_ready["total_active_days"], 1)
        if {"total_video_plays", "total_events"}.issubset(df_ready.columns):
            video_plays = df_ready["total_video_plays"].fillna(0)
            df_ready["video_play_ratio"] = video_plays / np.maximum(df_ready["total_events"], 1)
        if {"total_chapters", "total_active_days"}.issubset(df_ready.columns):
            df_ready["chapter_intensity"] = df_ready["total_chapters"] / np.maximum(df_ready["total_active_days"], 1)
        if "total_forum_posts" in df_ready.columns:
            df_ready["has_forum_activity"] = (df_ready["total_forum_posts"] > 0).astype("int8")
        if "n_courses" in df_ready.columns:
            df_ready["has_multiple_courses"] = (df_ready["n_courses"] > 1).astype("int8")

        # ตรวจสอบว่ามีฟีเจอร์ครบตามที่โมเดลต้องการทั้งหมด
        self._require_columns(df_ready, list(self.input_features))

        categorical_cols = {"gender", "LoE_DI", "country"}
        numeric_cols = [c for c in self.input_features if c not in categorical_cols]
        self._validate_numeric(df_ready, numeric_cols)

        for col in numeric_cols:
            if (df_ready[col].dropna() < 0).any():
                raise InputSchemaError(f"ฟีเจอร์ตัวเลข '{col}' ต้องไม่มีค่าติดลบ")

        if "n_courses" in df_ready.columns and (df_ready["n_courses"].dropna() < 1).any():
            raise InputSchemaError("จำนวนคอร์ส 'n_courses' ต้องมีค่าอย่างน้อย 1")
        for rate_col in ["view_rate", "video_data_available_rate"]:
            values = df_ready[rate_col].dropna()
            if ((values < 0) | (values > 1)).any():
                raise InputSchemaError(f"คอลัมน์อัตราส่วน '{rate_col}' ต้องมีค่าอยู่ระหว่าง 0 ถึง 1")
        if "age" in df_ready.columns:
            ages = df_ready["age"].dropna()
            if ((ages <= 0) | (ages > 100)).any():
                raise InputSchemaError("คอลัมน์อายุ 'age' ต้องอยู่ระหว่าง 1 ถึง 100 ปี หรือเป็นค่าว่าง")

        return df_ready

    def predict_proba(self, students: pd.DataFrame) -> np.ndarray:
        """คำนวณค่าความน่าจะเป็นที่นักศึกษาจะสำเร็จการศึกษาและได้รับใบประกาศนียบัตร P(certified=1)."""
        df_ready = self.validate_student_profiles(students)
        X_trans = self.preprocessor.transform(df_ready[self.input_features])
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_trans)[:, 1]
        else:
            probs = self.model.decision_function(X_trans)
        return np.clip(probs, 0.0, 1.0)

    def predict(self, students: pd.DataFrame) -> np.ndarray:
        """ทำนายผลแบบไบนารี (1 = ได้ใบจบ, 0 = ไม่ได้ใบจบ) ตามจุดตัดการตัดสินใจที่เหมาะสมที่สุด."""
        probs = self.predict_proba(students)
        return (probs >= self.optimal_threshold).astype(int)

    def predict_risk_tiers(self, students: pd.DataFrame) -> pd.DataFrame:
        """สร้าง DataFrame ผลการทำนายความเสี่ยงและแผนการสนับสนุนนักศึกษาแบบละเอียด."""
        df_ready = self.validate_student_profiles(students)
        probs = self.predict_proba(df_ready)
        binary_preds = (probs >= self.optimal_threshold).astype(int)

        t1_cfg = self.risk_tiers_config["tier_1"]
        t2_cfg = self.risk_tiers_config["tier_2"]
        t3_cfg = self.risk_tiers_config["tier_3"]

        tier_names = []
        actions = []
        confidences = []

        for p in probs:
            if p >= t1_cfg["min_probability"]:
                tier_names.append("Tier 1: Low Risk / Likely Completer")
                actions.append(t1_cfg["recommended_action"])
                confidences.append(float(round(p, 4)))
            elif p >= t2_cfg["min_probability"]:
                tier_names.append("Tier 2: Moderate Risk / Target for Nudge")
                actions.append(t2_cfg["recommended_action"])
                confidences.append(float(round(1.0 - abs(p - 0.50), 4)))
            else:
                tier_names.append("Tier 3: High Risk / Early Dropout")
                actions.append(t3_cfg["recommended_action"])
                confidences.append(float(round(1.0 - p, 4)))

        return pd.DataFrame({
            "userid_DI": df_ready["userid_DI"].values,
            "completion_probability": np.round(probs, 4),
            "predicted_completion": binary_preds,
            "decision_threshold": self.optimal_threshold,
            "risk_tier": tier_names,
            "confidence_score": confidences,
            "recommended_support_action": actions,
        })
