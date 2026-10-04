# Model Selection Rationale

Models are selected using the observed scale, eight non-outcome behavioral features, internal metrics, resample stability, interpretability, and deployment feasibility. All candidates are evaluated on the same deterministic sample. The sample size is calculated from a documented pairwise-distance memory budget, not a population margin-of-error formula. No known outcome is loaded by this stage.

The provisional model is the deployable candidate with the best mean rank across Silhouette (higher), Davies-Bouldin (lower), Calinski-Harabasz (higher), and resample ARI (higher). This equal-rank rule avoids allowing any metric's numerical scale to dominate. Final locking remains a separate Step 8 decision.
