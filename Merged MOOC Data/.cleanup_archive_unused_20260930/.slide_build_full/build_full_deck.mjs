import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const SKILL_DIR = '/Users/chingli/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const RUNTIME_PYTHON = '/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const workspaceDir = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data';
const TMP_DIR = path.join(workspaceDir, '.slide_build_full');
const FINAL_PPTX = path.join(workspaceDir, 'reports', 'MOOC_Student_Analytics_Full_Results_Deck_TH.pptx');
const root = workspaceDir;
const sup = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Sup';
const un = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Un';

const { resolvePresentationFont, finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')).href);
const font = resolvePresentationFont({ fontFamily: 'Arial' });
const pres = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const blue = '#004A73';
const gray = '#666666';
const light = '#F3F7FA';
const orange = '#D97924';
const green = '#2D7F5E';

function addShape(slide, x, y, w, h, fill = 'none', line = 'none') {
  return slide.shapes.add({ geometry: 'rect', position: { left: x, top: y, width: w, height: h }, fill, line: { fill: line, width: line === 'none' ? 0 : 1 } });
}
function addText(slide, text, x, y, w, h, opts = {}) {
  const t = slide.shapes.add({ geometry: 'textbox', position: { left: x, top: y, width: w, height: h }, fill: 'none', line: { fill: 'none', width: 0 } });
  t.text = text;
  t.text.style = { typeface: font, fontSize: opts.size ?? 22, bold: opts.bold ?? false, color: opts.color ?? '#222222', italic: opts.italic ?? false, autoFit: 'shrinkText' };
  return t;
}
function title(slide, main, sub = '') {
  addShape(slide, 74, 42, 6, 86, blue, blue);
  addText(slide, main, 105, 42, 1080, 58, { size: 38, bold: true, color: blue });
  if (sub) addText(slide, sub, 108, 103, 1040, 35, { size: 20, color: gray });
}
function footer(slide, txt = 'MOOC Student Analytics | HarvardX-MITx learner behavior pipeline') {
  addText(slide, txt, 80, 676, 920, 24, { size: 12, color: '#7A7A7A', italic: true });
}
async function addImage(slide, relOrAbs, x, y, w, h, alt, fit = 'contain') {
  const p = path.isAbsolute(relOrAbs) ? relOrAbs : path.join(root, relOrAbs);
  const blob = await fs.readFile(p);
  slide.images.add({ blob, contentType: 'image/png', alt, fit, position: { left: x, top: y, width: w, height: h } });
}
function bullets(slide, items, x, y, w, lineH = 32, size = 19) {
  items.forEach((it, i) => addText(slide, `• ${it}`, x, y + i * lineH, w, lineH + 6, { size, color: '#222222' }));
}
function metric(slide, label, value, x, y, w = 230, color = blue) {
  addText(slide, value, x, y, w, 42, { size: 34, bold: true, color });
  addText(slide, label, x, y + 43, w, 42, { size: 15, color: gray });
}
function table(slide, values, x, y, w, h, widths) {
  const tb = slide.tables.add({ rows: values.length, columns: values[0].length, left: x, top: y, width: w, height: h, values, columnWidths: widths });
  try {
    tb.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: values[0].length }).assign({ fill: blue, textStyle: { typeface: font, fontSize: 14, bold: true, color: '#FFFFFF' } });
    tb.cells.block({ row: 1, column: 0, rowCount: values.length - 1, columnCount: values[0].length }).assign({ textStyle: { typeface: font, fontSize: 13, color: '#222222' }, borders: { style: 'solid', fill: '#D9E3EA', width: 1 } });
  } catch {}
  return tb;
}

// 1
{
 const s = pres.slides.add(); s.background.fill = '#FFFFFF';
 addShape(s, 90, 54, 7, 120, blue, blue);
 addText(s, 'MOOC Student Analytics', 125, 60, 980, 58, { size: 46, bold: true, color: blue });
 addText(s, 'Merged learner behavior, segmentation, supervised prediction, deep learning and LLM evidence', 128, 123, 980, 38, { size: 22, color: gray });
 await addImage(s, 'outputs/figures/tracks/all_tracks_summary_comparison.png', 190, 205, 900, 330, 'All track model comparison');
 addText(s, 'สไลด์นี้เล่างานทั้งหมดตั้งแต่รวมข้อมูล ทำความสะอาด EDA เลือก K สร้าง persona ทำนาย certification และเปรียบเทียบโมเดลทุก track ด้วยผลจริงจากไฟล์งาน', 150, 570, 980, 52, { size: 22, color: '#333333' });
 footer(s, 'Prepared from current Merged MOOC Data, Sup and Un project outputs');
}
// 2
{
 const s = pres.slides.add(); s.background.fill = '#FFFFFF'; title(s, 'Agenda and evidence map', 'เล่าตาม pipeline จริง ไม่ใช่แค่ผลลัพธ์สุดท้าย');
 const vals = [['Part', 'What the slides show'], ['1. Data foundation', 'แหล่งข้อมูล, grain, merge logic, cleaning audit'], ['2. EDA', 'distribution, missingness, sparsity, correlation, outliers, video quality'], ['3. Unsupervised', 'K selection, model family, persona size, radar, PCA, posthoc outcome'], ['4. Supervised', 'split, candidate models, confusion matrix, ROC/PR, errors, feature importance'], ['5. Deep and LLM', 'MLP comparison, Gemini full test, Ollama pilot, provider status'], ['6. Recommendation', 'ผลหลัง merged, limitation, deployment and monitoring']];
 table(s, vals, 125, 170, 1030, 360, [210, 820]);
 addText(s, 'หลักฐานที่ใช้: CSV/JSON audit logs, output tables, PNG figures, dashboard reports และ slide/PDF reference เฉพาะด้านรูปแบบการเล่าเรื่อง', 140, 575, 1000, 50, { size: 20, color: '#333333' }); footer(s);
}
// 3
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Problem definition','โจทย์หลักคือเข้าใจพฤติกรรมผู้เรียนและทำนายผลลัพธ์การเรียนจากข้อมูล MOOC ขนาดใหญ่');
 bullets(s,[
  'Unit of analysis หลักหลัง merge คือหนึ่งแถวต่อ learner ที่รวมพฤติกรรมข้าม course-run อย่างมี audit trail',
  'Unsupervised track ใช้เพื่อหา persona หรือกลุ่มพฤติกรรมโดยไม่ใช้ target เป็นตัวนำ',
  'Supervised track ใช้ทำนาย certified/completion outcome ด้วย split ที่กัน leakage',
  'Deep and LLM track ใช้เปรียบเทียบวิธีที่ซับซ้อนกว่า tabular ML และอธิบายขอบเขตการใช้งานจริง'
 ],150,185,980,45,22);
 metric(s,'Raw harmonized rows','755,144',150,450); metric(s,'Unique learners','446,766',410,450,230,green); metric(s,'Course-run rows if preserved','624,674',680,450,300,orange); metric(s,'Final Un K','5',1010,450,120,blue);
 footer(s);
}
//4
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Merged data foundation','การ merge ใหม่ทำให้เห็นทั้งภาพ learner-level และ course-run-level ชัดขึ้น');
 const vals=[['Metric','Current value','Meaning'],['Raw harmonized rows','755,144','ข้อมูลตั้งต้นหลังรวมแหล่งข้อมูล'],['Unique students','446,766','จำนวนผู้เรียนไม่ซ้ำ'],['Student-course enrollments','575,060','key เดิมหลัง clean'],['Course-run enrollments','624,674','จำนวนที่ควรรักษาเมื่อแยก offering/run'],['Collapsed multi-run groups','49,614','กลุ่มที่ key เดิมรวม course-run เข้าด้วยกัน']];
 table(s, vals, 95,165,1090,310,[300,220,570]);
 addText(s,'หลัง recheck พบว่า key แบบ userid + course อาจทำให้ course-run บางส่วนถูก collapse จึงต้องรายงาน caveat นี้บน dashboard/slide และแยกการตีความ learner-level ออกจาก enrollment-level',120,515,1040,78,{size:22,color:'#333333'});
 footer(s,'Source: outputs/reproducibility/data_reclean_audit_summary.json');
}
//5
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Data cleaning audit','ขั้นตอนทำความสะอาดข้อมูลถูกบันทึกเป็น issue, decision และจำนวน record ที่กระทบ');
 const vals=[['Issue','Decision','Affected'],['Source-first cleaning','Clean each source before reconciliation','755,144'],['Cross-source overlap','Official-source-first non-null coalescing','180,084'],['Video sentinel','Convert 197757 to missing before merge','255,528'],['Invalid age','Convert invalid age to missing','745'],['Reversed dates','Swap valid inverted date pairs','1,846'],['Outcome consistency','Quarantine contradictions for supervised eligibility','78']];
 table(s, vals, 70,160,1140,400,[250,690,160]);
 addText(s,'ประเด็นสำคัญ: การ clean ไม่ได้ลบข้อมูลทิ้งแบบง่าย ๆ แต่แยก invalid/sentinel/quarantine เพื่อให้ downstream track ใช้ข้อมูลถูกประเภทและลด leakage',100,590,1050,44,{size:20,color:'#333333'}); footer(s,'Source: outputs/tables/cleaning_summary.csv');
}
//6
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Missingness and zero profile','ตรวจ missing, zero และ sparsity ก่อนสรุปพฤติกรรมผู้เรียน');
 await addImage(s,'outputs/figures/eda/zero_missing_outlier_profile.png',105,155,1070,430,'Zero missing outlier profile');
 addText(s,'กราฟนี้ใช้ตรวจว่าคอลัมน์ใดเป็น missing จริง คอลัมน์ใดมีค่า 0 ตามธรรมชาติ และคอลัมน์ใดเสี่ยงต่อ outlier ก่อนนำไปทำ feature engineering',135,600,1010,42,{size:19,color:'#333333'}); footer(s);
}
//7
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Behavior distributions','พฤติกรรมผู้เรียนมี skew สูง จึงต้องใช้ transformation และ robust features');
 await addImage(s,'outputs/figures/eda/full_distributions.png',85,150,1110,430,'Full distributions');
 addText(s,'distribution ของ events, active days, chapters และ video activity ไม่สมมาตร ผู้เรียนส่วนใหญ่กิจกรรมน้อย แต่มีผู้เรียนกลุ่มเล็กที่ active สูงมาก',125,600,1030,42,{size:19,color:'#333333'}); footer(s);
}
//8
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Correlation and relationships','ตรวจความสัมพันธ์ของ feature เพื่อลด feature ซ้ำและเลือก feature สำคัญ');
 await addImage(s,'outputs/figures/eda/correlation_matrix.png',125,150,1000,430,'Correlation matrix');
 addText(s,'correlation ช่วยบอกว่าพฤติกรรมบางชุดซ้ำกัน เช่น activity, chapter progress และ video engagement จึงควรใช้ feature screening ก่อนเข้าโมเดล',135,600,1010,42,{size:19,color:'#333333'}); footer(s);
}
//9
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Outliers and video quality','แยก outlier เชิงกิจกรรมและคุณภาพ video ก่อนตีความ segment');
 await addImage(s,'outputs/figures/eda/activity_outlier_diagnostics.png',70,150,560,400,'Activity outlier diagnostics');
 await addImage(s,'outputs/figures/eda/video_quality_diagnostics.png',650,150,560,400,'Video quality diagnostics');
 addText(s,'outlier ไม่ได้แปลว่าข้อมูลผิดเสมอไป ใน MOOC ผู้เรียน active สูงมากอาจเป็นกลุ่มที่มีความหมาย ส่วน video sentinel ต้องแปลงเป็น missing ก่อนวิเคราะห์',95,585,1080,48,{size:19,color:'#333333'}); footer(s);
}
//10
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Why merged data improved the analysis','merged pipeline ทำให้ผลลัพธ์ตีความได้ครบกว่าแยก Sup/Un แบบเดิม');
 const vals=[['Improvement','Before risk','After merge/recheck'],['Data grain','อาจปน learner, course และ course-run','แยก learner-level, student-course และ course-run audit'],['Video fields','sentinel 197757 อาจถูกตีความเป็นค่าจริง','convert เป็น missing ก่อน merge'],['Outcomes','contradictions เสี่ยงปน supervised labels','quarantine inconsistent outcomes'],['EDA','ดูแยกบาง track','รวม data quality, behavior, outcome, segment และ model comparison'],['Model story','ผลกระจายหลายโฟลเดอร์','เล่าเป็น pipeline เดียวพร้อมตารางเปรียบเทียบ']];
 table(s,vals,70,155,1140,420,[230,430,480]);
 addText(s,'ผลที่ดีขึ้นหลักคือความน่าเชื่อถือและ traceability ไม่ใช่แค่คะแนนโมเดลสูงขึ้น เพราะเรารู้ว่าแต่ละค่ามาจาก grain ไหนและผ่าน cleaning rule อะไร',90,605,1100,44,{size:19,color:'#333333'}); footer(s);
}
//11
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Unsupervised K selection','เลือก K ด้วยหลาย metric ไม่ใช้ elbow เพียงตัวเดียว');
 await addImage(s,'outputs/figures/tracks/multi_metric_k_selection_gap.png',95,145,1090,430,'Multi metric K selection gap');
 addText(s,'ใน merged dashboard ชุดล่าสุดใช้ six-metric composite และ gap evidence เพื่ออธิบายทิศทาง metric แต่ Un track หลักรายงาน Final K = 5 จาก gap one-SE บน sample 12,000',115,595,1050,48,{size:19,color:'#333333'}); footer(s,'Sources: outputs/tables/k_selection_decision.csv and Un/outputs/tables/k_selection_metrics.csv');
}
//12
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'K selection metrics table','ค่า K ต้องอ่านตามทิศทาง metric ไม่ใช่ดูตัวเลขแบบเดียวกันทุกกราฟ');
 const vals=[['Metric','Direction','Best / selected evidence'],['Silhouette','Higher is better','K=2 highest, but too coarse'],['Davies-Bouldin','Lower is better','K=3 in merged audit'],['Calinski-Harabasz','Higher is better','K=5 in merged audit'],['Gap statistic','Higher with one-SE rule','K=5 in Un final track'],['Stability ARI/NMI','Higher is better','Checks robustness, not final answer alone']];
 table(s,vals,100,160,1080,350,[260,300,520]);
 addText(s,'สไลด์นี้แก้ปัญหาที่เคยสับสนเรื่องลูกศร metric: แต่ละ metric มีทิศทางต่างกัน และบาง metric เช่น inertia เป็น monotonic จึงต้องใช้ bend หรือ composite rule',120,555,1040,70,{size:21,color:'#333333'}); footer(s);
}
//13
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Unsupervised model family comparison','ทดลองหลาย family ก่อนล็อกโมเดล ไม่เลือกจาก K อย่างเดียว');
 await addImage(s, path.join(un,'outputs/figures/modeling/model_comparison.png'),100,145,1080,420,'Un model comparison');
 addText(s,'K-Means K=5 ให้ balance ระหว่าง silhouette, Davies-Bouldin, Calinski-Harabasz และ stability ดีที่สุดในตารางเปรียบเทียบหลักของ Un track',125,590,1030,46,{size:19,color:'#333333'}); footer(s,'Source: Un/outputs/tables/unsupervised_model_comparison.csv');
}
//14
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Persona size and behavior radar','Final Un track แบ่งผู้เรียนเป็น 5 persona ตาม pattern พฤติกรรม');
 await addImage(s,path.join(un,'outputs/figures/evaluation/persona_cluster_donut.png'),90,150,500,395,'Persona donut');
 await addImage(s,path.join(un,'outputs/figures/evaluation/persona_behavior_radar.png'),630,150,560,395,'Persona radar');
 addText(s,'Cluster มีสัดส่วนประมาณ 13.8%, 18.5%, 16.5%, 29.1% และ 22.1% ทำให้ตีความเป็น persona ได้สมดุลกว่าการแบ่งที่กลุ่มหนึ่งใหญ่เกินไป',105,585,1060,46,{size:19,color:'#333333'}); footer(s,'Source: Un/outputs/tables/cluster_profiles.csv');
}
//15
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'PCA projection and posthoc outcomes','ตรวจว่า segment แยกเชิงพฤติกรรมและสัมพันธ์กับ outcome จริงหรือไม่');
 await addImage(s,path.join(un,'outputs/figures/evaluation/cluster_projection_pca_3d.png'),70,145,550,410,'PCA 3D');
 await addImage(s,path.join(un,'outputs/figures/evaluation/posthoc_outcomes_by_cluster.png'),650,145,560,410,'Posthoc outcomes');
 addText(s,'posthoc validation ไม่ได้ใช้เลือกโมเดล แต่ใช้ตรวจว่ากลุ่มพฤติกรรมมีความสัมพันธ์กับ certification, mean grade และ incomplete rate อย่างมีนัยสำคัญ',95,585,1080,46,{size:19,color:'#333333'}); footer(s);
}
//16
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Supervised prediction setup','Supervised track ทำนาย certified learner ด้วย split ที่กัน leakage');
 const vals=[['Item','Value'],['Student-level rows','335,650'],['Certified completers','13,881'],['Completion rate','4.136%'],['Train / validation / test','234,955 / 50,347 / 50,348'],['Test positives','2,082'],['Anti-leakage rule','split before fitting any pipeline']];
 table(s,vals,150,155,980,385,[430,550]);
 addText(s,'class imbalance สูงมาก จึงใช้ ROC-AUC, PR-AUC, recall, precision, F1 และ threshold optimization แทนการดู accuracy อย่างเดียว',155,580,970,50,{size:21,color:'#333333'}); footer(s,'Sources: Sup/data/processed/cleaning_audit.json and Sup/outputs/reproducibility/split_summary.json');
}
//17
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Supervised EDA','ก่อนเทรนโมเดลต้องดู class imbalance และพฤติกรรมของ completer/non-completer');
 await addImage(s,path.join(sup,'outputs/figures/eda/class_imbalance.png'),85,150,520,400,'Class imbalance');
 await addImage(s,path.join(sup,'outputs/figures/eda/activity_distributions.png'),640,150,560,400,'Activity distributions');
 addText(s,'ผู้เรียน certified มีสัดส่วนเพียง 4.136% แต่มี activity ต่างจากกลุ่มอื่นชัดเจน ทำให้ threshold และ PR-AUC สำคัญมากกว่าความแม่นยำรวม',105,585,1060,46,{size:19,color:'#333333'}); footer(s);
}
//18
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Supervised model comparison','Random Forest เป็น champion จาก balance ของ PR-AUC, F1 และ recall');
 await addImage(s,'outputs/figures/tracks/supervised_model_comparison.png',90,150,1100,410,'Supervised comparison');
 const vals=[['Champion','ROC-AUC','PR-AUC','F1','Precision','Recall','Accuracy'],['Random Forest d15','0.9933','0.8476','0.7889','0.7422','0.8420','0.9814']];
 table(s,vals,120,590,1040,78,[210,120,120,120,150,130,150]); footer(s,'Source: Sup/outputs/tables/test_evaluation_summary.csv');
}
//19
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Confusion matrix and error analysis','ผลลัพธ์ต้องอ่านร่วมกับ false negative และ false positive');
 await addImage(s,'outputs/figures/tracks/supervised_confusion_matrices_comparison.png',70,145,570,410,'Confusion matrices comparison');
 const vals=[['Type','Count','Mean events','Mean active days','Mean prob'],['Correct','49,410','408.0','5.95','0.0566'],['False negative','329','1,676.7','21.16','0.5860'],['False positive','609','4,322.7','42.51','0.9389']];
 table(s,vals,670,165,540,285,[160,80,115,115,100]);
 addText(s,'False negatives คือ completer ที่ถูกพลาด ส่วน false positives คือผู้เรียน active สูงแต่ไม่ certified จึงควรใช้โมเดลเพื่อจัดลำดับ intervention ไม่ใช่ตัดสินผลลัพธ์แบบเด็ดขาด',665,485,545,90,{size:18,color:'#333333'}); footer(s,'Source: Sup/outputs/tables/error_analysis.csv');
}
//20
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'ROC, PR and calibration','ตรวจความสามารถแยกกลุ่มและความน่าเชื่อถือของ probability');
 await addImage(s,path.join(sup,'outputs/figures/evaluation/roc_curves.png'),55,145,380,390,'ROC curves');
 await addImage(s,path.join(sup,'outputs/figures/evaluation/pr_curves.png'),450,145,380,390,'PR curves');
 await addImage(s,path.join(sup,'outputs/figures/evaluation/calibration_curves.png'),845,145,380,390,'Calibration curves');
 addText(s,'ROC-AUC สูงมาก แต่เพราะ positive class น้อย PR curve และ calibration สำคัญต่อการใช้งานจริง โดยเฉพาะการเลือก threshold ที่ลด missed completer',95,585,1080,46,{size:19,color:'#333333'}); footer(s);
}
//21
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Feature importance','โมเดลพึ่งพา feature เชิง activity และ course progress เป็นหลัก');
 await addImage(s,path.join(sup,'outputs/figures/evaluation/feature_importance.png'),120,145,1040,410,'Feature importance');
 addText(s,'feature สำคัญสูงสุดคือ max_chapters_single_course, total_chapters, total_active_days, overall_span_days, max_events_single_course และ total_events',130,585,1020,46,{size:19,color:'#333333'}); footer(s,'Source: Sup/outputs/tables/feature_importance.csv');
}
//22
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Deep learning track','MLP ให้ผลใกล้ supervised champion แต่ยังต้องดู runtime และการอธิบายผล');
 await addImage(s,'outputs/figures/tracks/deep_model_comparison.png',90,145,670,410,'Deep model comparison');
 const vals=[['Selected deep model','PR-AUC','ROC-AUC','F1','Recall','Precision'],['MLP 128,64','0.8388','0.9947','0.7917','0.8421','0.7470']];
 table(s,vals,790,190,390,120,[160,70,70,60,60,70]);
 addText(s,'Deep model ชนะบาง metric เช่น ROC-AUC และ F1 ใกล้เคียงมาก แต่ Random Forest ยังตีความง่ายกว่าและมี feature importance ที่ตรงกับพฤติกรรมผู้เรียน',790,350,390,125,{size:18,color:'#333333'}); footer(s,'Source: outputs/tables/deep_learning_model_comparison.csv');
}
//23
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'LLM and transformer track','LLM ใช้แปลงพฤติกรรมผู้เรียนเป็นข้อความแล้วประเมินผ่านโมเดล AI ที่รันได้จริง');
 await addImage(s,'outputs/figures/tracks/llm_behavior_embedding_projection.png',75,145,540,400,'LLM embedding projection');
 await addImage(s,'outputs/figures/tracks/llm_text_model_comparison.png',650,145,540,400,'LLM model comparison');
 addText(s,'ผลจริงที่ครบคือ Gemini full test 1,800 students: Accuracy 0.9628, Precision 0.4615, Recall 0.9310, F1 0.6171, ROC-AUC 0.9810 ส่วน OpenAI/Claude simulated ถูก quarantine ไม่ใช้เป็นผลจริง',90,585,1100,54,{size:18,color:'#333333'}); footer(s,'Source: outputs/tables/llm_comparative_model_comparison.csv and llm_api_provider_status.csv');
}
//24
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'All-track comparison','เปรียบเทียบผลจาก Un, Sup, Deep และ LLM ใน narrative เดียว');
 await addImage(s,'outputs/figures/tracks/all_tracks_summary_comparison.png',90,145,1100,400,'All tracks summary');
 addText(s,'ผลรวมชี้ว่า tabular supervised และ deep learning เหมาะกับ prediction ส่วน unsupervised เหมาะกับ persona และ LLM เหมาะกับการอธิบายพฤติกรรมจากข้อความ แต่มีข้อจำกัดเรื่อง cost, API และ comparability',105,585,1060,52,{size:18,color:'#333333'}); footer(s);
}
//25
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Deployment and monitoring','ผลลัพธ์ถูกเตรียมเป็น pipeline, schema และ dashboard เพื่อตรวจซ้ำได้');
 const vals=[['Artifact','Purpose'],['student_segmentation_report.html','dashboard รวมผล data, EDA, Un/Sup/Deep/LLM'],['clustering_pipeline.joblib','deployment artifact สำหรับ segment'],['supervised_model.joblib','deployment artifact สำหรับ risk prediction'],['input_schema.json','ตรวจ schema ก่อน inference'],['monitoring PSI report','ตรวจ drift และ trigger retraining']];
 table(s,vals,120,165,1040,330,[350,690]);
 addText(s,'ควร monitor distribution ของ feature, persona share, recall/F1 และ data drift เพราะ MOOC behavior อาจเปลี่ยนตาม course offering และ platform design',140,545,1000,70,{size:21,color:'#333333'}); footer(s);
}
//26
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Main findings','ข้อสรุปที่ใช้เล่าในห้องนำเสนอ');
 bullets(s,[
  'Merged pipeline ทำให้ grain และ cleaning audit ชัดขึ้น โดยเฉพาะ course-run issue ที่ต้องแยกจาก learner-level analysis',
  'EDA ยืนยันว่า behavior data มี skew, sparsity และ outlier สูง จึงต้องใช้ robust transformation และ feature screening',
  'Unsupervised track สรุป persona 5 กลุ่มจาก gap one-SE และตรวจด้วย radar, PCA และ posthoc outcomes',
  'Supervised Random Forest ทำงานดีที่สุดโดยรวมในงาน prediction: ROC-AUC 0.9933, PR-AUC 0.8476, F1 0.7889',
  'Deep MLP ให้ผลใกล้เคียง supervised champion ส่วน LLM/Gemini recall สูงแต่ precision ต่ำกว่า จึงเหมาะเป็น evidence track เพิ่มเติม'
 ],120,165,1040,55,21); footer(s);
}
//27
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Limitations','ข้อจำกัดที่ต้องพูดให้ชัดเพื่อไม่ให้ตีความเกินข้อมูล');
 bullets(s,[
  'course-run key ต้องรายงาน caveat เพราะ student-course key เดิม collapse multi-run groups 49,614 กลุ่ม',
  'Unsupervised K ไม่มีคำตอบจาก metric เดียว ต้องระบุ rule ที่ใช้เลือกและเก็บ metric อื่นเป็น audit evidence',
  'positive class ของ supervised มีเพียงประมาณ 4.136% จึงห้ามสรุปจาก accuracy อย่างเดียว',
  'LLM provider ไม่เท่ากันทั้งหมด เพราะมีเพียง Gemini full test ที่เป็น API run ครบ ส่วน OpenAI/Claude simulated ถูก quarantine',
  'ผล posthoc ของ cluster ใช้อธิบายความสัมพันธ์กับ outcome ไม่ได้ใช้เลือก cluster เพื่อหลีกเลี่ยง target leakage'
 ],120,165,1040,58,21); footer(s);
}
//28
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Final recommendation','รายงานผลเป็น workflow เดียวและแยกหน้าที่ของแต่ละ model family');
 const vals=[['Decision area','Recommended use'],['Persona and segment insight','Use Un K=5 persona with radar/PCA/posthoc validation'],['Student risk prediction','Use Random Forest supervised pipeline as primary model'],['Deep learning','Keep MLP as benchmark and future candidate'],['LLM','Use Gemini result as explanatory/comparative evidence, not primary deployment model'],['Data governance','Keep course-run caveat and cleaning audit visible in dashboard and slides']];
 table(s,vals,115,160,1050,360,[330,720]);
 addText(s,'ประโยคสรุป: งาน merged ทำให้ผลเล่าได้น่าเชื่อถือขึ้น เพราะเห็น data quality, grain, EDA, model evidence และ limitation อยู่ใน pipeline เดียวกัน',130,565,1020,62,{size:22,bold:true,color:blue}); footer(s);
}

await fs.mkdir(path.join(workspaceDir, '.codex-finalizer'), { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const candidatePath = path.join(workspaceDir, '.codex-finalizer', 'candidate_full_results_deck.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
const requirements = { explicitTotalSlideCount: 28, requiredNativeTableOwnerSlides: [2,4,5,10,12,16,18,19,22,25,28], requiredNativeChartOwnerSlides: [], requiredEmbeddedWorkbookChartOwnerSlides: [] };
const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit', ...requirements.requiredNativeTableOwnerSlides.flatMap(n => ['--require-native-table-slide', String(n)])],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy: { basis: 'design', families: [font] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(workspaceDir, '.codex-finalizer', 'MOOC_Student_Analytics_Full_Results_Deck_TH.validation.json')
});
console.log(JSON.stringify(result, null, 2));
