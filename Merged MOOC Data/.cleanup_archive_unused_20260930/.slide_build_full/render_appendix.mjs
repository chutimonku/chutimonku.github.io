import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const pptx='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Full_Results_Deck_TH_with_model_tables_v2.pptx';
const out='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/.slide_build_full/rendered_model_tables';
await fs.mkdir(out,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(pptx));
for (let idx=28; idx<35; idx++) {
 const slide=p.slides.getItem(idx);
 const png=await slide.export({format:'png', scale:0.9});
 await fs.writeFile(path.join(out,`slide_${String(idx+1).padStart(2,'0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log('rendered appendix');
