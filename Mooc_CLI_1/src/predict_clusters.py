"""Batch command-line inference for pre-aggregated student records."""
import argparse
import pandas as pd
from src.pipeline import predict_clusters

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()
    frame = pd.read_csv(args.input_csv)
    output = pd.concat([frame[["userid_DI"]].reset_index(drop=True), predict_clusters(frame).reset_index(drop=True)], axis=1)
    output.to_csv(args.output_csv, index=False)

if __name__ == "__main__":
    main()
