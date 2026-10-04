import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const pptx='/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Full_Results_Deck_TH_with_model_tables_v2.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(pptx));
const snap=await p.inspect({kind:'image,slide,table,textbox', maxChars:30000});
console.log(snap.ndjson);
