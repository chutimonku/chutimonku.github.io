# README.md

# PTB‑XL Longitudinal EKG Analytics

## 📚 Master Navigation Index

This repository follows a **Modular Phase‑Based Architecture**. Each phase corresponds to a major step in the data pipeline and is documented under `workflow_docs/`. The navigation sidebar (shown below) links directly to the detailed markdown guides.

---

### 📂 Repository Layout

```
.
├── src/                                 # Core pipeline code
│   ├── ingestion/        load_ptbxl.py
│   ├── cleaning/         filter_signals.py
│   ├── features/         extract_hrv.py
│   ├── training/         train_model.py
│   ├── visualization/    generate_html_dashboard.py
│   └── main_pipeline_router.py   <-- **Master router** (entry point)
├── outputs/
│   └── dashboard/
│       ├── app.py                     <-- **Modular Streamlit app**
│       ├── page_governance.py
│       ├── page_denoising.py
│       ├── page_features.py
│       ├── page_model.py
│       └── page_patient.py
├── workflow_docs/                     <-- Documentation per phase/step
│   ├── phase_1/step_1_1.md
│   ├── phase_2/step_2_1.md
│   ├── phase_3/step_3_1.md
│   ├── phase_4/step_4_1.md
│   └── phase_5/step_5_1.md
├── config/
│   └── project_config.yaml
├── data/...
└── ...
``` 

---

### 🔗 Quick Links (Sidebar Menu)

| Phase | Step | Documentation |
|-------|------|----------------|
| **Phase 1 – Ingestion** | Step 1.1 | [Ingestion & Data Foundation](workflow_docs/phase_1/step_1_1.md) |
| **Phase 2 – Signal Denoising** | Step 2.1 | [Signal Denoising & SQI](workflow_docs/phase_2/step_2_1.md) |
| **Phase 3 – Feature Extraction** | Step 3.1 | [HRV Feature Extraction & Fusion](workflow_docs/phase_3/step_3_1.md) |
| **Phase 4 – Model Training** | Step 4.1 | [GroupKFold Model Training & Validation](workflow_docs/phase_4/step_4_1.md) |
| **Phase 5 – Dashboard / Inspection** | Step 5.1 | [Patient Longitudinal Dashboard & XAI](workflow_docs/phase_5/step_5_1.md) |

---

### 🚀 Running the Pipeline

The **master router** provides a single entry point:

```bash
# Run the whole pipeline end‑to‑end
python src/main_pipeline_router.py

# Run a single phase (e.g., feature extraction)
python src/main_pipeline_router.py step3
```

See `src/main_pipeline_router.py` for the full command‑line interface.

---

### 🎯 Goal

- **One file = one sub‑step** – simplifies testing, versioning, and reuse.
- **Dedicated dashboard pages** – each major step lives in its own Streamlit module.
- **Central router** – orchestrates the workflow while allowing independent execution.

Feel free to explore the docs, tweak the code, and extend the pipeline!
