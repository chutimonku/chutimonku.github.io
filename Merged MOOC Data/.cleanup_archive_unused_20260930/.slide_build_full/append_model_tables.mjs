import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const SKILL_DIR = '/Users/chingli/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const RUNTIME_PYTHON = '/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const root = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data';
const sup = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Sup';
const un = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Un';
const source = path.join(root, 'reports', 'MOOC_Student_Analytics_Full_Results_Deck_TH.pptx');
const FINAL_PPTX = path.join(root, 'reports', 'MOOC_Student_Analytics_Full_Results_Deck_TH_with_model_tables_v2.pptx');
const { resolvePresentationFont, finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')).href);
const font = resolvePresentationFont({ fontFamily: 'Arial' });
const pres = await PresentationFile.importPptx(await FileBlob.load(source));
const blue = '#004A73'; const gray = '#666666'; const green='#2D7F5E'; const orange='#D97924';
function addShape(slide, x, y, w, h, fill = 'none', line = 'none') { return slide.shapes.add({ geometry: 'rect', position: { left:x, top:y, width:w, height:h }, fill, line:{fill:line,width:line==='none'?0:1} }); }
function addText(slide, text, x, y, w, h, opts={}) { const t=slide.shapes.add({ geometry:'textbox', position:{left:x,top:y,width:w,height:h}, fill:'none', line:{fill:'none',width:0} }); t.text=text; t.text.style={ typeface:font, fontSize:opts.size??18, bold:opts.bold??false, color:opts.color??'#222222', italic:opts.italic??false, autoFit:'shrinkText' }; return t; }
function title(slide, main, sub='') { addShape(slide,74,42,6,86,blue,blue); addText(slide,main,105,42,1080,58,{size:36,bold:true,color:blue}); if(sub) addText(slide,sub,108,103,1040,35,{size:19,color:gray}); }
function footer(slide, txt='MOOC Student Analytics | model selection and runtime appendix') { addText(slide,txt,80,676,1000,24,{size:12,color:'#7A7A7A',italic:true}); }
function fmt(v, d=4) {
  if (v === null || v === undefined || v === '') return '-';
  if (typeof v === 'boolean') return v ? 'True' : 'False';
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d });
  return n.toFixed(d);
}
async function csv(p) { const txt=await fs.readFile(p,'utf8'); const rows=[]; let row=[], cur='', q=false; for(let i=0;i<txt.length;i++){ const c=txt[i], n=txt[i+1]; if(c==='"'){ if(q&&n==='"'){cur+='"';i++;} else q=!q; } else if(c===','&&!q){ row.push(cur);cur=''; } else if((c==='\n'||c==='\r')&&!q){ if(c==='\r'&&n==='\n') i++; row.push(cur); if(row.some(x=>x!=='')) rows.push(row); row=[]; cur=''; } else cur+=c; } if(cur||row.length){row.push(cur);rows.push(row);} const head=rows.shift(); return rows.map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]??'']))); }
function makeTable(slide, values, x, y, w, h, widths, fontSize=11) { const tb=slide.tables.add({ rows:values.length, columns:values[0].length, left:x, top:y, width:w, height:h, values, columnWidths:widths }); try { tb.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({ fill:blue, textStyle:{typeface:font,fontSize,bold:true,color:'#FFFFFF'} }); tb.cells.block({row:1,column:0,rowCount:values.length-1,columnCount:values[0].length}).assign({ textStyle:{typeface:font,fontSize,color:'#222222'}, borders:{style:'solid',fill:'#D9E3EA',width:1} }); } catch {} return tb; }
async function addImage(slide, p, x,y,w,h, alt) { const blob=await fs.readFile(p); slide.images.add({ blob, contentType:'image/png', alt, fit:'contain', position:{left:x,top:y,width:w,height:h} }); }

const kComposite = await csv(path.join(root,'outputs/tables/k_selection_composite_scores.csv'));
const allTrack = await csv(path.join(root,'outputs/tables/all_track_model_comparison.csv'));
const unK = await csv(path.join(un,'outputs/tables/k_selection_metrics.csv'));
const unModels = await csv(path.join(un,'outputs/tables/model_comparison.csv'));
const supModels = await csv(path.join(sup,'outputs/tables/model_comparison.csv'));
const deep = await csv(path.join(root,'outputs/tables/deep_learning_model_comparison.csv'));
const llm = await csv(path.join(root,'outputs/tables/llm_comparative_model_comparison.csv'));
const llmStatus = await csv(path.join(root,'outputs/tables/llm_api_provider_status.csv'));

// 29 K graph plus detailed table
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'K selection evidence with six metrics','เพิ่มกราฟและตารางเพื่ออธิบายว่าค่า K ถูกเลือกจาก metric หลายตัว ไม่ใช่ elbow อย่างเดียว');
 await addImage(s,path.join(root,'outputs/figures/tracks/multi_metric_k_selection_gap.png'),60,145,520,340,'K selection graph');
 const rows=[['K','Silhouette','DBI','CH','ARI','NMI','Composite','Runtime','Selected']];
 for(const r of kComposite.slice(0,9)) rows.push([fmt(r.k,0),fmt(r.silhouette),fmt(r.davies_bouldin),fmt(r.calinski_harabasz,1),fmt(r.resample_ari),fmt(r.resample_nmi),fmt(r.composite_score),fmt(r.runtime_sec),r.selected_operational_k==='True'?'True':'False']);
 makeTable(s,rows,600,145,620,350,[38,72,62,90,58,58,82,70,90],10);
 addText(s,'Merged audit: K=3 มี composite score สูงสุดในตารางนี้ แต่ Un final track ใช้ K=5 จาก gap one-SE บน sample 12,000 ดังนั้นสไลด์นี้แสดง evidence ทั้งสองระดับอย่างโปร่งใส',80,555,1120,50,{size:18,color:'#333333'}); footer(s,'Sources: multi_metric_k_selection_gap.png, k_selection_composite_scores.csv');
}
// 30 family table at K=3 like user example
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Traditional unsupervised family table at K=3','ตารางรูปแบบเดียวกับตัวอย่างที่ขอ: family, K, internal metrics, stability, runtime และ selected flag');
 const k3=allTrack.filter(r=>r.track==='Traditional Unsupervised' && String(r.k)==='3.0');
 const order=['BIRCH','Gaussian Mixture','K-Means','K-Medoids (approx.)','MiniBatch K-Means','HAC (Ward)'];
 k3.sort((a,b)=>order.indexOf(a.model)-order.indexOf(b.model));
 const rows=[['Family','K','Silhouette','Davies-Bouldin','Calinski-Harabasz','ARI','Smallest cluster %','Runtime sec','Selected']];
 for(const r of k3) rows.push([r.model,fmt(r.k,0),fmt(r.silhouette),fmt(r.davies_bouldin),fmt(r.calinski_harabasz,4),fmt(r.stability_ari),'-',fmt(r.runtime_sec),r.model==='K-Means'?'True':r.selected]);
 makeTable(s,rows,45,155,1190,360,[190,45,95,105,155,70,135,100,90],10);
 addText(s,'อ่านตารางนี้ร่วมกับ K selection slide: ค่า selected ในหน้านี้เน้น K-Means K=3 ตาม operational composite ของ merged audit ส่วน family อื่นใช้เป็น benchmark เทียบ metric และ runtime',75,555,1120,50,{size:18,color:'#333333'}); footer(s,'Source: outputs/tables/all_track_model_comparison.csv');
}
// 31 Un final model runtime
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Unsupervised final-track model and runtime table','ตารางสรุป Un track หลักที่ใช้ K=5 และเปรียบเทียบโมเดล clustering หลาย family');
 const rows=[['Algorithm','Family','K','Silhouette','DBI','CH','ARI','Smallest cluster','Runtime sec','Deployable']];
 for(const r of unModels) rows.push([r.algorithm,r.family,fmt(r.k_requested,0),fmt(r.silhouette),fmt(r.davies_bouldin),fmt(r.calinski_harabasz,1),fmt(r.resample_stability_ari),fmt(Number(r.smallest_cluster_fraction)*100,2)+'%',fmt(r.runtime_seconds),r.deployable]);
 makeTable(s,rows,35,145,1210,410,[150,170,42,85,70,90,70,105,80,80],9.5);
 addText(s,'Un track ใช้หลาย family เพื่อตรวจว่า persona ไม่ได้เกิดจาก algorithm เดียว K-Means มี rank ภายในดีที่สุด แต่ Gaussian Mixture, BIRCH, DBSCAN และ hierarchical models ใช้เป็น robustness checks',65,585,1150,44,{size:17,color:'#333333'}); footer(s,'Source: Un/outputs/tables/model_comparison.csv');
}
//32 Sup all models
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Supervised model comparison table','เพิ่มตารางผลโมเดล supervised ทุกกลุ่มหลักพร้อม metric สำคัญ');
 const rows=[['Model','Family','ROC-AUC','PR-AUC','Brier','Threshold','F1','Precision','Recall','Accuracy','Bal Acc']];
 for(const r of supModels.slice(0,12)) rows.push([r.model_id,r.family,fmt(r.test_roc_auc,4),fmt(r.test_pr_auc,4),fmt(r.test_brier_score,4),fmt(r.optimal_threshold,4),fmt(r.test_f1_optimal,4),fmt(r.test_precision_optimal,4),fmt(r.test_recall_optimal,4),fmt(r.test_accuracy_optimal,4),fmt(r.test_balanced_acc,4)]);
 makeTable(s,rows,25,135,1230,455,[160,150,70,70,62,75,58,78,70,75,70],8.5);
 addText(s,'หมายเหตุ: ตาราง Sup ไม่มี runtime_sec ในไฟล์ model_comparison.csv ที่มีอยู่ จึงรายงานเฉพาะ metric ที่ถูก log จริง ไม่เติม runtime เอง',65,608,1150,38,{size:17,color:'#333333'}); footer(s,'Source: Sup/outputs/tables/model_comparison.csv');
}
//33 Deep all models runtime
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Deep learning model and runtime table','เพิ่มทุก MLP ที่รันจริง พร้อม epochs, runtime และ metric บน test set');
 const rows=[['Model','Epochs','Runtime sec','PR-AUC','ROC-AUC','Brier','Accuracy','Bal Acc','Precision','Recall','F1','Selected']];
 for(const r of deep) rows.push([r.model_id,fmt(r.epochs_or_iterations,0),fmt(r.runtime_sec),fmt(r.test_pr_auc,4),fmt(r.test_roc_auc,4),fmt(r.test_brier,4),fmt(r.test_accuracy,4),fmt(r.test_balanced_accuracy,4),fmt(r.test_precision,4),fmt(r.test_recall,4),fmt(r.test_f1,4),r.selected]);
 makeTable(s,rows,40,155,1200,330,[180,65,80,75,75,65,75,75,75,65,60,70],9.5);
 await addImage(s,path.join(root,'outputs/figures/tracks/deep_model_comparison.png'),95,505,500,135,'Deep comparison');
 addText(s,'MLP 128,64 ถูกเลือกเพราะให้ F1 0.7917, recall 0.8421 และ PR-AUC 0.8388 โดยใช้ runtime 12.27 วินาทีใน run นี้',640,525,520,75,{size:19,color:'#333333'}); footer(s,'Source: outputs/tables/deep_learning_model_comparison.csv');
}
//34 LLM results and provider table
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'LLM model status, runtime and result table','แยกผลจริง ออกจาก simulated/quarantined เพื่อให้เปรียบเทียบอย่างยุติธรรม');
 const rows=[['Provider','Model','Status','Students','Accuracy','Precision','Recall','F1','ROC-AUC','PR-AUC','Runtime sec','Selected']];
 for(const r of llm) rows.push([r.provider,r.model_name,'completed',r.evaluation_students,fmt(r.test_accuracy,4),fmt(r.test_precision,4),fmt(r.test_recall,4),fmt(r.test_f1,4),fmt(r.test_roc_auc,4),fmt(r.test_pr_auc,4),fmt(r.runtime_sec,2),r.selected]);
 for(const r of llmStatus.filter(x=>x.provider!=='Gemini')) rows.push([r.provider,r.model_name,r.status,r.evaluation_students,'-','-','-','-','-','-','-',r.quarantined==='True'?'Quarantined':'False']);
 makeTable(s,rows,35,145,1210,260,[90,190,115,70,75,75,65,55,70,65,85,90],9);
 await addImage(s,path.join(root,'outputs/figures/tracks/llm_text_model_comparison.png'),120,435,470,180,'LLM comparison');
 await addImage(s,path.join(root,'outputs/figures/tracks/llm_generative_confusion_matrices.png'),650,420,470,200,'LLM confusion');
 addText(s,'Gemini เป็น full held-out test 1,800 คน ส่วน OpenAI/Claude ไม่มี real API evaluation ในรอบนี้ จึงไม่รายงานเป็นผลโมเดลจริง',95,625,1100,35,{size:17,color:'#333333'}); footer(s,'Sources: llm_comparative_model_comparison.csv and llm_api_provider_status.csv');
}
//35 cross-track runtime summary
{
 const s=pres.slides.add(); s.background.fill='#FFFFFF'; title(s,'Cross-track selected model summary','สรุปโมเดลที่เลือก ผลลัพธ์ และ runtime เท่าที่มีการ log จริง');
 const rows=[['Track','Selected model','Primary outcome','Key metrics','Runtime evidence'],['Merged K audit','K-Means K=3','Operational composite K','Composite 0.8798, Silhouette 0.9435, DBI 0.1940','0.0185 sec'],['Un final','K-Means K=5','Persona segmentation','Composite 0.9937, ARI 0.9931, min cluster 13.23%','2.2843 sec'],['Sup','Random Forest d15','Certification prediction','ROC-AUC 0.9933, PR-AUC 0.8476, F1 0.7889','not logged in table'],['Deep','MLP 128,64','Neural prediction benchmark','PR-AUC 0.8388, F1 0.7917, Recall 0.8421','12.2695 sec'],['LLM','Gemini 3.5 Flash Lite','Text/AI benchmark','Accuracy 0.9628, Recall 0.9310, F1 0.6171','311.58 sec']];
 makeTable(s,rows,55,155,1170,375,[170,190,220,390,200],11);
 addText(s,'runtime เปรียบเทียบกันได้เฉพาะภายในบริบท run เดียวกัน เพราะ hardware, API latency และ sample size ต่างกัน โดยเฉพาะ LLM ใช้ request batching และ token cost',80,570,1120,58,{size:19,color:'#333333'}); footer(s);
}

await fs.mkdir(path.join(root,'.codex-finalizer'),{recursive:true});
const candidatePath=path.join(root,'.codex-finalizer','candidate_with_model_tables.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
const tableSlides=[2,4,5,10,12,16,18,19,22,25,28,29,30,31,32,33,34,35];
const result=await finalizePresentation({
 explicitTotalSlideCount:35,
 requiredNativeTableOwnerSlides:tableSlides,
 requiredNativeChartOwnerSlides:[], requiredEmbeddedWorkbookChartOwnerSlides:[],
 workspaceDir:root, candidatePath, finalPath:FINAL_PPTX, pythonExecutable:RUNTIME_PYTHON,
 integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:tableSlides,
 fontPolicy:{basis:'design',families:[font]}, verifyArtifactToolImport:true,
 receiptPath:path.join(root,'.codex-finalizer','MOOC_Student_Analytics_Full_Results_Deck_TH_with_model_tables_v2.validation.json')
});
console.log(JSON.stringify(result,null,2));
