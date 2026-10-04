# Active model cards

## Traditional Unsupervised
Uses 4 behavioral features selected from the reconciled clean data and returns a student cluster. Outcomes are excluded.

## Deep Learning
Uses a neural-network classifier on 34 governed pre-outcome inputs to predict certification probability. This is classification, not clustering.

## Supervised Learning
Predicts certification probability from 34 data-selected governed inputs. The saved decision threshold is 0.954638.

## Generative LLM
Converts cleaned video behavior columns into structured text before LLM/NLP representation. This is not raw spoken-video transcription; it is a text representation of the available video columns.

Runtime values are machine-dependent and are recorded in `outputs/tables/deployment_runtime.csv`.
