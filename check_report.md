# 📝 Python Project Lint + Runtime Report
Generated on: 2025-09-16 08:29:39

## 🔍 Results

| File | Lint | Lint Notes | Runtime | Runtime Notes |
|------|------|------------|---------|---------------|
| `app.py` | ✅ Lint OK |  | ❌ Runtime Crash | Command '['python', 'F:\\dev_2024\\MIT261-BSBA\\app.py']' timed out after 10 seconds |
| `check_project.py` | ✅ Lint OK |  | ❌ Runtime Crash | Command '['python', 'F:\\dev_2024\\MIT261-BSBA\\check_project.py']' timed out after 10 seconds |
| `config\settings.py` | ✅ Lint OK |  | ✅ Run OK |  |
| `controllers\admin_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\dashboard_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\faculty_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\login_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\student_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\admin\user_management_controller.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\class_scheduler_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\curriculum_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\enrollment_approval_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\enrollment_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\grade_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\prospectus_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\report_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\semester_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\student_records_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\registrar\subjects_manager.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\course_and_curriculum_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\registrar_main_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\semester_and_academic_year_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\student_demographics_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\student_performance_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `controllers\reports\subject_and_teacher_report.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `helpers\cache_helper.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `helpers\data_helper.py` | ⚠️ Lint Issues | F:\dev_2024\MIT261-BSBA\helpers\data_helper.py:456:21: F821 undefined name 'generate_password_hash'<br>F:\dev_2024\MIT261-BSBA\helpers\data_helper.py:526:21: F821 undefined name 'generate_password_hash' | ⏭️ Skipped | Not run (module-only file) |
| `helpers\data_helper_extended.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `helpers\faculty_helper.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `helpers\registrar_main_report_helper.py` | ⚠️ Lint Issues | F:\dev_2024\MIT261-BSBA\helpers\registrar_main_report_helper.py:361:22: F841 local variable 'results' is assigned to but never used | ⏭️ Skipped | Not run (module-only file) |
| `helpers\registration_helper.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `helpers\report_helper.py` | ✅ Lint OK |  | ⏭️ Skipped | Not run (module-only file) |
| `iscripts\clean_overshoot_grades.py` | ✅ Lint OK |  | ✅ Run OK | Updated 0 grade records. |
| `iscripts\curriculum_add.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\iscripts\curriculum_add.py", line 4, in <module><br>    from config.settings import MONGODB_URI, DB_NAME<br>ModuleNotFoundError: No module named 'config' |
| `iscripts\curriculum_fix.py` | ✅ Lint OK |  | ✅ Run OK |  |
| `iscripts\curriculum_subject_migration.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\iscripts\curriculum_subject_migration.py", line 2, in <module><br>    from config.settings import MONGODB_URI<br>ModuleNotFoundError: No module named 'config' |
| `iscripts\curriculum_update.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\iscripts\curriculum_update.py", line 4, in <module><br>    from config.settings import MONGODB_URI, DB_NAME<br>ModuleNotFoundError: No module named 'config' |
| `iscripts\find_student_fuzz.py` | ✅ Lint OK |  | ✅ Run OK |  |
| `iscripts\generate_grades_entries.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\iscripts\generate_grades_entries.py", line 70, in <module><br>    raise ValueError(f"❌ Semester not found in lookup: {key}")<br>ValueError: ❌ Semester not found in lookup: ('FirstSem', 2026) |
| `iscripts\grades_collection_add_status_sub_collection.py` | ✅ Lint OK |  | ❌ Runtime Crash | Command '['python', 'F:\\dev_2024\\MIT261-BSBA\\iscripts\\grades_collection_add_status_sub_collection.py']' timed out after 10 seconds |
| `iscripts\students_populate_100.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\iscripts\students_populate_100.py", line 5, in <module><br>    from config.settings import MONGODB_URI, DB_NAME<br>ModuleNotFoundError: No module named 'config' |
| `iscripts\useraccount_add_fullname.py` | ✅ Lint OK |  | ❌ Runtime Crash | Command '['python', 'F:\\dev_2024\\MIT261-BSBA\\iscripts\\useraccount_add_fullname.py']' timed out after 10 seconds |
| `staging\app.py` | ✅ Lint OK |  | ❌ Runtime Error | Traceback (most recent call last):<br>  File "F:\dev_2024\MIT261-BSBA\staging\app.py", line 4, in <module><br>    import registrar_report_hepler as r<br>ModuleNotFoundError: No module named 'registrar_report_hepler' |
| `staging\prospectus_data_generator\prospectus_data_generator.py` | ✅ Lint OK |  | ❌ Runtime Crash | Command '['python', 'F:\\dev_2024\\MIT261-BSBA\\staging\\prospectus_data_generator\\prospectus_data_generator.py']' timed out after 10 seconds |

## 📊 Summary

| Metric        | Count |
|---------------|-------|
| ✅ Lint OK     | 43 |
| ⚠️ Lint Issues | 2 |
| ✅ Run OK      | 4 |
| ❌ Run Errors  | 11 |
| ⏭️ Run Skipped | 30 |
