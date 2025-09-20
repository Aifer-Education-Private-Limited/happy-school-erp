

import frappe
import json
from datetime import datetime
from frappe.utils import now_datetime, now


@frappe.whitelist(allow_guest=True)
def get_student_materials():

    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        course_id = data.get("course_id")

        if not student_id or not course_id:
            return {"success": False, "error": "Student ID and Course ID are required"}

        # ---- Check if student is enrolled in the course ----
        is_enrolled = frappe.db.exists("User Courses", {"student_id": student_id, "course_id": course_id})
        if not is_enrolled:
            return {"success": False, "error": f"Student {student_id} is not enrolled in Course {course_id}"}

        materials = frappe.get_all(
            "Materials",
            filters={"student_id": student_id},
            fields=["name", "subject", "topic", "subtopic", "material_name", "session_id", "tutor_id", "submitted_date", "files","student_id"]
        )

        courses_data = []

        topic_dict = {}

        for material in materials:
            session_id = material.session_id

            live_classroom = frappe.get_all(
                "Live Classroom",
                filters={"name": session_id},  
                fields=["course_id"]
            )

            if live_classroom and live_classroom[0].course_id == course_id:
                if material.topic not in topic_dict:
                    topic_dict[material.topic] = {}

                if material.subtopic not in topic_dict[material.topic]:
                    topic_dict[material.topic][material.subtopic] = []

                material_data = {
                    "material_name": material.material_name,
                    "tutor_id": material.tutor_id,
                    "subject": material.subject,
                    "topic": material.topic,
                    "subtopic": material.subtopic,
                    "files": material.files,  
                    "submitted_date": material.submitted_date,
                    "session_id": material.session_id,
                    "student_id": material.student_id
                }

                topic_dict[material.topic][material.subtopic].append(material_data)

        for topic, subtopics in topic_dict.items():
            subject_data = {
                "topic": topic,
                "subTopic": []
            }

            for subtopic, materials in subtopics.items():
                subtopic_data = {
                    "title": subtopic,
                    "data": materials  
                }

                subject_data["subTopic"].append(subtopic_data)

            courses_data.append(subject_data)

        frappe.local.response.update({
            "success": True,
            "student_id": student_id,
            "courses": courses_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_student_materials API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })



@frappe.whitelist(allow_guest=True)
def get_announcements_by_student_or_parent():
    """
    Fetch announcements based on student_id or parent_id.
    If student_id is passed, show audience_type "Student" and "Both" and also fetch student-related events.
    If parent_id is passed, show audience_type "Parent" and "Both".
    Request body:
        {
            "student_id": "ST001", 
            "parent_id": "PR001"
        }
    """
    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        parent_id = data.get("parent_id")

        if not student_id and not parent_id:
            frappe.local.response.update({
                "success": False,
                "message": "Either Student ID or Parent ID is required"
            })
            return

        filters = {}

        # Filters for announcements
        if student_id:
            filters["audience_type"] = ["in", ["Student", "Both"]]
            filters["student_id"] = student_id

        if parent_id:
            filters["audience_type"] = ["in", ["Parent", "Both"]]
            filters["parent_id"] = parent_id

        # Fetch announcements
        announcements = frappe.get_all(
            "Announcement",
            filters=filters,
            fields=["name", "title", "description", "category", "status", "attachment", "creation"]
        )

        if not announcements:
            frappe.local.response.update({
                "success": False,
                "message": "No announcements found for the provided ID(s)"
            })
            return

        # ---- Fetch student events if student_id is provided ----
        events_data = []
        if student_id:
            events = frappe.get_all(
                "Events",
                filters={"student_id": student_id},
                fields=["event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
            )
            for event in events:
                events_data.append({
                    "event_date": event.event_date,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "meeting_link": event.meeting_link,
                    "expiry_date": event.expiry_date
                })

        # Return the list of announcements and events
        frappe.local.response.update({
            "success": True,
            "announcements": announcements,
            "events": events_data if student_id else []  # Include events only if student_id is present
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_announcements_by_student_or_parent API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


import frappe
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def get_test(course_id=None, type=None, student_id=None):
    try:
        if not course_id or not type:
            frappe.local.response.update({
                "success": False,
                "message": "course_id and type are required",
                "data": {}
            })
            return

        # ------------------------------
        # Get Active Tests
        # ------------------------------
        sort_order = "asc"
        if type in ["dt", "mmt"]:
            sort_order = "desc"

        active_tests = frappe.db.sql(
            """
            SELECT
                name as id,
                title,
                type,
                topic,
                is_paid,
                total_questions,
                valid_from,
                valid_to,
                duration,
                general_instruction,
                question_batch_id,
                is_free,
                correct_answer_mark,
                wrong_answer_mark,
                question_attend_limit,
                question_set_id
            FROM `tabTests`
            WHERE type = %s
              AND course_id LIKE %s
              AND is_active = 1
            ORDER BY creation {sort}
            """.format(sort=sort_order),
            (type, f"%{course_id}%"),
            as_dict=True
        )

        for t in active_tests:
            t["set_id"] = t.pop("question_set_id", None)
            if not t.get("correct_answer_mark"):
                t["correct_answer_mark"] = 1
            if not t.get("wrong_answer_mark"):
                t["wrong_answer_mark"] = 0

        # Get Attended Tests
        attended_tests = []
        if student_id:
            attended_tests = frappe.db.sql(
                """
                SELECT
                    tests.name as id,
                    tests.title,
                    tests.type,
                    tests.topic,
                    tests.total_questions,
                    tests.valid_from,
                    tests.valid_to,
                    tests.duration,
                    tests.general_instruction,
                    tuh.name as history_id,
                    tuh.attended_date,
                    tuh.total_time,
                    tuh.marks,
                    tuh.attempt_count,
                    tests.is_result_published,
                    tests.question_set_id,
                    tests.correct_answer_mark,
                    tests.wrong_answer_mark,
                    tests.is_response_sheet_needed
                FROM `tabTest User History` tuh
                INNER JOIN `tabTests` tests
                    ON tuh.test_id = tests.name
                WHERE tuh.student_id = %s
                  AND tests.type = %s
                  AND tests.course_id LIKE %s
                """,
                (student_id, type, f"%{course_id}%"),
                as_dict=True
            )

            for t in attended_tests:
                t["is_response_sheet_needed"] = True if t.get("is_response_sheet_needed") else False

        frappe.local.response.update({
            "success": True,
            "message": "Success",
            "data": {
                "active_tests": active_tests,
                "attended_tests": attended_tests,
                "server_time": now_datetime()
            }
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_test API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "data": {}
        })




@frappe.whitelist(allow_guest=True)
def test_complete():
    """
    One-shot submit API (no SQS, no Set History writes):
      - Upsert Test User History (attempt_count logic)
      - Upsert Test User Answers (set_id nullable)
      - Upsert Test User History Topic (set_id nullable)

    """
    try:
        payload = dict(frappe.local.form_dict or {})
        if not payload:
            try:
                if hasattr(frappe, "request") and frappe.request and frappe.request.data:
                    payload = json.loads(frappe.request.data)
            except Exception:
                pass

        test_id     = payload.get("test_id")
        student_id  = payload.get("student_id") or payload.get("uid") 
        attended_at = payload.get("date") or now_datetime()
        total_time  = payload.get("total_time")
        marks       = payload.get("marks")
        test_sets   = payload.get("test_sets") 

        if not test_id or not student_id:
            frappe.local.response.update({"success": False, "message": "test_id and student_id are required", "data": {}})
            return

        # -------- helpers ----------
        def deep_loads(obj):
            """Handle double/triple-encoded JSON until it becomes dict/list."""
            cur = obj
            for _ in range(5):
                if isinstance(cur, (dict, list)):
                    return cur
                if isinstance(cur, str):
                    cur = json.loads(cur)
                else:
                    break
            return cur

        def is_nullish(v):
            return v in (None, "null", "None", "", 0, "0")

        hist = frappe.db.sql("""
            SELECT name, attempt_count
            FROM `tabTest User History`
            WHERE test_id=%s AND student_id=%s
        """, (test_id, student_id), as_dict=True)

        if not hist:
            hdoc = frappe.get_doc({
                "doctype": "Test User History",
                "test_id": test_id,
                "student_id": student_id,
                "attended_date": attended_at,
                "total_time": total_time,
                "marks": marks,
                "attempt_count": 1
            })
            hdoc.insert(ignore_permissions=True)
            history_id = hdoc.name
            attempt_count = 1
        else:
            history_id = hist[0].name
            previous = hist[0].attempt_count or 0

            # If answers exist already, this submit increments attempt.
            ans_ct = frappe.db.sql("""
                SELECT COUNT(*) AS c FROM `tabTest User Answers` WHERE history_id=%s
            """, (history_id,), as_dict=True)[0].c
            attempt_count = previous + 1 if int(ans_ct or 0) > 0 else 1

            frappe.db.set_value("Test User History", history_id, {
                "attended_date": attended_at,
                "total_time": total_time,
                "marks": marks,
                "attempt_count": attempt_count
            })

        # -------- parse test_sets (array of JSON strings) ----------
        sets_list = deep_loads(test_sets) if test_sets else []
        # Each element may still be a JSON string → deep_loads again below

        # -------- upserts: answers + topic marks (NO set history) ----------
        for item in sets_list:
            set_obj = deep_loads(item) or {}
            set_id = set_obj.get("set_id")  # may be None/NULL
            answers_blob = set_obj.get("answers")
            topics_blob  = set_obj.get("topic_marks")

            # --- (COMMENTED OUT) Test User Set History ---
            # time_took = set_obj.get("time_took")
            # mark = set_obj.get("mark")
            # # Skipped per your instruction:
            # # _upsert_set_summary(history_id, set_id, time_took, mark)
            # ---------------------------------------------

            # --- answers ---
            if answers_blob:
                answers_list = deep_loads(answers_blob) or []
                for one in answers_list:
                    ans = deep_loads(one) or {}
                    qid = ans.get("question_id")
                    aval = ans.get("answer")

                    if is_nullish(set_id):
                        row = frappe.db.sql("""
                            SELECT name FROM `tabTest User Answers`
                            WHERE history_id=%s AND set_id IS NULL AND question_id=%s
                        """, (history_id, qid), as_dict=True)
                        if row:
                            frappe.db.sql("""UPDATE `tabTest User Answers` SET answer=%s WHERE name=%s""", (aval, row[0].name))
                        else:
                            adoc = frappe.get_doc({
                                "doctype": "Test User Answers",
                                "history_id": history_id,
                                "question_id": qid,
                                "answer": aval
                            })
                            adoc.insert(ignore_permissions=True)
                    else:
                        row = frappe.db.sql("""
                            SELECT name FROM `tabTest User Answers`
                            WHERE history_id=%s AND set_id=%s AND question_id=%s
                        """, (history_id, set_id, qid), as_dict=True)
                        if row:
                            frappe.db.sql("""UPDATE `tabTest User Answers` SET answer=%s WHERE name=%s""", (aval, row[0].name))
                        else:
                            adoc = frappe.get_doc({
                                "doctype": "Test User Answers",
                                "history_id": history_id,
                                "set_id": set_id,
                                "question_id": qid,
                                "answer": aval
                            })
                            adoc.insert(ignore_permissions=True)

            # --- topic marks ---
            if topics_blob:
                topics_list = deep_loads(topics_blob) or []
                for one in topics_list:
                    tm = deep_loads(one) or {}
                    topic = tm.get("topic")
                    mval  = tm.get("mark")

                    if is_nullish(set_id):
                        row = frappe.db.sql("""
                            SELECT name FROM `tabTest User History Topic`
                            WHERE history_id=%s AND set_id IS NULL AND topic=%s
                        """, (history_id, topic), as_dict=True)
                        if row:
                            frappe.db.sql("""UPDATE `tabTest User History Topic` SET mark=%s WHERE name=%s""", (mval, row[0].name))
                        else:
                            tdoc = frappe.get_doc({
                                "doctype": "Test User History Topic",
                                "history_id": history_id,
                                "topic": topic,
                                "mark": mval
                            })
                            tdoc.insert(ignore_permissions=True)
                    else:
                        row = frappe.db.sql("""
                            SELECT name FROM `tabTest User History Topic`
                            WHERE history_id=%s AND set_id=%s AND topic=%s
                        """, (history_id, set_id, topic), as_dict=True)
                        if row:
                            frappe.db.sql("""UPDATE `tabTest User History Topic` SET mark=%s WHERE name=%s""", (mval, row[0].name))
                        else:
                            tdoc = frappe.get_doc({
                                "doctype": "Test User History Topic",
                                "history_id": history_id,
                                "set_id": set_id,
                                "topic": topic,
                                "mark": mval
                            })
                            tdoc.insert(ignore_permissions=True)

        frappe.db.commit()
        frappe.local.response.update({
            "success": True,
            "message": "Test completed & saved successfully",
            "data": {"history_id": history_id, "attempt_count": attempt_count}
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "test_complete API Error")
        frappe.local.response.update({"success": False, "error": str(e), "data": {}})








import frappe, re

BASE_FILE_URL = "https://myfiles.space/user_files/85248_60f241cdfd3eef9a/85248_custom_files/"

def clean_html(value):
    """Remove Quill wrappers & fix file URLs"""
    if not value:
        return ""

    # Remove ql-editor divs
    value = re.sub(r'<div class="ql-editor[^>]*>', '', value)
    value = value.replace("</div>", "")

    # Fix relative /private/files/... → BASE_FILE_URL
    value = re.sub(r'src="\/private\/files\/([^"]+)"',
                   lambda m: f'src="{BASE_FILE_URL}{m.group(1)}"',
                   value)

    return value.strip()

@frappe.whitelist(allow_guest=True)
def get_set_questions(questions_batch_id=None):
    try:
        if not questions_batch_id:
            frappe.local.response.update({
                "success": False,
                "error": "questions_batch_id is required",
                "data": []
            })
            return

        rows = frappe.db.sql(
            """
            SELECT
                name AS id,
                question_number,
                question,
                option_1, option_2, option_3, option_4,
                right_answer,
                explenation,
                topic
            FROM `tabTest Questions`
            WHERE questions_batch_id = %s
            ORDER BY question_number ASC
            """,
            (questions_batch_id,),
            as_dict=True
        )

        formatted = []
        for r in rows:
            formatted.append({
                "id": r.id,
                "question": clean_html(r.question),
                "option_1": clean_html(r.option_1),
                "option_2": clean_html(r.option_2),
                "option_3": clean_html(r.option_3),
                "option_4": clean_html(r.option_4),
                "right_answer": r.right_answer,
                "explenation": clean_html(r.explenation),
                "topic": r.topic,
                "question_no": r.question_number
            })

        frappe.local.response.update({
            "success": True,
            "data": formatted
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_set_questions API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "data": []
        })
