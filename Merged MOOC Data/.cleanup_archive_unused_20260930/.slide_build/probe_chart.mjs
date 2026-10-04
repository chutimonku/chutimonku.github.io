import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const p = await PresentationFile.importPptx(await FileBlob.load('/Users/chingli/Desktop/AI/Mooc_CLI_2/Merged MOOC Data/reports/MOOC_Student_Analytics_Presentation_TH.pptx'));
const chart = p.resolve('ch/twj21wjy');
console.log('chart keys', Object.keys(chart));
console.log('series', chart.series ? Object.keys(chart.series) : 'no series');
console.log('series items', chart.series?.items?.length, chart.series?.items?.map(s=>Object.keys(s)));
console.log('categories', chart.categories);
console.log('type', chart.chartType);
