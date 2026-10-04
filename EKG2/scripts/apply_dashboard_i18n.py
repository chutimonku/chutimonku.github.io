# scripts/apply_dashboard_i18n.py
import sys

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

print('Initial content length:', len(content))

# 1. NAVBAR, SIDEBAR & STEPPER REPLACEMENT
p1 = content.find('<header class="top-navbar">')
p2 = content.find('<section id="page-step-1" class="step-page active-page">')

if p1 == -1 or p2 == -1:
    print('ERROR: Navbar / Stepper anchors not found')
    sys.exit(1)

nav_sidebar_stepper = """    <!-- TOP FIXED NAVBAR -->
    <header class="top-navbar">
        <div class="d-flex align-items-center justify-content-between w-100">
            <div class="d-flex align-items-center">
                <button class="btn btn-sm btn-outline-primary me-3 font-code d-flex align-items-center gap-2" id="btn-toggle-sidebar" onclick="toggleSidebar()" title="ย่อ/ขยายเมนูนำทาง (Toggle Sidebar Menu)">
                    <i class="fas fa-bars"></i>
                    <span id="btn-toggle-sidebar-text">☰ ย่อ/ขยายเมนู</span>
                </button>
                <span class="fs-4 me-2">⚡</span>
                <div>
                    <h5 class="mb-0 fw-bold text-dark font-code">PTB-XL ECG Intelligence Platform</h5>
                    <span class="text-muted" id="nav-app-subtitle" style="font-size: 0.72rem;">ระบบวิเคราะห์และติดตามคลื่นไฟฟ้าหัวใจ 12 ลีด (Clinical AI & CDS)</span>
                </div>
            </div>
            <div class="d-flex align-items-center gap-3">
                <span class="badge-neon-blue font-code" id="nb-stat-records"><i class="fas fa-database me-1"></i> 21,246 บันทึก EKG (18,499 คนไข้จริง)</span>
                <span class="badge-neon-green font-code" id="nb-stat-leakage"><i class="fas fa-shield-check me-1"></i> GroupKFold ป้องกันข้อมูลรั่วไหล ✅</span>
                <span class="badge-neon-teal font-code" id="nb-stat-hipaa"><i class="fas fa-lock me-1"></i> ได้มาตรฐาน HIPAA/PDPA ✅</span>

                <!-- BILINGUAL LANGUAGE SWITCHER BUTTONS -->
                <div class="btn-group font-code shadow-sm ms-2" role="group" aria-label="Language Selector">
                    <button type="button" class="btn btn-sm btn-primary py-1 px-3 fw-bold" id="btn-lang-th" onclick="setLanguage('th')">🇹🇭 TH</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary py-1 px-3 fw-bold" id="btn-lang-en" onclick="setLanguage('en')">🇬🇧 EN</button>
                </div>
            </div>
        </div>
    </header>

    <div class="app-layout">
        <!-- FIXED COLLAPSIBLE LEFT SIDEBAR NAVIGATION -->
        <nav class="sidebar">
            <div class="sidebar-heading" id="sidebar-main-heading">ขั้นตอนการวิเคราะห์ (Pipeline Steps)</div>

            <!-- STEP 1 -->
            <div class="nav-step-item">
                <button class="nav-step-btn active" id="btn-step-1" onclick="showPage('step-1')">
                    <span id="sidebar-step1-btn"><i class="fas fa-database text-primary icon-prefix me-2"></i> 1. ข้อมูลตั้งต้น & ที่มา 🏛️</span>
                    <i class="fas fa-chevron-down text-muted small chevron-icon" id="chevron-step-1"></i>
                </button>
                <ul class="submenu-list show" id="submenu-step-1">
                    <li><a href="#sec-grain-architecture" class="submenu-link" id="sub-grain-arch" onclick="jumpSection('step-1', 'sec-grain-architecture', event)">ระดับข้อมูลคนไข้และการตรวจ</a></li>
                    <li><a href="#sec-multi-visit" class="submenu-link" id="sub-multi-visit" onclick="jumpSection('step-1', 'sec-multi-visit', event)">การกระจายจำนวนครั้งที่ตรวจ</a></li>
                    <li><a href="#sec-attrition-funnel" class="submenu-link" id="sub-attrition" onclick="jumpSection('step-1', 'sec-attrition-funnel', event)">ขั้นตอนคัดกรองข้อมูล (Attrition)</a></li>
                    <li><a href="#sec-data-dict" class="submenu-link" id="sub-data-dict" onclick="jumpSection('step-1', 'sec-data-dict', event)">พจนานุกรมข้อมูล (Data Dictionary)</a></li>
                    <li><a href="#sec-missing-inv" class="submenu-link" id="sub-missing-inv" onclick="jumpSection('step-1', 'sec-missing-inv', event)">ข้อมูลสูญหาย (MCAR/MAR/MNAR)</a></li>
                    <li><a href="#sec-provenance" class="submenu-link" id="sub-provenance" onclick="jumpSection('step-1', 'sec-provenance', event)">ความถูกต้องของไฟล์ (SHA-256)</a></li>
                </ul>
            </div>

            <!-- STEP 2 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-2" onclick="showPage('step-2')">
                    <span id="sidebar-step2-btn"><i class="fas fa-wave-square text-info icon-prefix me-2"></i> 2. ล้างสัญญาณ EKG & DSP 🌊</span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-2"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-2">
                    <li><a href="#sec-dsp-pipeline" class="submenu-link" id="sub-dsp-pipe" onclick="jumpSection('step-2', 'sec-dsp-pipeline', event)">ขั้นตอนการกรองสัญญาณ DSP</a></li>
                    <li><a href="#sec-dual-waveform" class="submenu-link" id="sub-dual-wave" onclick="jumpSection('step-2', 'sec-dual-waveform', event)">เปรียบเทียบคลื่นก่อน-หลังล้าง</a></li>
                    <li><a href="#sec-sqi-heatmap" class="submenu-link" id="sub-sqi-heat" onclick="jumpSection('step-2', 'sec-sqi-heatmap', event)">แผนภาพคุณภาพสัญญาณ (SQI)</a></li>
                    <li><a href="#sec-quarantine-table" class="submenu-link" id="sub-quarantine" onclick="jumpSection('step-2', 'sec-quarantine-table', event)">สัญญาณที่ตัดออกเพราะสัญญาณรบกวน</a></li>
                </ul>
            </div>

            <!-- STEP 3 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-3" onclick="showPage('step-3')">
                    <span id="sidebar-step3-btn"><i class="fas fa-chart-line text-warning icon-prefix me-2"></i> 3. สำรวจข้อมูล (EDA) 🔬</span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-3"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-3">
                    <li><a href="#sec-eda-31" class="submenu-link" id="sub-eda-31" onclick="jumpSection('step-3', 'sec-eda-31', event)">3.1 ขนาดข้อมูลและคลังฟีเจอร์ (Data Dimensions)</a></li>
                    <li><a href="#sec-eda-32" class="submenu-link" id="sub-eda-32" onclick="jumpSection('step-3', 'sec-eda-32', event)">3.2 การกระจายตัวของข้อมูล (Univariate)</a></li>
                    <li><a href="#sec-eda-33" class="submenu-link" id="sub-eda-33" onclick="jumpSection('step-3', 'sec-eda-33', event)">3.3 ข้อมูลสูญหายและคุณภาพ (Missingness & SQI)</a></li>
                    <li><a href="#sec-eda-34" class="submenu-link" id="sub-eda-34" onclick="jumpSection('step-3', 'sec-eda-34', event)">3.4 ความสัมพันธ์ระหว่างตัวแปรและโรค (Multivariate)</a></li>
                    <li><a href="#sec-eda-35" class="submenu-link" id="sub-eda-35" onclick="jumpSection('step-3', 'sec-eda-35', event)">3.5 คลื่นสัญญาณและความถี่สเปกตรัม (Waveform & PSD)</a></li>
                    <li><a href="#sec-eda-36" class="submenu-link" id="sub-eda-36" onclick="jumpSection('step-3', 'sec-eda-36', event)">3.6 ตรวจจับค่าผิดปกติทางการแพทย์ (Outliers)</a></li>
                    <li><a href="#sec-eda-37" class="submenu-link" id="sub-eda-37" onclick="jumpSection('step-3', 'sec-eda-37', event)">3.7 คนไข้ที่มาตรวจซ้ำหลายครั้ง (Longitudinal)</a></li>
                    <li><a href="#sec-eda-38" class="submenu-link" id="sub-eda-38" onclick="jumpSection('step-3', 'sec-eda-38', event)">3.8 ตรวจสอบความพร้อมก่อนเทรนโมเดล (Readiness Gate)</a></li>
                </ul>
            </div>

            <!-- STEP 4 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-4" onclick="showPage('step-4')">
                    <span id="sidebar-step4-btn"><i class="fas fa-trophy text-success icon-prefix me-2"></i> 4. เปรียบเทียบโมเดล AI 🏆</span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-4"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-4">
                    <li><a href="#sec-table-b" class="submenu-link" id="sub-tab-b" onclick="jumpSection('step-4', 'sec-table-b', event)">ตาราง ข: โมเดล Supervised ML</a></li>
                    <li><a href="#sec-table-c" class="submenu-link" id="sub-tab-c" onclick="jumpSection('step-4', 'sec-table-c', event)">ตาราง ค: Deep Learning 1D Waveforms</a></li>
                    <li><a href="#sec-table-a" class="submenu-link" id="sub-tab-a" onclick="jumpSection('step-4', 'sec-table-a', event)">ตาราง ก: Unsupervised & Anomaly</a></li>
                    <li><a href="#sec-table-d" class="submenu-link" id="sub-tab-d" onclick="jumpSection('step-4', 'sec-table-d', event)">ตาราง ง: สรุปผลด้วย Clinical LLM</a></li>
                    <li><a href="#sec-groupkfold" class="submenu-link" id="sub-groupkfold" onclick="jumpSection('step-4', 'sec-groupkfold', event)">การแบ่งข้อมูลคนไข้ (GroupKFold)</a></li>
                    <li><a href="#sec-conf-matrix" class="submenu-link" id="sub-conf-matrix" onclick="jumpSection('step-4', 'sec-conf-matrix', event)">Confusion Matrix แยก 5 กลุ่มโรค</a></li>
                    <li><a href="#sec-roc-curves" class="submenu-link" id="sub-roc-curves" onclick="jumpSection('step-4', 'sec-roc-curves', event)">เส้นโค้ง ROC-AUC 5 กลุ่มโรค</a></li>
                    <li><a href="#sec-feature-gain" class="submenu-link" id="sub-feature-gain" onclick="jumpSection('step-4', 'sec-feature-gain', event)">15 ฟีเจอร์สำคัญที่สุด (Gain)</a></li>
                </ul>
            </div>

            <!-- STEP 5 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-5" onclick="showPage('step-5')">
                    <span id="sidebar-step5-btn"><i class="fas fa-user-injured text-danger icon-prefix me-2"></i> 5. ดูประวัติคนไข้ & CDS 🩺</span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-5"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-5">
                    <li><a href="#sec-executive-kpis" class="submenu-link" id="sub-exec-kpis" onclick="jumpSection('step-5', 'sec-executive-kpis', event)">ตัวชี้วัดสำคัญระดับผู้บริหาร (4 KPIs)</a></li>
                    <li><a href="#sec-patient-timeline" class="submenu-link" id="sub-pat-timeline" onclick="jumpSection('step-5', 'sec-patient-timeline', event)">ค้นหาคนไข้และไทม์ไลน์ (Level 1)</a></li>
                    <li><a href="#sec-instant-diagnosis" class="submenu-link" id="sub-instant-diag" onclick="jumpSection('step-5', 'sec-instant-diagnosis', event)">สรุปผลการวินิจฉัยโรคหัวใจทันที (Level 2)</a></li>
                    <li><a href="#sec-detailed-metrics" class="submenu-link" id="sub-det-metrics" onclick="jumpSection('step-5', 'sec-detailed-metrics', event)">ค่าสรีรวิทยาคลินิกโดยละเอียด</a></li>
                    <li><a href="#sec-12lead-xai" class="submenu-link" id="sub-12lead-xai" onclick="jumpSection('step-5', 'sec-12lead-xai', event)">คลื่น 12 ลีด & ไฮไลต์ AI (XAI)</a></li>
                    <li><a href="#sec-llm-narrative" class="submenu-link" id="sub-llm-narrative" onclick="jumpSection('step-5', 'sec-llm-narrative', event)">บันทึกสรุปผลทางการแพทย์ (Clinical LLM)</a></li>
                    <li><a href="#sec-local-shap" class="submenu-link" id="sub-local-shap" onclick="jumpSection('step-5', 'sec-local-shap', event)">ปัจจัยที่มีผลต่อการทำนาย (SHAP)</a></li>
                    <li><a href="#sec-what-if-sim" class="submenu-link" id="sub-whatif-sim" onclick="jumpSection('step-5', 'sec-what-if-sim', event)">ตัวจำลองความเสี่ยง What-If (Level 3)</a></li>
                </ul>
            </div>

            <div class="mt-4 p-3 rounded-4 bg-light border">
                <div class="small fw-bold text-dark mb-1 font-code" id="sidebar-disclaimer-title">
                    <i class="fas fa-shield-halved me-1 text-primary"></i> ขอบเขตการใช้งานทางคลินิก
                </div>
                <div class="text-muted" id="sidebar-disclaimer-body" style="font-size: 0.76rem; line-height: 1.5;">
                    ระบบนี้ออกแบบขึ้นเพื่อเป็น<strong>เครื่องมือช่วยแพทย์ตัดสินใจ (CDS)</strong> เพื่อคัดกรองเบื้องต้น ไม่สามารถทดแทนการวินิจฉัยยืนยันโดยแพทย์อายุรศาสตร์โรคหัวใจได้
                </div>
            </div>
        </nav>

        <!-- MAIN DISPLAY CANVAS -->
        <main class="main-canvas">

            <!-- ============================================================= -->
            <!-- GLOBAL PIPELINE PROGRESS STEPPER & SYSTEM ROADMAP              -->
            <!-- ============================================================= -->
            <div class="card card-custom mb-4 p-3 border-primary-subtle bg-white shadow-sm" id="pipeline-stepper-header">
                <div class="d-flex flex-wrap align-items-center justify-content-between pb-2 mb-2 border-bottom">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-primary text-white font-code px-2 py-1" id="stepper-header-badge"><i class="fas fa-project-diagram me-1"></i> PIPELINE ROADMAP</span>
                        <span class="fw-bold text-dark font-code" id="stepper-header-title" style="font-size: 0.95rem;">ขั้นตอนการทำงานและพัฒนาแบบจำลอง EKG ตั้งแต่ต้นจนจบ (Clinical ML/DL Workflow)</span>
                    </div>
                    <div class="d-flex align-items-center gap-2 font-code small text-muted">
                        <span class="badge-neon-green" id="stepper-badge-audit"><i class="fas fa-check-circle me-1"></i> มาตรฐานการวิเคราะห์ 5 เฟส</span>
                        <span class="badge-neon-blue" id="stepper-badge-nav"><i class="fas fa-sliders me-1"></i> คลิกเลือกดูแต่ละเฟสได้ทันที</span>
                    </div>
                </div>
                <div class="row g-2 text-center font-code">
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn active" id="stepper-step-1" onclick="showPage('step-1')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-primary text-white fw-bold" id="stepper-b1-phase">เฟส 1</span>
                                <i class="fas fa-database text-primary"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" id="stepper-b1-title">1. ข้อมูลตั้งต้น & ที่มา</div>
                            <div class="text-muted text-truncate" id="stepper-b1-sub" style="font-size: 0.70rem;">Grain & Provenance</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-2" onclick="showPage('step-2')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-info text-white fw-bold" id="stepper-b2-phase">เฟส 2</span>
                                <i class="fas fa-wave-square text-info"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" id="stepper-b2-title">2. ล้างสัญญาณ EKG</div>
                            <div class="text-muted text-truncate" id="stepper-b2-sub" style="font-size: 0.70rem;">DSP กรองคลื่น & คุณภาพ</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-3" onclick="showPage('step-3')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-warning text-dark fw-bold" id="stepper-b3-phase">เฟส 3</span>
                                <i class="fas fa-chart-line text-warning"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" id="stepper-b3-title">3. สำรวจข้อมูล (EDA)</div>
                            <div class="text-muted text-truncate" id="stepper-b3-sub" style="font-size: 0.70rem;">8 ขั้นตอนวิเคราะห์ละเอียด</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-4" onclick="showPage('step-4')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-success text-white fw-bold" id="stepper-b4-phase">เฟส 4</span>
                                <i class="fas fa-trophy text-success"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" id="stepper-b4-title">4. เปรียบเทียบโมเดล AI</div>
                            <div class="text-muted text-truncate" id="stepper-b4-sub" style="font-size: 0.70rem;">ML, DL & 1D-CNN</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-5" onclick="showPage('step-5')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-danger text-white fw-bold" id="stepper-b5-phase">เฟส 5</span>
                                <i class="fas fa-user-injured text-danger"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" id="stepper-b5-title">5. ประวัติคนไข้ & CDS</div>
                            <div class="text-muted text-truncate" id="stepper-b5-sub" style="font-size: 0.70rem;">ติดตามอาการ & จำลองผล</div>
                        </button>
                    </div>
                </div>
            </div>
"""

content = content[:p1] + nav_sidebar_stepper + content[p2:]
print('After Navbar & Stepper replacement length:', len(content))

# 2. STEP 1 HEADER REPLACEMENT
s1_old = """<section id="page-step-1" class="step-page active-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-blue mb-1">ระยะที่ 1 (Phase 1)</span>
                        <h2 class="fw-bold mb-0 text-dark">🏛️ โครงสร้างธรรมาภิบาลข้อมูล & ลำดับชั้นการบันทึก</h2>
                    </div>
                    <div class="text-end">
                        <span class="badge-neon-teal">
                            <i class="fas fa-database me-1"></i> หน่วยการวิเคราะห์: บันทึก EKG 10 วินาที (ecg_id)
                        </span>
                    </div>
                </div>"""

s1_new = """<section id="page-step-1" class="step-page active-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-blue mb-1" id="page-step-1-phase">ระยะที่ 1 (Phase 1)</span>
                        <h2 class="fw-bold mb-0 text-dark" id="page-step-1-title">🏛️ ข้อมูลตั้งต้น & ที่มาของข้อมูล (Data Foundation & Grain)</h2>
                    </div>
                    <div class="text-end">
                        <span class="badge-neon-teal" id="page-step-1-badge">
                            <i class="fas fa-database me-1"></i> หน่วยการวิเคราะห์: บันทึก EKG 10 วินาที (ecg_id)
                        </span>
                    </div>
                </div>"""

if s1_old in content:
    content = content.replace(s1_old, s1_new, 1)
    print('Step 1 header replaced successfully')
else:
    print('WARNING: s1_old not found')

# 3. STEP 2 HEADER REPLACEMENT
s2_old = """<section id="page-step-2" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-teal mb-1">ระยะที่ 2 (Phase 2)</span>
                        <h2 class="fw-bold mb-0 text-dark">🌊 การทำความสะอาดข้อมูล & การตรวจสอบสัญญาณดิจิทัล DSP</h2>
                    </div>
                    <div>
                        <span class="badge-neon-green">
                            <i class="fas fa-microchip me-1"></i> Butterworth 0.5–45Hz + 50Hz Notch Filter
                        </span>
                    </div>
                </div>"""

s2_new = """<section id="page-step-2" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-teal mb-1" id="page-step-2-phase">ระยะที่ 2 (Phase 2)</span>
                        <h2 class="fw-bold mb-0 text-dark" id="page-step-2-title">🌊 ล้างสัญญาณคลื่นไฟฟ้า & ตรวจสอบคุณภาพ DSP</h2>
                    </div>
                    <div>
                        <span class="badge-neon-green" id="page-step-2-badge">
                            <i class="fas fa-microchip me-1"></i> Butterworth 0.5–45Hz + 50Hz Notch Filter
                        </span>
                    </div>
                </div>"""

if s2_old in content:
    content = content.replace(s2_old, s2_new, 1)
    print('Step 2 header replaced successfully')
else:
    print('WARNING: s2_old not found')

# 4. STEP 3 HEADER & PILLS REPLACEMENT
s3_old = """<section id="page-step-3" class="step-page">
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
                </div>"""

s3_new = """<section id="page-step-3" class="step-page">
                <!-- PAGE HEADER & BREADCRUMB -->
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="badge-neon-purple" id="page-step-3-phase"><i class="fas fa-flask me-1"></i> ระยะที่ 3 (Phase 3)</span>
                            <span class="badge-neon-green" id="page-step-3-badge-std"><i class="fas fa-list-check me-1"></i> วิเคราะห์ละเอียด 8 ขั้นตอนตามมาตรฐาน EDA</span>
                        </div>
                        <h2 class="fw-bold mb-0 text-dark" id="page-step-3-title">🔬 สำรวจข้อมูลเชิงลึก 8 ขั้นตอน (EDA) & สกัดฟีเจอร์ EKG</h2>
                        <div class="text-muted small" id="page-step-3-subtitle">สำรวจข้อมูล EKG อย่างเป็นระบบตามลำดับขั้นตอน พร้อมสกัดฟีเจอร์คลื่นไฟฟ้าหัวใจ 63 ตัวแปร</div>
                    </div>
                    <div class="d-flex gap-2 align-items-center mt-2 mt-md-0">
                        <span class="badge-neon-blue font-code"><i class="fas fa-dna me-1"></i> 63 Biomedical Features</span>
                        <span class="badge-neon-teal font-code"><i class="fas fa-shield-halved me-1"></i> Zero Leakage Audited</span>
                    </div>
                </div>

                <!-- QUICK-JUMP HORIZONTAL PILL NAVIGATION FOR 8 EDA STEPS -->
                <div class="eda-pill-nav">
                    <a href="#sec-eda-31" class="eda-pill-btn" id="eda-pill-31"><span class="badge bg-purple text-white">3.1</span> ขนาดและมิติข้อมูล</a>
                    <a href="#sec-eda-32" class="eda-pill-btn" id="eda-pill-32"><span class="badge bg-purple text-white">3.2</span> ตัวแปรเดี่ยว & สมดุลโรค</a>
                    <a href="#sec-eda-33" class="eda-pill-btn" id="eda-pill-33"><span class="badge bg-purple text-white">3.3</span> ข้อมูลสูญหาย & คุณภาพ</a>
                    <a href="#sec-eda-34" class="eda-pill-btn" id="eda-pill-34"><span class="badge bg-purple text-white">3.4</span> สหสัมพันธ์ตัวแปร & โรค</a>
                    <a href="#sec-eda-35" class="eda-pill-btn" id="eda-pill-35"><span class="badge bg-purple text-white">3.5</span> คลื่นสัญญาณ & สเปกตรัม</a>
                    <a href="#sec-eda-36" class="eda-pill-btn" id="eda-pill-36"><span class="badge bg-purple text-white">3.6</span> ตรวจจับค่าผิดปกติ</a>
                    <a href="#sec-eda-37" class="eda-pill-btn" id="eda-pill-37"><span class="badge bg-purple text-white">3.7</span> คนไข้ที่ตรวจซ้ำ</a>
                    <a href="#sec-eda-38" class="eda-pill-btn" id="eda-pill-38"><span class="badge bg-purple text-white">3.8</span> เช็กความพร้อมเทรนโมเดล</a>
                </div>"""

if s3_old in content:
    content = content.replace(s3_old, s3_new, 1)
    print('Step 3 header & pills replaced successfully')
else:
    print('WARNING: s3_old not found')

# 5. STEP 4 HEADER REPLACEMENT
s4_old = """<section id="page-step-4" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-green mb-1">ระยะที่ 4 (Phase 4)</span>
                        <h2 class="fw-bold mb-0 text-dark">🏆 การประเมินกลุ่มแบบจำลองไฮบริด & ลีดเดอร์บอร์ดการทำนายโรค</h2>
                    </div>
                    <div>
                        <span class="badge-neon-blue">
                            <i class="fas fa-users-slash me-1"></i> ผู้ป่วยซ้อนทับ 0% (Zero Leakage)
                        </span>
                    </div>
                </div>"""

s4_new = """<section id="page-step-4" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-green mb-1" id="page-step-4-phase">ระยะที่ 4 (Phase 4)</span>
                        <h2 class="fw-bold mb-0 text-dark" id="page-step-4-title">🏆 เปรียบเทียบประสิทธิภาพโมเดล AI (ML & Deep Learning Leaderboard)</h2>
                    </div>
                    <div>
                        <span class="badge-neon-blue" id="page-step-4-badge">
                            <i class="fas fa-users-slash me-1"></i> ผู้ป่วยซ้อนทับ 0% (Zero Leakage)
                        </span>
                    </div>
                </div>"""

if s4_old in content:
    content = content.replace(s4_old, s4_new, 1)
    print('Step 4 header replaced successfully')
else:
    print('WARNING: s4_old not found')

# 6. STEP 5 HEADER REPLACEMENT
s5_old = """<section id="page-step-5" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-coral mb-1">ระยะที่ 5 (Phase 5)</span>
                        <h2 class="fw-bold mb-0 text-dark">🩺 ประวัติผู้ป่วยรายยาว &amp; ตัวจำลองการประเมินความเสี่ยงคลินิก</h2>
                    </div>
                    <div>
                        <span class="badge-neon-teal">
                            <i class="fas fa-stethoscope me-1"></i> Interactive Patient Simulator
                        </span>
                    </div>
                </div>"""

s5_new = """<section id="page-step-5" class="step-page">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <span class="badge-neon-coral mb-1" id="page-step-5-phase">ระยะที่ 5 (Phase 5)</span>
                        <h2 class="fw-bold mb-0 text-dark" id="page-step-5-title">🩺 ดูประวัติคนไข้ทางยาว &amp; ตัวจำลองความเสี่ยง (Longitudinal CDS & Simulator)</h2>
                    </div>
                    <div>
                        <span class="badge-neon-teal" id="page-step-5-badge">
                            <i class="fas fa-stethoscope me-1"></i> Interactive Patient Simulator
                        </span>
                    </div>
                </div>"""

if s5_old in content:
    content = content.replace(s5_old, s5_new, 1)
    print('Step 5 header replaced successfully')
else:
    print('WARNING: s5_old not found')

# 7. ADD IDS TO THE 8 EDA STEP CARDS (3.1 - 3.8)
eda_card_reps = [
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.1</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-boxes-stacked text-purple me-1"></i> การสำรวจมิติและโครงสร้างคลังข้อมูลฟีเจอร์ (Data Dimension & Feature Inventory Audit)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-31">ขั้นตอนที่ 3.1</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-31"><i class="fas fa-boxes-stacked text-purple me-1"></i> ขนาดของข้อมูลและคลังฟีเจอร์ EKG (Data Dimensions & Feature Inventory)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.2</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-chart-column text-primary me-1"></i> การแจกแจงตัวแปรเดี่ยวและความไม่สมดุลของคลาสเป้าหมาย (Univariate Distribution & Class Imbalance)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-32">ขั้นตอนที่ 3.2</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-32"><i class="fas fa-chart-column text-primary me-1"></i> การกระจายตัวของตัวแปรเดี่ยวและความไม่สมดุลของโรค (Univariate Distribution & Class Imbalance)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.3</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-filter-circle-xmark text-warning me-1"></i> การตรวจสอบกลไกข้อมูลสูญหายและคุณภาพสัญญาณ (Missingness Mechanism & SQI Audit)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-33">ขั้นตอนที่ 3.3</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-33"><i class="fas fa-filter-circle-xmark text-warning me-1"></i> การตรวจสอบข้อมูลสูญหายและคุณภาพสัญญาณ (Missingness Mechanism & SQI Audit)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.4</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-network-wired text-info me-1"></i> การวิเคราะห์ความสัมพันธ์สองตัวแปรและหลายตัวแปร (Bivariate & Multivariate Association)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-34">ขั้นตอนที่ 3.4</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-34"><i class="fas fa-network-wired text-info me-1"></i> ความสัมพันธ์ระหว่างตัวแปรทางคลินิกและกลุ่มโรค (Bivariate & Multivariate Association)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.5</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-wave-square text-teal me-1"></i> การวิเคราะห์รูปร่างคลื่นอนุกรมเวลาและความหนาแน่นสเปกตรัม (Time-Series Waveform & Welch PSD)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-35">ขั้นตอนที่ 3.5</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-35"><i class="fas fa-wave-square text-teal me-1"></i> สัญญาณคลื่น EKG ตามเวลาและสเปกตรัมความถี่ (Time-Series Waveform & Welch PSD)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.6</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-triangle-exclamation text-danger me-1"></i> การตรวจจับค่าผิดปกติและกฎความปลอดภัยทางคลินิก (Clinical Anomaly & Safety Rules)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-36">ขั้นตอนที่ 3.6</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-36"><i class="fas fa-triangle-exclamation text-danger me-1"></i> การตรวจจับค่าผิดปกติและกฎความปลอดภัยทางคลินิก (Clinical Anomaly & Safety Rules)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.7</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-clock-rotate-left text-primary me-1"></i> พลวัตการตรวจซ้ำและมิติทางยาวของผู้ป่วย (Longitudinal Encounter Dynamics)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-37">ขั้นตอนที่ 3.7</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-37"><i class="fas fa-clock-rotate-left text-primary me-1"></i> พฤติกรรมการตรวจซ้ำและมิติทางยาวของคนไข้ (Longitudinal Dynamics & Repeat Encounters)</span>'
    ),
    (
        '<span class="eda-badge-step">ขั้นตอนที่ 3.8</span>\n                            <span class="fw-bold fs-6 text-dark"><i class="fas fa-shield-halved text-success me-1"></i> ประตูกั้นตรวจสอบความพร้อมก่อนเทรนแบบจำลอง (Pre-Modeling Readiness Gate & Leakage Audit)</span>',
        '<span class="eda-badge-step" id="eda-step-badge-38">ขั้นตอนที่ 3.8</span>\n                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-38"><i class="fas fa-shield-halved text-success me-1"></i> ประตูกั้นตรวจสอบความพร้อมก่อนเทรนโมเดล (Pre-Modeling Readiness Gate & Leakage Audit)</span>'
    )
]

for old_str, new_str in eda_card_reps:
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        print('Replaced EDA step card header')
    else:
        print('WARNING: EDA step card header not matched exactly!')

# 8. JAVASCRIPT BILINGUAL LOGIC INJECTION
js_anchor = 'document.addEventListener("DOMContentLoaded", function() {'
p_js = content.find(js_anchor)
if p_js == -1:
    print('ERROR: DOMContentLoaded not found')
    sys.exit(1)

js_bilingual = """
        // --------------------------------------------------------
        // BILINGUAL LANGUAGE SYSTEM (TH / EN)
        // --------------------------------------------------------
        let currentLang = localStorage.getItem('ekg_platform_lang') || 'th';

        const I18N_DICT = {
            th: {
                'nav-app-subtitle': 'ระบบวิเคราะห์และติดตามคลื่นไฟฟ้าหัวใจ 12 ลีด (Clinical AI & CDS)',
                'btn-toggle-sidebar-text': '☰ ย่อ/ขยายเมนู',
                'nb-stat-records': '<i class="fas fa-database me-1"></i> 21,246 บันทึก EKG (18,499 คนไข้จริง)',
                'nb-stat-leakage': '<i class="fas fa-shield-check me-1"></i> GroupKFold ป้องกันข้อมูลรั่วไหล ✅',
                'nb-stat-hipaa': '<i class="fas fa-lock me-1"></i> ได้มาตรฐาน HIPAA/PDPA ✅',
                
                'sidebar-main-heading': 'ขั้นตอนการวิเคราะห์ (Pipeline Steps)',
                'sidebar-step1-btn': '<i class="fas fa-database text-primary icon-prefix me-2"></i> 1. ข้อมูลตั้งต้น & ที่มา 🏛️',
                'sidebar-step2-btn': '<i class="fas fa-wave-square text-info icon-prefix me-2"></i> 2. ล้างสัญญาณ EKG & DSP 🌊',
                'sidebar-step3-btn': '<i class="fas fa-chart-line text-warning icon-prefix me-2"></i> 3. สำรวจข้อมูล (EDA) 🔬',
                'sidebar-step4-btn': '<i class="fas fa-trophy text-success icon-prefix me-2"></i> 4. เปรียบเทียบโมเดล AI 🏆',
                'sidebar-step5-btn': '<i class="fas fa-user-injured text-danger icon-prefix me-2"></i> 5. ดูประวัติคนไข้ & CDS 🩺',

                'sub-grain-arch': 'ระดับข้อมูลคนไข้และการตรวจ',
                'sub-multi-visit': 'การกระจายจำนวนครั้งที่ตรวจ',
                'sub-attrition': 'ขั้นตอนคัดกรองข้อมูล (Attrition)',
                'sub-data-dict': 'พจนานุกรมข้อมูล (Data Dictionary)',
                'sub-missing-inv': 'ข้อมูลสูญหาย (MCAR/MAR/MNAR)',
                'sub-provenance': 'ความถูกต้องของไฟล์ (SHA-256)',

                'sub-dsp-pipe': 'ขั้นตอนการกรองสัญญาณ DSP',
                'sub-dual-wave': 'เปรียบเทียบคลื่นก่อน-หลังล้าง',
                'sub-sqi-heat': 'แผนภาพคุณภาพสัญญาณ (SQI)',
                'sub-quarantine': 'สัญญาณที่ตัดออกเพราะสัญญาณรบกวน',

                'sub-eda-31': '3.1 ขนาดข้อมูลและคลังฟีเจอร์ (Data Dimensions)',
                'sub-eda-32': '3.2 การกระจายตัวของข้อมูล (Univariate)',
                'sub-eda-33': '3.3 ข้อมูลสูญหายและคุณภาพ (Missingness & SQI)',
                'sub-eda-34': '3.4 ความสัมพันธ์ระหว่างตัวแปรและโรค (Multivariate)',
                'sub-eda-35': '3.5 คลื่นสัญญาณและความถี่สเปกตรัม (Waveform & PSD)',
                'sub-eda-36': '3.6 ตรวจจับค่าผิดปกติทางการแพทย์ (Outliers)',
                'sub-eda-37': '3.7 คนไข้ที่มาตรวจซ้ำหลายครั้ง (Longitudinal)',
                'sub-eda-38': '3.8 ตรวจสอบความพร้อมก่อนเทรนโมเดล (Readiness Gate)',

                'sub-tab-b': 'ตาราง ข: โมเดล Supervised ML',
                'sub-tab-c': 'ตาราง ค: Deep Learning 1D Waveforms',
                'sub-tab-a': 'ตาราง ก: Unsupervised & Anomaly',
                'sub-tab-d': 'ตาราง ง: สรุปผลด้วย Clinical LLM',
                'sub-groupkfold': 'การแบ่งข้อมูลคนไข้ (GroupKFold)',
                'sub-conf-matrix': 'Confusion Matrix แยก 5 กลุ่มโรค',
                'sub-roc-curves': 'เส้นโค้ง ROC-AUC 5 กลุ่มโรค',
                'sub-feature-gain': '15 ฟีเจอร์สำคัญที่สุด (Gain)',

                'sub-exec-kpis': 'ตัวชี้วัดสำคัญระดับผู้บริหาร (4 KPIs)',
                'sub-pat-timeline': 'ค้นหาคนไข้และไทม์ไลน์ (Level 1)',
                'sub-instant-diag': 'สรุปผลการวินิจฉัยโรคหัวใจทันที (Level 2)',
                'sub-det-metrics': 'ค่าสรีรวิทยาคลินิกโดยละเอียด',
                'sub-12lead-xai': 'คลื่น 12 ลีด & ไฮไลต์ AI (XAI)',
                'sub-llm-narrative': 'บันทึกสรุปผลทางการแพทย์ (Clinical LLM)',
                'sub-local-shap': 'ปัจจัยที่มีผลต่อการทำนาย (SHAP)',
                'sub-whatif-sim': 'ตัวจำลองความเสี่ยง What-If (Level 3)',

                'sidebar-disclaimer-title': '<i class="fas fa-shield-halved me-1 text-primary"></i> ขอบเขตการใช้งานทางคลินิก',
                'sidebar-disclaimer-body': 'ระบบนี้ออกแบบขึ้นเพื่อเป็น<strong>เครื่องมือช่วยแพทย์ตัดสินใจ (CDS)</strong> เพื่อคัดกรองเบื้องต้น ไม่สามารถทดแทนการวินิจฉัยยืนยันโดยแพทย์อายุรศาสตร์โรคหัวใจได้',

                'stepper-header-badge': '<i class="fas fa-project-diagram me-1"></i> PIPELINE ROADMAP',
                'stepper-header-title': 'ขั้นตอนการทำงานและพัฒนาแบบจำลอง EKG ตั้งแต่ต้นจนจบ (Clinical ML/DL Workflow)',
                'stepper-badge-audit': '<i class="fas fa-check-circle me-1"></i> มาตรฐานการวิเคราะห์ 5 เฟส',
                'stepper-badge-nav': '<i class="fas fa-sliders me-1"></i> คลิกเลือกดูแต่ละเฟสได้ทันที',

                'stepper-b1-phase': 'เฟส 1',
                'stepper-b1-title': '1. ข้อมูลตั้งต้น & ที่มา',
                'stepper-b1-sub': 'Grain & Provenance',

                'stepper-b2-phase': 'เฟส 2',
                'stepper-b2-title': '2. ล้างสัญญาณ EKG',
                'stepper-b2-sub': 'DSP กรองคลื่น & คุณภาพ',

                'stepper-b3-phase': 'เฟส 3',
                'stepper-b3-title': '3. สำรวจข้อมูล (EDA)',
                'stepper-b3-sub': '8 ขั้นตอนวิเคราะห์ละเอียด',

                'stepper-b4-phase': 'เฟส 4',
                'stepper-b4-title': '4. เปรียบเทียบโมเดล AI',
                'stepper-b4-sub': 'ML, DL & 1D-CNN',

                'stepper-b5-phase': 'เฟส 5',
                'stepper-b5-title': '5. ประวัติคนไข้ & CDS',
                'stepper-b5-sub': 'ติดตามอาการ & จำลองผล',

                'page-step-1-phase': 'ระยะที่ 1 (Phase 1)',
                'page-step-1-title': '🏛️ ข้อมูลตั้งต้น & ที่มาของข้อมูล (Data Foundation & Grain)',
                'page-step-1-badge': '<i class="fas fa-database me-1"></i> หน่วยการวิเคราะห์: บันทึก EKG 10 วินาที (ecg_id)',

                'page-step-2-phase': 'ระยะที่ 2 (Phase 2)',
                'page-step-2-title': '🌊 ล้างสัญญาณคลื่นไฟฟ้า & ตรวจสอบคุณภาพ DSP (DSP Cleaning & Signal QC)',
                'page-step-2-badge': '<i class="fas fa-microchip me-1"></i> Butterworth 0.5–45Hz + 50Hz Notch Filter',

                'page-step-3-phase': '<i class="fas fa-flask me-1"></i> ระยะที่ 3 (Phase 3)',
                'page-step-3-badge-std': '<i class="fas fa-list-check me-1"></i> วิเคราะห์ละเอียด 8 ขั้นตอนตามมาตรฐาน EDA',
                'page-step-3-title': '🔬 สำรวจข้อมูลเชิงลึก 8 ขั้นตอน (EDA) & สกัดฟีเจอร์ EKG',
                'page-step-3-subtitle': 'สำรวจข้อมูล EKG อย่างเป็นระบบตามลำดับขั้นตอน พร้อมสกัดฟีเจอร์คลื่นไฟฟ้าหัวใจ 63 ตัวแปร',

                'eda-pill-31': '<span class="badge bg-purple text-white">3.1</span> ขนาดและมิติข้อมูล',
                'eda-pill-32': '<span class="badge bg-purple text-white">3.2</span> ตัวแปรเดี่ยว & สมดุลโรค',
                'eda-pill-33': '<span class="badge bg-purple text-white">3.3</span> ข้อมูลสูญหาย & คุณภาพ',
                'eda-pill-34': '<span class="badge bg-purple text-white">3.4</span> สหสัมพันธ์ตัวแปร & โรค',
                'eda-pill-35': '<span class="badge bg-purple text-white">3.5</span> คลื่นสัญญาณ & สเปกตรัม',
                'eda-pill-36': '<span class="badge bg-purple text-white">3.6</span> ตรวจจับค่าผิดปกติ',
                'eda-pill-37': '<span class="badge bg-purple text-white">3.7</span> คนไข้ที่ตรวจซ้ำ',
                'eda-pill-38': '<span class="badge bg-purple text-white">3.8</span> เช็กความพร้อมเทรนโมเดล',

                'eda-step-badge-31': 'ขั้นตอนที่ 3.1',
                'eda-step-title-31': '<i class="fas fa-boxes-stacked text-purple me-1"></i> ขนาดของข้อมูลและคลังฟีเจอร์ EKG (Data Dimensions & Feature Inventory)',
                'eda-step-badge-32': 'ขั้นตอนที่ 3.2',
                'eda-step-title-32': '<i class="fas fa-chart-column text-primary me-1"></i> การกระจายตัวของตัวแปรเดี่ยวและความไม่สมดุลของโรค (Univariate Distribution & Class Imbalance)',
                'eda-step-badge-33': 'ขั้นตอนที่ 3.3',
                'eda-step-title-33': '<i class="fas fa-filter-circle-xmark text-warning me-1"></i> การตรวจสอบข้อมูลสูญหายและคุณภาพสัญญาณ (Missingness Mechanism & SQI Audit)',
                'eda-step-badge-34': 'ขั้นตอนที่ 3.4',
                'eda-step-title-34': '<i class="fas fa-network-wired text-info me-1"></i> ความสัมพันธ์ระหว่างตัวแปรทางคลินิกและกลุ่มโรค (Bivariate & Multivariate Association)',
                'eda-step-badge-35': 'ขั้นตอนที่ 3.5',
                'eda-step-title-35': '<i class="fas fa-wave-square text-teal me-1"></i> สัญญาณคลื่น EKG ตามเวลาและสเปกตรัมความถี่ (Time-Series Waveform & Welch PSD)',
                'eda-step-badge-36': 'ขั้นตอนที่ 3.6',
                'eda-step-title-36': '<i class="fas fa-triangle-exclamation text-danger me-1"></i> การตรวจจับค่าผิดปกติและกฎความปลอดภัยทางคลินิก (Clinical Anomaly & Safety Rules)',
                'eda-step-badge-37': 'ขั้นตอนที่ 3.7',
                'eda-step-title-37': '<i class="fas fa-clock-rotate-left text-primary me-1"></i> พฤติกรรมการตรวจซ้ำและมิติทางยาวของคนไข้ (Longitudinal Dynamics & Repeat Encounters)',
                'eda-step-badge-38': 'ขั้นตอนที่ 3.8',
                'eda-step-title-38': '<i class="fas fa-shield-halved text-success me-1"></i> ประตูกั้นตรวจสอบความพร้อมก่อนเทรนโมเดล (Pre-Modeling Readiness Gate & Leakage Audit)',

                'page-step-4-phase': 'ระยะที่ 4 (Phase 4)',
                'page-step-4-title': '🏆 เปรียบเทียบประสิทธิภาพโมเดล AI (ML & Deep Learning Leaderboard)',
                'page-step-4-badge': '<i class="fas fa-users-slash me-1"></i> ผู้ป่วยซ้อนทับ 0% (Zero Leakage)',

                'page-step-5-phase': 'ระยะที่ 5 (Phase 5)',
                'page-step-5-title': '🩺 ดูประวัติคนไข้ทางยาว &amp; ตัวจำลองความเสี่ยง (Longitudinal CDS & Simulator)',
                'page-step-5-badge': '<i class="fas fa-stethoscope me-1"></i> Interactive Patient Simulator'
            },
            en: {
                'nav-app-subtitle': '12-Lead Longitudinal ECG Intelligence & Clinical Decision Support (CDS)',
                'btn-toggle-sidebar-text': '☰ Toggle Menu',
                'nb-stat-records': '<i class="fas fa-database me-1"></i> 21,246 ECG Records (18,499 Patients)',
                'nb-stat-leakage': '<i class="fas fa-shield-check me-1"></i> GroupKFold Zero-Leakage ✅',
                'nb-stat-hipaa': '<i class="fas fa-lock me-1"></i> HIPAA/PDPA Compliant ✅',
                
                'sidebar-main-heading': 'Pipeline Steps',
                'sidebar-step1-btn': '<i class="fas fa-database text-primary icon-prefix me-2"></i> 1. Data Foundation 🏛️',
                'sidebar-step2-btn': '<i class="fas fa-wave-square text-info icon-prefix me-2"></i> 2. DSP Cleaning & QC 🌊',
                'sidebar-step3-btn': '<i class="fas fa-chart-line text-warning icon-prefix me-2"></i> 3. In-Depth EDA & Features 🔬',
                'sidebar-step4-btn': '<i class="fas fa-trophy text-success icon-prefix me-2"></i> 4. Model Leaderboard 🏆',
                'sidebar-step5-btn': '<i class="fas fa-user-injured text-danger icon-prefix me-2"></i> 5. Patient CDS & Simulator 🩺',

                'sub-grain-arch': 'Data Grain & Hierarchy',
                'sub-multi-visit': 'Visit Frequency Distribution',
                'sub-attrition': 'Attrition Funnel Cohort',
                'sub-data-dict': 'Clinical Data Dictionary',
                'sub-missing-inv': 'Missingness Audit (Rubin)',
                'sub-provenance': 'Data Integrity (SHA-256)',

                'sub-dsp-pipe': 'Digital Signal Processing Pipeline',
                'sub-dual-wave': 'Raw vs Filtered Waveforms',
                'sub-sqi-heat': 'Signal Quality Index (SQI)',
                'sub-quarantine': 'Quarantine Noise Registry',

                'sub-eda-31': '3.1 Dimensions & Feature Inventory',
                'sub-eda-32': '3.2 Univariate Distribution & Balance',
                'sub-eda-33': '3.3 Missingness & Signal Quality',
                'sub-eda-34': '3.4 Multivariate & Disease Correlation',
                'sub-eda-35': '3.5 Time-Series Waveform & PSD',
                'sub-eda-36': '3.6 Clinical Anomaly & Outliers',
                'sub-eda-37': '3.7 Longitudinal Dynamics (Repeat Visits)',
                'sub-eda-38': '3.8 Pre-Modeling Readiness Gate',

                'sub-tab-b': 'Table B: Supervised ML Leaderboard',
                'sub-tab-c': 'Table C: Deep Learning 1D Waveforms',
                'sub-tab-a': 'Table A: Unsupervised & Anomaly',
                'sub-tab-d': 'Table D: Clinical LLM Agent Layer',
                'sub-groupkfold': 'GroupKFold Patient Splitting Scheme',
                'sub-conf-matrix': 'Normalized Confusion Matrix',
                'sub-roc-curves': 'Multi-Class ROC-AUC Curves',
                'sub-feature-gain': 'Top 15 Feature Importance (Gain)',

                'sub-exec-kpis': 'Executive Summary KPIs',
                'sub-pat-timeline': 'Patient Search & Trajectory (Level 1)',
                'sub-instant-diag': 'Instant Dual Diagnosis (Level 2)',
                'sub-det-metrics': 'Detailed Clinical Electrophysiology',
                'sub-12lead-xai': '12-Lead ECG & AI Attention (XAI)',
                'sub-llm-narrative': 'Clinical LLM Narrative Report',
                'sub-local-shap': 'Local Feature Attribution (SHAP)',
                'sub-whatif-sim': 'What-If Risk Simulator (Level 3)',

                'sidebar-disclaimer-title': '<i class="fas fa-shield-halved me-1 text-primary"></i> Clinical Scope',
                'sidebar-disclaimer-body': 'This platform is engineered as a <strong>Clinical Decision Support (CDS)</strong> screening aid and does not substitute for formal clinical diagnosis by board-certified cardiologists.',

                'stepper-header-badge': '<i class="fas fa-project-diagram me-1"></i> PIPELINE ROADMAP',
                'stepper-header-title': 'End-to-End Longitudinal ECG Machine Learning & Deep Learning Pipeline',
                'stepper-badge-audit': '<i class="fas fa-check-circle me-1"></i> Audit-Ready 5-Phase Standard',
                'stepper-badge-nav': '<i class="fas fa-sliders me-1"></i> Click any phase to navigate',

                'stepper-b1-phase': 'Phase 1',
                'stepper-b1-title': '1. Data Foundation',
                'stepper-b1-sub': 'Grain & Provenance',

                'stepper-b2-phase': 'Phase 2',
                'stepper-b2-title': '2. DSP Cleaning',
                'stepper-b2-sub': 'Filter, SQI & QC',

                'stepper-b3-phase': 'Phase 3',
                'stepper-b3-title': '3. In-Depth EDA',
                'stepper-b3-sub': '8-Step Biomedical EDA',

                'stepper-b4-phase': 'Phase 4',
                'stepper-b4-title': '4. Model Benchmarks',
                'stepper-b4-sub': 'ML, DL & 1D-CNN',

                'stepper-b5-phase': 'Phase 5',
                'stepper-b5-title': '5. Patient CDS & Sim',
                'stepper-b5-sub': 'Trajectory & XAI Sim',

                'page-step-1-phase': 'Phase 1',
                'page-step-1-title': '🏛️ Data Foundation & Granular Architecture',
                'page-step-1-badge': '<i class="fas fa-database me-1"></i> Unit of Analysis: 10s ECG Record (ecg_id)',

                'page-step-2-phase': 'Phase 2',
                'page-step-2-title': '🌊 Signal Preprocessing, DSP Filtering & Quality Control',
                'page-step-2-badge': '<i class="fas fa-microchip me-1"></i> Butterworth 0.5–45Hz + 50Hz Notch Filter',

                'page-step-3-phase': '<i class="fas fa-flask me-1"></i> Phase 3',
                'page-step-3-badge-std': '<i class="fas fa-list-check me-1"></i> In-Depth 8-Step Biomedical EDA Standard',
                'page-step-3-title': '🔬 In-Depth 8-Step Biomedical EDA & Feature Engineering',
                'page-step-3-subtitle': 'Systematic Exploratory Data Analysis & 63-Feature Extraction Pipeline',

                'eda-pill-31': '<span class="badge bg-purple text-white">3.1</span> Dimensions & Features',
                'eda-pill-32': '<span class="badge bg-purple text-white">3.2</span> Univariate & Balance',
                'eda-pill-33': '<span class="badge bg-purple text-white">3.3</span> Missingness & SQI',
                'eda-pill-34': '<span class="badge bg-purple text-white">3.4</span> Correlation & Disease',
                'eda-pill-35': '<span class="badge bg-purple text-white">3.5</span> Waveform & PSD',
                'eda-pill-36': '<span class="badge bg-purple text-white">3.6</span> Clinical Outliers',
                'eda-pill-37': '<span class="badge bg-purple text-white">3.7</span> Repeat Visits',
                'eda-pill-38': '<span class="badge bg-purple text-white">3.8</span> Modeling Readiness Gate',

                'eda-step-badge-31': 'Step 3.1',
                'eda-step-title-31': '<i class="fas fa-boxes-stacked text-purple me-1"></i> Data Dimensions & Biomedical Feature Inventory Audit',
                'eda-step-badge-32': 'Step 3.2',
                'eda-step-title-32': '<i class="fas fa-chart-column text-primary me-1"></i> Univariate Distribution & Diagnostic Class Imbalance Analysis',
                'eda-step-badge-33': 'Step 3.3',
                'eda-step-title-33': '<i class="fas fa-filter-circle-xmark text-warning me-1"></i> Missingness Mechanism (Rubin\'s Framework) & Signal Quality Audit',
                'eda-step-badge-34': 'Step 3.4',
                'eda-step-title-34': '<i class="fas fa-network-wired text-info me-1"></i> Bivariate & Multivariate Electrophysiological Association Matrix',
                'eda-step-badge-35': 'Step 3.5',
                'eda-step-title-35': '<i class="fas fa-wave-square text-teal me-1"></i> Time-Series Waveform Morphometry & Power Spectral Density (PSD)',
                'eda-step-badge-36': 'Step 3.6',
                'eda-step-title-36': '<i class="fas fa-triangle-exclamation text-danger me-1"></i> Outlier Detection, Clinical Anomaly Registry & Medical Safety Rules',
                'eda-step-badge-37': 'Step 3.7',
                'eda-step-title-37': '<i class="fas fa-clock-rotate-left text-primary me-1"></i> Longitudinal Dynamics & Multi-Encounter Patient Follow-up Timeline',
                'eda-step-badge-38': 'Step 3.8',
                'eda-step-title-38': '<i class="fas fa-shield-halved text-success me-1"></i> Pre-Modeling Readiness Gate & Zero-Leakage Audit Checklist',

                'page-step-4-phase': 'Phase 4',
                'page-step-4-title': '🏆 Hybrid Model Evaluation & Predictive Leaderboard',
                'page-step-4-badge': '<i class="fas fa-users-slash me-1"></i> Zero Leakage Patient Split (0%)',

                'page-step-5-phase': 'Phase 5',
                'page-step-5-title': '🩺 Longitudinal Patient Trajectory & Clinical Risk Simulator',
                'page-step-5-badge': '<i class="fas fa-stethoscope me-1"></i> Interactive Patient Simulator'
            }
        };

        function setLanguage(lang) {
            currentLang = lang || 'th';
            localStorage.setItem('ekg_platform_lang', currentLang);

            // Toggle language buttons
            const btnTh = document.getElementById('btn-lang-th');
            const btnEn = document.getElementById('btn-lang-en');
            if (btnTh && btnEn) {
                if (currentLang === 'th') {
                    btnTh.className = 'btn btn-sm btn-primary py-1 px-3 fw-bold';
                    btnEn.className = 'btn btn-sm btn-outline-secondary py-1 px-3 fw-bold';
                } else {
                    btnTh.className = 'btn btn-sm btn-outline-secondary py-1 px-3 fw-bold';
                    btnEn.className = 'btn btn-sm btn-primary py-1 px-3 fw-bold';
                }
            }

            // Update registered IDs
            const dict = I18N_DICT[currentLang];
            if (dict) {
                for (const [id, val] of Object.entries(dict)) {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerHTML = val;
                    }
                }
            }

            // Update any elements with data-i18n-th / data-i18n-en
            document.querySelectorAll('[data-i18n-th]').forEach(el => {
                const text = el.getAttribute('data-i18n-' + currentLang);
                if (text) {
                    el.innerHTML = text;
                }
            });

            // Update Plotly chart titles if present
            updateChartsLanguage(currentLang);
        }

        function updateChartsLanguage(lang) {
            if (typeof Plotly === 'undefined') return;
            const isTh = (lang === 'th');
            
            const chartTitles = {
                'chart-visit-dist': {
                    th: 'การกระจายจำนวนครั้งที่ตรวจของผู้ป่วย (Encounter Frequency)',
                    en: 'Patient Visit Frequency Distribution (Longitudinal Cohort)'
                },
                'chart-funnel': {
                    th: 'กรวยคัดกรองข้อมูลประชากรศึกษา (Cohort Attrition Funnel)',
                    en: 'Cohort Attrition Funnel Diagram'
                },
                'chart-target-distribution': {
                    th: 'การกระจายตัวของกลุ่มโรคหัวใจ 5 กลุ่มหลัก (Target Imbalance)',
                    en: 'Target Class Distribution (5 Diagnostic Superclasses)'
                },
                'chart-age-sex-distribution': {
                    th: 'การกระจายตัวของอายุตามเพศของผู้ป่วย (Age Distribution by Sex)',
                    en: 'Age Distribution Stratified by Patient Sex'
                },
                'chart-bio-distribution': {
                    th: 'การกระจายตัวของอัตราการเต้นหัวใจและความกว้าง QRS',
                    en: 'Distribution of Clinical Vitals (Heart Rate & QRS Duration)'
                },
                'chart-missing-heatmap': {
                    th: 'การตรวจจับข้อมูลสูญหายและการประเมินคุณภาพสัญญาณ (SQI)',
                    en: 'Missingness Mechanism & Signal Quality (SQI) Audit'
                },
                'chart-corr-heatmap': {
                    th: 'เมทริกซ์สหสัมพันธ์ระหว่างตัวแปรทางคลินิก (Correlation Heatmap)',
                    en: 'Correlation Matrix of Clinical Electrophysiological Features'
                },
                'chart-morphology-box': {
                    th: 'การกระจายตัวของความกว้าง QRS แยกตามกลุ่มโรค (QRS by Disease)',
                    en: 'QRS Duration Distribution Stratified by Diagnostic Class'
                },
                'chart-age-disease-strat': {
                    th: 'อัตราส่วนกลุ่มโรคตามช่วงอายุของผู้ป่วย (Disease by Age Group)',
                    en: 'Diagnostic Class Prevalence Stratified by Age Cohort'
                },
                'chart-biomedical-overlay': {
                    th: 'การตรวจจับคลื่นสัญญาณ EKG Lead II พร้อมตำแหน่ง R-Peak และ ST Segment',
                    en: 'Lead II 10-Second Waveform with Pan-Tompkins R-Peaks & ST Window'
                },
                'chart-welch-psd': {
                    th: 'การวิเคราะห์ความหนาแน่นสเปกตรัมกำลังไฟฟ้า (Welch PSD Spectrum)',
                    en: 'Power Spectral Density (PSD) Analysis using Welch Method'
                },
                'chart-outlier-box': {
                    th: 'การกระจายตัวและค่าผิดปกติของตัวแปรทางคลินิก (Tukey IQR Boxplots)',
                    en: 'Outlier Detection & Distribution Spread (Tukey IQR Method)'
                },
                'chart-eda-visit-dist': {
                    th: 'การกระจายของระยะเวลาและจำนวนครั้งที่ตรวจซ้ำ (Repeat Visits)',
                    en: 'Encounter Frequency Distribution for Longitudinal Cohort'
                },
                'chart-confusion-matrix': {
                    th: 'Normalized Confusion Matrix (1D-CNN + ResNet Hybrid)',
                    en: 'Normalized Confusion Matrix (1D-CNN + ResNet Hybrid)'
                },
                'chart-roc-curves': {
                    th: 'Multi-Class ROC-AUC Curves (One-vs-Rest)',
                    en: 'Multi-Class ROC-AUC Curves (One-vs-Rest)'
                },
                'chart-feature-importance': {
                    th: '15 ฟีเจอร์ที่มีผลต่อการทำนายมากที่สุด (Feature Importance Gain)',
                    en: 'Top 15 Biomedical Feature Importance by Split Gain'
                }
            };

            for (const [id, titles] of Object.entries(chartTitles)) {
                const el = document.getElementById(id);
                if (el && el.data) {
                    try {
                        Plotly.relayout(id, { 'title.text': isTh ? titles.th : titles.en });
                    } catch(e) {}
                }
            }
        }
"""

# Insert JS bilingual logic before DOMContentLoaded
content = content[:p_js] + js_bilingual + "\n        " + content[p_js:]

# Also ensure setLanguage(currentLang) is called in DOMContentLoaded
dom_old = """            initStep1();
            initStep2();
            initStep3();
            initStep4();
            initStep5();"""

dom_new = """            initStep1();
            initStep2();
            initStep3();
            initStep4();
            initStep5();

            // Initialize UI language
            setLanguage(currentLang);"""

if dom_old in content:
    content = content.replace(dom_old, dom_new, 1)
    print('DOMContentLoaded updated to call setLanguage')
else:
    print('WARNING: dom_old not found')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated successfully! Final content length:', len(content))
