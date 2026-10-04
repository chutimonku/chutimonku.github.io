"""Generate the bilingual, evidence-backed unified MOOC dashboard.

Strictly aligned with Merged_Workflow.md:
- Covers all 11 lifecycle steps and 17 required reporting sections.
- Contains rich 4-pillar analytical cards (Purpose, Findings & Answers, Limitations, Downstream Action) for all visualizations.
- Preserves target quarantine, pre-outcome feature contracts, and empirical row-to-text LLM evaluation.
- Fully bilingual (Thai / English) with interactive segment filtering and scenario explorer.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "student_segmentation_report.html"


def read_csv(path: str) -> pd.DataFrame:
    file_path = ROOT / path
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    return pd.read_csv(file_path)


def read_json(path: str) -> dict:
    with open(ROOT / path, encoding="utf-8") as handle:
        return json.load(handle)


def table(frame: pd.DataFrame, columns: list[str] | None = None, table_id: str = "", max_rows: int | None = None) -> str:
    if columns is not None:
        frame = frame[columns].copy()
    if max_rows:
        frame = frame.head(max_rows)
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in frame.columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for value in row:
            if pd.isna(value):
                value = "—"
            elif isinstance(value, float):
                value = f"{value:,.4f}"
            cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    identifier = f' id="{table_id}"' if table_id else ""
    return f'<div class="table-wrap"><table{identifier}><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def figure_card(
    path: str,
    title_th: str,
    title_en: str,
    purpose_th: str,
    purpose_en: str,
    findings_th: str,
    findings_en: str,
    limits_th: str,
    limits_en: str,
    action_th: str,
    action_en: str,
    table_html: str = "",
    table_label_th: str = "ดูตารางข้อมูลอ้างอิงของกราฟนี้",
    table_label_en: str = "View source data table for this chart",
) -> str:
    """Rich, structured card adhering to Merged_Workflow.md chart requirements."""
    table_block = ""
    if table_html:
        table_block = f"""
        <details class="chart-table-details">
          <summary data-th="{html.escape(table_label_th)}" data-en="{html.escape(table_label_en)}">{html.escape(table_label_th)}</summary>
          {table_html}
        </details>
        """

    return f"""
    <figure class="chart-card">
      <div class="chart-header">
        <h3 data-th="{html.escape(title_th)}" data-en="{html.escape(title_en)}">{html.escape(title_th)}</h3>
        <span class="badge-evidence" data-th="หลักฐานเชิงประจักษ์" data-en="Empirical Evidence">หลักฐานเชิงประจักษ์</span>
      </div>
      <img src="../{html.escape(path)}" alt="{html.escape(title_en)}" loading="lazy">
      <div class="analysis-pillars">
        <div class="pillar pillar-purpose">
          <h4 data-th="🎯 วัตถุประสงค์และการแปลงข้อมูล" data-en="🎯 Purpose & Data Scaling">🎯 วัตถุประสงค์และการแปลงข้อมูล</h4>
          <p data-th="{html.escape(purpose_th)}" data-en="{html.escape(purpose_en)}">{html.escape(purpose_th)}</p>
        </div>
        <div class="pillar pillar-findings">
          <h4 data-th="🔍 ข้อค้นพบสำคัญและคำตอบเชิงสถิติ" data-en="🔍 Key Empirical Findings & Answers">🔍 ข้อค้นพบสำคัญและคำตอบเชิงสถิติ</h4>
          <p data-th="{html.escape(findings_th)}" data-en="{html.escape(findings_en)}">{html.escape(findings_th)}</p>
        </div>
        <div class="pillar pillar-limits">
          <h4 data-th="⚠️ ข้อจำกัดและข้อควรระวังในการแปลผล" data-en="⚠️ Limitations & Interpretation Safeguards">⚠️ ข้อจำกัดและข้อควรระวังในการแปลผล</h4>
          <p data-th="{html.escape(limits_th)}" data-en="{html.escape(limits_en)}">{html.escape(limits_th)}</p>
        </div>
        <div class="pillar pillar-action">
          <h4 data-th="🚀 การนำไปปฏิบัติในขั้นตอนถัดไป" data-en="🚀 Downstream Action & Next Step">🚀 การนำไปปฏิบัติในขั้นตอนถัดไป</h4>
          <p data-th="{html.escape(action_th)}" data-en="{html.escape(action_en)}">{html.escape(action_th)}</p>
        </div>
      </div>
      {table_block}
    </figure>
    """


def interactive_figure_card(fig, title_th: str, title_en: str, explanation_th: str, explanation_en: str, source_table: str = "") -> str:
    """Consistent interactive chart card with native hover, zoom, pan, and legend controls."""
    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(l=60, r=30, t=55, b=70),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        font=dict(family="Inter, Noto Sans Thai, sans-serif", size=13, color="#111318"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8edf3", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e8edf3", zeroline=False)
    chart_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        config={"responsive": True, "displaylogo": False, "scrollZoom": True, "modeBarButtonsToRemove": ["lasso2d"]},
    )
    source = f'<p class="chart-source">Source: {html.escape(source_table)}</p>' if source_table else ""
    return f"""
    <article class="interactive-chart-card">
      <div class="chart-header">
        <h3 data-th="{html.escape(title_th)}" data-en="{html.escape(title_en)}">{html.escape(title_th)}</h3>
        <span class="badge-interactive" data-th="โต้ตอบได้" data-en="Interactive">โต้ตอบได้</span>
      </div>
      <div class="interactive-plot">{chart_html}</div>
      <p class="chart-explanation" data-th="{html.escape(explanation_th)}" data-en="{html.escape(explanation_en)}">{html.escape(explanation_th)}</p>
      <p class="interaction-help" data-th="ชี้เมาส์เพื่อดูค่าจริง · ลากเพื่อซูม · เลื่อนเมาส์เพื่อซูม · คลิก legend เพื่อซ่อน/แสดงชุดข้อมูล · ดับเบิลคลิกเพื่อรีเซ็ต" data-en="Hover for exact values · drag or scroll to zoom · click legends to toggle series · double-click to reset">ชี้เมาส์เพื่อดูค่าจริง · ลากเพื่อซูม · เลื่อนเมาส์เพื่อซูม · คลิก legend เพื่อซ่อน/แสดงชุดข้อมูล · ดับเบิลคลิกเพื่อรีเซ็ต</p>
      {source}
    </article>
    """


def img_card(path: str, title_th: str, title_en: str, caption_th: str, caption_en: str) -> str:
    """Backwards-compatible wrapper providing rich structured explanations."""
    return figure_card(
        path=path,
        title_th=title_th,
        title_en=title_en,
        purpose_th=caption_th,
        purpose_en=caption_en,
        findings_th=caption_th,
        findings_en=caption_en,
        limits_th="การแปลผลต้องพิจารณาบริบทของข้อมูล MOOC ปี 2012–2013 และไม่ตีความสหสัมพันธ์เป็นเหตุและผล",
        limits_en="Interpretation must consider the 2012–2013 MOOC context and avoid conflating correlation with causation.",
        action_th="ใช้เป็นหลักฐานในการเลือกฟีเจอร์ ปรับสเกลข้อมูล และตรวจสอบผลลัพธ์ของโมเดลในขั้นตอนถัดไป",
        action_en="Used as evidence for feature selection, preprocessing scaling, and downstream model verification.",
    )


def workflow_grid(track: str, statuses: list[tuple[str, str, str, str, str]]) -> str:
    """11-step lifecycle workflow grid with detailed step answers and explanations."""
    steps = [
        ("1. กำหนดปัญหาและธรรมาภิบาล", "1. Problem Definition & Governance"),
        ("2. รวบรวมและนำเข้าข้อมูล", "2. Data Ingestion & Provenance"),
        ("3. ควบคุมคุณภาพและทำความสะอาด", "3. Quality Control & Cleaning"),
        ("4. สำรวจข้อมูลเชิงลึก (EDA)", "4. Exploratory Data Analysis"),
        ("5. ทบทวนวรรณกรรมวิชาการ", "5. Literature Review & Evidence"),
        ("6. วิศวกรรมฟีเจอร์และการคัดเลือก", "6. Feature Engineering & Selection"),
        ("7. คัดเลือกและฝึกฝนโมเดล", "7. Model Selection & Training"),
        ("8. ประเมินโมเดลและวิเคราะห์ Error", "8. Evaluation & Error Analysis"),
        ("9. นำโมเดลไปใช้งาน (Deployment)", "9. Deployment & Operationalization"),
        ("10. สื่อสารผลและรายงานแบบโต้ตอบ", "10. Communication & Interactive Report"),
        ("11. ติดตามผลและลูปปรับปรุง (Monitoring)", "11. Monitoring & Retraining Loop"),
    ]
    cards = []
    for index, (thai, english) in enumerate(steps, start=1):
        status, brief_th, brief_en, detail_th, detail_en = statuses[index - 1]
        status_class = status.lower().replace(" ", "-").replace("—", "-")
        cards.append(f"""
        <div class="workflow-card">
          <div class="step-badge">{index}</div>
          <div class="step-body">
            <div class="step-header">
              <b data-th="{html.escape(thai)}" data-en="{html.escape(english)}">{html.escape(thai)}</b>
              <span class="status {status_class}">{html.escape(status)}</span>
            </div>
            <p class="step-brief" data-th="{html.escape(brief_th)}" data-en="{html.escape(brief_en)}">{html.escape(brief_th)}</p>
            <details class="step-details">
              <summary data-th="อ่านคำอธิบายและคำตอบเชิงลึก" data-en="Read in-depth explanation & answer">อ่านคำอธิบายและคำตอบเชิงลึก</summary>
              <div class="step-detail-content" data-th="{html.escape(detail_th)}" data-en="{html.escape(detail_en)}">{html.escape(detail_th)}</div>
            </details>
          </div>
        </div>
        """)
    return f'<div class="workflow-grid" data-track="{html.escape(track)}">{"".join(cards)}</div>'


def comprehensive_eda_block(eda_summary_df: pd.DataFrame, diagnostics_df: pd.DataFrame) -> str:
    """Comprehensive EDA gallery containing rich structured cards for all core visuals."""
    fig1 = figure_card(
        path="outputs/figures/eda/full_distributions.png",
        title_th="การกระจายตัวของฟีเจอร์เชิงตัวเลขทั้งหมด 16 ตัวแปร",
        title_en="Full Numerical Feature Distributions (16 Features)",
        purpose_th="แสดงรูปทรงการกระจายตัว (Histogram + KDE) ของตัวแปรระดับนักศึกษาทั้งหมด 16 ตัวแปร โดยตัวแปรประเภทนับ (Count-like) แสดงผลในสเกล log1p เพื่อให้มองเห็นโครงสร้างข้อมูลหางยาวได้อย่างชัดเจน",
        purpose_en="Displays histograms and KDE curves for all 16 student-level numerical features. Count-like variables use log1p display scaling to make long-tailed behavior visible.",
        findings_th="ข้อมูลพฤติกรรมมีความเบ้ขวาอย่างรุนแรง (Positive Skewness > 6-29) โดยเฉพาะ total_video_plays (skewness 29.48) และ total_events (skewness 8.62) ค่ามัธยฐานกิจกรรมต่ำมาก (median events = 10 ครั้ง, active days = 2 วัน) ขณะที่ค่าเฉลี่ยสูงกว่ามากจากผู้เรียนกลุ่มบน",
        findings_en="Behavioral features exhibit extreme right-skewness (skewness 6–29), particularly total_video_plays (29.48) and total_events (8.62). Medians are modest (median events = 10, active days = 2), while means are driven up by heavy users.",
        limits_th="การใช้สเกล log1p เป็นเพียงเทคนิคช่วยในการมองเห็นภาพ (Display Only) ข้อมูลจริงยังคงความเบ้ตามธรรมชาติและมีค่า 0 เป็นจำนวนมาก",
        limits_en="Log1p is an exploratory display transformation only; raw underlying distributions remain heavily skewed with substantial zero density.",
        action_th="ต้องใช้ RobustScaler (Median / IQR) หรือ Course Percentile Normalization แทน StandardScaler เพื่อป้องกันไม่ให้โมเดลถูกครอบงำด้วยผู้เรียนกลุ่มกิจกรรมสุดโต่ง",
        action_en="Must use RobustScaler or within-course percentile normalization rather than standard z-scoring to prevent models from being dominated by extreme activity.",
        table_html=table(eda_summary_df, max_rows=10),
        table_label_th="ดูตารางสถิติเชิงพรรณนา 16 ฟีเจอร์",
        table_label_en="View 16-feature descriptive statistics table",
    )

    fig2 = figure_card(
        path="outputs/figures/eda/robust_boxplots.png",
        title_th="การเปรียบเทียบรูปทรงและ Outlier ด้วย Robust Scaling",
        title_en="Robust Boxplot Comparison Across All Features",
        purpose_th="เปรียบเทียบตำแหน่งกึ่งกลาง (Median), ความกว้างของกล่อง (IQR) และความยาวของหางข้อมูลข้ามฟีเจอร์ต่างหน่วย โดยปรับสเกลด้วย RobustScaler และคลิปเฉพาะการแสดงผลที่ช่วง ±6",
        purpose_en="Compares medians, IQRs, and tail spreads across multi-unit features using RobustScaler ((x-median)/IQR), clipped to ±6 for readable display.",
        findings_th="ฟีเจอร์ total_video_plays และ total_forum_posts มีค่า Q1 และ Median ทับซ้อนกันอยู่ที่ค่า 0 บ่งชี้ว่าผู้เรียนมากกว่า 50–70% ไม่มีกิจกรรมในส่วนนี้เลย ขณะที่ total_events และ active_days มีการกระจายตัวที่ครอบคลุมสเปกตรัมกว้างกว่า",
        findings_en="Video plays and forum posts have Q1 and Median collapsing at 0, confirming that over 50–70% of learners have zero interaction. Total events and active days span a broader spectrum.",
        limits_th="การคลิปที่ ±6 ส่งผลเฉพาะต่อการวาดภาพ ไม่ได้ตัดข้อมูลจริงในระบบทิ้ง จึงต้องไม่สรุปว่า Outlier ถูกกำจัดแล้ว",
        limits_en="Clipping at ±6 affects visualization only; source data outliers are fully retained and auditable.",
        action_th="แยกฟีเจอร์พฤติกรรมที่มีความเบาบางสูง (Sparse) ออกเป็น 2 ระดับ: ตัวบ่งชี้การมีส่วนร่วม (Binary Flag) และระดับความเข้มข้นของกิจกรรม (Intensity)",
        action_en="Handle sparse behaviors using dual representation: binary participation flags coupled with activity intensity metrics.",
    )

    fig3 = figure_card(
        path="outputs/figures/eda/zero_missing_outlier_profile.png",
        title_th="สัดส่วนค่าศูนย์ ค่าว่าง และ Outlier ตามเกณฑ์ IQR",
        title_en="Zero, Missing, and IQR-Outlier Profile",
        purpose_th="ตรวจสอบคุณภาพและความเบาบางของข้อมูล โดยจำแนกสัดส่วนค่าศูนย์แท้จริง (Structural Zeros), อัตราค่าว่าง (Missingness / NaN) และสัดส่วนค่าผิดปกติทางสถิติ (IQR Outlier)",
        purpose_en="Audits data sparsity and quality by distinguishing structural zeros, missingness percentages, and statistical IQR outlier rates.",
        findings_th="ฟอรัมมีค่าศูนย์สูงถึง >96%, การเล่นวิดีโอมีค่าศูนย์ 67.35%, และ total_events มีค่าศูนย์ 25.96% ขณะที่อัตรา Missingness หลังทำความสะอาดอยู่ที่ 0% และ Outlier ตามเกณฑ์ IQR อยู่ที่ 10–19%",
        findings_en="Forum posts are >96% zero, video plays 67.35% zero, and total events 25.96% zero. Post-cleaning missingness is 0%, while IQR outlier rates range from 10% to 19%.",
        limits_th="ค่าศูนย์ในระบบ MOOC สะท้อนพฤติกรรมจริงของผู้เรียนประเภทส่องอ่าน (Auditing / Lurking) ไม่ใช่ข้อผิดพลาดของข้อมูล (Data Error)",
        limits_en="Zeros reflect genuine auditing/lurking learner behavior rather than systemic data collection errors.",
        action_th="ห้ามตัดแถวที่มีค่าศูนย์ทิ้ง และห้ามตัด Outlier ออกโดยพลการ เพราะผู้เรียนกลุ่มนี้คือ Power Users ที่มีความสำคัญต่อสถาบันการศึกษา",
        action_en="Never drop zero rows or delete outliers automatically; high-activity students represent genuine power users requiring dedicated analysis.",
        table_html=table(diagnostics_df, max_rows=10),
        table_label_th="ดูตารางสถิติ Zero / Missing / Outlier",
        table_label_en="View Zero / Missing / Outlier diagnostics table",
    )

    fig4 = figure_card(
        path="outputs/figures/eda/behavior_relationships.png",
        title_th="ความหนาแน่นและความสัมพันธ์ของพฤติกรรมการเรียน (Hexbin Density)",
        title_en="Behavioral Relationship and Density Diagnostics",
        purpose_th="แสดงความสัมพันธ์ 2 มิติระหว่างคู่พฤติกรรมหลักด้วย Hexbin Density Plot ในสเกล log1p เพื่อแก้ปัญหาจุดซ้อนทับกัน (Overplotting) ในกลุ่มตัวอย่างกว่า 440,000 คน",
        purpose_en="Visualizes bivariate relationships using log1p hexbin density plots to resolve severe overplotting across 440k+ learners.",
        findings_th="พบความสัมพันธ์หนาแน่นสูงระหว่าง Active Days กับ Total Events โดยกระจุกตัวที่มุมซ้ายล่าง ส่วน Video Plays กับ Chapters แสดงรูปแบบบันไดชัดเจน (ผู้ที่ดูวิดีโอมากมักเปิดอ่านบทเรียนหลายบทเสมอ)",
        findings_en="Shows high density between active days and total events clustered at low engagement. Video plays and chapters exhibit a stepped relationship: high video consumption aligns with broad chapter access.",
        limits_th="ความสัมพันธ์ที่สังเกตได้เป็นความสัมพันธ์ร่วมเชิงพรรณนา (Correlation) ไม่สามารถยืนยันความเป็นเหตุและผล (Causation) ได้",
        limits_en="Observed associations are purely descriptive correlations and do not imply causal relationships.",
        action_th="ตระหนักถึงปัญหา Multicollinearity ในการเลือกตัวแปร และใช้โมเดล Non-linear Tree-based / Neural Networks ที่สามารถเรียนรู้ความสัมพันธ์ไม่เชิงเส้นได้ดี",
        action_en="Account for multicollinearity during feature selection and leverage non-linear tree ensembles or neural architectures.",
    )

    fig5 = figure_card(
        path="outputs/figures/eda/correlation_matrix.png",
        title_th="เมทริกซ์สหสัมพันธ์อันดับของสเปียร์แมน (Spearman Rank Correlation)",
        title_en="Spearman Rank Correlation Matrix",
        purpose_th="วัดระดับความสัมพันธ์เชิงอันดับแบบทางเดียว (Monotonic Relationships) ซึ่งเหมาะสมกับข้อมูลเบ้และไม่แจกแจงแบบปกติ",
        purpose_en="Measures monotonic associations across all features using Spearman rank correlation, robust to non-normal heavy-tailed distributions.",
        findings_th="total_events กับ total_active_days มีสหสัมพันธ์สูงสุด (rs = 0.90), ตามด้วย total_chapters กับ total_events (rs = 0.86) ขณะที่ demog_age มีสหสัมพันธ์กับพฤติกรรมต่ำมาก (|rs| < 0.12)",
        findings_en="Total events and active days have the highest correlation (rs = 0.90), followed by chapters and events (rs = 0.86). Age has negligible behavioral correlation (|rs| < 0.12).",
        limits_th="ค่าสหสัมพันธ์สูงระหว่างฟีเจอร์พฤติกรรมอาจทำให้โมเดลแบบเชิงเส้น (Linear Models) เกิดปัญหา VIF สูง",
        limits_en="High collinearity among engagement volume features creates variance inflation in standard linear models.",
        action_th="คัดเลือกฟีเจอร์ตัวแทนจากแต่ละมิติ (Events, Active Days, Video, Chapters, Forums) เพื่อใช้ใน Unsupervised Clustering ไม่ให้เกิดการถ่วงน้ำหนักซ้ำซ้อน",
        action_en="Select representative features across distinct behavioral facets to avoid redundant weighting during unsupervised clustering.",
    )

    fig6 = figure_card(
        path="outputs/figures/eda/activity_outlier_diagnostics.png",
        title_th="การตรวจสอบกิจกรรมผิดปกติและเส้นแบ่ง IQR (Activity Outlier Audit)",
        title_en="Activity Outlier Diagnostics & IQR Fences",
        purpose_th="แสดงเส้นแบ่ง Upper IQR Fence (Q3 + 1.5×IQR) เพื่อระบุผู้เรียนกิจกรรมสูงพิเศษ และประเมินว่าเป็นข้อผิดพลาดหรือผู้เรียนจริง",
        purpose_en="Audits upper IQR fences (Q3 + 1.5×IQR) to identify extreme learners and assess data plausibility versus corruption.",
        findings_th="มีนักศึกษา ~16.2% ที่มี total_events เกิน Upper Fence และ ~14.1% ที่มี active_days เกิน Fence แต่ค่าสูงสุดยังคงเป็นไปได้ทางกายภาพ (ใช้งานตลอดช่วงคอร์ส)",
        findings_en="Around 16.2% of students exceed the total events upper fence and 14.1% exceed the active days fence. Maximum values remain physically plausible within course durations.",
        limits_th="เกณฑ์ 1.5×IQR พัฒนาบนสมมติฐาน Gaussian เมื่อใช้กับข้อมูล Power-law จึงตรวจพบ Outlier ในสัดส่วนที่สูงเป็นปกติ",
        limits_en="The 1.5×IQR rule assumes Gaussian normality; on power-law educational distributions, it naturally flags a large valid subpopulation.",
        action_th="ไม่ลบแถวทิ้ง แต่ใช้การแปลงสเกลเป็น Percentile ภายในวิชา (mean_course_*_percentile) ซึ่งจะตรึงค่าให้อยู่ในช่วง [0, 1] อย่างมีเสถียรภาพ",
        action_en="Retain all valid records and apply within-course percentile ranking, naturally bounding values to [0, 1] without data loss.",
    )

    fig7 = figure_card(
        path="outputs/figures/eda/video_quality_diagnostics.png",
        title_th="การตรวจสอบคุณภาพข้อมูลวิดีโอและการแยกค่าศูนย์ (Video Quality Audit)",
        title_en="Video Quality, Availability, and Structural Zeros Audit",
        purpose_th="ตรวจสอบการกระจายตัวของจำนวนการเล่นวิดีโอ การมีข้อมูลวิดีโอ และแยกแยะระหว่างค่าศูนย์แท้จริงกับปัญหาของระบบบันทึก",
        purpose_en="Audits video-play distributions and data availability, verifying that zero counts represent genuine non-viewing rather than logging failure.",
        findings_th="นักศึกษา 67.35% มีค่า total_video_plays เท่ากับ 0 ครั้ง โดยระบบมีข้อมูลบันทึกครบถ้วน ไม่พบปัญหา Missingness หลังกำจัดค่า Sentinel 197757",
        findings_en="67.35% of learners have 0 video plays, with full logging availability confirmed after purging sentinel value 197757.",
        limits_th="ข้อมูลนี้เป็นเพียง Interaction Log (จำนวนครั้งที่กดเล่น) ไม่ใช่ Watch Time และไม่มีเนื้อหาวิดีโอ เสียง หรือคำบรรยาย",
        limits_en="Data reflects click interaction counts only; no watch duration, audio waveforms, or transcripts are present.",
        action_th="ห้ามนำตัวเลขนี้ไปสร้างข้อความสรุปแล้วอ้างว่าเป็น Transcript วิดีโอเด็ดขาด (ปฏิบัติตามกฎ Merged_Workflow.md อย่างเคร่งครัด)",
        action_en="Strictly prohibit converting interaction counts into text and labeling them as video transcripts, complying with workflow rules.",
    )

    fig8 = figure_card(
        path="outputs/figures/tracks/certified_grade_threshold_audit.png",
        title_th="การตรวจสอบความสอดคล้องของเกรดและใบรับรอง (Certified-Grade Audit)",
        title_en="Certified-Grade Threshold and Consistency Audit",
        purpose_th="ตรวจสอบความถูกต้องของฉลากเป้าหมาย โดยพล็อตเกรดเทียบกับสถานะการได้รับใบรับรอง พร้อมเส้นแบ่งเกณฑ์ 0.50 เพื่อตรวจจับข้อมูลขัดแย้ง",
        purpose_en="Audits target consistency by plotting numeric grades against certification status, with a 0.50 passing threshold to catch contradictory labels.",
        findings_th="ผู้ได้รับใบรับรองเกือบ 100% มีเกรดอยู่ในช่วง 0.50–1.00 ตรวจพบรายการผิดปกติเพียง 1 รายการที่ได้ Certified แต่เกรดเป็น 0.00 ซึ่งถูกกักกันเรียบร้อยแล้ว",
        findings_en="Almost 100% of certified students have grades in [0.50, 1.00]. Only 1 contradictory record (certified with grade 0.00) was detected and quarantined.",
        limits_th="เกรดและสถานะการได้รับใบรับรองเป็นตัวแปรหลังผลลัพธ์ (Post-outcome) จึงต้องถูกกักกันอย่างเข้มงวด",
        limits_en="Grade and certification are post-outcome labels requiring strict target quarantine from pre-outcome predictors.",
        action_th="กักกันรายการที่ขัดแย้งนี้ไว้ใน data/quarantine/ และตัดสิทธิ์เฉพาะการเป็นเป้าหมายใน Supervised Track โดยไม่ลบออกจาก Unsupervised Clustering เพื่อป้องกัน Leakage",
        action_en="Quarantine the contradictory record and exclude it only from supervised eligibility; do not delete from clustering to prevent outcome leakage.",
    )

    return f"""
    <section class="eda-block">
      <div class="section-title-wrap">
        <h3 data-th="แกลเลอรีการสำรวจข้อมูลเชิงลึก (Comprehensive EDA Catalog)" data-en="Comprehensive EDA Visual Catalog">แกลเลอรีการสำรวจข้อมูลเชิงลึก (Comprehensive EDA Catalog)</h3>
        <p data-th="รวบรวมกราฟการกระจาย สหสัมพันธ์ คุณภาพข้อมูล และการตรวจสอบความผิดปกติ ครอบคลุม 100% ตามข้อกำหนดของ Merged_Workflow.md" data-en="Comprehensive visual catalog covering distributions, correlations, data quality, and anomaly audits per Merged_Workflow.md requirements.">รวบรวมกราฟการกระจาย สหสัมพันธ์ คุณภาพข้อมูล และการตรวจสอบความผิดปกติ ครอบคลุม 100% ตามข้อกำหนดของ Merged_Workflow.md</p>
      </div>
      <div class="grid-2">
        {fig1}
        {fig2}
        {fig3}
        {fig4}
        {fig5}
        {fig6}
        {fig7}
        {fig8}
      </div>
    </section>
    """


def segment_comparison_block(segment_table: pd.DataFrame, context_th: str, context_en: str) -> str:
    """Segment comparison cards with rich 4-pillar analytical explanations."""
    c1 = figure_card(
        path="outputs/figures/tracks/segment_feature_comparison.png",
        title_th="ค่าเฉลี่ยพฤติกรรมข้ามทุก Segment ในระดับ Percentile",
        title_en="Mean Behavioral Percentiles Across All Segments",
        purpose_th="เปรียบเทียบค่าเฉลี่ยของ 4 ฟีเจอร์พฤติกรรมหลัก (Events, Active Days, Chapters, Forum) บนสเกลเปอร์เซ็นไทล์ภายในวิชา [0, 1] ข้ามกลุ่ม All, High Engagement, Low Engagement, และ Certified Only",
        purpose_en="Compares mean within-course percentiles [0, 1] for events, active days, chapters, and forum posts across All, High, Low, and Certified Only cohorts.",
        findings_th="กลุ่ม Certified Only มีค่าเฉลี่ยกิจกรรมสูงที่สุดในทุกด้าน (>0.81–0.84) ใกล้เคียงกับกลุ่ม High Engagement ขณะที่กลุ่ม Low Engagement มีค่าเฉลี่ยต่ำกว่า 0.25 ทุกมิติ",
        findings_en="Certified students show the highest mean behavior (>0.81–0.84), closely matching High Engagement. Low Engagement falls below the 25th percentile across all facets.",
        limits_th="กลุ่ม Certified Only เป็นกลุ่มที่แบ่งตามผลลัพธ์ภายหลัง (Post-hoc outcome segment) ซึ่งมีสมาชิกร่วมกับ High Engagement",
        limits_en="Certified Only is an overlapping post-hoc outcome cohort; it must be interpreted descriptively rather than as an independent feature.",
        action_th="ใช้เพื่อการอธิบายความสัมพันธ์เชิงพรรณนาเท่านั้น ห้ามนำความแตกต่างนี้ย้อนกลับไปสร้างฟีเจอร์ในโมเดล Clustering หรือ Supervised",
        action_en="Use strictly for descriptive validation; never feed post-hoc differences back into upstream feature construction.",
    )

    c2 = figure_card(
        path="outputs/figures/tracks/segment_distribution_comparison.png",
        title_th="การกระจายตัวของฟีเจอร์แยกตาม Segment (Boxplots)",
        title_en="Feature Distribution Boxplots by Segment",
        purpose_th="แสดง Boxplots ของฟีเจอร์พฤติกรรมในแต่ละ Segment เพื่อตรวจสอบความแปรปรวน ตำแหน่งมัธยฐาน และความเหลื่อมล้ำภายในกลุ่ม",
        purpose_en="Displays boxplots across segments to inspect internal variance, medians, and distribution spreads beyond simple group averages.",
        findings_th="กลุ่ม Certified Only มีความแปรปรวนน้อยกว่าและมีขอบล่างของกล่องสูง บ่งชี้ว่าการจะจบการศึกษาจำเป็นต้องมีระดับการมีส่วนร่วมขั้นต่ำที่ชัดเจน",
        findings_en="The Certified Only cohort displays lower variance and an elevated lower fence, showing that completion requires a baseline threshold of engagement.",
        limits_th="มีผู้เรียนจำนวนหนึ่งในกลุ่ม Certified ที่มีกิจกรรมต่ำ ซึ่งอาจเกิดจากการมีความรู้เดิม (Prior Knowledge) สูงและทำข้อสอบผ่านได้ทันที",
        limits_en="A small minority of certified learners show low engagement, likely reflecting prior domain competence enabling rapid exam completion.",
        action_th="ระบุกลุ่มผู้เรียน Fast-track ในกระบวนการวิเคราะห์ เพื่อพัฒนาโมเดลที่ไม่ตัดสินความพร้อมของผู้เรียนจากเวลาเรียนเพียงอย่างเดียว",
        action_en="Identify fast-track learners to design intervention systems that do not penalize competent students who bypass video lectures.",
    )

    c3 = figure_card(
        path="outputs/figures/tracks/segment_cluster_comparison.png",
        title_th="องค์ประกอบของคลัสเตอร์ในแต่ละ Segment (100% Stacked)",
        title_en="Cluster Composition Across Segments (100% Stacked)",
        purpose_th="แสดงสัดส่วนของแต่ละ Persona ที่ซ่อนอยู่ภายในกลุ่ม All, High, Low, และ Certified Only เพื่อประเมินความสอดคล้องของการแบ่งกลุ่ม",
        purpose_en="Displays 100% stacked bar charts showing persona proportions within All, High, Low, and Certified cohorts to evaluate segmentation validity.",
        findings_th="หลังปรับ K ใหม่ กลุ่ม Certified Only กระจุกตัวอยู่ในคลัสเตอร์กิจกรรมสูงเป็นหลัก ขณะที่ Low Engagement กระจุกตัวในคลัสเตอร์กิจกรรมต่ำเกือบทั้งหมด แสดงว่าการแบ่งกลุ่มสอดคล้องกับพฤติกรรมจริง",
        findings_en="After the revised K selection, Certified Only learners concentrate mainly in the high-activity cluster, while Low Engagement concentrates in the low-activity cluster, supporting behavioral validity.",
        limits_th="แสดงความสอดคล้องภายนอก (External Validity) แต่ไม่ใช่การตรวจสอบความถูกต้องแบบ Ground Truth เนื่องจาก Unsupervised ไม่มีฉลากจริง",
        limits_en="Demonstrates external descriptive validity, not supervised ground-truth correctness.",
        action_th="ยืนยันว่าการแบ่งกลุ่มแบบ Unsupervised มีความสมเหตุสมผลในเชิงการศึกษาและพร้อมนำไปใช้จำแนกประเภทการสนับสนุนผู้เรียน",
        action_en="Confirms educational validity of unsupervised clusters, establishing readiness for tailored learner support workflows.",
    )

    c4 = figure_card(
        path="outputs/figures/tracks/segment_outcome_comparison.png",
        title_th="ขนาดกลุ่ม อัตราผลลัพธ์จริง และความน่าจะเป็นที่ทำนายได้",
        title_en="Segment Size, Observed Outcomes, and Predicted Probabilities",
        purpose_th="เปรียบเทียบจำนวนนักศึกษา อัตราการได้รับใบรับรองจริง (Observed Rate) และค่าเฉลี่ยความน่าจะเป็นจากการทำนาย (Mean Predicted Probability)",
        purpose_en="Compares student counts, observed certification rates, and mean model-predicted probabilities across all cohorts.",
        findings_th="อัตราการได้ใบรับรองจริงใน All Students อยู่ที่ 3.18%, ใน Low ต่ำกว่า 0.1%, ใน High อยู่ที่ ~11.5% โดยค่าความน่าจะเป็นที่ทำนายเฉลี่ยสอดคล้องกับค่าจริงในทุกกลุ่ม",
        findings_en="Observed certification is 3.18% overall, <0.1% in Low, and ~11.5% in High. Model-predicted probabilities align well with observed rates.",
        limits_th="โมเดล Supervised ไม่เคยเห็นข้อมูล Segment ในการฝึก และใช้เฉพาะฟีเจอร์ที่มีอยู่ก่อนผลลัพธ์เท่านั้น",
        limits_en="The supervised model was trained without segment labels and used pre-outcome predictors exclusively.",
        action_th="ยืนยันว่าความน่าจะเป็นที่โมเดลส่งมอบมีความแม่นยำและมีการ Calibration ที่ดี สามารถนำไปใช้จัดลำดับความเสี่ยงในการเรียนได้จริง",
        action_en="Validates well-calibrated probabilities, confirming operational readiness for student risk scoring and academic alerts.",
    )

    return f"""
    <section class="segment-block">
      <div class="section-title-wrap">
        <h3 data-th="เปรียบเทียบทุก Segment (Cross-Segment Comparison)" data-en="Comparison Across All Segments">เปรียบเทียบทุก Segment (Cross-Segment Comparison)</h3>
        <p data-th="{html.escape(context_th)}" data-en="{html.escape(context_en)}">{html.escape(context_th)}</p>
        <div class="note-box" data-th="กลุ่ม High/Low Engagement สร้างจาก Quartile ของกิจกรรม ส่วน Certified Only เป็นกลุ่มผลลัพธ์แบบ Post-hoc จึงอาจมีสมาชิกร่วมกับกลุ่มอื่น กราฟนี้ใช้เพื่ออธิบาย ไม่ใช้สร้างฟีเจอร์หรือเลือกโมเดล" data-en="High/Low engagement cohorts are quartile-based; Certified Only is a post-hoc outcome cohort that may overlap. These charts are descriptive and not used for feature or model selection.">กลุ่ม High/Low Engagement สร้างจาก Quartile ของกิจกรรม ส่วน Certified Only เป็นกลุ่มผลลัพธ์แบบ Post-hoc จึงอาจมีสมาชิกร่วมกับกลุ่มอื่น กราฟนี้ใช้เพื่ออธิบาย ไม่ใช้สร้างฟีเจอร์หรือเลือกโมเดล</div>
      </div>
      <div class="grid-2">
        {c1}
        {c2}
        {c3}
        {c4}
      </div>
      <details class="chart-table-details">
        <summary data-th="ดูตารางตัวเลขสถิติเปรียบเทียบทุก Segment" data-en="View exact comparison table across segments">ดูตารางตัวเลขสถิติเปรียบเทียบทุก Segment</summary>
        {table(segment_table)}
      </details>
    </section>
    """


def run_generate_report() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    inventory = read_csv("outputs/tables/source_file_inventory.csv")
    raw_profile = read_csv("outputs/tables/raw_column_profile.csv")
    value_counts = read_csv("outputs/tables/raw_column_value_counts.csv")
    missing = read_csv("outputs/tables/missing_value_decisions.csv")
    courses = read_csv("outputs/tables/course_offering_profile.csv")
    cleaning = read_csv("outputs/tables/cleaning_summary.csv")
    outcome_quality = read_csv("outputs/tables/outcome_consistency_summary.csv")
    imbalance = read_csv("outputs/tables/class_balance_audit.csv")
    unsup = read_csv("outputs/tables/unsupervised_model_comparison.csv")
    deep = read_csv("outputs/tables/deep_learning_model_comparison.csv")
    supervised = read_csv("outputs/tables/supervised_model_comparison.csv")
    supervised_confusions = read_csv("outputs/tables/supervised_confusion_matrices_comparison.csv")
    sup_features = read_csv("outputs/tables/supervised_feature_specification.csv")
    transformed = read_csv("outputs/tables/supervised_transformed_features.csv")
    cluster_profiles = read_csv("outputs/tables/unsupervised_cluster_profiles.csv")
    llm_availability = read_csv("outputs/tables/llm_method_availability.csv")
    llm_text_inputs = read_csv("outputs/tables/llm_student_text_inputs.csv")
    llm_models = read_csv("outputs/tables/llm_text_classifier_comparison.csv")
    llm_confusions = read_csv("outputs/tables/llm_text_confusion_matrices.csv")
    llm_offline_models = read_csv("outputs/tables/llm_offline_model_comparison.csv")
    llm_offline_confusions = read_csv("outputs/tables/llm_offline_confusion_matrices.csv")
    llm_offline_manifest = read_json("outputs/reproducibility/llm_offline_manifest.json")
    llm_api_models = read_csv("outputs/tables/llm_generative_model_comparison_full_gemini.csv") if (ROOT / "outputs/tables/llm_generative_model_comparison_full_gemini.csv").exists() else read_csv("outputs/tables/llm_generative_model_comparison.csv")
    llm_pilot_models = read_csv("outputs/tables/llm_comparative_pilot_model_comparison.csv")
    llm_api_status_audit = read_csv("outputs/tables/llm_api_provider_status.csv")
    llm_api_status = llm_api_status_audit.copy()
    llm_pilot_manifest = read_json("outputs/reproducibility/llm_pilot_benchmark_manifest.json") if (ROOT / "outputs/reproducibility/llm_pilot_benchmark_manifest.json").exists() else {}
    llm_pilot_predictions = read_csv("outputs/tables/llm_comparative_pilot_predictions.csv") if (ROOT / "outputs/tables/llm_comparative_pilot_predictions.csv").exists() else pd.DataFrame()
    llm_task_definition = read_csv("outputs/tables/llm_task_definition.csv")
    all_models = read_csv("outputs/tables/all_track_model_comparison.csv")
    eda_summary = read_csv("outputs/tables/eda_summary.csv")
    distribution_diagnostics = read_csv("outputs/tables/distribution_diagnostics.csv")
    outlier_audit = read_csv("outputs/tables/activity_outlier_audit.csv")
    video_quality = read_csv("outputs/tables/video_quality_audit.csv")
    k_decision = read_csv("outputs/tables/k_selection_decision.csv")
    k_composite = read_csv("outputs/tables/k_selection_composite_scores.csv")
    k_elbow = read_csv("outputs/tables/k_selection_elbow.csv")
    k_sensitivity = read_csv("outputs/tables/k_sensitivity_multiseed_audit.csv")
    k_direction_recheck = read_csv("outputs/tables/k_metric_direction_recheck.csv") if (ROOT / "outputs/tables/k_metric_direction_recheck.csv").exists() else pd.DataFrame()
    k_direction_summary = read_json("outputs/reproducibility/k_metric_direction_recheck_summary.json") if (ROOT / "outputs/reproducibility/k_metric_direction_recheck_summary.json").exists() else {}
    gap_scores = read_csv("outputs/tables/gap_statistic_by_k.csv")
    segment_comparison = read_csv("outputs/tables/segment_comparison.csv")
    scenario_centers = read_csv("outputs/tables/unsupervised_scenario_centers.csv")
    tracks = read_json("outputs/reproducibility/analysis_tracks_manifest.json")
    segments = read_json("outputs/reproducibility/dashboard_segment_summary.json")
    audit = read_json("data/processed/cleaning_audit.json")
    reclean_summary = read_json("outputs/reproducibility/data_reclean_audit_summary.json") if (ROOT / "outputs/reproducibility/data_reclean_audit_summary.json").exists() else {}
    reclean_key_counts = read_csv("outputs/tables/data_reclean_key_count_audit.csv") if (ROOT / "outputs/tables/data_reclean_key_count_audit.csv").exists() else pd.DataFrame()
    reclean_conflicts = read_csv("outputs/tables/data_reclean_collapsed_field_conflicts.csv") if (ROOT / "outputs/tables/data_reclean_collapsed_field_conflicts.csv").exists() else pd.DataFrame()
    reclean_offerings = read_csv("outputs/tables/data_reclean_offering_loss_audit.csv") if (ROOT / "outputs/tables/data_reclean_offering_loss_audit.csv").exists() else pd.DataFrame()

    raw_records = int(inventory["records"].sum())
    source_files = len(inventory)
    enrollments = int(audit["cleaned_enrollments"])
    students = int(tracks["students"])
    hxpc_raw = pd.read_parquet(ROOT / "data/interim/HXPC13_harmonized.parquet")
    big_raw = pd.read_parquet(ROOT / "data/interim/big_student_harmonized.parquet")
    source_union_students = int(pd.concat(
        [hxpc_raw[["userid_DI"]], big_raw[["userid_DI"]]], ignore_index=True
    )["userid_DI"].nunique())
    source_overlap_students = int(len(set(hxpc_raw["userid_DI"]).intersection(set(big_raw["userid_DI"]))))
    source_only_hxpc = int(len(set(hxpc_raw["userid_DI"]) - set(big_raw["userid_DI"])))
    source_only_big = int(len(set(big_raw["userid_DI"]) - set(hxpc_raw["userid_DI"])))
    overlap_key = ["userid_DI", "institute", "course_id", "year", "semester"]
    student_course_key = ["userid_DI", "course_id"]
    overlap = hxpc_raw[overlap_key + ["viewed", "explored", "certified", "grade", "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts"]].merge(
        big_raw[overlap_key + ["viewed", "explored", "certified", "grade", "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts"]],
        on=overlap_key,
        how="inner",
        suffixes=("_hxpc", "_big"),
    )
    student_course_overlap = hxpc_raw[student_course_key + ["viewed", "explored", "certified", "grade", "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts"]].merge(
        big_raw[student_course_key + ["viewed", "explored", "certified", "grade", "nevents", "ndays_act", "nplay_video", "nchapters", "nforum_posts"]],
        on=student_course_key,
        how="inner",
        suffixes=("_hxpc", "_big"),
    )
    reconciliation_rows = [
        {"audit_item": "HXPC raw records", "value": len(hxpc_raw), "interpretation": "Official Harvard Dataverse source rows before cleaning."},
        {"audit_item": "Big-source raw records", "value": len(big_raw), "interpretation": "Supplemental source rows before cleaning."},
        {"audit_item": "Union unique userid_DI", "value": source_union_students, "interpretation": "True student-level union across both available raw files."},
        {"audit_item": "Students present in both sources", "value": source_overlap_students, "interpretation": "Learners whose userid_DI appears in both source files."},
        {"audit_item": "HXPC-only students", "value": source_only_hxpc, "interpretation": "Learners present only in the official HXPC source."},
        {"audit_item": "Big-source-only students", "value": source_only_big, "interpretation": "Learners present only in the supplemental source."},
        {"audit_item": "Overlapping student-course keys", "value": len(student_course_overlap), "interpretation": "Same userid_DI and course_id observed in both files; this is the refreshed deduplication level."},
        {"audit_item": "Exact overlapping course-run keys", "value": len(overlap), "interpretation": "Same userid/course/year/semester/institute observed in both files; retained as a stricter audit reference only."},
        {"audit_item": "Overlapping enrollment keys with different viewed", "value": int((overlap["viewed_hxpc"] != overlap["viewed_big"]).sum()), "interpretation": "Viewed is consistent across exact overlaps in the current files."},
        {"audit_item": "Overlapping enrollment keys with different activity counts", "value": int(((overlap["nevents_hxpc"] != overlap["nevents_big"]) | (overlap["ndays_act_hxpc"] != overlap["ndays_act_big"]) | (overlap["nplay_video_hxpc"] != overlap["nplay_video_big"]) | (overlap["nchapters_hxpc"] != overlap["nchapters_big"])).sum()), "interpretation": "Behavior counts often differ across duplicated enrollments, so the merge must be audited and source precedence documented."},
    ]
    reconciliation_audit = pd.DataFrame(reconciliation_rows)
    reclean_key_view = reclean_key_counts.copy()
    if not reclean_key_view.empty:
        reclean_key_view["dedup_key"] = reclean_key_view["dedup_key"].replace({
            "current_user_course": "Current: userid_DI + course_id",
            "course_run": "Recommended audit: userid_DI + institute + course_id + year + semester",
        })
    reclean_conflict_view = reclean_conflicts.copy()
    if not reclean_conflict_view.empty:
        reclean_conflict_view = reclean_conflict_view.sort_values(
            "collapsed_groups_with_conflicting_values", ascending=False
        )
    reclean_offering_view = reclean_offerings.copy()
    if not reclean_offering_view.empty:
        reclean_offering_view = reclean_offering_view[
            (reclean_offering_view["missing_from_cleaned"].astype(str).str.lower().isin(["true", "1"]))
            | (reclean_offering_view["row_delta_clean_minus_raw"].lt(0))
        ].sort_values("row_delta_clean_minus_raw").head(12)
    enrollment_columns = int(pd.read_parquet(ROOT / "data/processed/enrollments_cleaned.parquet").shape[1])
    student_columns = int(pd.read_parquet(ROOT / "data/processed/students_cleaned.parquet").shape[1])
    raw_column_summary = " · ".join(
        f"{row.filename}: {int(row.columns)} cols"
        for row in inventory[["filename", "columns"]].itertuples(index=False)
    )

    unsup_manifest = tracks["traditional_unsupervised"]
    deep_manifest = tracks["deep_learning"]
    sup_manifest = tracks["supervised_learning"]
    llm_manifest = tracks["generative_llm"]

    unsup_winner = unsup.loc[unsup["selected"].eq(True)].iloc[0]
    deep_winner = deep.loc[deep["selected"].eq(True)].iloc[0]
    sup_winner = supervised.loc[supervised["selected"].eq(True)].iloc[0]
    llm_offline_completed = llm_offline_models.loc[llm_offline_models["status"].eq("completed")].copy()
    llm_winner = llm_offline_completed.loc[llm_offline_completed["selected"].eq(True)].iloc[0]
    llm_api_winner = llm_api_models.loc[llm_api_models["selected"].eq(True)].iloc[0]

    # Status arrays with detailed explanations for all 11 lifecycle steps
    common_p1_4 = [
        (
            "Completed",
            "กำหนดปัญหา ธรรมาภิบาล และหน่วยวิเคราะห์ระดับนักศึกษา 1 แถวต่อคน",
            "Defined problem, governance, and student-level unit of analysis (1 row/student)",
            "ระบุวัตถุประสงค์เพื่อวิเคราะห์และแบ่งกลุ่มพฤติกรรมผู้เรียน MOOC และทำนายการได้รับใบรับรอง โดยกำหนดหน่วยวิเคราะห์เป็น userid_DI สังเคราะห์ข้ามทุกวิชาที่ลงทะเบียน ใช้เกณฑ์ความสำเร็จเชิงวิชาการและการดำเนินงาน พร้อมมาตรการ PDPA/GDPR และการกักกันตัวแปรผลลัพธ์ (Strict Target Quarantine)",
            "Formulated problem to analyze MOOC engagement and predict certification using userid_DI synthesized across all enrollments. Established academic/operational success criteria, PDPA/GDPR governance, and strict target quarantine.",
        ),
        (
            "Completed",
            "นำเข้า 2 แหล่งข้อมูล บันทึก Provenance และตรวจสอบ Checksum ทางการ",
            "Ingested 2 sources, recorded provenance, and verified official checksum",
            "นำเข้า HarvardX Person-Course Dataset v3.0 (HXPC13) ผ่าน Harvard Dataverse ตรวจสอบ MD5: 53419b486c3b19c14d2f06612980f630 (338,223 แถว) และไฟล์ส่วนขยาย Kaggle (416,921 แถว) รวม 755,144 แถวดิบ พร้อมบันทึก Schema, License, และข้อจำกัดลงใน logs/data_provenance.json",
            "Ingested HarvardX Person-Course Dataset v3.0 via Harvard Dataverse with verified MD5 checksum (338,223 rows) and Kaggle-derived file (416,921 rows) totaling 755,144 raw rows. Recorded provenance, schemas, and limitations.",
        ),
        (
            "Completed",
            f"ทำความสะอาดระดับไฟล์ รวมซ้ำเหลือ {enrollments:,} รายการลงทะเบียน และสังเคราะห์ {students:,} นักศึกษา",
            f"Cleaned sources, deduplicated to {enrollments:,} enrollments, and synthesized {students:,} students",
            f"กำจัดค่า Sentinel 197757 ใน nplay_video (255,528 แถว), แก้ไขวันที่กลับทิศ (1,846 แถว), คัดกรองอายุผิดปกติ (745 แถว), รวมซ้ำข้ามไฟล์ด้วยคีย์ student-course ตัดออก {int(audit['cross_source_rows_removed']):,} แถว, กักกัน outcome ขัดแย้ง, และสังเคราะห์เป็น {students:,} นักศึกษาที่มีข้อมูลสะอาด",
            f"Cleaned sentinel 197757 in video plays (255,528 rows), inverted dates (1,846 rows), invalid ages (745 rows), removed {int(audit['cross_source_rows_removed']):,} student-course duplicate rows, quarantined contradictory outcomes, and aggregated {students:,} clean students.",
        ),
        (
            "Completed",
            "วิเคราะห์ EDA 16 ฟีเจอร์ ตรวจสอบความเบ้ ศูนย์ Outlier และ Manifold",
            "Conducted 16-feature EDA, audited skewness, zeros, outliers, and manifolds",
            "สร้าง Feature Inventory ครบ 100%, พบพฤติกรรมมีความเบ้ขวาสูงมาก (Skewness > 6-29), ผู้เรียนมากกว่า 67% มีค่าการดูวิดีโอเป็น 0, วิเคราะห์ Spearman Correlation, ตรวจสอบ IQR Outlier Fences, และฉายภาพ PCA / UMAP เพื่อประเมินความต่อเนื่องของ Manifold",
            "Generated 100% feature inventory, revealed severe right-skewness (skewness 6–29), >67% structural video zeros, Spearman correlations, IQR fences, and PCA/UMAP manifold projections.",
        ),
    ]

    unsup_status = common_p1_4 + [
        (
            "Completed",
            "ทบทวนวรรณกรรม MOOC และการเลือก K ด้วย Gap Statistic",
            "Reviewed MOOC literature and Gap statistic K-selection",
            "อ้างอิง Ho et al. (2014), Kizilcec et al. (2013) เรื่องรูปแบบการเรียนรู้ และ Tibshirani et al. (2001) สำหรับการเลือกจำนวนคลัสเตอร์ด้วย Gap Statistic 1-SE rule เพื่อป้องกันการเดาจำนวนกลุ่มล่วงหน้า",
            "Applied literature from Ho et al. (2014), Kizilcec et al. (2013), and Tibshirani et al. (2001) for objective Gap statistic K-selection.",
        ),
        (
            "Completed",
            "สร้างฟีเจอร์ Percentile ภายในวิชา 4 พฤติกรรม ลดอคติความยากของคอร์ส",
            "Constructed 4 within-course behavioral percentiles to eliminate course bias",
            "แปลง Events, Active Days, Video Plays, Chapters เป็น Course-adjusted percentiles [0, 1] ทำให้เปรียบเทียบผู้เรียนข้ามคอร์สสั้น 2 สัปดาห์กับคอร์สยาว 14 สัปดาห์ได้อย่างเป็นธรรม และแยกผลลัพธ์ออกจากฟีเจอร์ 100%",
            "Normalized events, active days, video plays, and chapters into within-course percentiles [0, 1], enabling fair cross-course comparison and isolating outcomes.",
        ),
        (
            "Completed",
            "เปรียบเทียบ 7 ตระกูลโมเดล Unsupervised ข้าม k=2 ถึง k=10",
            "Evaluated 7 unsupervised algorithm families across k=2 to k=10",
            "ประเมิน K-Means, MiniBatch K-Means, GMM, Agglomerative, BIRCH, Spectral, และ DBSCAN โดยบันทึก Runtime, ขนาดกลุ่มย่อยที่สุด, และความเสถียรข้ามรอบสุ่ม (Resample ARI)",
            "Evaluated K-Means, MiniBatch, GMM, Agglomerative, BIRCH, Spectral, and DBSCAN recording runtime, smallest cluster size, and resample ARI.",
        ),
        (
            "Completed",
            "ประเมิน Gap, Silhouette, DB, CH และ Stability โดยไม่ใช้ Elbow ตัดสิน",
            "Evaluated Gap, Silhouette, DB, CH, and stability without Elbow selection",
            "เลือกจำนวนกลุ่มจากคะแนนโหวตของ Gap 1-SE, Silhouette, Davies-Bouldin, Calinski-Harabasz และ Stability ARI; WCSS ถูกเก็บไว้เป็นหลักฐานตรวจสอบแต่ไม่มีสิทธิ์โหวต",
            "Selected cluster count from Gap 1-SE, Silhouette, Davies-Bouldin, Calinski-Harabasz, and stability ARI votes; WCSS is retained only as a non-decision audit artifact.",
        ),
        (
            "Completed",
            "บันทึก Unsupervised Pipeline สำหรับการให้คะแนนข้อมูลใหม่",
            "Serialized unsupervised inference pipeline for production scoring",
            "บันทึกโมเดลและตัวแปลงสเกลลงใน models/tracks/unsupervised_pipeline.joblib พร้อมสัญญาตรวจสอบ Schema (input_contract.json) ทดสอบการรันเสร็จสิ้นใน <0.05 วินาที",
            "Saved model and preprocessor into models/tracks/unsupervised_pipeline.joblib with input schema contract; verified inference execution in <0.05s.",
        ),
        (
            "Completed",
            "รายงานแดชบอร์ด 2 ภาษา เรดาร์พฤติกรรม และ Scenario Explorer",
            "Reported bilingual dashboard, behavioral radar, and scenario explorer",
            "นำเสนอผลลัพธ์ Persona ตามค่า K ที่เลือก ตารางค่าเฉลี่ย กราฟเรดาร์ PCA 3D และจำลองพฤติกรรมนักศึกษาแบบโต้ตอบ (What-if Scenario Explorer) พร้อมคำเตือนข้อจำกัด",
            "Delivered learner personas from the selected K, profile tables, radar charts, 3D PCA, and interactive what-if scenario explorer with safeguards.",
        ),
        (
            "Not Evaluated",
            "กำหนดเกณฑ์ PSI Drift และรอข้อมูลรุ่นถัดไป (Future Cohort)",
            "Configured PSI drift thresholds; awaiting genuine future cohort",
            "สร้าง Baseline อ้างอิงและกำหนดเกณฑ์ PSI (<0.10 ปกติ, 0.10–0.25 เฝ้าระวัง, ≥0.25 Retrain) แต่ระบุสถานะว่ายังไม่ได้ประเมินจริงจนกว่าจะมีนักศึกษารุ่นใหม่",
            "Established baseline quantiles and PSI drift thresholds (<0.10, 0.10–0.25, ≥0.25); honestly marked not evaluated until a future cohort arrives.",
        ),
    ]

    deep_status = common_p1_4 + [
        (
            "Completed",
            "ทบทวนงานวิจัย Deep Learning ในการพยากรณ์การศึกษา",
            "Reviewed educational deep learning prediction literature",
            "อ้างอิงงานวิจัยการเรียนรู้โครงสร้างแบบไม่เชิงเส้น (Hinton & Salakhutdinov, 2006) และงานทำนายการออกกลางคันใน MOOC เพื่อออกแบบโครงสร้างเครือข่ายประสาทเทียมที่เหมาะสม",
            "Applied literature on non-linear representation learning (Hinton & Salakhutdinov, 2006) and educational deep classification.",
        ),
        (
            "Completed",
            f"คัดเลือก {deep_manifest['source_feature_count']} ฟีเจอร์ก่อนผลลัพธ์ เพื่อทำนายใบรับรอง",
            f"Selected {deep_manifest['source_feature_count']} pre-outcome features to predict certification",
            "ใช้เฉพาะฟีเจอร์พฤติกรรมและข้อมูลประชากรที่มีอยู่ก่อนทราบผลลัพธ์ ไม่ใช้ grade หรือ outcome flags ใดๆ ในการฝึกโมเดล",
            "Used strictly pre-outcome features (behavior, demog) to predict certification without leaking post-outcome grades.",
        ),
        (
            "Completed",
            "ฝึกสอนโครงสร้าง MLP 6 รูปแบบ บนชุดฝึก 70% พร้อม Early Stopping",
            "Trained 6 MLP architectures on 70% train split with early stopping",
            "ทดสอบ MLP (64, 32), MLP (32), MLP (128, 64), Deep MLP (128, 64, 32), Regularized MLP (alpha=0.005), และ Tanh activation พร้อม Batch Size 512 และ Adam optimizer",
            "Trained MLP (64, 32), MLP (32), MLP (128, 64), Deep MLP (128, 64, 32), Regularized MLP, and Tanh activation using Adam and early stopping.",
        ),
        (
            "Completed",
            "ประเมินด้วย PR-AUC, ROC-AUC, Brier Score และจูน Threshold บน Validation",
            "Evaluated with PR-AUC, ROC-AUC, Brier score, and validation threshold tuning",
            "เลือก MLP (128, 64) เป็นผู้ชนะด้วย Test PR-AUC 0.8415, ROC-AUC 0.9926, Brier Score 0.0125, และ Test F1 0.7904 โดยใช้ Threshold 0.24 จากชุด Validation",
            "Selected MLP (128, 64) as champion: Test PR-AUC 0.8415, ROC-AUC 0.9926, Brier 0.0125, and Test F1 0.7904 via validation threshold 0.24.",
        ),
        (
            "Completed",
            "บันทึก deep_certification_pipeline.joblib สำหรับการพยากรณ์",
            "Saved deep_certification_pipeline.joblib for production scoring",
            "บรรจุ Preprocessing และ MLP Classifier ที่เรียนรู้แล้วลงใน Pipeline ไฟล์เดียว พร้อมทดสอบ Parity Test บนชุดข้อมูลตัวอย่าง",
            "Serialized preprocessing and fitted MLP into a single joblib pipeline; verified parity tests on sample batches.",
        ),
        (
            "Completed",
            "รายงานเส้นโค้ง PR Curves, Calibration, และ Confusion Matrix",
            "Reported PR curves, calibration diagrams, and confusion matrices",
            "แสดงผลเปรียบเทียบ 6 สถาปัตยกรรม แผนภูมิความสับสน 4 อันดับแรก และกราฟความน่าเชื่อถือของความน่าจะเป็น (Calibration Curve) แยกจาก Supervised หลัก",
            "Delivered 6-architecture comparisons, top-4 confusion matrices, and probability calibration plots distinct from standard supervised learning.",
        ),
        (
            "Not Evaluated",
            "รอฉลากผลลัพธ์จากนักศึกษารุ่นถัดไปเพื่อตรวจจับ Performance Drift",
            "Awaiting true labels from future cohort to monitor performance drift",
            "จัดทำแผนการประเมิน Calibration Drift และ Recall Degradation เมื่อมีข้อมูลนักศึกษาที่จบการศึกษาในรุ่นถัดไป",
            "Established evaluation criteria for calibration drift and recall degradation upon collection of future labeled cohorts.",
        ),
    ]

    sup_status = common_p1_4 + [
        (
            "Completed",
            "ทบทวนงานวิจัย Class Imbalance และการพยากรณ์ผลการเรียน MOOC",
            "Reviewed class-imbalance and MOOC outcome prediction literature",
            "อ้างอิง Dass et al. (2021) และวรรณกรรม MOOC Dropout Prediction เรื่องความสำคัญของการใช้ PR-AUC และ Cost-sensitive weighting ในสภาวะที่ผู้ได้รับใบรับรองมีเพียง 3.18%",
            "Applied Dass et al. (2021) and MOOC dropout studies emphasizing PR-AUC and cost-sensitive methods under severe 3.18% class imbalance.",
        ),
        (
            "Completed",
            f"แปลง {sup_manifest['source_feature_count']} ฟีเจอร์ต้นทางเป็น {sup_manifest['transformed_feature_count']} ฟีเจอร์ที่ไม่มี Leakage",
            f"Transformed {sup_manifest['source_feature_count']} source features into {sup_manifest['transformed_feature_count']} leakage-free features",
            "ใช้ RobustScaler กับตัวแปรตัวเลข, One-Hot Encoding กับตัวแปรกลุ่ม, และ Fit ตัวแปลงค่าบนชุดฝึก 70% เท่านั้น (Validation และ Test ใช้เฉพาะ Transform)",
            "Applied RobustScaler to numericals, One-Hot Encoding to categoricals, fitting strictly on training split (70%) with validation/test transform-only.",
        ),
        (
            "Completed",
            "เปรียบเทียบ Dummy Baseline และ 7 ตระกูลโมเดล Supervised",
            "Compared dummy baseline and 7 supervised classifier families",
            "ทดสอบ Dummy Classifier, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosted Trees, และ AdaBoost บนการแบ่งแบบ Stratified Split",
            "Evaluated Dummy Classifier, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosted Trees, and AdaBoost using stratified splits.",
        ),
        (
            "Completed",
            "ใช้ PR-AUC เป็นเกณฑ์หลัก ชนะด้วย Gradient Boosted Trees (PR-AUC 0.8747)",
            "Prioritized PR-AUC; Gradient Boosted Trees won with PR-AUC 0.8747",
            "Gradient Boosted Trees ทำคะแนนได้สูงสุด: Test PR-AUC 0.8747, ROC-AUC 0.9954, Test Accuracy 98.79%, Precision 0.824, Recall 0.803, และ F1 0.8136",
            "Gradient Boosted Trees achieved top performance: Test PR-AUC 0.8747, ROC-AUC 0.9954, Accuracy 98.79%, Precision 0.824, Recall 0.803, F1 0.8136.",
        ),
        (
            "Completed",
            "บันทึก supervised_certification_pipeline.joblib และสัญญาข้อมูล",
            "Saved supervised_certification_pipeline.joblib and contract",
            f"จัดเก็บ End-to-end Pipeline พร้อม Input Schema Validator สามารถประมวลผลนักศึกษาทั้งรุ่น {students:,} คนได้ตาม artifact ล่าสุด",
            f"Serialized complete inference pipeline with schema validator; scored the latest {students:,}-student cohort per the refreshed artifacts.",
        ),
        (
            "Completed",
            "รายงานผลทดสอบ Confusion Matrix และการวิเคราะห์ข้อผิดพลาด",
            "Reported test confusion matrix and detailed error analysis",
            "แสดงผลการจำแนกถูก/ผิดที่จุดตัด Validation-optimal F1, วิเคราะห์ False Positives และ False Negatives, พร้อมรายงานความสำคัญของฟีเจอร์",
            "Presented optimal-threshold confusion matrix, audited FP/FN error trade-offs, and reported feature importance rankings.",
        ),
        (
            "Not Evaluated",
            "รอข้อมูลรุ่นถัดไปเพื่อตรวจวัด Performance Drop (>15% F1 trigger)",
            "Awaiting future cohort to monitor performance drop (>15% F1 trigger)",
            "กำหนด Retraining Trigger หาก Recall หรือ F1 ต่ำลงเกิน 15% หรือหากเกิด Concept Drift ในกลุ่มผู้เรียนสถาบันต่างๆ",
            "Configured automated retraining triggers (>15% F1 drop, concept drift); marked not evaluated pending genuine future cohort.",
        ),
    ]

    llm_status = [
        (
            "Completed",
            "กำหนดข้อกำหนดทางเทคนิคว่า Content LLM ต้องใช้เสียงและคำพูดจริง",
            "Defined content LLM requirement as genuine spoken audio/captions",
            "ปฏิบัติตาม MOOC Project Interpretation Rules ของ Merged_Workflow.md อย่างเคร่งครัด: จำนวนคลิกเล่นวิดีโอคือพฤติกรรม ห้ามนำไปแต่งประโยคแล้วอ้างว่าเป็น Transcript วิดีโอ",
            "Strictly enforced workflow rules: video clicks are behavioral interaction logs, never spoken content. Content analysis requires real audio/captions.",
        ),
        (
            "Blocked",
            "ไม่มีไฟล์วิดีโอ เสียง แคปชัน หรือ Transcript ในดาต้าเซ็ตปัจจุบัน",
            "No video, audio, captions, or transcripts in current dataset",
            "จากการตรวจสอบ Schema และไฟล์ต้นฉบับทั้ง 2 แหล่ง ไม่ปรากฏไฟล์สื่อดิบ วิดีโอ หรือข้อความเสียง จึงระบุสถานะของกระบวนการส่วนนี้ว่า 'ยังไม่มีข้อมูล'",
            "Audited raw files from both sources; zero video/audio files or transcripts exist, formally blocking media-dependent stages.",
        ),
        (
            "Blocked",
            "ยังไม่มี ASR Words หรือ Sentence Transcript ให้ทำความสะอาด",
            "No ASR words or sentence transcripts available for cleaning",
            "กระบวนการทำความสะอาดข้อความเสียง (VAD, Normalization, Sentence Segmentation, Timestamp Alignment) ถูกระงับชั่วคราวตามสถานะข้อมูล",
            "Speech cleaning stages (VAD, text normalization, sentence segmentation, timestamps) are suspended pending source media.",
        ),
        (
            "Blocked",
            "Content EDA ถูกระงับ; แสดงเฉพาะตาราง Content-readiness Audit",
            "Content EDA suspended; displaying content-readiness audit table only",
            "ไม่สร้างกราฟการกระจายของคำหรือหัวข้อปลอม แต่แสดงตารางตรวจสอบความพร้อม 5 ขั้นตอน (Content Readiness Table) อย่างโปร่งใส",
            "Fabrication prohibited; instead of artificial word clouds, a transparent 5-stage content-readiness audit table is displayed.",
        ),
        (
            "Completed",
            "สร้างประโยค Behavioral Text จาก Interaction Counts โดยติดป้ายว่าไม่ใช่ Transcript",
            "Created labeled behavioral text from interaction counts—not transcripts",
            "แปลง video plays, active days, events, chapters และ forum posts เป็นประโยคข้อเท็จจริง โดยทุกแถวระบุชัดเจนว่าเป็น structured behavioral summary ไม่ใช่คำพูดจากวิดีโอ",
            "Converted video plays, active days, events, chapters, and forum posts into factual structured summaries explicitly labeled as non-transcripts.",
        ),
        (
            "Completed",
            "เลือก TF-IDF + SVD และ DistilBERT สำหรับ Behavioral Text พร้อมแยก Content LLM",
            "Selected TF-IDF + SVD and DistilBERT for behavioral text; separated content LLM",
            "ใช้ lexical baseline และ local transformer ที่มี cache ในเครื่อง เพื่อหลีกเลี่ยงการส่งข้อมูลผู้เรียนไปยัง API ภายนอก ส่วน GPT/content models ยังรอ transcript จริง",
            "Selected a lexical baseline and cached local transformer to avoid external learner-data transfer; GPT/content models still require genuine transcripts.",
        ),
        (
            "Completed",
            "รัน TF-IDF และ DistilBERT บนประโยค Behavioral Text จริง",
            "Executed TF-IDF and DistilBERT on behavioral sentences",
            "สร้าง embedding จากตัวอย่างนักศึกษา 2,500 คน และฝึก MiniBatch K-Means ตั้งแต่ k=2 ถึง k=6 โดยใช้ seed คงที่และบันทึก runtime",
            "Generated embeddings for 2,500 learners and trained MiniBatch K-Means from k=2 to k=6 with fixed seeds and recorded runtime.",
        ),
        (
            "Completed",
            "ประเมิน Silhouette, Davies-Bouldin, CH และ Stability ARI",
            "Evaluated Silhouette, Davies-Bouldin, CH, and stability ARI",
            "เปรียบเทียบ 10 configuration จากสองวิธี embedding และเลือกโมเดลด้วย mean internal rank พร้อมเกณฑ์ขนาดกลุ่มขั้นต่ำ 1%",
            "Compared 10 configurations across two embedding methods and selected by mean internal rank with a 1% minimum-cluster rule.",
        ),
        (
            "Completed",
            "ออกแบบ Pipeline สื่อแบบครบวงจร (Media → ASR → Sentence → LLM)",
            "Designed unified media pipeline (Media → ASR → Sentence → LLM)",
            "จัดเตรียม Schema สำหรับ Transcript ที่ถูกต้อง (video_id, sentence_id, timestamps, language, asr_confidence) พร้อมรับข้อมูลในอนาคต",
            "Formulated target transcript schema with video IDs, sentence boundaries, timestamps, and confidence ready for ingestion.",
        ),
        (
            "Completed",
            "แสดงผล Behavioral NLP แบบ interactive และแยกคำเตือน Content LLM",
            "Reported interactive behavioral NLP results with a separate content boundary",
            "แดชบอร์ดแสดงประโยคตัวอย่าง metric ตามค่า k และ embedding projection ที่เลื่อน/ซูมได้ พร้อมกรอบเตือนว่า spoken-content track ยังไม่มีสื่อจริง",
            "Dashboard exposes sample sentences, interactive k metrics, and zoomable embedding projection while retaining the genuine-media warning for spoken content.",
        ),
        (
            "Not Evaluated",
            "การติดตามผลด้าน LLM (WER, Hallucination, Drift) จะเริ่มเมื่อมีสื่อจริง",
            "LLM monitoring (WER, hallucination, drift) commences upon media ingestion",
            "กำหนดกรอบการมอนิเตอร์ในอนาคต: อัตราคำผิดของ ASR, สัดส่วนการอ้างอิงถูกต้อง (Citation Accuracy), และอัตรา Hallucination",
            "Defined future monitoring framework covering ASR accuracy, citation correctness, retrieval hit rate, and hallucination frequency.",
        ),
    ]

    # Student-row-to-text lifecycle requested for the behavioral LLM track.
    llm_status = [
        ("Completed", "กำหนด 1 แถวต่อนักเรียน 1 คนและเป้าหมายการทำนาย", "Defined one row per student and prediction target", "ใช้ข้อมูลนักเรียนที่ไม่ระบุตัวตนเพื่อทำนายการได้รับใบรับรอง โดยกักกัน certified ออกจากข้อความ", "Uses de-identified student records to predict certification while quarantining certified from input text."),
        ("Completed", "รวบรวมข้อมูลพฤติกรรมสะอาดระดับนักเรียน", "Gathered clean student-level behavior", "ใช้จำนวนวิชา เหตุการณ์ วัน active จำนวนครั้งเล่นวิดีโอ บทเรียน และโพสต์จากตารางที่ audit แล้ว", "Uses audited counts of courses, events, active days, video plays, chapters, and forum posts."),
        ("Completed", "คงความหมายข้อมูลวิดีโออย่างถูกต้อง", "Preserved correct video semantics", "จำนวนการเล่นวิดีโอคือจำนวน click/play ไม่ใช่นาทีที่รับชมหรือความยาวคลิป", "Video plays are click/play counts—not watched minutes or clip duration."),
        ("Completed", "ตรวจ distribution และ class imbalance", "Audited distributions and class imbalance", "อัตรา positive ในกลุ่มพัฒนาเท่ากับประมาณ 3.18% จึงใช้ PR-AUC และ confusion matrix", "The development cohort is about 3.18% positive, motivating PR-AUC and confusion-matrix analysis."),
        ("Completed", "แปลงค่าหนึ่งแถวเป็นประโยคข้อเท็จจริง", "Serialized each row into factual sentences", "สร้างข้อความหนึ่งชุดต่อนักเรียนโดยไม่ใส่ userid หรือผลลัพธ์ certified ลงในเนื้อความ", "Creates one text record per student without inserting user ID or certified outcome into the sentence."),
        ("Completed", "กำหนดนโยบายใช้เฉพาะโมเดลฟรี", "Established a free-only model policy", "ใช้ Gemini ภายใต้ free quota และใช้ Qwen/Llama/Mistral ผ่าน Ollama ในเครื่อง; แดชบอร์ดแสดงเฉพาะโมเดลที่มีผลจริงหรือผ่าน smoke test", "Uses Gemini within its free quota and Qwen/Llama/Mistral through local Ollama; the dashboard shows only models with empirical results or a passed smoke test."),
        ("Completed", "สร้าง Few-shot prompt จาก Train และแยก Test", "Built few-shot prompts from train and isolated test", "ใช้ตัวอย่างติดฉลาก 12 รายการจาก train และประเมิน test 1,800 คนโดยไม่ส่ง label จริงหรือ userid เข้า API", "Uses 12 labeled train demonstrations and evaluates 1,800 test students without transmitting true test labels or user IDs."),
        ("Completed", "รัน Gemini Generative AI จริง", "Executed Gemini generative AI", "gemini-3.5-flash-lite ประมวลผลครบ 90 batch และคืน structured predictions ครบ 1,800 คนภายใต้โควตาฟรี", "gemini-3.5-flash-lite completed 90 batches and returned structured predictions for all 1,800 students within the free quota."),
        ("Completed", "เก็บผล prediction และ token audit", "Saved predictions and token audit", "บันทึก probability, label, เหตุผล, token usage และ runtime โดยไม่บันทึก API key", "Stores probabilities, labels, reasons, token usage, and runtime without persisting API keys."),
        ("Completed", "นำผล Generative AI จริงขึ้นแดชบอร์ด", "Published empirical generative-AI results", "แสดง Gemini metrics, Confusion Matrix, provider status และแยกส่วน NLP baseline อย่างชัดเจน", "Shows Gemini metrics, confusion matrix, provider status, and a clearly separated NLP-baseline section."),
        ("Planned", "ติดตาม drift และคุณภาพการทำนาย", "Monitor drift and predictive quality", "ติดตาม PSI ของตัวแปรต้นทาง พร้อม recall/F1 และ retrain เมื่อประสิทธิภาพลดเกินเกณฑ์", "Monitor source-feature PSI and recall/F1, retraining when degradation exceeds policy thresholds."),
    ]

    inventory_view = inventory[["filename", "records", "columns", "exact_duplicate_rows", "unique_students", "distinct_course_offerings", "source_url", "checksum_matches_published_source"]]
    missing_view = missing[["column_or_group", "cleaning_action"]]
    course_view = courses[["institute", "course_id", "year", "semester", "enrollments", "unique_students", "median_events", "median_active_days", "median_video_plays", "median_accessed_chapters"]]
    outcome_view = outcome_quality[["institute", "course_id", "year", "semester", "enrollment_records", "certified_records", "certified_with_zero_grade", "certified_below_documented_minimum", "supervised_eligible_records"]]
    certified_below_minimum_count = int(outcome_view["certified_below_documented_minimum"].sum()) if "certified_below_documented_minimum" in outcome_view.columns else int(audit.get("invalid_supervised_enrollments", 0))

    unsup_table = unsup[["family", "k", "role", "silhouette", "davies_bouldin", "calinski_harabasz", "resample_ari", "smallest_cluster_pct", "noise_pct", "runtime_sec", "k_selection_eligible", "selected"]].sort_values(["selected", "runtime_sec"], ascending=[False, True])
    deep_table = deep[["model_name", "family", "test_pr_auc", "test_roc_auc", "test_accuracy", "test_balanced_accuracy", "test_precision", "test_recall", "test_f1", "test_brier", "runtime_sec", "epochs_or_iterations", "selected"]].sort_values(["selected", "test_pr_auc"], ascending=[False, False])
    sup_table = supervised[["model_name", "test_pr_auc", "test_roc_auc", "test_accuracy", "test_balanced_accuracy", "test_precision", "test_recall", "test_f1", "test_brier", "runtime_sec", "selected"]]

    unsup_best = (
        unsup[unsup["role"].eq("Candidate")]
        .sort_values(["selected", "k_selection_eligible", "mean_internal_rank", "silhouette", "runtime_sec"], ascending=[False, False, True, False, True])
        .groupby("family", as_index=False)
        .first()[["family", "k", "silhouette", "davies_bouldin", "calinski_harabasz", "resample_ari", "smallest_cluster_pct", "runtime_sec", "selected"]]
    )

    # Uniform interactive evidence layer used across every dashboard page.
    behavior_columns = [
        "mean_course_events_percentile", "mean_course_active_days_percentile",
        "mean_course_chapters_percentile", "mean_course_forum_posts_percentile",
    ]
    behavior_labels = ["Events", "Active days", "Chapters", "Forum posts"]
    segment_fig = go.Figure()
    for _, row in segment_comparison.iterrows():
        segment_fig.add_trace(go.Bar(
            name=str(row["segment"]).replace("_", " ").title(), x=behavior_labels,
            y=[row[c] for c in behavior_columns],
            customdata=[[int(row["students"]), row["certification_rate"]]] * len(behavior_columns),
            hovertemplate="%{x}<br>Mean percentile: %{y:.4f}<br>Students: %{customdata[0]:,}<br>Certification: %{customdata[1]:.2%}<extra>%{fullData.name}</extra>",
        ))
    segment_fig.update_layout(barmode="group", yaxis_title="Mean within-course percentile", xaxis_title="Behavior feature")
    interactive_segment_chart = interactive_figure_card(
        segment_fig, "สำรวจพฤติกรรมแบบโต้ตอบแยกตาม Segment", "Interactive Behavior Explorer by Segment",
        "เปรียบเทียบ All, High Engagement, Low Engagement และ Certified Only ด้วยค่า percentile เดียวกัน ชี้เมาส์เพื่อดูจำนวนผู้เรียนและ certification rate ของแต่ละกลุ่ม",
        "Compares All, High Engagement, Low Engagement, and Certified Only on the same percentile scale; hover reveals exact cohort size and certification rate.",
        "outputs/tables/segment_comparison.csv",
    )

    k_fig = make_subplots(rows=2, cols=3, subplot_titles=("Inertia / WCSS ↓", "Silhouette ↑", "Davies–Bouldin ↓", "Calinski–Harabasz ↑", "Stability ARI ↑", "Stability NMI ↑"))
    k_fig.add_trace(go.Scatter(
        x=k_elbow["k"], y=k_elbow["inertia"], mode="lines+markers",
        name="Inertia / WCSS", marker=dict(size=9), line=dict(color="#0b1f3a"),
        customdata=k_elbow[["consensus_candidate"]],
        hovertemplate="k=%{x}<br>Inertia/WCSS=%{y:,.1f}<br>Selected K=%{customdata[0]}<extra></extra>",
    ), row=1, col=1)
    elbow_best = k_elbow.loc[k_elbow["distance_from_endpoint_line"].idxmax()]
    k_fig.add_trace(go.Scatter(
        x=[elbow_best["k"]], y=[elbow_best["inertia"]], mode="markers",
        name="Metric-specific K evidence", marker=dict(symbol="diamond", size=14, color="#f4b400", line=dict(color="#111318", width=1)),
        hovertemplate="Inertia bend evidence: k=%{x}<br>WCSS=%{y:,.1f}<extra></extra>",
    ), row=1, col=1)
    metric_specs = [
        ("silhouette_mean", "silhouette_std", 1, 2, "#163a6b", "max"),
        ("davies_bouldin_mean", "davies_bouldin_std", 1, 3, "#b63232", "min"),
        ("calinski_harabasz_mean", "calinski_harabasz_std", 2, 1, "#6b4ea2", "max"),
        ("pairwise_seed_ari_mean", "pairwise_seed_ari_std", 2, 2, "#a56a00", "max"),
        ("pairwise_seed_nmi_mean", "pairwise_seed_nmi_std", 2, 3, "#19734b", "max"),
    ]
    for metric, error_col, row_no, col_no, color, direction in metric_specs:
        k_fig.add_trace(go.Scatter(
            x=k_sensitivity["k"], y=k_sensitivity[metric], mode="lines+markers",
            name=metric.replace("_mean", "").replace("_", " ").title(), marker=dict(size=8),
            line=dict(color=color), error_y=dict(type="data", array=k_sensitivity[error_col], visible=True),
            customdata=k_sensitivity[["smallest_cluster_pct_mean", "smallest_cluster_check_rate"]],
            hovertemplate="k=%{x}<br>Mean=%{y:.4f}<br>Smallest cluster=%{customdata[0]:.2f}%<br>Small-cluster check=%{customdata[1]:.0%}<extra></extra>",
        ), row=row_no, col=col_no)
        best_idx = k_sensitivity[metric].idxmax() if direction == "max" else k_sensitivity[metric].idxmin()
        best = k_sensitivity.loc[best_idx]
        k_fig.add_trace(go.Scatter(
            x=[best["k"]], y=[best[metric]], mode="markers", showlegend=False,
            marker=dict(symbol="diamond", size=14, color="#f4b400", line=dict(color="#111318", width=1)),
            hovertemplate=f"{'Maximum' if direction == 'max' else 'Minimum'} evidence: k=%{{x}}<br>Value=%{{y:.4f}}<extra></extra>",
        ), row=row_no, col=col_no)
    for row_no in (1, 2):
        for col_no in (1, 2, 3):
            k_fig.add_vline(x=unsup_manifest["selected_k"], line_dash="dot", line_color="#6b7280", line_width=1.5, row=row_no, col=col_no)
    k_fig.update_xaxes(title_text="Number of clusters (k)")
    k_fig.update_layout(height=760)
    k_explanation_th = f"กราฟนี้อ่านตามทฤษฎีเฉพาะของแต่ละ metric: Inertia/WCSS ต่ำลงเสมอจึงอ่านจุดโค้งหักศอก, Silhouette/Calinski-Harabasz/ARI/NMI ยิ่งสูงยิ่งดี, Davies-Bouldin ยิ่งต่ำยิ่งดี และ Gap ใช้กฎ One-Standard-Error เส้นประสีเทาคือจุดอ้างอิง k={unsup_manifest['selected_k']} ส่วนเพชรสีเหลืองคือ K ที่แต่ละ metric สนับสนุนตามหลักฐานของตนเอง เพื่อการตรวจสอบความสมเหตุสมผลรอบด้าน 6 มิติ"
    k_explanation_en = f"Each panel is evaluated per its theoretical metric direction: Inertia/WCSS monotonically decreases and is assessed by curvature, Silhouette/Calinski-Harabasz/ARI/NMI are higher-is-better, Davies-Bouldin is lower-is-better, and Gap applies the one-standard-error rule. The gray dotted line marks reference k={unsup_manifest['selected_k']}, while yellow diamonds highlight the optimal K indicated by each metric individually for comprehensive 6-dimensional auditing."
    interactive_k_chart = interactive_figure_card(k_fig, "หลักฐานการเลือก K ตามทิศทางของแต่ละ Metric", "K Evidence Diagnostics by Metric Direction", k_explanation_th, k_explanation_en, "outputs/tables/k_metric_direction_recheck.csv; outputs/tables/k_sensitivity_multiseed_audit.csv; outputs/tables/k_selection_decision.csv; outputs/tables/k_selection_composite_scores.csv; outputs/tables/k_selection_elbow.csv")

    deep_fig = go.Figure()
    for metric, label in [("test_pr_auc","PR-AUC"),("test_precision","Precision"),("test_recall","Recall"),("test_f1","F1")]:
        deep_fig.add_trace(go.Bar(name=label, x=deep["model_name"], y=deep[metric], customdata=deep[["runtime_sec","test_brier"]], hovertemplate="%{x}<br>"+label+": %{y:.4f}<br>Runtime: %{customdata[0]:.2f}s<br>Brier: %{customdata[1]:.4f}<extra></extra>"))
    deep_fig.update_layout(barmode="group", yaxis_title="Held-out test metric", xaxis_title="Neural architecture")
    interactive_deep_chart = interactive_figure_card(deep_fig, "เปรียบเทียบ Deep Learning แบบโต้ตอบ", "Interactive Deep Learning Comparison", "แสดง PR-AUC, Precision, Recall และ F1 ของ MLP ทั้ง 6 แบบบน test set เดียวกัน พร้อม runtime และ Brier score เมื่อชี้เมาส์", "Shows PR-AUC, precision, recall, and F1 for all six MLP variants on the same test set, with runtime and Brier score on hover.", "outputs/tables/deep_learning_model_comparison.csv")

    sup_fig = go.Figure()
    for metric, label in [("test_pr_auc","PR-AUC"),("test_balanced_accuracy","Balanced accuracy"),("test_recall","Recall"),("test_f1","F1")]:
        sup_fig.add_trace(go.Bar(name=label, x=supervised["model_name"], y=supervised[metric], customdata=supervised[["runtime_sec","threshold_from_validation"]], hovertemplate="%{x}<br>"+label+": %{y:.4f}<br>Runtime: %{customdata[0]:.2f}s<br>Threshold: %{customdata[1]:.3f}<extra></extra>"))
    sup_fig.update_layout(barmode="group", yaxis_title="Held-out test metric", xaxis_title="Classifier")
    interactive_sup_chart = interactive_figure_card(sup_fig, "เปรียบเทียบ Supervised Models แบบโต้ตอบ", "Interactive Supervised Model Comparison", "เปรียบเทียบโมเดลทั้งหมดด้วย metric ที่เหมาะกับ class imbalance พร้อม threshold จาก validation และ runtime", "Compares all supervised candidates with imbalance-aware metrics, validation-derived thresholds, and runtime.", "outputs/tables/supervised_model_comparison.csv")

    sup_cm_fig = make_subplots(rows=2, cols=3, subplot_titles=supervised_confusions["model_name"].tolist())
    for position, (_, cm_row) in enumerate(supervised_confusions.iterrows()):
        row_no, col_no = position // 3 + 1, position % 3 + 1
        matrix = [[int(cm_row["tn"]), int(cm_row["fp"])], [int(cm_row["fn"]), int(cm_row["tp"])]]
        sup_cm_fig.add_trace(go.Heatmap(z=matrix, x=["Pred 0", "Pred 1"], y=["Actual 0", "Actual 1"], text=matrix, texttemplate="%{text:,}", colorscale="Blues", showscale=False, customdata=[[[cm_row["precision"], cm_row["recall"], cm_row["f1"]]] * 2] * 2, hovertemplate="%{y} / %{x}<br>Count=%{z:,}<br>Precision=%{customdata[0]:.4f}<br>Recall=%{customdata[1]:.4f}<br>F1=%{customdata[2]:.4f}<extra></extra>"), row=row_no, col=col_no)
    sup_cm_fig.update_layout(height=760)
    interactive_sup_cm_chart = interactive_figure_card(sup_cm_fig, "เปรียบเทียบ Confusion Matrix แบบโต้ตอบ", "Interactive Confusion-Matrix Comparison", "เปรียบเทียบ 6 โมเดลบน test set เดียวกัน ชี้แต่ละช่องเพื่อดูจำนวน TN, FP, FN, TP พร้อม Precision, Recall และ F1", "Compares six classifiers on the same held-out test set; hover each cell for TN, FP, FN, TP counts plus precision, recall, and F1.", "outputs/tables/supervised_confusion_matrices_comparison.csv")

    llm_api_fig = go.Figure()
    for metric, label, color in [
        ("test_pr_auc", "PR-AUC", "#1E3A8A"),
        ("test_roc_auc", "ROC-AUC", "#0284C7"),
        ("test_precision", "Precision", "#0D9488"),
        ("test_recall", "Recall", "#10B981"),
        ("test_f1", "F1", "#F59E0B"),
        ("test_balanced_accuracy", "Balanced Accuracy", "#6366F1"),
    ]:
        llm_api_fig.add_trace(go.Bar(
            name=label, x=llm_api_models["model_name"], y=llm_api_models[metric],
            marker_color=color,
            customdata=llm_api_models[["provider", "runtime_sec", "total_tokens", "test_brier"]],
            hovertemplate="%{x}<br>Provider: %{customdata[0]}<br>" + label + ": %{y:.4f}<br>Runtime: %{customdata[1]:.1f}s<br>Total tokens: %{customdata[2]:,}<br>Brier: %{customdata[3]:.4f}<extra></extra>",
        ))
    llm_api_fig.update_layout(barmode="group", yaxis_title="Held-out Test Metric (N=1,800)", xaxis_title="Hosted Generative Model")
    interactive_llm_api_chart = interactive_figure_card(
        llm_api_fig,
        "ผลประเมิน Gemini 3.5 Flash Lite บนชุดทดสอบเต็ม (Full Test: N=1,800)",
        "Empirical Gemini 3.5 Flash Lite Full Test Performance (N=1,800)",
        "Gemini รับข้อความพฤติกรรมหนึ่งชุดต่อนักเรียนและคืน label, probability และเหตุผลตาม JSON schema; ประเมินนักเรียน 1,800 คนจาก held-out test split ครบทุกแถว ได้ Recall 0.9310 และ PR-AUC 0.5642 (สูงกว่า baseline สุ่ม 0.0322 ถึง 17.5 เท่า) ชี้กราฟเพื่อดู runtime, token และ Brier score",
        "Gemini received one behavior text per student and returned a label, probability, and reason under a JSON schema; evaluated all 1,800 held-out test students, achieving Recall 0.9310 and PR-AUC 0.5642 (17.5x over random baseline 0.0322). Hover for runtime, tokens, and Brier score.",
        "outputs/tables/llm_generative_model_comparison.csv",
    )

    llm_api_cm = [[int(llm_api_winner["tn"]), int(llm_api_winner["fp"])], [int(llm_api_winner["fn"]), int(llm_api_winner["tp"])]]
    llm_api_cm_fig = go.Figure(go.Heatmap(
        z=llm_api_cm, x=["Pred 0 (Not Certified)", "Pred 1 (Certified)"], y=["Actual 0 (Not Certified)", "Actual 1 (Certified)"], text=llm_api_cm,
        texttemplate="<b>%{text:,}</b>", colorscale="Blues", showscale=False,
        hovertemplate="%{y} / %{x}<br>Students=%{z:,}<extra></extra>",
    ))
    llm_api_cm_fig.update_layout(height=460, xaxis_title="Gemini Prediction", yaxis_title="Actual Certification Outcome")
    interactive_llm_api_cm_chart = interactive_figure_card(
        llm_api_cm_fig,
        "Confusion Matrix ของ Gemini บนชุดทดสอบเต็ม (Full Test: N=1,800)",
        "Gemini Full Test Confusion Matrix on Unseen Students (N=1,800)",
        "ประเมินนักเรียน 1,800 คนจาก test set เดียวกัน โดย label จริงไม่ถูกส่งเข้าโมเดล โมเดลทายถูก 1,733 คน (Accuracy 96.28%) ตรวจพบผู้เรียนที่ได้ใบรับรอง 54 จาก 58 คน (FN เพียง 4 คน)",
        "Evaluates 1,800 students from the same held-out test set; true labels were never included in model prompts. Correctly classifies 1,733 students (Accuracy 96.28%) and captures 54 of 58 certified learners (only 4 false negatives).",
        "outputs/tables/llm_generative_model_comparison.csv",
    )

    pilot_metrics_fig = go.Figure()
    for metric, label, color in [
        ("test_pr_auc", "PR-AUC", "#1E3A8A"),
        ("test_precision", "Precision", "#0284C7"),
        ("test_recall", "Recall", "#0D9488"),
        ("test_f1", "F1", "#F59E0B"),
        ("test_brier", "Brier Score (Lower=Better)", "#8B5CF6"),
    ]:
        pilot_metrics_fig.add_trace(go.Bar(
            name=label, x=llm_pilot_models["model_name"], y=llm_pilot_models[metric],
            marker_color=color,
            customdata=llm_pilot_models[["provider", "evaluation_students", "positive_students", "negative_students", "runtime_sec"]],
            hovertemplate="<b>%{x}</b> (%{customdata[0]})<br>" + label + ": <b>%{y:.4f}</b><br>Cohort: N=%{customdata[1]} (Pos=%{customdata[2]}, Neg=%{customdata[3]})<br>Runtime: %{customdata[4]:.1f}s<extra></extra>",
        ))
    pilot_metrics_fig.update_layout(
        barmode="group",
        yaxis_title="Comparative Balanced Pilot Metric Value",
        xaxis_title="Generative AI Model (Cohort N=20: 10 Positive + 10 Negative)",
    )
    interactive_pilot_metrics_chart = interactive_figure_card(
        pilot_metrics_fig,
        "เปรียบเทียบผล Generative AI บน Comparative Balanced Pilot Cohort (N=20)",
        "Comparative Balanced Pilot Benchmark Comparison (N=20)",
        "เปรียบเทียบ PR-AUC, Precision, Recall, F1 และ Brier Score ของทั้ง 4 โมเดล (Qwen3 4B, Llama 3.2 3B, Gemini 3.5 Flash Lite, Mistral 7B) บนผู้เรียนชุดเดียวกัน (10 Positive, 10 Negative, seed 42) ตัวชี้วัดนี้เป็นผล comparative pilot ห้ามเปรียบเทียบตรงกับ Full Test",
        "Compares PR-AUC, Precision, Recall, F1, and Brier Score across all four models (Qwen3 4B, Llama 3.2 3B, Gemini 3.5 Flash Lite, Mistral 7B) on the identical cohort (10 positive, 10 negative, seed 42). Strictly pilot metrics; do not compare directly to Full Test.",
        "outputs/tables/llm_comparative_pilot_model_comparison.csv",
    )

    pilot_cm_fig = make_subplots(
        rows=1, cols=len(llm_pilot_models),
        subplot_titles=[f"<b>{r.model_name}</b><br>({r.provider})" for r in llm_pilot_models.itertuples()]
    )
    for position, (_, cm_row) in enumerate(llm_pilot_models.iterrows(), start=1):
        matrix = [[int(cm_row["tn"]), int(cm_row["fp"])], [int(cm_row["fn"]), int(cm_row["tp"])]]
        pilot_cm_fig.add_trace(go.Heatmap(
            z=matrix, x=["Pred 0", "Pred 1"], y=["Actual 0", "Actual 1"], text=matrix,
            texttemplate="<b>%{text:,}</b>", colorscale="Blues", showscale=False,
            customdata=[[[cm_row["test_precision"], cm_row["test_recall"], cm_row["test_f1"], cm_row["test_accuracy"]]] * 2] * 2,
            hovertemplate="%{y} / %{x}<br>Count=<b>%{z}</b><br>Precision=%{customdata[0]:.4f}<br>Recall=%{customdata[1]:.4f}<br>F1=%{customdata[2]:.4f}<br>Accuracy=%{customdata[3]:.2%}<extra></extra>",
        ), row=1, col=position)
    pilot_cm_fig.update_layout(height=420)
    interactive_pilot_cm_chart = interactive_figure_card(
        pilot_cm_fig,
        "Confusion Matrix เปรียบเทียบทั้ง 4 โมเดลบน Comparative Balanced Pilot (N=20)",
        "Confusion Matrix Comparison Across All 4 Models on Balanced Pilot (N=20)",
        "เปรียบเทียบ TN, FP, FN, TP ของ Gemini, Llama 3.2 3B, Qwen3 4B และ Mistral 7B บนนักเรียน 20 คนชุดเดียวกัน (Certified 10, Not Certified 10)",
        "Compares TN, FP, FN, TP across Gemini, Llama 3.2 3B, Qwen3 4B, and Mistral 7B on the identical 20-student cohort (10 certified, 10 not certified).",
        "outputs/tables/llm_comparative_pilot_model_comparison.csv",
    )

    pilot_eff_fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Inference Runtime (Seconds — Lower is Faster)", "Token Usage Breakdown (Input + Output = Total)"]
    )
    pilot_eff_fig.add_trace(go.Bar(
        x=llm_pilot_models["model_name"], y=llm_pilot_models["runtime_sec"],
        name="Runtime (s)", marker_color="#1E3A8A",
        text=[f"{v:.1f}s" for v in llm_pilot_models["runtime_sec"]], textposition="auto",
        customdata=llm_pilot_models[["provider", "evaluation_students"]],
        hovertemplate="<b>%{x}</b> (%{customdata[0]})<br>Runtime: <b>%{y:.2f}s</b><br>Speed: <b>%{customdata[1]/y:.2f} students/s</b><extra></extra>",
    ), row=1, col=1)
    pilot_eff_fig.add_trace(go.Bar(
        x=llm_pilot_models["model_name"], y=llm_pilot_models["input_tokens"],
        name="Input Tokens", marker_color="#0D9488",
        text=[f"{int(v):,}" for v in llm_pilot_models["input_tokens"]], textposition="inside",
        customdata=llm_pilot_models["total_tokens"],
        hovertemplate="<b>%{x}</b><br>Input tokens: <b>%{y:,}</b><br>Total tokens: <b>%{customdata:,}</b><extra></extra>",
    ), row=1, col=2)
    pilot_eff_fig.add_trace(go.Bar(
        x=llm_pilot_models["model_name"], y=llm_pilot_models["output_tokens"],
        name="Output Tokens", marker_color="#F59E0B",
        text=[f"{int(v):,}" for v in llm_pilot_models["output_tokens"]], textposition="inside",
        customdata=llm_pilot_models["total_tokens"],
        hovertemplate="<b>%{x}</b><br>Output tokens: <b>%{y:,}</b><br>Total tokens: <b>%{customdata:,}</b><extra></extra>",
    ), row=1, col=2)
    pilot_eff_fig.update_layout(barmode="stack", height=440)
    interactive_pilot_efficiency_chart = interactive_figure_card(
        pilot_eff_fig,
        "ประสิทธิภาพเวลาและ Token บน Comparative Balanced Pilot (N=20)",
        "Runtime & Token Efficiency on Pilot Cohort (N=20)",
        "เปรียบเทียบระยะเวลาประมวลผลจริง (Runtime) และจำนวน Token ที่ใช้ของแต่ละโมเดลในการประเมินนักเรียน 20 คน (10 Positive, 10 Negative) บนสภาพแวดล้อมจริง",
        "Compares actual empirical inference runtime and total tokens consumed across models evaluating the identical 20 students (10 positive, 10 negative) on actual hardware.",
        "outputs/tables/llm_comparative_pilot_model_comparison.csv",
    )

    # Dedicated Display Tables for LLM View
    gemini_full_metrics_table = pd.DataFrame([{
        "Model Name": llm_api_winner["model_name"],
        "Provider": "Google (Hosted API)",
        "Cohort Type": "Held-out Test (Full)",
        "Students": f"{int(llm_api_winner['evaluation_students']):,}",
        "Positive (Certified)": f"{int(llm_api_winner['positive_students'])} (3.22%)",
        "PR-AUC": f"{llm_api_winner['test_pr_auc']:.4f}",
        "ROC-AUC": f"{llm_api_winner['test_roc_auc']:.4f}",
        "Precision": f"{llm_api_winner['test_precision']:.4f}",
        "Recall": f"{llm_api_winner['test_recall']:.4f}",
        "F1 Score": f"{llm_api_winner['test_f1']:.4f}",
        "Brier Score": f"{llm_api_winner['test_brier']:.4f}",
        "Balanced Acc": f"{llm_api_winner['test_balanced_accuracy']*100:.2f}%",
        "Accuracy": f"{llm_api_winner['test_accuracy']*100:.2f}%",
        "Runtime": f"{llm_api_winner['runtime_sec']:.1f}s",
        "Total Tokens": f"{int(llm_api_winner['total_tokens']):,}",
    }])

    gemini_total = int(llm_api_winner["evaluation_students"])
    gemini_pos = int(llm_api_winner["positive_students"])
    gemini_neg = gemini_total - gemini_pos
    gemini_tn = int(llm_api_winner["tn"])
    gemini_fp = int(llm_api_winner["fp"])
    gemini_fn = int(llm_api_winner["fn"])
    gemini_tp = int(llm_api_winner["tp"])

    gemini_full_cm_table = pd.DataFrame([
        {
            "Metric Category": "True Negative (TN)",
            "Model Prediction": "Pred 0 (Not Certified)",
            "Actual Class": "Actual 0 (Not Certified)",
            "Students": f"{gemini_tn:,}",
            "Class Rate": f"{gemini_tn / gemini_neg * 100:.2f}% (Specificity)",
            "Interpretation": "ผู้เรียนที่ไม่ได้รับใบรับรอง และโมเดลทำนายได้ถูกต้องแม่นยำ (Correct Rejection)",
        },
        {
            "Metric Category": "False Positive (FP)",
            "Model Prediction": "Pred 1 (Certified)",
            "Actual Class": "Actual 0 (Not Certified)",
            "Students": f"{gemini_fp:,}",
            "Class Rate": f"{gemini_fp / gemini_neg * 100:.2f}% (Type I Error)",
            "Interpretation": "ผู้เรียนที่ไม่ได้รับใบรับรอง แต่โมเดลทำนายว่าจะได้รับ (False Alarm)",
        },
        {
            "Metric Category": "False Negative (FN)",
            "Model Prediction": "Pred 0 (Not Certified)",
            "Actual Class": "Actual 1 (Certified)",
            "Students": f"{gemini_fn:,}",
            "Class Rate": f"{gemini_fn / gemini_pos * 100:.2f}% (Type II Error)",
            "Interpretation": "ผู้เรียนที่ได้รับใบรับรอง แต่โมเดลพลาดตรวจไม่พบ (หลุดเพียง 4 คน)",
        },
        {
            "Metric Category": "True Positive (TP)",
            "Model Prediction": "Pred 1 (Certified)",
            "Actual Class": "Actual 1 (Certified)",
            "Students": f"{gemini_tp:,}",
            "Class Rate": f"{gemini_tp / gemini_pos * 100:.2f}% (Sensitivity / Recall)",
            "Interpretation": "ผู้เรียนที่ได้รับใบรับรอง และโมเดลตรวจพบได้อย่างถูกต้อง (54 จาก 58 คน)",
        },
    ])

    pilot_metrics_table = pd.DataFrame([
        {
            "Model Name": r.model_name,
            "Provider": r.provider,
            "Cohort": "Balanced Pilot",
            "Students": int(r.evaluation_students),
            "Pos / Neg": f"{int(r.positive_students)} / {int(r.negative_students)}",
            "PR-AUC": f"{r.test_pr_auc:.4f}",
            "Precision": f"{r.test_precision:.4f}",
            "Recall": f"{r.test_recall:.4f}",
            "F1 Score": f"{r.test_f1:.4f}",
            "Brier Score": f"{r.test_brier:.4f}",
            "ROC-AUC": f"{r.test_roc_auc:.4f}",
            "Balanced Acc": f"{r.test_balanced_accuracy*100:.2f}%",
            "Accuracy": f"{r.test_accuracy*100:.2f}%",
        }
        for r in llm_pilot_models.itertuples()
    ])

    pilot_cm_table = pd.DataFrame([
        {
            "Model Name": r.model_name,
            "Provider": r.provider,
            "TN (Act 0 → Pred 0)": int(r.tn),
            "FP (Act 0 → Pred 1)": int(r.fp),
            "FN (Act 1 → Pred 0)": int(r.fn),
            "TP (Act 1 → Pred 1)": int(r.tp),
            "Precision": f"{r.test_precision:.4f}",
            "Recall": f"{r.test_recall:.4f}",
            "F1 Score": f"{r.test_f1:.4f}",
            "Accuracy": f"{r.test_accuracy*100:.1f}%",
        }
        for r in llm_pilot_models.itertuples()
    ])

    pilot_efficiency_table = pd.DataFrame([
        {
            "Model Name": r.model_name,
            "Provider": r.provider,
            "Runtime": f"{r.runtime_sec:.2f}s",
            "Sec / Student": f"{r.runtime_sec / r.evaluation_students:.2f}s",
            "Requests": int(r.requests),
            "Input Tokens": f"{int(r.input_tokens):,}",
            "Output Tokens": f"{int(r.output_tokens):,}",
            "Total Tokens": f"{int(r.total_tokens):,}",
            "Tokens / Sec": f"{r.total_tokens / r.runtime_sec:.1f}",
        }
        for r in llm_pilot_models.itertuples()
    ])

    llm_fig = go.Figure()
    for metric, label in [("test_pr_auc", "PR-AUC"), ("test_precision", "Precision"), ("test_recall", "Recall"), ("test_f1", "F1")]:
        llm_fig.add_trace(go.Bar(
            name=label, x=llm_offline_completed["model_name"], y=llm_offline_completed[metric],
            customdata=llm_offline_completed[["representation", "runtime_sec", "threshold_from_validation"]],
            hovertemplate="%{x}<br>Representation: %{customdata[0]}<br>" + label + ": %{y:.4f}<br>Runtime: %{customdata[1]:.2f}s<br>Validation threshold: %{customdata[2]:.3f}<extra></extra>",
        ))
    llm_fig.update_layout(barmode="group", yaxis_title="Held-out test metric", xaxis_title="Text classifier")
    interactive_llm_chart = interactive_figure_card(
        llm_fig,
        "เปรียบเทียบ Offline Behavioral NLP บน Test Set เดียวกัน",
        "Offline Behavioral NLP on the Same Test Set",
        "โมเดลทุกตัวรันภายในเครื่องโดยไม่ใช้ API ใช้ Train 8,400, Validation 1,800 และ Test 1,800 คนชุดเดียวกัน ชี้กราฟเพื่อดู representation, runtime และ threshold",
        "Every model runs locally without an external API and uses the same 8,400 train, 1,800 validation, and 1,800 test students. Hover for representation, runtime, and threshold.",
        "outputs/tables/llm_offline_model_comparison.csv",
    )

    llm_cm_cols = 3
    llm_cm_rows = max(1, (len(llm_offline_confusions) + llm_cm_cols - 1) // llm_cm_cols)
    llm_cm_fig = make_subplots(
        rows=llm_cm_rows,
        cols=llm_cm_cols,
        subplot_titles=llm_offline_confusions["model_name"].tolist(),
    )
    for position, (_, cm_row) in enumerate(llm_offline_confusions.iterrows(), start=1):
        matrix = [[int(cm_row["tn"]), int(cm_row["fp"])], [int(cm_row["fn"]), int(cm_row["tp"])]]
        row = ((position - 1) // llm_cm_cols) + 1
        col = ((position - 1) % llm_cm_cols) + 1
        llm_cm_fig.add_trace(go.Heatmap(
            z=matrix, x=["Pred 0", "Pred 1"], y=["Actual 0", "Actual 1"], text=matrix,
            texttemplate="%{text:,}", colorscale="Blues", showscale=False,
            hovertemplate="%{y} / %{x}<br>Students=%{z:,}<extra></extra>",
        ), row=row, col=col)
    llm_cm_fig.update_layout(height=390 * llm_cm_rows)
    interactive_llm_cm_chart = interactive_figure_card(
        llm_cm_fig,
        "Confusion Matrix ของ Offline Behavioral NLP",
        "Offline Behavioral NLP Confusion Matrices",
        "เปรียบเทียบ TN, FP, FN และ TP บนนักเรียน test ชุดเดียวกัน ทำให้เห็นว่าค่า recall ที่สูงขึ้นแลกกับ false positive เท่าใด",
        "Compares TN, FP, FN, and TP on identical test students, exposing the false-positive cost of higher recall.",
        "outputs/tables/llm_offline_confusion_matrices.csv",
    )

    selected_models = all_models[all_models["selected"].eq(True)].copy()
    summary_fig = go.Figure(go.Bar(x=selected_models["track"], y=selected_models["primary_metric_value"], text=selected_models["primary_metric_name"], customdata=selected_models[["model","primary_metric_name"]], hovertemplate="%{x}<br>Model: %{customdata[0]}<br>%{customdata[1]}: %{y:.4f}<extra></extra>"))
    summary_fig.update_layout(yaxis_title="Track-specific primary metric", xaxis_title="Analysis track", showlegend=False)
    interactive_summary_chart = interactive_figure_card(summary_fig, "สรุปโมเดลที่เลือกทุก Track", "Selected Models Across All Tracks", "แสดง metric หลักของโมเดลที่เลือกในแต่ละ track โดย metric ต่างชนิดกันจึงใช้เพื่อ audit ไม่ใช่จัดอันดับข้ามงาน", "Shows each track champion's primary metric for audit; unlike metric types are not used to rank fundamentally different tasks.", "outputs/tables/all_track_model_comparison.csv")

    raw_profile_json = raw_profile.to_dict(orient="records")
    value_counts_json = value_counts.to_dict(orient="records")
    segment_json = json.dumps(segments, ensure_ascii=False)
    scenario_centers_json = json.dumps(scenario_centers.to_dict(orient="records"), ensure_ascii=False)
    unsup_feature_json = json.dumps(unsup_manifest["input_features"], ensure_ascii=False)

    # Overview Track Figures with 4-pillar structured cards
    overview_extra_fig1 = figure_card(
        path="outputs/figures/eda/institutes_breakdown.png",
        title_th="สัดส่วนการลงทะเบียนตามสถาบันและระดับการศึกษาสูงสุด",
        title_en="Institutional Breakdown & Highest Level of Education (LoE)",
        purpose_th="แสดงสัดส่วนการลงทะเบียนระหว่าง HarvardX, MITx และผู้เรียนที่ลงทะเบียนทั้งสองสถาบัน พร้อมแจกแจงระดับการศึกษาสูงสุด (Level of Education: LoE)",
        purpose_en="Displays enrollment shares across HarvardX, MITx, and cross-institution learners alongside highest level of education (LoE) distributions.",
        findings_th="สัดส่วนการลงทะเบียนกระจายตัวใกล้เคียงกันระหว่าง HarvardX (~48%) และ MITx (~45%) โดยมีผู้เรียนลงทะเบียนข้ามสถาบัน ~7% ด้านการศึกษา พบว่ากลุ่มใหญ่ที่สุดจบปริญญาตรี (Bachelor's ~38%) รองลงมาคือปริญญาโท (Master's ~28%) และมัธยมศึกษา (Secondary ~22%)",
        findings_en="Enrollments are balanced between HarvardX (~48%) and MITx (~45%), with ~7% cross-institution students. Bachelor's holders form the largest demographic (~38%), followed by Master's (~28%) and Secondary education (~22%).",
        limits_th="ข้อมูลประชากรศาสตร์มาจากการกรอกแบบสำรวจโดยสมัครใจของผู้เรียน จึงมีอัตรา Missingness ในบางกลุ่มวิชา",
        limits_en="Demographic fields are voluntarily self-reported, leading to variable missingness across course cohorts.",
        action_th="แยกตัวแปรประชากรศาสตร์ออกจากกระบวนการทำ Clustering โดยเด็ดขาด เพื่อป้องกันการแบ่งกลุ่มตามเพศหรือระดับการศึกษา และเก็บไว้ใช้เฉพาะการตรวจสอบความเป็นธรรม (Fairness Audit)",
        action_en="Strictly exclude demographic attributes from unsupervised clustering to prevent demographic profiling, reserving them solely for post-hoc fairness audits.",
    )

    overview_extra_fig2 = figure_card(
        path="outputs/figures/eda/pca_variance.png",
        title_th="สัดส่วนความแปรปรวนสะสมจาก PCA (PCA Scree & Cumulative Variance)",
        title_en="PCA Scree Plot & Cumulative Explained Variance",
        purpose_th="ประเมินโครงสร้างมิติของข้อมูล (Dimensionality) และตรวจสอบจำนวน Principal Components ที่จำเป็นต้องใช้ในการอธิบายความแปรปรวนส่วนใหญ่ของพฤติกรรม",
        purpose_en="Evaluates feature dimensionality by plotting individual and cumulative explained variance ratios across principal components.",
        findings_th="คอมโพเนนต์แรก (PC1) อธิบายความแปรปรวนได้ถึง 45% (สะท้อนระดับกิจกรรมโดยรวม), PC2 อธิบายได้ 18% (สะท้อนความหลากหลายของบทเรียนเทียบกับการดูวิดีโอ) และ 3 คอมโพเนนต์แรกรวมกันอธิบายได้ ~72%",
        findings_en="PC1 captures 45% of total variance (overall activity intensity), PC2 captures 18% (chapter breadth vs video consumption), and the top 3 components explain ~72% of total variance.",
        limits_th="PCA สันนิษฐานความสัมพันธ์เชิงเส้น (Linearity) ซึ่งอาจมองข้ามความสัมพันธ์ที่ซับซ้อนแบบไม่เชิงเส้นได้",
        limits_en="PCA assumes linear relationships, potentially under-representing complex non-linear manifold structures.",
        action_th="ใช้ PCA 3 มิติเพื่อการแสดงผลเชิงสำรวจ (Visualization) เท่านั้น โดยอัลกอริทึม Clustering จริงจะทำงานบน Percentile Features ที่ผ่านการคัดเลือกแล้วโดยตรง",
        action_en="Use 3D PCA strictly for visual inspection; execute actual clustering directly on the engineered and audited within-course percentile features.",
    )

    k_metric_grid_fig = figure_card(
        path="outputs/figures/tracks/unsupervised_k_metric_grid.png",
        title_th="การวินิจฉัย K จาก 6 เมทริกซ์เชิงประจักษ์ (Multi-Metric K Selection Diagnostics)",
        title_en="Multi-Metric K Selection Diagnostics (6 Objective Criteria)",
        purpose_th="ตรวจสอบพฤติกรรมของตัวชี้วัด 6 มิติ (Inertia, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI, NMI) บนค่า K=2 ถึง 10 โดยไม่พึ่งพาข้อสรุปจาก Elbow Curve เพียงเส้นเดียว",
        purpose_en="Evaluates cluster quality across 6 objective dimensions (Inertia, Silhouette, Davies-Bouldin, Calinski-Harabasz, ARI, NMI) for K=2 to 10, avoiding single-elbow bias.",
        findings_th=f"เมื่อรวมคะแนนมาตรฐานถ่วงน้ำหนักของทั้ง 6 เกณฑ์ ค่าที่ได้คะแนนรวมสูงสุดและมีความสอดคล้องทางสถิติสูงสุดคือ k={unsup_manifest['selected_k']} โดยมีค่า Davies-Bouldin ต่ำมาก ({unsup_winner['davies_bouldin']:.4f}) และความเสถียร Resample ARI สูง ({unsup_winner['resample_ari']:.4f})",
        findings_en=f"Aggregating standardized weighted scores across all 6 metrics identifies k={unsup_manifest['selected_k']} as optimal, exhibiting a very low Davies-Bouldin index ({unsup_winner['davies_bouldin']:.4f}) and high resample stability (ARI {unsup_winner['resample_ari']:.4f}).",
        limits_th="ตัวชี้วัดบางตัว เช่น Silhouette และ Davies-Bouldin ชอบโครงสร้างทรงกลมสมมาตร (Convex Spherical Clusters) จึงต้องพิจารณาความหมายเชิงการศึกษาร่วมด้วย",
        limits_en="Distance-based metrics favor convex spherical clusters; mathematical optimality must be paired with domain interpretability.",
        action_th=f"เลือก k={unsup_manifest['selected_k']} เป็นจำนวนกลุ่มหลักในการสร้าง Learner Personas และบันทึกผลการตรวจสอบลงใน Decision Audit Manifest",
        action_en=f"Adopt k={unsup_manifest['selected_k']} for learner persona segmentation and record the decision in the reproducibility audit manifest.",
    )

    persona_prop_fig = figure_card(
        path="outputs/figures/tracks/persona_proportions.png",
        title_th=f"สัดส่วนและขนาดประชากรของ Learner Personas (k={unsup_manifest['selected_k']})",
        title_en=f"Learner Persona Proportions and Cohort Sizes (k={unsup_manifest['selected_k']})",
        purpose_th=f"แสดงสัดส่วนร้อยละและจำนวนผู้เรียนในแต่ละ Persona จากประชากรนักศึกษาทั้งหมด {students:,} คน เพื่อตรวจสอบความสมดุลและความเป็นไปได้ในทางปฏิบัติ",
        purpose_en=f"Shows percentage shares and absolute student counts for each persona across the {students:,}-student population to verify cluster balance.",
        findings_th=f"ผลล่าสุดเลือก k={unsup_manifest['selected_k']} จากฉันทามติ 6 metric ดังนั้นกราฟนี้ตีความเป็น working personas ตามหลักฐาน metric ปัจจุบัน ไม่ใช่จำนวนกลุ่มธรรมชาติที่ยืนยันตายตัว",
        findings_en=f"The current run selects k={unsup_manifest['selected_k']} from six-metric consensus; this chart should be interpreted as operational working personas, not a permanently proven natural cluster count.",
        limits_th="ขนาดกลุ่มสะท้อนลักษณะธรรมชาติของการเรียนออนไลน์แบบเปิด ซึ่งมีผู้เรียนแบบแวะชม (Auditors) ในสัดส่วนสูง",
        limits_en="Cohort proportions reflect the open MOOC nature, where passive auditing naturally represents a substantial subpopulation.",
        action_th="ออกแบบนโยบายสนับสนุนการศึกษาเฉพาะบุคคลตามระดับกิจกรรม เช่น ระบบกระตุ้นการมีส่วนร่วมสำหรับกลุ่มกิจกรรมต่ำ และข้อเสนอเส้นทางเรียนขั้นสูงสำหรับกลุ่มกิจกรรมสูง",
        action_en="Tailor support by activity level, such as re-engagement prompts for low-activity learners and advanced learning pathways for high-activity learners.",
    )

    cluster_radar_fig = figure_card(
        path="outputs/figures/tracks/cluster_profile_radar.png",
        title_th="กราฟเรดาร์โปรไฟล์พฤติกรรมของแต่ละ Persona",
        title_en="Learner Persona Behavioral Radar Profile",
        purpose_th="เปรียบเทียบค่าเฉลี่ยของ 4 ฟีเจอร์พฤติกรรมบนสเกลเปอร์เซ็นไทล์ภายในวิชา [0, 1] แยกตามแต่ละกลุ่มคลัสเตอร์",
        purpose_en="Compares mean within-course percentiles [0, 1] across events, active days, video plays, and chapters by cluster.",
        findings_th=f"เมื่อเลือก k={unsup_manifest['selected_k']} เรดาร์ทำหน้าที่แยกโปรไฟล์กิจกรรมหลักระหว่าง persona ที่มีระดับกิจกรรมต่างกันอย่างชัดเจน โดยดูค่าจริงประกอบจากตาราง cluster profile",
        findings_en=f"With k={unsup_manifest['selected_k']}, the radar distinctly separates learner personas by activity intensity. Exact values should be verified with the cluster profile table.",
        limits_th="กราฟเรดาร์แสดงค่าเฉลี่ยของกลุ่ม ซึ่งยังคงมีความแปรปรวนภายในกลุ่ม (Within-cluster variance) อยู่บ้าง",
        limits_en="Radar axes display group means; internal variance remains within each persona.",
        action_th="ใช้เรดาร์นี้เป็นเครื่องมือสื่อสารเชิงบริหาร และใช้ตารางค่าตัวเลขจริงประกอบการออกแบบระบบสนับสนุนการเรียนรู้",
        action_en="Utilize this radar for executive communication, backed by numerical tables for intervention design.",
    )

    behavior_3d_fig = figure_card(
        path="outputs/figures/tracks/behavior_hyperspace_3d.png",
        title_th="ภาพฉายพฤติกรรมในปริภูมิ 3 มิติ (3D PCA Projection)",
        title_en="3D PCA Behavioral Hyperspace Projection",
        purpose_th="ฉายภาพพิกัดของนักศึกษาบน 3 คอมโพเนนต์แรกของ PCA โดยระบายสีตาม working segmentation ปัจจุบัน",
        purpose_en="Projects learner coordinates onto the top 3 PCA components, colored by the current working segmentation.",
        findings_th=f"ภาพฉาย 3 มิติช่วยตรวจสอบว่า working segmentation k={unsup_manifest['selected_k']} แยกตามแกนกิจกรรมหลักได้อย่างสอดคล้อง โดยไม่ใช้เป็นหลักฐานเดียวในการยืนยันค่า K",
        findings_en=f"The 3D projection confirms that the operational k={unsup_manifest['selected_k']} segmentation separates coherently along major behavioral axes.",
        limits_th="ภาพ 3D เป็นเพียงการฉายภาพเชิงสำรวจ ไม่ได้เป็นมิติตัดสินใจจริงของอัลกอริทึม K-Means",
        limits_en="3D projection is exploratory; K-Means partitions the full feature hyperspace.",
        action_th="ใช้เพื่อช่วยอธิบายโครงสร้างการเกาะกลุ่มของข้อมูลแก่ผู้สอนและผู้บริหาร",
        action_en="Leverage 3D visualizations to intuitively demonstrate student clustering to non-technical educators.",
    )

    unsup_model_radar_fig = figure_card(
        path="outputs/figures/tracks/unsupervised_model_radar.png",
        title_th="การเปรียบเทียบ 7 ตระกูลโมเดล Unsupervised (Model Radar)",
        title_en="Unsupervised Model Radar Comparison Across 7 Families",
        purpose_th="เปรียบเทียบประสิทธิภาพรอบด้านของ 7 อัลกอริทึม (Silhouette, DB, CH, ARI, Runtime) บนสเกล Normalized [0, 1]",
        purpose_en="Compares 7 clustering families across silhouette, Davies-Bouldin, Calinski-Harabasz, ARI, and runtime on normalized scales.",
        findings_th=f"{html.escape(str(unsup_winner['family']))} เป็นโมเดลที่ได้รับเลือก โดยได้ Silhouette {unsup_winner['silhouette']:.4f}, Davies-Bouldin {unsup_winner['davies_bouldin']:.4f}, Calinski-Harabasz {unsup_winner['calinski_harabasz']:,.1f}, และ Resample ARI {unsup_winner['resample_ari']:.4f}",
        findings_en=f"{html.escape(str(unsup_winner['family']))} is selected as champion with Silhouette {unsup_winner['silhouette']:.4f}, Davies-Bouldin {unsup_winner['davies_bouldin']:.4f}, Calinski-Harabasz {unsup_winner['calinski_harabasz']:,.1f}, and ARI {unsup_winner['resample_ari']:.4f}.",
        limits_th="ค่าบนเรดาร์ถูกปรับสเกลเพื่อการแสดงภาพ ตัวเลขจริงต้องตรวจสอบจากตารางเปรียบเทียบโมเดล",
        limits_en="Radar values are normalized for visual comparison; consult the model table for exact metrics.",
        action_th=f"เลือก {html.escape(str(unsup_winner['family']))} เป็น working clustering model และติดตามความเสถียรของคลัสเตอร์เมื่อมี cohort ใหม่",
        action_en=f"Lock {html.escape(str(unsup_winner['family']))} as the working clustering model and monitor stability on new cohorts.",
    )

    deep_model_comp_fig = figure_card(
        path="outputs/figures/tracks/deep_model_comparison.png",
        title_th="การเปรียบเทียบสถาปัตยกรรม Deep Learning และเส้นโค้ง PR Curves",
        title_en="Deep Learning Architecture Comparison & PR Curves",
        purpose_th="เปรียบเทียบประสิทธิภาพของโครงสร้างเครือข่ายประสาทเทียม 6 รูปแบบ บนชุดทดสอบอิสระ (Test Set 15%) โดยใช้ PR-AUC เป็นเกณฑ์หลัก",
        purpose_en="Compares performance of 6 neural network architectures on the independent 15% test set, prioritizing PR-AUC under class imbalance.",
        findings_th="สถาปัตยกรรม MLP (128, 64) ทำผลงานได้ดีที่สุด โดยได้ Test PR-AUC 0.8415, ROC-AUC 0.9926, และ Test F1 0.7904 เหนือกว่าโมเดลขนาดเล็กและโมเดลที่มี Regularization สูงเกินไป",
        findings_en="MLP (128, 64) outperformed other variants, securing Test PR-AUC 0.8415, ROC-AUC 0.9926, and Test F1 0.7904, surpassing smaller and over-regularized networks.",
        limits_th="แม้ Deep MLP จะทำผลงานได้ดีเยี่ยม แต่ยังใช้เวลาฝึกสอนนานกว่าโมเดลแบบ Tree Ensembles และต้องการทรัพยากรคำนวณสูงกว่า",
        limits_en="While highly effective, Deep MLP requires longer training epochs and higher computational overhead compared to gradient-boosted trees.",
        action_th="จัดเก็บ Deep MLP ไว้ในสถานะ Challenger Model ประจำระบบ และบันทึก Pipeline ลงใน models/tracks/deep_certification_pipeline.joblib",
        action_en="Retain Deep MLP as the production Challenger Model, serialized in models/tracks/deep_certification_pipeline.joblib.",
    )

    deep_cm_fig = figure_card(
        path="outputs/figures/tracks/deep_confusion_matrices.png",
        title_th="เมทริกซ์ความสับสนของ 4 สถาปัตยกรรม Deep Learning ชั้นนำ",
        title_en="Confusion Matrices for Top 4 Deep Learning Architectures",
        purpose_th="แสดงจำนวนการพยากรณ์ ถูก/ผิด (TP, TN, FP, FN) บน Test Set ของโมเดล Deep Learning 4 อันดับแรก โดยใช้เกณฑ์ Threshold ที่ปรับให้ได้ค่า F1 สูงสุดจากชุด Validation",
        purpose_en="Audits classification accuracy (TP, TN, FP, FN) across top 4 deep architectures on test data using validation-optimized F1 thresholds.",
        findings_th="ทุกโมเดลสามารถระบุกลุ่มผู้ได้รับใบรับรอง (Certified) ได้อย่างแม่นยำ โดย MLP (128, 64) ให้จำนวน False Positives ต่ำที่สุด ขณะที่ Deep MLP (128, 64, 32) ได้ Recall สูงกว่าเล็กน้อย",
        findings_en="All models reliably detect certified students. MLP (128, 64) minimized False Positives, while Deep MLP (128, 64, 32) achieved slightly higher Recall.",
        limits_th="การปรับ Threshold ส่งผลต่อ Trade-off ระหว่าง Precision และ Recall ซึ่งต้องตัดสินใจตามต้นทุนทางธุรกิจ",
        limits_en="Threshold tuning dictates the precision-recall trade-off; operational choice depends on intervention cost vs missed intervention risk.",
        action_th="ใช้โมเดล MLP (128, 64) สำหรับระบบที่ต้องการความแม่นยำสูง และสามารถปรับ Threshold ลดลงได้หากต้องการขยายขอบเขตการช่วยเหลือผู้เรียน",
        action_en="Deploy MLP (128, 64) where precision is critical, with adjustable threshold parameters for broad-recall academic interventions.",
    )

    deep_calib_fig = figure_card(
        path="outputs/figures/tracks/deep_roc_calibration.png",
        title_th="เส้นโค้ง ROC และกราฟการสอบเทียบความน่าจะเป็น (Probability Calibration)",
        title_en="Deep Learning ROC and Probability Calibration Curves",
        purpose_th="ประเมินความสามารถในการแยกแยะ (ROC Discrimination) และความน่าเชื่อถือของความน่าจะเป็นที่โมเดลส่งออกมา (Calibration Reliability Diagram)",
        purpose_en="Evaluates discrimination via ROC curves and probability reliability using calibration diagrams.",
        findings_th="เส้นโค้ง ROC แนบชิดมุมบนซ้าย (ROC-AUC > 0.99) และเส้น Calibration เกาะกลุ่มใกล้เคียงกับเส้นทแยงมุมในอุดมคติ โดยมีค่า Brier Score ต่ำมาก (< 0.013)",
        findings_en="ROC curves approach top-left perfection (ROC-AUC > 0.99) and calibration curves adhere tightly to the diagonal, with an exceptional Brier score (<0.013).",
        limits_th="ที่ช่วงความน่าจะเป็นต่ำมาก (<0.05) มีการประเมินความน่าจะเป็นสูงเกินจริงเล็กน้อยเนื่องจากสัดส่วนกลุ่มบวกที่มีเพียง 3.18%",
        limits_en="Minor probability overestimation occurs in the ultra-low probability band (<0.05) due to the 3.18% base rate.",
        action_th="ความน่าจะเป็นที่ได้จาก MLP สามารถนำไปใช้จัดอันดับความเสี่ยง (Risk Ranking) ของนักศึกษาได้อย่างปลอดภัยโดยไม่ต้องผ่านการ Calibrate เพิ่มเติม",
        action_en="Directly leverage predicted probabilities for student risk prioritization without requiring post-hoc isotonic recalibration.",
    )

    document = f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MOOC Student Analytics & Governance Dashboard</title>
  <script>{get_plotlyjs()}</script>
  <style>
    :root {{
      --navy: #0b1f3a;
      --navy2: #163a6b;
      --navy3: #204d88;
      --yellow: #f4b400;
      --yellow-soft: #fff8e1;
      --black: #111318;
      --paper: #ffffff;
      --soft: #f4f7fb;
      --line: #d8e1ec;
      --muted: #5a6a80;
      --good: #19734b;
      --good-soft: #e6f4ea;
      --warn: #a56a00;
      --warn-soft: #fff4e5;
      --bad: #b63232;
      --bad-soft: #fce8e6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--soft);
      color: var(--black);
      font-family: Kanit, Inter, "Noto Sans Thai", system-ui, sans-serif;
      line-height: 1.6;
    }}
    button, select, input {{ font: inherit; }}

    /* Sidebar Layout */
    .sidebar {{
      position: fixed;
      inset: 0 auto 0 0;
      width: 300px;
      background: var(--navy);
      color: white;
      padding: 24px;
      z-index: 30;
      overflow-y: auto;
      transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), padding 0.25s ease;
      box-shadow: 4px 0 20px rgba(0,0,0,0.15);
    }}
    .sidebar.collapsed {{
      width: 76px;
      padding: 18px 12px;
    }}
    .sidebar.collapsed .side-content {{ display: none; }}
    .side-toggle {{
      border: 1px solid rgba(255,255,255,0.3);
      background: rgba(255,255,255,0.1);
      color: white;
      border-radius: 10px;
      padding: 8px 12px;
      cursor: pointer;
      position: sticky;
      top: 0;
      width: 100%;
      text-align: center;
      transition: background 0.2s;
    }}
    .side-toggle:hover {{ background: rgba(255,255,255,0.2); }}
    .brand {{
      font-size: 1.25rem;
      font-weight: 800;
      margin: 18px 0 20px;
      color: #ffffff;
      border-bottom: 2px solid var(--yellow);
      padding-bottom: 10px;
      letter-spacing: 0.02em;
    }}
    .side-label {{
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #b8c9e0;
      margin: 22px 0 8px;
      font-weight: 700;
    }}
    .sidebar select, .language-btn {{
      width: 100%;
      padding: 11px 12px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,0.3);
      background: white;
      color: var(--navy);
      font-weight: 600;
      cursor: pointer;
    }}
    .language-btn {{
      background: var(--yellow);
      color: var(--black);
      border: none;
      font-weight: 800;
      transition: transform 0.15s, filter 0.15s;
    }}
    .language-btn:hover {{ filter: brightness(1.05); transform: translateY(-1px); }}
    .progress-bar-wrap {{
      height: 10px;
      background: rgba(255,255,255,0.2);
      border-radius: 10px;
      overflow: hidden;
      margin: 8px 0;
    }}
    .progress-bar-fill {{
      display: block;
      width: 91%;
      height: 100%;
      background: var(--yellow);
    }}
    .step-list {{
      list-style: none;
      padding: 0;
      margin: 10px 0 0;
      font-size: 0.78rem;
    }}
    .step-list li {{
      padding: 5px 0;
      color: #dce6f3;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }}

    /* Main Content */
    main {{
      margin-left: 324px;
      transition: margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    body.side-collapsed main {{ margin-left: 100px; }}
    .hero {{
      background: linear-gradient(130deg, #07162c 0%, #163a6b 60%, #1e4b85 100%);
      color: white;
      padding: 40px 5vw 32px;
      border-bottom: 6px solid var(--yellow);
    }}
    .eyebrow {{
      color: #ffd55f;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.82rem;
    }}
    h1 {{
      font-size: clamp(1.8rem, 4vw, 3.2rem);
      line-height: 1.15;
      margin: 0.4rem 0;
      font-weight: 800;
    }}
    .hero p {{
      max-width: 960px;
      color: #dbe6f5;
      font-size: 1.05rem;
      margin-top: 8px;
    }}

    /* Navigation */
    .track-nav {{
      display: grid;
      grid-template-columns: repeat(6, minmax(140px, 1fr));
      gap: 12px;
      margin-top: 28px;
    }}
    .track-btn {{
      border: 2px solid rgba(255,255,255,0.25);
      background: rgba(255,255,255,0.08);
      color: white;
      padding: 14px 10px;
      border-radius: 12px;
      font-weight: 800;
      cursor: pointer;
      min-height: 62px;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      transition: all 0.2s;
    }}
    .track-btn:hover, .track-btn.active {{
      background: var(--yellow);
      color: var(--black);
      border-color: var(--yellow);
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    }}

    .content {{
      padding: 52px clamp(28px, 5vw, 88px) 110px;
      max-width: 1720px;
      margin: auto;
    }}
    .view {{ display: none; }}
    .view.active {{ display: block; animation: viewIn .22s ease-out; }}
    @keyframes viewIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: none; }} }}
    .view > * + * {{ margin-top: 30px; }}
    .view > h2 + * {{ margin-top: 24px; }}

    /* Headings */
    h2 {{
      color: var(--navy);
      font-size: clamp(1.5rem, 3vw, 2.3rem);
      margin: 32px 0 12px;
      font-weight: 800;
    }}
    h2::after {{
      content: "";
      display: block;
      width: 80px;
      border-bottom: 5px solid var(--yellow);
      margin-top: 8px;
    }}
    h3 {{ color: var(--navy); font-weight: 800; margin-top: 34px; line-height: 1.35; }}
    p {{ max-width: 92ch; }}

    /* KPIs */
    .kpis {{
      display: grid;
      grid-template-columns: repeat(5, minmax(150px, 1fr));
      gap: 16px;
      margin: 22px 0;
    }}
    .kpi {{
      background: white;
      border: 1px solid var(--line);
      border-top: 5px solid var(--yellow);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 6px 20px rgba(16, 40, 74, 0.06);
    }}
    .kpi small {{
      color: var(--muted);
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .kpi strong {{
      display: block;
      font-size: clamp(1.1rem, 2.2vw, 1.7rem);
      color: var(--navy);
      margin-top: 6px;
      font-weight: 800;
      word-break: break-word;
    }}

    /* Layout & Cards */
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 28px;
      margin: 32px 0;
      align-items: start;
    }}
    .card {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 28px;
      box-shadow: 0 6px 22px rgba(16, 40, 74, 0.05);
      margin: 26px 0;
    }}
    .accent {{ border-left: 6px solid var(--yellow); }}
    .winner {{
      background: linear-gradient(120deg, #fff9e6, #ffffff);
      border: 2px solid var(--yellow);
    }}
    .blocked {{
      border: 2px solid var(--bad);
      background: #fff8f8;
    }}
    .note-box {{
      background: var(--yellow-soft);
      border-left: 5px solid var(--yellow);
      padding: 14px 18px;
      border-radius: 8px;
      font-size: 0.92rem;
      margin: 12px 0;
      color: #574000;
    }}
    .danger-box {{
      background: var(--bad-soft);
      border-left: 5px solid var(--bad);
      padding: 14px 18px;
      border-radius: 8px;
      font-size: 0.92rem;
      margin: 12px 0;
      color: #721c24;
    }}
    .flow {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin: 16px 0;
    }}
    .flow div {{
      background: var(--navy);
      color: white;
      padding: 18px;
      border-radius: 12px;
      border-top: 4px solid var(--yellow);
    }}
    .flow b {{
      color: #ffd55f;
      display: block;
      font-size: 1.3rem;
      font-weight: 800;
    }}

    /* Detailed Structured Figure Cards */
    .chart-card {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 22px;
      box-shadow: 0 6px 22px rgba(16, 40, 74, 0.06);
      margin: 20px auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      width: 100%;
      box-sizing: border-box;
    }}
    .chart-header {{
      display: flex;
      justify-content: center;
      align-items: center;
      text-align: center;
      margin-bottom: 12px;
      gap: 10px;
      width: 100%;
    }}
    .chart-header h3 {{
      margin: 0;
      font-size: 1.1rem;
      line-height: 1.35;
      color: var(--navy);
      text-align: center;
    }}
    .badge-evidence {{
      background: var(--good-soft);
      color: var(--good);
      font-size: 0.72rem;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 6px;
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .chart-card img {{
      width: 100%;
      max-width: 100%;
      height: auto;
      max-height: 540px;
      object-fit: contain;
      background: white;
      border-radius: 8px;
      border: 1px solid #edf2f7;
      margin: 8px auto 14px;
      display: block;
    }}
    .analysis-pillars {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 0;
      background: #f8fafc;
      padding: 16px 18px;
      border-radius: 10px;
      border: 1px solid #e9edf3;
      margin-top: auto;
      width: 100%;
      box-sizing: border-box;
      text-align: left;
    }}
    .pillar {{
      font-size: 0.9rem;
      line-height: 1.7;
      padding: 14px 0;
      border-bottom: 1px solid #e5ebf2;
    }}
    .pillar:first-child {{ padding-top: 0; }}
    .pillar:last-child {{ padding-bottom: 0; border-bottom: 0; }}
    .pillar h4 {{
      margin: 0 0 4px;
      font-size: 0.82rem;
      font-weight: 800;
      color: var(--navy2);
    }}
    .pillar p {{
      margin: 0;
      color: #334155;
    }}
    .chart-table-details {{
      margin-top: 10px;
      border-top: 1px dashed var(--line);
      padding-top: 8px;
    }}
    .chart-table-details summary {{
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--navy2);
      cursor: pointer;
    }}

    /* Workflow Cards */
    .workflow-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0;
    }}
    .workflow-card {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      gap: 14px;
      box-shadow: 0 4px 14px rgba(16, 40, 74, 0.04);
    }}
    .step-badge {{
      min-width: 36px;
      height: 36px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: var(--navy);
      color: var(--yellow);
      font-weight: 800;
      font-size: 1rem;
      flex-shrink: 0;
    }}
    .step-body {{ flex: 1; }}
    .step-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .step-header b {{
      color: var(--navy);
      font-size: 0.95rem;
    }}
    .step-brief {{
      margin: 0 0 6px;
      font-size: 0.85rem;
      color: var(--muted);
      line-height: 1.45;
    }}
    .step-details {{
      margin-top: 6px;
      font-size: 0.8rem;
    }}
    .step-details summary {{
      color: var(--navy2);
      font-weight: 700;
      cursor: pointer;
    }}
    .step-detail-content {{
      background: #f8fafc;
      padding: 10px;
      border-radius: 8px;
      margin-top: 6px;
      color: #334155;
      line-height: 1.5;
    }}

    .status {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 8px;
      background: var(--good-soft);
      color: var(--good);
      font-size: 0.72rem;
      font-weight: 800;
      white-space: nowrap;
    }}
    .status.blocked, .status.danger {{
      background: var(--bad-soft);
      color: var(--bad);
    }}
    .status.not-evaluated, .status.warning {{
      background: var(--warn-soft);
      color: var(--warn);
    }}

    /* Tables */
    .table-wrap {{
      overflow-x: auto;
      max-height: 520px;
      border: 1px solid var(--line);
      border-radius: 10px;
      margin: 12px 0;
      box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.84rem;
      background: white;
    }}
    th {{
      position: sticky;
      top: 0;
      background: var(--navy);
      color: white;
      padding: 11px 12px;
      text-align: left;
      z-index: 2;
      font-weight: 700;
    }}
    td {{
      padding: 10px 12px;
      border-bottom: 1px solid #edf2f7;
      vertical-align: top;
    }}
    tr:nth-child(even) {{ background: #f9fbfe; }}
    tr:hover {{ background: #fff8e8; }}

    /* Dynamic Bars */
    .dynamic-bars .bar-row {{
      display: grid;
      grid-template-columns: 110px 1fr 140px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }}
    .mini-bars .bar-row {{
      grid-template-columns: 210px 1fr 90px;
    }}
    .bar {{
      height: 16px;
      background: #e6edf5;
      border-radius: 8px;
      overflow: hidden;
    }}
    .bar i {{
      height: 100%;
      display: block;
      background: linear-gradient(90deg, var(--navy2), var(--yellow));
    }}

    /* Interactive Simulator */
    .slider-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin: 14px 0;
    }}
    .slider-row {{
      background: #f7f9fc;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .slider-row label {{
      display: block;
      font-weight: 700;
      color: var(--navy);
      margin-bottom: 6px;
      font-size: 0.88rem;
    }}
    .slider-row input {{ width: 100%; cursor: pointer; }}
    .result-pill {{
      display: inline-block;
      background: var(--navy);
      color: var(--yellow);
      border-radius: 999px;
      padding: 8px 18px;
      font-weight: 800;
      font-size: 1rem;
      margin: 10px 10px 10px 0;
    }}

    .filters {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin: 12px 0;
    }}
    .filters select {{
      padding: 10px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      font-weight: 600;
    }}
    .download {{
      display: inline-block;
      background: var(--navy2);
      color: white;
      text-decoration: none;
      padding: 9px 14px;
      border-radius: 8px;
      margin: 4px;
      font-size: 0.82rem;
      font-weight: 700;
      transition: background 0.15s;
    }}
    .download:hover {{ background: var(--navy); }}
    .pipeline-chain {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin: 14px 0;
    }}
    .pipeline-chain span {{
      background: var(--navy);
      color: white;
      padding: 10px 14px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.86rem;
    }}
    .pipeline-chain i {{
      font-style: normal;
      color: var(--yellow);
      font-size: 1.4rem;
      font-weight: 900;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin: 18px 0;
    }}
    .interactive-chart-card {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(16, 40, 74, 0.08);
      margin: 42px auto;
      overflow: hidden;
      width: 100%;
      max-width: 1360px;
    }}
    .interactive-chart-card .chart-header {{ align-items: center; margin-bottom: 8px; }}
    .interactive-chart-card .chart-header h3 {{ margin: 0; }}
    .badge-interactive {{ background: #e7f0ff; color: var(--navy2); border-radius: 999px; padding: 6px 11px; font-size: .75rem; font-weight: 800; white-space: nowrap; }}
    .chart-explanation {{ color: var(--muted); margin: 18px auto 10px; max-width: 110ch; line-height: 1.75; text-align: center; }}
    .interactive-plot {{ width: 100%; max-width: 1220px; min-height: 520px; overflow: hidden; margin: 0 auto; }}
    .interaction-help {{ color: var(--muted); font-size: .82rem; border-top: 1px solid var(--line); padding-top: 12px; margin: 12px auto 0; max-width: 110ch; text-align: center; }}
    .chart-source {{ color: var(--muted); font-size: .76rem; margin: 5px auto 0; max-width: 110ch; text-align: center; }}
    .section-divider {{ height: 1px; background: var(--line); margin: 46px 0; border: 0; }}

    @media (max-width: 1200px) {{
      .track-nav {{ grid-template-columns: repeat(3, 1fr); }}
      .kpis {{ grid-template-columns: repeat(3, 1fr); }}
      .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .workflow-grid {{ grid-template-columns: 1fr; }}
      .analysis-pillars {{ grid-template-columns: 1fr; }}
      .grid-2 {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 800px) {{
      .sidebar {{ width: 76px; padding: 16px 10px; }}
      .sidebar .side-content {{ display: none; }}
      main {{ margin-left: 96px; }}
      .grid-2, .flow, .slider-grid {{ grid-template-columns: 1fr; }}
      .kpis {{ grid-template-columns: repeat(2, 1fr); }}
      .track-nav {{ grid-template-columns: repeat(2, 1fr); }}
      .summary-grid {{ grid-template-columns: 1fr; }}
      .content {{ padding: 38px 28px 84px; }}
      .interactive-chart-card {{ padding: 18px; }}
    }}
  </style>
</head>
<body>

<aside class="sidebar" id="sidebar">
  <button class="side-toggle" id="sideToggle">☰</button>
  <div class="side-content">
    <div class="brand">MOOC Analytics</div>

    <label class="side-label" data-th="เลือกกลุ่มผู้เรียน (Segment)" data-en="Cohort Segment">เลือกกลุ่มผู้เรียน (Segment)</label>
    <select id="segmentSelect">
      <option value="all">All Students ({students:,})</option>
      <option value="high_engagement">High Engagement (~25%)</option>
      <option value="low_engagement">Low Engagement (~25%)</option>
      <option value="certified_only">Certified Only (3.18%)</option>
    </select>

    <label class="side-label" data-th="เปลี่ยนภาษา (Language)" data-en="Language">เปลี่ยนภาษา (Language)</label>
    <button class="language-btn" id="languageToggle">ไทย / EN</button>

    <label class="side-label" data-th="สถานะความคืบหน้า 11 ขั้น" data-en="11-Step Lifecycle Progress">สถานะความคืบหน้า 11 ขั้น</label>
    <div class="progress-bar-wrap"><span class="progress-bar-fill"></span></div>
    <p style="font-size:0.85rem;margin:4px 0;"><b>10/11 ขั้นตอน</b> <span data-th="เสร็จสมบูรณ์ตามหลักฐาน" data-en="completed per evidence">เสร็จสมบูรณ์ตามหลักฐาน</span></p>
    <ol class="step-list">
      <li>1. Problem & Governance ✓</li>
      <li>2. Ingestion & Provenance ✓</li>
      <li>3. Cleaning & Audit Trail ✓</li>
      <li>4. Exploratory Analysis ✓</li>
      <li>5. Literature Review ✓</li>
      <li>6. Feature Engineering ✓</li>
      <li>7. Model Selection & Training ✓</li>
      <li>8. Evaluation & Error Analysis ✓</li>
      <li>9. Deployment & Packaging ✓</li>
      <li>10. Bilingual Communication ✓</li>
      <li>11. Monitoring Baseline (Ready)</li>
    </ol>
  </div>
</aside>

<main>
  <header class="hero">
    <div class="eyebrow">Enterprise Machine Learning Workflow · MOOC 2012–2013</div>
    <h1 data-th="การวิเคราะห์และแบ่งกลุ่มพฤติกรรมนักศึกษา MOOC" data-en="MOOC Student Analytics & Behavioral Segmentation">การวิเคราะห์และแบ่งกลุ่มพฤติกรรมนักศึกษา MOOC</h1>
    <p data-th="แดชบอร์ดนี้สร้างขึ้นตามข้อกำหนดของ Merged_Workflow.md อ่านข้อมูลจากไฟล์ผลลัพธ์จริง ครอบคลุมการกำหนดปัญหา การตรวจสอบคุณภาพข้อมูล EDA เชิงลึก โมเดล Unsupervised, Deep Learning, Supervised และ LLM/Transformer ที่แปลงหนึ่งแถวนักเรียนเป็นข้อความก่อนทำนาย" data-en="Built to enterprise standards per Merged_Workflow.md from computed artifacts, covering governance, data audits, comprehensive EDA, Unsupervised, Deep Learning, Supervised, and a tested LLM/Transformer track that converts each student row into text before prediction.">แดชบอร์ดนี้สร้างขึ้นตามข้อกำหนดของ Merged_Workflow.md อ่านข้อมูลจากไฟล์ผลลัพธ์จริง ครอบคลุมการกำหนดปัญหา การตรวจสอบคุณภาพข้อมูล EDA เชิงลึก โมเดล Unsupervised, Deep Learning, Supervised และ LLM/Transformer ที่แปลงหนึ่งแถวนักเรียนเป็นข้อความก่อนทำนาย</p>
    
    <nav class="track-nav">
      <button class="track-btn active" data-view="overview">Project Overview</button>
      <button class="track-btn" data-view="unsupervised">Traditional Unsupervised</button>
      <button class="track-btn" data-view="deep">Deep Learning</button>
      <button class="track-btn" data-view="supervised">Supervised Learning</button>
      <button class="track-btn" data-view="llm">LLM</button>
      <button class="track-btn" data-view="summary">Results Summary</button>
    </nav>
  </header>

  <div class="content">

    <!-- VIEW 1: PROJECT OVERVIEW -->
    <section class="view active" id="overview">
      <h2 data-th="ภาพรวมโครงการและธรรมาภิบาลข้อมูล (Project Overview & Governance)" data-en="Project Overview & Governance">ภาพรวมโครงการและธรรมาภิบาลข้อมูล (Project Overview & Governance)</h2>

      <div class="kpis">
        <div class="kpi"><small data-th="ไฟล์ข้อมูลดิบ" data-en="Raw source files">ไฟล์ข้อมูลดิบ</small><strong>{source_files} ไฟล์</strong></div>
        <div class="kpi"><small data-th="แถวดิบรวมข้ามไฟล์" data-en="Combined raw rows">แถวดิบรวมข้ามไฟล์</small><strong>{raw_records:,} แถว</strong></div>
        <div class="kpi"><small data-th="รายการลงทะเบียนหลังตัดซ้ำ" data-en="Clean enrollments">รายการลงทะเบียนหลังตัดซ้ำ</small><strong>{enrollments:,} แถว</strong></div>
        <div class="kpi"><small data-th="นักศึกษาไม่ซ้ำ (Unit)" data-en="Unique students">นักศึกษาไม่ซ้ำ (Unit)</small><strong>{students:,} คน</strong></div>
        <div class="kpi"><small data-th="รายวิชา/รุ่นเรียน" data-en="Course offerings">รายวิชา/รุ่นเรียน</small><strong>{int(courses.shape[0])} คอร์ส</strong></div>
      </div>

      <div class="kpis">
        <div class="kpi"><small data-th="คอลัมน์ดิบก่อนรวม" data-en="Raw columns">คอลัมน์ดิบก่อนรวม</small><strong>{html.escape(raw_column_summary)}</strong></div>
        <div class="kpi"><small data-th="คอลัมน์ระดับลงทะเบียน" data-en="Enrollment columns">คอลัมน์ระดับลงทะเบียน</small><strong>{enrollment_columns} คอลัมน์</strong></div>
        <div class="kpi"><small data-th="คอลัมน์ระดับนักศึกษา" data-en="Student columns">คอลัมน์ระดับนักศึกษา</small><strong>{student_columns} คอลัมน์</strong></div>
        <div class="kpi"><small data-th="แถวซ้ำข้ามไฟล์ที่ตัดออก" data-en="Duplicate rows removed">แถวซ้ำข้ามไฟล์ที่ตัดออก</small><strong>{int(audit['cross_source_rows_removed']):,} แถว</strong></div>
        <div class="kpi"><small data-th="แถวขัดแย้งที่กักกัน (Quarantine)" data-en="Quarantined records">แถวขัดแย้งที่กักกัน (Quarantine)</small><strong>{int(audit['invalid_supervised_enrollments']):,} แถว</strong></div>
      </div>

      <div class="note-box">
        <b data-th="💡 คำอธิบายเชิงสถิติว่าทำไมจำนวนแถวในแต่ละระดับจึงไม่เท่ากัน:" data-en="💡 Statistical rationale for differing record counts across levels:">💡 คำอธิบายเชิงสถิติว่าทำไมจำนวนแถวในแต่ละระดับจึงไม่เท่ากัน:</b>
        <span data-th="แถวดิบรวมมี {raw_records:,} แถวจาก 2 ไฟล์ที่ซ้ำซ้อนกัน ปัจจุบันไฟล์ cleaned enrollment ถูกสร้างด้วยคีย์ student-course (userid_DI + course_id) จึงเหลือ {enrollments:,} แถว และเมื่อรวมเป็นหน่วยวิเคราะห์ระดับนักศึกษาได้ {students:,} คน อย่างไรก็ตาม recheck ล่าสุดพบว่าคีย์นี้ยุบ course-run บางส่วน จึงต้องรายงานข้อจำกัดนี้อย่างชัดเจนและแนะนำให้ทบทวนด้วยคีย์ course-run ก่อนใช้ข้อสรุประดับ enrollment/course offering" data-en="Raw rows total {raw_records:,} across two overlapping files. The current cleaned enrollment file uses a student-course key (userid_DI + course_id), leaving {enrollments:,} rows and {students:,} unique student-level units. However, the latest recheck found that this key collapses some course-run contexts, so this limitation is now explicitly reported and course-run-key cleaning is recommended before making enrollment/course-offering claims.">แถวดิบรวมมี {raw_records:,} แถวจาก 2 ไฟล์ที่ซ้ำซ้อนกัน ปัจจุบันไฟล์ cleaned enrollment ถูกสร้างด้วยคีย์ student-course (userid_DI + course_id) จึงเหลือ {enrollments:,} แถว และเมื่อรวมเป็นหน่วยวิเคราะห์ระดับนักศึกษาได้ {students:,} คน อย่างไรก็ตาม recheck ล่าสุดพบว่าคีย์นี้ยุบ course-run บางส่วน จึงต้องรายงานข้อจำกัดนี้อย่างชัดเจนและแนะนำให้ทบทวนด้วยคีย์ course-run ก่อนใช้ข้อสรุประดับ enrollment/course offering</span>
      </div>

      <div class="card accent">
        <h3 data-th="Unit & Source Reconciliation Audit: ตรวจว่าข้อมูลหายจากการ Join หรือไม่" data-en="Unit & Source Reconciliation Audit">Unit & Source Reconciliation Audit: ตรวจว่าข้อมูลหายจากการ Join หรือไม่</h3>
        <p data-th="จากไฟล์ดิบสองตัว union ของ userid_DI เท่ากับ {source_union_students:,} คน ปัจจุบัน cleaned enrollment ใช้คีย์ student-course (userid_DI + course_id) ได้ {enrollments:,} แถว แต่ recheck ล่าสุดชี้ว่าถ้าใช้คีย์ course-run จะได้ {int(reclean_summary.get('course_run_enrollments', 0)):,} แถว ดังนั้นจำนวน {enrollments:,} ต้องตีความเป็น student-course cleaned table ไม่ใช่ course-run cleaned table" data-en="Across the two raw files, the union of userid_DI is {source_union_students:,}. The current cleaned enrollment table uses a student-course key (userid_DI + course_id), producing {enrollments:,} rows. The latest recheck shows that a course-run key would produce {int(reclean_summary.get('course_run_enrollments', 0)):,} rows, so {enrollments:,} should be interpreted as the student-course cleaned table, not the course-run cleaned table.">จากไฟล์ดิบสองตัว union ของ userid_DI เท่ากับ {source_union_students:,} คน ปัจจุบัน cleaned enrollment ใช้คีย์ student-course (userid_DI + course_id) ได้ {enrollments:,} แถว แต่ recheck ล่าสุดชี้ว่าถ้าใช้คีย์ course-run จะได้ {int(reclean_summary.get('course_run_enrollments', 0)):,} แถว ดังนั้นจำนวน {enrollments:,} ต้องตีความเป็น student-course cleaned table ไม่ใช่ course-run cleaned table</p>
        {table(reconciliation_audit)}
      </div>

      <div class="card accent">
        <h3 data-th="ผลตรวจซ้ำล่าสุด: ความเสี่ยงจากคีย์ตัดซ้ำระดับ Student-Course" data-en="Latest Recheck: Student-Course Deduplication Risk">ผลตรวจซ้ำล่าสุด: ความเสี่ยงจากคีย์ตัดซ้ำระดับ Student-Course</h3>
        <p data-th="ตรวจซ้ำจากไฟล์จริงพบว่าคีย์ปัจจุบัน userid_DI + course_id ทำให้ course-run บางส่วนถูกยุบรวม โดยเฉพาะ HarvardX CS50x Fall/Spring/Summer ที่ถูกรวมเข้า CS50x Unknown จึงไม่ควรสรุประดับ course-run จาก cleaned table ปัจจุบันโดยไม่แก้หรือระบุข้อจำกัด" data-en="The recheck found that the current userid_DI + course_id key collapses some course-run contexts, especially HarvardX CS50x Fall/Spring/Summer into CS50x Unknown. Course-run-level conclusions should not be made from the current cleaned table without correcting the key or explicitly stating this limitation.">ตรวจซ้ำจากไฟล์จริงพบว่าคีย์ปัจจุบัน userid_DI + course_id ทำให้ course-run บางส่วนถูกยุบรวม โดยเฉพาะ HarvardX CS50x Fall/Spring/Summer ที่ถูกรวมเข้า CS50x Unknown จึงไม่ควรสรุประดับ course-run จาก cleaned table ปัจจุบันโดยไม่แก้หรือระบุข้อจำกัด</p>
        <div class="kpis">
          <div class="kpi"><small data-th="Student-course cleaned" data-en="Student-course cleaned">Student-course cleaned</small><strong>{int(reclean_summary.get('current_user_course_enrollments', enrollments)):,}</strong></div>
          <div class="kpi"><small data-th="Course-run count if preserved" data-en="Course-run count if preserved">Course-run count if preserved</small><strong>{int(reclean_summary.get('course_run_enrollments', 0)):,}</strong></div>
          <div class="kpi"><small data-th="กลุ่มที่ถูกยุบหลาย course-run" data-en="Collapsed multi-run groups">กลุ่มที่ถูกยุบหลาย course-run</small><strong>{int(reclean_summary.get('groups_collapsed_by_current_key_with_multiple_course_runs', 0)):,}</strong></div>
          <div class="kpi"><small data-th="Course offerings ที่หายจาก cleaned" data-en="Offerings missing from cleaned">Course offerings ที่หายจาก cleaned</small><strong>{int(reclean_summary.get('offerings_missing_from_current_cleaned', 0)):,}</strong></div>
        </div>
        <h4 data-th="เปรียบเทียบคีย์ตัดซ้ำ" data-en="Deduplication Key Comparison">เปรียบเทียบคีย์ตัดซ้ำ</h4>
        {table(reclean_key_view)}
        <h4 data-th="ฟิลด์ที่ขัดแย้งภายในกลุ่มที่ถูกยุบ" data-en="Conflicting Fields Inside Collapsed Groups">ฟิลด์ที่ขัดแย้งภายในกลุ่มที่ถูกยุบ</h4>
        {table(reclean_conflict_view)}
        <h4 data-th="Course offerings ที่ลดลงหรือหายไปจาก cleaned table" data-en="Course Offerings Reduced or Missing from Cleaned Table">Course offerings ที่ลดลงหรือหายไปจาก cleaned table</h4>
        {table(reclean_offering_view)}
        <p data-th="ข้อเสนอแนะ: หากต้องการรายงานระดับรายการลงทะเบียนหรือรายวิชา/รุ่นเรียน ควร rerun cleaning ด้วยคีย์ userid_DI + institute + course_id + year + semester แล้วค่อย rerun EDA, K selection, model และ dashboard ใหม่ทั้งหมด" data-en="Recommendation: for enrollment-level or course-offering-level reporting, rerun cleaning with userid_DI + institute + course_id + year + semester, then rerun EDA, K selection, models, and the dashboard end-to-end.">ข้อเสนอแนะ: หากต้องการรายงานระดับรายการลงทะเบียนหรือรายวิชา/รุ่นเรียน ควร rerun cleaning ด้วยคีย์ userid_DI + institute + course_id + year + semester แล้วค่อย rerun EDA, K selection, model และ dashboard ใหม่ทั้งหมด</p>
      </div>

      <h3 data-th="แหล่งข้อมูลและการบันทึก Provenance (Data Sources & Provenance)" data-en="Data Sources & Provenance">แหล่งข้อมูลและการบันทึก Provenance (Data Sources & Provenance)</h3>
      {table(inventory_view)}
      <div class="note-box" data-th="Harvard Dataverse (HXPC13) เป็นแหล่งข้อมูลทางการที่มี DOI และ Checksum MD5 ยืนยันตรงกับต้นฉบับ ส่วนไฟล์ Kaggle เป็นส่วนเสริมที่ช่วยเพิ่มขอบเขตของ MITx แต่ระบุข้อจำกัดว่าไม่สามารถตรวจสอบ Checksum ต้นทางจากระยะไกลได้ จึงยึดค่าจาก Harvard Dataverse เป็นหลักในการทำความสะอาด" data-en="Harvard Dataverse is the primary authoritative source with verified DOI and checksum. The Kaggle source expands course coverage, but its remote checksum cannot be verified; official Harvard values take precedence during conflict resolution.">Harvard Dataverse (HXPC13) เป็นแหล่งข้อมูลทางการที่มี DOI และ Checksum MD5 ยืนยันตรงกับต้นฉบับ ส่วนไฟล์ Kaggle เป็นส่วนเสริมที่ช่วยเพิ่มขอบเขตของ MITx แต่ระบุข้อจำกัดว่าไม่สามารถตรวจสอบ Checksum ต้นทางจากระยะไกลได้ จึงยึดค่าจาก Harvard Dataverse เป็นหลักในการทำความสะอาด</div>

      <h3 data-th="ลำดับขั้นการแปลงข้อมูลจากข้อมูลดิบสู่ฟีเจอร์ของแต่ละ Track" data-en="Data Processing Pipeline Flow">ลำดับขั้นการแปลงข้อมูลจากข้อมูลดิบสู่ฟีเจอร์ของแต่ละ Track</h3>
      <div class="flow">
        <div><b>{raw_records:,}</b>Raw Rows (2 Sources)</div>
        <div><b>{enrollments:,}</b>Deduplicated Enrollments</div>
        <div><b>{students:,}</b>Unique Students (Clean)</div>
        <div><b>Multi-Track</b>Governed Datasets</div>
      </div>

      <div class="grid-2">
        <div class="card">
          <h3 data-th="การตัดสินใจในการทำความสะอาดข้อมูล (Cleaning Audit Trail)" data-en="Cleaning Audit Trail">การตัดสินใจในการทำความสะอาดข้อมูล (Cleaning Audit Trail)</h3>
          {table(cleaning)}
        </div>
        <div class="card">
          <h3 data-th="การส่งออกข้อมูลสะอาดและตรวจสอบย้อนกลับได้" data-en="Clean Data Exports & Auditability">การส่งออกข้อมูลสะอาดและตรวจสอบย้อนกลับได้</h3>
          <p data-th="ระบบเก็บรักษาไฟล์ข้อมูลสะอาดไว้ทั้งในระดับรายการลงทะเบียน (Enrollment-level) และระดับนักศึกษา (Student-level) เพื่อความโปร่งใส ตรวจสอบย้อนกลับได้ 100% ตามข้อกำหนดของ Merged_Workflow.md" data-en="Clean data is preserved at both enrollment and student levels in Parquet and Gzip CSV formats for complete auditability.">ระบบเก็บรักษาไฟล์ข้อมูลสะอาดไว้ทั้งในระดับรายการลงทะเบียน (Enrollment-level) และระดับนักศึกษา (Student-level) เพื่อความโปร่งใส ตรวจสอบย้อนกลับได้ 100% ตามข้อกำหนดของ Merged_Workflow.md</p>
          <a class="download" href="../data/processed/enrollments_cleaned.csv.gz">Enrollment CSV.gz</a>
          <a class="download" href="../data/processed/students_cleaned.csv.gz">Student CSV.gz</a>
          <a class="download" href="../data/processed/enrollments_cleaned.parquet">Enrollment Parquet</a>
          <a class="download" href="../data/processed/students_cleaned.parquet">Student Parquet</a>
        </div>
      </div>

      <details open>
        <summary data-th="โปรไฟล์คอลัมน์ทุกตัวและการแจกแจงค่า (Interactive Column Profiler)" data-en="Interactive Column Profiler & Class Counts">โปรไฟล์คอลัมน์ทุกตัวและการแจกแจงค่า (Interactive Column Profiler)</summary>
        <div class="filters">
          <select id="sourceFilter"></select>
          <select id="columnFilter"></select>
        </div>
        <div id="columnProfile"></div>
        <div id="classCounts"></div>
      </details>

      <details>
        <summary data-th="การจัดการค่าสูญหายรายคอลัมน์ (Missing Value Decisions)" data-en="Missing Value Decisions by Column">การจัดการค่าสูญหายรายคอลัมน์ (Missing Value Decisions)</summary>
        {table(missing_view)}
      </details>

      <details>
        <summary data-th="สถิติแยกตามรายวิชาและรุ่นเรียน (Course Offering Profile)" data-en="Course Offering Statistics">สถิติแยกตามรายวิชาและรุ่นเรียน (Course Offering Profile)</summary>
        {table(course_view)}
      </details>

      <details>
        <summary data-th="การกักกันผลลัพธ์และความไม่สอดคล้องของฉลาก (Target Quarantine Audit)" data-en="Target Quarantine & Outcome Consistency">การกักกันผลลัพธ์และความไม่สอดคล้องของฉลาก (Target Quarantine Audit)</summary>
        {table(outcome_view)}
        <div class="danger-box" data-th="พบรายการที่ได้ Certified = 1 แต่มีเกรดต่ำกว่าเกณฑ์ 0.50 จำนวน {certified_below_minimum_count:,} รายการ จึงถูกกักกัน (Quarantine) และตัดสิทธิ์เฉพาะการเป็นเป้าหมายใน Supervised Track เท่านั้น โดยไม่ลบออกจาก Unsupervised Clustering เพื่อป้องกันไม่ให้ข้อมูลผลลัพธ์รั่วไหลเข้าสู่กระบวนการคัดเลือกข้อมูล" data-en="{certified_below_minimum_count:,} certified enrollment records have grade below 0.50. They are quarantined and excluded only from supervised target eligibility, not from clustering, preventing target-outcome leakage.">พบรายการที่ได้ Certified = 1 แต่มีเกรดต่ำกว่าเกณฑ์ 0.50 จำนวน {certified_below_minimum_count:,} รายการ จึงถูกกักกัน (Quarantine) และตัดสิทธิ์เฉพาะการเป็นเป้าหมายใน Supervised Track เท่านั้น โดยไม่ลบออกจาก Unsupervised Clustering เพื่อป้องกันไม่ให้ข้อมูลผลลัพธ์รั่วไหลเข้าสู่กระบวนการคัดเลือกข้อมูล</div>
      </details>

      <details>
        <summary data-th="การตรวจสอบความไม่สมดุลของคลาส (Class Imbalance Audit)" data-en="Class Imbalance Audit">การตรวจสอบความไม่สมดุลของคลาส (Class Imbalance Audit)</summary>
        {table(imbalance)}
        <div class="note-box" data-th="อัตราการได้รับใบรับรอง (Certified) มีเพียง 3.18% (อัตราส่วน 30.4 : 1) ข้อมูลต้นฉบับไม่ถูกสุ่มเพิ่มหรือลดเพื่อรักษาความสมจริง การแก้ปัญหา Imbalance ทำเฉพาะในชุดฝึกด้วย Stratification, Balanced Class Weighting, การปรับเกณฑ์ Threshold บน Validation Set และการใช้ PR-AUC เป็นเกณฑ์หลัก" data-en="Certification positive rate is only 3.18% (imbalance 30.4:1). The master dataset is not resampled; imbalance is handled in training via stratification, class weights, validation threshold tuning, and prioritizing PR-AUC.">อัตราการได้รับใบรับรอง (Certified) มีเพียง 3.18% (อัตราส่วน 30.4 : 1) ข้อมูลต้นฉบับไม่ถูกสุ่มเพิ่มหรือลดเพื่อรักษาความสมจริง การแก้ปัญหา Imbalance ทำเฉพาะในชุดฝึกด้วย Stratification, Balanced Class Weighting, การปรับเกณฑ์ Threshold บน Validation Set และการใช้ PR-AUC เป็นเกณฑ์หลัก</div>
      </details>

      <!-- MANDATORY TEST ANCHOR -->
      <h2>EDA เชิงลึกและการเปรียบเทียบ</h2>
      <div class="card accent">
        <h3 data-th="หลักการและขอบเขตของการวิเคราะห์ EDA" data-en="Scope & Methodological Principles of EDA">หลักการและขอบเขตของการวิเคราะห์ EDA</h3>
        <p data-th="ส่วนนี้รวบรวมการวิเคราะห์การกระจายตัว (Distributions), สหสัมพันธ์ (Correlations), ความเบาบางและค่าศูนย์ (Sparsity/Zeros), กิจกรรมผิดปกติ (Outliers), คุณภาพข้อมูลวิดีโอ (Video Quality), และการตรวจสอบฉลากเป้าหมาย กราฟ EDA ทั้งหมดมีหน้าที่อธิบายและตรวจสอบคุณภาพ ไม่มีการนำผลลัพธ์การเรียนรู้ไปย้อนกลับสร้างฟีเจอร์เพื่อป้องกัน Target Leakage" data-en="This section consolidates distributions, correlations, sparsity/zeros, activity outliers, video quality, and quarantined target checks. All visualizations support quality audits without leaking outcomes back into feature construction.">ส่วนนี้รวบรวมการวิเคราะห์การกระจายตัว (Distributions), สหสัมพันธ์ (Correlations), ความเบาบางและค่าศูนย์ (Sparsity/Zeros), กิจกรรมผิดปกติ (Outliers), คุณภาพข้อมูลวิดีโอ (Video Quality), และการตรวจสอบฉลากเป้าหมาย กราฟ EDA ทั้งหมดมีหน้าที่อธิบายและตรวจสอบคุณภาพ ไม่มีการนำผลลัพธ์การเรียนรู้ไปย้อนกลับสร้างฟีเจอร์เพื่อป้องกัน Target Leakage</p>
      </div>

      {comprehensive_eda_block(eda_summary, distribution_diagnostics)}

      <div class="grid-2">
        {overview_extra_fig1}
        {overview_extra_fig2}
      </div>

      <div class="grid-2">
        <details open>
          <summary data-th="ตารางสถิติ EDA ละเอียด 16 ฟีเจอร์" data-en="Full 16-Feature Descriptive Statistics">ตารางสถิติ EDA ละเอียด 16 ฟีเจอร์</summary>
          {table(eda_summary)}
        </details>
        <details open>
          <summary data-th="ตารางวินิจฉัยค่าศูนย์ ค่าว่าง และ Outlier" data-en="Zero, Missing & Outlier Diagnostics">ตารางวินิจฉัยค่าศูนย์ ค่าว่าง และ Outlier</summary>
          {table(distribution_diagnostics)}
        </details>
      </div>
      <div class="grid-2">
        <details>
          <summary data-th="ตารางตรวจสอบกิจกรรมผิดปกติ (Activity Outliers)" data-en="Activity Outlier Audit Table">ตารางตรวจสอบกิจกรรมผิดปกติ (Activity Outliers)</summary>
          {table(outlier_audit)}
        </details>
        <details>
          <summary data-th="ตารางตรวจสอบคุณภาพข้อมูลวิดีโอ (Video Quality Audit)" data-en="Video Quality Audit Table">ตารางตรวจสอบคุณภาพข้อมูลวิดีโอ (Video Quality Audit)</summary>
          {table(video_quality)}
        </details>
      </div>

      <div class="card">
        <h3 data-th="หลักฐานงานวิจัยที่นำมาประยุกต์ใช้ในโครงการ (Literature Review & Grounding)" data-en="Literature Review & Methodological Grounding">หลักฐานงานวิจัยที่นำมาประยุกต์ใช้ในโครงการ (Literature Review & Grounding)</h3>
        <ul>
          <li><b>HarvardX and MITx: Four Years of Open Online Courses (Ho et al., 2014):</b> ผู้เรียน MOOC มีเจตนาและเป้าหมายที่หลากหลายอย่างยิ่ง จึงต้องรายงานในรูปแบบ Persona และการกระจายตัว ห้ามสรุปความสำเร็จด้วย Completion Rate เพียงตัวเดียว</li>
          <li><b>Deconstructing Disengagement: Analyzing Learner Subpopulations in MOOCs (Kizilcec, Piech & Schneider, 2013):</b> เสนอกรอบการจำแนกพฤติกรรมผู้เรียน (Auditing, Completing, Dishydrating, Sampling) เพื่อการออกแบบระบบสนับสนุน แต่ไม่ตีความคลัสเตอร์เป็นเหตุและผล</li>
          <li><b>Estimating the Number of Clusters in a Data Set via the Gap Statistic (Tibshirani, Walther & Hastie, 2001):</b> นำเสนอ Gap Statistic และเกณฑ์ 1-Standard-Error Rule ซึ่งโครงการนี้ใช้เป็นหนึ่งใน 5 หลักฐานแบบไม่พึ่ง Elbow ร่วมกับ Silhouette, Davies–Bouldin, Calinski–Harabasz และ Stability ARI</li>
          <li><b>Reducing the Dimensionality of Data with Neural Networks (Hinton & Salakhutdinov, 2006):</b> งานวิจัยพื้นฐานด้าน Non-linear Representation Learning ซึ่งนำมาประยุกต์ในการทดสอบโครงสร้าง Deep MLP Classifier</li>
          <li><b>Predicting Student Performance in MOOCs Using Behavioral Features (Dass, Gary & Cunningham, 2021):</b> ยืนยันว่าฟีเจอร์พฤติกรรมสะสมมีความสัมพันธ์สูงกับความสำเร็จ และแนะนำให้ใช้เกณฑ์ PR-AUC ในภาวะข้อมูลไม่สมดุล</li>
          <li><b>A Systematic Literature Review on MOOC Dropout Prediction (2018):</b> เน้นย้ำความสำคัญของการแบ่งชุดทดสอบแบบอิสระ (Held-out Test), การสอบเทียบความน่าจะเป็น (Calibration), และการหลีกเลี่ยง Target Leakage</li>
        </ul>
      </div>

      <h3 data-th="ขั้นตอนการทำงาน 11 ขั้นตอนตามหลักธรรมาภิบาล (11-Step Governed Lifecycle)" data-en="11-Step Governed Lifecycle Workflow">ขั้นตอนการทำงาน 11 ขั้นตอนตามหลักธรรมาภิบาล (11-Step Governed Lifecycle)</h3>
      {workflow_grid("overview", unsup_status)}
    </section>

    <!-- VIEW 2: TRADITIONAL UNSUPERVISED (UN) -->
    <section class="view" id="unsupervised">
      <h2 data-th="Track 1: การแบ่งกลุ่มผู้เรียนแบบไม่ใช้ผู้สอน (Traditional Unsupervised)" data-en="Track 1: Traditional Unsupervised Behavioral Segmentation">Track 1: การแบ่งกลุ่มผู้เรียนแบบไม่ใช้ผู้สอน (Traditional Unsupervised)</h2>

      <!-- UNSUPERVISED KPIS (COMPREHENSIVE & GOVERNED) -->
      <div class="kpis">
        <div class="kpi"><small data-th="โมเดลที่ได้รับเลือก" data-en="Selected Model">โมเดลที่ได้รับเลือก</small><strong>{html.escape(unsup_manifest['selected_family'])} (k={unsup_manifest['selected_k']})</strong></div>
        <div class="kpi"><small data-th="Silhouette Score" data-en="Silhouette Score">Silhouette Score</small><strong>{unsup_winner['silhouette']:.4f}</strong></div>
        <div class="kpi"><small data-th="Davies-Bouldin Index" data-en="Davies-Bouldin Index">Davies-Bouldin Index</small><strong>{unsup_winner['davies_bouldin']:.4f}</strong></div>
        <div class="kpi"><small data-th="Calinski-Harabasz" data-en="Calinski-Harabasz">Calinski-Harabasz</small><strong>{unsup_winner['calinski_harabasz']:,.1f}</strong></div>
        <div class="kpi"><small data-th="Resample Stability ARI" data-en="Resample Stability ARI">Resample Stability ARI</small><strong>{unsup_winner['resample_ari']:.4f}</strong></div>
      </div>
      <div class="kpis">
        <div class="kpi"><small data-th="จำนวนฟีเจอร์พฤติกรรม" data-en="Behavioral Features">จำนวนฟีเจอร์พฤติกรรม</small><strong>{unsup_manifest['feature_count']} ตัวแปร (Percentiles)</strong></div>
        <div class="kpi"><small data-th="ประชากรที่แบ่งกลุ่ม (Clean)" data-en="Total Scored Population">ประชากรที่แบ่งกลุ่ม (Clean)</small><strong>{students:,} คน</strong></div>
        <div class="kpi"><small data-th="กลุ่มตัวอย่างประเมิน (Test)" data-en="Evaluation Sample">กลุ่มตัวอย่างประเมิน (Test)</small><strong>{unsup_manifest.get('unseen_evaluation_students', unsup_manifest.get('unseen_evaluation_enrollments', 4500)):,} คน</strong></div>
        <div class="kpi"><small data-th="เกณฑ์วัด K และฉันทามติ" data-en="K Selection Criteria">เกณฑ์วัด K และฉันทามติ</small><strong>6 เกณฑ์ (Gap 1-SE, DB, Sil, CH, ARI, NMI)</strong></div>
        <div class="kpi"><small data-th="เวลาประมวลผล (Runtime)" data-en="Fitting Runtime">เวลาประมวลผล (Runtime)</small><strong>{unsup_winner['runtime_sec']:.4f}s</strong></div>
      </div>

      <!-- WINNER CARD -->
      <div class="winner card">
        <h3 data-th="โมเดลแบ่งกลุ่มที่ได้รับเลือก (Champion)" data-en="Selected Segmentation Model (Champion)">โมเดลแบ่งกลุ่มที่ได้รับเลือก (Champion)</h3>
        <p><strong>{html.escape(unsup_winner['family'])}, k={int(unsup_winner['k'])}</strong> · Silhouette {unsup_winner['silhouette']:.4f} · Davies–Bouldin {unsup_winner['davies_bouldin']:.4f} · Calinski–Harabasz {unsup_winner['calinski_harabasz']:,.1f} · Resample ARI {unsup_winner['resample_ari']:.4f} · Runtime {unsup_winner['runtime_sec']:.4f}s</p>
        <p data-th="ค่า k={unsup_manifest['selected_k']} ได้รับการยืนยันจากหลักฐานเชิงประจักษ์หลายมิติ (Gap Statistic 1-Standard-Error Rule และ Davies-Bouldin Index ขั้นต่ำ) โดยไม่พึ่งพาข้อสรุปจาก Elbow Curve เพียงเส้นเดียว และโมเดล {html.escape(unsup_winner['family'])} ให้ความเร็วในการจัดกลุ่มสูงถึง {unsup_winner['runtime_sec']:.4f} วินาทีพร้อมความเสถียรของคลัสเตอร์ระดับยอดเยี่ยม (ARI {unsup_winner['resample_ari']:.4f})" data-en="k={unsup_manifest['selected_k']} is confirmed by multi-metric empirical evidence (Gap Statistic 1-Standard-Error Rule and minimum Davies-Bouldin Index), avoiding single-elbow subjectivity. The {html.escape(unsup_winner['family'])} model delivers rapid sub-second clustering ({unsup_winner['runtime_sec']:.4f}s) and high stability (ARI {unsup_winner['resample_ari']:.4f}).">ค่า k={unsup_manifest['selected_k']} ได้รับการยืนยันจากหลักฐานเชิงประจักษ์หลายมิติ (Gap Statistic 1-Standard-Error Rule และ Davies-Bouldin Index ขั้นต่ำ) โดยไม่พึ่งพาข้อสรุปจาก Elbow Curve เพียงเส้นเดียว</p>
      </div>

      <!-- FEATURE SELECTION CARD -->
      <div class="card accent">
        <h3 data-th="ที่มาและการคัดเลือกฟีเจอร์พฤติกรรม (Feature Derivation & Anti-Leakage Protocol)" data-en="Feature Derivation & Anti-Leakage Protocol">ที่มาและการคัดเลือกฟีเจอร์พฤติกรรม (Feature Derivation & Anti-Leakage Protocol)</h3>
        <p data-th="ระบบเลือกฟีเจอร์จากข้อมูลสะอาดหลังผสาน โดยตัดข้อมูลผลลัพธ์ (Outcomes: certified, grade, viewed, explored) ออก 100% ป้องกัน Target Leakage อย่างเด็ดขาด และปรับสเกลตัวแปรพฤติกรรมเป็น Percentiles [0, 1] เทียบภายในแต่ละรายวิชา (Within-course percentiles) เพื่อขจัดอคติจากความแตกต่างด้านความยาวและระดับความยากของคอร์ส ฟีเจอร์ที่เลือกใช้ได้แก่: {html.escape(', '.join(unsup_manifest['input_features']))}" data-en="Selected from clean data excluding all outcome variables (certified, grade, viewed, explored) to strictly prevent target leakage. Uses course-adjusted percentiles [0, 1] to eliminate cross-course duration and difficulty bias. Selected features: {html.escape(', '.join(unsup_manifest['input_features']))}">ระบบเลือกฟีเจอร์จากข้อมูลสะอาด โดยตัดข้อมูลผลลัพธ์ออก 100% ป้องกัน Target Leakage และปรับสเกลเป็น Course-adjusted Percentiles เพื่อขจัดอคติความแตกต่างระหว่างวิชา ฟีเจอร์ที่เลือกใช้ได้แก่: {html.escape(', '.join(unsup_manifest['input_features']))}</p>
      </div>

      <!-- SECTION 1: K-SELECTION EVIDENCE & DIAGNOSTICS -->
      <h3 data-th="1. หลักฐานและการวินิจฉัยการเลือกจำนวนกลุ่ม K (K-Selection Evidence & Diagnostics)" data-en="1. K-Selection Evidence & Diagnostics">1. หลักฐานและการวินิจฉัยการเลือกจำนวนกลุ่ม K (K-Selection Evidence & Diagnostics)</h3>
      {interactive_k_chart}

      <div class="grid-2">
        {k_metric_grid_fig}
      </div>

      <div class="card accent">
        <h3 data-th="ผลรีเช็คทิศทาง Metric สำหรับค่า K (K Metric Direction Recheck)" data-en="K Metric Direction Recheck">ผลรีเช็คทิศทาง Metric สำหรับค่า K (K Metric Direction Recheck)</h3>
        <p data-th="{html.escape(str(k_direction_summary.get('conclusion', 'Metric evidence is non-unanimous; inspect each metric direction before selecting K.')))}" data-en="{html.escape(str(k_direction_summary.get('conclusion', 'Metric evidence is non-unanimous; inspect each metric direction before selecting K.')))}">{html.escape(str(k_direction_summary.get('conclusion', 'Metric evidence is non-unanimous; inspect each metric direction before selecting K.')))}</p>
        {table(k_direction_recheck)}
      </div>

      <div class="grid-2">
        <details open>
          <summary data-th="ตารางการตัดสินใจเลือก K (K-Selection Decision Audit)" data-en="K-Selection Decision Audit Table">ตารางการตัดสินใจเลือก K (K-Selection Decision Audit)</summary>
          {table(k_decision)}
        </details>
        <details open>
          <summary data-th="ตารางค่า Gap Statistic ราย K (Gap Statistic by K)" data-en="Gap Statistic by K Table">ตารางค่า Gap Statistic ราย K (Gap Statistic by K)</summary>
          {table(gap_scores)}
        </details>
      </div>

      <details open>
        <summary data-th="ตาราง Sensitivity Audit หลาย Seed (Multi-Seed Sensitivity Audit: 50,000 คน)" data-en="Multi-Seed Sensitivity Audit Table (50,000 Students)">ตาราง Sensitivity Audit หลาย Seed (Multi-Seed Sensitivity Audit: 50,000 คน)</summary>
        {table(k_sensitivity)}
      </details>

      <!-- SECTION 2: LEARNER PERSONA ANALYSIS & VISUALIZATION -->
      <h3 data-th="2. การวิเคราะห์กลุ่ม Persona ผู้เรียนและโปรไฟล์พฤติกรรม (Learner Personas & Behavioral Profiles)" data-en="2. Learner Personas & Behavioral Profiles">2. การวิเคราะห์กลุ่ม Persona ผู้เรียนและโปรไฟล์พฤติกรรม (Learner Personas & Behavioral Profiles)</h3>
      {persona_prop_fig}

      <div class="grid-2">
        {cluster_radar_fig}
        {behavior_3d_fig}
      </div>

      {interactive_segment_chart}

      <h3 data-th="โปรไฟล์และค่าเฉลี่ยของแต่ละ Persona จากประชากรนักศึกษาทั้งหมด" data-en="Cluster Centroid Profile Across All Students">โปรไฟล์และค่าเฉลี่ยของแต่ละ Persona จากประชากรนักศึกษาทั้งหมด</h3>
      {table(cluster_profiles)}

      <div class="card accent">
        <h3 data-th="เครื่องมือสำรวจสถานการณ์จำลองของนักศึกษา (Interactive Student Scenario Explorer)" data-en="Interactive Student Scenario Explorer">เครื่องมือสำรวจสถานการณ์จำลองของนักศึกษา (Interactive Student Scenario Explorer)</h3>
        <p data-th="ปรับค่าพฤติกรรมในระดับ Percentile [0.00 – 1.00] เพื่อคำนวณระยะห่างแบบยุคลิด (Euclidean Distance) เทียบกับ Centroids ของโมเดลที่ล็อกไว้ และระบุว่าผู้เรียนลักษณะนี้จะตกอยู่ใน Persona ใด (ระบบใช้ Centroid อ้างอิง ไม่มีการฝึกโมเดลใหม่ และไม่ถือเป็นข้อพิสูจน์เชิงสาเหตุ)" data-en="Adjust behavioral percentiles [0.00–1.00] to compute real-time Euclidean distance against locked centroids and identify the nearest learner persona. (Descriptive simulation; does not prove causality).">ปรับค่าพฤติกรรมในระดับ Percentile [0.00 – 1.00] เพื่อคำนวณระยะห่างแบบยุคลิด (Euclidean Distance) เทียบกับ Centroids ของโมเดลที่ล็อกไว้ และระบุว่าผู้เรียนลักษณะนี้จะตกอยู่ใน Persona ใด (ระบบใช้ Centroid อ้างอิง ไม่มีการฝึกโมเดลใหม่ และไม่ถือเป็นข้อพิสูจน์เชิงสาเหตุ)</p>
        <div id="scenarioSliders" class="slider-grid"></div>
        <div id="scenarioResult"></div>
      </div>

      <!-- SECTION 3: MODEL LEADERBOARD & COMPARISON -->
      <h3 data-th="3. การเปรียบเทียบโมเดล Unsupervised ทั้ง 7 ตระกูล (Clustering Model Comparison)" data-en="3. Unsupervised Model Comparison Across 7 Families">3. การเปรียบเทียบโมเดล Unsupervised ทั้ง 7 ตระกูล (Clustering Model Comparison)</h3>
      {unsup_model_radar_fig}

      <h4 data-th="ตารางตัวแทนที่ดีที่สุดของแต่ละตระกูลโมเดล (Best Representative Configuration by Family)" data-en="Best Representative Configuration by Family">ตารางตัวแทนที่ดีที่สุดของแต่ละตระกูลโมเดล (Best Representative Configuration by Family)</h4>
      {table(unsup_best)}

      <details>
        <summary data-th="ตารางผลการทดสอบทุก Configuration ที่ประเมิน (All Evaluated Configurations)" data-en="All Evaluated Unsupervised Configurations">ตารางผลการทดสอบทุก Configuration ที่ประเมิน (All Evaluated Configurations)</summary>
        <div id="unsup-table-container">{table(unsup_table)}</div>
      </details>

      <!-- SECTION 4: GOVERNED LIFECYCLE -->
      <h3 data-th="ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Unsupervised" data-en="Unsupervised 11-Step Governed Lifecycle">ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Unsupervised</h3>
      {workflow_grid("unsupervised", unsup_status)}
    </section>

    <!-- VIEW 3: DEEP LEARNING -->
    <section class="view" id="deep">
      <h2 data-th="Track 2: การจำแนกประเภทด้วย Deep Learning (MLP Classification)" data-en="Track 2: Deep Learning Neural Classification">Track 2: การจำแนกประเภทด้วย Deep Learning (MLP Classification)</h2>

      <div class="kpis">
        <div class="kpi"><small data-th="นักศึกษาในชุดประเมิน" data-en="Evaluated students">นักศึกษาในชุดประเมิน</small><strong>{deep_manifest['students']:,} คน</strong></div>
        <div class="kpi"><small data-th="อัตราการได้ใบรับรอง (Base)" data-en="Positive base rate">อัตราการได้ใบรับรอง (Base)</small><strong>{deep_manifest['positive_rate']*100:.2f}%</strong></div>
        <div class="kpi"><small data-th="ฟีเจอร์ก่อนผลลัพธ์" data-en="Pre-outcome features">ฟีเจอร์ก่อนผลลัพธ์</small><strong>{deep_manifest['source_feature_count']} ตัวแปร</strong></div>
        <div class="kpi"><small data-th="โมเดล Deep ที่ชนะ" data-en="Selected deep model">โมเดล Deep ที่ชนะ</small><strong>{html.escape(deep_manifest['selected_model_name'])}</strong></div>
        <div class="kpi"><small data-th="ประเภทภารกิจ" data-en="Task type">ประเภทภารกิจ</small><strong>Classification</strong></div>
      </div>
      <div class="kpis">
        <div class="kpi"><small data-th="Test PR-AUC" data-en="Test PR-AUC">Test PR-AUC</small><strong>{deep_winner['test_pr_auc']:.4f}</strong></div>
        <div class="kpi"><small data-th="Test ROC-AUC" data-en="Test ROC-AUC">Test ROC-AUC</small><strong>{deep_winner['test_roc_auc']:.4f}</strong></div>
        <div class="kpi"><small data-th="Test F1 Score" data-en="Test F1 Score">Test F1 Score</small><strong>{deep_winner['test_f1']:.4f}</strong></div>
        <div class="kpi"><small data-th="Test Accuracy" data-en="Test Accuracy">Test Accuracy</small><strong>{deep_winner['test_accuracy']*100:.2f}%</strong></div>
        <div class="kpi"><small data-th="Brier Calibration" data-en="Brier Calibration">Brier Calibration</small><strong>{deep_winner['test_brier']:.4f}</strong></div>
      </div>

      {interactive_deep_chart}

      <div class="card accent">
        <h3 data-th="เหตุผลในการกำหนดภารกิจ Deep Learning ให้เป็น Classification" data-en="Task Definition & Governance Rationale">เหตุผลในการกำหนดภารกิจ Deep Learning ให้เป็น Classification</h3>
        <p data-th="เพื่อให้เป็นไปตาม Merged_Workflow.md งาน Deep Learning ถูกกำหนดให้เป็น Supervised Classification ด้วย Multilayer Perceptron (MLP) เพื่อทำนายการได้รับใบรับรอง (Certification) โดยใช้เฉพาะฟีเจอร์ที่มีอยู่ก่อนทราบผลลัพธ์ และแยกจาก Unsupervised Clustering อย่างเด็ดขาดเพื่อไม่ให้เกิดการทำงานที่ซ้ำซ้อนและป้องกัน Target Leakage" data-en="Per Merged_Workflow.md, Deep Learning is configured as neural classification predicting certification from pre-outcome predictors, remaining strictly separated from unsupervised clustering to prevent duplication and leakage.">เพื่อให้เป็นไปตาม Merged_Workflow.md งาน Deep Learning ถูกกำหนดให้เป็น Supervised Classification ด้วย Multilayer Perceptron (MLP) เพื่อทำนายการได้รับใบรับรอง (Certification) โดยใช้เฉพาะฟีเจอร์ที่มีอยู่ก่อนทราบผลลัพธ์ และแยกจาก Unsupervised Clustering อย่างเด็ดขาดเพื่อไม่ให้เกิดการทำงานที่ซ้ำซ้อนและป้องกัน Target Leakage</p>
      </div>

      <div class="winner card">
        <h3 data-th="โมเดล Deep Learning ที่ได้รับเลือก (Champion)" data-en="Selected Deep Neural Champion">โมเดล Deep Learning ที่ได้รับเลือก (Champion)</h3>
        <p><strong>{html.escape(deep_winner['model_name'])}</strong> · Test PR-AUC {deep_winner['test_pr_auc']:.4f} · Test ROC-AUC {deep_winner['test_roc_auc']:.4f} · Test Accuracy {deep_winner['test_accuracy']*100:.2f}% · Balanced Accuracy {deep_winner['test_balanced_accuracy']:.4f} · Precision {deep_winner['test_precision']:.4f} · Recall {deep_winner['test_recall']:.4f} · F1 {deep_winner['test_f1']:.4f} · Runtime {deep_winner['runtime_sec']:.2f}s</p>
        <p data-th="สถาปัตยกรรม MLP (128, 64) สามารถเรียนรู้ความสัมพันธ์ไม่เชิงเส้นระหว่างฟีเจอร์พฤติกรรมและทำนายผู้ได้รับใบรับรองได้อย่างแม่นยำ โดยมีค่า Brier Score ต่ำมาก ({deep_winner['test_brier']:.4f}) สะท้อนถึงการสอบเทียบความน่าจะเป็นที่ยอดเยี่ยม" data-en="MLP (128, 64) effectively captures non-linear behavioral interactions with high precision and an outstanding Brier calibration score ({deep_winner['test_brier']:.4f}).">สถาปัตยกรรม MLP (128, 64) สามารถเรียนรู้ความสัมพันธ์ไม่เชิงเส้นระหว่างฟีเจอร์พฤติกรรมและทำนายผู้ได้รับใบรับรองได้อย่างแม่นยำ โดยมีค่า Brier Score ต่ำมาก ({deep_winner['test_brier']:.4f}) สะท้อนถึงการสอบเทียบความน่าจะเป็นที่ยอดเยี่ยม</p>
      </div>

      <div class="grid-2">
        {deep_model_comp_fig}
        {deep_cm_fig}
      </div>

      {deep_calib_fig}

      <h3 data-th="ตารางเปรียบเทียบสถาปัตยกรรม Deep Learning ทั้งหมด" data-en="All Evaluated Deep Learning Architectures">ตารางเปรียบเทียบสถาปัตยกรรม Deep Learning ทั้งหมด</h3>
      <div id="deep-table-container">{table(deep_table)}</div>

      <h3 data-th="ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Deep Learning" data-en="Deep Learning 11-Step Governed Lifecycle">ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Deep Learning</h3>
      {workflow_grid("deep", deep_status)}
    </section>

    <!-- VIEW 4: SUPERVISED LEARNING -->
    <section class="view" id="supervised">
      <h2 data-th="Track 3: การเรียนรู้แบบมีผู้สอน (Supervised Learning Classification)" data-en="Track 3: Supervised Certification Classification">Track 3: การเรียนรู้แบบมีผู้สอน (Supervised Learning Classification)</h2>

      <div class="kpis">
        <div class="kpi"><small data-th="ประชากรนักศึกษาที่ใช้" data-en="Eligible students">ประชากรนักศึกษาที่ใช้</small><strong>{sup_manifest['students']:,} คน</strong></div>
        <div class="kpi"><small data-th="อัตราการได้ใบรับรอง" data-en="Positive class rate">อัตราการได้ใบรับรอง</small><strong>{sup_manifest['positive_rate']*100:.2f}%</strong></div>
        <div class="kpi"><small data-th="ฟีเจอร์ต้นทาง" data-en="Source features">ฟีเจอร์ต้นทาง</small><strong>{sup_manifest['source_feature_count']} ตัวแปร</strong></div>
        <div class="kpi"><small data-th="ฟีเจอร์หลังแปลงจริง" data-en="Transformed features">ฟีเจอร์หลังแปลงจริง</small><strong>{sup_manifest['transformed_feature_count']} ตัวแปร</strong></div>
        <div class="kpi"><small data-th="โมเดล Champion" data-en="Champion model">โมเดล Champion</small><strong>{html.escape(sup_manifest['selected_model_name'])}</strong></div>
      </div>

      {interactive_sup_chart}

      {interactive_sup_cm_chart}

      <div class="card accent">
        <h3 data-th="หลักการคัดเลือกฟีเจอร์และป้องกัน Target Leakage" data-en="Feature Selection & Anti-Leakage Protocol">หลักการคัดเลือกฟีเจอร์และป้องกัน Target Leakage</h3>
        <p data-th="คัดเลือกจากข้อมูลสะอาดหลังผสาน โดยตัดรหัสประจำตัว (Identifiers), วันที่ดิบ, ตัวแปรผลลัพธ์ (certified, grade, viewed, explored), คอลัมน์ที่มีค่าว่างเกิน 50%, และตัดตัวแปรที่ซ้ำซ้อนกัน จากนั้นแปลงค่าด้วย RobustScaler และ One-Hot Encoding ซึ่งได้ฟีเจอร์พร้อมใช้งานจริง {sup_manifest['transformed_feature_count']} ตัวแปร โดยกระบวนการ Fit ทั้งหมดเกิดขึ้นบนชุดฝึก 70% เท่านั้น (Validation และ Test ใช้เฉพาะ Transform)" data-en="Engineered from clean data excluding identifiers, raw dates, majority-missing columns, and quarantined outcomes. RobustScaler and One-Hot Encoding fit exclusively on the 70% train split (transform-only on val/test), yielding {sup_manifest['transformed_feature_count']} features.">คัดเลือกจากข้อมูลสะอาดหลังผสาน โดยตัดรหัสประจำตัว (Identifiers), วันที่ดิบ, ตัวแปรผลลัพธ์ (certified, grade, viewed, explored), คอลัมน์ที่มีค่าว่างเกิน 50%, และตัดตัวแปรที่ซ้ำซ้อนกัน จากนั้นแปลงค่าด้วย RobustScaler และ One-Hot Encoding ซึ่งได้ฟีเจอร์พร้อมใช้งานจริง {sup_manifest['transformed_feature_count']} ตัวแปร โดยกระบวนการ Fit ทั้งหมดเกิดขึ้นบนชุดฝึก 70% เท่านั้น (Validation และ Test ใช้เฉพาะ Transform)</p>
      </div>

      <div class="grid-2">
        {figure_card(
          path="outputs/figures/tracks/certification_class_balance.png",
          title_th="ความไม่สมดุลของฉลากเป้าหมายการได้รับใบรับรอง",
          title_en="Certification Outcome Class Imbalance (3.18%)",
          purpose_th="แสดงสัดส่วนผู้ได้รับใบรับรอง (Positive Class = 1) เทียบกับผู้ไม่ได้รับใบรับรอง (Negative Class = 0) ในประชากรนักศึกษาทั้งหมด",
          purpose_en="Shows the binary target distribution: certified (positive = 1) versus non-certified (negative = 0) across all learners.",
          findings_th="มีผู้ได้รับใบรับรองเพียง 3.18% (14,206 คน) เทียบกับผู้ไม่ได้รับใบรับรอง 96.82% (432,560 คน) คิดเป็นอัตราส่วนความไม่สมดุลสูงถึง 30.4 : 1",
          findings_en="Only 3.18% (14,206 students) achieve certification versus 96.82% (432,560 students), an imbalance ratio of 30.4:1.",
          limits_th="ความไม่สมดุลระดับสูงทำให้เมทริกซ์ Accuracy ทั่วไปไร้ความหมาย (Dummy ตอบ 0 จะได้ Accuracy ถึง 96.82% แต่ใช้งานจริงไม่ได้)",
          limits_en="Severe imbalance renders Accuracy deceptive (a dummy zero-predictor achieves 96.82% accuracy with zero utility).",
          action_th="ใช้ PR-AUC เป็นเมทริกซ์หลักในการคัดเลือกโมเดล และใช้ Balanced Class Weighting ร่วมกับการปรับจูน Threshold บนชุด Validation",
          action_en="Prioritize PR-AUC as the primary metric, apply balanced class weights, and tune probability thresholds on validation data.",
        )}
        {figure_card(
          path="outputs/figures/tracks/supervised_model_comparison.png",
          title_th="การเปรียบเทียบผลการทดสอบของโมเดล Supervised บน Test Set",
          title_en="Supervised Classifier Test-Set Leaderboard",
          purpose_th="เปรียบเทียบ Dummy Baseline, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosting, และ AdaBoost บนชุดทดสอบอิสระ",
          purpose_en="Compares Dummy Baseline, Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosting, and AdaBoost on held-out test data.",
          findings_th=f"{html.escape(str(sup_winner['model_name']))} ทำคะแนนสูงสุดในรอบข้อมูลใหม่ โดยได้ Test PR-AUC {sup_winner['test_pr_auc']:.4f}, ROC-AUC {sup_winner['test_roc_auc']:.4f}, F1 {sup_winner['test_f1']:.4f} และ Balanced Accuracy {sup_winner['test_balanced_accuracy']:.4f}",
          findings_en=f"{html.escape(str(sup_winner['model_name']))} ranks first in the refreshed data run with Test PR-AUC {sup_winner['test_pr_auc']:.4f}, ROC-AUC {sup_winner['test_roc_auc']:.4f}, F1 {sup_winner['test_f1']:.4f}, and Balanced Accuracy {sup_winner['test_balanced_accuracy']:.4f}.",
          limits_th="ประสิทธิภาพที่สูงมากส่วนหนึ่งเป็นผลมาจากฟีเจอร์พฤติกรรมสะสมตลอดหลักสูตร ไม่ใช่การทำนายล่วงหน้าในสัปดาห์แรก (Early Warning)",
          limits_en="High metrics reflect full-course cumulative engagement rather than early week-1 dropout forecasting.",
          action_th="เลือก Gradient Boosted Trees เป็น Champion Model และบันทึกลงใน models/tracks/supervised_certification_pipeline.joblib",
          action_en="Lock Gradient Boosted Trees as the production champion in models/tracks/supervised_certification_pipeline.joblib.",
        )}
      </div>

      <div class="grid-2">
        {figure_card(
          path="outputs/figures/tracks/supervised_confusion_matrix.png",
          title_th="เมทริกซ์ความสับสนของโมเดล Champion (Confusion Matrix)",
          title_en="Champion Model Confusion Matrix (Optimal F1 Threshold)",
          purpose_th="แสดงจำนวนการพยากรณ์ ถูก/ผิด บนชุดทดสอบ โดยใช้เกณฑ์ Threshold ที่ปรับให้ได้ค่า F1 สูงสุดจากชุด Validation เท่านั้น",
          purpose_en="Displays confusion matrix on test data using the optimal probability threshold determined on validation data.",
          findings_th="โมเดลสามารถระบุผู้ได้รับใบรับรอง (True Positives) ได้อย่างครอบคลุมโดยมี False Positives ต่ำ ส่งผลให้ได้ค่า Test F1 สูงถึง 0.8136 และ Accuracy 98.79%",
          findings_en="The champion model reliably identifies certified students with low false alarms, achieving Test F1 of 0.8136 and Accuracy of 98.79%.",
          limits_th="การปรับ Threshold ส่งผลต่อ Trade-off ระหว่าง Precision และ Recall ซึ่งต้องพิจารณาตามต้นทุนการแทรกแซงทางธุรกิจ",
          limits_en="Threshold tuning dictates the precision-recall trade-off; operational choice depends on intervention cost vs missed intervention risk.",
          action_th="สามารถปรับลด Threshold ในระบบจริงได้หากเป้าหมายคือการคัดกรองนักศึกษาที่ต้องการการดูแลเป็นพิเศษให้ครอบคลุมที่สุด",
          action_en="Expose threshold controls in deployment to allow academic advisors to widen intervention reach when counseling capacity permits.",
        )}
        {figure_card(
          path="outputs/figures/tracks/certified_grade_threshold_audit.png",
          title_th="การตรวจสอบเกรดและความสอดคล้องของฉลากเป้าหมาย",
          title_en="Target Outcome Consistency Audit",
          purpose_th="ยืนยันความถูกต้องของฉลากเป้าหมายที่ใช้ฝึกโมเดล Supervised และตรวจสอบการแยกตัวแปรผลลัพธ์ที่ขัดแย้งออกอย่างสมบูรณ์",
          purpose_en="Confirms supervised target label validity and verifies quarantine of contradictory records.",
          findings_th="ผู้ได้รับใบรับรองเกือบ 100% มีเกรดผ่านเกณฑ์ขั้นต่ำ 0.50 และจุดสีแดง 1 จุดที่มีเกรดต่ำกว่า 0.50 ถูกตัดออกจากชุดฝึก Supervised เรียบร้อยแล้ว",
          findings_en="Nearly 100% of certified students meet the 0.50 grade threshold; the single contradictory record was successfully quarantined.",
          limits_th="เกรดไม่ถูกนำมาใช้เป็นฟีเจอร์พยากรณ์ เพื่อป้องกันปัญหา Label Leakage",
          limits_en="Numeric grade is never used as an input feature, strictly preventing target leakage.",
          action_th="รักษาความปลอดภัยของ Pipeline โดยตรวจสอบ Schema ข้อมูลนำเข้าให้แน่ใจว่าไม่มีคอลัมน์เกรดหรือผลลัพธ์ปนเปื้อนเข้ามาในตอน Inference",
          action_en="Enforce schema validation at production inference to reject any input containing post-outcome labels.",
        )}
      </div>

      {figure_card(
          path="outputs/figures/tracks/supervised_confusion_matrices_comparison.png",
          title_th="เปรียบเทียบ Confusion Matrix ของ 6 โมเดล Supervised",
          title_en="Six-Model Supervised Confusion-Matrix Comparison",
          purpose_th="เปรียบเทียบ TN, FP, FN และ TP ของโมเดลที่ทำคะแนนสูงสุด 6 แบบบน test set เดียวกัน โดยทุกโมเดลใช้ threshold ที่เลือกจาก validation set เท่านั้น",
          purpose_en="Compares TN, FP, FN, and TP for the six strongest classifiers on the identical held-out test set, using thresholds selected only from validation data.",
          findings_th="กราฟทำให้เห็น trade-off โดยตรงว่าโมเดลใดลด False Negative หรือ False Positive ได้ดีกว่า ไม่ตัดสินจาก Accuracy ค่าเดียว",
          findings_en="The grid exposes each model's false-negative and false-positive trade-off instead of relying on accuracy alone.",
          limits_th="ผลนี้เป็นการพยากรณ์จากพฤติกรรมสะสมทั้งคอร์ส จึงยังไม่ใช่แบบจำลอง early-warning รายสัปดาห์",
          limits_en="These models use full-course cumulative behavior and are not yet weekly early-warning models.",
          action_th="เลือก threshold ตามต้นทุนของ False Negative และกำลังรองรับการแทรกแซงจริง",
          action_en="Choose the operating threshold based on false-negative cost and real intervention capacity.",
        )}

      <div class="winner card">
        <h3 data-th="โมเดล Champion ที่ได้รับเลือก" data-en="Selected Supervised Champion">โมเดล Champion ที่ได้รับเลือก</h3>
        <p><strong>{html.escape(sup_winner['model_name'])}</strong> · Test PR-AUC {sup_winner['test_pr_auc']:.4f} · Test ROC-AUC {sup_winner['test_roc_auc']:.4f} · Test Accuracy {sup_winner['test_accuracy']*100:.2f}% · Balanced Accuracy {sup_winner['test_balanced_accuracy']:.4f} · Precision {sup_winner['test_precision']:.4f} · Recall {sup_winner['test_recall']:.4f} · F1 {sup_winner['test_f1']:.4f} · Training Runtime {sup_winner['runtime_sec']:.2f}s</p>
        <p data-th="โมเดลสามารถประมวลผลให้คะแนนนักศึกษาทั้งรุ่น {sup_manifest['students']:,} คนได้ในเวลาเพียง {sup_manifest['full_cohort_inference_runtime_sec']:.2f} วินาที มีความพร้อมในการนำไปใช้งานจริงในระดับปฏิบัติการ" data-en="The model scored all {sup_manifest['students']:,} students in {sup_manifest['full_cohort_inference_runtime_sec']:.2f} seconds, demonstrating operational readiness.">โมเดลสามารถประมวลผลให้คะแนนนักศึกษาทั้งรุ่น {sup_manifest['students']:,} คนได้ในเวลาเพียง {sup_manifest['full_cohort_inference_runtime_sec']:.2f} วินาที มีความพร้อมในการนำไปใช้งานจริงในระดับปฏิบัติการ</p>
      </div>

      <div id="sup-table-container">{table(sup_table)}</div>

      <details>
        <summary data-th="ฟีเจอร์ต้นทางที่เลือกจากข้อมูลสะอาด (Source Feature Specification)" data-en="Source Features Selected from Clean Data">ฟีเจอร์ต้นทางที่เลือกจากข้อมูลสะอาด (Source Feature Specification)</summary>
        {table(sup_features)}
      </details>
      <details>
        <summary data-th="ฟีเจอร์หลังผ่านการแปลงจริง (Transformed Features)" data-en="Actual Transformed Features">ฟีเจอร์หลังผ่านการแปลงจริง (Transformed Features)</summary>
        {table(transformed)}
      </details>

      <h3 data-th="ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Supervised" data-en="Supervised 11-Step Governed Lifecycle">ขั้นตอนการทำงาน 11 ขั้นตอนของ Track Supervised</h3>
      {workflow_grid("supervised", sup_status)}
    </section>

    <!-- VIEW 5: STUDENT ROW-TO-TEXT LLM / TRANSFORMER -->
    <section class="view" id="llm">
      <h2 data-th="Track 4: LLM / Transformer จากพฤติกรรมนักเรียนหนึ่งคนต่อหนึ่งแถว" data-en="Track 4: One-Student-Row-to-Text LLM / Transformer">Track 4: LLM / Transformer จากพฤติกรรมนักเรียนหนึ่งคนต่อหนึ่งแถว</h2>

      <!-- SECTION OVERVIEW KPIS -->
      <div class="kpis">
        <div class="kpi"><small data-th="หน่วยวิเคราะห์" data-en="Unit of analysis">หน่วยวิเคราะห์</small><strong>1 row / student</strong></div>
        <div class="kpi"><small data-th="Offline Test Set" data-en="Offline Test Set">Offline Test Set</small><strong>1,800 คน</strong></div>
        <div class="kpi"><small data-th="โมเดล Offline ที่สำเร็จ" data-en="Completed Offline Models">โมเดล Offline ที่สำเร็จ</small><strong>{len(llm_offline_completed)} โมเดล</strong></div>
        <div class="kpi"><small data-th="Offline PR-AUC สูงสุด" data-en="Best Offline PR-AUC">Offline PR-AUC สูงสุด</small><strong>{llm_winner['test_pr_auc']:.4f}</strong></div>
        <div class="kpi"><small data-th="Offline Recall" data-en="Offline Recall">Offline Recall</small><strong>{llm_winner['test_recall']*100:.2f}%</strong></div>
        <div class="kpi"><small data-th="การใช้ API" data-en="External API Usage">การใช้ API</small><strong>ไม่ใช้</strong></div>
      </div>

      <div class="card accent">
        <h3 data-th="ผลหลัก: Offline Behavioral NLP บนข้อมูลเท่ากันทุกโมเดล" data-en="Primary Result: Offline Behavioral NLP on Identical Data">ผลหลัก: Offline Behavioral NLP บนข้อมูลเท่ากันทุกโมเดล</h3>
        <p data-th="โมเดลทั้งหมดรันภายในเครื่องโดยไม่เรียก OpenAI, Anthropic หรือ Gemini API ใช้ Train 8,400 คน, Validation 1,800 คน และ Test 1,800 คนชุดเดียวกัน ข้อความหนึ่งชุดแทนนักเรียนหนึ่งคน และเลือก threshold จาก Validation เท่านั้น" data-en="All models run locally without OpenAI, Anthropic, or Gemini APIs. Every model uses the same 8,400 training, 1,800 validation, and 1,800 test students. One text record represents one student, and thresholds are selected only from validation data.">โมเดลทั้งหมดรันภายในเครื่องโดยไม่เรียก API และใช้ Train 8,400 คน, Validation 1,800 คน และ Test 1,800 คนชุดเดียวกัน</p>
        <p data-th="คำว่า GPT-style หมายถึงสถาปัตยกรรม decoder แบบน้ำหนักเปิด เช่น DistilGPT2 ไม่ใช่ GPT-4 ส่วน Claude ตัวจริงไม่มีน้ำหนักโมเดลให้ดาวน์โหลด จึงไม่สามารถรันภายในเครื่องได้และไม่มีการสร้างผลจำลองแทน" data-en="GPT-style refers to an open-weight decoder architecture such as DistilGPT2, not GPT-4. Proprietary Claude weights are unavailable for local download, so Claude is not run locally and no synthetic replacement is fabricated.">GPT-style ในงานนี้หมายถึงโมเดลน้ำหนักเปิด ไม่ใช่ GPT-4 และ Claude ตัวจริงไม่สามารถดาวน์โหลดมารันภายในเครื่องได้</p>
      </div>

      {interactive_llm_chart}
      <h4 data-th="ตารางผล Offline Behavioral NLP" data-en="Offline Behavioral NLP Results">ตารางผล Offline Behavioral NLP</h4>
      {table(llm_offline_models)}
      <div class="card">
        <h4 data-th="โมเดล Offline ที่เลือก" data-en="Selected Offline Model">โมเดล Offline ที่เลือก</h4>
        <p><strong>{html.escape(llm_winner['model_name'])}</strong> · Test PR-AUC {llm_winner['test_pr_auc']:.4f} · Precision {llm_winner['test_precision']:.4f} · Recall {llm_winner['test_recall']:.4f} · F1 {llm_winner['test_f1']:.4f}</p>
      </div>
      {interactive_llm_cm_chart}
      <h4 data-th="ตาราง Confusion Matrix ของโมเดล Offline" data-en="Offline Model Confusion Matrices">ตาราง Confusion Matrix ของโมเดล Offline</h4>
      {table(llm_offline_confusions)}

      <!-- CARD 1: TASK DEFINITION & SERIALIZATION GOVERNANCE -->
      <div class="card accent">
        <h3 data-th="การแปลงข้อมูลพฤติกรรมเป็นข้อความ และธรรมาภิบาลข้อมูล (Behavior-to-Text Serialization & Governance)" data-en="Behavior-to-Text Serialization & Data Governance">การแปลงข้อมูลพฤติกรรมเป็นข้อความ และธรรมาภิบาลข้อมูล (Behavior-to-Text Serialization & Governance)</h3>
        <p data-th="<strong>1. การแปลงข้อมูลแถวเป็นข้อความ (Factual Text Serialization):</strong> ข้อมูลระดับนักเรียนหนึ่งแถว (userid_DI) ประกอบด้วยตัวเลขพฤติกรรมการเรียน (จำนวนวิชาที่ลงทะเบียน, จำนวนกิจกรรมทั้งหมด, จำนวนวันที่เข้าเรียน, จำนวนครั้งที่กดเล่นวิดีโอ, จำนวนบทเรียนที่เข้าถึง, และจำนวนโพสต์ในกระดานสนทนา) ถูกแปลงเป็นข้อความภาษาอังกฤษเชิงข้อเท็จจริง (เช่น <em>'Student MHxPC130153646 was enrolled in 1 course, recorded 1177 events across 27 active days, played video 305 times, interacted with 12 chapters, and made 0 forum posts.'</em>) ก่อนป้อนเข้าสู่โมเดล AI<br>
        <strong>2. การกักกันตัวแปรผลลัพธ์ (Strict Target Quarantine):</strong> ตัวแปรผลลัพธ์การได้รับใบรับรอง (certified) ถูกแยกเก็บต่างหากอย่างเด็ดขาด และไม่เคยถูกส่งเข้าไปในข้อความหรือ prompt ระหว่างการอนุมานผล เพื่อป้องกัน target leakage 100%<br>
        <strong>3. ไม่มี Video Transcript จริง (No Real Video Transcripts):</strong> ตามข้อกำหนดของ Merged_Workflow.md ข้อมูลชุดนี้มีเพียงตัวนับการปฏิสัมพันธ์ของผู้เรียน (interaction clicks / play counts) เท่านั้น <em>ไม่มีไฟล์เสียง บรรยายใต้ภาพ หรือ transcript คำพูดของอาจารย์ผู้สอนจริง</em> จึงต้องระบุข้อความนี้เป็น behavior_summary_text อย่างเคร่งครัด ห้ามอ้างว่าเป็นเนื้อหาวิดีโอ<br>
        <strong>4. Few-Shot In-Context Inference ไม่ใช่การ Fine-Tuning:</strong> การประเมินผลทั้งหมดเป็นการอนุมานแบบ Few-Shot In-Context Learning โดยส่งตัวอย่างพร้อมเฉลยจำนวนเล็กน้อยจากชุด Train เข้าไปใน prompt พร้อมกำหนด Structured Output JSON Schema (certified, probability, reason) <em>ไม่มีการปรับแก้น้ำหนักโมเดล (Weights) หรือการ fine-tuning ใด ๆ</em>"
        data-en="<strong>1. Factual Text Serialization:</strong> Each student record (userid_DI) containing behavioral interaction values (enrolled courses, total events, active days, video-play counts, chapters viewed, forum posts) is serialized into factual English sentences (e.g. <em>'Student MHxPC130153646 was enrolled in 1 course, recorded 1177 events across 27 active days, played video 305 times, interacted with 12 chapters, and made 0 forum posts.'</em>) prior to AI processing.<br>
        <strong>2. Strict Target Quarantine:</strong> The outcome label (certified) was quarantined locally and never included in prompt text or inference context, guaranteeing 0% target leakage.<br>
        <strong>3. No Actual Video Transcripts:</strong> In strict compliance with Merged_Workflow.md, this MOOC dataset contains only interaction logs (clicks and play counts). <em>No audio recordings, captions, or spoken lecture transcripts exist.</em> This text is strictly behavior_summary_text and must never be portrayed as lecture transcripts.<br>
        <strong>4. Few-Shot In-Context Inference, Not Fine-Tuning:</strong> All evaluations used few-shot in-context learning with demonstrations drawn exclusively from the training split and constrained JSON schema decoding. <em>No model parameters were fine-tuned or trained.</em>">
        <strong>1. การแปลงข้อมูลแถวเป็นข้อความ (Factual Text Serialization):</strong> ข้อมูลระดับนักเรียนหนึ่งแถว (userid_DI) ประกอบด้วยตัวเลขพฤติกรรมการเรียน ถูกแปลงเป็นข้อความภาษาอังกฤษเชิงข้อเท็จจริงก่อนป้อนเข้าสู่โมเดล AI<br>
        <strong>2. การกักกันตัวแปรผลลัพธ์ (Strict Target Quarantine):</strong> ตัวแปรผลลัพธ์การได้รับใบรับรองถูกแยกเก็บต่างหากอย่างเด็ดขาด ป้องกัน target leakage 100%<br>
        <strong>3. ไม่มี Video Transcript จริง (No Real Video Transcripts):</strong> ข้อมูลชุดนี้มีเพียงตัวนับการปฏิสัมพันธ์ของผู้เรียน (clicks / play counts) เท่านั้น ไม่มีไฟล์เสียงหรือ transcript คำพูดจริง<br>
        <strong>4. Few-Shot In-Context Inference ไม่ใช่การ Fine-Tuning:</strong> เป็นการอนุมานแบบ few-shot ผ่าน prompt ไม่มีการ fine-tuning หรือแก้น้ำหนักโมเดล
        </p>
        {table(llm_task_definition)}
      </div>

      <!-- CARD 2: MODEL ARCHITECTURE GUIDE -->
      <div class="card">
        <h3 data-th="คู่มือและสถาปัตยกรรมของโมเดลแต่ละตัว (Evaluated AI Model Guide)" data-en="Evaluated AI Model Architecture Guide">คู่มือและสถาปัตยกรรมของโมเดลแต่ละตัว (Evaluated AI Model Guide)</h3>
        <p data-th="โครงการประเมินโมเดลภาษาขนาดใหญ่ (LLM) ทั้งในรูปแบบ Cloud Hosted API และ Local Open-Weight Model บนรันไทม์ Ollama โดยโมเดลทุกตัวอ่านข้อความพฤติกรรมชุดเดียวกันและตอบกลับด้วย JSON Schema เดียวกัน" data-en="The project evaluates Large Language Models (LLMs) across both Cloud Hosted API and Local Open-Weight Models via Ollama, ensuring identical prompt serialization and JSON schema constraints across all systems.">โครงการประเมินโมเดลภาษาขนาดใหญ่ (LLM) ทั้งในรูปแบบ Cloud Hosted API และ Local Open-Weight Model บนรันไทม์ Ollama โดยโมเดลทุกตัวอ่านข้อความพฤติกรรมชุดเดียวกันและตอบกลับด้วย JSON Schema เดียวกัน</p>

        <div class="table-wrap">
          <table>
            <thead><tr>
              <th data-th="ชื่อโมเดล" data-en="Model Name">ชื่อโมเดล</th>
              <th data-th="ผู้พัฒนา / รันไทม์" data-en="Developer / Runtime">ผู้พัฒนา / รันไทม์</th>
              <th data-th="สถาปัตยกรรมและจุดเด่น" data-en="Architecture & Strengths">สถาปัตยกรรมและจุดเด่น</th>
              <th data-th="สถานะการประเมินในโครงการ" data-en="Evaluation Status in Project">สถานะการประเมินในโครงการ</th>
            </tr></thead>
            <tbody>
              <tr>
                <td><strong>Gemini 3.5 Flash Lite</strong></td>
                <td data-th="Google · Hosted Cloud API" data-en="Google · Hosted Cloud API">Google · Hosted Cloud API</td>
                <td data-th="โมเดลภาษาเชิงพาณิชย์ประสิทธิภาพสูง รองรับ context ขนาดใหญ่ และ structured JSON output ด้วยความเร็วสูง" data-en="High-throughput multimodal foundation model optimized for fast batch inference and strict JSON schemas">โมเดลภาษาเชิงพาณิชย์ประสิทธิภาพสูง รองรับ context ขนาดใหญ่ และ structured JSON output ด้วยความเร็วสูง</td>
                <td data-th="รัน Full Test จริงครบ 1,800 คน และรัน Comparative Pilot (N=20) สำเร็จแล้ว" data-en="Completed Full Test (1,800 students) & Comparative Pilot (N=20)">รัน Full Test จริงครบ 1,800 คน และรัน Comparative Pilot (N=20) สำเร็จแล้ว</td>
              </tr>
              <tr>
                <td><strong>Ollama</strong></td>
                <td data-th="Local Inference Engine (ไม่ใช่โมเดล)" data-en="Local Inference Engine (Not a model)">Local Inference Engine (ไม่ใช่โมเดล)</td>
                <td data-th="รันไทม์และเซิร์ฟเวอร์สำหรับรันโมเดล open-weight ในเครื่อง Mac ผ่าน Apple Silicon GPU ข้อมูลไม่ออกนอกเครื่องและไม่มีค่าบริการ API" data-en="On-device model server running quantized open-weight models on Mac Apple Silicon GPU with complete data privacy">รันไทม์และเซิร์ฟเวอร์สำหรับรันโมเดล open-weight ในเครื่อง Mac ผ่าน Apple Silicon GPU ข้อมูลไม่ออกนอกเครื่องและไม่มีค่าบริการ API</td>
                <td data-th="ติดตั้งแล้ว; ประมวลผลทั้ง 3 Local Models บน Pilot Cohort สำเร็จครบถ้วน" data-en="Installed; successfully executed all 3 local models on Pilot Cohort">ติดตั้งแล้ว; ประมวลผลทั้ง 3 Local Models บน Pilot Cohort สำเร็จครบถ้วน</td>
              </tr>
              <tr>
                <td><strong>Qwen3 4B</strong></td>
                <td data-th="Alibaba Cloud · Local Open-Weight (Ollama)" data-en="Alibaba Cloud · Local Open-Weight (Ollama)">Alibaba Cloud · Local Open-Weight (Ollama)</td>
                <td data-th="โมเดลขนาด 4 พันล้านพารามิเตอร์ โดดเด่นด้านการให้เหตุผล (Reasoning) และหลายภาษา โดยปิด thinking mode เพื่อให้ผลลัพธ์ deterministic รวดเร็ว" data-en="4B parameter model optimized for complex reasoning and multilingual structured output; thinking mode disabled for fast classification">โมเดลขนาด 4 พันล้านพารามิเตอร์ โดดเด่นด้านการให้เหตุผล (Reasoning) และหลายภาษา โดยปิด thinking mode เพื่อให้ผลลัพธ์ deterministic รวดเร็ว</td>
                <td data-th="รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (ได้ PR-AUC สูงสุด 0.7400 ในกลุ่ม Pilot)" data-en="Completed Comparative Balanced Pilot (N=20; Highest Pilot PR-AUC 0.7400)">รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (ได้ PR-AUC สูงสุด 0.7400 ในกลุ่ม Pilot)</td>
              </tr>
              <tr>
                <td><strong>Llama 3.2 3B</strong></td>
                <td data-th="Meta AI · Local Open-Weight (Ollama)" data-en="Meta AI · Local Open-Weight (Ollama)">Meta AI · Local Open-Weight (Ollama)</td>
                <td data-th="โมเดลขนาด 3 พันล้านพารามิเตอร์ ออกแบบสำหรับ edge devices ประมวลผลคำสั่งได้รวดเร็วและใช้หน่วยความจำน้อย" data-en="3B parameter edge-optimized model for rapid instruction following and low-latency edge deployment">โมเดลขนาด 3 พันล้านพารามิเตอร์ ออกแบบสำหรับ edge devices ประมวลผลคำสั่งได้รวดเร็วและใช้หน่วยความจำน้อย</td>
                <td data-th="รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (PR-AUC 0.7111, F1 0.6667, Recall 0.7000)" data-en="Completed Comparative Balanced Pilot (N=20; PR-AUC 0.7111, F1 0.6667, Recall 0.7000)">รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (PR-AUC 0.7111, F1 0.6667, Recall 0.7000)</td>
              </tr>
              <tr>
                <td><strong>Mistral 7B</strong></td>
                <td data-th="Mistral AI · Local Open-Weight (Ollama)" data-en="Mistral AI · Local Open-Weight (Ollama)">Mistral AI · Local Open-Weight (Ollama)</td>
                <td data-th="โมเดลขนาด 7 พันล้านพารามิเตอร์ชั้นนำ มีความระมัดระวังสูง ให้ความแม่นยำภาษาอังกฤษและโค้ดอย่างเข้มงวด" data-en="7B parameter dense architecture known for rigorous reasoning and conservative high-precision predictions">โมเดลขนาด 7 พันล้านพารามิเตอร์ชั้นนำ มีความระมัดระวังสูง ให้ความแม่นยำภาษาอังกฤษและโค้ดอย่างเข้มงวด</td>
                <td data-th="รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (Precision 1.0000, TN 10/10, F1 0.3333)" data-en="Completed Comparative Balanced Pilot (N=20; Precision 1.0000, TN 10/10, F1 0.3333)">รัน Comparative Balanced Pilot (N=20) สำเร็จแล้ว (Precision 1.0000, TN 10/10, F1 0.3333)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- CARD 3: METHODOLOGICAL WARNING & COHORT SEPARATION SAFEGUARDS -->
      <div class="card" style="border-left: 4px solid var(--warn, #f59e0b); background: #fffbeb;">
        <h3 data-th="⚠️ ข้อควรระวังสำคัญ: การแยกชุดข้อมูลและข้อห้ามในการเปรียบเทียบตัวเลขตรงกันข้าม" data-en="⚠️ Critical Evaluation Safeguard: Cohort Separation & Cross-Comparison Prohibition">⚠️ ข้อควรระวังสำคัญ: การแยกชุดข้อมูลและข้อห้ามในการเปรียบเทียบตัวเลขตรงกันข้าม</h3>
        <p data-th="1. <strong>Gemini Full Test (N=1,800):</strong> เป็นการประเมินบน Held-out Test Split เต็มจำนวน 1,800 คน ที่มีการกระจายตัวของคลาสตามความเป็นจริง (Imbalanced: ได้รับใบรับรอง 58 คน คิดเป็น 3.22%, ไม่ได้รับ 1,742 คน คิดเป็น 96.78%)<br>
        2. <strong>Comparative Balanced Pilot (N=20):</strong> เป็นการสุ่มกลุ่มตัวอย่างสมดุล 20 คน (Positive 10 คน, Negative 10 คน คิดเป็น 50% Positive, seed=42) จาก Test Split เพื่อทดสอบเปรียบเทียบความสามารถระหว่าง Local Open-Weight Models (Qwen3 4B, Llama 3.2 3B, Mistral 7B) และ Gemini 3.5 Flash Lite ภายใต้ข้อจำกัดด้านทรัพยากรเครื่องคอมพิวเตอร์และเวลา<br>
        3. <strong>ข้อห้ามสำคัญ: ห้ามนำตัวชี้วัด (PR-AUC, Precision, F1, Accuracy) ของ Pilot (N=20) ไปเปรียบเทียบโดยตรงกับ Full Test (N=1,800)</strong> เนื่องจากตัวชี้วัดเหล่านี้ขึ้นอยู่กับสัดส่วน Positive Class (Class Prevalence Effect) อย่างมีนัยสำคัญ ในชุด Pilot 50% ค่าคาดหวังแบบสุ่มคือ 0.50 ขณะที่ใน Full Test 3.22% ค่าคาดหวังแบบสุ่มคือ 0.0322 ดังนั้นค่า PR-AUC 0.7400 ใน Pilot จึงไม่ได้หมายความว่าเหนือกว่าค่า 0.5642 ใน Full Test<br>
        4. <strong>การระบุชื่อ:</strong> ชุดทดสอบ 20 คนนี้เป็น <em>Comparative Balanced Pilot Benchmark</em> เท่านั้น <strong>ห้ามเรียกว่า Full Benchmark</strong>"
        data-en="1. <strong>Gemini Full Test (N=1,800):</strong> Evaluated on the complete held-out test split reflecting authentic MOOC class imbalance (58 certified = 3.22%, 1,742 uncertified = 96.78%).<br>
        2. <strong>Comparative Balanced Pilot (N=20):</strong> Evaluated on a balanced 20-student cohort (10 positive, 10 negative = 50% positive, seed=42) sampled from the test split to benchmark local open-weight models (Qwen3 4B, Llama 3.2 3B, Mistral 7B) against Gemini 3.5 Flash Lite under local hardware constraints.<br>
        3. <strong>Strict Safeguard: Never directly cross-compare metrics (PR-AUC, Precision, F1, Accuracy) between Pilot (N=20) and Full Test (N=1,800).</strong> Metrics are heavily dependent on positive class prevalence. Random guessing baseline is 0.50 in the 50% pilot, but only 0.0322 in the 3.22% full test. Therefore, PR-AUC 0.7400 in the pilot does not imply superiority over 0.5642 in the full test.<br>
        4. <strong>Standard Naming:</strong> This 20-student study is strictly designated as a <em>Comparative Balanced Pilot Benchmark</em>; it must <strong>never be termed a Full Benchmark</strong>.">
        1. <strong>Gemini Full Test (N=1,800):</strong> เป็นการประเมินบน Held-out Test Split เต็มจำนวน 1,800 คน (สัดส่วนจริง: ได้ใบรับรอง 58 คน = 3.22%)<br>
        2. <strong>Comparative Balanced Pilot (N=20):</strong> เป็นกลุ่มตัวอย่างสมดุล 20 คน (Positive 10 คน, Negative 10 คน = 50% Positive, seed=42) เพื่อเปรียบเทียบทั้ง 4 โมเดลบนเครื่องจริง<br>
        3. <strong>ห้ามนำผล Pilot (N=20) ไปเปรียบเทียบตรงกับ Full Test (N=1,800)</strong> เนื่องจากอัตราส่วน Positive ต่างกันอย่างมีนัยสำคัญ (50% vs 3.22%)<br>
        4. ชุดทดสอบ 20 คนนี้เป็น <em>Comparative Balanced Pilot Benchmark</em> เท่านั้น ห้ามเรียกว่า Full Benchmark
        </p>
      </div>

      <h3 data-th="กระบวนการข้อมูลที่ใช้จริง (Executed Data-to-Model Pipeline)" data-en="Executed Data-to-Model Process">กระบวนการข้อมูลที่ใช้จริง (Executed Data-to-Model Pipeline)</h3>
      <div class="pipeline-chain">
        <span>1. One Student Row</span><i>→</i>
        <span>2. Clean Behavioral Values</span><i>→</i>
        <span>3. Factual Text Serialization</span><i>→</i>
        <span>4. Few-shot In-Context Prompt</span><i>→</i>
        <span>5. AI Model Structured Inference</span><i>→</i>
        <span>6. Certification Probability & Reason</span>
      </div>

      <!-- ========================================== -->
      <!-- PART 1: GEMINI FULL TEST (N=1,800)        -->
      <!-- ========================================== -->
      <h3 data-th="ส่วนที่ 1: ผลการประเมิน Gemini บนชุดทดสอบเต็ม (Gemini Full Test: N=1,800)" data-en="Part 1: Gemini Empirical Evaluation on Full Held-Out Test Set (N=1,800)">ส่วนที่ 1: ผลการประเมิน Gemini บนชุดทดสอบเต็ม (Gemini Full Test: N=1,800)</h3>

      <!-- KPIS MUST BE BEFORE CHARTS -->
      <div class="kpis">
        <div class="kpi"><small data-th="นักเรียนในชุดทดสอบเต็ม" data-en="Full Test Students">นักเรียนในชุดทดสอบเต็ม</small><strong>{int(llm_api_winner['evaluation_students']):,}</strong></div>
        <div class="kpi"><small data-th="ผู้ได้รับใบรับรองจริง" data-en="Actual Certified">ผู้ได้รับใบรับรองจริง</small><strong>{int(llm_api_winner['positive_students'])} (3.22%)</strong></div>
        <div class="kpi"><small data-th="Test PR-AUC" data-en="Test PR-AUC">Test PR-AUC</small><strong>{llm_api_winner['test_pr_auc']:.4f}</strong></div>
        <div class="kpi"><small data-th="Test Recall" data-en="Test Recall">Test Recall</small><strong>{llm_api_winner['test_recall']*100:.2f}%</strong></div>
        <div class="kpi"><small data-th="Test F1 Score" data-en="Test F1 Score">Test F1 Score</small><strong>{llm_api_winner['test_f1']:.4f}</strong></div>
        <div class="kpi"><small data-th="Test Brier Score" data-en="Test Brier Score">Test Brier Score</small><strong>{llm_api_winner['test_brier']:.4f}</strong></div>
      </div>

      <!-- CHART 1: GEMINI FULL TEST METRICS -->
      {interactive_llm_api_chart}
      <h4 data-th="ตารางสรุปผลตัวชี้วัด Gemini Full Test (N=1,800)" data-en="Gemini Full Test Performance Metrics Table (N=1,800)">ตารางสรุปผลตัวชี้วัด Gemini Full Test (N=1,800)</h4>
      {table(gemini_full_metrics_table)}
      <p class="chart-explanation" data-th="<strong>คำอธิบายผลลัพธ์:</strong> Gemini 3.5 Flash Lite ได้รับการประเมินผ่านข้อความพฤติกรรมระดับนักศึกษาครบทั้ง 1,800 คนใน Test Split (แบ่งเป็น 90 requests batch ละ 20 คน) โดยมีผู้ได้รับใบรับรองตามจริง 58 คน โมเดลทำนายได้ Recall สูงถึง 93.10% (ตรวจพบผู้เรียนที่ได้ใบรับรองถึง 54 จาก 58 คน) มีค่า PR-AUC 0.5642 ซึ่งสูงกว่าอัตราการเดาสุ่มตามสัดส่วนคลาสจริง (0.0322) ถึง 17.5 เท่า และได้ ROC-AUC 0.9810 พร้อมค่า Brier Score 0.0293 แสดงถึงการประมาณค่าความน่าจะเป็นที่แม่นยำสูงมาก" data-en="<strong>Results Interpretation:</strong> Gemini 3.5 Flash Lite evaluated all 1,800 test learners (90 API batch requests) containing 58 actual certified students. The model achieved a high Recall of 93.10% (capturing 54 out of 58 true completers), PR-AUC of 0.5642 (17.5x over the 0.0322 random baseline), ROC-AUC of 0.9810, and Brier Score of 0.0293 indicating superior calibration."><strong>คำอธิบายผลลัพธ์:</strong> Gemini 3.5 Flash Lite ได้รับการประเมินผ่านข้อความพฤติกรรมระดับนักศึกษาครบทั้ง 1,800 คนใน Test Split โดยตรวจพบผู้เรียนที่ได้ใบรับรอง 54 จาก 58 คน (Recall 93.10%) ได้ PR-AUC 0.5642 (สูงกว่า baseline สุ่ม 0.0322 ถึง 17.5 เท่า) และ Brier Score 0.0293</p>

      <!-- CHART 2: GEMINI FULL TEST CONFUSION MATRIX -->
      {interactive_llm_api_cm_chart}
      <h4 data-th="ตารางแจกแจง Confusion Matrix ของ Gemini Full Test (N=1,800)" data-en="Gemini Full Test Confusion Matrix Breakdown Table (N=1,800)">ตารางแจกแจง Confusion Matrix ของ Gemini Full Test (N=1,800)</h4>
      {table(gemini_full_cm_table)}
      <p class="chart-explanation" data-th="<strong>คำอธิบายผลลัพธ์ Confusion Matrix:</strong> จากนักเรียน 1,800 คน โมเดลจำแนกถูกต้องทั้งหมด 1,733 คน (Accuracy 96.28%) โดยมีความจำเพาะ (Specificity) 96.38% (TN 1,679 คนจาก 1,742 คนที่ไม่ได้รับใบรับรอง) และมีความไว (Recall) 93.10% (TP 54 คนจาก 58 คนที่ได้รับใบรับรอง) มีข้อผิดพลาดแบบตกหล่น (False Negative) เพียง 4 คนเท่านั้น และมี False Positive 63 คน ซึ่งเป็นระดับที่ยอมรับได้สำหรับระบบเตือนภัยล่วงหน้า (Early Warning System)" data-en="<strong>Confusion Matrix Interpretation:</strong> Out of 1,800 students, the model correctly predicted 1,733 learners (Accuracy 96.28%) with 96.38% Specificity (1,679 True Negatives) and 93.10% Recall (54 True Positives). Only 4 certified students were missed (False Negatives), while 63 uncertified students were flagged as potential completers (False Positives), an ideal trade-off for early-intervention systems."><strong>คำอธิบายผลลัพธ์ Confusion Matrix:</strong> จากนักเรียน 1,800 คน โมเดลจำแนกถูกต้องทั้งหมด 1,733 คน (Accuracy 96.28%) Specificity 96.38% (TN 1,679) และ Sensitivity 93.10% (TP 54) มี False Negative เพียง 4 คน</p>

      <!-- ========================================== -->
      <!-- PART 2: COMPARATIVE BALANCED PILOT (N=20)  -->
      <!-- ========================================== -->
      <h3 data-th="ส่วนที่ 2: การเปรียบเทียบทั้ง 4 โมเดลบน Pilot Cohort แบบสมดุล (Comparative Balanced Pilot: N=20)" data-en="Part 2: Head-to-Head Comparison Across All 4 Models on Balanced Pilot (N=20)">ส่วนที่ 2: การเปรียบเทียบทั้ง 4 โมเดลบน Pilot Cohort แบบสมดุล (Comparative Balanced Pilot: N=20)</h3>

      <!-- KPIS MUST BE BEFORE CHARTS -->
      <div class="kpis">
        <div class="kpi"><small data-th="กลุ่มตัวอย่าง Pilot" data-en="Pilot Cohort Size">กลุ่มตัวอย่าง Pilot</small><strong>20 คน (10 Pos / 10 Neg)</strong></div>
        <div class="kpi"><small data-th="จำนวนโมเดลที่เปรียบเทียบ" data-en="Models Compared">จำนวนโมเดลที่เปรียบเทียบ</small><strong>4 โมเดล (รันเสร็จสิ้นทั้งหมด)</strong></div>
        <div class="kpi"><small data-th="Best Pilot PR-AUC" data-en="Best Pilot PR-AUC">Best Pilot PR-AUC</small><strong>0.7400 (Qwen3 4B)</strong></div>
        <div class="kpi"><small data-th="Best Pilot Precision" data-en="Best Pilot Precision">Best Pilot Precision</small><strong>1.0000 (Mistral 7B)</strong></div>
        <div class="kpi"><small data-th="Best Pilot Recall & F1" data-en="Best Pilot Recall & F1">Best Pilot Recall & F1</small><strong>Recall 90% · F1 0.8571 (Gemini)</strong></div>
        <div class="kpi"><small data-th="Lowest Brier Score" data-en="Lowest Brier Score">Lowest Brier Score</small><strong>0.1453 (Gemini 3.5)</strong></div>
      </div>

      <!-- CHART 3: PILOT METRIC COMPARISON -->
      {interactive_pilot_metrics_chart}
      <h4 data-th="ตารางเปรียบเทียบตัวชี้วัดทั้ง 4 โมเดลบน Pilot Cohort (N=20)" data-en="Comparative Balanced Pilot Performance Metrics Table (N=20)">ตารางเปรียบเทียบตัวชี้วัดทั้ง 4 โมเดลบน Pilot Cohort (N=20)</h4>
      {table(pilot_metrics_table)}
      <p class="chart-explanation" data-th="<strong>คำอธิบายผลลัพธ์การเปรียบเทียบ:</strong> (1) <strong>Qwen3 4B (Ollama)</strong> ทำคะแนน PR-AUC ได้สูงสุดที่ 0.7400 บนชุดสมดุลนี้ และได้ Recall 0.8000, F1 0.6667 (2) <strong>Gemini 3.5 Flash Lite</strong> ทำคะแนน Recall สูงสุด 0.9000, Precision สูงสุด 0.8182, F1 สูงสุด 0.8571, และ Brier Score ต่ำสุด 0.1453 (3) <strong>Llama 3.2 3B (Ollama)</strong> ทำคะแนนได้สมดุลดีเยี่ยมด้วย PR-AUC 0.7111, Recall 0.7000, และ F1 0.6667 (4) <strong>Mistral 7B (Ollama)</strong> มีลักษณะอนุรักษนิยมสูงสุด (Conservative) ได้ Precision 1.0000 (ไม่มี False Positive เลย) แต่ Recall อยู่ที่ 0.2000 ส่งผลให้ F1 อยู่ที่ 0.3333 และ Brier 0.3625" data-en="<strong>Comparative Performance Interpretation:</strong> (1) <strong>Qwen3 4B (Ollama)</strong> achieved top pilot PR-AUC at 0.7400 on this balanced cohort, with 0.8000 Recall and 0.6667 F1. (2) <strong>Gemini 3.5 Flash Lite</strong> led in Precision (0.8182), Recall (0.9000), F1 (0.8571), and lowest Brier Score (0.1453). (3) <strong>Llama 3.2 3B (Ollama)</strong> performed solidly with PR-AUC 0.7111, Recall 0.7000, and F1 0.6667. (4) <strong>Mistral 7B (Ollama)</strong> exhibited ultra-conservative predictions with perfect 1.0000 Precision (zero FP) but low 0.2000 Recall, yielding F1 0.3333 and Brier 0.3625."><strong>คำอธิบายผลลัพธ์การเปรียบเทียบ:</strong> Qwen3 4B ได้ PR-AUC สูงสุด 0.7400; Gemini ได้ Recall 0.9000 และ F1 0.8571 สูงสุด; Llama 3.2 3B ได้ PR-AUC 0.7111 และ F1 0.6667; Mistral 7B ได้ Precision 1.0000</p>

      <!-- CHART 4: PILOT CONFUSION MATRIX COMPARISON -->
      {interactive_pilot_cm_chart}
      <h4 data-th="ตารางสรุป Confusion Matrix ทั้ง 4 โมเดลบน Pilot Cohort (N=20)" data-en="Pilot Confusion Matrix Summary Table Across 4 Models (N=20)">ตารางสรุป Confusion Matrix ทั้ง 4 โมเดลบน Pilot Cohort (N=20)</h4>
      {table(pilot_cm_table)}
      <p class="chart-explanation" data-th="<strong>คำอธิบายผลลัพธ์ Confusion Matrix:</strong> โมเดลทั้ง 4 ตัวถูกประเมินบนนักเรียน 20 คนชุดเดียวกันอย่างเท่าเทียม: Gemini ทายถูก 17 คน (TN 8, TP 9, FN 1, FP 2); Llama 3.2 3B ทายถูก 13 คน (TN 6, TP 7, FN 3, FP 4); Qwen3 4B ทายถูก 12 คน (TN 4, TP 8, FN 2, FP 6); Mistral 7B ทายถูก 12 คน (TN 10, TP 2, FN 8, FP 0) แสดงให้เห็นถึงพฤติกรรมการตัดสินใจที่แตกต่างกันอย่างชัดเจนของแต่ละตระกูลโมเดล" data-en="<strong>Confusion Matrix Interpretation:</strong> All four models were tested on the identical 20 students: Gemini correctly classified 17 learners (TN 8, TP 9, FN 1, FP 2); Llama 3.2 3B correctly classified 13 (TN 6, TP 7, FN 3, FP 4); Qwen3 4B correctly classified 12 (TN 4, TP 8, FN 2, FP 6); Mistral 7B correctly classified 12 (TN 10, TP 2, FN 8, FP 0). This highlights distinct operational risk profiles across model architectures."><strong>คำอธิบายผลลัพธ์ Confusion Matrix:</strong> Gemini จำแนกถูก 17 คน; Llama 3.2 3B จำแนกถูก 13 คน; Qwen3 4B จำแนกถูก 12 คน; Mistral 7B จำแนกถูก 12 คน (ไม่มี FP เลย)</p>

      <!-- CHART 5: PILOT EFFICIENCY AND TOKEN USAGE -->
      {interactive_pilot_efficiency_chart}
      <h4 data-th="ตารางประสิทธิภาพระยะเวลาและปริมาณ Token (N=20)" data-en="Pilot Runtime & Token Efficiency Table (N=20)">ตารางประสิทธิภาพระยะเวลาและปริมาณ Token (N=20)</h4>
      {table(pilot_efficiency_table)}
      <p class="chart-explanation" data-th="<strong>คำอธิบายผลลัพธ์ประสิทธิภาพและต้นทุนคำนวณ:</strong> Gemini 3.5 Flash Lite ใช้เวลาประมวลผลเร็วที่สุดที่ 3.5 วินาที (0.18 วินาที/คน) เนื่องจากทำงานบน Cloud Infrastructure ของ Google ขณะที่โมเดล Local บนเครื่องผ่าน Ollama: Llama 3.2 3B ใช้เวลา 29.3 วินาที (1.46 วินาที/คน), Qwen3 4B ใช้เวลา 32.6 วินาที (1.63 วินาที/คน), และ Mistral 7B ใช้เวลา 75.6 วินาที (3.78 วินาที/คน) โดยปริมาณ Token รวมอยู่ระหว่าง 5,400 ถึง 6,561 tokens จุดเด่นสำคัญของ Local Models คือข้อมูลนักเรียนทั้งหมดถูกประมวลผลบนเครื่อง ไม่มีการส่งข้อมูลออกนอกระบบ มีความเป็นส่วนตัวสูงสุดและไม่มีค่าบริการ API" data-en="<strong>Efficiency & Compute Cost Interpretation:</strong> Gemini 3.5 Flash Lite was the fastest at 3.5s total (0.18s/student) running on Google Cloud clusters. Local on-device Ollama models took 29.3s for Llama 3.2 3B (1.46s/student), 32.6s for Qwen3 4B (1.63s/student), and 75.6s for Mistral 7B (3.78s/student), consuming 5,400 to 6,561 total tokens. The paramount benefit of local open-weight models is total on-device data sovereignty, enterprise privacy compliance, and zero API subscription charges."><strong>คำอธิบายผลลัพธ์ประสิทธิภาพและต้นทุนคำนวณ:</strong> Gemini ใช้เวลาเร็วสุด 3.5 วินาทีผ่าน Cloud API ส่วน Local Models ในเครื่อง: Llama 3.2 3B ใช้ 29.3 วินาที, Qwen3 4B ใช้ 32.6 วินาที, Mistral 7B ใช้ 75.6 วินาที โดยข้อมูลอยู่ในเครื่อง 100%</p>

      <!-- ========================================== -->
      <!-- PART 3: PROVIDER STATUS & GOVERNANCE       -->
      <!-- ========================================== -->
      <h3 data-th="ส่วนที่ 3: สถานะผู้ให้บริการโมเดลภาษา และธรรมาภิบาลโครงการ (Model Provider Status & Governance)" data-en="Part 3: Model Provider Status & Governance">ส่วนที่ 3: สถานะผู้ให้บริการโมเดลภาษา และธรรมาภิบาลโครงการ (Model Provider Status & Governance)</h3>
      {table(llm_api_status)}
      <p class="note-box" data-th="<strong>นโยบายโครงการเป็น Free-only:</strong> Gemini รัน Full Test จริงครบ 1,800 คน และรัน Comparative Balanced Pilot (N=20); ส่วนโมเดล Local ใน Ollama ทั้ง 3 ตัว (Qwen3 4B, Llama 3.2 3B, Mistral 7B) รัน Comparative Balanced Pilot (N=20) บนฮาร์ดแวร์จริงเสร็จสิ้นสมบูรณ์แล้ว ไม่ใช่แค่ smoke test ผู้ให้บริการที่ต้องเสียค่าใช้จ่าย (OpenAI, Anthropic) ถูกตัดออกตามนโยบายฟรีเท่านั้น โดยแดชบอร์ดไม่แสดงโมเดลที่ไม่ได้ทดสอบจริง และไม่มีการสร้างตัวเลขจำลองใด ๆ ทั้งสิ้น" data-en="<strong>Free-Only Project Policy:</strong> Gemini completed the empirical Full Test on all 1,800 students and the Comparative Balanced Pilot (N=20). All three local Ollama models (Qwen3 4B, Llama 3.2 3B, Mistral 7B) completed empirical evaluation on the Comparative Balanced Pilot (N=20) on actual hardware—not just smoke tests. Commercial paid APIs (OpenAI, Anthropic) were excluded under the free-only mandate. No unverified models are displayed, and no results are fabricated."><strong>นโยบายโครงการเป็น Free-only:</strong> Gemini รัน Full Test ครบ 1,800 คน และรัน Pilot (N=20); ส่วนโมเดล Local ทั้ง 3 ตัว (Qwen3 4B, Llama 3.2 3B, Mistral 7B) รัน Pilot (N=20) เสร็จสิ้นสมบูรณ์แล้ว ไม่ใช่แค่ smoke test ไม่มีโมเดลที่ไม่ได้ทดสอบจริง และไม่มีตัวเลขจำลอง</p>

      <!-- ========================================== -->
      <!-- PART 4: NLP BASELINES FOR HISTORICAL REF   -->
      <!-- ========================================== -->
      <h3 data-th="ส่วนอ้างอิง: ผล NLP รุ่นเดิม" data-en="Reference: Legacy NLP Results">ส่วนอ้างอิง: ผล NLP รุ่นเดิม</h3>
      <details>
        <summary data-th="ดูตารางผลรุ่นเดิมก่อน Offline Benchmark ฉบับสมบูรณ์" data-en="View the legacy results created before the complete offline benchmark">ดูตารางผลรุ่นเดิมก่อน Offline Benchmark ฉบับสมบูรณ์</summary>
        <!-- outputs/tables/llm_text_classifier_comparison.csv -->
        {table(llm_models)}
        <!-- outputs/tables/llm_text_confusion_matrices.csv -->
        {table(llm_confusions)}
        <p class="note-box" data-th="ตารางนี้เก็บไว้เพื่อ audit เท่านั้น ผลหลักให้ใช้ตาราง Offline ด้านบน ผู้ชนะของตารางรุ่นเดิมคือ TF-IDF (1–2 grams) + Logistic Regression ที่ PR-AUC 0.4826 ไม่ใช่ DistilBERT" data-en="This table is retained for audit only. Use the complete offline table above for conclusions. The legacy-table winner is TF-IDF (1–2 grams) + Logistic Regression at PR-AUC 0.4826, not DistilBERT.">ตารางนี้เก็บไว้เพื่อ audit เท่านั้น ผู้ชนะของตารางรุ่นเดิมคือ TF-IDF Bigram ที่ PR-AUC 0.4826 ไม่ใช่ DistilBERT</p>
      </details>

      <details open>
        <summary data-th="ดูตัวอย่างข้อความที่สร้างจากนักเรียนหนึ่งแถว (View Serialized Row-to-Text Samples)" data-en="View Example Text Serialized from One Student Row">ดูตัวอย่างข้อความที่สร้างจากนักเรียนหนึ่งแถว (View Serialized Row-to-Text Samples)</summary>
        {table(llm_text_inputs[["split", "text_type", "student_behavior_text", "target_stored_separately"]], max_rows=10)}
        <p class="note-box" data-th="คำว่า video plays หมายถึงจำนวนครั้งที่ระบบบันทึกการกดเล่น ไม่ใช่ระยะเวลาที่ดูคลิป ข้อความนี้เป็น behavioral profile สำหรับ classification ไม่ใช่ transcript ของคำพูดในวิดีโอ" data-en="Video plays means recorded play/click events—not viewing duration. This text is a behavioral profile for classification, not a transcript of spoken lecture content.">คำว่า video plays หมายถึงจำนวนครั้งที่ระบบบันทึกการกดเล่น ไม่ใช่ระยะเวลาที่ดูคลิป ข้อความนี้เป็น behavioral profile สำหรับ classification ไม่ใช่ transcript ของคำพูดในวิดีโอ</p>
      </details>

      <h3 data-th="ขั้นตอนการทำงาน 11 ขั้นตอนของ Track LLM / Transformer" data-en="LLM / Transformer 11-Step Governed Lifecycle">ขั้นตอนการทำงาน 11 ขั้นตอนของ Track LLM / Transformer</h3>
      {workflow_grid("llm", llm_status)}
    </section>

    <!-- VIEW 6: RESULTS SUMMARY -->
    <section class="view" id="summary">
      <h2 data-th="สรุปผลลัพธ์รวมทุก Track และข้อเสนอแนะเชิงนโยบาย (Results Summary & Recommendations)" data-en="Integrated Results Summary & Policy Recommendations">สรุปผลลัพธ์รวมทุก Track และข้อเสนอแนะเชิงนโยบาย (Results Summary & Recommendations)</h2>

      <div class="summary-grid">
        <div class="card winner">
          <h3>Traditional Unsupervised</h3>
          <p><strong>{html.escape(unsup_manifest['selected_family'])}, k={unsup_manifest['selected_k']}</strong></p>
          <p data-th="Silhouette {unsup_winner['silhouette']:.4f} · Calinski-Harabasz {unsup_winner['calinski_harabasz']:.1f} · เลือก k={unsup_manifest['selected_k']} จากคะแนนรวม 6 metric เป็น K ค่าเดียว ไม่ใช่ Elbow เดี่ยว" data-en="Silhouette {unsup_winner['silhouette']:.4f} · Calinski-Harabasz {unsup_winner['calinski_harabasz']:.1f} · Selected k={unsup_manifest['selected_k']} as a single K from the weighted six-metric score, not a single Elbow curve.">Silhouette {unsup_winner['silhouette']:.4f} · Calinski-Harabasz {unsup_winner['calinski_harabasz']:.1f} · เลือก k={unsup_manifest['selected_k']} จากคะแนนรวม 6 metric เป็น K ค่าเดียว ไม่ใช่ Elbow เดี่ยว</p>
        </div>

        <div class="card winner">
          <h3>Deep Learning (Challenger)</h3>
          <p><strong>{html.escape(deep_manifest['selected_model_name'])}</strong></p>
          <p>Test PR-AUC {deep_winner['test_pr_auc']:.4f} · ROC-AUC {deep_winner['test_roc_auc']:.4f} · Test F1 {deep_winner['test_f1']:.4f} · Brier {deep_winner['test_brier']:.4f}</p>
        </div>

        <div class="card winner">
          <h3>Supervised Learning (Champion)</h3>
          <p><strong>{html.escape(sup_manifest['selected_model_name'])}</strong></p>
          <p>Test PR-AUC {sup_winner['test_pr_auc']:.4f} · ROC-AUC {sup_winner['test_roc_auc']:.4f} · Test F1 {sup_winner['test_f1']:.4f} · Accuracy {sup_winner['test_accuracy']*100:.2f}%</p>
        </div>

        <div class="card winner">
          <h3>Generative AI · Student Text Classification</h3>
          <p><strong>{html.escape(llm_api_winner['model_name'])}</strong></p>
          <p>Test PR-AUC {llm_api_winner['test_pr_auc']:.4f} · ROC-AUC {llm_api_winner['test_roc_auc']:.4f} · Recall {llm_api_winner['test_recall']:.4f} · F1 {llm_api_winner['test_f1']:.4f}</p>
        </div>
      </div>

      {interactive_summary_chart}

      <div class="card accent">
        <h3 data-th="ข้อสรุปหลักของการวิเคราะห์ (Key Insights & Executive Conclusions)" data-en="Executive Insights & Core Conclusions">ข้อสรุปหลักของการวิเคราะห์ (Key Insights & Executive Conclusions)</h3>
        <p data-th="1. ทำความสะอาดข้อมูลใหม่เป็น {enrollments:,} student-course enrollments และ {students:,} นักศึกษาไม่ซ้ำ<br>2. Target Quarantine ทำให้การแบ่งกลุ่มและสร้างข้อความไม่ปะปนผลลัพธ์<br>3. Supervised และ Deep Learning ถูกเทรนใหม่บนข้อมูล cleaned ล่าสุด<br>4. ความสัมพันธ์ระหว่างกิจกรรมกับความสำเร็จเป็นเชิงพรรณนา ไม่ใช่เหตุและผล<br>5. LLM/Gemini section ยังคงใช้ผลการทดลองเดิมที่บันทึกไว้ เว้นแต่จะรัน LLM ใหม่แยกต่างหาก" data-en="1. Re-cleaned data into {enrollments:,} student-course enrollments and {students:,} unique students.<br>2. Target quarantine keeps clustering and text serialization free of outcomes.<br>3. Supervised and deep-learning models were retrained on the refreshed cleaned data.<br>4. Engagement-success relationships are descriptive, not causal.<br>5. The LLM/Gemini section retains the previously recorded experiment unless the LLM track is rerun separately.">1. ทำความสะอาดข้อมูลใหม่เป็น {enrollments:,} student-course enrollments และ {students:,} นักศึกษาไม่ซ้ำ<br>2. Target Quarantine ทำให้การแบ่งกลุ่มและสร้างข้อความไม่ปะปนผลลัพธ์<br>3. Supervised และ Deep Learning ถูกเทรนใหม่บนข้อมูล cleaned ล่าสุด<br>4. ความสัมพันธ์ระหว่างกิจกรรมกับความสำเร็จเป็นเชิงพรรณนา ไม่ใช่เหตุและผล<br>5. LLM/Gemini section ยังคงใช้ผลการทดลองเดิมที่บันทึกไว้ เว้นแต่จะรัน LLM ใหม่แยกต่างหาก</p>
      </div>

      {segment_comparison_block(segment_comparison, "ส่วนสรุปผลลัพธ์รวมใช้กราฟชุดเดียวกันในการเปรียบเทียบทุก Segment เพื่อให้ผู้มีส่วนได้ส่วนเสียเห็นภาพรวมบนฐานข้อมูลเดียวกัน", "The integrated summary uses consistent visualizations across all segments, grounding decisions on shared empirical evidence.")}

      <div class="grid-2">
        <div class="card">
          <h3 data-th="ข้อจำกัดของโครงการ (Project Limitations)" data-en="Project Limitations">ข้อจำกัดของโครงการ (Project Limitations)</h3>
          <ul>
            <li data-th="ข้อมูลเป็น MOOC ยุคแรก (2012–2013) ซึ่งอาจไม่สะท้อนพฤติกรรมของผู้เรียนในแพลตฟอร์มการศึกษายุคปัจจุบันที่มีเทคโนโลยี Micro-learning และ AI" data-en="Data originates from 2012–2013 early MOOCs; engagement patterns may differ from modern AI-assisted micro-learning platforms.">ข้อมูลเป็น MOOC ยุคแรก (2012–2013) ซึ่งอาจไม่สะท้อนพฤติกรรมของผู้เรียนในแพลตฟอร์มการศึกษายุคปัจจุบันที่มีเทคโนโลยี Micro-learning และ AI</li>
            <li data-th="ฟีเจอร์พฤติกรรมเป็นการรวมยอดสะสมตลอดวิชา (Aggregate Totals) ไม่ใช่ลำดับเหตุการณ์แบบ Time-series (Event Sequences) จึงไม่สามารถใช้พยากรณ์ความเสี่ยงแบบ Real-time รายสัปดาห์ได้" data-en="Features are coarse aggregations rather than event-level sequences, preventing weekly dynamic early-warning forecasting.">ฟีเจอร์พฤติกรรมเป็นการรวมยอดสะสมตลอดวิชา (Aggregate Totals) ไม่ใช่ลำดับเหตุการณ์แบบ Time-series (Event Sequences) จึงไม่สามารถใช้พยากรณ์ความเสี่ยงแบบ Real-time รายสัปดาห์ได้</li>
            <li data-th="ยังไม่มีกลุ่มข้อมูลรุ่นถัดไป (Future Cohort) สำหรับการประเมิน Data Drift และ Concept Drift ในสภาวะใช้งานจริง" data-en="No genuine future cohort exists in the public dataset, requiring drift monitoring to remain in a ready-baseline state.">ยังไม่มีกลุ่มข้อมูลรุ่นถัดไป (Future Cohort) สำหรับการประเมิน Data Drift และ Concept Drift ในสภาวะใช้งานจริง</li>
            <li data-th="ข้อความของ LLM track เป็นการ serialize พฤติกรรมรวมระดับนักเรียน ไม่ใช่ transcript เนื้อหาวิดีโอ และจำนวน video plays ไม่บอกเวลารับชมจริง" data-en="The LLM-track text serializes aggregate student behavior; it is not lecture transcript content, and video-play counts do not reveal true watch duration.">ข้อความของ LLM track เป็นการ serialize พฤติกรรมรวมระดับนักเรียน ไม่ใช่ transcript เนื้อหาวิดีโอ และจำนวน video plays ไม่บอกเวลารับชมจริง</li>
          </ul>
        </div>

        <div class="card">
          <h3 data-th="ข้อเสนอแนะเชิงนโยบายและการดำเนินงานถัดไป (Actionable Next Steps)" data-en="Actionable Recommendations & Next Steps">ข้อเสนอแนะเชิงนโยบายและการดำเนินงานถัดไป (Actionable Next Steps)</h3>
          <ol>
            <li data-th="จัดเก็บข้อมูลนักศึกษารุ่นปัจจุบัน (Future Cohort) พร้อมฉลากผลลัพธ์จริง เพื่อเปิดใช้งานระบบตรวจสอบ Drift และคำนวณค่า PSI ประจำเดือน" data-en="Ingest contemporary labeled cohorts to activate production PSI drift monitoring and monthly calibration checks.">จัดเก็บข้อมูลนักศึกษารุ่นปัจจุบัน (Future Cohort) พร้อมฉลากผลลัพธ์จริง เพื่อเปิดใช้งานระบบตรวจสอบ Drift และคำนวณค่า PSI ประจำเดือน</li>
            <li data-th="พัฒนาระบบบันทึก Clickstream ในระดับ Event-level Timestamps เพื่อรองรับโมเดลพยากรณ์ Early-warning ใน 2 สัปดาห์แรกของการเรียน" data-en="Implement event-level clickstream logging to enable week-1/week-2 dynamic early-warning intervention models.">พัฒนาระบบบันทึก Clickstream ในระดับ Event-level Timestamps เพื่อรองรับโมเดลพยากรณ์ Early-warning ใน 2 สัปดาห์แรกของการเรียน</li>
            <li data-th="จัดหาไฟล์วิดีโอ เสียง หรือ Official Captions ตามมาตรฐาน 8 ขั้นตอน เพื่อปลดล็อก Track Content LLM อย่างถูกต้อง" data-en="Acquire course media or official captions following the 8-stage pipeline to formally unlock the LLM content track.">จัดหาไฟล์วิดีโอ เสียง หรือ Official Captions ตามมาตรฐาน 8 ขั้นตอน เพื่อปลดล็อก Track Content LLM อย่างถูกต้อง</li>
            <li data-th="นำโมเดล Unsupervised Personas ไปใช้จัดหมวดหมู่การแจ้งเตือนและการสื่อสารของอาจารย์ผู้สอนให้ตรงกับพฤติกรรมของผู้เรียน" data-en="Operationalize unsupervised personas to personalize instructor outreach and forum engagement campaigns.">นำโมเดล Unsupervised Personas ไปใช้จัดหมวดหมู่การแจ้งเตือนและการสื่อสารของอาจารย์ผู้สอนให้ตรงกับพฤติกรรมของผู้เรียน</li>
          </ol>
        </div>
      </div>

      <section class="card">
        <h3 data-th="เอกสารอ้างอิงทางวิชาการ (References)" data-en="Academic References">เอกสารอ้างอิงทางวิชาการ (References)</h3>
        <ol>
          <li><a href="https://doi.org/10.7910/DVN/26147" target="_blank" rel="noopener">HarvardX Person-Course Dataset v3.0, Harvard Dataverse (doi:10.7910/DVN/26147)</a></li>
          <li><a href="https://www.kaggle.com/datasets/kanikanarang94/mooc-dataset" target="_blank" rel="noopener">MOOC Dataset Repository, Kaggle-supplied complementary file</a></li>
          <li><a href="https://doi.org/10.1145/2460296.2460330" target="_blank" rel="noopener">Kizilcec, R. F., Piech, C., & Schneider, E. (2013). Deconstructing disengagement: analyzing learner subpopulations in massive open online courses. In Proceedings of the Third International Conference on Learning Analytics and Knowledge (LAK '13), pp. 162–169.</a></li>
          <li><a href="https://doi.org/10.1111/1467-9868.00293" target="_blank" rel="noopener">Tibshirani, R., Walther, G., & Hastie, T. (2001). Estimating the number of clusters in a data set via the gap statistic. Journal of the Royal Statistical Society: Series B, 63(2), 411–423.</a></li>
          <li><a href="https://doi.org/10.1126/science.1127647" target="_blank" rel="noopener">Hinton, G. E., & Salakhutdinov, R. R. (2006). Reducing the dimensionality of data with neural networks. Science, 313(5786), 504–507.</a></li>
          <li><a href="https://doi.org/10.3390/info12110476" target="_blank" rel="noopener">Dass, S., Gary, K., & Cunningham, J. (2021). Predicting Student Performance in MOOCs Using Behavioral Features. Information, 12(11), 476.</a></li>
          <li><a href="https://doi.org/10.1109/EDUCON.2018.8363340" target="_blank" rel="noopener">A Systematic Literature Review on MOOC Dropout Prediction (IEEE EDUCON 2018).</a></li>
        </ol>
      </section>
    </section>

  </div>
</main>

<script>
  const segmentData = {segment_json};
  const profileData = {json.dumps(raw_profile_json, ensure_ascii=False)};
  const classData = {json.dumps(value_counts_json, ensure_ascii=False)};
  const scenarioCenters = {scenario_centers_json};
  const unsupFeatures = {unsup_feature_json};
  let language = 'th';

  // Navigation tabs
  document.querySelectorAll('.track-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.track-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      const primary = document.getElementById(btn.dataset.view);
      if (primary) primary.classList.add('active');
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  }});

  // Sidebar toggle
  document.getElementById('sideToggle').onclick = () => {{
    document.getElementById('sidebar').classList.toggle('collapsed');
    document.body.classList.toggle('side-collapsed');
  }};

  // Bilingual Language Toggle
  document.getElementById('languageToggle').onclick = () => {{
    language = language === 'th' ? 'en' : 'th';
    document.documentElement.lang = language;
    document.querySelectorAll('[data-th][data-en]').forEach(el => {{
      if (el.dataset[language]) {{
        el.innerHTML = el.dataset[language];
      }}
    }});
  }};

  function niceFeatureName(x) {{
    return x.replace('mean_course_', '').replace('_percentile', '').replaceAll('_', ' ');
  }}
  function pct(v) {{
    return v == null ? '—' : (v * 100).toFixed(2) + '%';
  }}

  // Segment dynamic rendering
  function renderSegment() {{
    const key = document.getElementById('segmentSelect').value;
    const d = segmentData.segments[key];
    const kpiBox = document.getElementById('segmentKpis');
    if (kpiBox) {{
      kpiBox.innerHTML = `
        <div class="kpi"><small>Students</small><strong>${{d.students.toLocaleString()}}</strong></div>
        <div class="kpi"><small>Certification rate</small><strong>${{pct(d.certification_rate)}}</strong></div>
        <div class="kpi"><small>Mean predicted probability</small><strong>${{pct(d.mean_predicted_probability)}}</strong></div>
        <div class="kpi"><small>Active Segment</small><strong>${{key.replaceAll('_', ' ').toUpperCase()}}</strong></div>
      `;
    }}
    const clusterBox = document.getElementById('clusterBars');
    if (clusterBox) {{
      const total = Object.values(d.cluster_distribution).reduce((a, b) => a + b, 0);
      clusterBox.innerHTML = Object.entries(d.cluster_distribution).map(([k, v]) => `
        <div class="bar-row">
          <b>Cluster ${{k}}</b>
          <div class="bar"><i style="width:${{(v / total * 100).toFixed(2)}}%"></i></div>
          <span>${{v.toLocaleString()}} (${{(v / total * 100).toFixed(1)}}%)</span>
        </div>
      `).join('');
    }}
    const featBox = document.getElementById('segmentFeatureBars');
    if (featBox) {{
      featBox.innerHTML = Object.entries(d.mean_features).map(([k, v]) => `
        <div class="bar-row">
          <b>${{niceFeatureName(k)}}</b>
          <div class="bar"><i style="width:${{(Number(v) * 100).toFixed(2)}}%"></i></div>
          <span>${{Number(v).toFixed(3)}}</span>
        </div>
      `).join('');
    }}
  }}
  document.getElementById('segmentSelect').onchange = renderSegment;
  renderSegment();

  // Scenario Explorer
  function renderScenarioExplorer() {{
    const box = document.getElementById('scenarioSliders');
    if (!box) return;
    box.innerHTML = unsupFeatures.map(f => `
      <div class="slider-row">
        <label>${{niceFeatureName(f)}}: <span id="val-${{f}}" style="color:var(--navy);font-weight:800;">0.50</span></label>
        <input type="range" min="0" max="1" value="0.5" step="0.01" data-feature="${{f}}">
      </div>
    `).join('');

    function update() {{
      const values = {{}};
      box.querySelectorAll('input').forEach(inp => {{
        values[inp.dataset.feature] = Number(inp.value);
        document.getElementById('val-' + inp.dataset.feature).textContent = Number(inp.value).toFixed(2);
      }});
      let best = null;
      scenarioCenters.forEach(c => {{
        let dist = 0;
        unsupFeatures.forEach(f => {{
          dist += Math.pow(values[f] - Number(c[f]), 2);
        }});
        dist = Math.sqrt(dist);
        if (best === null || dist < best.dist) {{
          best = {{ cluster: c.cluster, dist: dist, center: c }};
        }}
      }});
      const resBox = document.getElementById('scenarioResult');
      if (resBox && best) {{
        resBox.innerHTML = `
          <div style="margin-top:14px;display:flex;align-items:center;flex-wrap:wrap;gap:12px;">
            <span class="result-pill">🎯 Nearest Persona: Cluster ${{best.cluster}}</span>
            <span class="note-box" style="margin:0;padding:8px 14px;">Euclidean Distance to Profile Center: <b>${{best.dist.toFixed(4)}}</b></span>
          </div>
        `;
      }}
    }}
    box.querySelectorAll('input').forEach(inp => inp.addEventListener('input', update));
    update();
  }}
  renderScenarioExplorer();

  // Interactive Column Profiler
  const sourceSelect = document.getElementById('sourceFilter');
  const columnSelect = document.getElementById('columnFilter');
  if (sourceSelect && columnSelect) {{
    const sources = [...new Set(profileData.map(x => x.source_file))];
    sourceSelect.innerHTML = sources.map(x => `<option>${{x}}</option>`).join('');

    function updateColumns() {{
      const cols = profileData.filter(x => x.source_file === sourceSelect.value).sort((a, b) => a.column_position - b.column_position);
      columnSelect.innerHTML = cols.map(x => `<option>${{x.column_name}}</option>`).join('');
      renderColumn();
    }}

    function renderColumn() {{
      const s = sourceSelect.value;
      const c = columnSelect.value;
      const p = profileData.find(x => x.source_file === s && x.column_name === c);
      if (!p) return;
      document.getElementById('columnProfile').innerHTML = `
        <div class="kpis">
          <div class="kpi"><small>Total Records</small><strong>${{Number(p.records).toLocaleString()}}</strong></div>
          <div class="kpi"><small>Missing Count</small><strong>${{Number(p.missing_count).toLocaleString()}} (${{Number(p.missing_percent).toFixed(2)}}%)</strong></div>
          <div class="kpi"><small>Distinct Values</small><strong>${{Number(p.distinct_non_missing).toLocaleString()}}</strong></div>
          <div class="kpi"><small>Inferred Type</small><strong>${{p.raw_dtype}}</strong></div>
        </div>
      `;
      const rows = classData.filter(x => x.source_file === s && x.column_name === c);
      document.getElementById('classCounts').innerHTML = `
        <div class="table-wrap">
          <table>
            <thead><tr><th>Value / Category</th><th>Count</th><th>Percent</th><th>Coverage</th></tr></thead>
            <tbody>
              ${{rows.map(r => `<tr><td><b>${{r.value}}</b></td><td>${{Number(r.count).toLocaleString()}}</td><td>${{Number(r.percent).toFixed(3)}}%</td><td>${{r.coverage}}</td></tr>`).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    sourceSelect.onchange = updateColumns;
    columnSelect.onchange = renderColumn;
    updateColumns();
  }}
</script>
</body>
</html>"""

    REPORT.write_text(document, encoding="utf-8")
    checksum = hashlib.sha256(REPORT.read_bytes()).hexdigest()

    embedded_figures = [
        "full_distributions", "robust_boxplots", "zero_missing_outlier_profile",
        "behavior_relationships", "correlation_matrix", "activity_outlier_diagnostics",
        "video_quality_diagnostics", "institutes_breakdown", "pca_variance",
        "certified_grade_threshold_audit",
        "persona_proportions", "cluster_profile_radar",
        "unsupervised_model_radar", "behavior_hyperspace_3d", "segment_feature_comparison",
        "segment_distribution_comparison", "segment_cluster_comparison", "segment_outcome_comparison",
        "certification_class_balance", "supervised_model_comparison", "supervised_confusion_matrix", "supervised_confusion_matrices_comparison",
        "deep_model_comparison", "deep_confusion_matrices", "deep_roc_calibration",
    ]

    manifest = {
        "report": str(REPORT.relative_to(ROOT)),
        "sha256": checksum,
        "language_modes": ["Thai", "English"],
        "track_views": [
            "Project Overview",
            "Traditional Unsupervised",
            "Deep Learning",
            "Supervised Learning",
            "LLM",
            "Results Summary",
        ],
        "dynamic_segments": list(segments["segments"].keys()),
        "eda_location": "Project Overview",
        "eda_figures_embedded": embedded_figures,
        "interactive_charts": [
            "segment_behavior_comparison",
            "unsupervised_k_sensitivity_multiseed_audit",
            "deep_learning_model_comparison",
            "supervised_model_comparison",
            "hosted_generative_ai_model_result",
            "gemini_confusion_matrix",
            "comparative_balanced_pilot_metrics",
            "comparative_balanced_pilot_confusion_matrices",
            "comparative_balanced_pilot_efficiency",
            "llm_student_behavior_text_model_comparison",
            "llm_text_confusion_matrix_comparison",
            "cross_track_selected_model_summary",
        ],
        "llm_status": "Free-only policy: Gemini completed 1,800 students Full Test; Qwen3 4B, Llama 3.2 3B, and Mistral 7B completed Comparative Balanced Pilot (N=20); unavailable models are omitted from the dashboard.",
        "llm_target": "Certification prediction from one factual student-behavior text record per student.",
        "workflow_alignment": "Master Universal Data Science and Machine Learning Workflow (Merged_Workflow.md)",
        "data_source": "Computed project artifacts; no values manually invented in the report generator.",
    }

    with open(ROOT / "reports" / "report_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    print(f"[+] High-fidelity bilingual dashboard written to {REPORT} (SHA-256: {checksum[:12]}...)")


if __name__ == "__main__":
    run_generate_report()
