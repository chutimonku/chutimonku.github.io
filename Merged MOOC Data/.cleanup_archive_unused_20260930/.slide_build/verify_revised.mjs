import fs from 'node:fs/promises';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const path = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH_revised_latest.pptx';
const p = await PresentationFile.importPptx(await FileBlob.load(path));
const snap = await p.inspect({kind:'slide,textbox,table,chart,notes', search:'Final K', maxChars: 20000});
console.log('--- Final K search ---');
console.log(snap.ndjson);
const snap2 = await p.inspect({kind:'slide,textbox,table,chart,notes', search:'575,060', maxChars: 20000});
console.log('--- 575,060 search ---');
console.log(snap2.ndjson);
const snap3 = await p.inspect({kind:'slide,textbox,table,chart,notes', search:'98.80', maxChars: 20000});
console.log('--- 98.80 search ---');
console.log(snap3.ndjson);
const montage = await p.export({format:'webp', montage:true, scale:1});
await fs.writeFile('/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/.slide_build/revised_montage.webp', new Uint8Array(await montage.arrayBuffer()));
for (const idx of [3,8,9,13,14,15]) {
  const slide = p.slides.getItem(idx);
  const img = await p.export({slide, format:'png', scale:1});
  await fs.writeFile(`/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/.slide_build/slide_${idx+1}.png`, new Uint8Array(await img.arrayBuffer()));
}
