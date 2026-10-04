## Step 2 — Data Gathering, Ingestion, and Provenance

### 2.1 Identify data sources

Use reliable and legally permitted sources such as internal databases, data warehouses, public datasets, APIs, sensors, surveys, media repositories, document collections, authorized web sources, and human annotation.

### 2.2 Record data provenance

Record in `logs/data_provenance.json`:

- Source name, URL, owner, license, and usage restrictions
- Extraction date and covered time period
- Record count and file size
- Languages and modality
- Schema and raw-data version
- SHA-256 hash
- Extraction query or API version
- Sampling method and known limitations

### 2.3 Transform multimodal data

- **Tabular:** numerical, categorical, and ordinal representations
- **Text:** tokens, TF-IDF, linguistic features, or embeddings
- **Images:** pixels, descriptors, or visual embeddings
- **Audio:** waveforms, MFCCs, Mel-spectrograms, or embeddings
- **Video:** frames, motion, optical flow, or multimodal embeddings
- **Time series:** lags, rolling statistics, seasonality, or frequency features
- **Graphs:** node, edge, subgraph, or graph embeddings
- **Multimodal:** early, intermediate, or late fusion

#### Optional extension: physiological signals, clinical waveforms, and scanned waveform images

This extension applies when the project contains a physiological waveform (for example, ECG/EKG, EEG, PPG, respiratory, pressure, or other biosignal) in native digital form, as a device export, or as a photograph/scanned printout. It is an optional modality-specific branch, not a requirement for unrelated projects.

- Preserve the immutable original signal, image, and device export. Record device/vendor, lead or channel names, sampling rate, gain, filter settings where available, acquisition duration, timestamps, calibration marks, and source-system version.
- For a native waveform, verify sampling rate, channel order, units, amplitude scale, time base, signal length, synchronization, gaps, clipping, saturation, and duplicate acquisition identifiers. Never silently resample, relabel leads, or infer unavailable metadata.
- For a scanned or photographed waveform, record image resolution, color space, orientation, crop boundaries, visible lead labels, paper speed, gain, grid scale, annotation/overlay presence, and whether the image is complete enough for the proposed use.
- Image preparation may include orientation correction, deskewing, contrast normalization, illumination correction, crop/alignment of the graph area, grid-line suppression or modeling, and quality flags. Retain the original image and record every derived-image transform; grid removal must not erase the waveform or clinically relevant annotations.
- Signal extraction from an image is a separate, fallible reconstruction task. If it is used, validate the recovered time-series against a suitable reference, preserve an extraction-confidence/quality score, and keep image-derived signals distinct from device-native signals.
- Do not treat an image of a plotted waveform as proof that the underlying digital waveform, timestamps, sampling rate, lead identity, or clinical annotation is available.

### 2.4 Perform initial validation

Check schema consistency, file corruption, counts, unique identifiers, timestamps, label availability, class distribution, consent, unexpected columns, duplicate extraction, and train-serving consistency risks.

For repeated-observation datasets, validate the entity-to-observation cardinality, visit/study ordering, duplicate versus clinically distinct observations, time-zone and clock consistency, and any label delay. A repeated study is not automatically a duplicate. Define the event key that distinguishes a repeated measurement from an accidental re-export.

### Dashboard requirements

- Data-provenance table
- Record counts and time coverage
- Modality and language summaries
- Dataset version and hash
- Known limitations

---