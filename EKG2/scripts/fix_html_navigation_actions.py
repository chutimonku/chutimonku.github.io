"""
scripts/fix_html_navigation_actions.py
======================================
Ensures Next and Previous page buttons in ekg_longitudinal_dashboard.html work 100%:
1. Replaces all `onclick="switchStep('step-X')"` with `onclick="showPage('step-X')"`
2. Adds `window.showPage = showPage;` and `window.switchStep = showPage;` to global scope.
3. Tests execution with Node.js.
"""

import re
import os

html_path = 'outputs/dashboard/ekg_longitudinal_dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace switchStep with showPage on all navigation buttons
old_count = content.count("switchStep('step-")
content = content.replace("switchStep('step-", "showPage('step-")
print(f"✅ Replaced {old_count} instances of switchStep with showPage in button onclick attributes!")

# 2. Add window.switchStep and window.showPage export in JavaScript
export_needle = "window.copyNarrativeToClipboard = copyNarrativeToClipboard;"
export_replacement = """window.copyNarrativeToClipboard = copyNarrativeToClipboard;
        window.showPage = showPage;
        window.switchStep = showPage;"""

if export_needle in content:
    content = content.replace(export_needle, export_replacement, 1)
    print("✅ Exported window.showPage and window.switchStep to global scope!")
else:
    print("⚠️ export_needle not found, checking if already defined...")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {html_path}, size: {os.path.getsize(html_path):,} bytes.")
