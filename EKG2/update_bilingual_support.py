# update_bilingual_support.py
"""
Script to add bilingual language switching (Thai & English) to ekg_longitudinal_dashboard.html
with natural, friendly, non-overly-formal Thai ('ภาษาไทยปกติ ไม่ต้องเป็นทางการ').
"""

import re

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# -----------------------------------------------------------------------------
# 1. UPDATE NAVBAR TO ADD BILINGUAL BUTTONS & NATURAL THAI
# -----------------------------------------------------------------------------
p_nav_start = content.find('<header class="top-navbar">')
p_nav_end = content.find('</header>', p_nav_start) + len('</header>')

old_navbar = content[p_nav_start:p_nav_end]

new_navbar = """    <!-- TOP FIXED NAVBAR WITH BILINGUAL TOGGLE -->
    <header class="top-navbar">
        <div class="d-flex align-items-center justify-content-between w-100">
            <div class="d-flex align-items-center">
                <button class="btn btn-sm btn-outline-primary me-3 font-code d-flex align-items-center gap-2" id="btn-toggle-sidebar" onclick="toggleSidebar()" title="ย่อ/ขยายเมนู (Toggle Menu)">
                    <i class="fas fa-bars"></i>
                    <span data-i18n="btn_toggle_menu"> เมนู</span>
                </button>
                <span class="fs-4 me-2">⚡</span>
                <div>
                    <h5 class="mb-0 fw-bold text-dark font-code" data-i18n="navbar_app_title">PTB-XL ECG Intelligence Platform</h5>
                    <span class="text-muted" style="font-size: 0.72rem;" data-i18n="navbar_app_subtitle">ระบบติดตามและวิเคราะห์คลื่นหัวใจ 12 ลีด ช่วยประเมินอาการคนไข้ (Clinical CDS)</span>
                </div>
            </div>
            <div class="d-flex align-items-center gap-2">
                <span class="badge-neon-blue font-code d-none d-lg-inline-block" data-i18n="navbar_badge_records"><i class="fas fa-database me-1"></i> 21,246 บันทึก EKG (18,499 คนไข้จริง)</span>
                <span class="badge-neon-green font-code d-none d-md-inline-block" data-i18n="navbar_badge_leakage"><i class="fas fa-shield-check me-1"></i> แยกคนไข้เด็ดขาด (Zero Leakage) ✅</span>
                <span class="badge-neon-teal font-code d-none d-xl-inline-block" data-i18n="navbar_badge_hipaa"><i class="fas fa-lock me-1"></i> ปลอดภัยตามเกณฑ์ HIPAA/PDPA ✅</span>
                
                <!-- BILINGUAL LANGUAGE SWITCHER -->
                <div class="btn-group font-code shadow-sm ms-2" role="group" aria-label="Language Selector">
                    <button type="button" class="btn btn-sm btn-primary py-1 px-2 fw-bold" id="btn-lang-th" onclick="setLanguage('th')" title="ภาษาไทยแบบเข้าใจง่าย (ไม่ทางการ)">
                        🇹🇭 TH
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2 fw-bold" id="btn-lang-en" onclick="setLanguage('en')" title="Switch to English">
                        🇬🇧 EN
                    </button>
                </div>
            </div>
        </div>
    </header>"""

content = content[:p_nav_start] + new_navbar + content[p_nav_end:]
print("1. Updated Navbar with Bilingual Switcher successfully!")

# -----------------------------------------------------------------------------
# 2. UPDATE SIDEBAR WITH data-i18n AND NATURAL THAI
# -----------------------------------------------------------------------------
p_side_start = content.find('<nav class="sidebar">')
p_side_end = content.find('</nav>', p_side_start) + len('</nav>')

old_sidebar = content[p_side_start:p_side_end]

new_sidebar = """        <nav class="sidebar">
            <div class="sidebar-heading" data-i18n="sidebar_heading">ขั้นตอนการทำงาน (Pipeline Steps)</div>

            <!-- STEP 1 -->
            <div class="nav-step-item">
                <button class="nav-step-btn active" id="btn-step-1" onclick="showPage('step-1')">
                    <span><i class="fas fa-database text-primary icon-prefix me-2"></i> <span data-i18n="sidebar_step_1">1. ข้อมูลเบื้องต้น & จัดการข้อมูล 🏛️</span></span>
                    <i class="fas fa-chevron-down text-muted small chevron-icon" id="chevron-step-1"></i>
                </button>
                <ul class="submenu-list show" id="submenu-step-1">
                    <li><a href="#sec-grain-architecture" class="submenu-link" onclick="jumpSection('step-1', 'sec-grain-architecture', event)" data-i18n="sub_1_grain">โครงสร้างระดับข้อมูลคนไข้</a></li>
                    <li><a href="#sec-multi-visit" class="submenu-link" onclick="jumpSection('step-1', 'sec-multi-visit', event)" data-i18n="sub_1_visit">จำนวนครั้งที่คนไข้มาตรวจ</a></li>
                    <li><a href="#sec-attrition-funnel" class="submenu-link" onclick="jumpSection('step-1', 'sec-attrition-funnel', event)" data-i18n="sub_1_funnel">ขั้นตอนคัดกรองข้อมูล</a></li>
                    <li><a href="#sec-data-dict" class="submenu-link" onclick="jumpSection('step-1', 'sec-data-dict', event)" data-i18n="sub_1_dict">ความหมายตัวแปรและข้อมูล</a></li>
                    <li><a href="#sec-missing-inv" class="submenu-link" onclick="jumpSection('step-1', 'sec-missing-inv', event)" data-i18n="sub_1_missing">รายการข้อมูลที่ขาดหาย</a></li>
                    <li><a href="#sec-provenance" class="submenu-link" onclick="jumpSection('step-1', 'sec-provenance', event)" data-i18n="sub_1_prov">ที่มาและความถูกต้องข้อมูล</a></li>
                </ul>
            </div>

            <!-- STEP 2 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-2" onclick="showPage('step-2')">
                    <span><i class="fas fa-wave-square text-info icon-prefix me-2"></i> <span data-i18n="sidebar_step_2">2. ล้างคลื่น EKG & คุณภาพ 🌊</span></span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-2"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-2">
                    <li><a href="#sec-dsp-pipeline" class="submenu-link" onclick="jumpSection('step-2', 'sec-dsp-pipeline', event)" data-i18n="sub_2_filter">ขั้นตอนกรองสัญญาณ Noise</a></li>
                    <li><a href="#sec-dual-waveform" class="submenu-link" onclick="jumpSection('step-2', 'sec-dual-waveform', event)" data-i18n="sub_2_compare">เทียบคลื่นก่อน-หลังล้าง</a></li>
                    <li><a href="#sec-sqi-heatmap" class="submenu-link" onclick="jumpSection('step-2', 'sec-sqi-heatmap', event)" data-i18n="sub_2_sqi">คะแนนคุณภาพสัญญาณ (SQI)</a></li>
                    <li><a href="#sec-quarantine-table" class="submenu-link" onclick="jumpSection('step-2', 'sec-quarantine-table', event)" data-i18n="sub_2_quarantine">คลื่นสัญญาณรบกวนที่คัดออก</a></li>
                </ul>
            </div>

            <!-- STEP 3 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-3" onclick="showPage('step-3')">
                    <span><i class="fas fa-chart-line text-warning icon-prefix me-2"></i> <span data-i18n="sidebar_step_3">3. สำรวจข้อมูล EDA (8 ขั้น) 🔬</span></span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-3"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-3">
                    <li><a href="#sec-eda-31" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-31', event)" data-i18n="sub_3_1">3.1 มิติและคลังฟีเจอร์</a></li>
                    <li><a href="#sec-eda-32" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-32', event)" data-i18n="sub_3_2">3.2 กราฟตัวแปรเดี่ยว</a></li>
                    <li><a href="#sec-eda-33" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-33', event)" data-i18n="sub_3_3">3.3 ข้อมูลสูญหายและคุณภาพ</a></li>
                    <li><a href="#sec-eda-34" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-34', event)" data-i18n="sub_3_4">3.4 ความสัมพันธ์และแบ่งตามโรค</a></li>
                    <li><a href="#sec-eda-35" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-35', event)" data-i18n="sub_3_5">3.5 รูปคลื่นจริงและสเปกตรัม</a></li>
                    <li><a href="#sec-eda-36" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-36', event)" data-i18n="sub_3_6">3.6 ตรวจจับค่าผิดปกติ</a></li>
                    <li><a href="#sec-eda-37" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-37', event)" data-i18n="sub_3_7">3.7 คนไข้ที่มาตรวจซ้ำ</a></li>
                    <li><a href="#sec-eda-38" class="submenu-link" onclick="jumpSection('step-3', 'sec-eda-38', event)" data-i18n="sub_3_8">3.8 ตรวจสอบข้อมูลรั่วไหล</a></li>
                </ul>
            </div>

            <!-- STEP 4 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-4" onclick="showPage('step-4')">
                    <span><i class="fas fa-trophy text-success icon-prefix me-2"></i> <span data-i18n="sidebar_step_4">4. เปรียบเทียบโมเดล AI 🏆</span></span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-4"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-4">
                    <li><a href="#sec-table-b" class="submenu-link" onclick="jumpSection('step-4', 'sec-table-b', event)" data-i18n="sub_4_tab_b">ตาราง ข: โมเดล Machine Learning</a></li>
                    <li><a href="#sec-table-c" class="submenu-link" onclick="jumpSection('step-4', 'sec-table-c', event)" data-i18n="sub_4_tab_c">ตาราง ค: Deep Learning (1D-CNN)</a></li>
                    <li><a href="#sec-table-a" class="submenu-link" onclick="jumpSection('step-4', 'sec-table-a', event)" data-i18n="sub_4_tab_a">ตาราง ก: ตรวจจับสิ่งผิดปกติ</a></li>
                    <li><a href="#sec-table-d" class="submenu-link" onclick="jumpSection('step-4', 'sec-table-d', event)" data-i18n="sub_4_tab_d">ตาราง ง: สรุปผลด้วย Clinical LLM</a></li>
                    <li><a href="#sec-groupkfold" class="submenu-link" onclick="jumpSection('step-4', 'sec-groupkfold', event)" data-i18n="sub_4_split">การแบ่งคนไข้ GroupKFold</a></li>
                    <li><a href="#sec-conf-matrix" class="submenu-link" onclick="jumpSection('step-4', 'sec-conf-matrix', event)" data-i18n="sub_4_cm">ตารางความแม่นยำรายโรค</a></li>
                    <li><a href="#sec-roc-curves" class="submenu-link" onclick="jumpSection('step-4', 'sec-roc-curves', event)" data-i18n="sub_4_roc">กราฟ ROC-AUC 5 กลุ่มโรค</a></li>
                    <li><a href="#sec-feature-gain" class="submenu-link" onclick="jumpSection('step-4', 'sec-feature-gain', event)" data-i18n="sub_4_feat">15 ฟีเจอร์ที่สำคัญที่สุด</a></li>
                </ul>
            </div>

            <!-- STEP 5 -->
            <div class="nav-step-item">
                <button class="nav-step-btn" id="btn-step-5" onclick="showPage('step-5')">
                    <span><i class="fas fa-user-injured text-danger icon-prefix me-2"></i> <span data-i18n="sidebar_step_5">5. ประวัติคนไข้ & จำลองผล 🩺</span></span>
                    <i class="fas fa-chevron-right text-muted small chevron-icon" id="chevron-step-5"></i>
                </button>
                <ul class="submenu-list" id="submenu-step-5">
                    <li><a href="#sec-executive-kpis" class="submenu-link" onclick="jumpSection('step-5', 'sec-executive-kpis', event)" data-i18n="sub_5_kpi">สรุปภาพรวมสำคัญ (4 KPIs)</a></li>
                    <li><a href="#sec-patient-timeline" class="submenu-link" onclick="jumpSection('step-5', 'sec-patient-timeline', event)" data-i18n="sub_5_search">ค้นหาและเลือกคนไข้</a></li>
                    <li><a href="#sec-instant-diagnosis" class="submenu-link" onclick="jumpSection('step-5', 'sec-instant-diagnosis', event)" data-i18n="sub_5_diag">ผลวิเคราะห์โรคทันที (2 ข้อ)</a></li>
                    <li><a href="#sec-detailed-metrics" class="submenu-link" onclick="jumpSection('step-5', 'sec-detailed-metrics', event)" data-i18n="sub_5_metrics">ค่าสถิติสรีรวิทยาละเอียด</a></li>
                    <li><a href="#sec-12lead-xai" class="submenu-link" onclick="jumpSection('step-5', 'sec-12lead-xai', event)" data-i18n="sub_5_wave">คลื่น 12 ลีด & จุดที่ AI สนใจ</a></li>
                    <li><a href="#sec-llm-narrative" class="submenu-link" onclick="jumpSection('step-5', 'sec-llm-narrative', event)" data-i18n="sub_5_llm">สรุปความเห็นแพทย์ (AI LLM)</a></li>
                    <li><a href="#sec-local-shap" class="submenu-link" onclick="jumpSection('step-5', 'sec-local-shap', event)" data-i18n="sub_5_shap">เหตุผลการตัดสินใจ (SHAP)</a></li>
                    <li><a href="#sec-what-if-sim" class="submenu-link" onclick="jumpSection('step-5', 'sec-what-if-sim', event)" data-i18n="sub_5_sim">ลองปรับค่าจำลองความเสี่ยง</a></li>
                </ul>
            </div>

            <div class="mt-4 p-3 rounded-4 bg-light border">
                <div class="small fw-bold text-dark mb-1 font-code">
                    <i class="fas fa-shield-halved me-1 text-primary"></i> <span data-i18n="disclaimer_title">ขอบเขตการใช้งานทางคลินิก</span>
                </div>
                <div class="text-muted" style="font-size: 0.76rem; line-height: 1.5;" data-i18n="disclaimer_body">
                    ระบบนี้ทำหน้าที่เป็น<strong>เครื่องมือช่วยคัดกรองเบื้องต้น (Clinical Decision Support)</strong> ไม่สามารถใช้แทนการวินิจฉัยยืนยันโดยแพทย์อายุรศาสตร์หัวใจได้
                </div>
            </div>
        </nav>"""

content = content[:p_side_start] + new_sidebar + content[p_side_end:]
print("2. Updated Sidebar with Natural Thai and data-i18n successfully!")

# -----------------------------------------------------------------------------
# 3. UPDATE PIPELINE STEPPER HEADER WITH data-i18n
# -----------------------------------------------------------------------------
p_step_start = content.find('<div class="card card-custom mb-4 p-3 border-primary-subtle bg-white shadow-sm" id="pipeline-stepper-header">')
p_step_end = content.find('<!-- ============================================================= -->\n            <!-- หน้า 1:', p_step_start)

old_stepper = content[p_step_start:p_step_end]

new_stepper = """<div class="card card-custom mb-4 p-3 border-primary-subtle bg-white shadow-sm" id="pipeline-stepper-header">
                <div class="d-flex flex-wrap align-items-center justify-content-between pb-2 mb-2 border-bottom">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-primary text-white font-code px-2 py-1"><i class="fas fa-project-diagram me-1"></i> <span data-i18n="stepper_badge">PIPELINE ROADMAP</span></span>
                        <span class="fw-bold text-dark font-code" style="font-size: 0.95rem;" data-i18n="stepper_main_title">ขั้นตอนการวิเคราะห์และพัฒนาโมเดล EKG ทั้งหมด (End-to-End Workflow)</span>
                    </div>
                    <div class="d-flex align-items-center gap-2 font-code small text-muted">
                        <span class="badge-neon-green" data-i18n="stepper_badge_audit"><i class="fas fa-check-circle me-1"></i> มาตรฐาน 5 เฟสตรวจสอบได้</span>
                        <span class="badge-neon-blue" data-i18n="stepper_badge_interactive"><i class="fas fa-sliders me-1"></i> คลิกเลือกดูแต่ละขั้นตอนได้ทันที</span>
                    </div>
                </div>
                <div class="row g-2 text-center font-code">
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn active" id="stepper-step-1" onclick="showPage('step-1')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-primary text-white fw-bold" data-i18n="step_1_phase">เฟส 1</span>
                                <i class="fas fa-database text-primary"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" data-i18n="step_1_title">1. ข้อมูลเบื้องต้น</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;" data-i18n="step_1_sub">โครงสร้าง & ที่มาคนไข้</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-2" onclick="showPage('step-2')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-info text-white fw-bold" data-i18n="step_2_phase">เฟส 2</span>
                                <i class="fas fa-wave-square text-info"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" data-i18n="step_2_title">2. ล้างคลื่น EKG</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;" data-i18n="step_2_sub">กรอง Noise & คัดคุณภาพ</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-3" onclick="showPage('step-3')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-warning text-dark fw-bold" data-i18n="step_3_phase">เฟส 3</span>
                                <i class="fas fa-chart-line text-warning"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" data-i18n="step_3_title">3. สำรวจข้อมูล EDA</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;" data-i18n="step_3_sub">8 ขั้นตอนเจาะลึกฟีเจอร์</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-4" onclick="showPage('step-4')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-success text-white fw-bold" data-i18n="step_4_phase">เฟส 4</span>
                                <i class="fas fa-trophy text-success"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" data-i18n="step_4_title">4. เปรียบเทียบโมเดล</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;" data-i18n="step_4_sub">ML, DL & 1D-CNN</div>
                        </button>
                    </div>
                    <div class="col">
                        <button class="btn btn-sm w-100 p-2 rounded-3 text-start stepper-btn" id="stepper-step-5" onclick="showPage('step-5')">
                            <div class="d-flex align-items-center justify-content-between mb-1">
                                <span class="badge bg-danger text-white fw-bold" data-i18n="step_5_phase">เฟส 5</span>
                                <i class="fas fa-user-injured text-danger"></i>
                            </div>
                            <div class="fw-bold text-dark small text-truncate" data-i18n="step_5_title">5. ประวัติคนไข้ & CDS</div>
                            <div class="text-muted text-truncate" style="font-size: 0.70rem;" data-i18n="step_5_sub">ไทม์ไลน์ & ลองจำลองผล</div>
                        </button>
                    </div>
                </div>
            </div>
            """

content = content[:p_step_start] + new_stepper + content[p_step_end:]
print("3. Updated Global Stepper Header with data-i18n successfully!")

# -----------------------------------------------------------------------------
# 4. UPDATE PAGE HEADERS WITH NATURAL THAI AND data-i18n
# -----------------------------------------------------------------------------
# Step 1 Page Header
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🏛️ โครงสร้างธรรมาภิบาลข้อมูล & ลำดับชั้นการบันทึก</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_1_h2">🏛️ ข้อมูลเบื้องต้น & โครงสร้างประวัติคนไข้</h2>'
)

# Step 2 Page Header
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🌊 การทำความสะอาดข้อมูล & การตรวจสอบสัญญาณดิจิทัล DSP</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_2_h2">🌊 การล้างคลื่น EKG & คัดกรองคุณภาพสัญญาณ (DSP)</h2>'
)

# Step 3 Page Header
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🔬 การสำรวจข้อมูลเชิงลึก (EDA) & วิศวกรรมฟีเจอร์คลื่นไฟฟ้าหัวใจ</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_3_h2">🔬 สำรวจข้อมูลเชิงลึก (EDA) & ฟีเจอร์คลื่นหัวใจ 8 ขั้นตอน</h2>'
)

# Step 4 Page Header
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🏆 การประเมินกลุ่มแบบจำลองไฮบริด & ลีดเดอร์บอร์ดการทำนายโรค</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_4_h2">🏆 เปรียบเทียบผลโมเดล AI & ตารางอันดับความแม่นยำ</h2>'
)

# Step 5 Page Header
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🩺 ประวัติผู้ป่วยรายยาว & ตัวจำลองการประเมินความเสี่ยงคลินิก</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_5_h2">🩺 ดูประวัติคนไข้ตามเวลา & จำลองผลตรวจ AI (XAI Simulator)</h2>'
)
content = content.replace(
    '<h2 class="fw-bold mb-0 text-dark">🩺 ประวัติผู้ป่วยรายยาว &amp; ตัวจำลองการประเมินความเสี่ยงคลินิก</h2>',
    '<h2 class="fw-bold mb-0 text-dark" data-i18n="page_5_h2">🩺 ดูประวัติคนไข้ตามเวลา & จำลองผลตรวจ AI (XAI Simulator)</h2>'
)

print("4. Updated Page Headers with Natural Thai and data-i18n successfully!")

# -----------------------------------------------------------------------------
# 5. INJECT COMPREHENSIVE JAVASCRIPT BILINGUAL ENGINE
# -----------------------------------------------------------------------------
# Find where script starts or near initStep1
p_script = content.find('<script>')
p_script_end = content.find('</script>', p_script)

js_i18n_engine = """
        // =====================================================================
        // COMPREHENSIVE BILINGUAL TRANSLATION ENGINE (THAI & ENGLISH)
        // Note: Thai uses natural, friendly, clear terms ('ภาษาไทยปกติ ไม่ต้องเป็นทางการ')
        // =====================================================================
        let CURRENT_LANG = localStorage.getItem('ekg_lang') || 'th';

        const I18N_DICT = {
            th: {
                // Navbar
                'btn_toggle_menu': ' เมนู',
                'navbar_app_title': 'PTB-XL ECG Intelligence Platform',
                'navbar_app_subtitle': 'ระบบติดตามและวิเคราะห์คลื่นหัวใจ 12 ลีด ช่วยประเมินอาการคนไข้ (Clinical CDS)',
                'navbar_badge_records': '<i class="fas fa-database me-1"></i> 21,246 บันทึก EKG (18,499 คนไข้จริง)',
                'navbar_badge_leakage': '<i class="fas fa-shield-check me-1"></i> แยกคนไข้เด็ดขาด (Zero Leakage) ✅',
                'navbar_badge_hipaa': '<i class="fas fa-lock me-1"></i> ปลอดภัยตามเกณฑ์ HIPAA/PDPA ✅',

                // Stepper Header
                'stepper_badge': 'PIPELINE ROADMAP',
                'stepper_main_title': 'ขั้นตอนการวิเคราะห์และพัฒนาโมเดล EKG ทั้งหมด (End-to-End Workflow)',
                'stepper_badge_audit': '<i class="fas fa-check-circle me-1"></i> มาตรฐาน 5 เฟสตรวจสอบได้',
                'stepper_badge_interactive': '<i class="fas fa-sliders me-1"></i> คลิกเลือกดูแต่ละขั้นตอนได้ทันที',
                'step_1_phase': 'เฟส 1',
                'step_1_title': '1. ข้อมูลเบื้องต้น',
                'step_1_sub': 'โครงสร้าง & ที่มาคนไข้',
                'step_2_phase': 'เฟส 2',
                'step_2_title': '2. ล้างคลื่น EKG',
                'step_2_sub': 'กรอง Noise & คัดคุณภาพ',
                'step_3_phase': 'เฟส 3',
                'step_3_title': '3. สำรวจข้อมูล EDA',
                'step_3_sub': '8 ขั้นตอนเจาะลึกฟีเจอร์',
                'step_4_phase': 'เฟส 4',
                'step_4_title': '4. เปรียบเทียบโมเดล',
                'step_4_sub': 'ML, DL & 1D-CNN',
                'step_5_phase': 'เฟส 5',
                'step_5_title': '5. ประวัติคนไข้ & CDS',
                'step_5_sub': 'ไทม์ไลน์ & ลองจำลองผล',

                // Sidebar
                'sidebar_heading': 'ขั้นตอนการทำงาน (Pipeline Steps)',
                'sidebar_step_1': '1. ข้อมูลเบื้องต้น & จัดการข้อมูล 🏛️',
                'sidebar_step_2': '2. ล้างคลื่น EKG & คุณภาพ 🌊',
                'sidebar_step_3': '3. สำรวจข้อมูล EDA (8 ขั้น) 🔬',
                'sidebar_step_4': '4. เปรียบเทียบโมเดล AI 🏆',
                'sidebar_step_5': '5. ประวัติคนไข้ & จำลองผล 🩺',
                'sub_1_grain': 'โครงสร้างระดับข้อมูลคนไข้',
                'sub_1_visit': 'จำนวนครั้งที่คนไข้มาตรวจ',
                'sub_1_funnel': 'ขั้นตอนคัดกรองข้อมูล',
                'sub_1_dict': 'ความหมายตัวแปรและข้อมูล',
                'sub_1_missing': 'รายการข้อมูลที่ขาดหาย',
                'sub_1_prov': 'ที่มาและความถูกต้องข้อมูล',
                'sub_2_filter': 'ขั้นตอนกรองสัญญาณ Noise',
                'sub_2_compare': 'เทียบคลื่นก่อน-หลังล้าง',
                'sub_2_sqi': 'คะแนนคุณภาพสัญญาณ (SQI)',
                'sub_2_quarantine': 'คลื่นสัญญาณรบกวนที่คัดออก',
                'sub_3_1': '3.1 มิติและคลังฟีเจอร์',
                'sub_3_2': '3.2 กราฟตัวแปรเดี่ยว',
                'sub_3_3': '3.3 ข้อมูลสูญหายและคุณภาพ',
                'sub_3_4': '3.4 ความสัมพันธ์และแบ่งตามโรค',
                'sub_3_5': '3.5 รูปคลื่นจริงและสเปกตรัม',
                'sub_3_6': '3.6 ตรวจจับค่าผิดปกติ',
                'sub_3_7': '3.7 คนไข้ที่มาตรวจซ้ำ',
                'sub_3_8': '3.8 ตรวจสอบข้อมูลรั่วไหล',
                'sub_4_tab_b': 'ตาราง ข: โมเดล Machine Learning',
                'sub_4_tab_c': 'ตาราง ค: Deep Learning (1D-CNN)',
                'sub_4_tab_a': 'ตาราง ก: ตรวจจับสิ่งผิดปกติ',
                'sub_4_tab_d': 'ตาราง ง: สรุปผลด้วย Clinical LLM',
                'sub_4_split': 'การแบ่งคนไข้ GroupKFold',
                'sub_4_cm': 'ตารางความแม่นยำรายโรค',
                'sub_4_roc': 'กราฟ ROC-AUC 5 กลุ่มโรค',
                'sub_4_feat': '15 ฟีเจอร์ที่สำคัญที่สุด',
                'sub_5_kpi': 'สรุปภาพรวมสำคัญ (4 KPIs)',
                'sub_5_search': 'ค้นหาและเลือกคนไข้',
                'sub_5_diag': 'ผลวิเคราะห์โรคทันที (2 ข้อ)',
                'sub_5_metrics': 'ค่าสถิติสรีรวิทยาละเอียด',
                'sub_5_wave': 'คลื่น 12 ลีด & จุดที่ AI สนใจ',
                'sub_5_llm': 'สรุปความเห็นแพทย์ (AI LLM)',
                'sub_5_shap': 'เหตุผลการตัดสินใจ (SHAP)',
                'sub_5_sim': 'ลองปรับค่าจำลองความเสี่ยง',
                'disclaimer_title': 'ขอบเขตการใช้งานทางคลินิก',
                'disclaimer_body': 'ระบบนี้ทำหน้าที่เป็น<strong>เครื่องมือช่วยคัดกรองเบื้องต้น (Clinical Decision Support)</strong> ไม่สามารถใช้แทนการวินิจฉัยยืนยันโดยแพทย์อายุรศาสตร์หัวใจได้',

                // Page Headers
                'page_1_h2': '🏛️ ข้อมูลเบื้องต้น & โครงสร้างประวัติคนไข้',
                'page_2_h2': '🌊 การล้างคลื่น EKG & คัดกรองคุณภาพสัญญาณ (DSP)',
                'page_3_h2': '🔬 สำรวจข้อมูลเชิงลึก (EDA) & ฟีเจอร์คลื่นหัวใจ 8 ขั้นตอน',
                'page_4_h2': '🏆 เปรียบเทียบผลโมเดล AI & ตารางอันดับความแม่นยำ',
                'page_5_h2': '🩺 ดูประวัติคนไข้ตามเวลา & จำลองผลตรวจ AI (XAI Simulator)'
            },
            en: {
                // Navbar
                'btn_toggle_menu': ' Menu',
                'navbar_app_title': 'PTB-XL ECG Intelligence Platform',
                'navbar_app_subtitle': '12-Lead Longitudinal ECG Analytics & Clinical Decision Support (CDS) Platform',
                'navbar_badge_records': '<i class="fas fa-database me-1"></i> 21,246 ECG Records (18,499 Patients)',
                'navbar_badge_leakage': '<i class="fas fa-shield-check me-1"></i> GroupKFold Zero-Leakage ✅',
                'navbar_badge_hipaa': '<i class="fas fa-lock me-1"></i> HIPAA/PDPA Compliant ✅',

                // Stepper Header
                'stepper_badge': 'PIPELINE ROADMAP',
                'stepper_main_title': 'End-to-End Clinical ML/DL Workflow Roadmap',
                'stepper_badge_audit': '<i class="fas fa-check-circle me-1"></i> 5-Phase Audit-Ready Standard',
                'stepper_badge_interactive': '<i class="fas fa-sliders me-1"></i> Interactive Stage Navigation',
                'step_1_phase': 'Phase 1',
                'step_1_title': '1. Foundation',
                'step_1_sub': 'Grain & Provenance',
                'step_2_phase': 'Phase 2',
                'step_2_title': '2. Denoising',
                'step_2_sub': 'DSP Filters & QC',
                'step_3_phase': 'Phase 3',
                'step_3_title': '3. Exploratory EDA',
                'step_3_sub': '8-Step Features EDA',
                'step_4_phase': 'Phase 4',
                'step_4_title': '4. Model Evaluation',
                'step_4_sub': 'ML, DL & 1D-CNN Pool',
                'step_5_phase': 'Phase 5',
                'step_5_title': '5. Patient CDS',
                'step_5_sub': 'Trajectory & XAI Sim',

                // Sidebar
                'sidebar_heading': 'Pipeline Analysis Steps',
                'sidebar_step_1': '1. Data Foundation 🏛️',
                'sidebar_step_2': '2. Signal Cleaning (DSP) 🌊',
                'sidebar_step_3': '3. Exploratory EDA (8 Steps) 🔬',
                'sidebar_step_4': '4. Model Leaderboard 🏆',
                'sidebar_step_5': '5. Patient Trajectory & Sim 🩺',
                'sub_1_grain': 'Patient-Encounter Grain Architecture',
                'sub_1_visit': 'Visit Count Frequency Distribution',
                'sub_1_funnel': 'Data Attrition Cleaning Funnel',
                'sub_1_dict': 'Medical Data Dictionary',
                'sub_1_missing': 'Missing Data Inventory (MCAR/MAR/MNAR)',
                'sub_1_prov': 'Data Provenance & Cryptographic Audit',
                'sub_2_filter': 'DSP Waveform Filtering Audit',
                'sub_2_compare': 'Raw vs Cleaned Dual Comparison',
                'sub_2_sqi': 'Signal Quality Index (SQI) Heatmap',
                'sub_2_quarantine': 'Quarantined Corrupted Registry',
                'sub_3_1': '3.1 Dimensions & Inventory',
                'sub_3_2': '3.2 Univariate Distributions',
                'sub_3_3': '3.3 Missingness & Signal Quality',
                'sub_3_4': '3.4 Correlation & Stratification',
                'sub_3_5': '3.5 Waveform Overlay & Welch PSD',
                'sub_3_6': '3.6 Outlier & Clinical Anomaly',
                'sub_3_7': '3.7 Longitudinal Visit Dynamics',
                'sub_3_8': '3.8 Data Leakage Audit Gate',
                'sub_4_tab_b': 'Table B: Supervised ML Leaderboard',
                'sub_4_tab_c': 'Table C: Deep Learning (1D-CNN)',
                'sub_4_tab_a': 'Table A: Unsupervised & Anomaly',
                'sub_4_tab_d': 'Table D: Clinical LLM Layer',
                'sub_4_split': 'GroupKFold Patient Separation',
                'sub_4_cm': 'Normalized Confusion Matrix',
                'sub_4_roc': 'ROC-AUC Curves (5 Superclasses)',
                'sub_4_feat': 'Top 15 Biomedical Features',
                'sub_5_kpi': 'Executive KPIs Overview (4 KPIs)',
                'sub_5_search': 'Patient Search & Timeline Selector',
                'sub_5_diag': 'Instant Diagnostic Readout (2 Answers)',
                'sub_5_metrics': 'Detailed Electrophysiological Vitals',
                'sub_5_wave': '12-Lead Traces & 1D-CAM AI Heatmap',
                'sub_5_llm': 'Clinical Narrative Summary (LLM)',
                'sub_5_shap': 'Local Explainability (SHAP Waterfall)',
                'sub_5_sim': 'What-If Clinical Risk Simulator',
                'disclaimer_title': 'Clinical Scope of Use',
                'disclaimer_body': 'This platform serves as a <strong>Clinical Decision Support (CDS) screening tool</strong>. It does not replace definitive medical evaluation by a certified cardiologist.',

                // Page Headers
                'page_1_h2': '🏛️ Data Foundation & Patient Grain Hierarchy',
                'page_2_h2': '🌊 Signal Denoising & Digital Signal Processing (DSP)',
                'page_3_h2': '🔬 8-Step Exploratory Data Analysis & Feature Engineering',
                'page_4_h2': '🏆 Hybrid Model Benchmarks & Superclass Leaderboard',
                'page_5_h2': '🩺 Longitudinal Patient Trajectory & Clinical CDS Simulator'
            }
        };

        function setLanguage(lang) {
            if (!lang || !I18N_DICT[lang]) lang = 'th';
            CURRENT_LANG = lang;
            localStorage.setItem('ekg_lang', lang);

            // Update Language Switcher Buttons
            const btnTh = document.getElementById('btn-lang-th');
            const btnEn = document.getElementById('btn-lang-en');
            if (btnTh && btnEn) {
                if (lang === 'th') {
                    btnTh.className = 'btn btn-sm btn-primary py-1 px-2 fw-bold';
                    btnEn.className = 'btn btn-sm btn-outline-secondary py-1 px-2 fw-bold';
                } else {
                    btnTh.className = 'btn btn-sm btn-outline-secondary py-1 px-2 fw-bold';
                    btnEn.className = 'btn btn-sm btn-primary py-1 px-2 fw-bold';
                }
            }

            // Translate elements with data-i18n
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (I18N_DICT[lang] && I18N_DICT[lang][key]) {
                    el.innerHTML = I18N_DICT[lang][key];
                }
            });

            // Update search placeholder if applicable
            const searchInput = document.getElementById('input-patient-search');
            if (searchInput) {
                searchInput.placeholder = (lang === 'th')
                    ? 'พิมพ์ค้นหา เช่น 21602, 9898, MI, หญิง, 72 ปี...'
                    : 'Search by ID, class, age, sex, e.g. 21602, MI, female, 72...';
            }

            // Re-render active Plotly charts with the selected language
            updateChartsLanguage(lang);
        }

        function updateChartsLanguage(lang) {
            const isTh = (lang === 'th');

            // 1. Target Distribution
            if (document.getElementById('chart-target-distribution')) {
                Plotly.relayout('chart-target-distribution', {
                    'xaxis.title': isTh ? 'กลุ่มโรคหัวใจ 5 ซูเปอร์คลาส (Diagnostic Superclasses)' : 'Diagnostic Superclasses (5 Classes)',
                    'yaxis.title': isTh ? 'จำนวนบันทึก (Records)' : 'Record Count'
                });
            }

            // 2. Age & Sex Distribution
            if (document.getElementById('chart-age-sex-distribution')) {
                Plotly.relayout('chart-age-sex-distribution', {
                    'xaxis.title': isTh ? 'ช่วงอายุคนไข้ (Age Groups)' : 'Patient Age Groups',
                    'yaxis.title': isTh ? 'จำนวนคนไข้ (คน)' : 'Patient Count'
                });
            }

            // 3. Biomedical HR Distribution
            if (document.getElementById('chart-bio-distribution')) {
                Plotly.relayout('chart-bio-distribution', {
                    'xaxis.title': isTh ? 'ช่วงอัตราการเต้นหัวใจ (Heart Rate - bpm)' : 'Heart Rate Bins (bpm)',
                    'yaxis.title': isTh ? 'จำนวนบันทึก (Records)' : 'Record Count'
                });
            }

            // 4. Waveform Lead II Overlay
            if (document.getElementById('chart-biomedical-overlay')) {
                Plotly.relayout('chart-biomedical-overlay', {
                    'xaxis.title': isTh ? 'เวลา (วินาที - Seconds)' : 'Time (Seconds)',
                    'yaxis.title': isTh ? 'แรงดันไฟฟ้า (มิลลิโวลต์ - mV)' : 'Amplitude (mV)'
                });
            }

            // 5. Welch PSD
            if (document.getElementById('chart-welch-psd')) {
                Plotly.relayout('chart-welch-psd', {
                    'xaxis.title': isTh ? 'ความถี่ (เฮิรตซ์ - Hz)' : 'Frequency (Hz)',
                    'yaxis.title': isTh ? 'กำลังสเปกตรัม (ms²/Hz)' : 'Spectral Power (ms²/Hz)'
                });
            }

            // 6. Outlier Boxplot
            if (document.getElementById('chart-outlier-box')) {
                Plotly.relayout('chart-outlier-box', {
                    'yaxis.title': isTh ? 'สเกลเปรียบเทียบสถิติ (Normalized Units)' : 'Normalized Metric Scale'
                });
            }

            // 7. Visit Distribution
            if (document.getElementById('chart-eda-visit-dist')) {
                Plotly.relayout('chart-eda-visit-dist', {
                    'xaxis.title': isTh ? 'จำนวนครั้งที่ตรวจต่อคนไข้ 1 ราย (Visit Frequency)' : 'Encounter Frequency Per Patient',
                    'yaxis.title': isTh ? 'จำนวนคนไข้จริง (คน)' : 'Patient Count'
                });
            }
        }
"""

# Insert i18n engine before window.onload or DOMContentLoaded
p_onload = content.find('document.addEventListener(\'DOMContentLoaded\'')
if p_onload == -1:
    p_onload = content.find('window.addEventListener(\'DOMContentLoaded\'')

if p_onload != -1:
    content = content[:p_onload] + js_i18n_engine + "\n        " + content[p_onload:]
    print("5. Injected Bilingual JavaScript Engine successfully!")
else:
    # insert before </script>
    p_last_script = content.rfind('</script>')
    content = content[:p_last_script] + js_i18n_engine + "\n    " + content[p_last_script:]
    print("5. Injected Bilingual JavaScript Engine before </script> successfully!")

# Ensure setLanguage(CURRENT_LANG) is called inside DOMContentLoaded
p_dcl = content.find("document.addEventListener('DOMContentLoaded', () => {")
if p_dcl != -1:
    insert_call = "document.addEventListener('DOMContentLoaded', () => {\n            // Initialize Bilingual Language\n            setLanguage(CURRENT_LANG);\n"
    content = content.replace("document.addEventListener('DOMContentLoaded', () => {", insert_call, 1)
    print("6. Added setLanguage(CURRENT_LANG) to DOMContentLoaded successfully!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: ekg_longitudinal_dashboard.html bilingual update completed!")
