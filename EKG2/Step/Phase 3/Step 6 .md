# Phase 3: Feature and Model Development

## Step 6 — Feature Engineering and Selection

### 6.1 Split data before learned preprocessing

Create separate training, validation, and test sets. Any operation with `.fit()` must be fitted exclusively on training data. Validation and test data may only use `.transform()`.

### 6.2 Create candidate features

Examples include ratios, rates, differences, interactions, polynomial terms, time-since-event variables, lags, rolling statistics, frequency features, linguistic features, media embeddings, and domain-specific scores.

Every feature must be available at inference time, avoid future information, have a statistical or domain rationale, have a documented formula and version, and be reproducible in production.

#### Optional physiological-signal and waveform-image feature paths

Choose one or more paths only when supported by the source data and the problem; compare them fairly using the same eligible cohort and leakage controls.

1. **Direct vision path.** Use a suitably prepared waveform image directly with image normalization, resizing, and a validated vision model or visual embedding. Candidate backbones may include CNNs or vision transformers such as ResNet, EfficientNet, or ViT. Preserve aspect ratio, calibration information, and lead layout when clinically relevant; do not crop away information simply to fit a standard image size.
2. **Signal-reconstruction path.** Convert a waveform image to a digitized time series only after validation of calibration, grid scale, lead separation, trace extraction, and reconstruction error. Image processing, OCR, and line-tracing may support this path, but extracted signals must be labeled as image-derived and must not be presented as device-native data.
3. **Native signal path.** Start from the device-native waveform, apply justified quality processing, and derive time-domain, frequency-domain, time-frequency, morphology, and learned representation features as appropriate.

Candidate time-domain features include peak locations and confidence; beat count; heart-rate summary; RR intervals; heart-rate variability; P-wave, QRS, and T-wave morphology; PR, QRS, QT, and corrected-QT intervals; amplitude and axis features; beat-to-beat variation; and signal-quality indicators. Their definitions, units, lead choice, detection method, failure behavior, and clinical assumptions must be documented. These measurements are not universally reliable across all rhythms, leads, devices, populations, or image-derived signals.

Candidate frequency-domain features include Fourier/PSD summaries, band power, spectral entropy, and low-/high-frequency HRV measures when their physiological interpretation is appropriate. Candidate time-frequency representations include STFT spectrograms and wavelet/CWT scalograms. Feature extraction must use only the information available at the stated prediction time.

For repeated measurements, construct longitudinal features only from observations available before the index time: count of prior studies, elapsed time since prior study, within-entity trend, variability, and change-from-baseline. Do not use future studies or outcomes.

### 6.3 Transform features

#### Log transformation

$$
y=\log(1+x)
$$

#### Standard scaling

$$
z=\frac{x-\mu_{\text{train}}}{\sigma_{\text{train}}}
$$

#### Robust scaling

$$
z_{\text{robust}}=\frac{x-\mathrm{Median}_{\text{train}}}{Q3_{\text{train}}-Q1_{\text{train}}}
$$

Other options include power and quantile transformations, binning, one-hot and ordinal encoding, cross-fitted target encoding, dimensionality reduction, and embedding reduction.

### 6.4 Select features

Consider domain relevance, missingness, variance, multicollinearity, mutual information, regularization, permutation importance, recursive elimination, stability across folds, collection cost, and inference-time availability.

### 6.5 Conduct ablation studies

Compare baseline features, engineered features, reduced sets, and full sets to demonstrate whether new features add stable value.

For multimodal work, ablate modalities and quality gates separately: metadata/tabular baseline; native-signal features; image path; image-derived signal path; and fused model. Report coverage and failure rates for each branch so an apparent performance gain is not caused by evaluating only the easiest records.

### Dashboard requirements

- Before-and-after distributions
- Feature-lineage table
- Selected and removed features
- Leakage-check results
- Train-only fitting verification
- Ablation comparison

---