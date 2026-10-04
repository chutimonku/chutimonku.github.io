"""
scripts/update_html_cnn_llm.py
Enhances ekg_longitudinal_dashboard.html:
1. Adds 1D-CNN Stage 1 / Stage 2 badges inside container-llm-narrative-content.
2. Adds 1D-CAM (Grad-CAM) attention trace on the encounter ECG waveform plot.
3. Ensures valid JS syntax.
"""

import re
import os

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Enhance llmContainer.innerHTML
target_str = "cotHtml += `<div class=\"font-code small text-muted mb-1\">${c}</div>`;\n                });\n\n                llmContainer.innerHTML = `"

replacement_str = """cotHtml += `<div class="font-code small text-muted mb-1">${c}</div>`;
                });

                let cnnBadgesHtml = '';
                if (enc.cnn_predictions) {
                    const cnn = enc.cnn_predictions;
                    const isAbn = cnn.stage1_binary ? cnn.stage1_binary.is_abnormal : false;
                    const pAbn = cnn.stage1_binary ? cnn.stage1_binary.prob_abnormal : 0;
                    const pCls = cnn.stage2_multiclass ? cnn.stage2_multiclass.predicted_class : '';
                    cnnBadgesHtml = `
                        <div class="p-2 mb-3 rounded-3 bg-white border d-flex gap-2 align-items-center flex-wrap">
                            <span class="badge ${isAbn ? 'bg-danger' : 'bg-success'} text-white font-code px-2 py-1">
                                <i class="fas fa-microchip me-1"></i> 1D-CNN Stage 1: ${isAbn ? 'Abnormal (ความเสี่ยง ' + pAbn + '%)' : 'Normal'}
                            </span>
                            <span class="badge bg-primary text-white font-code px-2 py-1">
                                <i class="fas fa-layer-group me-1"></i> 1D-CNN Stage 2: ${pCls}
                            </span>
                            <span class="badge bg-dark text-white font-code px-2 py-1">
                                <i class="fas fa-robot me-1"></i> Clinical LLM Copilot
                            </span>
                            <span class="text-muted small font-code ms-auto">
                                สกัดสัณฐานคลื่นดิบ 500 Hz + Grad-CAM
                            </span>
                        </div>
                    `;
                }

                llmContainer.innerHTML = `
                    ${cnnBadgesHtml}"""

if target_str in content:
    content = content.replace(target_str, replacement_str, 1)
    print("✅ Successfully updated llmContainer with 1D-CNN and LLM Copilot badges!")
else:
    print("⚠️ Target string for llmContainer not found.")

# 2. Enhance updateEncounterWaveformView to add 1D-CAM trace
target_wave_str = """            const traces = [traceSig];
            if (lead === 'II' && enc.r_peaks) {"""

replacement_wave_str = """            const traces = [traceSig];

            // 1D-CAM (Grad-CAM) Attention Points Overlay
            if (enc.cnn_1d_cam_weights && enc.cnn_1d_cam_weights.length > 0) {
                const camX = [];
                const camY = [];
                const camVals = enc.cnn_1d_cam_weights;
                const step = Math.max(1, Math.floor(sig.length / camVals.length));
                for (let k = 0; k < camVals.length; k++) {
                    const idx = k * step;
                    if (idx < sig.length) {
                        camX.push(timeAxis[idx]);
                        camY.push(sig[idx]);
                    }
                }
                traces.push({
                    x: camX,
                    y: camY,
                    type: 'scatter',
                    mode: 'markers',
                    name: '1D-CAM จุดที่ AI ให้ความสำคัญ',
                    marker: {
                        color: camVals,
                        colorscale: 'Reds',
                        size: 6,
                        showscale: false
                    }
                });
            }

            if (lead === 'II' && enc.r_peaks) {"""

if target_wave_str in content:
    content = content.replace(target_wave_str, replacement_wave_str, 1)
    print("✅ Successfully updated updateEncounterWaveformView with 1D-CAM overlay!")
else:
    print("⚠️ Target string for updateEncounterWaveformView not found.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {html_path}, size: {os.path.getsize(html_path):,} bytes.")
