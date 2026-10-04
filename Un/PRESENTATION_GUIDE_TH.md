# คู่มือพรีเซนต์โครงการ Student Segmentation

เอกสารนี้สรุปที่มาของงาน การปรับ Workflow ของอาจารย์ให้เหมาะกับโครงการ การแก้โค้ด การวิเคราะห์ ผลลัพธ์ และข้อจำกัด โดยอ้างอิงจากไฟล์และผลคำนวณจริงในโครงการ

> หมายเหตุเรื่องพรอมต์: ส่วน “ลำดับพรอมต์” เก็บข้อความสำคัญที่ปรากฏในประวัติงานและสรุปเจตนาของคำสั่งที่แก้ทีละจุด ไม่ได้อ้างว่าเป็น transcript คำต่อคำของข้อความสั้นหรือไฟล์แนบทุกฉบับ ข้อความ “ต่อไป” เป็นการขอให้พัฒนา Workflow ทีละขั้นเพื่อประหยัดโทเคน ไม่ใช่การเปลี่ยนวิธีวิเคราะห์

---

## 1. สรุปโครงการภายใน 1 นาที

โครงการนี้ใช้ข้อมูล MOOC เพื่อค้นหารูปแบบพฤติกรรมของนักศึกษาโดยใช้ **Unsupervised Learning หรือ Clustering** เป้าหมายไม่ใช่การทำนายว่าใครจะผ่านหรือตก แต่เป็นการค้นหากลุ่มพฤติกรรมที่มีลักษณะต่างกัน เพื่อใช้เป็นข้อมูลประกอบการวางแผนสนับสนุนนักศึกษาอย่างรับผิดชอบ

ข้อมูลดิบมี **416,921 records, 22 columns และนักศึกษาไม่ซ้ำ 335,650 คน** หนึ่งคนอาจมีมากกว่าหนึ่ง record เพราะอาจลงทะเบียนหลายวิชา จึงต้อง aggregate ให้เป็น **หนึ่งแถวต่อนักศึกษา** ก่อนทำ clustering การลดจาก 416,921 เหลือ 335,650 จึงเป็นการเปลี่ยนหน่วยวิเคราะห์ ไม่ใช่การลบข้อมูลนักศึกษา

ตัวแปรผลลัพธ์ ได้แก่ `certified`, `grade`, `incomplete_flag` และ `explored` ถูกแยกออกตั้งแต่ต้นและไม่ถูกใช้สร้าง feature เลือกโมเดล tune โมเดล หรือเลือกจำนวน cluster หลังจากเลือกและล็อกโมเดลด้วย internal metrics แล้วจึงนำ outcome มาใช้ตรวจสอบภายหลังแบบ **post-hoc validation** เท่านั้น

โครงการเปรียบเทียบ **29 configurations จาก 6 clustering families** และเลือก **K-Means จำนวน 4 clusters** จากกฎจัดอันดับหลายตัวชี้วัดร่วมกัน โมเดลสุดท้ายถูก fit ใหม่กับนักศึกษาครบ 335,650 คน ผลหลักคือ Silhouette = **0.3737**, Davies–Bouldin = **0.9858**, Calinski–Harabasz = **3,193.55** และ resample stability ARI = **0.9803**

ผลลัพธ์ทั้งหมดสร้างซ้ำได้ด้วย `python run_project.py` มี dashboard HTML, โมเดลพร้อมใช้งาน, schema validation, leakage tests, monitoring baseline, logs และ artifact verification

---

## 2. โจทย์ตั้งต้นและเหตุผลที่ต้องปรับ Workflow

### 2.1 Workflow ต้นฉบับของอาจารย์

Workflow ต้นฉบับมี 10 ขั้น ตั้งแต่การกำหนดปัญหา การหาและโหลดข้อมูล EDA, literature review, feature engineering, model selection, model evaluation, การสรุปและวิเคราะห์ข้อผิดพลาด, การ revise งาน และการสร้าง HTML

ข้อจำกัดสำหรับโครงการนี้คือยังไม่มี Data Cleaning และ Model Training เป็นขั้นแยก บังคับเลือกทั้ง clustering และ classification อย่างน้อยประเภทละ 5 โมเดล และบังคับ confusion matrix ซึ่งไม่เหมาะกับ Student Segmentation แบบ unsupervised นอกจากนี้ยังไม่มี deployment, monitoring, feedback loop, การป้องกัน outcome leakage และผลส่งมอบที่ตรวจสอบย้อนกลับได้

### 2.2 Workflow กลางที่ปรับปรุงแล้ว

จึงปรับ Workflow ต้นฉบับเป็นกระบวนการ Data Science ทั่วไป 11 ขั้นใน `Workflow.md`:

1. Problem Definition
2. Data Gathering
3. Data Cleaning
4. Exploratory Data Analysis
5. Feature Engineering
6. Model Selection
7. Model Training
8. Model Evaluation
9. Model Deployment
10. Communicate Results
11. Monitor and Maintain

พร้อม Model Optimization Cycle ระหว่าง Steps 5–8 และ Feedback Loop กลับไป Step 2

Workflow กลางนี้ครบวงจรกว่าเดิม แต่ยังไม่ได้ระบุรายละเอียดเฉพาะของ Student Segmentation เช่น หน่วยวิเคราะห์หนึ่งแถวต่อนักศึกษา การห้าม outcome leakage วิธีประเมิน clustering ซึ่งไม่มี accuracy และการใช้ outcome หลังล็อกโมเดลเท่านั้น จึงสร้าง `agy_workflow.md` เพื่อแปลง Workflow กลางให้เป็น Workflow เฉพาะโครงการ

### 2.3 คำถามหลักของโครงการ

- นักศึกษามีรูปแบบพฤติกรรมการเรียนที่แตกต่างกันอย่างไร
- กลุ่มที่ค้นพบมีความเสถียรเมื่อเปลี่ยน initialization หรือ resample หรือไม่
- feature ที่ไม่ใช่ outcome ใดช่วยแยกกลุ่มมากที่สุด
- กลุ่มที่พบสามารถใช้ประกอบการวางแผนช่วยเหลือนักศึกษาอย่างไม่ตีตราได้อย่างไร

### 2.4 ทำไมเป็น Clustering ไม่ใช่ Classification

คำว่า “segmentation” ในงานนี้หมายถึงการแบ่งนักศึกษาออกเป็นกลุ่มที่ค้นพบจากพฤติกรรม จึงเป็น unsupervised learning และไม่มี target label สำหรับฝึกโมเดล ส่วน `certified`, `grade`, `explored` และ `incomplete_flag` เป็น outcome ที่ทราบภายหลัง หากนำมาใช้ระหว่าง clustering จะทำให้กลุ่มถูกออกแบบตามผลลัพธ์ ซึ่งขัดกับโจทย์ “ค้นพบกลุ่ม” และเกิด data leakage

ดังนั้นโครงการนี้จึงไม่รายงาน classification accuracy หรือ confusion matrix เพราะค่าดังกล่าวต้องมี true class label ส่วนคุณภาพ clustering ประเมินด้วย internal metrics, stability, interpretability, cluster sizes, sensitivity และ error/ambiguity analysis

---

## 3. ลำดับพรอมต์และการตัดสินใจที่เกิดขึ้น

### ระยะที่ 1: ปรับ Workflow ทีละขั้น

คำขอเริ่มต้นคือให้เพิ่มสิ่งที่ขาดจริง โดยคงโครงสร้างสั้นและอธิบายทีละข้อว่า “เพิ่มอะไร เพราะอะไร ช่วยอะไร” เพื่อประหยัดโทเคน จึงค่อย ๆ ปรับ:

- Problem Definition ให้มี objective, target outcome, task type และ success criteria
- Data Gathering ให้บันทึกแหล่งที่มา ขอบเขต และข้อจำกัด
- เพิ่ม Data Cleaning เป็นขั้นแยกจาก EDA
- EDA ให้ดู missingness, outliers, patterns, relationships, correlations และ important features
- Feature Engineering ให้สร้าง แปลง เลือก encode และ scale ตามความจำเป็น
- นำ Literature Review มารวมกับ Model Selection เพื่อให้การเลือกโมเดลมีเหตุผล
- แยก Model Training ออกจาก Model Evaluation
- เพิ่ม Model Optimization Cycle ระหว่าง Steps 5–8
- เพิ่ม Deployment, Communication, Monitoring และ Feedback Loop กลับไปเก็บข้อมูล

ผลของระยะนี้คือ `Workflow.md` เวอร์ชันกระบวนการทั่วไปที่กระชับและครบวงจร

### ระยะที่ 2: สร้าง Workflow เฉพาะ Student Segmentation

พรอมต์หลักที่ใช้เริ่มโครงการคือ:

```text
Read Workflow.md and create a concise, project-specific workflow named agy_workflow.md.

Project: Student Segmentation
Dataset source: https://www.kaggle.com/datasets/kanikanarang94/mooc-dataset
Data size: Approximately 500,000 raw records, 22 columns
Unit of analysis: One row per student
Goal: Discover meaningful student clusters for responsible student-support planning
Task type: Unsupervised learning
Constraint: Known outcomes may be used only for post-hoc validation and must not be
used as clustering features or for sampling.
```

สิ่งสำคัญที่พรอมต์นี้กำหนดคือประเภทงาน หน่วยวิเคราะห์ เป้าหมาย และข้อห้าม leakage แต่คำว่า “approximately 500,000” เป็นเพียงข้อมูลเบื้องต้น จึงต้องตรวจขนาดจริงจากไฟล์ ไม่ใช้เป็นค่าจริงในรายงาน

### ระยะที่ 3: แก้ Workflow ที่ตั้งสมมติฐานล่วงหน้า

ผลร่างแรกมีการเสนอ algorithm, persona และ intervention ก่อนตรวจข้อมูล จึงใช้คำสั่งแก้ไขสาระสำคัญดังนี้:

```text
Revise agy_workflow.md only.

- If sampling is needed, require justification, method, size, seed,
  representativeness, and limitations.
- Do not assume unavailable columns, derived features, algorithms, cluster counts,
  personas, or interventions before inspecting the data.
- Select the final clustering model using only internal metrics, stability, and
  interpretability.
- Lock the final model before post-hoc outcome validation. Outcomes must not influence
  feature engineering, sampling, model selection, tuning, or optimization.
- Distinguish raw records from the unknown number of unique students.
- Aggregate to one row per student before deciding whether sampling is needed.
```

ผลคือ `agy_workflow.md` กำหนดการตรวจข้อมูลก่อนตัดสินใจ ไม่บังคับจำนวน cluster หรือชื่อกลุ่มล่วงหน้า และแยก model lock ออกจาก post-hoc validation ชัดเจน

### ระยะที่ 4: ตรวจผลการรันครั้งแรก

เมื่อรันโครงการครั้งแรก พบประเด็นที่ต้องแก้จากการตรวจไฟล์จริงและ dashboard:

- ข้อมูลจริงคือ 416,921 records ไม่ใช่ 500,000 records
- จำนวน 335,650 คือ unique students หลัง aggregation ไม่ใช่ข้อมูลสูญหาย
- มีการบังคับ sample 50,000 คน ทั้งที่ EDA บนประชากรทั้งหมดทำได้
- การจัดการ `nplay_video=197757` เป็นศูนย์ยังไม่มีหลักฐานเพียงพอ
- บางขั้นใช้ค่าหรือ threshold ที่กำหนดล่วงหน้า เช่น PCA 80%, `k=2..8`, stability threshold และ PSI 0.25
- รายการโมเดลนับ K-Means และ MiniBatch K-Means คล้ายเป็นคนละแนวคิด ทั้งที่เป็น centroid family เดียวกัน
- dashboard มีตัวเลขและคำอธิบายบางส่วน hard-code และมี persona/intervention ที่อาจตีตรา
- monitoring จำลอง future cohort ทั้งที่ไม่มีข้อมูลอนาคตจริง
- deployment artifact มีความเสี่ยงโหลดไม่ได้จาก process ใหม่
- ยังไม่มีการตรวจ output ตาม Workflow อย่างเป็นระบบ

### ระยะที่ 5: แก้ Steps 6–7 และตรวจทั้งโครงการ

มีการขอแก้ Step 6–7 หลายรอบ เพื่อให้โมเดลหลากหลายจริง ไม่ซ้ำ family และไม่กำหนดค่าตามความคิดล่วงหน้า จากนั้นมีข้อกำหนดสำคัญว่าไม่ควรแก้เฉพาะ dashboard เพราะอาจารย์จะตรวจ Workflow และกระบวนการ จึงต้องแก้ Workflow-aligned pipeline แล้วรันสร้างผลใหม่

การแก้รอบสุดท้ายจึงครอบคลุม Steps 1–11 ไม่ใช่เพียงโมเดลหรือหน้ารายงาน

### ระยะที่ 6: ย้ายผลลัพธ์กลับไปโฟลเดอร์ส่งงาน

เนื่องจากพื้นที่แก้ไขทำงานอยู่ในโฟลเดอร์สำเนา จึงสำรองโฟลเดอร์เดิมเป็น `Mooc_CLI_original_before_fix` แล้วคัดลอกฉบับที่แก้เสร็จไปที่ `/Users/chingli/Desktop/Mooc_CLI` เพื่อให้อาจารย์ตรวจจากเครื่องได้

### ระยะที่ 7: Audit รอบสุดท้าย

หลังตรวจว่า Workflow กับงานตรงกัน พบว่างานมีไฟล์ครบ แต่ `run_project.py` เดิมตรวจเพียง 38 artifacts และยังไม่ครอบคลุมไฟล์ประกอบทุกประเภท จึงเพิ่มการตรวจ Workflow, source ทุก Step, quarantine, feature comparison, candidate models, EDA/evaluation figures, inference code, tests และ examples ปัจจุบันตรวจ **75 artifact requirements**

ระหว่าง audit ยังพบว่าคำอธิบาย Cluster ใช้คำว่า “Higher” กับ feature ที่จริงยังต่ำกว่าค่าเฉลี่ย เพียงแต่ติดลบน้อยที่สุด จึงแก้ logic ให้ตรวจเครื่องหมายของ standardized centroid ก่อนสร้างข้อความ หลังรันล่าสุด Cluster 0 ถูกอธิบายว่า **“All core features below average; lowest view rate”** ซึ่งตรงกับค่าจริงกว่า

---

## 4. เปรียบเทียบ Workflow กลางที่ปรับปรุงแล้วกับ Workflow ของโครงการ

| ขั้น | Workflow กลางที่ปรับปรุงแล้ว | สิ่งที่เพิ่มสำหรับโครงการนี้ | เหตุผล |
|---|---|---|---|
| 1 | Define problem/objective | unit of analysis, ethics, users, research questions, clustering success criteria | ป้องกันการเลือกโมเดลโดยไม่มีเป้าหมาย |
| 2 | Gather/load data | checksum, schema audit, unique-student count, field roles, physical outcome quarantine | ยืนยันแหล่งข้อมูลและป้องกัน leakage |
| 3 | Clean data | sentinel handling, uncertainty preservation, field-specific aggregation, count audit | ทำให้หนึ่งแถวแทนหนึ่งคนโดยไม่อ้างว่าข้อมูลหาย |
| 4 | EDA | full-population EDA และกฎว่าหาก sample ต้องมีเหตุผล ขนาด seed และ representativeness | ไม่เลือก sample แบบสะดวกหรือใช้ outcome ช่วย sample |
| 5 | Engineer features | behavior-only features, log transform, scaling, redundancy check, video sensitivity set | clustering ไวต่อ scale และ missingness |
| 6 | Select models | literature review, distinct model families, data-derived candidate k | ป้องกันโมเดลซ้ำและค่าที่ตั้งล่วงหน้า |
| 7 | Train/tune | deterministic sampling จากข้อจำกัดหน่วยความจำ, disjoint evaluation sample, resample stability | ทำให้เปรียบเทียบโมเดลขนาดใหญ่ได้อย่างทำซ้ำได้ |
| 8 | Evaluate | internal metrics หลายตัว, ambiguity, ablation, fairness, model lock ก่อน outcomes | clustering ไม่มี accuracy และต้องป้องกัน outcome influence |
| 5–8 | Optimization cycle | เก็บ hypothesis/configuration/result และห้ามย้อนกลับหลังดู outcomes | ป้องกันการ tune ตามผลลัพธ์โดยไม่รู้ตัว |
| 9 | Deploy | portable pipeline, schema validation, outcome rejection, examples และ tests | ทำให้โมเดลใช้กับข้อมูลใหม่อย่างสอดคล้อง |
| 10 | Communicate | self-contained HTML ที่อ่านค่าจาก artifacts และมี interactive explorer | ป้องกันตัวเลข hard-code และผลเก่าไม่ตรงโค้ด |
| 11 | Monitor | baseline-only จนมี future cohort จริง และ feedback loop กลับ Step 2 | ไม่สร้าง drift result ปลอม |

---

## 5. สิ่งที่แก้ในโค้ด: ก่อนแก้ → หลังแก้ → ผลที่ช่วย

### 5.1 การเริ่ม Workflow

**ก่อนแก้:** `run_project.py` เริ่มที่ Step 2 ไม่มี Step 1 ที่สร้างผลลัพธ์จริง และตรวจเพียงว่า script จบโดยไม่ error

**หลังแก้:** เพิ่ม `src/step1_problem_definition.py`, configuration, per-step logs, run manifest และ artifact verification

**ช่วย:** อาจารย์ตรวจย้อนกลับได้ว่าโจทย์ success criteria และข้อจำกัดถูกกำหนดก่อน modeling และทุกขั้นถูกรันตามลำดับ

### 5.2 Data provenance

**ก่อนแก้:** ใช้คำอธิบายข้อมูลประมาณ 500,000 records และไม่มีหลักฐาน checksum ที่ชัดเจนใน report

**หลังแก้:** คำนวณจากไฟล์จริง ได้ 416,921 records, 22 columns, 335,650 unique students, file size และ SHA-256

**ช่วย:** แยกข้อมูลประมาณการจากข้อมูลจริง และยืนยันได้ว่าใช้ไฟล์ใดในการวิเคราะห์

### 5.3 Outcome leakage

**ก่อนแก้:** มี outcome quarantine แล้ว แต่ manifest/report บางส่วนเปิดเผยสถิติ outcome ก่อน model lock และ dashboard มีค่าที่เขียนไว้ล่วงหน้า

**หลังแก้:** quarantine outcome เป็น Parquet แยกทางกายภาพ ไม่คำนวณ distribution ก่อน lock; Step 8 เขียน model checksum ก่อนอ่าน quarantine; assignments แยกจาก post-hoc output

**ช่วย:** outcome มีอิทธิพลต่อการเลือกโมเดลเป็นศูนย์ตามหลักการออกแบบ

### 5.4 Data cleaning และ `nplay_video`

**ก่อนแก้:** เปลี่ยนค่า `197757` เป็น 0 และตีความว่าไม่มีการดูวิดีโอ ทั้งที่ยังไม่มีหลักฐานว่าศูนย์คือความหมายที่ถูกต้อง

**หลังแก้:** เก็บเป็น missing และสร้างตัวบอก availability; video features ถูกใช้เฉพาะ sensitivity analysis เพราะ missing สูง ไม่อยู่ใน core clustering

**ช่วย:** ไม่เปลี่ยน “ไม่ทราบ” ให้กลายเป็น “ไม่ทำกิจกรรม” ซึ่งอาจสร้าง cluster เทียม

### 5.5 Missing age และวันที่ผิดปกติ

**ก่อนแก้:** มีการ impute อายุและแก้ค่าบางส่วนด้วยกฎที่อาจไม่มีหลักฐาน รวมถึง fallback การศึกษาเป็น Bachelor's

**หลังแก้:** เก็บ missing age และ date uncertainty ไว้ ไม่บังคับ category ที่ไม่ทราบ และบันทึก cleaning rules/audit

**ช่วย:** ป้องกันการสร้างข้อมูลประชากรที่ไม่ได้สังเกตจริง

### 5.6 416,921 เหลือ 335,650

**ก่อนแก้:** ตัวเลขหลัง cleaning ทำให้ดูเหมือนลบข้อมูลจำนวนมาก

**หลังแก้:** audit ระบุชัดว่า 416,921 records มี 335,650 unique students และ output มี 335,650 students ครบทุกคน

**ช่วย:** อธิบายได้ว่าการลดจำนวนแถวเกิดจาก aggregation หลาย records ของคนเดียว ไม่ใช่การทิ้งนักศึกษา

### 5.7 Sampling

**ก่อนแก้:** บังคับ sample 50,000 คนสำหรับ EDA

**หลังแก้:** EDA และ preprocessing ใช้ประชากรนักศึกษาทั้งหมด ส่วน model training ใช้ 23,168 คน และ metric evaluation ใช้ 5,792 คนจากข้อจำกัด pairwise-memory 256 MB มี random seed และ representativeness diagnostics จาก non-outcome features โมเดลสุดท้าย fit บน 335,650 คนทั้งหมด

**ช่วย:** ประหยัด computation ในจุดที่จำเป็นโดยไม่แอบอ้างว่า sample คือข้อมูลทั้งหมด และไม่เสียข้อมูลตอนสร้างโมเดลสุดท้าย

### 5.8 Feature engineering

**ก่อนแก้:** features บางส่วนซ้ำซ้อน ใช้ video โดยไม่จัดการ missing อย่างเหมาะสม และมีเส้น threshold PCA 80% ที่ตั้งไว้ล่วงหน้า

**หลังแก้:** core มี 8 behavior-only features ได้แก่:

1. `log_n_courses`
2. `view_rate`
3. `log_total_events`
4. `log_total_active_days`
5. `log_total_chapters`
6. `log_total_forum_posts`
7. `log_overall_span_days`
8. `log_event_intensity`

ใช้ `log1p` ลด skew และ scaling ทำให้ features อยู่ในสเกลเทียบกันได้ Demographics ไม่ใช้แบ่งกลุ่ม ส่วน video ถูกทดสอบเป็น sensitivity variant เท่านั้น

**ช่วย:** ลดการครอบงำจาก feature ที่สเกลใหญ่ ลด redundancy และลดความเสี่ยงเรื่อง fairness

### 5.9 Model selection

**ก่อนแก้:** มี `k=2..8` แบบ fixed, นับ K-Means/MiniBatch คล้ายคนละแนวคิด และมีรายงานค่าบางส่วนแบบ hard-code

**หลังแก้:** ใช้ข้อมูลและ literature เลือก 6 distinct families และ 29 configurations:

- Centroid: K-Means; MiniBatch เป็น scalability variant ไม่ได้นับเป็น family เพิ่ม
- Probabilistic: Gaussian Mixture
- CF-tree hierarchical: BIRCH
- Divisive hierarchical: Bisecting K-Means
- Agglomerative hierarchical: Ward
- Density-based: DBSCAN

จำนวน cluster ที่ทดสอบหลักคือ 4, 5, 6, 7 จาก empirical k-probe ไม่ใช่กำหนดให้ต้องได้ 4 ตั้งแต่ต้น

**ช่วย:** เปรียบเทียบแนวคิดของโมเดลที่ต่างกันจริงและอธิบายการเลือกได้

### 5.10 Model evaluation และ locking

**ก่อนแก้:** Step 8 มี fallback ที่สามารถสร้าง K-Means เองและมีคำอธิบาย persona ผูกกับผลลัพธ์

**หลังแก้:** Step 8 อ่าน provisional winner จากผล Step 6–7, ประเมินหลาย metrics, refit บนประชากรทั้งหมด, บันทึก checksum และ status `LOCKED` ก่อนอ่าน outcome

**ช่วย:** ไม่มีการเปลี่ยนโมเดลตาม outcome และตรวจสอบ model artifact ที่ใช้จริงได้

### 5.11 Error, sensitivity, ablation และ fairness

**ก่อนแก้:** มี analysis บางส่วนแต่ใช้ threshold หรือค่าที่กำหนดไว้และยังไม่เชื่อมกับผล final อย่างชัดเจน

**หลังแก้:** เพิ่ม silhouette diagnostics ราย cluster, negative-silhouette fraction, assignment ambiguity, feature-group ablation, permutation assignment importance และ demographic association เพื่อ human review

**ช่วย:** ไม่รายงานเพียงคะแนนรวม แต่แสดงว่าจุดใดของโมเดลยังไม่ชัดหรือไวต่อ features ใด

### 5.12 Deployment

**ก่อนแก้:** class ของโมเดลถูกผูกกับ execution context และมี output persona/support strategy ที่อาจใช้ไม่ได้หรือโหลดข้าม process ไม่สำเร็จ

**หลังแก้:** ย้าย class ไป module ที่ import ได้, เพิ่ม `predict_clusters.py`, input schema, outcome rejection, validation ของ dtype/null/range/duplicate, ให้ pipeline คำนวณ derived feature เอง, examples, model card และ automated tests

**ช่วย:** saved pipeline โหลดและ predict ใน Python process ใหม่ได้จริง และป้องกัน outcome หลุดเข้า inference

### 5.13 Dashboard

**ก่อนแก้:** HTML มีข้อความ ตัวเลข persona และ recommendation หลายส่วน hard-code เนื้อหาสำคัญบางส่วนขาด และค่าบางชุดไม่ตรงกับผลล่าสุด

**หลังแก้:** สร้าง dashboard จาก artifacts ล่าสุดโดยอัตโนมัติ มีหัวข้อ:

- Executive Overview
- Problem Definition & Research Questions
- Literature Review & Method Rationale
- Dataset Provenance & Quality
- Data Dictionary
- Descriptive Statistics & EDA
- Statistical Feature Screening
- Preprocessing & Feature Engineering
- Unsupervised Clustering Models
- Cluster Profiles & Visualizations
- Cluster-Defining Feature Contributions
- Error Analysis, Ablation & Sensitivity
- Post-Hoc Validation
- Interactive Student Scenario Explorer
- Monitoring
- Conclusions, Limitations & Next Steps

**ช่วย:** ลดความเสี่ยงที่ report จะไม่ตรงกับโค้ด และทำให้ผู้ฟังเห็นกระบวนการครบวงจร

### 5.14 Monitoring

**ก่อนแก้:** สร้าง future cohort จำลองและใช้ PSI threshold 0.25 เหมือนเป็นผล production จริง

**หลังแก้:** บันทึก baseline จากข้อมูลฝึก พร้อม schema, missingness, distribution, cluster share, assignment uncertainty, empirical outlier rate และ refit stability และระบุ `not_evaluated` เพราะยังไม่มี future cohort จริง

**ช่วย:** ไม่สร้างผล drift ที่ไม่มีข้อมูลสนับสนุน เมื่อมี cohort ใหม่จึงค่อยตรวจและตัดสิน retraining

### 5.15 การเก็บงานเดิม

**ก่อนแก้:** output เก่าอาจปะปนกับ output ใหม่

**หลังแก้:** ย้าย output เก่าที่ไม่ถูกใช้งานออกจาก active project ไป macOS Trash และเก็บเฉพาะ artifacts ที่ Workflow, report, deployment หรือการตรวจย้อนหลังใช้จริง

**ช่วย:** เปรียบเทียบก่อน–หลังได้และย้อนกลับได้หากจำเป็น

---

## 6. กระบวนการวิเคราะห์จริงตาม Steps 1–11

### Step 1 — Problem Definition

กำหนดวัตถุประสงค์ หน่วยวิเคราะห์ task type คำถามวิจัย ผู้ใช้ผลลัพธ์ success criteria และ ethical boundary ผลเก็บใน `data/processed/problem_definition.json`

### Step 2 — Data Gathering & Outcome Quarantine

อ่านไฟล์ raw ตรวจ dimensions, types, missingness, duplicate keys, unique students, file size และ SHA-256 จากนั้นแยก outcome พร้อม identifier ไป `data/quarantine/` และสร้าง non-outcome store

### Step 3 — Data Cleaning & Aggregation

จัดการ types, missingness, sentinel และ date uncertainty จากนั้น aggregate ตามความหมายของแต่ละตัวแปรให้หนึ่งแถวต่อนักศึกษา Audit ยืนยันว่า unique-student count ถูกเก็บครบ

### Step 4 — EDA

ใช้ประชากรนักศึกษาเต็มสำหรับ descriptive EDA และ feature screening วิเคราะห์ distributions, missingness, sparsity, outliers, categorical frequencies และ correlations รูปและตารางถูกเก็บแยกเป็น artifacts

### Step 5 — Feature Engineering

สร้าง behavior-only features, ใช้ log transformation กับตัวแปรเบ้, scale ตัวแปร และเปรียบเทียบ core กับ core-plus-video โดยไม่ใช้ outcome

### Step 6 — Model Selection

ทบทวน literature และพิจารณาขนาดข้อมูล geometry, scalability, deployability และสมมติฐานของโมเดล เพื่อสร้าง candidate families ที่ต่างกันจริง

### Step 7 — Training & Tuning

ใช้ deterministic random seed `612731450` ซึ่ง derive จาก checksum ของข้อมูล ใช้ training sample 23,168 และ disjoint metric sample 5,792 ตาม memory budget บันทึก runtime, failures, configurations และ stability

### Step 8 — Evaluation, Locking & Post-Hoc

จัดอันดับ deployable candidates แบบ equal-weight mean rank จาก Silhouette, Davies–Bouldin, Calinski–Harabasz และ resample ARI แล้ว refit winner บนข้อมูลทั้งหมด บันทึก checksum ก่อนอ่าน outcome หลังจากนั้นจึงทำ Chi-square/Cramér's V และ Kruskal–Wallis/Epsilon-squared เพื่ออธิบายความแตกต่างภายหลัง

### Step 9 — Deployment

รวม preprocessing และ locked clustering model เป็น pipeline เดียว เพิ่ม schema validation, outcome guard, batch prediction, example input/output และ tests

### Step 10 — Communication

สร้าง self-contained HTML report จาก CSV, JSON, model metadata และ figures ที่บันทึกไว้ ไม่กรอกค่าผลลัพธ์ด้วยมือ มี interactive scenario explorer ที่ใช้ scaler และ centroids ของโมเดลจริง

### Step 11 — Monitoring

สร้าง training baseline และ monitoring rules แต่ยังไม่รายงาน drift เพราะไม่มี future cohort จริง หากภายหลังพบ drift หรือ cluster degradation จึงย้อนกลับ Step 2 ตาม Feedback Loop

---

## 7. ผลลัพธ์จริงและวิธีตีความ

### 7.1 ข้อมูล

| รายการ | ผลจริง |
|---|---:|
| Raw records | 416,921 |
| Columns | 22 |
| Unique students | 335,650 |
| Exact duplicate rows | 0 |
| Records ต่อ student โดยเฉลี่ย | 1.2421 |
| Final-fit population | 335,650 |

### 7.2 โมเดลสุดท้าย

| รายการ | ผลจริง |
|---|---:|
| Algorithm | K-Means |
| Number of clusters | 4 |
| Silhouette | 0.3737 |
| Davies–Bouldin | 0.9858 |
| Calinski–Harabasz | 3,193.55 |
| Resample stability ARI | 0.9803 |
| Outcomes accessed before lock | False |

### 7.3 ขนาดและลักษณะกลุ่ม

| Cluster | นักศึกษา | สัดส่วน | คำอธิบายจาก non-outcome behavior |
|---|---:|---:|---|
| 0 | 96,906 | 28.87% | core behavioral features ต่ำกว่าค่าเฉลี่ยทั้งหมด โดย view rate ต่ำที่สุด |
| 1 | 78,687 | 23.44% | active days และ activity volume สูง แต่ forum posts ต่ำ |
| 2 | 154,822 | 46.13% | view rate สูงกว่าเฉลี่ย แต่ active days ต่ำกว่าเฉลี่ย |
| 3 | 5,235 | 1.56% | forum contribution และ activity สูง เป็นกลุ่มขนาดเล็ก |

ชื่อเหล่านี้เป็นคำอธิบายเชิงพฤติกรรม ไม่ใช่การตัดสินความสามารถ ไม่ควรเปลี่ยนเป็นชื่อที่ตีตรา เช่น “เด็กไม่ตั้งใจ” หรือ “ผู้ล้มเหลว”

### 7.4 Post-hoc validation

ผลลัพธ์ต่อไปนี้ถูกดูหลัง model lock เท่านั้นและ **ไม่ได้ใช้เลือกโมเดล**:

| Outcome | Test | Effect size |
|---|---|---:|
| Any certified | Chi-square / Cramér's V | 0.3598 |
| Any explored | Chi-square / Cramér's V | 0.4912 |
| Certification rate | Kruskal–Wallis / Epsilon-squared | 0.1293 |
| Mean grade | Kruskal–Wallis / Epsilon-squared | 0.3793 |
| Incomplete rate | Kruskal–Wallis / Epsilon-squared | 0.0341 |

ความหมายคือ cluster ที่สร้างจากพฤติกรรมมีความแตกต่างด้าน outcome ภายหลังในระดับต่างกัน แต่ไม่ได้พิสูจน์เหตุและผล และไม่ควรนำไปใช้ตัดสินนักศึกษาเป็นรายบุคคล

### 7.5 Feature contribution

Permutation assignment importance วัดว่าการสลับค่าของ feature ทำให้ assignment เปลี่ยนมากเพียงใด โดย top features คือ:

1. `view_rate` — mean ARI loss 0.3622
2. `log_total_active_days` — 0.2799
3. `log_total_events` — 0.2390
4. `log_total_chapters` — 0.2375
5. `log_overall_span_days` — 0.1960

นี่ไม่ใช่ causal importance แต่เป็นความไวของ cluster assignment ต่อ feature

### 7.6 จุดที่โมเดลยังไม่สมบูรณ์

- Silhouette 0.3737 แสดงการแยกกลุ่มระดับปานกลาง ไม่ใช่กลุ่มที่แยกขาดทั้งหมด
- Cluster 1 มี negative silhouette 13.89% ใน evaluation sample แปลว่าสมาชิกบางส่วนอยู่ใกล้กลุ่มอื่นและควรตีความด้วยความระมัดระวัง
- Cluster 3 มีเพียง 1.56% แม้ไม่ใช่ noise แต่ต้องติดตามความเสถียรเมื่อมี cohort ใหม่
- Ablation ทำให้ assignment agreement เปลี่ยน โดยเฉพาะเมื่อตัด participation breadth หรือ activity volume แสดงว่าโครงสร้างกลุ่มขึ้นกับกลุ่ม feature เหล่านี้จริง
- Demographics ไม่ได้ใช้ clustering แต่ post-analysis พบ association ขนาดเล็ก ได้แก่ Cramér's V ประมาณ 0.0318 สำหรับ gender, 0.0307 สำหรับ education และ 0.0812 สำหรับ country จึงควรมี human fairness review
- ยังไม่มีข้อมูล cohort ในอนาคต จึงยังสรุป production drift ไม่ได้

---

## 8. ผลออกมาดีหรือไม่

คำตอบที่เหมาะสมคือ **ผลมีคุณภาพเพียงพอสำหรับ exploratory student segmentation และมีหลักฐานด้านความเสถียรสูง แต่ไม่ควรอ้างว่าเป็นโมเดลสมบูรณ์หรือใช้ตัดสินนักศึกษาโดยอัตโนมัติ**

เหตุผลที่ถือว่าดี:

- ARI 0.9803 แสดงว่า assignment เสถียรมากเมื่อ resample
- เลือกโมเดลจากหลาย metrics ไม่ใช่คะแนนเดียว
- final model fit กับนักศึกษาทั้งหมด
- outcome ไม่รั่วเข้า model selection
- มี sensitivity, ablation, ambiguity, fairness และ deployment tests
- ผล post-hoc แสดงว่ากลุ่มมี educational relevance หลังล็อกโมเดล
- ผลสร้างซ้ำได้และมี checksum/logs

เหตุผลที่ยังต้องระวัง:

- clustering ไม่มี ground-truth accuracy
- Silhouette อยู่ระดับปานกลาง
- กลุ่มเล็กและ boundary cases ต้องติดตาม
- outcome difference ไม่ใช่ causal effect
- ข้อมูลมาจากบริบท MOOC ชุดหนึ่ง อาจ generalize ไปสถาบันอื่นไม่ได้ทันที
- monitoring ยังเป็น baseline เพราะไม่มี future cohort

---

## 9. ไฟล์ที่เพิ่ม แก้ ย้าย และเหตุผล

### ไฟล์ที่เพิ่มสำคัญ

- `src/step1_problem_definition.py` — ทำ Step 1 ให้รันได้จริง
- `src/feature_transformer.py` — เก็บ preprocessing class ใน module ที่ import ได้
- `src/deployment.py` — เก็บ deployment class แบบ portable
- `src/predict_clusters.py` — inference command สำหรับข้อมูลใหม่
- `src/generate_report.py` — สร้าง dashboard จาก artifacts
- `config/project_config.json` — configuration ที่ทำซ้ำได้
- `CHANGELOG.md` — บันทึกการแก้โครงการ
- `PRESENTATION_GUIDE_TH.md` — เอกสารสรุปสำหรับพรีเซนต์
- `data/processed/*` — provenance, dictionary, rules, audit, features และ matrices
- `outputs/research/*` — literature review และ model rationale
- `outputs/tables/*` — EDA, models, diagnostics, ablation, fairness และ post-hoc
- `models/candidates/*` — candidate model artifacts
- `models/final/*` — locked model, pipeline, schema และ model card
- `monitoring/*` — baseline, report, history และ decision
- `examples/*` และ `tests/*` — ตัวอย่างและ verification tests

### ไฟล์ที่แก้สำคัญ

- `run_project.py` — เพิ่ม Step 1, module execution, logs, manifest และ 75 artifact requirements
- `src/step2_data_gathering.py` — provenance และ strict quarantine
- `src/step3_data_cleaning.py` — แก้ sentinel/missing/date/aggregation logic
- `src/step4_eda.py` — full-population EDA และ truthful sampling report
- `src/step5_feature_engineering.py` — core features และ sensitivity comparison
- `src/step6_7_model_training.py` — literature, distinct families, data-derived k, sampling, metrics และ stability
- `src/step8_evaluation_and_posthoc.py` — model locking, full refit, diagnostics, fairness และ post-hoc separation
- `src/pipeline.py` — portable deployment packaging
- `src/step11_monitoring.py` — ลบ simulated drift/fixed threshold และเพิ่ม schema, uncertainty, outlier และ stability ที่คำนวณจริง
- `tests/test_pipeline.py` — ตรวจ prediction, aggregation, leakage, schema และ fresh-process loading

### ไฟล์ที่ย้ายออกจาก active project

legacy outputs, summary ที่ซ้ำ, radar figure ที่รายงานไม่ใช้ และ bytecode caches ถูกย้ายไป macOS Trash เพื่อไม่ให้ปะปนกับหลักฐานปัจจุบันและยังสามารถกู้คืนได้

### สิ่งที่ไม่ได้ทำ

- ไม่แก้ raw dataset
- ไม่สร้าง synthetic records
- ไม่แต่ง model scores
- ไม่ใช้ outcome เป็น clustering features หรือ sampling variables
- ไม่ใช้ accuracy/confusion matrix กับงาน clustering
- ไม่สร้าง persona หรือ intervention แบบตายตัวก่อนดูข้อมูล
- ไม่อ้างว่ามี production drift เมื่อยังไม่มี future cohort

---

## 10. โครงร่างสไลด์และสคริปต์พูด

### Slide 1 — Project Overview

**บนสไลด์:** Student Segmentation for Responsible Support Planning; dataset; unsupervised learning; one row per student

**พูด:** “งานนี้ไม่ได้ทำนายผลการเรียน แต่ค้นหากลุ่มพฤติกรรมของนักศึกษาใน MOOC เพื่อช่วยวางแผนการสนับสนุน โดย outcome จะถูกเก็บไว้ตรวจภายหลังเท่านั้น”

### Slide 2 — Why the Workflow Was Adapted

**บนสไลด์:** General workflow → project-specific controls

**พูด:** “Workflow อาจารย์ให้โครงครบวงจรอยู่แล้ว ฉันเพิ่มรายละเอียดที่จำเป็นสำหรับ clustering ได้แก่ หน่วยวิเคราะห์ outcome quarantine, internal metrics, model locking และ feedback loop ที่ทำซ้ำได้”

### Slide 3 — Dataset Provenance and Unit of Analysis

**บนสไลด์:** 416,921 records; 22 columns; 335,650 students; SHA-256

**พูด:** “ตัวเลข 500,000 เป็นประมาณการจากหน้า dataset แต่ไฟล์ที่ใช้จริงมี 416,921 records หนึ่งคนมีหลาย records จึง aggregate เป็น 335,650 students โดยไม่ได้สูญเสียนักศึกษา”

### Slide 4 — Leakage Prevention

**บนสไลด์:** outcomes quarantined → model selected/locked → post-hoc only

**พูด:** “certified, grade, incomplete และ explored ถูกแยกทางกายภาพก่อน EDA และ modeling โมเดลถูกเลือกจาก non-outcome internal evidence แล้วบันทึก checksum ก่อนเปิด outcome”

### Slide 5 — Cleaning and EDA

**บนสไลด์:** no student loss; preserve uncertainty; full-population EDA

**พูด:** “ฉันไม่เปลี่ยนค่าที่ไม่ทราบเป็นศูนย์โดยไม่มีหลักฐาน ค่า video sentinel ถูกเก็บเป็น missing และอายุที่หายยังคงเป็น missing EDA ใช้ประชากรนักศึกษาทั้งหมด”

### Slide 6 — Feature Engineering

**บนสไลด์:** 8 behavior-only core features; log1p; scaling; video sensitivity only

**พูด:** “ใช้ features พฤติกรรม 8 ตัว ลด skew ด้วย log1p และ scale เพื่อไม่ให้ feature ที่มีค่ามากครอบงำ demographics ไม่ถูกใช้สร้างกลุ่ม และ video แยกเป็น sensitivity analysis เพราะ missing สูง”

### Slide 7 — Model Selection and Training

**บนสไลด์:** 6 families; 29 configurations; k shortlist 4, 5, 6 และ 12; deterministic seed

**พูด:** “ฉันไม่นับ MiniBatch K-Means เป็น family ใหม่ แต่เปรียบเทียบแนวคิดที่ต่างกันจริง 6 families รวม 29 configurations ช่วง k มาจาก empirical probe และ sample มาจากข้อจำกัด memory พร้อม representativeness checks”

### Slide 8 — Final Model and Quality

**บนสไลด์:** K-Means k=4; Silhouette .3737; DB .9858; CH 3,193.55; ARI .9803

**พูด:** “K-Means 4 กลุ่มชนะจาก mean rank ของ 4 criteria ไม่ใช่คะแนนเดียว และ refit กับนักศึกษาทั้งหมด จุดเด่นคือ stability สูง ส่วน separation อยู่ระดับปานกลาง จึงไม่อ้างว่ากลุ่มแยกขาดสมบูรณ์”

### Slide 9 — Cluster Profiles

**บนสไลด์:** ตาราง 4 clusters พร้อมขนาดและ neutral descriptors

**พูด:** “ใช้ชื่อ Cluster 0–3 และคำอธิบายจากค่าพฤติกรรมจริง ไม่ใช้ชื่อที่ตีตรา กลุ่ม 3 มีขนาดเล็ก 1.56% จึงเป็นกลุ่มที่ต้องติดตามความเสถียร”

### Slide 10 — Validation and Limitations

**บนสไลด์:** post-hoc effect sizes; ambiguity; fairness; no causality

**พูด:** “หลังล็อกโมเดล outcome ต่างกันระหว่างกลุ่ม แต่เป็น post-hoc association ไม่ใช่เหตุและผล นอกจากนี้ Cluster 1 มี boundary cases และ demographics แม้ไม่ได้ใช้ฝึกก็ยังต้องตรวจ fairness”

### Slide 11 — Deployment and Monitoring

**บนสไลด์:** portable pipeline; leakage/schema tests; baseline-only monitoring

**พูด:** “โมเดลมี preprocessing และ prediction workflow เดียวกัน โหลดใน process ใหม่ได้ มี test ป้องกัน outcome และ column ผิด ส่วน monitoring ยังไม่สร้าง drift result เพราะยังไม่มี cohort อนาคตจริง”

### Slide 12 — Reproducibility and Conclusion

**บนสไลด์:** `python run_project.py`; 12/12 stages; 75 requirements; HTML dashboard

**พูด:** “งานทั้งหมดรันซ้ำได้จากคำสั่งเดียว มี logs, checksums และตรวจ 75 artifact requirements ผลเหมาะกับ exploratory support planning แต่ไม่ใช้ตัดสินหรือให้โทษนักศึกษาอัตโนมัติ”

---

## 11. คำถามที่อาจารย์อาจถามและคำตอบ

### ทำไมข้อมูล 416,921 เหลือ 335,650?

เพราะ 416,921 คือจำนวน course-level records แต่หน่วยวิเคราะห์คือหนึ่งแถวต่อนักศึกษา จึง aggregate records ของคนเดียวกัน เหลือนักศึกษาไม่ซ้ำ 335,650 คน Audit ยืนยันว่าไม่มี unique student สูญหาย

### ทำไมไม่ใช้ข้อมูลทั้งหมดตอนเปรียบเทียบโมเดล?

EDA และ preprocessing ใช้ข้อมูลทั้งหมด แต่บาง internal metrics เช่น Silhouette ต้องคำนวณ pairwise distances ซึ่งใช้หน่วยความจำสูง Sample size จึงคำนวณจาก memory budget 256 MB มี seed และ representativeness checks โมเดลสุดท้าย refit กับนักศึกษาทั้งหมด

### ทำไมไม่มี accuracy หรือ confusion matrix?

เพราะ clustering ไม่มี true label และไม่ได้ทำนาย class การใช้ accuracy/confusion matrix จะเปลี่ยนโจทย์เป็น classification คุณภาพจึงวัดด้วย Silhouette, Davies–Bouldin, Calinski–Harabasz, stability และ diagnostics

### ทำไมเลือก K-Means?

ไม่ได้เลือกเพราะคุ้นเคย แต่เพราะมี mean rank ดีที่สุดจาก 4 non-outcome criteria, deploy ได้, stability สูง และตีความได้ หลังเลือกจึง refit บนประชากรทั้งหมด

### ทำไมได้ 4 clusters?

ไม่ได้กำหนด 4 ล่วงหน้า Empirical probe สร้าง shortlist 4–7 จากนั้นทุก configuration ถูกเปรียบเทียบด้วยกฎเดียวกัน K-Means k=4 ให้ balance ดีที่สุดตาม selection rule

### Outcome ถูกใช้ตอนไหน?

ใช้หลัง model lock เท่านั้นเพื่อ post-hoc validation ไม่ใช้ใน cleaning decision, sampling, feature engineering, tuning หรือ model selection

### ผลถือว่าดีแค่ไหน?

Stability สูงมากที่ ARI 0.9803 แต่ separation ปานกลางที่ Silhouette 0.3737 จึงเหมาะกับ exploratory segmentation ไม่ใช่การตัดสินบุคคลแบบเด็ดขาด

### Cluster 3 เล็กเกินไปหรือไม่?

มี 1.56% จึงต้องรายงานและ monitor แต่ไม่ควรลบทิ้งเพียงเพราะเล็ก เพราะมีรูปแบบพฤติกรรมที่ต่างชัด โดยเฉพาะ forum activity การตัดสินต้องดู stability และ cohort ใหม่ร่วมด้วย

### ทำไมไม่ใช้เพศ ประเทศ หรือการศึกษาเป็น features?

เป้าหมายคือ behavioral segmentation และลดความเสี่ยงการแบ่งกลุ่มตาม demographic identity ตัวแปรเหล่านี้จึงใช้เฉพาะ fairness diagnostics หลังสร้างกลุ่ม

### ทำไมไม่ตั้งชื่อ persona?

persona อาจตีตราหรือสื่อความหมายเกินหลักฐาน จึงใช้ neutral descriptors ที่สร้างจาก measured profile และแยกข้อเสนอเชิงนโยบายออกจากข้อเท็จจริง

### Monitoring ทำงานหรือยัง?

ระบบ baseline พร้อมแล้ว แต่สถานะเป็น `not_evaluated` เพราะยังไม่มี future cohort จริง เมื่อมีข้อมูลช่วงถัดไปจึงคำนวณ drift และตัดสิน retraining

---

## 12. วิธีสาธิตงาน

เข้าโฟลเดอร์:

```bash
cd '/Users/chingli/Desktop/Mooc_CLI'
```

รัน Workflow ทั้งหมด:

```bash
python run_project.py
```

ผลที่ควรเห็น:

```text
COMPLETE — 75 artifact requirements verified
```

เปิด dashboard:

```bash
open reports/student_segmentation_report.html
```

ไฟล์หลักที่ควรเปิดให้อาจารย์ดู:

- `Workflow.md` — Workflow กลาง 11 ขั้นที่ปรับปรุงจากต้นฉบับ
- `agy_workflow.md` — Workflow เฉพาะโครงการ
- `CHANGELOG.md` — ประวัติการแก้
- `outputs/reproducibility/run_manifest.json` — ผลการรันแต่ละขั้น
- `outputs/reproducibility/artifact_check.json` — หลักฐานว่า output ครบ
- `models/final/model_lock.json` — หลักฐาน model lock และ metrics
- `reports/student_segmentation_report.html` — dashboard สุดท้าย

---

## 13. ประโยคสรุปปิดการนำเสนอ

“โครงการนี้ปรับ Workflow Data Science ทั่วไปให้เหมาะกับ unsupervised student segmentation โดยตรวจข้อมูลจริง เปลี่ยนหน่วยวิเคราะห์เป็นหนึ่งแถวต่อนักศึกษา ป้องกัน outcome leakage เปรียบเทียบโมเดลหลาย family ล็อกโมเดลก่อน post-hoc validation และสร้าง deployment/dashboard/monitoring ที่รันซ้ำได้ ผลคือ 4 กลุ่มที่มี stability สูงและมีความหมายเชิงพฤติกรรม แต่ยังตีความอย่างระมัดระวังเพราะ separation อยู่ระดับปานกลาง ไม่มี causal conclusion และยังต้องตรวจด้วย future cohort ก่อนใช้งานจริง”
