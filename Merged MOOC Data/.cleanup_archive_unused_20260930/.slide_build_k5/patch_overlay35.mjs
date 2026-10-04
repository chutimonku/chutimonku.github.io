import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const SKILL_DIR='/Users/chingli/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const RUNTIME_PYTHON='/Users/chingli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const root='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data';
const source=path.join(root,'reports','MOOC_Student_Analytics_Final_K5_TH_v2.pptx');
const finalPath=path.join(root,'reports','MOOC_Student_Analytics_Final_K5_TH_clean.pptx');
const { resolvePresentationFont, finalizePresentation }=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const pres=await PresentationFile.importPptx(await FileBlob.load(source));
function shape(slide,x,y,w,h,fill,line='none'){return slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1}})}
function text(slide,t,x,y,w,h,size=18,color='#222',bold=false){const o=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});o.text=t;o.text.style={typeface:font,fontSize:size,color,bold,autoFit:'shrinkText'};return o;}
function makeTable(slide,values,x,y,w,h,widths){const tb=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});try{tb.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:'#004A73',textStyle:{typeface:font,fontSize:10,bold:true,color:'#FFFFFF'}});tb.cells.block({row:1,column:0,rowCount:values.length-1,columnCount:values[0].length}).assign({fill:'#FFFFFF',textStyle:{typeface:font,fontSize:9.5,color:'#222222'},borders:{style:'solid',fill:'#D9E3EA',width:1}});}catch{}return tb;}
const slide=pres.slides.getItem(34);
// move old imported slide-35 objects away before drawing the corrected K=5 summary
for (const id of ['sh/idonexon','sh/3ex47ip8','sh/hcfm5s72','sh/u943ador','tb/p8bedgze']) {
  try { const obj = pres.resolve(id); obj.delete(); } catch (e) { try { const obj = pres.resolve(id); obj.frame = { left: 2000, top: 2000, width: 10, height: 10 }; } catch {} }
}
shape(slide,45,135,1190,500,'#FFFFFF','#FFFFFF');
text(slide,'Cross-track selected model summary',105,42,1080,58,36,'#004A73',true);
text(slide,'สรุปโมเดลที่เลือก ผลลัพธ์ และ runtime เท่าที่มีการ log จริง',108,103,1040,35,19,'#666666');
const vals=[['Track','Selected model','Primary outcome','Key metrics','Runtime evidence'],['Unsupervised','K-Means K=5','Persona segmentation','Gap one-SE selected K=5, silhouette 0.4276, DBI 0.8827, ARI 0.9931','2.2843 sec'],['Sup','Random Forest d15','Certification prediction','ROC-AUC 0.9933, PR-AUC 0.8476, F1 0.7889','not logged in table'],['Deep','MLP 128,64','Neural prediction benchmark','PR-AUC 0.8388, F1 0.7917, Recall 0.8421','12.2695 sec'],['LLM','Gemini 3.5 Flash Lite','Text benchmark','Accuracy 0.9628, Recall 0.9310, F1 0.6171','311.58 sec'],['Persona output','5 clusters','Behavior groups','Cluster shares: 13.79%, 18.54%, 16.49%, 29.11%, 22.06%','cluster_profiles.csv']];
makeTable(slide,vals,55,155,1170,375,[160,180,210,430,190]);
text(slide,'runtime เปรียบเทียบได้เฉพาะในบริบทของแต่ละ track เพราะ sample size, hardware และ API latency ไม่เท่ากัน แต่ final segmentation ของงานนี้ล็อกที่ K=5',80,570,1120,58,18,'#333333');
text(slide,'MOOC Student Analytics | final K=5 segmentation summary',80,676,1000,24,12,'#7A7A7A');
const candidatePath=path.join(root,'.codex-finalizer','candidate_final_k5_v3.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
const tableSlides=[2,4,5,10,12,16,18,19,22,25,28,29,30,31,32,33,34,35];
const result=await finalizePresentation({explicitTotalSlideCount:35,requiredNativeTableOwnerSlides:tableSlides,requiredNativeChartOwnerSlides:[],requiredEmbeddedWorkbookChartOwnerSlides:[],workspaceDir:root,candidatePath,finalPath,pythonExecutable:RUNTIME_PYTHON,integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tableSlides,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(root,'.codex-finalizer','MOOC_Student_Analytics_Final_K5_TH_clean.validation.json')});
console.log(JSON.stringify(result,null,2));
