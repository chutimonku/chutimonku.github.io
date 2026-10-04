import re

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Patient Search & Cohort Selector HTML
# Find section from '<div class="row g-3 align-items-center mb-3">' under sec-patient-timeline
p_start = content.find('<div class="card card-custom mb-4" id="sec-patient-timeline">')
if p_start == -1:
    print("Could not find sec-patient-timeline")
    exit(1)

p_target_start = content.find('<div class="row g-3 align-items-center mb-3">', p_start)
p_target_end = content.find('<!-- Full-Width Patient Chronological Visit Timeline Chart', p_target_start)

old_selector_html = content[p_target_start:p_target_end]

new_selector_html = """<!-- Patient Search & Cohort Selector Bar -->
                        <div class="p-3 mb-3 rounded-4 bg-light border">
                            <div class="row g-3 align-items-center mb-2">
                                <div class="col-md-6">
                                    <label class="form-label small text-muted mb-1 font-code"><i class="fas fa-magnifying-glass text-primary me-1"></i> ค้นหาผู้ป่วย (Search by ID, Disease Class, Age/Sex):</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-white"><i class="fas fa-search text-muted"></i></span>
                                        <input type="text" class="form-control font-code" id="input-patient-search" placeholder="พิมพ์ค้นหา เช่น 21602, 9898, MI, หญิง, 72 ปี..." oninput="onPatientSearchInput(this.value)">
                                        <button class="btn btn-outline-secondary" type="button" onclick="clearPatientSearch()"><i class="fas fa-times"></i></button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label small text-muted mb-1 font-code"><i class="fas fa-users text-primary me-1"></i> เลือกผู้ป่วยที่มีประวัติติดตามผล (Patient Cohort):</label>
                                    <select class="form-select font-code fw-bold text-primary" id="select-patient-id" onchange="loadSelectedPatientTimeline()">
                                        <option value="21602" selected>ผู้ป่วย #21602 (7 รอบตรวจ | 1993-05 ถึง 1999-11 | NORM ➔ CD ➔ MI)</option>
                                        <option value="9898">ผู้ป่วย #9898 (10 รอบตรวจ | 1989-10 ถึง 1999-07 | Multi-Visit Cohort)</option>
                                        <option value="8304">ผู้ป่วย #8304 (9 รอบตรวจ | 1991-03 ถึง 1998-04 | Longitudinal Follow-up)</option>
                                        <option value="10107">ผู้ป่วย #10107 (9 รอบตรวจ | 1992-01 ถึง 1997-12 | Longitudinal Follow-up)</option>
                                        <option value="15765">ผู้ป่วย #15765 (8 รอบตรวจ | 1990-06 ถึง 1996-08 | Longitudinal Follow-up)</option>
                                        <option value="8810">ผู้ป่วย #8810 (8 รอบตรวจ | 1993-04 ถึง 1998-09 | Longitudinal Follow-up)</option>
                                        <option value="13145">ผู้ป่วย #13145 (8 รอบตรวจ | 1994-02 ถึง 1999-05 | Longitudinal Follow-up)</option>
                                        <option value="20655">ผู้ป่วย #20655 (7 รอบตรวจ | 1991-08 ถึง 1997-10 | Longitudinal Follow-up)</option>
                                        <option value="307">ผู้ป่วย #307 (3 รอบตรวจ | 1995-02 ถึง 1998-03 | Longitudinal Follow-up)</option>
                                        <option value="319">ผู้ป่วย #319 (2 รอบตรวจ | 1996-04 ถึง 1997-01 | Longitudinal Follow-up)</option>
                                        <option value="318">ผู้ป่วย #318 (2 รอบตรวจ | 1996-04 ถึง 1997-01 | Longitudinal Follow-up)</option>
                                        <option value="302">ผู้ป่วย #302 (2 รอบตรวจ | 1995-01 ถึง 1996-09 | Longitudinal Follow-up)</option>
                                    </select>
                                </div>
                            </div>

                            <!-- Quick Filter Category Pills -->
                            <div class="d-flex flex-wrap align-items-center gap-2 pt-2 border-top">
                                <span class="small text-muted font-code"><i class="fas fa-filter text-info me-1"></i> ตัวกรองหมวดหมู่:</span>
                                <button type="button" class="btn btn-sm btn-primary py-0 px-2 font-code active" id="filter-btn-all" onclick="filterPatientCategory('all')">ทั้งหมด (12 ราย)</button>
                                <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 font-code" id="filter-btn-mi" onclick="filterPatientCategory('MI')">เคสวิกฤต MI (4 ราย)</button>
                                <button type="button" class="btn btn-sm btn-outline-purple py-0 px-2 font-code" id="filter-btn-cd" onclick="filterPatientCategory('CD')">การนำไฟฟ้าขัดข้อง CD (3 ราย)</button>
                                <button type="button" class="btn btn-sm btn-outline-success py-0 px-2 font-code" id="filter-btn-norm" onclick="filterPatientCategory('NORM')">สัญญาณปกติ NORM (3 ราย)</button>
                                <button type="button" class="btn btn-sm btn-outline-info py-0 px-2 font-code" id="filter-btn-freq" onclick="filterPatientCategory('freq')">ตรวจซ้ำ ≥ 7 รอบ (8 ราย)</button>
                            </div>
                        </div>

                        <!-- Demographics & Summary Info -->
                        <div class="p-3 mb-3 rounded-4 bg-white border d-flex flex-wrap justify-content-between align-items-center gap-2">
                            <div>
                                <div class="small text-muted font-code">ข้อมูลทั่วไปของผู้ป่วยที่กำลังเลือก:</div>
                                <div class="fs-5 fw-bold text-dark font-code" id="info-patient-demographics">
                                    ผู้ป่วย #21602 | อายุ 72 ปี | เพศ: หญิง
                                </div>
                            </div>
                            <div class="text-end">
                                <div class="small text-muted font-code">ประวัติการตรวจทั้งหมด:</div>
                                <span class="badge-neon-blue fs-6" id="badge-patient-enc-count">7 รอบการตรวจ</span>
                            </div>
                        </div>

                        """

content = content[:p_target_start] + new_selector_html + content[p_target_end:]
print("Updated HTML selector container successfully!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
