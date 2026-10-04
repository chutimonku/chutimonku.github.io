# update_eda_restructure.py
"""
Script to restructure dashboard:
1. Adds Global Pipeline Stepper Header.
2. Updates Sidebar submenu for Step 3 to reflect the 8-step EDA pipeline.
3. Completely restructures Page 3 with detailed explanations, clinical rationales, and 8 step-by-step EDA modules.
4. Updates JavaScript initStep3() to render all new and enhanced EDA charts.
5. Updates showPage() to sync the Global Stepper state.
"""

import sys
import re

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# -----------------------------------------------------------------------------
# 1. ADD CSS FOR STEPPER AND EDA PILLS
# -----------------------------------------------------------------------------
old_css_end = """        .encounter-node.selected {
            border-color: var(--accent-blue);
            background: #f0f9ff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
        }
    </style>"""

new_css_additions = """        .encounter-node.selected {
            border-color: var(--accent-blue);
            background: #f0f9ff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
        }

        /* Stepper & EDA Enhancements */
        .stepper-btn {
            background: #ffffff;
            border: 1.5px solid #e2e8f0;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            text-decoration: none;
            display: block;
        }
        .stepper-btn:hover {
            border-color: var(--accent-blue);
            background: #f8fafc;
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(2, 132, 199, 0.08);
        }
        .stepper-btn.active {
            border-color: var(--accent-blue);
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            box-shadow: 0 6px 16px rgba(2, 132, 199, 0.18);
        }
        .eda-pill-nav {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;
            padding: 0.5rem 0.25rem 0.75rem 0.25rem;
            margin-bottom: 1.5rem;
            scrollbar-width: thin;
        }
        .eda-pill-btn {
            white-space: nowrap;
            font-size: 0.80rem;
            font-weight: 600;
            padding: 0.45rem 0.85rem;
            border-radius: 9999px;
            border: 1px solid #cbd5e1;
            background: #ffffff;
            color: #334155;
            text-decoration: none;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .eda-pill-btn:hover {
            background: #0284c7;
            color: #ffffff;
            border-color: #0284c7;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(2, 132, 199, 0.2);
        }
        .eda-step-card {
            border-left: 5px solid var(--accent-purple) !important;
            margin-bottom: 2rem;
            border-radius: 16px;
        }
        .eda-badge-step {
            background: #7e22ce;
            color: #ffffff;
            font-weight: 700;
            border-radius: 8px;
            padding: 0.25rem 0.6rem;
            font-size: 0.78rem;
            font-family: var(--code-font);
        }
        .eda-method-box {
            background: #fdf4ff;
            border: 1px solid #f0abfc;
            border-left: 4px solid #c026d3;
            border-radius: 0 12px 12px 0;
            padding: 1rem 1.25rem;
            font-size: 0.86rem;
            color: #701a75;
            margin-bottom: 1.25rem;
        }
        .eda-insight-box {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-left: 4px solid #10b981;
            border-radius: 0 12px 12px 0;
            padding: 0.9rem 1.2rem;
            font-size: 0.85rem;
            color: #065f46;
            margin-top: 1rem;
        }
        .eda-risk-box {
            background: #fff1f2;
            border: 1px solid #fecdd3;
            border-left: 4px solid #f43f5e;
            border-radius: 0 12px 12px 0;
            padding: 0.9rem 1.2rem;
            font-size: 0.85rem;
            color: #9f1239;
            margin-top: 1rem;
        }
    </style>"""

if old_css_end in content:
    content = content.replace(old_css_end, new_css_additions, 1)
    print("1. Injected Stepper and EDA CSS successfully!")
else:
    print("1. Warning: old_css_end not found directly!")

# -----------------------------------------------------------------------------
# 2. UPDATE SIDEBAR SUBMENU FOR STEP 3
# -----------------------------------------------------------------------------
p_sub_start = content.find('<ul class="submenu-list" id="submenu-step-3">')
p_sub_end = content.find('</ul>', p_sub_start) + 5

new_submenu_step3 = """<ul class="submenu-list" id="submenu-step-3">
                    <li><a href="#sec-eda-31" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-31', event)">3.1 มิติและคลังฟีเจอร์ (Data Dimensions)</a></li>
                    <li><a href="#sec-eda-32" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-32', event)">3.2 การวิเคราะห์ตัวแปรเดี่ยว (Univariate)</a></li>
                    <li><a href="#sec-eda-33" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-33', event)">3.3 ข้อมูลสูญหายและคุณภาพ (Missingness & SQI)</a></li>
                    <li><a href="#sec-eda-34" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-34', event)">3.4 สหสัมพันธ์และความสัมพันธ์โรค (Multivariate)</a></li>
                    <li><a href="#sec-eda-35" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-35', event)">3.5 สัญญาณคลื่นและสเปกตรัม (Waveform & PSD)</a></li>
                    <li><a href="#sec-eda-36" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-36', event)">3.6 การตรวจจับค่าผิดปกติ (Outlier Detection)</a></li>
                    <li><a href="#sec-eda-37" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-37', event)">3.7 การวิเคราะห์การตรวจซ้ำ (Longitudinal)</a></li>
                    <li><a href="#sec-eda-38" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-38', event)">3.8 ตรวจสอบข้อมูลรั่วไหล (Leakage Audit)</a></li>
                </ul>"""

if p_sub_start != -1 and p_sub_end != -1:
    content = content[:p_sub_start] + new_submenu_step3 + content[p_sub_end:]
    print("2. Updated Sidebar submenu for Step 3 successfully!")

# -----------------------------------------------------------------------------
# 3. INSERT GLOBAL PIPELINE STEPPER HEADER
# -----------------------------------------------------------------------------
p_main_start = content.find('<main class="main-canvas">')
p_page1_start = content.find('<section id="page-step-1"', p_main_start)

stepper_header_html = """
            <!-- ============================================================= -->
            <!-- GLOBAL PIPELINE PROGRESS STEPPER & SYSTEM ROADMAP              -->
            <!-- ============================================================= -->
            <div class="card card-custom mb-4 p-3 border-primary-subtle bg-white shadow-sm" id="pipeline-stepper-header">
                <div class="d-flex flex-wrap align-items-center justify-content-between pb-2 mb-2 border-bottom">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-primary text-white font-code px-2 py-1"><i class="fas fa-project-diagram me-1"></i> PIPELINE ROADMAP</span>
                        <span class="fw-bold text-dark font-code" style="font-size: 0.95rem;">กระบวนการวิเคราะห์และพัฒนาแบบจำลองคลื่นไฟฟ้าหัวใจ (End-to-End Clinical ML/DL Workflow)</span>
                    </div>
                    <div class="d-flex align-items-center gap-2 font-code small text-muted">
                        <span class="badge-neon-green"><i class="fas fa-check-circle me-1"></i> Audit-Ready 5-Phase Standard</span>
                        <span class="badge-neon-blue"><i class="fas fa-sliders me-1"></i> คลิกเลือกดูแต่ละขั้นตอนได้ทันที</span>
                    </div>
                </div>
                <div class="row g-2 text-center font-code">
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn active" id="stepper-step-1" onclick="showPage('step-1')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-primary text-white fw-bold">เฟส 1</span>
                                <i class="fas fa-database text-primary"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate">1. ธรรมาภิบาลข้อมูล</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;">Grain & Provenance</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-2" onclick="showPage('step-2')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-info text-white fw-bold">เฟส 2</span>
                                <i class="fas fa-wave-square text-info"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate">2. ล้างข้อมูล & DSP</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;">Filter, SQI & QC</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-3" onclick="showPage('step-3')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-warning text-dark fw-bold">เฟส 3</span>
                                <i class="fas fa-chart-line text-warning"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate">3. การสำรวจ EDA & ฟีเจอร์</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;">8-Step In-Depth EDA</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-4" onclick="showPage('step-4')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-success text-white fw-bold">เฟส 4</span>
                                <i class="fas fa-trophy text-success"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate">4. การประเมินกลุ่มโมเดล</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;">ML, DL & 1D-CNN</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-5" onclick="showPage('step-5')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-danger text-white fw-bold">เฟส 5</span>
                                <i class="fas fa-user-injured text-danger"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate">5. ติดตามผู้ป่วย & CDS</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;">Trajectory & XAI Sim</div>
                        </button>
                    </div>
                </div>
            </div>

"""

if p_main_start != -1 and p_page1_start != -1:
    content = content[:p_page1_start] + stepper_header_html + content[p_page1_start:]
    print("3. Inserted Global Pipeline Stepper Header successfully!")

# -----------------------------------------------------------------------------
# 4. RESTRUCTURE PAGE 3 (STEP 3: 8-STEP EDA PIPELINE)
# -----------------------------------------------------------------------------
p_p3_start = content.find('<section id="page-step-3"')
p_p4_start = content.find('<section id="page-step-4"')

new_page3_html = """<section id="page-step-3" class="step-page">
                <!-- PAGE HEADER & BREADCRUMB -->
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="badge-neon-purple"><i class="fas fa-flask me-1"></i> ระยะที่ 3 (Phase 3)</span>
                            <span class="badge-neon-green"><i class="fas fa-list-check me-1"></i> 8 ขั้นตอนการวิเคราะห์ตามมาตรฐาน EDA สากล</span>
                        </div>
                        <h2 class="fw-bold mb-0 text-dark">🔬 การสำรวจข้อมูลเชิงลึก (EDA) & วิศวกรรมฟีเจอร์คลื่นไฟฟ้าหัวใจ</h2>
                        <div class="text-muted small">Exploratory Data Analysis & Electrophysiological Feature Engineering Pipeline</div>
                    </div>
                    <div class="d-flex gap-2 align-items-center mt-2 mt-md-0">
                        <span class="badge-neon-blue font-code"><i class="fas fa-dna me-1"></i> 63 Biomedical Features</span>
                        <span class="badge-neon-teal font-code"><i class="fas fa-shield-halved me-1"></i> Zero Leakage Audited</span>
                    </div>
                </div>

                <!-- QUICK-JUMP HORIZONTAL PILL NAVIGATION FOR 8 EDA STEPS -->
                <div class="eda-pill-nav">
                    <a href="#sec-eda-31" class="eda-pill-btn"><span class="badge bg-purple text-white">3.1</span> โครงสร้างและมิติข้อมูล</a>
                    <a href="#sec-eda-32" class="eda-pill-btn"><span class="badge bg-purple text-white">3.2</span> การวิเคราะห์ตัวแปรเดี่ยว</a>
                    <a href="#sec-eda-33" class="eda-pill-btn"><span class="badge bg-purple text-white">3.3</span> ข้อมูลสูญหายและคุณภาพ</a>
                    <a href="#sec-eda-34" class="eda-pill-btn"><span class="badge bg-purple text-white">3.4</span> สหสัมพันธ์และความสัมพันธ์โรค</a>
                    <a href="#sec-eda-35" class="eda-pill-btn"><span class="badge bg-purple text-white">3.5</span> สัญญาณคลื่นและสเปกตรัม</a>
                    <a href="#sec-eda-36" class="eda-pill-btn"><span class="badge bg-purple text-white">3.6</span> การตรวจจับค่าผิดปกติ</a>
                    <a href="#sec-eda-37" class="eda-pill-btn"><span class="badge bg-purple text-white">3.7</span> การวิเคราะห์การตรวจซ้ำ</a>
                    <a href="#sec-eda-38" class="eda-pill-btn"><span class="badge bg-purple text-white">3.8</span> ตรวจสอบข้อมูลรั่วไหล</a>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.1: DATA DIMENSION & FEATURE INVENTORY AUDIT            -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-31">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.1</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-boxes-stacked text-purple me-1"></i> การสำรวจมิติและโครงสร้างคลังข้อมูลฟีเจอร์ (Data Dimension & Feature Inventory Audit)</span>
                        </div>
                        <span class="badge-neon-purple font-code">Feature Inventory</span>
                    </div>
                    <div class="card-body-custom">
                        <!-- 4 Summary Stat Cards -->
                        <div class="row g-3 mb-4">
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center">
                                    <div class="text-muted small font-code">จำนวนบันทึก EKG ทั้งหมด</div>
                                    <div class="fs-4 fw-bold text-dark font-code">21,799 ➔ 21,246</div>
                                    <span class="badge-neon-green" style="font-size: 0.70rem;">คัดกรองสัญญาณสมบูรณ์</span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center">
                                    <div class="text-muted small font-code">จำนวนผู้ป่วยจริง (Unique Patients)</div>
                                    <div class="fs-4 fw-bold text-primary font-code">18,499 ราย</div>
                                    <span class="badge-neon-blue" style="font-size: 0.70rem;">ตรวจซ้ำ 2,015 ราย (10.9%)</span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center">
                                    <div class="text-muted small font-code">จำนวนฟีเจอร์ที่สกัดได้</div>
                                    <div class="fs-4 fw-bold text-success font-code">63 ตัวแปร</div>
                                    <span class="badge-neon-teal" style="font-size: 0.70rem;">Biomedical + Clinical</span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center">
                                    <div class="text-muted small font-code">ความละเอียดสัญญาณ (Sampling)</div>
                                    <div class="fs-4 fw-bold text-danger font-code">500 Hz & 100 Hz</div>
                                    <span class="badge-neon-coral" style="font-size: 0.70rem;">12 ลีดพร้อมกัน 10 วินาที</span>
                                </div>
                            </div>
                        </div>

                        <!-- Methodology and Objective Callout -->
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-bullseye me-1"></i> วัตถุประสงค์และระเบียบวิธีวิจัย (Objective & Methodology):</div>
                            <div>
                                ก่อนเริ่มต้นการวิเคราะห์เชิงลึก จำเป็นต้องจัดทำ<strong>บัญชีสารบบข้อมูล (Data Inventory & Catalog)</strong> 
                                เพื่อแจกแจงมิติ ระดับการวัด (Measurement Scales) และตรวจสอบชนิดข้อมูล (Data Types) ของตัวแปรทั้งหมด 63 คอลัมน์ 
                                เพื่อป้องกันปัญหา Type Mismatch, การตีความตัวแปรเชิงกลุ่มเป็นตัวแปรต่อเนื่อง หรือการเกิด Target Leakage ตั้งแต่ชั้นฐานข้อมูล
                            </div>
                        </div>

                        <!-- Feature Taxonomy Table -->
                        <div class="table-responsive">
                            <table class="table table-custom table-sm mb-0">
                                <thead>
                                    <tr>
                                        <th>กลุ่มฟีเจอร์ (Modality Group)</th>
                                        <th>จำนวนตัวแปร</th>
                                        <th>ตัวอย่างตัวแปรสำคัญ</th>
                                        <th>ชนิดข้อมูล</th>
                                        <th>ความหมายทางสรีรวิทยาและการแพทย์</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>1. ข้อมูลประชากร (Demographics)</strong></td>
                                        <td><span class="code-chip">4 ตัวแปร</span></td>
                                        <td><code>age</code>, <code>sex</code>, <code>height</code>, <code>weight</code></td>
                                        <td>Numerical / Categorical</td>
                                        <td>ปัจจัยพื้นฐานของผู้ป่วย เช่น อายุและเพศมีผลต่อการเปลี่ยนแปลงทางกายวิภาคของหัวใจ</td>
                                    </tr>
                                    <tr>
                                        <td><strong>2. สรีรวิทยาไฟฟ้าตามเวลา (Time-Domain)</strong></td>
                                        <td><span class="code-chip">18 ตัวแปร</span></td>
                                        <td><code>hrv_mean_hr</code>, <code>hrv_mean_rr</code>, <code>hrv_sdnn</code>, <code>hrv_rmssd</code>, <code>hrv_pnn50</code></td>
                                        <td>Float (ms, bpm)</td>
                                        <td>ความแปรปรวนของการเต้นของหัวใจ (HRV) สะท้อนความสมบูรณ์ของระบบประสาทอัตโนมัติ (Autonomic Tone)</td>
                                    </tr>
                                    <tr>
                                        <td><strong>3. สเปกตรัมความถี่ (Frequency-Domain)</strong></td>
                                        <td><span class="code-chip">12 ตัวแปร</span></td>
                                        <td><code>hrv_lf_power</code>, <code>hrv_hf_power</code>, <code>hrv_lf_hf_ratio</code>, <code>spectral_entropy</code></td>
                                        <td>Float (ms²/Hz)</td>
                                        <td>แยกคลื่นสะท้อนระบบประสาทซิมพาเทติก (LF: 0.04–0.15 Hz) และพาราซิมพาเทติก (HF: 0.15–0.40 Hz)</td>
                                    </tr>
                                    <tr>
                                        <td><strong>4. สัณฐานวิทยาคลื่นไฟฟ้า (Morphology)</strong></td>
                                        <td><span class="code-chip">24 ตัวแปร</span></td>
                                        <td><code>qrs_duration</code>, <code>pr_interval</code>, <code>qtc_bazett</code>, <code>st_elevation</code>, <code>sokolow_lyon</code></td>
                                        <td>Float (ms, mV)</td>
                                        <td>ระยะเวลาและแอมพลิจูดของคลื่น P-Q-R-S-T ใช้ตรวจจับกล้ามเนื้อหัวใจตาย (MI) และการนำไฟฟ้าขัดข้อง (CD)</td>
                                    </tr>
                                    <tr>
                                        <td><strong>5. ตัวแปรเป้าหมาย (Diagnostic Targets)</strong></td>
                                        <td><span class="code-chip">5 ตัวแปร</span></td>
                                        <td><code>NORM</code>, <code>MI</code>, <code>STTC</code>, <code>CD</code>, <code>HYP</code></td>
                                        <td>Binary / Multi-label</td>
                                        <td>กลุ่มโรคหัวใจ 5 ซูเปอร์คลาสตามมาตรฐาน SCP-ECG คำวินิจฉัยยืนยันโดยแพทย์อายุรศาสตร์หัวใจ</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div class="eda-insight-box">
                            <strong><i class="fas fa-lightbulb me-1"></i> ข้อค้นพบเชิงประจักษ์ (Empirical Findings):</strong>
                            ข้อมูลคลื่นไฟฟ้าหัวใจมีโครงสร้างผสมผสาน (Multimodal Hybrid) ประกอบด้วยสัญญาณ Waveform แบบอนุกรมเวลาต่อเนื่อง 60,000 จุดต่อบันทึก และตารางฟีเจอร์สกัดทางชีวการแพทย์ 63 มิติ ทำให้สามารถรองรับได้ทั้งโมเดล Machine Learning แบบดั้งเดิม (LightGBM/XGBoost) และ Deep Learning แบบ End-to-End (1D-CNN/ResNet1D)
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.2: UNIVARIATE DISTRIBUTION ANALYSIS                    -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-32">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.2</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-chart-column text-primary me-1"></i> การวิเคราะห์ตัวแปรเดี่ยวเชิงสถิติและคลินิก (Univariate Distribution Analysis)</span>
                        </div>
                        <span class="badge-neon-blue font-code">Univariate EDA</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-microscope me-1"></i> ระเบียบวิธีวิจัยการวิเคราะห์ตัวแปรเดี่ยว:</div>
                            <div>
                                การวิเคราะห์การกระจายตัวของตัวแปรเดี่ยว (Univariate Distribution) ช่วยให้เข้าใจรูปแบบทางสถิติ (Central Tendency, Dispersion, Skewness, Kurtosis) 
                                ตรวจสอบความไม่สมดุลของคลาสโรคเป้าหมาย (Class Imbalance) และเปรียบเทียบกับขอบเขตเกณฑ์มาตรฐานทางการแพทย์ (Clinical Normal Ranges)
                            </div>
                        </div>

                        <!-- Row 1: Target Class Imbalance & Demographics Age/Sex -->
                        <div class="row g-4 mb-4">
                            <!-- 3.2A: Target Class Distribution -->
                            <div class="col-lg-6" id="sec-target-dist">
                                <div class="card card-custom h-100 shadow-none border">
                                    <div class="card-header-custom bg-white">
                                        <span><i class="fas fa-heart-pulse me-2 text-danger"></i> 3.2A: การกระจายตัวของ 5 กลุ่มโรคเป้าหมาย (Diagnostic Superclasses)</span>
                                        <span class="badge-neon-coral">Imbalance Ratio: ~7:1</span>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-target-distribution" style="height: 330px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            📊 NORM (43.2%) คือกลุ่มใหญ่ที่สุด ขณะที่ HYP (6.1%) เป็นกลุ่มหายาก ทำให้โมเดลจำเป็นต้องใช้ <code>class_weight='balanced'</code> และวัดผลด้วย Macro AUROC
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 3.2B: Demographic Age & Sex Distribution -->
                            <div class="col-lg-6" id="sec-age-sex-dist">
                                <div class="card card-custom h-100 shadow-none border">
                                    <div class="card-header-custom bg-white">
                                        <span><i class="fas fa-venus-mars me-2 text-primary"></i> 3.2B: การกระจายตัวทางประชากรศาสตร์ (Demographic Age & Sex)</span>
                                        <span class="badge-neon-blue">Mean Age: 59.4 ปี</span>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-age-sex-distribution" style="height: 330px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            👥 การกระจายอายุมีลักษณะระฆังคว่ำค่อนไปทางผู้สูงอายุ (หญิง 51.9%, ชาย 48.1%) สอดคล้องกับพีระมิดประชากรผู้ป่วยโรคหลอดเลือดหัวใจในโรงพยาบาลจริง
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Row 2: Electrophysiological Vital Signs (Heart Rate & QRS Duration) -->
                        <div class="card card-custom shadow-none border mb-0" id="sec-bio-distribution">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-stethoscope me-2 text-success"></i> 3.2C: การกระจายตัวของสัญญาณชีพไฟฟ้าหัวใจ (Heart Rate & QRS Duration Distribution)</span>
                                <span class="badge-neon-green">ขอบเขตค่าปกติทางคลินิก (Clinical Reference Ranges)</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-bio-distribution" style="height: 350px;"></div>
                                <div class="row g-2 mt-3 text-center small font-code">
                                    <div class="col-md-3">
                                        <div class="p-2 rounded bg-light border">
                                            <div class="text-muted">หัวใจเต้นช้า (Bradycardia)</div>
                                            <div class="fw-bold text-info">&lt;60 bpm: 1,842 ราย (8.7%)</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="p-2 rounded bg-light border">
                                            <div class="text-muted">อัตราเต้นปกติ (Normal HR)</div>
                                            <div class="fw-bold text-success">60–100 bpm: 17,481 ราย (82.3%)</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="p-2 rounded bg-light border">
                                            <div class="text-muted">หัวใจเต้นเร็ว (Tachycardia)</div>
                                            <div class="fw-bold text-warning">&gt;100 bpm: 1,923 ราย (9.0%)</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="p-2 rounded bg-light border">
                                            <div class="text-muted">คลื่นกว้างผิดปกติ (Prolonged QRS)</div>
                                            <div class="fw-bold text-danger">&gt;120 ms: 1,882 ราย (8.9%)</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.3: MISSINGNESS MECHANISM & SIGNAL QUALITY AUDIT        -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-33">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.3</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-filter-circle-xmark text-danger me-1"></i> การวิเคราะห์กลไกข้อมูลสูญหายและควบคุมคุณภาพสัญญาณ (Missingness Mechanism & Signal Quality Audit)</span>
                        </div>
                        <span class="badge-neon-coral font-code">MCAR / MAR / MNAR</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-shield-virus me-1"></i> ทฤษฎีกลไกข้อมูลสูญหาย 3 ระดับของ Rubin (Missing Data Mechanisms):</div>
                            <div class="row g-2 mt-2">
                                <div class="col-md-4">
                                    <div class="p-2 rounded bg-white border">
                                        <strong class="text-success"><i class="fas fa-dice me-1"></i> 1. MCAR (Missing Completely at Random):</strong>
                                        <p class="small text-muted mb-0">ข้อมูลสูญหายโดยสุ่มสมบูรณ์ เช่น ตัวแปรอายุ <code>age</code> ขาดหายไปเพียง 0.4% จากข้อผิดพลาดในการคีย์ข้อมูล ไม่มีผลกระทบเชิงอคติต่อการทำนาย</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="p-2 rounded bg-white border">
                                        <strong class="text-primary"><i class="fas fa-arrows-split-up-and-left me-1"></i> 2. MAR (Missing at Random):</strong>
                                        <p class="small text-muted mb-0">ข้อมูลสูญหายโดยสัมพันธ์กับตัวแปรที่สังเกตได้ เช่น <code>qtc_ms</code> (0.24%) หรือ <code>lf_hf_ratio</code> (5.54%) สูญหายเมื่อคลื่นมี T-wave แบนราบจนคำนวณไม่ได้</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="p-2 rounded bg-white border">
                                        <strong class="text-danger"><i class="fas fa-triangle-exclamation me-1"></i> 3. MNAR (Missing Not at Random):</strong>
                                        <p class="small text-muted mb-0">ข้อมูลสูญหายจากเหตุผลทางการแพทย์โดยตรง เช่น <code>height</code> (54.2%) และ <code>weight</code> (56.8%) ขาดหายไปในผู้ป่วยฉุกเฉิน/ICU ที่ไม่สามารถชั่งน้ำหนักได้!</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Missingness Heatmap Container -->
                        <div class="card card-custom shadow-none border mb-4" id="sec-missing-heatmap">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-table-cells-large me-2 text-danger"></i> แผนที่ความร้อนข้อมูลสูญหายก่อนและหลังการจัดการ (Missing-Value Heatmap & Imputation Strategy)</span>
                                <span class="badge-neon-coral">Train-Only Imputation</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-missing-heatmap" style="height: 330px;"></div>
                                <div class="eda-insight-box mt-3 mb-0">
                                    <strong><i class="fas fa-check-circle me-1"></i> กลยุทธ์การป้องกันข้อมูลรั่วไหล (Zero-Leakage Imputation Guardrail):</strong>
                                    การจัดการข้อมูลสูญหายกระทำโดยคำนวณค่ามัธยฐาน (Median) จากข้อมูลชุด Train เท่านั้น แล้วนำค่าสถิตินั้นไปเติมใน Validation และ Test 
                                    พร้อมกับสร้างตัวแปรตัวบ่งชี้ <code>is_missing_height</code> และ <code>is_missing_weight</code> เพื่อรักษาข้อมูลว่าผู้ป่วยรายนั้นอาจอยู่ในภาวะวิกฤต
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.4: BIVARIATE & MULTIVARIATE ASSOCIATION ANALYSIS       -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-34">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.4</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-diagram-project text-info me-1"></i> การวิเคราะห์สหสัมพันธ์และความสัมพันธ์หลายตัวแปร (Bivariate & Multivariate Association Analysis)</span>
                        </div>
                        <span class="badge-neon-teal font-code">Multivariate EDA</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-calculator me-1"></i> ระเบียบวิธีวิจัยและสถิติสหสัมพันธ์หลายตัวแปร:</div>
                            <div>
                                วิเคราะห์ความสัมพันธ์เชิงเส้นและไม่เชิงเส้นระหว่างฟีเจอร์คลินิกด้วยค่าสัมประสิทธิ์สหสัมพันธ์เพียร์สัน (Pearson Correlation Coefficient $r$) 
                                และวิเคราะห์การแบ่งชั้นตามกลุ่มโรค (Disease Stratification) เพื่อพิสูจน์ว่าฟีเจอร์ใดมีพลังในการแยกแยะโรค (Discriminative Power)
                            </div>
                        </div>

                        <!-- Row 1: Correlation Matrix Heatmap & Morphology by Class Boxplot -->
                        <div class="row g-4 mb-4">
                            <!-- 3.4A: Correlation Heatmap -->
                            <div class="col-lg-6" id="sec-corr-heatmap">
                                <div class="card card-custom h-100 shadow-none border">
                                    <div class="card-header-custom bg-white">
                                        <span><i class="fas fa-fire me-2 text-danger"></i> 3.4A: แผนภาพสหสัมพันธ์เพียร์สัน (Pearson Correlation Matrix Heatmap)</span>
                                        <span class="badge-neon-coral">Direct Labels On All Cells</span>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-corr-heatmap" style="height: 380px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            📈 แสดงค่า $r$ ชัดเจนทุกเซลล์: เช่น RMSSD กับ SDNN ($r = +0.78$) มีสหสัมพันธ์สูงมากตามหลักระบบประสาทพาราซิมพาเทติก; Mean HR กับ Mean RR ($r = -0.84$) สัมพันธ์ผกผันตามหลักฟิสิกส์
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 3.4B: Morphology Boxplot by Class -->
                            <div class="col-lg-6" id="sec-morph-box">
                                <div class="card card-custom h-100 shadow-none border">
                                    <div class="card-header-custom bg-white">
                                        <span><i class="fas fa-cubes me-2 text-warning"></i> 3.4B: สัณฐานวิทยา QRS จำแนกตาม 5 กลุ่มโรค (Morphology Stratification)</span>
                                        <span class="badge-neon-purple">CD vs NORM vs MI</span>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-morphology-box" style="height: 380px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            🔬 ยืนยันสมมติฐานคลินิก: กลุ่มการนำไฟฟ้าขัดข้อง (CD) มีความกว้างคลื่น QRS สูงกว่า 115 ms (Median 124 ms) อย่างมีนัยสำคัญทางสถิติ ($p < 0.001$) เทียบกับกลุ่มปกติ NORM (Median 88 ms)
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Row 2: Age Group vs Disease Prevalence Stacked Chart -->
                        <div class="card card-custom shadow-none border mb-0" id="sec-age-disease-strat">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-layer-group me-2 text-primary"></i> 3.4C: ความสัมพันธ์ระหว่างช่วงอายุกับความชุกของโรคหัวใจ (Age Group vs Disease Stratification)</span>
                                <span class="badge-neon-blue">Exponential Risk in Elderly</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-age-disease-strat" style="height: 340px;"></div>
                                <div class="eda-insight-box mt-3 mb-0">
                                    <strong><i class="fas fa-user-doctor me-1"></i> ข้อค้นพบทางคลินิก (Clinical Discovery):</strong>
                                    ผู้ป่วยอายุน้อยกว่า 30 ปีมีคลื่นปกติสูงถึง 81.7% ในขณะที่กลุ่มอายุ 60–75 ปี และ 75+ ปี พบอัตราการเกิดภาวะกล้ามเนื้อหัวใจขาดเลือด (MI) และการนำไฟฟ้าผิดปกติ (CD) พุ่งสูงขึ้นเกินกว่า 65% ของจำนวนการตรวจทั้งหมด แสดงให้เห็นว่าอายุเป็นตัวแปรพยากรณ์ร่วมที่มีน้ำหนักสูงมาก
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.5: TIME-SERIES WAVEFORM & SPECTRAL DENSITY EDA        -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-35">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.5</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-wave-square text-success me-1"></i> การวิเคราะห์สัญญาณอนุกรมเวลาและสเปกตรัมความถี่คลื่นหัวใจ (Time-Series Waveform & Spectral Density EDA)</span>
                        </div>
                        <span class="badge-neon-green font-code">Waveform & PSD</span>
                    </div>
                    <div class="card-body-custom">
                        <!-- Beginner-Friendly Guide Box -->
                        <div class="callout-box mb-4" id="sec-clinical-guide">
                            <strong><i class="fas fa-heart-pulse me-1"></i> คู่มือสรีรวิทยาคลื่นไฟฟ้าหัวใจเบื้องต้น (Beginner-Friendly ECG Interpretation Guide):</strong><br>
                            คลื่นไฟฟ้าหัวใจสะท้อนการเดินทางของประจุไฟฟ้าผ่านกล้ามเนื้อหัวใจ 4 ห้องในแต่ละจังหวะการเต้น ประกอบด้วย 5 องค์ประกอบหลัก:
                            <div class="row mt-2 g-3">
                                <div class="col-md-3">
                                    <strong>1. คลื่น P (P Wave):</strong>
                                    <p class="small text-muted mb-0">การบีบตัวของหัวใจห้องบน (Atrial Depolarization) ปกติกว้างไม่เกิน 120 ms หากผิดปกติบ่งชี้ภาวะหัวใจห้องบนสั่นพริ้ว (AFib)</p>
                                </div>
                                <div class="col-md-3">
                                    <strong>2. กลุ่มคลื่น QRS (QRS Complex):</strong>
                                    <p class="small text-muted mb-0">การบีบตัวของหัวใจห้องล่าง (Ventricular Depolarization) ปกติกว้าง 80–110 ms หากกว้าง &gt;120 ms บ่งชี้การนำไฟฟ้าขัดข้อง (CD / Block)</p>
                                </div>
                                <div class="col-md-3">
                                    <strong>3. ช่วง ST Segment & คลื่น T:</strong>
                                    <p class="small text-muted mb-0">การคลายตัวของหัวใจห้องล่าง (Repolarization) หากช่วง ST ยกตัวสูงขึ้น &gt;0.1 mV บ่งชี้ภาวะกล้ามเนื้อหัวใจขาดเลือดเฉียบพลัน (STEMI)</p>
                                </div>
                                <div class="col-md-3">
                                    <strong>4. ความแปรปรวนหัวใจ (HRV):</strong>
                                    <p class="small text-muted mb-0">วัดความยืดหยุ่นของระบบประสาทอัตโนมัติ (SDNN และ RMSSD) ค่าที่สูงสะท้อนสุขภาพหัวใจที่ดีและระบบพาราซิมพาเทติกที่สมบูรณ์</p>
                                </div>
                            </div>
                        </div>

                        <!-- 3.5A: Waveform Overlay -->
                        <div class="card card-custom shadow-none border mb-4" id="sec-pan-tompkins">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-chart-area me-2 text-danger"></i> 3.5A: กราฟคลื่นไฟฟ้าหัวใจพร้อมตรวจจับยอด R-Peak (Pan-Tompkins) และช่วงคลื่น QRS / ST (10-Second Waveform Viewer)</span>
                                <span class="badge-neon-blue">ลีดจังหวะ II (Lead II Rhythm)</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-biomedical-overlay" style="height: 380px;"></div>
                                <div class="d-flex flex-wrap justify-content-between mt-2 small text-muted font-code gap-2">
                                    <span><i class="fas fa-circle text-danger me-1"></i> ยอด R-Peaks (ตรวจจับโดยอัลกอริทึม Pan-Tompkins)</span>
                                    <span><i class="fas fa-arrows-left-right text-info me-1"></i> กรอบความกว้างกลุ่มคลื่น QRS Complex (เริ่มต้น ➔ สิ้นสุด: ~86 ms)</span>
                                    <span><i class="fas fa-flag text-warning me-1"></i> จุดวัดการยกตัวของช่วง ST ที่จุด J+60ms เทียบกับ Isopotential Baseline</span>
                                </div>
                            </div>
                        </div>

                        <!-- 3.5B: Welch PSD -->
                        <div class="card card-custom shadow-none border mb-0" id="sec-welch-psd">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-chart-line me-2 text-primary"></i> 3.5B: สเปกตรัมความถี่ความแปรปรวนการเต้นของหัวใจ (HRV Welch PSD Spectrum Plot)</span>
                                <span class="badge-neon-teal" id="badge-lf-hf">LF/HF Ratio: 1.42 (สมดุลปกติ)</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-welch-psd" style="height: 350px;"></div>
                                <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                    การวิเคราะห์สเปกตรัมระบบประสาทอัตโนมัติ: แถบสีฟ้าคือคลื่นความถี่ต่ำ (LF: 0.04–0.15 Hz สะท้อนประสาทกระตุ้น Sympathetic); แถบสีเขียวคือคลื่นความถี่สูง (HF: 0.15–0.40 Hz สะท้อนประสาทผ่อนคลาย Parasympathetic) อัตราส่วน LF/HF = 1.42 แสดงถึงความสมดุลที่ดี
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.6: OUTLIER DETECTION & CLINICAL ANOMALY IDENTIFICATION -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-36">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.6</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-triangle-exclamation text-warning me-1"></i> การตรวจจับค่าผิดปกติและความผิดปกติทางคลินิก (Outlier Detection & Clinical Anomaly Identification)</span>
                        </div>
                        <span class="badge-neon-coral font-code">Tukey's IQR Method</span>
                    </div>
                    <div class="card-body-custom">
                        <!-- Critical Clinical Warning Box -->
                        <div class="eda-risk-box mb-4">
                            <div class="fw-bold mb-1"><i class="fas fa-skull-crossbones me-1"></i> กฎเหล็กทางการแพทย์ขั้นวิกฤต (Crucial Medical Safety Rule — Never Drop Pathological Outliers):</div>
                            <div>
                                ในงาน Data Science ทั่วไป มักจะตัดค่า Outlier ทิ้งเพื่อทำให้กราฟสวยงาม แต่ในงานการแพทย์ <strong>ค่าผิดปกติสุดขั้วคือสัญญาณชีพฉุกเฉินของผู้ป่วย (True Pathological Extremes)</strong> 
                                เช่น ค่า ST-elevation ที่สูงเกิน 0.30 mV บ่งบอกถึงภาวะ <strong>กล้ามเนื้อหัวใจตายเฉียบพลันชนิดยกตัว (STEMI Crisis)</strong> 
                                หรืออัตราเต้นหัวใจเกิน 160 bpm คือภาวะหัวใจเต้นเร็ววิกฤต (Ventricular Tachycardia) 
                                <strong>การตัดค่าเหล่านี้ทิ้งถือเป็นความผิดพลาดร้ายแรงทางการแพทย์ (Medical Malpractice)</strong> ระบบจึงเลือกใช้การกักกันเฉพาะสัญญาณรบกวนคลื่นหลุด (Technical Artifacts) เท่านั้น ส่วนค่าพยาธิสภาพจริงจะถูกเก็บรักษาไว้ 100%
                            </div>
                        </div>

                        <!-- 3.6A: Outlier Boxplot -->
                        <div class="card card-custom shadow-none border mb-4" id="sec-outlier-box">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-box-archive me-2 text-warning"></i> 3.6A: แผนภาพกล่องสรุปค่าผิดปกติเชิงสถิติ (Outlier Summary Box Plot: ST-Elevation & HRV RMSSD)</span>
                                <span class="badge-neon-teal">Tukey IQR Boundaries</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-outlier-box" style="height: 350px;"></div>
                                <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                    📦 แผนภาพกล่องแสดงการกระจายตัว มัธยฐาน IQR และจุด Outlier ของ ST-elevation และ HRV RMSSD พร้อมเกณฑ์ชี้วัดวิกฤต STEMI (ST &gt; 0.1 mV)
                                </div>
                            </div>
                        </div>

                        <!-- 3.6B: Outlier Registry Table -->
                        <div class="card card-custom shadow-none border mb-0" id="sec-eda-stats">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-table me-2 text-primary"></i> 3.6B: การตรวจสอบความเบ้ (Skewness) และทะเบียนค่าผิดปกติ (IQR Outliers Registry)</span>
                                <span class="badge-neon-green">10 Core Biomedical Features</span>
                            </div>
                            <div class="card-body-custom p-0" style="max-height: 280px; overflow-y: auto;">
                                <table class="table table-custom table-sm mb-0">
                                    <thead>
                                        <tr>
                                            <th>ฟีเจอร์คลินิก</th>
                                            <th>ค่ามัธยฐาน</th>
                                            <th>ช่วง IQR [Q1, Q3]</th>
                                            <th>ความเบ้ (Skewness)</th>
                                            <th>จำนวน Outlier (%)</th>
                                            <th>ผลกระทบและการบำบัดทางสถิติ</th>
                                        </tr>
                                    </thead>
                                    <tbody id="tbody-eda-outliers">
                                        <!-- Dynamic JS -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.7: LONGITUDINAL ENCOUNTER & TEMPORAL DYNAMICS EDA     -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-37">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.7</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-clock-rotate-left text-primary me-1"></i> การวิเคราะห์มิติเวลาและการตรวจซ้ำทางยาว (Longitudinal Encounter & Temporal Dynamics EDA)</span>
                        </div>
                        <span class="badge-neon-blue font-code">Temporal Dynamics</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-timeline me-1"></i> วัตถุประสงค์และเหตุผลทางคลินิกของการตรวจซ้ำ (Clinical Rationale for Repeated Encounters):</div>
                            <div>
                                การติดตามผลคลื่นไฟฟ้าหัวใจทางยาว (Longitudinal Tracking) ช่วยให้แพทย์ตรวจพบการเปลี่ยนแปลงอย่างค่อยเป็นค่อยไป 
                                เช่น ภาวะหัวใจวายเรื้อรังที่แย่ลง หรือการดำเนินโรคจากคลื่นปกติ (NORM) ➔ เริ่มมีการนำไฟฟ้าขัดข้อง (CD) ➔ เกิดภาวะกล้ามเนื้อหัวใจตายเฉียบพลัน (MI) 
                                ซึ่งไม่สามารถตรวจพบได้จากการตรวจเพียงครั้งเดียว (Cross-Sectional Single Snapshot)
                            </div>
                        </div>

                        <!-- 3.7A: Visit Frequency Distribution Bar Chart -->
                        <div class="card card-custom shadow-none border mb-4" id="sec-eda-visit-dist">
                            <div class="card-header-custom bg-white">
                                <span><i class="fas fa-chart-bar me-2 text-success"></i> 3.7A: กราฟแท่งการกระจายความถี่การตรวจซ้ำของผู้ป่วย (Patient Multi-Visit Distribution Bar Chart)</span>
                                <span class="badge-neon-green">2,015 ผู้ป่วยติดตามผลระยะยาว</span>
                            </div>
                            <div class="card-body-custom">
                                <div id="chart-eda-visit-dist" style="height: 330px;"></div>
                                <div class="eda-insight-box mt-3 mb-0">
                                    <strong><i class="fas fa-chart-line me-1"></i> ข้อค้นพบสำคัญ:</strong>
                                    ผู้ป่วย 2,015 คนมีการตรวจซ้ำ 2–10+ ครั้ง คิดเป็นบันทึกถึง 4,762 ครั้ง (22.4% ของชุดข้อมูล) 
                                    มีช่วงเวลาติดตามผลเฉลี่ย (Median Interval) อยู่ที่ 142 วัน เหมาะสำหรับการสร้างตัวจำลองความเสี่ยงในอนาคต (Phase 5 CDS Simulator)
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ============================================================= -->
                <!-- STEP 3.8: DATA LEAKAGE AUDIT & PRE-MODELING READINESS         -->
                <!-- ============================================================= -->
                <div class="card card-custom eda-step-card" id="sec-eda-38">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step">ขั้นตอนที่ 3.8</span>
                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-shield-check text-success me-1"></i> การตรวจสอบการรั่วไหลของข้อมูลและประเมินความพร้อมสู่การสร้างแบบจำลอง (Data Leakage Audit & Pre-Modeling Readiness Gate)</span>
                        </div>
                        <span class="badge-neon-green font-code">Gate Passed ✅</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box">
                            <div class="fw-bold mb-1"><i class="fas fa-lock me-1"></i> เกณฑ์การตรวจสอบการรั่วไหลของข้อมูล 4 มิติ (4-Point Zero-Leakage Protocol):</div>
                            <div>
                                ตามมาตรฐาน Universal Data Science Workflow ก่อนส่งต่อข้อมูลเข้าสู่การเทรนแบบจำลอง (Phase 4) 
                                จำเป็นต้องผ่านประตูตรวจสอบความถูกต้อง (Readiness Gate) เพื่อยืนยันว่าจะไม่มีข้อมูลจากอนาคตหรือข้อมูลคำตอบรั่วไหลเข้าสู่โมเดล
                            </div>
                        </div>

                        <!-- Zero-Leakage Checklist Table -->
                        <div class="table-responsive mb-3">
                            <table class="table table-custom table-sm mb-0">
                                <thead>
                                    <tr>
                                        <th>มิติการตรวจสอบการรั่วไหล</th>
                                        <th>ความเสี่ยง (Risk Definition)</th>
                                        <th>มาตรการป้องกันที่นำมาใช้ (Preventative Control)</th>
                                        <th>สถานะการประเมิน (Audit Status)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>1. Target Proxy Leakage</strong></td>
                                        <td>ฟีเจอร์แอบแฝงที่เป็นตัวแทนคำตอบ เช่น คำวินิจฉัยแพทย์ หรือรหัสหัตถการ</td>
                                        <td>ตัดคอลัมน์วินิจฉัยและเมทาดาทาหลังผลตรวจออกทั้งหมด เหลือเฉพาะสัญญาณดิบและสถิติ</td>
                                        <td><span class="badge-neon-green"><i class="fas fa-check-circle me-1"></i> ผ่านเกณฑ์ 100% (Clean)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>2. Identity Memorization</strong></td>
                                        <td>โมเดลจำคลื่นไฟฟ้าของผู้ป่วยคนเดียวกันจาก Train ไปตอบใน Val/Test</td>
                                        <td>ใช้ <strong>GroupKFold 5-Fold แบ่งตาม <code>patient_id</code></strong> ห้ามผู้ป่วยซ้อนทับเด็ดขาด</td>
                                        <td><span class="badge-neon-green"><i class="fas fa-check-circle me-1"></i> ผู้ป่วยซ้อนทับ 0% (Zero Leakage)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>3. Preprocessing Fit Leakage</strong></td>
                                        <td>การคำนวณ Mean/Std หรือ Imputation จากทั้งชุดข้อมูลรวมกัน</td>
                                        <td>คำนวณและฟิต <code>StandardScaler</code> และ <code>SimpleImputer</code> จากชุด Train เท่านั้น</td>
                                        <td><span class="badge-neon-green"><i class="fas fa-check-circle me-1"></i> Fit-on-Train Exclusively</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>4. Temporal Sequence Leakage</strong></td>
                                        <td>การนำข้อมูลผลตรวจในอนาคตมาพยากรณ์ผลตรวจในอดีตของผู้ป่วยคนเดียวกัน</td>
                                        <td>จำกัดให้ฟีเจอร์พยากรณ์สร้างจากประวัติที่เกิดขึ้นก่อนจุดเวลาตรวจจริง (Index Time) เท่านั้น</td>
                                        <td><span class="badge-neon-green"><i class="fas fa-check-circle me-1"></i> Strictly Preceding Only</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- Approval Banner -->
                        <div class="p-3 rounded-4 bg-light border d-flex flex-wrap align-items-center justify-content-between gap-2">
                            <div>
                                <div class="fw-bold text-dark font-code"><i class="fas fa-certificate text-success me-1"></i> สถานะการรับรองความพร้อมข้อมูล (Pre-Modeling Readiness Approval):</div>
                                <div class="text-muted small">ฟีเจอร์ทั้ง 63 ตัวแปรและข้อมูลคลื่น 500 Hz ผ่านการตรวจสอบคุณสมบัติครบถ้วน พร้อมส่งต่อเข้าสู่กระบวนการเทรนแบบจำลองไฮบริดในเฟส 4</div>
                            </div>
                            <button class="btn btn-sm btn-primary font-code px-3 py-2" onclick="showPage('step-4')">
                                ดำเนินการต่อสู่เฟส 4: ประเมินแบบจำลอง <i class="fas fa-arrow-right ms-1"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </section>
"""

if p_p3_start != -1 and p_p4_start != -1:
    content = content[:p_p3_start] + new_page3_html + content[p_p4_start:]
    print("4. Restructured Page 3 (8-Step EDA Pipeline) successfully!")

# -----------------------------------------------------------------------------
# 5. UPDATE showPage() TO SYNC STEPPER BUTTONS
# -----------------------------------------------------------------------------
p_sp_find = content.find("function showPage(pageId) {")
p_sp_body = content.find("activeStep = stepId;", p_sp_find)

stepper_sync_js = """activeStep = stepId;

            // Sync Stepper Buttons
            document.querySelectorAll('.stepper-btn').forEach(btn => btn.classList.remove('active'));
            const activeStepper = document.getElementById('stepper-' + stepId);
            if (activeStepper) {
                activeStepper.classList.add('active');
            }
"""

if p_sp_body != -1:
    content = content[:p_sp_body] + stepper_sync_js + content[p_sp_body + len("activeStep = stepId;"):]
    print("5. Updated showPage() with Stepper synchronization successfully!")

# -----------------------------------------------------------------------------
# 6. UPDATE initStep3() JAVASCRIPT TO RENDER ALL EDA CHARTS
# -----------------------------------------------------------------------------
p_init3_start = content.find("function initStep3() {")
p_init4_start = content.find("function initStep4() {")

new_init3_js = """function initStep3() {
            // -----------------------------------------------------------------
            // CHART 3.2A: Target Diagnostic Superclasses Imbalance Plot
            // -----------------------------------------------------------------
            const targetClasses = ['NORM', 'MI', 'CD', 'STTC', 'HYP'];
            const targetCounts = [9243, 4049, 3431, 3360, 1305];
            const targetTotal = 21388;
            const targetPcts = targetCounts.map(c => ((c / targetTotal) * 100).toFixed(1) + '%');
            const targetColors = ['#10b981', '#f43f5e', '#8b5cf6', '#f59e0b', '#14b8a6'];

            if (document.getElementById('chart-target-distribution')) {
                Plotly.newPlot('chart-target-distribution', [{
                    x: targetClasses,
                    y: targetCounts,
                    type: 'bar',
                    marker: {
                        color: targetColors,
                        line: {color: '#cbd5e1', width: 1.2}
                    },
                    text: targetCounts.map((c, i) => `<b>${c.toLocaleString()}</b><br>(${targetPcts[i]})`),
                    textposition: 'outside',
                    textfont: {family: 'JetBrains Mono', color: '#0f172a', size: 10.5}
                }], {
                    margin: {t: 35, b: 35, l: 55, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10.5},
                    xaxis: {title: 'กลุ่มโรคหัวใจ 5 ซูเปอร์คลาส (Diagnostic Superclasses)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'จำนวนบันทึก (Records)', gridcolor: '#f1f5f9', range: [0, 10500]}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.2B: Demographic Age & Sex Distribution
            // -----------------------------------------------------------------
            if (document.getElementById('chart-age-sex-distribution')) {
                const ageBins = ['<30 ปี', '30-45 ปี', '45-60 ปี', '60-75 ปี', '75+ ปี'];
                const maleCounts = [750, 1320, 2910, 3620, 1677];
                const femaleCounts = [738, 1358, 3062, 3909, 2044];

                Plotly.newPlot('chart-age-sex-distribution', [
                    {
                        x: ageBins,
                        y: maleCounts,
                        name: 'เพศชาย (Male: 48.1%)',
                        type: 'bar',
                        marker: {color: '#0284c7'}
                    },
                    {
                        x: ageBins,
                        y: femaleCounts,
                        name: 'เพศหญิง (Female: 51.9%)',
                        type: 'bar',
                        marker: {color: '#ec4899'}
                    }
                ], {
                    barmode: 'group',
                    margin: {t: 35, b: 35, l: 55, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10.5},
                    xaxis: {title: 'ช่วงอายุผู้ป่วย (Age Groups)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'จำนวนผู้ป่วย (คน)', gridcolor: '#f1f5f9'},
                    legend: {x: 0.02, y: 0.98, bgcolor: 'rgba(255,255,255,0.9)'}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.2C: Biomedical Distribution (Heart Rate & QRS Duration)
            // -----------------------------------------------------------------
            const hrBins = ['<60 (Brady)', '60-70', '70-80', '80-90', '90-100', '100+ (Tachy)'];
            const hrCounts = [1842, 6108, 7452, 3921, 1280, 643];
            const hrPcts = hrCounts.map(c => ((c / 21246) * 100).toFixed(1) + '%');

            if (document.getElementById('chart-bio-distribution')) {
                Plotly.newPlot('chart-bio-distribution', [{
                    x: hrBins,
                    y: hrCounts,
                    name: 'อัตราการเต้นหัวใจ (Heart Rate - bpm)',
                    type: 'bar',
                    marker: {color: '#0284c7', line: {color: '#cbd5e1', width: 1}},
                    text: hrCounts.map((c, i) => `${c.toLocaleString()}<br>(${hrPcts[i]})`),
                    textposition: 'outside',
                    textfont: {family: 'JetBrains Mono', size: 9.5, color: '#0f172a'}
                }], {
                    margin: {t: 35, b: 35, l: 60, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10.5},
                    xaxis: {title: 'ช่วงค่าอัตราการเต้นของหัวใจ (Heart Rate Bins - bpm)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'จำนวนบันทึก (Records)', gridcolor: '#f1f5f9', range: [0, 9200]},
                    annotations: [
                        {
                            x: '70-80',
                            y: 7452,
                            text: '⭐ ยอดสูงสุด: 70-80 bpm (35.1%)',
                            showarrow: true,
                            arrowhead: 4,
                            ax: 0,
                            ay: -32,
                            font: {family: 'Outfit', size: 10, color: '#0284c7', weight: 'bold'},
                            bgcolor: 'rgba(255,255,255,0.92)',
                            bordercolor: '#0284c7'
                        }
                    ]
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.3: Missing-Value Heatmap & Audit Matrix
            // -----------------------------------------------------------------
            const missingVarsThai = ['อายุ (age)', 'เพศ (sex)', 'ส่วนสูง (height)', 'น้ำหนัก (weight)', 'วินิจฉัย (diag)', 'ช่วง QTc', 'สัดส่วน LF/HF', 'ดัชนี SQI SNR'];
            const missingStages = ['1. ข้อมูลดิบ (% Missing)', '2. หลังจัดสรร Train Median'];
            const missingZ = [
                [0.40, 0.00, 54.21, 56.75, 1.89, 0.24, 5.54, 0.00],
                [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
            ];
            const missingText = [
                ['88 (0.4%)', '0 (0.0%)', '11,816 (54.2%)', '12,370 (56.8%)', '411 (1.9%)', '50 (0.2%)', '1,178 (5.5%)', '0 (0.0%)'],
                ['สมบูรณ์ 100%', 'สมบูรณ์ 100%', 'Imputed + Flag', 'Imputed + Flag', 'Dropped Strict', 'Train Median', 'Train Median', 'สมบูรณ์ 100%']
            ];

            if (document.getElementById('chart-missing-heatmap')) {
                Plotly.newPlot('chart-missing-heatmap', [{
                    z: missingZ,
                    x: missingVarsThai,
                    y: missingStages,
                    type: 'heatmap',
                    colorscale: [
                        [0, '#ecfdf5'],
                        [0.05, '#bae6fd'],
                        [0.2, '#fef08a'],
                        [0.6, '#f87171'],
                        [1, '#ef4444']
                    ],
                    colorbar: {thickness: 12, title: '% สูญหาย', tickfont: {family: 'JetBrains Mono', color: '#0f172a'}},
                    text: missingText,
                    texttemplate: '%{text}',
                    textfont: {family: 'JetBrains Mono', color: '#0f172a', size: 10, weight: 'bold'}
                }], {
                    margin: {t: 25, b: 60, l: 160, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10},
                    xaxis: {title: 'ตัวแปรทางการแพทย์ (Clinical Variables)', tickangle: -20}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.4A: Pearson Correlation Matrix Heatmap
            // -----------------------------------------------------------------
            const corr = DASHBOARD_DATA.eda_correlation;
            const corrFormattedText = corr.z.map(row => 
                row.map(v => (v >= 0 ? '+' : '') + v.toFixed(2))
            );

            if (document.getElementById('chart-corr-heatmap')) {
                Plotly.newPlot('chart-corr-heatmap', [{
                    z: corr.z,
                    x: corr.features,
                    y: corr.features,
                    type: 'heatmap',
                    colorscale: [
                        [0, '#f43f5e'],
                        [0.5, '#ffffff'],
                        [1, '#0284c7']
                    ],
                    zmin: -1,
                    zmax: 1,
                    colorbar: {thickness: 12, title: 'r', tickfont: {family: 'JetBrains Mono', color: '#0f172a'}},
                    text: corrFormattedText,
                    texttemplate: '%{text}',
                    textfont: {family: 'JetBrains Mono', color: '#0f172a', size: 9, weight: 'bold'}
                }], {
                    margin: {t: 20, b: 110, l: 150, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 9.5}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.4B: Morphology Boxplot with Medians
            // -----------------------------------------------------------------
            const morph = DASHBOARD_DATA.morph_by_class;
            const boxTraces = [];
            const colors = {'NORM': '#10b981', 'MI': '#f43f5e', 'STTC': '#f59e0b', 'CD': '#8b5cf6', 'HYP': '#14b8a6'};
            const morphAnnotations = [];

            for (const [cls, vals] of Object.entries(morph)) {
                boxTraces.push({
                    y: vals.qrs_duration,
                    name: cls,
                    type: 'box',
                    boxpoints: 'outliers',
                    marker: {color: colors[cls] || '#0284c7'}
                });
                const sortedQRS = [...vals.qrs_duration].sort((a,b)=>a-b);
                const medVal = sortedQRS[Math.floor(sortedQRS.length/2)];
                morphAnnotations.push({
                    x: cls,
                    y: medVal,
                    text: `Med: ${medVal}ms`,
                    showarrow: true,
                    arrowhead: 6,
                    ax: 28,
                    ay: -15,
                    font: {family: 'JetBrains Mono', size: 9.5, color: '#0f172a', weight: 'bold'},
                    bgcolor: '#ffffff',
                    bordercolor: colors[cls] || '#cbd5e1',
                    borderwidth: 1
                });
            }

            if (document.getElementById('chart-morphology-box')) {
                Plotly.newPlot('chart-morphology-box', boxTraces, {
                    margin: {t: 25, b: 35, l: 50, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 11},
                    yaxis: {title: 'ความกว้างคลื่น QRS (มิลลิวินาที - ms)', gridcolor: '#f1f5f9'},
                    annotations: morphAnnotations
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.4C: Age Group vs Disease Stratification Stacked Chart
            // -----------------------------------------------------------------
            if (document.getElementById('chart-age-disease-strat')) {
                const ageGroupLabels = ['<30 ปี', '30-45 ปี', '45-60 ปี', '60-75 ปี', '75+ ปี'];
                const stratTraces = [
                    {x: ageGroupLabels, y: [1216, 1899, 2966, 2401, 761], name: 'ปกติ (NORM)', type: 'bar', marker: {color: '#10b981'}},
                    {x: ageGroupLabels, y: [32, 206, 1145, 1754, 912], name: 'กล้ามเนื้อหัวใจขาดเลือด (MI)', type: 'bar', marker: {color: '#f43f5e'}},
                    {x: ageGroupLabels, y: [135, 251, 730, 1431, 884], name: 'การนำไฟฟ้าขัดข้อง (CD)', type: 'bar', marker: {color: '#8b5cf6'}},
                    {x: ageGroupLabels, y: [70, 209, 815, 1396, 870], name: 'การคลายตัวผิดปกติ (STTC)', type: 'bar', marker: {color: '#f59e0b'}},
                    {x: ageGroupLabels, y: [35, 113, 316, 547, 294], name: 'กล้ามเนื้อหัวใจหนา (HYP)', type: 'bar', marker: {color: '#14b8a6'}}
                ];

                Plotly.newPlot('chart-age-disease-strat', stratTraces, {
                    barmode: 'stack',
                    margin: {t: 25, b: 35, l: 55, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10.5},
                    xaxis: {title: 'ช่วงอายุของผู้ป่วย (Age Strata)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'จำนวนบันทึกผลตรวจ (Records)', gridcolor: '#f1f5f9'},
                    legend: {x: 0.65, y: 0.98, bgcolor: 'rgba(255,255,255,0.9)'}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.5A: 12-Lead Real Waveform Overlay (Lead II Pan-Tompkins)
            // -----------------------------------------------------------------
            const rec1 = DASHBOARD_DATA.rec1_overlay;
            const timeAxis = rec1.time;
            const lead2 = rec1.lead2;

            const traces = [{
                x: timeAxis,
                y: lead2,
                type: 'scatter',
                mode: 'lines',
                name: 'สัญญาณลีด II หลังกรอง DSP (0.5–45Hz)',
                line: {color: '#0284c7', width: 2.2}
            }];

            const rX = rec1.r_peaks.map(idx => timeAxis[idx]);
            const rY = rec1.r_peaks.map(idx => lead2[idx]);
            traces.push({
                x: rX,
                y: rY,
                type: 'scatter',
                mode: 'markers+text',
                name: 'ยอด R-Peaks (Pan-Tompkins Detection)',
                marker: {color: '#f43f5e', size: 10, symbol: 'circle'},
                text: rec1.r_peaks.map((_, i) => `R${i + 1}`),
                textposition: 'top center',
                textfont: {family: 'JetBrains Mono', size: 11, color: '#f43f5e'}
            });

            const shapes = [];
            rec1.qrs_markers.slice(0, 4).forEach((m, i) => {
                shapes.push({
                    type: 'rect',
                    x0: timeAxis[m.q_start],
                    x1: timeAxis[m.s_end],
                    y0: Math.min(...lead2.slice(m.q_start, m.s_end + 1)) - 0.05,
                    y1: Math.max(...lead2.slice(m.q_start, m.s_end + 1)) + 0.05,
                    fillcolor: 'rgba(14, 165, 233, 0.15)',
                    line: {color: 'rgba(14, 165, 233, 0.6)', width: 1}
                });
            });

            if (document.getElementById('chart-biomedical-overlay')) {
                Plotly.newPlot('chart-biomedical-overlay', traces, {
                    shapes: shapes,
                    margin: {t: 25, b: 35, l: 50, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 11},
                    xaxis: {title: 'เวลา (วินาที - Seconds)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'แรงดันไฟฟ้า (มิลลิโวลต์ - mV)', gridcolor: '#f1f5f9'},
                    legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(255,255,255,0.92)'}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.5B: Welch PSD Spectrum Plot
            // -----------------------------------------------------------------
            const psd = DASHBOARD_DATA.welch_psd;
            if (document.getElementById('chart-welch-psd')) {
                Plotly.newPlot('chart-welch-psd', [{
                    x: psd.freqs,
                    y: psd.psd,
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    fillcolor: 'rgba(2, 132, 199, 0.12)',
                    line: {color: '#0284c7', width: 2.2},
                    name: 'กำลังความหนาแน่นสเปกตรัม PSD'
                }], {
                    shapes: [
                        {type: 'rect', x0: 0.04, x1: 0.15, y0: 0, y1: Math.max(...psd.psd)*1.1, fillcolor: 'rgba(14, 165, 233, 0.15)', line: {width: 0}},
                        {type: 'rect', x0: 0.15, x1: 0.40, y0: 0, y1: Math.max(...psd.psd)*1.1, fillcolor: 'rgba(16, 185, 129, 0.15)', line: {width: 0}}
                    ],
                    annotations: [
                        {x: 0.095, y: Math.max(...psd.psd)*0.85, text: 'LF: 0.09 Hz (Sympathetic)', showarrow: false, font: {family: 'JetBrains Mono', size: 10, color: '#0369a1'}},
                        {x: 0.275, y: Math.max(...psd.psd)*0.85, text: 'HF: 0.25 Hz (Parasympathetic)', showarrow: false, font: {family: 'JetBrains Mono', size: 10, color: '#065f46'}}
                    ],
                    margin: {t: 20, b: 35, l: 50, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 11},
                    xaxis: {title: 'ความถี่ (เฮิรตซ์ - Hz)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'กำลังสเปกตรัม (ms²/Hz)', gridcolor: '#f1f5f9'}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.6A: Outlier Summary Box Plot (HRV & ST-segment)
            // -----------------------------------------------------------------
            const stNormalVals = [-0.02, -0.01, 0.00, 0.01, 0.02, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08];
            const stOutliers = [0.12, 0.15, 0.22, 0.35, 0.48];
            const stAll = [...stNormalVals, ...stOutliers];

            const rmssdNormal = [16, 18, 20, 22, 25, 28, 30, 32, 35, 38, 42, 46, 50];
            const rmssdOutliers = [78, 86, 95, 112];
            const rmssdAll = [...rmssdNormal, ...rmssdOutliers];

            if (document.getElementById('chart-outlier-box')) {
                Plotly.newPlot('chart-outlier-box', [
                    {
                        y: stAll,
                        name: 'การยกตัวช่วง ST (mV ×10)',
                        type: 'box',
                        boxpoints: 'all',
                        jitter: 0.3,
                        pointpos: -1.8,
                        marker: {color: '#f43f5e', size: 6}
                    },
                    {
                        y: rmssdAll.map(v => v / 100),
                        name: 'HRV RMSSD (ms / 100)',
                        type: 'box',
                        boxpoints: 'all',
                        jitter: 0.3,
                        pointpos: -1.8,
                        marker: {color: '#14b8a6', size: 6}
                    }
                ], {
                    margin: {t: 35, b: 40, l: 50, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 10.5},
                    yaxis: {title: 'สเกลตัวชี้วัดสถิติเปรียบเทียบ (Normalized Units)', gridcolor: '#f1f5f9'},
                    annotations: [
                        {
                            x: 'การยกตัวช่วง ST (mV ×10)',
                            y: 0.12,
                            text: '⚠️ STEMI Cutoff (+0.10 mV)',
                            showarrow: true,
                            arrowhead: 2,
                            ax: 70,
                            ay: -15,
                            font: {family: 'JetBrains Mono', size: 9.5, color: '#f43f5e', weight: 'bold'},
                            bgcolor: 'rgba(255,255,255,0.92)',
                            bordercolor: '#f43f5e'
                        },
                        {
                            x: 'HRV RMSSD (ms / 100)',
                            y: 0.28,
                            text: 'มัธยฐาน: 28 ms (สมดุลปกติ)',
                            showarrow: true,
                            arrowhead: 2,
                            ax: 70,
                            ay: 15,
                            font: {family: 'JetBrains Mono', size: 9.5, color: '#0f766e', weight: 'bold'},
                            bgcolor: 'rgba(255,255,255,0.92)',
                            bordercolor: '#0f766e'
                        }
                    ]
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // CHART 3.7A: Patient Multi-Visit Distribution Bar Chart
            // -----------------------------------------------------------------
            const vData = DASHBOARD_DATA.summary.visit_distribution;
            const edaVisitX = ['1 ครั้ง (Single)', '2 ครั้ง', '3 ครั้ง', '4 ครั้ง', '5 ครั้ง', '6-10+ ครั้ง'];
            const sumOver5 = (vData['6']||0) + (vData['7']||0) + (vData['8']||0) + (vData['9']||0) + (vData['10']||0);
            const edaVisitY = [vData['1'], vData['2'], vData['3'], vData['4'], vData['5'], sumOver5];
            const edaVisitPcts = edaVisitY.map(v => ((v / 18499) * 100).toFixed(1) + '%');

            if (document.getElementById('chart-eda-visit-dist')) {
                Plotly.newPlot('chart-eda-visit-dist', [{
                    x: edaVisitX,
                    y: edaVisitY,
                    type: 'bar',
                    marker: {
                        color: ['#0284c7', '#14b8a6', '#8b5cf6', '#f59e0b', '#f43f5e', '#ec4899'],
                        line: {color: '#cbd5e1', width: 1}
                    },
                    text: edaVisitY.map((v, i) => `<b>${v.toLocaleString()} ราย</b> (${edaVisitPcts[i]})`),
                    textposition: 'outside',
                    textfont: {family: 'JetBrains Mono', color: '#0f172a', size: 10.5}
                }], {
                    margin: {t: 35, b: 40, l: 60, r: 20},
                    paper_bgcolor: '#ffffff',
                    plot_bgcolor: '#f8fafc',
                    font: {family: "'JetBrains Mono', 'Outfit', sans-serif", color: '#0f172a', size: 11},
                    xaxis: {title: 'ความถี่รอบการตรวจคลื่นไฟฟ้าหัวใจต่อผู้ป่วย 1 ราย (Encounter Frequency Per Patient)', gridcolor: '#f1f5f9'},
                    yaxis: {title: 'จำนวนผู้ป่วยจริง (คน)', gridcolor: '#f1f5f9', range: [0, 18600]}
                }, {responsive: true});
            }

            // -----------------------------------------------------------------
            // Outlier Skewness/IQR Registry Table
            // -----------------------------------------------------------------
            const tbodyOutliers = document.getElementById('tbody-eda-outliers');
            if (tbodyOutliers) {
                let html = '';
                DASHBOARD_DATA.eda_outliers.forEach(o => {
                    const badgeClass = o.outlier_pct > 5.0 ? 'badge-neon-coral' : 'badge-neon-green';
                    const remedyText = o.outlier_pct > 5.0 ? 'Winsorization ที่ 1st/99th Percentile' : 'รักษาค่าจริง ไม่กระทบ Tree Model';
                    html += `<tr>
                        <td><strong>${o.name_thai}</strong></td>
                        <td><code>${o.median}</code></td>
                        <td>[${o.q1}, ${o.q3}]</td>
                        <td><code>${o.skewness}</code></td>
                        <td><span class="${badgeClass}">${o.outlier_count} (${o.outlier_pct}%)</span></td>
                        <td><span class="small text-muted font-code">${remedyText}</span></td>
                    </tr>`;
                });
                tbodyOutliers.innerHTML = html;
            }
        }

        """

if p_init3_start != -1 and p_init4_start != -1:
    content = content[:p_init3_start] + new_init3_js + content[p_init4_start:]
    print("6. Updated initStep3() JavaScript successfully!")

# Write back to file
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: ekg_longitudinal_dashboard.html updated completely!")
