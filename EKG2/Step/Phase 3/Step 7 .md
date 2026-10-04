## Step 7 — Model Selection, Training, and Experiment Tracking

### 7.1 Select models based on the task

Construct a candidate pool according to the problem. When the data and project scope permit, evaluate at least five meaningfully different candidates for the activated task. Fewer models are acceptable when justified.

#### Classification candidates

- Dummy classifier
- Logistic regression
- Naive Bayes
- k-Nearest Neighbors
- Decision tree
- Random forest or Extra Trees
- Gradient boosting
- XGBoost, LightGBM, or CatBoost
- Support vector machine
- Multilayer perceptron
- CNN or Transformer-based classifier

#### Clustering candidates

- K-Means or MiniBatch K-Means
- Gaussian Mixture Model
- Agglomerative clustering
- BIRCH
- DBSCAN or HDBSCAN
- Spectral clustering
- K-Medoids
- Self-organizing map
- Deep clustering

#### Regression candidates

- Mean or median baseline
- Linear regression or Elastic Net
- Decision tree or random forest
- Gradient boosting
- XGBoost, LightGBM, or CatBoost
- Support vector regression
- Neural network

#### Time-series candidates

- Naive and seasonal-naive forecasts
- Exponential smoothing
- ARIMA or SARIMA
- Prophet
- Gradient-boosted lag model
- State-space model
- RNN, LSTM, or Temporal Fusion Transformer

#### Signal, waveform-image, and longitudinal candidates

- Rule-based or conventional signal-processing baseline
- Regularized linear/logistic model or gradient boosting on validated engineered features
- XGBoost, LightGBM, or CatBoost for tabular, derived-signal, and longitudinal features
- 1D-CNN, temporal convolutional network, RNN, LSTM, GRU, or time-series transformer for native waveform sequences
- CNN, vision transformer, or hybrid vision model for validated waveform images
- Fusion models only when each modality is available at inference time and missing-modality behavior is defined

The candidate list is not a requirement to use deep learning. A model should be activated only when the signal/image quality, sample size, labels, compute, evaluation design, and intended use justify it.

#### Anomaly-detection candidates

- Rule-based baseline
- Robust statistical threshold
- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- Autoencoder

### 7.2 Select a splitting strategy

Use stratified, group, time-series, spatial, entity-aware, or nested cross-validation as appropriate. A general starting point is 70% training, 15% validation, and 15% testing, but the final split must reflect data volume and structure.

For datasets containing repeated observations from the same entity, use a grouped or otherwise entity-aware split for claims about performance on unseen entities. All observations from one entity must remain in one partition. If the intended use is prediction for a known entity at a later time, evaluate that use separately with a strictly forward-in-time split and a documented index time. Report both the split rule and the number of entities and observations in each partition.

### 7.3 Handle imbalanced data

Options include class weighting, threshold adjustment, under-sampling, over-sampling, SMOTE within training folds only, cost-sensitive learning, and focal loss. Never resample validation or test data.

### 7.4 Tune hyperparameters

Use grid search, random search, Bayesian optimization, or successive halving. Never use the test set to select features, models, thresholds, or hyperparameters.

### 7.5 Track experiments

Record the run ID, dataset and feature versions, code version, seed, splitting strategy, preprocessing, model, hyperparameters, runtime, memory, hardware, validation metrics, artifact paths, warnings, and failures.

### Dashboard requirements

- Activated model-track matrix
- Experiment table and validation leaderboard
- Runtime and memory comparison
- Reproducibility status
- Data-split visualization

---
