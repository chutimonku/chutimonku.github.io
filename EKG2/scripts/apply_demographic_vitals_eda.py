# scripts/apply_demographic_vitals_eda.py
"""
Script to upgrade Step 3.2 in outputs/dashboard/ekg_longitudinal_dashboard.html
with deep-dive demographic and vitals EDA:
- Age & Sex Population Pyramid
- Gender Disparities in Cardiac Disease
- Age-Driven Disease Progression Gradient (6 Brackets)
- Anthropometrics & WHO BMI Distributions
- Clinical Vitals (Heart Rate & QRS Duration)
Also updates Streamlit page_3_features.py and bilingual dictionaries.
"""

import sys

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

print('Initial length:', len(content))

# -----------------------------------------------------------------------------
# 1. UPGRADE SEC-EDA-32 HTML IN DASHBOARD
# -----------------------------------------------------------------------------
p_32_start = content.find('<div class="card card-custom eda-step-card" id="sec-eda-32">')
p_33_start = content.find('<div class="card card-custom eda-step-card" id="sec-eda-33">')

if p_32_start == -1 or p_33_start == -1:
    print('ERROR: sec-eda-32 or sec-eda-33 not found')
    sys.exit(1)

new_sec_32 = """<div class="card card-custom eda-step-card" id="sec-eda-32">
                    <div class="card-header-custom">
                        <div class="d-flex align-items-center gap-2">
                            <span class="eda-badge-step" id="eda-step-badge-32">ขั้นตอนที่ 3.2</span>
                            <span class="fw-bold fs-6 text-dark" id="eda-step-title-32"><i class="fas fa-users-viewfinder text-primary me-1"></i> การวิเคราะห์เจาะลึก: อายุ เพศ สัดส่วนร่างกาย และความเสี่ยงโรคหัวใจ (Deep Dive: Age, Sex, Anthropometrics & Disease Risk)</span>
                        </div>
                        <span class="badge-neon-blue font-code">Demographics & Vitals EDA</span>
                    </div>
                    <div class="card-body-custom">
                        <div class="eda-method-box mb-4">
                            <div class="fw-bold mb-1"><i class="fas fa-microscope me-1"></i> ระเบียบวิธีวิจัยการวิเคราะห์ตัวแปรประชากรและสรีรวิทยา (Demographic & Clinical Vitals Methodology):</div>
                            <div>
                                ข้อมูลอายุ (Age) เพศ (Sex) และสัดส่วนร่างกาย (ส่วนสูง น้ำหนัก BMI) เป็นตัวแปรควบคุมทางระบาดวิทยาขั้นพื้นฐานที่มีอิทธิพลโดยตรงต่อแรงดันไฟฟ้าของคลื่น EKG 
                                ความหนาของผนังหัวใจ และความเสี่ยงในการเกิดโรคกล้ามเนื้อหัวใจขาดเลือดเฉียบพลัน การเข้าใจความแตกต่างระหว่างเพศชาย-หญิง (Sex Disparities) 
                                และความเสี่ยงที่เพิ่มขึ้นตามวัย (Age-Driven Progression Gradient) ช่วยให้แบบจำลอง AI ไม่เกิดอคติทางประชากร (Algorithmic Fairness)
                            </div>
                        </div>

                        <!-- 4 STAT KPI SUMMARY CARDS FOR DEMOGRAPHICS -->
                        <div class="row g-3 mb-4 font-code">
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center h-100">
                                    <div class="text-muted small">อายุเฉลี่ยผู้ป่วย (Mean Age)</div>
                                    <div class="fs-4 fw-bold text-dark my-1">59.4 ± 16.7 ปี</div>
                                    <div class="small text-primary"><i class="fas fa-venus-mars me-1"></i> ชาย 58.7 ปี | หญิง 60.2 ปี</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center h-100">
                                    <div class="text-muted small">สัดส่วนเพศ (Sex Ratio)</div>
                                    <div class="fs-4 fw-bold text-dark my-1">ชาย 52.0% / หญิง 48.0%</div>
                                    <div class="small text-success"><i class="fas fa-check-circle me-1"></i> กระจายตัวสมดุลในประชากร</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center h-100">
                                    <div class="text-muted small">จุดพีคความเสี่ยง MI สูงสุด</div>
                                    <div class="fs-4 fw-bold text-danger my-1">ชาย 50–69 ปี</div>
                                    <div class="small text-danger"><i class="fas fa-arrow-trend-up me-1"></i> พบ MI สูงกว่าหญิง 1.7 เท่า</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 rounded-4 bg-light border text-center h-100">
                                    <div class="text-muted small">ภาวะน้ำหนักเกินและอ้วน (BMI &gt; 25)</div>
                                    <div class="fs-4 fw-bold text-warning my-1">53.7% ของผู้ตรวจวัด</div>
                                    <div class="small text-muted"><i class="fas fa-weight-scale me-1"></i> เกณฑ์ Overweight/Obese WHO</div>
                                </div>
                            </div>
                        </div>

                        <!-- ROW 1: TARGET CLASS & POPULATION PYRAMID -->
                        <div class="row g-4 mb-4">
                            <!-- 3.2A: Target Superclass Distribution -->
                            <div class="col-lg-5">
                                <div class="card card-custom shadow-none border h-100">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small">
                                            <i class="fas fa-chart-pie text-success me-1"></i> 1. สัดส่วนกลุ่มโรคหัวใจ 5 กลุ่มหลัก (Target Classes)
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-target-distribution" style="height: 330px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            <i class="fas fa-info-circle me-1 text-primary"></i> <strong>คลาส NORM</strong> เป็นกลุ่มใหญ่สุด (43.2%) ขณะที่ <strong>HYP</strong> มีสัดส่วนน้อยสุด (6.1%) สะท้อนความไม่สมดุลตามธรรมชาติ
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 3.2B: Age & Sex Population Pyramid -->
                            <div class="col-lg-7">
                                <div class="card card-custom shadow-none border h-100">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small" id="title-age-sex-pyramid">
                                            <i class="fas fa-users text-primary me-1"></i> 2. พีระมิดประชากรผู้ป่วย: การกระจายตัวของอายุตามเพศชาย-หญิง
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-age-sex-distribution" style="height: 330px;"></div>
                                        <div class="p-2 rounded bg-light border small text-muted font-code mt-2">
                                            👥 <strong>ลักษณะพีระมิดประชากร:</strong> หนาแน่นสูงสุดในช่วงอายุ <strong>50–75 ปี</strong> (คิดเป็น 55.4% ของผู้ป่วยทั้งหมด) สะท้อนช่วงวัยที่มีความเสี่ยงต่อโรคหลอดเลือดและระบบนำไฟฟ้าหัวใจสูงสุด
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- ROW 2: GENDER DISPARITIES & AGE-DRIVEN DISEASE GRADIENT -->
                        <div class="row g-4 mb-4">
                            <!-- 3.2C: Sex Disparities in Disease Classes -->
                            <div class="col-lg-6">
                                <div class="card card-custom shadow-none border h-100">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small" id="title-sex-disease-disparity">
                                            <i class="fas fa-venus-mars text-danger me-1"></i> 3. ความต่างของอัตราการเกิดโรคระหว่างเพศชาย vs เพศหญิง
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-sex-disease-disparity" style="height: 330px;"></div>
                                        <div class="p-3 rounded-3 bg-light border small font-code mt-2">
                                            <strong class="text-dark"><i class="fas fa-stethoscope text-primary me-1"></i> ข้อค้นพบสำคัญทางระบาดวิทยาคลินิก:</strong>
                                            <ul class="mb-0 mt-1 ps-3 text-muted">
                                                <li><strong>ผู้ชายเป็น MI สูงถึง 62.9% (2,545 คน)</strong> และเป็น <strong>CD สูงถึง 61.4% (2,106 คน)</strong> สูงกว่าผู้หญิงอย่างมีนัยสำคัญ</li>
                                                <li><strong>ผู้หญิงพบ STTC สูงกว่าผู้ชาย (55.6% vs 44.4%)</strong> สอดคล้องกับทฤษฎีสรีรวิทยาไฟฟ้าที่ผู้หญิงมีการตอบสนองของระบบประสาทอัตโนมัติและความผันผวนของฮอร์โมนต่อคลื่น T-wave สูงกว่า</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 3.2D: Age-Driven Disease Progression Gradient -->
                            <div class="col-lg-6">
                                <div class="card card-custom shadow-none border h-100">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small" id="title-age-disease-gradient">
                                            <i class="fas fa-chart-area text-warning me-1"></i> 4. สัดส่วนกลุ่มโรคหัวใจตามช่วงอายุ 6 ช่วงวัย (Age-Driven Risk Gradient)
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-age-disease-gradient" style="height: 330px;"></div>
                                        <div class="p-3 rounded-3 bg-light border small font-code mt-2">
                                            <strong class="text-dark"><i class="fas fa-arrow-trend-up text-danger me-1"></i> อัตราการเกิดโรคเร่งตัวตามอายุขัย:</strong>
                                            <ul class="mb-0 mt-1 ps-3 text-muted">
                                                <li>กลุ่มอายุน้อย (&lt;40 ปี) มีสัดส่วน <strong>ผลตรวจปกติ (NORM) สูงถึง 78.6%</strong></li>
                                                <li>กลุ่มผู้สูงอายุ (80+ ปี) ผลตรวจปกติลดลงเหลือเพียง <strong>17.8%</strong> ขณะที่ <strong>MI พุ่งเป็น 26.3%</strong> และ <strong>CD พุ่งเป็น 23.8%</strong> จากการเสื่อมของระบบนำไฟฟ้าตามวัย</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- ROW 3: ANTHROPOMETRICS (HEIGHT, WEIGHT & BMI) + CLINICAL VITALS -->
                        <div class="row g-4 mb-2">
                            <!-- 3.2E: Anthropometrics & BMI Distribution -->
                            <div class="col-lg-6">
                                <div class="card card-custom shadow-none border h-100">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small" id="title-bmi-distributions">
                                            <i class="fas fa-weight-scale text-purple me-1"></i> 5. สัดส่วนร่างกายและดัชนีมวลกาย (Height, Weight & BMI Distribution)
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-bmi-distributions" style="height: 330px;"></div>
                                        <div class="row g-2 mt-2 font-code small text-center">
                                            <div class="col-4">
                                                <div class="p-2 rounded bg-light border">
                                                    <div class="text-muted" style="font-size:0.72rem;">ส่วนสูงเฉลี่ย</div>
                                                    <div class="fw-bold text-dark">ชาย 173.7 cm<br>หญิง 161.2 cm</div>
                                                </div>
                                            </div>
                                            <div class="col-4">
                                                <div class="p-2 rounded bg-light border">
                                                    <div class="text-muted" style="font-size:0.72rem;">น้ำหนักเฉลี่ย</div>
                                                    <div class="fw-bold text-dark">ชาย 77.7 kg<br>หญิง 64.5 kg</div>
                                                </div>
                                            </div>
                                            <div class="col-4">
                                                <div class="p-2 rounded bg-light border">
                                                    <div class="text-muted" style="font-size:0.72rem;">BMI เฉลี่ย</div>
                                                    <div class="fw-bold text-warning">ชาย 25.8 (เกิน)<br>หญิง 24.8 (ปกติ)</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 3.2F: Electrophysiological Vitals (HR & QRS Duration) -->
                            <div class="col-lg-6">
                                <div class="card card-custom shadow-none border h-100" id="sec-bio-distribution">
                                    <div class="card-header-custom bg-transparent">
                                        <div class="fw-bold text-dark font-code small" id="title-bio-distribution">
                                            <i class="fas fa-heart-pulse text-danger me-1"></i> 6. สัญญาณชีพและสรีรวิทยาไฟฟ้าหัวใจ (Heart Rate & QRS Duration)
                                        </div>
                                    </div>
                                    <div class="card-body-custom">
                                        <div id="chart-bio-distribution" style="height: 330px;"></div>
                                        <div class="row g-2 mt-2 font-code small text-center">
                                            <div class="col-6">
                                                <div class="p-2 rounded bg-light border">
                                                    <div class="text-muted" style="font-size:0.72rem;">อัตราเต้นหัวใจเฉลี่ย</div>
                                                    <div class="fw-bold text-dark">74.2 ± 16.5 bpm</div>
                                                    <div class="text-success" style="font-size:0.70rem;">ปกติ (60–100 bpm): 78.4%</div>
                                                </div>
                                            </div>
                                            <div class="col-6">
                                                <div class="p-2 rounded bg-light border">
                                                    <div class="text-muted" style="font-size:0.72rem;">ความกว้างคลื่น QRS เฉลี่ย</div>
                                                    <div class="fw-bold text-dark">96.4 ± 22.8 ms</div>
                                                    <div class="text-danger" style="font-size:0.70rem;">กว้างผิดปกติ (&gt;120ms): 8.9%</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                """

content = content[:p_32_start] + new_sec_32 + content[p_33_start:]
print('Replaced Step 3.2 HTML! New length:', len(content))

# -----------------------------------------------------------------------------
# 2. UPDATE INITSTEP3() IN JAVASCRIPT FOR THE NEW DEMOGRAPHIC CHARTS
# -----------------------------------------------------------------------------
old_charts_32 = """            // -----------------------------------------------------------------
            // CHART 3.2B: Age and Sex Distribution
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
                        marker: { color: '#3b82f6' }
                    },
                    {
                        x: ageBins,
                        y: femaleCounts,
                        name: 'เพศหญิง (Female: 51.9%)',
                        type: 'bar',
                        marker: { color: '#ec4899' }
                    }
                ], {
                    barmode: 'group',
                    margin: { l: 40, r: 20, t: 20, b: 40 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { orientation: 'h', y: 1.15 },
                    font: { family: 'IBM Plex Sans Thai, sans-serif' }
                }, { responsive: true, displayModeBar: false });
            }"""

new_charts_32 = """            // -----------------------------------------------------------------
            // CHART 3.2B: Age & Sex Population Pyramid
            // -----------------------------------------------------------------
            if (document.getElementById('chart-age-sex-distribution')) {
                const pyramidAges = ['<30', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'];
                const malePyramid = [568, 815, 1307, 2582, 3144, 1869, 826];
                const femalePyramid = [802, 643, 1135, 1777, 2285, 2117, 1518];

                Plotly.newPlot('chart-age-sex-distribution', [
                    {
                        x: pyramidAges,
                        y: malePyramid,
                        name: 'เพศชาย (Male: 52.0%)',
                        type: 'bar',
                        marker: { color: '#3b82f6' },
                        text: malePyramid.map(v => v.toLocaleString()),
                        textposition: 'auto'
                    },
                    {
                        x: pyramidAges,
                        y: femalePyramid,
                        name: 'เพศหญิง (Female: 48.0%)',
                        type: 'bar',
                        marker: { color: '#ec4899' },
                        text: femalePyramid.map(v => v.toLocaleString()),
                        textposition: 'auto'
                    }
                ], {
                    barmode: 'group',
                    margin: { l: 45, r: 20, t: 25, b: 40 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { orientation: 'h', y: 1.15, x: 0.1 },
                    xaxis: { title: 'ช่วงอายุผู้ป่วย (Age Brackets)' },
                    yaxis: { title: 'จำนวนผู้ป่วย (คน)' },
                    font: { family: 'IBM Plex Sans Thai, sans-serif' }
                }, { responsive: true, displayModeBar: false });
            }

            // -----------------------------------------------------------------
            // CHART 3.2C: Sex Disparities in Cardiac Disease
            // -----------------------------------------------------------------
            if (document.getElementById('chart-sex-disease-disparity')) {
                const sexDisparityDx = ['MI (กล้ามเนื้อตาย)', 'CD (การนำไฟฟ้าช้า)', 'HYP (หัวใจหนาตัว)', 'STTC (ST/T เปลี่ยน)', 'NORM (ปกติ)'];
                const malePct = [62.9, 61.4, 57.2, 44.4, 45.7];
                const femalePct = [37.1, 38.6, 42.8, 55.6, 54.3];

                Plotly.newPlot('chart-sex-disease-disparity', [
                    {
                        y: sexDisparityDx,
                        x: malePct,
                        name: 'เพศชาย (Male %)',
                        type: 'bar',
                        orientation: 'h',
                        marker: { color: '#3b82f6' },
                        text: malePct.map(v => v + '%'),
                        textposition: 'auto'
                    },
                    {
                        y: sexDisparityDx,
                        x: femalePct,
                        name: 'เพศหญิง (Female %)',
                        type: 'bar',
                        orientation: 'h',
                        marker: { color: '#ec4899' },
                        text: femalePct.map(v => v + '%'),
                        textposition: 'auto'
                    }
                ], {
                    barmode: 'stack',
                    margin: { l: 130, r: 20, t: 25, b: 40 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { orientation: 'h', y: 1.15, x: 0.1 },
                    xaxis: { title: 'สัดส่วนระหว่างเพศ (%)', range: [0, 100] },
                    font: { family: 'IBM Plex Sans Thai, sans-serif' }
                }, { responsive: true, displayModeBar: false });
            }

            // -----------------------------------------------------------------
            // CHART 3.2D: Age-Driven Disease Progression Gradient
            // -----------------------------------------------------------------
            if (document.getElementById('chart-age-disease-gradient')) {
                const ageGradBrackets = ['<40 ปี', '40-49 ปี', '50-59 ปี', '60-69 ปี', '70-79 ปี', '80+ ปี'];
                const normRate = [78.6, 64.8, 48.0, 33.7, 27.5, 17.8];
                const miRate   = [ 3.6, 12.0, 19.5, 23.7, 22.6, 26.3];
                const sttcRate = [ 5.2, 10.0, 14.3, 17.5, 20.3, 24.8];
                const cdRate   = [ 9.4,  9.2, 12.7, 18.2, 21.1, 23.8];
                const hypRate  = [ 3.1,  4.1,  5.4,  6.9,  8.4,  7.3];

                Plotly.newPlot('chart-age-disease-gradient', [
                    { x: ageGradBrackets, y: normRate, name: 'NORM (ปกติ)', type: 'bar', marker: { color: '#10b981' } },
                    { x: ageGradBrackets, y: miRate, name: 'MI (กล้ามเนื้อตาย)', type: 'bar', marker: { color: '#f43f5e' } },
                    { x: ageGradBrackets, y: sttcRate, name: 'STTC (ST/T ผิดปกติ)', type: 'bar', marker: { color: '#06b6d4' } },
                    { x: ageGradBrackets, y: cdRate, name: 'CD (นำไฟฟ้าช้า)', type: 'bar', marker: { color: '#8b5cf6' } },
                    { x: ageGradBrackets, y: hypRate, name: 'HYP (หัวใจหนาตัว)', type: 'bar', marker: { color: '#f59e0b' } }
                ], {
                    barmode: 'stack',
                    margin: { l: 45, r: 20, t: 25, b: 40 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { orientation: 'h', y: 1.15, x: 0 },
                    yaxis: { title: 'สัดส่วนในกลุ่มอายุ (%)', range: [0, 100] },
                    font: { family: 'IBM Plex Sans Thai, sans-serif' }
                }, { responsive: true, displayModeBar: false });
            }

            // -----------------------------------------------------------------
            // CHART 3.2E: Anthropometrics & WHO BMI Distributions
            // -----------------------------------------------------------------
            if (document.getElementById('chart-bmi-distributions')) {
                const bmiCategories = ['Underweight (<18.5)', 'Normal (18.5-24.9)', 'Overweight (25-29.9)', 'Obese (30+)'];
                const bmiCounts = [104, 3093, 2665, 1042];
                const bmiColors = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444'];

                Plotly.newPlot('chart-bmi-distributions', [{
                    x: bmiCategories,
                    y: bmiCounts,
                    type: 'bar',
                    marker: { color: bmiColors },
                    text: [
                        '104 คน (1.5%)',
                        '3,093 คน (44.8%)',
                        '2,665 คน (38.6%)',
                        '1,042 คน (15.1%)'
                    ],
                    textposition: 'auto'
                }], {
                    margin: { l: 45, r: 20, t: 25, b: 45 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    xaxis: { title: 'เกณฑ์ดัชนีมวลกายสากล (WHO BMI Categories)' },
                    yaxis: { title: 'จำนวนคนไข้ที่วัดจริง (คน)' },
                    font: { family: 'IBM Plex Sans Thai, sans-serif' }
                }, { responsive: true, displayModeBar: false });
            }"""

if old_charts_32 in content:
    content = content.replace(old_charts_32, new_charts_32, 1)
    print("Replaced Chart 3.2 JavaScript logic in initStep3()")
else:
    print("WARNING: old_charts_32 not found")

# -----------------------------------------------------------------------------
# 3. UPDATE CHART TITLES IN UPDATECHARTSLANGUAGE()
# -----------------------------------------------------------------------------
chart_title_old = """                'chart-age-sex-distribution': {
                    th: 'การกระจายตัวของอายุตามเพศของผู้ป่วย (Age Distribution by Sex)',
                    en: 'Age Distribution Stratified by Patient Sex'
                },"""

chart_title_new = """                'chart-age-sex-distribution': {
                    th: 'พีระมิดประชากรผู้ป่วย: การกระจายตัวของอายุตามเพศชาย-หญิง',
                    en: 'Patient Population Pyramid: Age & Sex Distribution'
                },
                'chart-sex-disease-disparity': {
                    th: 'ความต่างของอัตราการเกิดโรคระหว่างเพศชาย vs เพศหญิง',
                    en: 'Sex Disparities in Cardiac Disease Prevalence'
                },
                'chart-age-disease-gradient': {
                    th: 'สัดส่วนกลุ่มโรคหัวใจตามช่วงอายุ 6 ช่วงวัย (Age-Driven Risk Gradient)',
                    en: 'Age-Driven Cardiac Disease Risk Gradient (6 Brackets)'
                },
                'chart-bmi-distributions': {
                    th: 'สัดส่วนร่างกายและดัชนีมวลกายตามเกณฑ์ WHO (Height, Weight & BMI)',
                    en: 'Anthropometrics & WHO BMI Category Distribution'
                },"""

if chart_title_old in content:
    content = content.replace(chart_title_old, chart_title_new, 1)
    print("Updated updateChartsLanguage() demographic chart titles")
else:
    print("WARNING: chart_title_old not found")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated dashboard HTML successfully! Final length:', len(content))
