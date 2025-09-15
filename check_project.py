import os
from datetime import datetime
import subprocess

# --- Folders to skip ---
SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache"}

# --- Storage for results ---
lint_results = []
summary_counts = {"lint_ok": 0, "lint_err": 0}

# --- Project root ---
project_root = os.path.dirname(os.path.abspath(__file__))

# --- Collect Python files (skip __init__.py, only inside project root) ---
py_files = []
for root, dirs, files in os.walk(project_root):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        full_path = os.path.join(root, f)
        if f.endswith(".py") and f != "__init__.py" and full_path.startswith(project_root):
            py_files.append(full_path)
# --- Print total once ---
print(f"🔍 Checking {len(py_files)} Python files with flake8 (skip blank/long lines)...\n")

# --- Lint each file ---
for file in py_files:
    rel_file = os.path.relpath(file, project_root)
    print(f"Linting: {rel_file} ...", end=" ")
    try:
        # Run flake8 on the file, ignore E501 (line too long) and E303 (blank lines)
        result = subprocess.run(
            ["flake8", "--ignore=E501,E303,E101,E111,E201,E231,W191,W293,W291,E302,F401,F541,E225,E503,E261,E262,W292,E402,206", file],
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        if output:
            print(f"⚠️ Issues found")
            lint_results.append((rel_file, "⚠️ Issues", output))
            summary_counts["lint_err"] += 1
        else:
            print("✅ OK")
            lint_results.append((rel_file, "✅ OK", ""))
            summary_counts["lint_ok"] += 1
    except Exception as e:
        print(f"❌ Error running flake8: {e}")
        lint_results.append((rel_file, "❌ Error", str(e)))
        summary_counts["lint_err"] += 1

# --- Generate Markdown report ---
report_file = os.path.join(project_root, "check_report.md")
with open(report_file, "w", encoding="utf-8") as f:
    f.write(f"# 📝 Python Project Lint Report (flake8)\n")
    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # Lint table
    f.write("## 🔍 Lint Results\n\n")
    f.write("| File | Status | Notes |\n|------|--------|-------|\n")
    for file, status, notes in lint_results:
        notes_clean = notes.replace("\n", "<br>")  # preserve line breaks in Markdown
        f.write(f"| `{file}` | {status} | {notes_clean} |\n")
    f.write("\n")

    # Summary
    f.write("## 📊 Summary\n\n")
    f.write("| Metric | Count |\n|--------|-------|\n")
    f.write(f"| ✅ OK          | {summary_counts['lint_ok']} |\n")
    f.write(f"| ⚠️ Issues      | {summary_counts['lint_err']} |\n")

print(f"\n✅ Done! Markdown report saved to {report_file}")
