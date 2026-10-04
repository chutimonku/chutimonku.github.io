"""Train, tune, select, lock, and test both required model branches."""
from src.workflow import train_classification, train_clustering

if __name__ == "__main__":
    print("Classification:", train_classification())
    cluster = train_clustering(); cluster.pop("assignments", None)
    print("Clustering:", cluster)
