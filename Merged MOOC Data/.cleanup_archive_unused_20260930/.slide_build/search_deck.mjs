import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const sourcePath = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx';
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
for (const term of ['575', '624', 'K=3', 'k=3', '57.', 'Gap', 'cluster', 'clean']) {
  const snap = await presentation.inspect({kind:'slide,textbox,chart,table,notes', search: term, maxChars: 12000});
  console.log('\n--- SEARCH', term, '---');
  console.log(snap.ndjson);
}
