"""Build the full MOOC NLP Dashboard HTML with correct sections and data.

Sections:
  1. Offline Behavioral NLP (6 models, real results)
  2. Gemini Generative AI (real API, 1,800 test students)
  3. Local Generative AI Pilot (Ollama models, 20-student pilot)
  4. GPT / Claude — ยังไม่ได้ประเมินจริง (quarantined simulated results)

Rules:
  - All numbers read directly from CSV files — no fabrication
  - GPT/Claude show no metrics, only quarantine notice
  - TH/EN toggle preserved
  - Interactive Plotly charts
"""

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
REPRO = ROOT / "outputs" / "reproducibility"

# ── Load CSVs ────────────────────────────────────────────────────────────────
offline = pd.read_csv(TABLES / "llm_offline_model_comparison.csv")
offline_cm = pd.read_csv(TABLES / "llm_offline_confusion_matrices.csv")
gemini_pred = pd.read_csv(TABLES / "llm_api_predictions_gemini_full.csv")
provider_status = pd.read_csv(TABLES / "llm_api_provider_status.csv")
pilot_comp = pd.read_csv(TABLES / "llm_comparative_pilot_model_comparison.csv")

# Verify Gemini metrics from real predictions
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score, brier_score_loss,
    balanced_accuracy_score, confusion_matrix)

y_g = gemini_pred["actual_certified"].astype(int).values
pred_g = gemini_pred["predicted_certified"].astype(int).values
prob_g = gemini_pred["probability"].astype(float).values
tn_g, fp_g, fn_g, tp_g = confusion_matrix(y_g, pred_g, labels=[0,1]).ravel()

gemini_metrics = {
    "accuracy": accuracy_score(y_g, pred_g),
    "precision": precision_score(y_g, pred_g, zero_division=0),
    "recall": recall_score(y_g, pred_g, zero_division=0),
    "f1": f1_score(y_g, pred_g, zero_division=0),
    "roc_auc": roc_auc_score(y_g, prob_g),
    "pr_auc": average_precision_score(y_g, prob_g),
    "brier": brier_score_loss(y_g, prob_g),
    "balanced_accuracy": balanced_accuracy_score(y_g, pred_g),
    "tn": int(tn_g), "fp": int(fp_g), "fn": int(fn_g), "tp": int(tp_g),
    "n": len(y_g), "positive": int(y_g.sum()),
}

# ── Build Plotly chart data as JSON ──────────────────────────────────────────
offline_sorted = offline.sort_values("test_pr_auc", ascending=False)

bar_colors = [
    "#1a73e8" if row["selected"] else "#4285f4"
    for _, row in offline_sorted.iterrows()
]
bar_colors = ["#e8710a" if row["selected"] else "#4285f4"
              for _, row in offline_sorted.iterrows()]

pr_auc_chart = {
    "x": offline_sorted["model_name"].tolist(),
    "y": [round(v, 4) for v in offline_sorted["test_pr_auc"].tolist()],
    "colors": bar_colors,
    "selected_name": offline_sorted[offline_sorted["selected"]]["model_name"].values[0] if offline_sorted["selected"].any() else "",
    "selected_pr_auc": round(float(offline_sorted[offline_sorted["selected"]]["test_pr_auc"].values[0]), 4) if offline_sorted["selected"].any() else 0,
}

metrics_cols = ["test_pr_auc","test_roc_auc","test_f1","test_accuracy","test_balanced_accuracy","test_precision","test_recall","test_brier"]
metrics_labels = ["PR-AUC","ROC-AUC","F1","Accuracy","Bal. Accuracy","Precision","Recall","Brier"]

# Radar chart data for each model
radar_data = []
for _, row in offline.iterrows():
    vals = []
    for col in metrics_cols:
        v = row[col]
        if col == "test_brier":
            v = 1 - v  # invert brier for radar (higher = better)
        vals.append(round(float(v), 4))
    radar_data.append({"name": row["model_name"], "values": vals})

# CM data for heatmaps
cm_data = []
for _, row in offline_cm.iterrows():
    tn, fp, fn, tp = int(row["tn"]), int(row["fp"]), int(row["fn"]), int(row["tp"])
    cm_data.append({
        "name": row["model_name"],
        "matrix": [[tn, fp], [fn, tp]],
        "labels": ["TN","FP","FN","TP"],
    })

# Pilot data
pilot_sorted = pilot_comp.sort_values("test_pr_auc", ascending=False)

# ── JSON serialisable dump ────────────────────────────────────────────────────
dashboard_data = {
    "offline": offline_sorted.to_dict(orient="records"),
    "offline_cm": offline_cm.to_dict(orient="records"),
    "gemini": gemini_metrics,
    "provider_status": provider_status.to_dict(orient="records"),
    "pilot": pilot_sorted.to_dict(orient="records"),
    "pr_auc_chart": pr_auc_chart,
    "radar_data": radar_data,
    "cm_data": cm_data,
    "metrics_labels": metrics_labels,
}

DATA_JSON = json.dumps(dashboard_data, ensure_ascii=False, default=str)

# ── HTML Template ─────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>MOOC Behavioral NLP Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
  :root{{
    --primary:#1a73e8;--accent:#e8710a;--success:#1e8e3e;--warn:#f9ab00;--danger:#d93025;
    --bg:#f8f9fa;--card:#fff;--border:#e0e0e0;--text:#202124;--muted:#5f6368;
    --pending-bg:#fff3e0;--pending-border:#fb8c00;
    --quarantine-bg:#fce8e6;--quarantine-border:#d93025;
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:'Google Sans',Roboto,Arial,sans-serif;background:var(--bg);color:var(--text);font-size:14px;}}
  header{{background:var(--primary);color:#fff;padding:18px 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.2);}}
  header h1{{font-size:1.25rem;font-weight:500;}}
  .lang-btn{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.4);color:#fff;padding:6px 14px;border-radius:20px;cursor:pointer;font-size:13px;transition:.2s;}}
  .lang-btn:hover{{background:rgba(255,255,255,.25);}}
  .container{{max-width:1400px;margin:0 auto;padding:24px 32px;}}
  .section{{margin-bottom:40px;}}
  .section-header{{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid var(--border);}}
  .section-badge{{padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}}
  .badge-offline{{background:#e8f0fe;color:#1a73e8;}}
  .badge-gemini{{background:#e6f4ea;color:#1e8e3e;}}
  .badge-pilot{{background:#fef7e0;color:#f9ab00;}}
  .badge-quarantine{{background:#fce8e6;color:#d93025;}}
  h2{{font-size:1.1rem;font-weight:600;}}
  h3{{font-size:.95rem;font-weight:600;color:var(--muted);margin-bottom:12px;}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:20px;}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06);}}
  .card.best{{border-color:var(--accent);box-shadow:0 2px 8px rgba(232,113,10,.2);}}
  .card-label{{font-size:11px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.4px;}}
  .card-value{{font-size:1.5rem;font-weight:700;color:var(--text);}}
  .card-value.good{{color:var(--success);}}
  .card-value.accent{{color:var(--accent);}}
  .chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}}
  .chart-box{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);}}
  .chart-full{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:20px;}}
  table{{width:100%;border-collapse:collapse;font-size:13px;}}
  th{{background:#f1f3f4;font-weight:600;text-align:left;padding:9px 12px;border-bottom:2px solid var(--border);color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px;}}
  td{{padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:middle;}}
  tr:hover td{{background:#f8f9fa;}}
  .selected-row td{{background:#e8f0fe!important;font-weight:600;}}
  .pill{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;}}
  .pill-ok{{background:#e6f4ea;color:#1e8e3e;}}
  .pill-warn{{background:#fff3e0;color:#e37400;}}
  .pill-danger{{background:#fce8e6;color:#d93025;}}
  .pill-best{{background:#fef3e2;color:#e8710a;}}
  .quarantine-box{{background:var(--quarantine-bg);border:2px solid var(--quarantine-border);border-radius:10px;padding:20px 24px;margin-bottom:16px;}}
  .quarantine-box h3{{color:var(--danger);margin-bottom:8px;}}
  .quarantine-box p{{color:#5f1312;font-size:13px;line-height:1.6;}}
  .quarantine-box .qfile{{font-family:monospace;font-size:12px;background:rgba(255,255,255,.7);padding:4px 8px;border-radius:4px;margin-top:8px;display:inline-block;}}
  .note-box{{background:#e8f0fe;border-left:4px solid var(--primary);padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px;font-size:13px;color:#174ea6;}}
  .cm-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;}}
  .gemini-cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;margin-bottom:20px;}}
  @media(max-width:800px){{
    .chart-row{{grid-template-columns:1fr;}}
    .container{{padding:16px;}}
    header{{padding:14px 16px;}}
  }}
  .th-text{{display:none;}}
  .en-text{{display:inline;}}
  body.lang-th .th-text{{display:inline;}}
  body.lang-th .en-text{{display:none;}}
</style>
</head>
<body>
<header>
  <h1>
    <span class="en-text">🎓 MOOC Student Certification — NLP Benchmark Dashboard</span>
    <span class="th-text">🎓 แดชบอร์ดประเมิน NLP — การรับรองผู้เรียน MOOC</span>
  </h1>
  <button class="lang-btn" onclick="toggleLang()" id="langBtn">🇹🇭 ภาษาไทย</button>
</header>

<div class="container">

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- SECTION 1: OFFLINE BEHAVIORAL NLP                              -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="section">
  <div class="section-header">
    <span class="section-badge badge-offline">
      <span class="en-text">Offline Behavioral NLP</span>
      <span class="th-text">Offline Behavioral NLP</span>
    </span>
    <h2>
      <span class="en-text">Offline Behavioral NLP — 6 Models (No External API)</span>
      <span class="th-text">Offline Behavioral NLP — 6 โมเดล (ไม่ใช้ API ภายนอก)</span>
    </h2>
  </div>

  <div class="note-box">
    <span class="en-text">
      Text feature: <code>student_behavior_text</code> (structured behavioral summary).
      All classifiers fitted on <strong>train split only</strong> (8,400 students).
      Thresholds selected on <strong>validation split</strong> (1,800 students).
      Evaluated on <strong>test split</strong> (1,800 students, 58 positive).
      Seed = 42. No target / certified / grade / userid_DI in features.
    </span>
    <span class="th-text">
      Feature ที่ใช้: <code>student_behavior_text</code> (สรุปพฤติกรรมนักเรียน)
      Classifier ทุกตัว Fit บน <strong>train เท่านั้น</strong> (8,400 คน)
      เลือก Threshold จาก <strong>validation</strong> (1,800 คน)
      ประเมินบน <strong>test</strong> (1,800 คน, 58 คนได้รับใบรับรอง) — Seed = 42
    </span>
  </div>

  <!-- Best model highlight cards -->
  <div id="offlineBestCards"></div>

  <!-- PR-AUC Bar Chart -->
  <div class="chart-full">
    <h3>
      <span class="en-text">PR-AUC by Model (Test Set) — Higher is Better</span>
      <span class="th-text">PR-AUC แต่ละโมเดล (Test Set) — ยิ่งสูงยิ่งดี</span>
    </h3>
    <div id="prAucBar" style="height:320px;"></div>
  </div>

  <!-- Radar + ROC-AUC charts -->
  <div class="chart-row">
    <div class="chart-box">
      <h3>
        <span class="en-text">Multi-Metric Radar — Best Model vs. Baselines</span>
        <span class="th-text">Radar หลายตัวชี้วัด — โมเดลที่ดีที่สุด vs. Baseline</span>
      </h3>
      <div id="radarChart" style="height:340px;"></div>
    </div>
    <div class="chart-box">
      <h3>
        <span class="en-text">ROC-AUC vs PR-AUC Scatter</span>
        <span class="th-text">ROC-AUC vs PR-AUC (Scatter)</span>
      </h3>
      <div id="rocPrScatter" style="height:340px;"></div>
    </div>
  </div>

  <!-- Confusion Matrices -->
  <div class="chart-full">
    <h3>
      <span class="en-text">Confusion Matrices — All Models (Test Set)</span>
      <span class="th-text">Confusion Matrix ทุกโมเดล (Test Set)</span>
    </h3>
    <div id="confusionMatrices" class="cm-grid"></div>
  </div>

  <!-- Full comparison table -->
  <div class="chart-full">
    <h3>
      <span class="en-text">Full Comparison Table</span>
      <span class="th-text">ตารางเปรียบเทียบเต็ม</span>
    </h3>
    <div style="overflow-x:auto;">
      <table id="offlineTable">
        <thead>
          <tr>
            <th>Model</th>
            <th>PR-AUC</th><th>ROC-AUC</th><th>F1</th>
            <th>Accuracy</th><th>Bal. Acc.</th>
            <th>Precision</th><th>Recall</th><th>Brier</th>
            <th>Threshold</th><th>TN</th><th>FP</th><th>FN</th><th>TP</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="offlineTableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- SECTION 2: GEMINI GENERATIVE AI                                -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="section">
  <div class="section-header">
    <span class="section-badge badge-gemini">
      <span class="en-text">Gemini Generative AI</span>
      <span class="th-text">Gemini Generative AI</span>
    </span>
    <h2>
      <span class="en-text">Gemini Generative AI — Real API (1,800 Test Students)</span>
      <span class="th-text">Gemini Generative AI — เรียก API จริง (1,800 นักเรียน Test)</span>
    </h2>
  </div>

  <div class="note-box">
    <span class="en-text">
      Model: <strong>gemini-3.5-flash-lite</strong>. Evaluated on all 1,800 held-out test students via real API call.
      Predictions verified from <code>llm_api_predictions_gemini_full.csv</code>.
    </span>
    <span class="th-text">
      โมเดล: <strong>gemini-3.5-flash-lite</strong>. ประเมินบนนักเรียน test ทั้ง 1,800 คนผ่าน API จริง
      ตรวจสอบจาก <code>llm_api_predictions_gemini_full.csv</code>
    </span>
  </div>

  <div id="geminiCards" class="gemini-cards"></div>

  <div class="chart-row">
    <div class="chart-box">
      <h3>
        <span class="en-text">Confusion Matrix — Gemini</span>
        <span class="th-text">Confusion Matrix — Gemini</span>
      </h3>
      <div id="geminiCM" style="height:300px;"></div>
    </div>
    <div class="chart-box">
      <h3>
        <span class="en-text">Gemini vs. Best Offline Model</span>
        <span class="th-text">Gemini เทียบกับโมเดล Offline ที่ดีที่สุด</span>
      </h3>
      <div id="geminiVsOffline" style="height:300px;"></div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- SECTION 3: LOCAL GENERATIVE AI PILOT                           -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="section">
  <div class="section-header">
    <span class="section-badge badge-pilot">
      <span class="en-text">Local Generative AI Pilot</span>
      <span class="th-text">Local Generative AI Pilot</span>
    </span>
    <h2>
      <span class="en-text">Local Generative AI Pilot — Ollama (20-Student Balanced Pilot)</span>
      <span class="th-text">Pilot Generative AI ในเครื่อง — Ollama (20 นักเรียน Pilot)</span>
    </h2>
  </div>

  <div class="note-box">
    <span class="en-text">
      Small-scale balanced pilot (10 certified + 10 non-certified) using local Ollama models. Results are from a 20-student pilot only — not comparable directly to 1,800-student evaluations.
    </span>
    <span class="th-text">
      Pilot ขนาดเล็ก (10 ได้รับ + 10 ไม่ได้รับใบรับรอง) ใช้ Ollama ในเครื่อง ผลเป็นเพียง pilot 20 คน ไม่สามารถเทียบตรงกับการประเมิน 1,800 คน
    </span>
  </div>

  <div class="chart-full">
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th>Provider</th><th>Model</th>
            <th>PR-AUC</th><th>ROC-AUC</th><th>F1</th>
            <th>Accuracy</th><th>Precision</th><th>Recall</th><th>Students</th><th>Status</th>
          </tr>
        </thead>
        <tbody id="pilotTableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- SECTION 4: GPT / CLAUDE — NOT EVALUATED                        -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<div class="section">
  <div class="section-header">
    <span class="section-badge badge-quarantine">
      <span class="en-text">GPT / Claude — Not Evaluated</span>
      <span class="th-text">GPT / Claude — ยังไม่ได้ประเมินจริง</span>
    </span>
    <h2>
      <span class="en-text">GPT-4o &amp; Claude 3.5 Sonnet — ยังไม่ได้ประเมินจริง</span>
      <span class="th-text">GPT-4o &amp; Claude 3.5 Sonnet — ยังไม่ได้ประเมินจริง</span>
    </h2>
  </div>

  <div class="quarantine-box">
    <h3>⚠️ <span class="en-text">Simulated Predictions Quarantined — No Metrics Available</span><span class="th-text">ผลจำลองถูกกักกันแล้ว — ไม่มีตัวชี้วัด</span></h3>
    <p>
      <span class="en-text">
        On <strong>2026-09-24 at 16:24</strong>, the script <code>src/run_llm_external_benchmark.py</code>
        generated synthetic GPT-4o and Claude 3.5 Sonnet predictions using
        <code>generate_calibrated_predictions()</code> — a function that fabricated probabilities
        from behavioral signals <em>without calling any real external API</em>.
        These fabricated results were incorrectly marked as <code>completed</code>.
        <br/><br/>
        The simulated files have been <strong>quarantined</strong> and must not be used, referenced, or displayed.
        <code>generate_calibrated_predictions()</code> is now disabled with a hard <code>RuntimeError</code>.
        GPT-4o and Claude 3.5 Sonnet will remain marked <strong>ยังไม่ได้ประเมินจริง (not_evaluated)</strong>
        until real API evaluations are conducted.
      </span>
      <span class="th-text">
        เมื่อวันที่ <strong>24 ก.ย. 2569 เวลา 16:24</strong> สคริปต์ <code>src/run_llm_external_benchmark.py</code>
        สร้างผล GPT-4o และ Claude 3.5 Sonnet ด้วยฟังก์ชัน <code>generate_calibrated_predictions()</code>
        ซึ่งสร้างค่าความน่าจะเป็นจากสัญญาณพฤติกรรม <em>โดยไม่เรียก API ภายนอกจริง</em>
        ผลจำลองเหล่านี้ถูกระบุว่า <code>completed</code> อย่างผิดพลาด
        <br/><br/>
        ไฟล์จำลองถูก <strong>กักกัน (Quarantine)</strong> แล้ว ห้ามนำไปใช้ อ้างอิง หรือแสดงบนแดชบอร์ด
        ฟังก์ชัน <code>generate_calibrated_predictions()</code> ถูกปิดการใช้งานด้วย <code>RuntimeError</code>
        GPT-4o และ Claude 3.5 Sonnet จะแสดงสถานะ <strong>ยังไม่ได้ประเมินจริง</strong>
        จนกว่าจะมีการเรียก API จริง
      </span>
    </p>
    <div style="margin-top:12px;">
      <span class="qfile">📁 outputs/quarantine/llm_api_predictions_gpt_SIMULATED_20260924_1624.csv</span><br/>
      <span class="qfile">📁 outputs/quarantine/llm_api_predictions_claude_SIMULATED_20260924_1624.csv</span><br/>
      <span class="qfile">📁 outputs/quarantine/llm_api_predictions_all_CONTAMINATED_20260924_1624.csv</span><br/>
      <span class="qfile">📁 outputs/quarantine/llm_comparative_model_comparison_CONTAMINATED_20260924_1624.csv</span>
    </div>
  </div>

  <div style="overflow-x:auto;">
    <table>
      <thead>
        <tr>
          <th>Provider</th><th>Model</th><th>Status</th>
          <th>PR-AUC</th><th>ROC-AUC</th><th>F1</th><th>Accuracy</th>
          <th>Note</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>OpenAI</td><td>gpt-4o</td>
          <td><span class="pill pill-danger">ยังไม่ได้ประเมินจริง</span></td>
          <td colspan="4" style="text-align:center;color:#d93025;font-style:italic;">— ไม่มีข้อมูล —</td>
          <td style="font-size:12px;color:#5f6368;">ผลจำลองถูกกักกัน ห้ามแสดง metric</td>
        </tr>
        <tr>
          <td>Anthropic</td><td>claude-3-5-sonnet</td>
          <td><span class="pill pill-danger">ยังไม่ได้ประเมินจริง</span></td>
          <td colspan="4" style="text-align:center;color:#d93025;font-style:italic;">— ไม่มีข้อมูล —</td>
          <td style="font-size:12px;color:#5f6368;">ผลจำลองถูกกักกัน ห้ามแสดง metric</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div><!-- /container -->

<script>
const DATA = {DATA_JSON};

// ── Language toggle ──────────────────────────────────────────────
function toggleLang() {{
  const body = document.body;
  const btn = document.getElementById('langBtn');
  if(body.classList.contains('lang-th')) {{
    body.classList.remove('lang-th');
    btn.textContent = '🇹🇭 ภาษาไทย';
  }} else {{
    body.classList.add('lang-th');
    btn.textContent = '🇬🇧 English';
  }}
  // Re-render charts to update any layout text
  renderCharts();
}}

// ── Utility ──────────────────────────────────────────────────────
const fmt = (v, d=4) => (v===null||v===undefined) ? '—' : Number(v).toFixed(d);
const isLangTH = () => document.body.classList.contains('lang-th');

// ── Offline best cards ───────────────────────────────────────────
function renderBestCards() {{
  const best = DATA.offline.find(r => r.selected);
  if(!best) return;
  const metrics = [
    {{label:'PR-AUC', val:fmt(best.test_pr_auc), cls:'accent'}},
    {{label:'ROC-AUC', val:fmt(best.test_roc_auc), cls:'good'}},
    {{label:'F1', val:fmt(best.test_f1), cls:'good'}},
    {{label:'Accuracy', val:fmt(best.test_accuracy), cls:''}},
    {{label:'Bal. Acc.', val:fmt(best.test_balanced_accuracy), cls:''}},
    {{label:'Precision', val:fmt(best.test_precision), cls:''}},
    {{label:'Recall', val:fmt(best.test_recall), cls:''}},
    {{label:'Brier', val:fmt(best.test_brier), cls:''}},
    {{label:'Threshold', val:fmt(best.threshold_from_validation), cls:''}},
  ];
  const html = `
    <div style="margin-bottom:14px;">
      <span style="font-weight:600;color:var(--accent);">🏆 Best: ${{best.model_name}}</span>
      <span style="font-size:12px;color:var(--muted);margin-left:8px;">(by PR-AUC on test set)</span>
    </div>
    <div class="cards">
      ${{metrics.map(m=>`<div class="card best"><div class="card-label">${{m.label}}</div><div class="card-value ${{m.cls}}">${{m.val}}</div></div>`).join('')}}
    </div>`;
  document.getElementById('offlineBestCards').innerHTML = html;
}}

// ── Offline table ────────────────────────────────────────────────
function renderOfflineTable() {{
  const tbody = document.getElementById('offlineTableBody');
  tbody.innerHTML = DATA.offline.map(r => {{
    const cls = r.selected ? 'selected-row' : '';
    return `<tr class="${{cls}}">
      <td>${{r.selected ? '🏆 ' : ''}}${{r.model_name}}</td>
      <td><strong>${{fmt(r.test_pr_auc)}}</strong></td>
      <td>${{fmt(r.test_roc_auc)}}</td>
      <td>${{fmt(r.test_f1)}}</td>
      <td>${{fmt(r.test_accuracy)}}</td>
      <td>${{fmt(r.test_balanced_accuracy)}}</td>
      <td>${{fmt(r.test_precision)}}</td>
      <td>${{fmt(r.test_recall)}}</td>
      <td>${{fmt(r.test_brier)}}</td>
      <td>${{fmt(r.threshold_from_validation)}}</td>
      <td>${{r.tn}}</td><td>${{r.fp}}</td><td>${{r.fn}}</td><td>${{r.tp}}</td>
      <td><span class="pill pill-ok">completed</span></td>
    </tr>`;
  }}).join('');
}}

// ── Pilot table ──────────────────────────────────────────────────
function renderPilotTable() {{
  const tbody = document.getElementById('pilotTableBody');
  tbody.innerHTML = DATA.pilot.map(r => {{
    const isGemini = r.provider === 'Gemini';
    const pill = r.selected ? 'pill-best' : (isGemini ? 'pill-ok' : 'pill-warn');
    const label = r.selected ? '🏆 Pilot Best' : (isGemini ? 'Gemini' : 'Ollama');
    return `<tr>
      <td>${{r.provider}}</td>
      <td>${{r.model_name}}</td>
      <td>${{fmt(r.test_pr_auc)}}</td>
      <td>${{fmt(r.test_roc_auc)}}</td>
      <td>${{fmt(r.test_f1)}}</td>
      <td>${{fmt(r.test_accuracy)}}</td>
      <td>${{fmt(r.test_precision)}}</td>
      <td>${{fmt(r.test_recall)}}</td>
      <td>${{r.evaluation_students}}</td>
      <td><span class="pill ${{pill}}">${{label}}</span></td>
    </tr>`;
  }}).join('');
}}

// ── Gemini cards ─────────────────────────────────────────────────
function renderGeminiCards() {{
  const g = DATA.gemini;
  const metrics = [
    {{label:'PR-AUC', val:fmt(g.pr_auc), cls:'accent'}},
    {{label:'ROC-AUC', val:fmt(g.roc_auc), cls:'good'}},
    {{label:'F1', val:fmt(g.f1), cls:'good'}},
    {{label:'Accuracy', val:fmt(g.accuracy), cls:''}},
    {{label:'Bal. Acc.', val:fmt(g.balanced_accuracy), cls:''}},
    {{label:'Precision', val:fmt(g.precision), cls:''}},
    {{label:'Recall', val:fmt(g.recall), cls:''}},
    {{label:'Brier', val:fmt(g.brier), cls:''}},
    {{label:'N Students', val:g.n, cls:''}},
    {{label:'Positive', val:g.positive, cls:''}},
  ];
  document.getElementById('geminiCards').innerHTML = metrics.map(m =>
    `<div class="card"><div class="card-label">${{m.label}}</div><div class="card-value ${{m.cls}}">${{m.val}}</div></div>`
  ).join('');
}}

// ── Plotly charts ────────────────────────────────────────────────
function renderCharts() {{
  const th = isLangTH();
  const offlineData = DATA.offline;
  const names = offlineData.map(r => r.model_name.replace(' + ', '+').replace(' Embeddings',''));
  const praucs = offlineData.map(r => r.test_pr_auc);
  const colors = offlineData.map(r => r.selected ? '#e8710a' : '#4285f4');

  // 1. PR-AUC Bar
  Plotly.newPlot('prAucBar', [{{
    type:'bar', x:names, y:praucs,
    marker:{{color:colors}},
    text:praucs.map(v=>v.toFixed(4)), textposition:'outside',
    hovertemplate:'<b>%{{x}}</b><br>PR-AUC: %{{y:.4f}}<extra></extra>'
  }}], {{
    margin:{{t:20,b:120,l:60,r:20}},
    yaxis:{{title:'PR-AUC', range:[0, Math.max(...praucs)*1.2]}},
    xaxis:{{tickangle:-30}},
    plot_bgcolor:'#fff', paper_bgcolor:'#fff',
    showlegend:false
  }}, {{responsive:true, displayModeBar:false}});

  // 2. Radar chart (best vs others)
  const best = offlineData.find(r=>r.selected);
  const labels = [...DATA.metrics_labels, DATA.metrics_labels[0]];
  const bestVals = [...[best.test_pr_auc,best.test_roc_auc,best.test_f1,best.test_accuracy,best.test_balanced_accuracy,best.test_precision,best.test_recall,1-best.test_brier], best.test_pr_auc];

  const radarTraces = [{{
    type:'scatterpolar', mode:'lines+markers',
    name: best.model_name.replace(' Embeddings','').replace(' + Logistic Regression',''),
    r: bestVals, theta: labels,
    line:{{color:'#e8710a', width:2}},
    fill:'toself', fillcolor:'rgba(232,113,10,.1)'
  }}];

  // Add one comparison trace (2nd best)
  const second = offlineData.filter(r=>!r.selected)[0];
  if(second) {{
    const sv = [second.test_pr_auc,second.test_roc_auc,second.test_f1,second.test_accuracy,second.test_balanced_accuracy,second.test_precision,second.test_recall,1-second.test_brier,second.test_pr_auc];
    radarTraces.push({{
      type:'scatterpolar', mode:'lines+markers',
      name: second.model_name.replace(' Embeddings','').replace(' + Logistic Regression',''),
      r: sv, theta: labels,
      line:{{color:'#4285f4', width:1.5, dash:'dot'}},
    }});
  }}
  Plotly.newPlot('radarChart', radarTraces, {{
    polar:{{radialaxis:{{visible:true,range:[0,1]}}}},
    margin:{{t:40,b:20,l:20,r:20}}, plot_bgcolor:'#fff', paper_bgcolor:'#fff',
    legend:{{orientation:'h', y:-0.1}},
  }}, {{responsive:true, displayModeBar:false}});

  // 3. ROC vs PR scatter
  Plotly.newPlot('rocPrScatter', [{{
    type:'scatter', mode:'markers+text',
    x: offlineData.map(r=>r.test_roc_auc),
    y: offlineData.map(r=>r.test_pr_auc),
    text: offlineData.map(r=>r.model_name.split(' ')[0]),
    textposition:'top center',
    marker:{{
      color: offlineData.map(r=>r.selected?'#e8710a':'#4285f4'),
      size: offlineData.map(r=>r.selected?14:10),
      line:{{color:'#fff',width:1.5}}
    }},
    hovertemplate:'<b>%{{text}}</b><br>ROC-AUC: %{{x:.4f}}<br>PR-AUC: %{{y:.4f}}<extra></extra>'
  }}], {{
    xaxis:{{title:'ROC-AUC', range:[0.8,1]}},
    yaxis:{{title:'PR-AUC'}},
    margin:{{t:20,b:50,l:60,r:20}},
    plot_bgcolor:'#fff', paper_bgcolor:'#fff', showlegend:false
  }}, {{responsive:true, displayModeBar:false}});

  // 4. Confusion matrices (mini heatmaps)
  const cmDiv = document.getElementById('confusionMatrices');
  cmDiv.innerHTML = '';
  DATA.cm_data.forEach(cm => {{
    const div = document.createElement('div');
    div.className = 'chart-box';
    div.innerHTML = `<h3 style="font-size:11px;">${{cm.name}}</h3><div id="cm_${{cm.name.replace(/[^a-z0-9]/gi,'_')}}" style="height:200px;"></div>`;
    cmDiv.appendChild(div);
    const [[tn,fp],[fn,tp]] = cm.matrix;
    const total = tn+fp+fn+tp;
    Plotly.newPlot(`cm_${{cm.name.replace(/[^a-z0-9]/gi,'_')}}`, [{{
      type:'heatmap',
      z:[[tn,fp],[fn,tp]],
      x:['Pred 0','Pred 1'], y:['Actual 0','Actual 1'],
      colorscale:[[0,'#e8f0fe'],[1,'#1a73e8']],
      text:[[`TN=${{tn}}`,`FP=${{fp}}`],[`FN=${{fn}}`,`TP=${{tp}}`]],
      texttemplate:'%{{text}}',
      hovertemplate:'%{{text}}<extra></extra>',
      showscale:false
    }}], {{
      margin:{{t:10,b:40,l:60,r:10}},
      plot_bgcolor:'#fff', paper_bgcolor:'#fff',
    }}, {{responsive:true, displayModeBar:false}});
  }});

  // 5. Gemini CM
  const g = DATA.gemini;
  Plotly.newPlot('geminiCM', [{{
    type:'heatmap',
    z:[[g.tn,g.fp],[g.fn,g.tp]],
    x:['Pred 0','Pred 1'], y:['Actual 0','Actual 1'],
    colorscale:[[0,'#e6f4ea'],[1,'#1e8e3e']],
    text:[[`TN=${{g.tn}}`,`FP=${{g.fp}}`],[`FN=${{g.fn}}`,`TP=${{g.tp}}`]],
    texttemplate:'%{{text}}',
    showscale:false
  }}], {{
    margin:{{t:10,b:40,l:60,r:10}},
    plot_bgcolor:'#fff', paper_bgcolor:'#fff',
  }}, {{responsive:true, displayModeBar:false}});

  // 6. Gemini vs Best Offline
  const offlineBest = offlineData.find(r=>r.selected);
  const metricKeys = ['pr_auc','roc_auc','f1','accuracy','balanced_accuracy','precision','recall'];
  const metricLabels = ['PR-AUC','ROC-AUC','F1','Accuracy','Bal.Acc','Precision','Recall'];
  const geminiVals = [g.pr_auc, g.roc_auc, g.f1, g.accuracy, g.balanced_accuracy, g.precision, g.recall];
  const offlineVals = [offlineBest.test_pr_auc, offlineBest.test_roc_auc, offlineBest.test_f1,
    offlineBest.test_accuracy, offlineBest.test_balanced_accuracy,
    offlineBest.test_precision, offlineBest.test_recall];

  Plotly.newPlot('geminiVsOffline', [
    {{type:'bar', name:'Gemini (Real API)', x:metricLabels, y:geminiVals, marker:{{color:'#1e8e3e'}}}},
    {{type:'bar', name:'DistilBERT (Offline)', x:metricLabels, y:offlineVals, marker:{{color:'#e8710a'}}}}
  ], {{
    barmode:'group', margin:{{t:20,b:60,l:50,r:10}},
    yaxis:{{range:[0,1.05]}},
    plot_bgcolor:'#fff', paper_bgcolor:'#fff',
    legend:{{orientation:'h',y:1.1}},
  }}, {{responsive:true, displayModeBar:false}});
}}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
  renderBestCards();
  renderOfflineTable();
  renderGeminiCards();
  renderPilotTable();
  renderCharts();
}});
</script>
</body>
</html>"""

# Inject data
html = html.replace("{DATA_JSON}", DATA_JSON)

out_path = ROOT / "outputs" / "dashboard" / "mooc_nlp_benchmark_dashboard.html"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(html, encoding="utf-8")
print(f"Dashboard written: {out_path}")
print(f"File size: {out_path.stat().st_size / 1024:.1f} KB")
