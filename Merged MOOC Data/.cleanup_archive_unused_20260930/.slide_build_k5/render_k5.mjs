import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const pptx='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Final_K5_TH_clean.pptx';
const out='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/.slide_build_k5/rendered';
await fs.mkdir(out,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(pptx));
for (const n of [11,12,29,30,31,35]) {
 const slide=p.slides.getItem(n-1);
 const png=await slide.export({format:'png',scale:0.9});
 await fs.writeFile(path.join(out,`slide_${String(n).padStart(2,'0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log('rendered');
