# Research basis, dataset alignment, and applied decisions

## Dataset-specific sources

1. HarvardX Person-Course Academic Year 2013 De-Identified Dataset, version 3.0. Harvard Dataverse. https://doi.org/10.7910/DVN/26147
   - Relevance: official provenance for de-identified person-course records and their scope/limitations.
   - Applied here: source inventory, checksum/provenance audit, one-student aggregation, and explicit caution that aggregate records are not event sequences.
2. Ho et al. (2014), HarvardX and MITx: The First Year of Open Online Courses. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2381263
   - Finding: participation, intent, engagement, and certification are highly heterogeneous.
   - Applied here: distributions and persona proportions are reported alongside completion outcomes; certification alone is not treated as the sole definition of success.
3. Kizilcec, Piech, and Schneider (2013), Deconstructing Disengagement. https://doi.org/10.1145/2460296.2460330
   - Finding: longitudinal engagement subpopulations reveal more than a binary completion view.
   - Applied here: behavioral personas are profiled with radar and distribution plots, while clusters remain descriptive and non-causal.

## Method sources

4. Tibshirani, Walther, and Hastie (2001), Estimating the number of clusters via the Gap statistic. https://doi.org/10.1111/1467-9868.00293
   - Applied here: Gap(k), its simulation standard error, and the one-standard-error selection rule are combined with Silhouette, Davies-Bouldin, Calinski-Harabasz, stability ARI, and minimum cluster size. Elbow/WCSS is retained only for audit and contributes no selection vote.
5. Gitinabard et al. (2018), Your Actions or Your Associates? Predicting Certification and Dropout in MOOCs. https://arxiv.org/abs/1809.00052
   - Applied here: behavioral and forum features inform certification models; PR-AUC, recall, F1, calibration, and confusion matrices are reported because the positive class is rare.
6. Fei and Yeung (2015/2017), Temporal Models for Predicting Student Dropout in Massive Open Online Courses. https://arxiv.org/abs/1702.06404
7. Yang et al. (2016), Modelling Student Behavior using Granular Large Scale Action Data from a MOOC. https://arxiv.org/abs/1608.04789
   - Boundary applied here: sequence CNN/RNN/LSTM models are not claimed because the available modeling table contains aggregates rather than ordered event-level sequences.
8. Gardner and Brooks (2018), Dropout Model Evaluation in MOOCs. https://arxiv.org/abs/1802.06009
   - Applied here: stratified train/validation/test isolation, a baseline, threshold selection on validation only, and final evaluation on untouched test data.

## Student-row-to-text LLM / Transformer track

The unit of analysis is one student row. Audited behavioral values are deterministically rendered as factual natural-language statements and passed to lexical and transformer representations for supervised certification prediction. The target remains quarantined and never enters the text. Video fields are interpreted only as play/click counts; they are not watch duration and are not presented as spoken-video transcripts.
