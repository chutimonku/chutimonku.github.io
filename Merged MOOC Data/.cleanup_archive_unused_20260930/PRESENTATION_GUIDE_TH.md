# คู่มือพรีเซ็น: Multi-Track MOOC Student Analytics

## 1. โจทย์และข้อมูล

- ใช้ข้อมูล 2 ไฟล์: HarvardX ทางการจาก Harvard Dataverse และไฟล์ HarvardX–MITx ที่โครงการได้รับจาก Kaggle
- ข้อมูลดิบรวม 755,144 แถว → ตัดรายการลงทะเบียนซ้ำข้ามไฟล์เหลือ 609,637 แถว → รวมเป็นหนึ่งแถวต่อนักศึกษาเหลือ 446,766 คน
- เก็บทั้งไฟล์สะอาดระดับการลงทะเบียนและระดับนักศึกษา จึงยังตรวจสอบที่มาของจำนวนมากกว่า 500,000 แถวได้

## 2. ทำความสะอาดอะไร

- ตรวจทุกคอลัมน์: ชนิดข้อมูล ค่าว่าง จำนวนค่าที่แตกต่าง สถิติ และจำนวนของแต่ละ class/category
- แปลง video sentinel `197757` จำนวน 255,528 แถวเป็น missing พร้อมสร้างตัวบ่งชี้
- อายุผิดช่วง 678 แถวเป็น missing; ข้อมูลเพศ/การศึกษา/ประเทศที่หายเป็น `Unknown`
- วันที่เริ่ม–สิ้นสุดกลับด้าน 1,231 แถวถูกสลับอย่างมีหลักฐาน ไม่ลบนักศึกษา
- พบผลลัพธ์ขัดกัน 1 แถวที่ certified แต่ grade ต่ำกว่า 0.50: เก็บไว้ใน quality audit และตัดเฉพาะจาก label ที่ใช้ฝึก Supervised

## 3. แยกงานเป็นหลาย Track เพราะอะไร

- ข้อมูลสะอาดชุดเดียวใช้เป็น master แต่แต่ละโจทย์ต้องใช้ฟีเจอร์และกฎป้องกัน leakage ต่างกัน
- Traditional และ Deep Learning เลือกฟีเจอร์พฤติกรรมจากข้อมูลสะอาดหลัง merge ด้วยกฎ coverage, variance, redundancy และ leakage
- Supervised เลือกฟีเจอร์จากข้อมูลสะอาดหลัง merge เพื่อทำนายการได้ certificate โดยรับ label หลังขอบเขตการแบ่งข้อมูล
- Generative LLM ใช้เป็น track สำหรับสร้างคำอธิบายสองภาษาจาก artifact จริง ไม่ใช้แทนโมเดลทำนายหรือโมเดลแบ่งกลุ่ม

## 4. Traditional Unsupervised

- รอบนี้ระบบเลือกฟีเจอร์พฤติกรรม 4 ตัวจากข้อมูล clean+merge: forum posts, chapters, active days และ events แบบ percentile ภายในวิชา
- การใช้ percentile ภายในวิชาเดียวกันช่วยลดความต่างของโอกาสทำกิจกรรมระหว่างวิชา ก่อนเฉลี่ยต่อคน
- ทดลอง `k=2–10` และ 7 ตระกูลวิธี: K-Means, MiniBatch K-Means, GMM, BIRCH, HAC, DBSCAN และ approximate K-Medoids
- กราฟ elbow พบจุดหักศอกที่ `k=4`; รอบสุดท้ายจึงเทียบ `k=3–5` ด้วย Silhouette, Davies–Bouldin, Calinski–Harabasz, resample ARI, ขนาดกลุ่ม และ runtime
- ผลจริงเลือก **MiniBatch K-Means, k=3**: Silhouette 0.3426, Davies–Bouldin 0.8333, Calinski–Harabasz 13,195.97, ARI 0.5575 และ runtime 0.0050 วินาทีในรอบนี้
- Radar เป็นภาพ normalize เพื่อช่วยมอง ไม่ใช้แทนค่าจริงในตาราง; PCA 3 มิติใช้แสดงภาพ ไม่ใช่ฟีเจอร์โมเดล

## 5. Deep Learning

- ใช้ฟีเจอร์พฤติกรรมที่เลือกจากข้อมูลจริง 4 ตัวเดิม ผ่าน Autoencoder 4 → 3 มิติ 30 epochs
- เปรียบเทียบ K-Means และ GMM ตั้งแต่ `k=2–10`
- ผลจริงเลือก **Autoencoder + GMM, k=2**: Silhouette 0.9699, Davies–Bouldin 0.3621, Calinski–Harabasz 25,121.33 และ ARI 1.0000; ใช้เป็นแนวทางเปรียบเทียบ representation ไม่ใช่แทนที่ Traditional โดยอัตโนมัติ

## 6. Supervised Learning

- เป้าหมายคือ “นักศึกษาเคยได้ certificate ในรายการลงทะเบียนที่ label ผ่านการตรวจหรือไม่” อัตรากลุ่มบวก 3.18% จึงไม่ควรดู Accuracy อย่างเดียว
- ฟีเจอร์ต้นทางรอบนี้ 34 ตัว เลือกจากข้อมูลสะอาดหลัง merge โดยตัด identifier, วันที่ดิบ, quality/provenance flags, คอลัมน์ missing สูง, categorical กว้างเกินไป และ numeric ที่ซ้ำกันมากเกินไป
- หลัง imputation, scaling, binary handling และ one-hot encoding ได้ 75 transformed features
- แบ่ง 70/15/15: ฝึก 312,732 คน, validation 67,014 คน และ test 67,015 คน
- เปรียบเทียบ baseline, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosted Trees, Linear SVM และ Gaussian Naive Bayes
- ผลจริงเลือก **Gradient Boosted Trees** จาก PR-AUC 0.8747; ROC-AUC 0.9954, Accuracy 98.79%, Balanced Accuracy 91.09%, Precision 79.91%, Recall 82.87%, F1 81.36% และเวลาฝึก 10.46 วินาทีในการรันล่าสุด
- Threshold 0.9546 เลือกจาก validation แล้วรายงานผลครั้งสุดท้ายบน test set เท่านั้น

## 7. Generative LLM

- ใช้เป็น track สำหรับสื่อสารผล ไม่ใช่โมเดลทำนายหรือโมเดลแบ่งกลุ่ม
- Input คือ artifact จริง เช่น `unsupervised_cluster_profiles.csv`, `unsupervised_model_comparison.csv`, `supervised_model_comparison.csv` และ `supervised_track_manifest.json`
- Output คือ `llm_generated_summaries.csv` จำนวน 4 แถว: สรุป 3 clusters และสรุปโมเดล Supervised
- ไม่ใส่ Accuracy, PR-AUC หรือ Silhouette ให้ LLM เพราะไม่ใช่งาน classification หรือ clustering

## 8. Deployment, Dashboard และ Monitoring

- บันทึก preprocessing และโมเดลของแต่ละ Track ใน `models/tracks/` พร้อม input contract, model cards, ตัวอย่าง input/output และ runtime
- Dashboard มี 5 ปุ่ม: Overview, Traditional Unsupervised, Deep Learning, Supervised Learning และ LLM; สลับไทย/อังกฤษ ซ่อน sidebar และเปลี่ยน Segment ได้
- Segment เป็นการกรองเพื่ออธิบายผล ไม่ได้เทรนโมเดลใหม่และไม่เปลี่ยน cluster
- Monitoring สถานะ `Not Evaluated` เพราะยังไม่มี future cohort จริง แต่มี baseline ของ schema, missingness, ฟีเจอร์, สัดส่วนกลุ่ม และค่าทำนายแล้ว

## 9. ข้อจำกัดที่ต้องพูด

- Runtime ขึ้นกับเครื่องและรอบการรัน จึงใช้เปรียบเทียบภายใต้สภาพแวดล้อมเดียวกันเท่านั้น
- Clustering ไม่มี Accuracy แบบ Classification; ต้องใช้คุณภาพภายใน ความคงที่ และความหมายของกลุ่ม
- Accuracy สูงของ Supervised ส่วนหนึ่งมาจาก class imbalance จึงใช้ PR-AUC, Balanced Accuracy, Recall และ F1 ร่วมด้วย
- ผลเป็นความสัมพันธ์จาก log บนแพลตฟอร์ม ไม่พิสูจน์เหตุและผล และไม่ควรใช้ลงโทษหรือปิดโอกาสนักศึกษา
