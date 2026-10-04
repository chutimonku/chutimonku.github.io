import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const sourcePath = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx';
const p = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
for (const term of ['รายการ', '446', 'Cleaning', 'rows', 'Cluster 0', 'Persona', '57.43', 'Gradient']) {
  const snap = await p.inspect({kind:'textbox,chart,table,notes', search: term, maxChars: 18000});
  console.log('\n--- SEARCH', term, '---');
  console.log(snap.ndjson);
}
