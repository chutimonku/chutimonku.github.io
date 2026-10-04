# Literature Review and Method Rationale

The project uses behavior-only clustering and reserves known educational outcomes for post-hoc validation. Prior MOOC research has used Ward hierarchical clustering followed by K-Means to derive learner-behavior groups, while later work demonstrates that unsupervised learner groups can reveal temporal patterns without prescribing outcome labels.

Candidate families are deliberately different: centroid methods provide a scalable baseline; Gaussian mixtures test probabilistic elliptical structure; BIRCH provides a large-data CF-tree approach; divisive and agglomerative methods test hierarchical geometry; and DBSCAN tests density-connected structure and noise. MiniBatch K-Means is reported as a scalability variant, not a separate model family.

## References

- HarvardX (2014). *HarvardX Person-Course Academic Year 2013 De-Identified Dataset, version 3.0*. https://doi.org/10.7910/DVN/26147
- Tseng et al. (2016). *Who will pass? Analyzing learner behaviors in MOOCs*. https://doi.org/10.1186/s41039-016-0033-5
- Peach et al. (2019). *Data-driven unsupervised clustering of online learner behaviour*. https://doi.org/10.1038/s41539-019-0054-0
- Lloyd (1982). *Least squares quantization in PCM*. https://doi.org/10.1109/TIT.1982.1056489
- Dempster, Laird, and Rubin (1977). *Maximum likelihood from incomplete data via the EM algorithm*. https://doi.org/10.1111/j.2517-6161.1977.tb01600.x
- Zhang, Ramakrishnan, and Livny (1996). *BIRCH: An efficient data clustering method for very large databases*. https://doi.org/10.1145/233269.233324
- Ward (1963). *Hierarchical grouping to optimize an objective function*. https://doi.org/10.1080/01621459.1963.10500845
- Ester et al. (1996). *A density-based algorithm for discovering clusters in large spatial databases with noise*. https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf
