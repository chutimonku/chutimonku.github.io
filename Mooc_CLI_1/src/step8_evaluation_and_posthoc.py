"""Outcome access for clustering is permitted only after its model lock."""
from src.workflow import posthoc_cluster_validation

if __name__ == "__main__":
    print(posthoc_cluster_validation())
