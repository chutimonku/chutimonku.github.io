import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Full_Results_Deck_TH.pptx'));
console.log(Object.keys(p.slides));
console.log('length', p.slides.length, 'count', p.slides.count, 'size', p.slides.size);
console.log(p.slides.getItem(0));
