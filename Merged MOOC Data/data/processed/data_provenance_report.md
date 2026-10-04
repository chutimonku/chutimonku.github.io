# Data Sources and Selection Rationale

## Source files used

1. **HXPC13_DI_v3_11-13-2019.csv** — official HarvardX person-course release from Harvard Dataverse: https://doi.org/10.7910/DVN/26147  
   The local MD5 matches the published checksum. The source is suitable because it has a persistent DOI, accompanying documentation, de-identification information, and broad reuse in MOOC research.
2. **big_student_clear_third_version.csv** — expanded HarvardX-MITx file supplied with the project; declared source: https://www.kaggle.com/datasets/kanikanarang94/mooc-dataset  
   It is used because it adds MITx and wider course coverage. Its exact remote filename and checksum could not be independently matched, so this limitation remains explicit rather than being presented as verified provenance.

## Scope after source reconciliation

- Raw files: 2
- Raw records before cross-source reconciliation: 755,144
- Exact offering-level enrollments after reconciliation: 609,637
- Distinct course offerings: 18
- Unique students: 446,766

The HarvardX and MITx first-year report provides the research context for these person-course records: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2381263
