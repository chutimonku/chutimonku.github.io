## Step 10 — Communication and Interactive HTML Reporting

Create a responsive HTML report that can run as a standalone report or server-backed dashboard.

### Required report sections

1. Executive summary
2. Problem definition
3. Data provenance
4. Data quality and cleaning
5. Exploratory data analysis
6. Literature review
7. Feature engineering
8. Model selection
9. Training and experiments
10. Model evaluation
11. Error analysis
12. Explainability and fairness
13. Deployment readiness
14. Monitoring plan
15. Limitations
16. Recommendations
17. Reproducibility information

### Bilingual requirements

When bilingual reporting is required, the TH/EN control should translate navigation, headings, explanations, chart labels, table headings, statistical annotations, warnings, and recommendations.

### Interactive components

Dashboard charts should be interactive by default, with accessible data tables and static export available as a fallback. Where appropriate, include filters, date selectors, segment selectors, model and metric selectors, feature selectors, tooltips, linked highlighting, zoom/pan/reset controls, downloadable tables, expandable methods, a what-if simulator, and prediction explanations. An interactive control must not change a locked model result or silently recompute a metric without clearly displaying the active cohort, filters, model version, and calculation state.

### What-if simulator safeguards

The simulator must validate inputs, display the active model version, show uncertainty where possible, use only features available at inference, prevent post-outcome features, and state that simulation does not prove causality.

---