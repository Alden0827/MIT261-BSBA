# 📝 Python Project Lint Report (flake8)
Generated on: 2025-09-16 04:06:21

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
| `controllers\student_controller.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\student_controller.py:143:5: E306 expected 1 blank line before a nested definition, found 0 |
| `controllers\admin\user_management_controller.py` | ✅ OK |  |
| `controllers\registrar\class_scheduler_manager.py` | ✅ OK |  |
| `controllers\registrar\curriculum_manager.py` | ✅ OK |  |
| `controllers\registrar\enrollment_approval_manager.py` | ✅ OK |  |
| `controllers\registrar\enrollment_manager.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\registrar\enrollment_manager.py:50:9: F841 local variable 'selected_course' is assigned to but never used<br>C:\MIT261-BSBA\controllers\registrar\enrollment_manager.py:115:17: W503 line break before binary operator<br>C:\MIT261-BSBA\controllers\registrar\enrollment_manager.py:116:17: W503 line break before binary operator |
| `controllers\registrar\grade_manager.py` | ✅ OK |  |
| `controllers\registrar\prospectus_manager.py` | ✅ OK |  |
| `controllers\registrar\report_manager.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\registrar\report_manager.py:59:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:65:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:74:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:80:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:83:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:96:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:99:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:152:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:157:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:158:22: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:162:14: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:164:17: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:165:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:168:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:185:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:194:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\report_manager.py:196:9: F821 undefined name 'st' |
| `controllers\registrar\semester_manager.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\registrar\semester_manager.py:5:2: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:33:2: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:35:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:36:14: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:37:15: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:41:8: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:46:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:47:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:49:2: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:51:5: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:52:8: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:54:9: F821 undefined name 'st'<br>C:\MIT261-BSBA\controllers\registrar\semester_manager.py:55:9: F821 undefined name 'st' |
| `controllers\registrar\student_records_manager.py` | ✅ OK |  |
| `controllers\registrar\subjects_manager.py` | ✅ OK |  |
| `controllers\reports\course_and_curriculum_report.py` | ✅ OK |  |
| `controllers\reports\registrar_main_report.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\reports\registrar_main_report.py:8:1: F811 redefinition of unused 'pd' from line 3<br>C:\MIT261-BSBA\controllers\reports\registrar_main_report.py:238:13: W503 line break before binary operator<br>C:\MIT261-BSBA\controllers\reports\registrar_main_report.py:239:13: W503 line break before binary operator |
| `controllers\reports\semester_and_academic_year_report.py` | ✅ OK |  |
| `controllers\reports\student_demographics_report.py` | ✅ OK |  |
| `controllers\reports\student_performance_report.py` | ✅ OK |  |
| `controllers\reports\subject_and_teacher_report.py` | ⚠️ Issues | C:\MIT261-BSBA\controllers\reports\subject_and_teacher_report.py:224:30: E203 whitespace before ':'<br>C:\MIT261-BSBA\controllers\reports\subject_and_teacher_report.py:225:30: E203 whitespace before ':' |
| `helpers\cache_helper.py` | ✅ OK |  |
| `helpers\data_helper.py` | ⚠️ Issues | C:\MIT261-BSBA\helpers\data_helper.py:160:5: F841 local variable 'students_col' is assigned to but never used<br>C:\MIT261-BSBA\helpers\data_helper.py:528:21: F821 undefined name 'generate_password_hash'<br>C:\MIT261-BSBA\helpers\data_helper.py:598:21: F821 undefined name 'generate_password_hash' |
| `helpers\data_helper_extended.py` | ✅ OK |  |
| `helpers\faculty_helper.py` | ✅ OK |  |
| `helpers\registrar_main_report_helper.py` | ⚠️ Issues | C:\MIT261-BSBA\helpers\registrar_main_report_helper.py:330:11: E121 continuation line under-indented for hanging indent<br>C:\MIT261-BSBA\helpers\registrar_main_report_helper.py:331:11: E131 continuation line unaligned for hanging indent<br>C:\MIT261-BSBA\helpers\registrar_main_report_helper.py:361:22: F841 local variable 'results' is assigned to but never used<br>C:\MIT261-BSBA\helpers\registrar_main_report_helper.py:542:5: E306 expected 1 blank line before a nested definition, found 0 |
| `helpers\registration_helper.py` | ⚠️ Issues | C:\MIT261-BSBA\helpers\registration_helper.py:24:11: F821 undefined name 'data' |
| `helpers\report_helper.py` | ✅ OK |  |
| `iscripts\clean_overshoot_grades.py` | ✅ OK |  |
| `iscripts\curriculum_add.py` | ⚠️ Issues | C:\MIT261-BSBA\iscripts\curriculum_add.py:20:6: E121 continuation line under-indented for hanging indent |
| `iscripts\curriculum_fix.py` | ⚠️ Issues | C:\MIT261-BSBA\iscripts\curriculum_fix.py:6:2: E121 continuation line under-indented for hanging indent |
| `iscripts\curriculum_subject_migration.py` | ✅ OK |  |
| `iscripts\curriculum_update.py` | ⚠️ Issues | C:\MIT261-BSBA\iscripts\curriculum_update.py:23:2: E121 continuation line under-indented for hanging indent |
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
| ✅ OK          | 32 |
| ⚠️ Issues      | 13 |
