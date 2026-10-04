import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Final_K5_TH_v2.pptx'));
const tb=p.resolve('tb/p8bedgze');
console.log(Object.keys(tb));
console.log(tb.left,tb.top,tb.width,tb.height,tb.frame,tb.position);
const sh=p.resolve('sh/hcfm5s72'); console.log('shape keys',Object.keys(sh), sh.frame, sh.position);
