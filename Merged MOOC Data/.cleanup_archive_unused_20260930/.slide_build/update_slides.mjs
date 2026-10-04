import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const workspaceDir = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data';
const sourcePath = path.join(workspaceDir, 'reports/MOOC_Student_Analytics_Presentation_TH.pptx');
const finalPath = path.join(workspaceDir, 'reports/MOOC_Student_Analytics_Presentation_TH_revised_latest.pptx');
const SKILL_DIR = '/Users/chingli/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const RUNTIME_PYTHON = '/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';

const { finalizePresentation, resolvePresentationFont, applyPresentationChartFont } = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')).href);
const family = resolvePresentationFont();
const p = await PresentationFile.importPptx(await FileBlob.load(sourcePath));

function setText(id, text, style={}) {
  const sh = p.resolve(id);
  sh.text.set(text);
  if (Object.keys(style).length) sh.text.style = style;
}
function setNotes(id, text) {
  const nt = p.resolve(id);
  nt.text = text;
}

// Slide 4: data cleaning recheck
setText('sh/3ihk3et8', 'Raw harmonized rows: 755,144\nCurrent cleaned enrollments: 575,060 using userid_DI + course_id\nCourse-run count if preserved: 624,674\nRecheck found 49,614 student-course groups collapsed across multiple course-runs\nStudent-level unit remains consistent: 446,766 unique learners', { fontSize: 24, color: '#263238', autoFit: 'shrinkText' });
setText('sh/ih8ju9sn', 'Cleaning caveat: use course-run key before making enrollment-level or course-offering claims.', { fontSize: 22, bold: true, color: '#B63232', autoFit: 'shrinkText' });
setNotes('nt/jyx0ra1s', 'Source: outputs/reproducibility/data_cleaning_recheck_report.md and outputs/reproducibility/data_reclean_audit_summary.json. The student-level unit is consistent, but the current student-course deduplication collapses some course-run contexts.');
try {
  const chart = p.resolve('ch/pwrm5kvq');
  const s0 = chart.series.getItemAt(0);
  s0.categories = ['Raw rows', 'Student-course', 'Course-run', 'Students'];
  s0.values = [755144, 575060, 624674, 446766];
  s0.name = 'Record count';
  chart.apply({ dataLabels: { showValue: true, position: 'outEnd' }, hasLegend: false, yAxis: { numberFormatCode: '#,##0' } });
  applyPresentationChartFont(chart, { fontFamily: family });
} catch (e) {
  console.error('slide4 chart update skipped', e.message);
}

// Slide 9: K decision
setText('sh/bih4na5w', 'Final K = 3\n\nPrimary rule: Gap statistic one-standard-error → K=3\nCorroborating index: Davies-Bouldin minimum → K=3\nAudit evidence: Elbow K=4, CH K=5, Silhouette K=2', { fontSize: 20, color: '#263238', autoFit: 'shrinkText' });
setText('sh/ah8nu54b', 'Final clustering result reports K=3. Other K values remain diagnostic evidence, not the final decision rule.', { fontSize: 22, bold: true, color: '#0B1F3A', autoFit: 'shrinkText' });
setNotes('nt/udsvah03', 'Source: outputs/tables/k_metric_direction_recheck.csv and outputs/reproducibility/k_metric_direction_recheck_summary.json. Final K=3 because Gap Statistic one-standard-error rule and Davies-Bouldin both select K=3.');
try {
  const chart = p.resolve('ch/to3qhgje');
  const s0 = chart.series.getItemAt(0);
  s0.categories = ['K=2', 'K=3', 'K=4', 'K=5', 'K=6'];
  s0.values = [0, 2, 1, 1, 0];
  s0.name = 'Decision evidence count';
  chart.apply({ dataLabels: { showValue: true, position: 'outEnd' }, hasLegend: false, yAxis: { title: 'Supporting criteria' } });
  applyPresentationChartFont(chart, { fontFamily: family });
} catch (e) {
  console.error('slide9 chart update skipped', e.message);
}

// Slide 10: Persona proportions from latest clustering
setText('sh/cbu58j2h', 'Persona ผู้เรียนจาก Final K=3', { fontSize: 34, bold: true, color: '#0B1F3A', autoFit: 'shrinkText' });
setText('sh/725onyl4', 'Cluster 0  กิจกรรมทั่วไปส่วนใหญ่\n441,385 คน (98.80%)\n\nCluster 1  กิจกรรมสูงมาก\n3,137 คน (0.70%)\n\nCluster 2  กิจกรรมสูงเฉพาะด้าน\n2,244 คน (0.50%)', { fontSize: 20, color: '#263238', autoFit: 'shrinkText' });
setText('sh/m1cnetkj', 'ข้อควรอ่าน: สัดส่วนกลุ่มไม่สมดุลมาก จึงควรตีความเป็น activity-extreme segmentation มากกว่า persona ที่สมดุลเท่ากัน', { fontSize: 20, bold: true, color: '#B63232', autoFit: 'shrinkText' });
setNotes('nt/m90b6t0r', 'Source: outputs/tables/unsupervised_cluster_profiles.csv. Latest cluster shares: 98.80%, 0.70%, and 0.50% of 446,766 learners.');
try {
  const chart = p.resolve('ch/twj21wjy');
  const s0 = chart.series.getItemAt(0);
  s0.categories = ['Cluster 0', 'Cluster 1', 'Cluster 2'];
  s0.values = [98.80, 0.70, 0.50];
  s0.name = 'Share (%)';
  chart.apply({ dataLabels: { showValue: true, position: 'outEnd' }, hasLegend: false, yAxis: { numberFormatCode: '0.00' } });
  applyPresentationChartFont(chart, { fontFamily: family });
} catch (e) {
  console.error('slide10 chart update skipped', e.message);
}

// Slide 14: final recommendations
setText('sh/kfidonqx', '• Final unsupervised K = 3 from Gap Statistic and Davies-Bouldin\n• Student-level unit is valid: 446,766 unique learners\n• Enrollment cleaning needs course-run key review before course-level claims\n• Persona shares are highly imbalanced, so interpret clusters as activity extremes\n• LLM results remain separate until full comparable model runs finish', { fontSize: 22, color: '#263238', autoFit: 'shrinkText' });
setText('sh/kre1k3y9', 'ข้อเสนอหลัก: รายงาน Final K=3 พร้อม data-cleaning caveat และใช้ dashboard audit tables เป็นหลักฐานประกอบการนำเสนอ', { fontSize: 20, bold: true, color: '#0B1F3A', autoFit: 'shrinkText' });
setNotes('nt/6lsnupw7', 'Summary reflects latest dashboard artifacts: final K=3, data cleaning recheck, and latest cluster profile. LLM track remains separated where full comparable results are not complete.');

// Add slide 15: data-cleaning recheck table
function addHeader(slide, section, title) {
  slide.background.fill = '#FFFFFF';
  slide.shapes.add({ geometry: 'rect', position: { left: 0, top: 0, width: 1280, height: 12 }, fill: '#0B1F3A', line: { width: 0, fill: '#0B1F3A' } });
  const s = slide.shapes.add({ geometry: 'textbox', position: { left: 72, top: 35, width: 760, height: 24 }, fill: 'none', line: { width: 0, fill: 'none' } });
  s.text.set(section); s.text.style = { fontSize: 18, bold: true, color: '#B63232' };
  const t = slide.shapes.add({ geometry: 'textbox', position: { left: 72, top: 63, width: 1136, height: 58 }, fill: 'none', line: { width: 0, fill: 'none' } });
  t.text.set(title); t.text.style = { fontSize: 34, bold: true, color: '#0B1F3A' };
  slide.shapes.add({ geometry: 'rect', position: { left: 72, top: 132, width: 1136, height: 2 }, fill: '#0B1F3A', line: { width: 0, fill: '#0B1F3A' } });
}
function styleTable(table) {
  table.borders.assign({ style: 'solid', fill: '#D9E2EC', width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: table.cols }).assign({ fill: '#0B1F3A', textStyle: { color: '#FFFFFF', bold: true, fontSize: 14 } });
  table.cells.block({ row: 1, column: 0, rowCount: table.rows - 1, columnCount: table.cols }).assign({ textStyle: { color: '#263238', fontSize: 13 } });
}
const s15 = p.slides.add();
addHeader(s15, 'LATEST AUDIT', 'Data cleaning recheck');
const body15 = s15.shapes.add({ geometry: 'textbox', position: { left: 80, top: 155, width: 1080, height: 70 }, fill: 'none', line: { width: 0, fill: 'none' } });
body15.text.set('Student-level data remains consistent, but the current student-course deduplication collapses some course-run contexts. Use this caveat when presenting enrollment-level results.');
body15.text.style = { fontSize: 22, color: '#263238', autoFit: 'shrinkText' };
const table15 = s15.tables.add({ rows: 6, columns: 3, left: 95, top: 245, width: 1090, height: 290, values: [
  ['Audit item', 'Latest value', 'Interpretation'],
  ['Raw harmonized rows', '755,144', 'Two source files combined'],
  ['Student-course cleaned rows', '575,060', 'Current cleaned enrollment file'],
  ['Course-run rows if preserved', '624,674', 'Recommended key for course-run claims'],
  ['Collapsed multi-run groups', '49,614', 'Student-course key merges multiple run contexts'],
  ['Missing course offerings', '3', 'CS50x Fall, Spring, Summer collapse into Unknown'],
]});
styleTable(table15);
s15.speakerNotes.text = 'Source: outputs/reproducibility/data_cleaning_recheck_report.md and data_reclean_audit_summary.json.';

// Add slide 16: K final decision table
const s16 = p.slides.add();
addHeader(s16, 'UNSUPERVISED TRACK', 'Final K decision');
const body16 = s16.shapes.add({ geometry: 'textbox', position: { left: 80, top: 155, width: 1080, height: 70 }, fill: 'none', line: { width: 0, fill: 'none' } });
body16.text.set('Final K = 3. The decision uses Gap Statistic as the primary rule and Davies-Bouldin as the corroborating internal index. Other metrics remain diagnostic checks.');
body16.text.style = { fontSize: 22, color: '#263238', autoFit: 'shrinkText' };
const table16 = s16.tables.add({ rows: 6, columns: 4, left: 80, top: 245, width: 1120, height: 300, values: [
  ['Metric', 'Direction', 'K indicated', 'Decision role'],
  ['Gap Statistic', 'One-SE rule', '3', 'Primary rule'],
  ['Davies-Bouldin', 'Lower is better', '3', 'Corroborates final K'],
  ['Inertia bend', 'Diminishing return', '4', 'Audit check'],
  ['Calinski-Harabasz', 'Higher is better', '5', 'Audit check'],
  ['Silhouette', 'Higher is better', '2', 'Warns of coarse dominant structure'],
]});
styleTable(table16);
s16.speakerNotes.text = 'Source: outputs/tables/k_metric_direction_recheck.csv and k_metric_direction_recheck_summary.json. Final K=3 because Gap Statistic and Davies-Bouldin both indicate K=3.';

// Export and finalize
const stagingDir = path.join(workspaceDir, '.codex-finalizer');
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const candidatePath = path.join(stagingDir, 'candidate_revised_latest.pptx');
await (await PresentationFile.exportPptx(p)).save(candidatePath);
const result = await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit'],
  fontPolicy: { basis: 'design', families: ['Arial Unicode MS', 'Calibri', 'Helvetica Neue'] },
  verifyArtifactToolImport: true,
  materializeLiteralChartWorkbooks: true,
  receiptPath: path.join(stagingDir, 'MOOC_Student_Analytics_Presentation_TH_revised_latest.validation.json'),
});
console.log(JSON.stringify({finalPath, result}, null, 2));
