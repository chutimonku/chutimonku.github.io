import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const sourcePath = '/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx';
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({kind:'slide,textbox,shape,image,table,chart,notes,layout', maxChars: 30000});
console.log(snapshot.ndjson);
