import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const p = await PresentationFile.importPptx(await FileBlob.load('/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx'));
const chart = p.resolve('ch/twj21wjy');
console.log('series type', chart.series?.constructor?.name);
console.log('getItemAt', typeof chart.series?.getItemAt);
const s0 = chart.series?.getItemAt ? chart.series.getItemAt(0) : chart.series?.items?.[0];
console.log('s0', s0?.constructor?.name, typeof s0);
for (const prop of ['name','values','categories','fill','stroke']) { try { console.log(prop, s0?.[prop]); } catch(e){ console.log(prop, e.message); } }
console.log('methods chart apply', typeof chart.apply);
