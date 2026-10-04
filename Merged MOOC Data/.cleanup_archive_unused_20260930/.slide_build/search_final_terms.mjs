import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const path = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH_revised_latest.pptx';
const p = await PresentationFile.importPptx(await FileBlob.load(path));
for (const term of ['provisional', 'true K', '57.43', '41.34', '1.23%', 'working solution']) {
 const snap = await p.inspect({kind:'textbox,notes', search:term, maxChars:8000});
 console.log('\nTERM', term); console.log(snap.ndjson || '(none)');
}
