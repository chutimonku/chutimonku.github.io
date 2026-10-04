import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const pptx='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Full_Results_Deck_TH.pptx';
const out='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/.slide_build_full/rendered';
await fs.mkdir(out,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(pptx));
let i = 1;
for (let idx = 0; idx < p.slides.count; idx++) {
 const slide = p.slides.getItem(idx);
 const png = await slide.export({format:'png', scale:0.7});
 await fs.writeFile(path.join(out,`slide_${String(i).padStart(2,'0')}.png`), new Uint8Array(await png.arrayBuffer()));
 i++;
}
console.log('rendered', i - 1);
