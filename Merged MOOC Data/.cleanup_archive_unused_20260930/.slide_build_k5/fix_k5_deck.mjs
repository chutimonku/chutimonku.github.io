import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const SKILL_DIR='/Users/chingli/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const RUNTIME_PYTHON='/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const RUNTIME_NODE_MODULES='/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const root='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data';
const un='/Users/chingli/Desktop/AI/Mooc_CLI_2/Un';
const source=path.join(root,'reports','MOOC_Student_Analytics_Full_Results_Deck_TH_with_model_tables_v2.pptx');
const finalPath=path.join(root,'reports','MOOC_Student_Analytics_Final_K5_TH_v2.pptx');
const { resolvePresentationFont, finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const pres=await PresentationFile.importPptx(await FileBlob.load(source));

async function csv(p){
 const txt=await fs.readFile(p,'utf8'); const rows=[]; let row=[],cur='',q=false;
 for(let i=0;i<txt.length;i++){const c=txt[i],n=txt[i+1]; if(c==='"'){if(q&&n==='"'){cur+='"';i++;}else q=!q;}else if(c===','&&!q){row.push(cur);cur='';}else if((c==='\n'||c==='\r')&&!q){if(c==='\r'&&n==='\n')i++; row.push(cur); if(row.some(x=>x!==''))rows.push(row); row=[];cur='';}else cur+=c;}
 if(cur||row.length){row.push(cur);rows.push(row);} const head=rows.shift(); return rows.map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]??''])));
}
function num(v){ const n=Number(v); return Number.isFinite(n)?n:null; }
function fmt(v,d=4){ const n=num(v); if(n===null) return '-'; if(Math.abs(n)>=1000) return n.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}); return n.toFixed(d); }
function pct(v,d=2){ const n=num(v); return n===null?'-':`${n.toFixed(d)}%`; }
function setText(id,text){ const o=pres.resolve(id); o.text=text; o.text.style={typeface:font, fontSize:o.text?.style?.fontSize ?? 18, color:o.text?.style?.color ?? '#222222', autoFit:'shrinkText'}; }
function setBox(id,text,size=18,color='#222222',bold=false){ const o=pres.resolve(id); o.text=text; o.text.style={typeface:font,fontSize:size,color,bold,autoFit:'shrinkText'}; }
function setCell(tb,r,c,val){ tb.getCell(r,c).value = String(val); }
function fillTable(id, values){ const tb=pres.resolve(id); for(let r=0;r<tb.rows.length;r++){ for(let c=0;c<tb.columns.length;c++){ setCell(tb,r,c, values[r]?.[c] ?? ''); } } return tb; }
async function replaceImage(id,imgPath,alt){ const im=pres.resolve(id); await im.replace({blob:await fs.readFile(imgPath), contentType:'image/png', alt}); }

const kRows=await csv(path.join(un,'outputs/tables','k_selection_metrics.csv'));
const modelRows=await csv(path.join(un,'outputs/tables','unsupervised_model_comparison.csv'));
const clusterRows=await csv(path.join(un,'outputs/tables','cluster_profiles.csv'));
const k5=kRows.find(r=>Number(r.k)===5);

// Slide 11: make final K=5 only and replace graph with Un K metric graph.
setBox('sh/xcryxg7y','Unsupervised K selection',36,'#004A73',true);
setBox('sh/wbih4b6d','Final K = 5 groups from the Un track gap one-SE selection',19,'#666666');
setBox('sh/250zy18b','ค่า K สุดท้ายของงานนี้คือ 5 กลุ่ม โดยใช้ gap statistic one-SE เป็นกติกาหลัก และตรวจซ้ำด้วย silhouette, Davies-Bouldin, Calinski-Harabasz, stability และขนาด cluster',18,'#333333');
setBox('sh/98rytw72','Source: Un/outputs/tables/k_selection_metrics.csv and Un/outputs/figures/modeling/k_selection_four_metrics.png',12,'#7A7A7A');
await replaceImage('im/2lcz2l0n', path.join(un,'outputs/figures/modeling/k_selection_four_metrics.png'), 'K selection four metrics from Un track');

// Slide 12 table: K=5 final evidence, no K=3 final language.
setBox('sh/1gbm9s3a','K=5 decision evidence',36,'#004A73',true);
setBox('sh/0f2lgnmp','ตารางนี้อธิบายว่าทำไม final segmentation ใช้ 5 กลุ่ม',19,'#666666');
setBox('sh/q903ad4n','K=5 ถูกเลือกจาก gap one-SE rule และยังมี cluster ขนาดเล็กสุด 13.23% จึงใช้งานเชิง persona ได้ โดย metric อื่นใช้เป็น audit evidence ไม่ใช่ final decision เพียงตัวเดียว',18,'#333333');
const t12=[['Metric','Direction','K=5 evidence'],['Gap statistic','One-SE selected K','Gap 1.1741, selected K = 5'],['Silhouette','Higher is better','0.4275, lower than K=2 but still acceptable'],['Davies-Bouldin','Lower is better','0.8827, used as separation check'],['Calinski-Harabasz','Higher is better','16,546.0233, variance separation evidence'],['Cluster size','Avoid tiny unusable clusters','Smallest cluster 13.23%, largest 29.29%']];
fillTable('tb/2xsfqlcz',t12);

// Slide 29: K=5 appendix evidence and graph.
setBox('sh/tk36hwby','K=5 selection evidence',36,'#004A73',true);
setBox('sh/8jup8rad','สไลด์นี้เก็บ candidate K ทั้งหมดไว้ แต่ selected/final คือ K=5 เท่านั้น',19,'#666666');
setBox('sh/h8n6lwbu','ตารางด้านขวาแสดง metric ตามค่า K จาก Un track ขนาด sample 12,000 แถว กติกา gap one-SE เลือก K=5 และใช้ metric อื่นเป็นหลักฐานประกอบการตรวจสอบ',18,'#333333');
setBox('sh/g7upcra9','Source: Un/outputs/tables/k_selection_metrics.csv',12,'#7A7A7A');
await replaceImage('im/bexgz2to', path.join(un,'outputs/figures/modeling/k_selection_four_metrics.png'), 'K selection metrics for final K 5');
const table29=[['K','Silhouette','DBI','CH','ARI mean','Gap','Min cluster','Runtime','Selected']];
for(const r of kRows){ table29.push([fmt(r.k,0),fmt(r.silhouette,4),fmt(r.davies_bouldin,4),fmt(r.calinski_harabasz,1),fmt(r.resample_ari_mean,4),fmt(r.gap_statistic,4),pct(r.smallest_cluster_pct,2),fmt(r.runtime_seconds,4),Number(r.k)===5?'True':'False']); }
fillTable('tb/n6lw3yp0',table29);

// Slide 30: K=5 model family table.
setBox('sh/po72d8nm','Unsupervised model family table at K=5',34,'#004A73',true);
setBox('sh/o3yl4361','ตารางนี้สรุปโมเดล clustering ที่ทดสอบกับจำนวนกลุ่มสุดท้าย 5 กลุ่ม',18,'#666666');
setBox('sh/apg36do7','K-Means K=5 ถูกใช้เป็น final clustering model เพราะให้ composite score สูงสุดในตารางเปรียบเทียบโมเดลหลัก พร้อม silhouette 0.4276, Davies-Bouldin 0.8827 และ ARI 0.9931',17,'#333333');
setBox('sh/xsr2h8ni','Source: Un/outputs/tables/unsupervised_model_comparison.csv',12,'#7A7A7A');
const table30=[['Family','K','Silhouette','Davies-Bouldin','Calinski-Harabasz','ARI','Smallest cluster %','Runtime sec','Selected']];
for(const r of modelRows){ table30.push([r.model_family,fmt(r.k,0),fmt(r.silhouette,4),fmt(r.davies_bouldin,4),fmt(r.calinski_harabasz,1),fmt(r.resample_ari,4),pct(r.smallest_cluster_pct,2),fmt(r.runtime_seconds,4),r.model_family==='K-Means'?'True':'False']); }
while(table30.length<7) table30.push(['','','','','','','','','']);
fillTable('tb/ydkrm5sr',table30);

// Slide 31: keep K=5 final text concise.
setBox('sh/cfa903yt','ตารางสรุป Un track หลังล็อกจำนวนกลุ่มสุดท้ายเป็น K=5',19,'#666666');
setBox('sh/ehsr2dgz','Un track ใช้ K=5 เพื่อสร้าง persona 5 กลุ่ม โดย K-Means เป็นโมเดล final ส่วน family อื่นใช้เป็น benchmark และ robustness checks',18,'#333333');

// Slide 35: remove merged K=3 audit row, make K=5 summary.
setBox('sh/hcfm5s72','runtime เปรียบเทียบได้เฉพาะในบริบทของแต่ละ track เพราะ sample size, hardware และ API latency ไม่เท่ากัน แต่ final segmentation ของงานนี้ล็อกที่ K=5',18,'#333333');
const table35=[['Track','Selected model','Primary outcome','Key metrics','Runtime evidence'],['Unsupervised','K-Means K=5','Persona segmentation','Gap one-SE selected K=5, silhouette 0.4276, DBI 0.8827, ARI 0.9931','2.2843 sec'],['Sup','Random Forest d15','Certification prediction','ROC-AUC 0.9933, PR-AUC 0.8476, F1 0.7889','not logged in table'],['Deep','MLP 128,64','Neural prediction benchmark','PR-AUC 0.8388, F1 0.7917, Recall 0.8421','12.2695 sec'],['LLM','Gemini 3.5 Flash Lite','Text benchmark','Accuracy 0.9628, Recall 0.9310, F1 0.6171','311.58 sec'],['Persona output','5 clusters','Behavior groups','Cluster shares: 13.79%, 18.54%, 16.49%, 29.11%, 22.06%','from cluster_profiles.csv']];
fillTable('tb/p8bedgze',table35);

// Add speaker notes source breadcrumbs where useful.
pres.resolve('nt/jetc3ut0').textFrame.setText('Final K=5 source: Un/outputs/tables/k_selection_metrics.csv. K=5 selected_by_gap_one_se=True.');
pres.resolve('nt/wnqh07ex').textFrame.setText('Model family K=5 source: Un/outputs/tables/unsupervised_model_comparison.csv.');
pres.resolve('nt/1obmtofm').textFrame.setText('Final segmentation summary uses K=5 cluster_profiles.csv and selected model K-Means K=5.');

const candidatePath=path.join(root,'.codex-finalizer','candidate_final_k5.pptx');
await fs.mkdir(path.dirname(candidatePath),{recursive:true});
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
const tableSlides=[2,4,5,10,12,16,18,19,22,25,28,29,30,31,32,33,34,35];
const result=await finalizePresentation({
 explicitTotalSlideCount:35,
 requiredNativeTableOwnerSlides:tableSlides,
 requiredNativeChartOwnerSlides:[], requiredEmbeddedWorkbookChartOwnerSlides:[],
 workspaceDir:root, candidatePath, finalPath,
 pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:tableSlides,
 fontPolicy:{basis:'design',families:[font]}, verifyArtifactToolImport:true,
 receiptPath:path.join(root,'.codex-finalizer','MOOC_Student_Analytics_Final_K5_TH_v2.validation.json')
});
console.log(JSON.stringify(result,null,2));
