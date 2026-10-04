"""ขั้นตอนที่ 1: การกำหนดปัญหาสำหรับระบบทำนายความเสี่ยงและโอกาสสำเร็จการศึกษาของนักศึกษา MOOC."""

import json
import os

OUTPUT_PATH = os.path.join("data", "processed", "problem_definition.json")
CONFIG_PATH = os.path.join("config", "project_config.json")


def run_problem_definition():
    """สร้างและบันทึกเอกสารกำหนดขอบเขตปัญหา เป้าหมาย และเกณฑ์ความสำเร็จของระบบ."""
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    definition = {
        "project": config["project"],
        "objective": (
            "สร้างโมเดลการเรียนรู้แบบมีผู้สอนที่มีการเทียบเคียงความน่าจะเป็น เพื่อทำนายสถานะการสำเร็จการศึกษา "
            "และแบ่งกลุ่มนักศึกษาออกเป็น 3 ระดับความเสี่ยงสำหรับการวางแผนสนับสนุนเชิงรุก"
        ),
        "unit_of_analysis": f"หนึ่งแถวต่อนักศึกษาหนึ่งคน ({config['unit_of_analysis']})",
        "task_type": "Supervised Learning (Binary Classification & Risk Tiering)",
        "target_label": config["target_column"],
        "operational_tiers": config["risk_tiers"],
        "research_questions": [
            "พฤติกรรมการเรียนและการมีส่วนร่วมรูปแบบใดที่ทำนายการสำเร็จการศึกษาเทียบกับการออกกลางคันได้อย่างแม่นยำ?",
            "โมเดลตัวเลือกสามารถแยกแยะระหว่างผู้สำเร็จและไม่สำเร็จการศึกษาในข้อมูลที่มีความไม่สมดุลสูงได้ดีเพียงใด?",
            "ค่าความน่าจะเป็นที่โมเดลทำนายได้ มีความเที่ยงตรงเทียบเท่าความน่าจะเป็นจริง (Well-calibrated) หรือไม่?",
            "โมเดลยังคงรักษาความเป็นธรรมและความเสมอภาคในทุกกลุ่มประชากรย่อยหรือไม่?",
            "จะสามารถแปลงผลการทำนายไปสู่มาตรการช่วยเหลือสนับสนุนนักศึกษาที่ไม่เป็นการลงโทษได้อย่างไร?",
        ],
        "intended_users": [
            "อาจารย์ที่ปรึกษาทางวิชาการ (Academic advisors)",
            "ทีมผู้สอนประจำรายวิชา (Instructional teams)",
            "ผู้ประสานงานความสำเร็จของนักศึกษา (Student-success coordinators)",
            "นักวิจัยด้านการวิเคราะห์การเรียนรู้ (Learning analytics researchers)",
        ],
        "success_criteria": {
            "discrimination": "ROC-AUC >= 0.85 และ PR-AUC >= 0.35 เทียบกับค่าฐาน ~4.1%",
            "calibration": "Brier score <= 0.05 และผ่านการเทียบเคียงความน่าจะเป็นสอดคล้องกับค่าจริงในทุก Decile",
            "anti_leakage": (
                "แยกคอลัมน์ผลลัพธ์ทั้งหมด (certified, grade, incomplete_flag, explored) "
                "ออกจากฟีเจอร์ X อย่างเด็ดขาด ปราศจากการรั่วไหลข้าม Train/Validation/Test"
            ),
            "fairness": "ตรวจสอบความเสมอภาคของอัตราความแม่นยำข้ามเพศ ระดับการศึกษา และภูมิศาสตร์",
            "actionability": "แปลงค่าความน่าจะเป็นไปสู่ 3 ระดับความเสี่ยงเพื่อการปฏิบัติงานจริงได้อย่างชัดเจน",
        },
        "governance": {
            "anti_leakage_enforced": True,
            "forbidden_outcome_columns": config["outcome_columns"],
            "intended_use": "การช่วยเหลือทางการศึกษาเชิงรุก การส่งสัญญาณเตือนล่วงหน้า การทบทวนพื้นฐานความรู้",
            "prohibited_use": "การตัดสิทธิ์อัตโนมัติ การถอนรายวิชาแบบลงโทษ หรือการตัดสินผลการรับเข้าเรียนแบบเลือกปฏิบัติ",
        },
        "supported_new_data": config["supported_new_data"],
        "incompatible_data_policy": config["incompatible_data_policy"],
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(definition, handle, indent=2, ensure_ascii=False)

    print(f"[+] บันทึกเอกสารกำหนดปัญหาเรียบร้อยแล้วที่: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_problem_definition()
