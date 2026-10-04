import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const sourcePath = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx';
const p = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
for (const slide of [4,9,10,14]) {
  const snap = await p.inspect({kind:'slide,textbox,table,chart,notes', target:{slide}, maxChars: 10000});
  console.log('\n### SLIDE', slide);
  console.log(snap.ndjson);
}
