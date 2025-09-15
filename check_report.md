# 📝 Python Project Lint Report (flake8)
Generated on: 2025-09-16 06:23:16

## 🔍 Lint Results

| File | Status | Notes |
|------|--------|-------|
| `app.py` | ✅ OK |  |
| `check_project.py` | ✅ OK |  |
| `config\settings.py` | ✅ OK |  |
| `controllers\admin_controller.py` | ✅ OK |  |
| `controllers\dashboard_controller.py` | ✅ OK |  |
| `controllers\faculty_controller.py` | ✅ OK |  |
| `controllers\login_controller.py` | ✅ OK |  |
| `controllers\registrar_controller.py` | ✅ OK |  |
| `controllers\student_controller.py` | ✅ OK |  |
| `controllers\admin\user_management_controller.py` | ✅ OK |  |
| `controllers\registrar\class_scheduler_manager.py` | ✅ OK |  |
| `controllers\registrar\curriculum_manager.py` | ✅ OK |  |
| `controllers\registrar\enrollment_approval_manager.py` | ✅ OK |  |
| `controllers\registrar\enrollment_manager.py` | ✅ OK |  |
| `controllers\registrar\grade_manager.py` | ✅ OK |  |
| `controllers\registrar\prospectus_manager.py` | ✅ OK |  |
| `controllers\registrar\report_manager.py` | ✅ OK |  |
| `controllers\registrar\semester_manager.py` | ✅ OK |  |
| `controllers\registrar\student_records_manager.py` | ✅ OK |  |
| `controllers\registrar\subjects_manager.py` | ✅ OK |  |
| `controllers\reports\course_and_curriculum_report.py` | ✅ OK |  |
| `controllers\reports\registrar_main_report.py` | ✅ OK |  |
| `controllers\reports\semester_and_academic_year_report.py` | ✅ OK |  |
| `controllers\reports\student_demographics_report.py` | ✅ OK |  |
| `controllers\reports\student_performance_report.py` | ✅ OK |  |
| `controllers\reports\subject_and_teacher_report.py` | ✅ OK |  |
| `helpers\cache_helper.py` | ✅ OK |  |
| `helpers\data_helper.py` | ⚠️ Issues | C:\MIT261-BSBA\helpers\data_helper.py:456:21: F821 undefined name 'generate_password_hash'<br>C:\MIT261-BSBA\helpers\data_helper.py:526:21: F821 undefined name 'generate_password_hash' |
| `helpers\data_helper_extended.py` | ✅ OK |  |
| `helpers\faculty_helper.py` | ✅ OK |  |
| `helpers\registrar_main_report_helper.py` | ⚠️ Issues | C:\MIT261-BSBA\helpers\registrar_main_report_helper.py:361:22: F841 local variable 'results' is assigned to but never used |
| `helpers\registration_helper.py` | ✅ OK |  |
| `helpers\report_helper.py` | ✅ OK |  |
| `iscripts\clean_overshoot_grades.py` | ✅ OK |  |
| `iscripts\curriculum_add.py` | ✅ OK |  |
| `iscripts\curriculum_fix.py` | ✅ OK |  |
| `iscripts\curriculum_subject_migration.py` | ✅ OK |  |
| `iscripts\curriculum_update.py` | ✅ OK |  |
| `iscripts\find_student_fuzz.py` | ✅ OK |  |
| `iscripts\generate_grades_entries.py` | ✅ OK |  |
| `iscripts\grades_collection_add_status_sub_collection.py` | ✅ OK |  |
| `iscripts\students_populate_100.py` | ✅ OK |  |
| `iscripts\useraccount_add_fullname.py` | ✅ OK |  |
| `staging\app.py` | ⚠️ Issues | C:\MIT261-BSBA\staging\app.py:6:17: F811 redefinition of unused 'st' from line 2 |
| `staging\prospectus_data_generator\prospectus_data_generator.py` | ✅ OK |  |

## 📊 Summary

| Metric | Count |
|--------|-------|
| ✅ OK          | 42 |
| ⚠️ Issues      | 3 |
