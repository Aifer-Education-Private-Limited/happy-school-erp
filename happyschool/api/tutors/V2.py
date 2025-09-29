import frappe
from datetime import datetime
from frappe import _
from frappe.utils import nowdate, now_datetime
import json


@frappe.whitelist(allow_guest=True)
def add_feedback():

    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        tutor_id = data.get("tutor_id")
        rating = data.get("rating")
        review = data.get("review")

        if not student_id or not tutor_id or not rating:
            frappe.local.response.update({
                "success": False,
                "message": "student_id, tutor_id and rating are required"
            })
            return

        # ---- Validate Student exists ----
        if not frappe.db.exists("HS Students", student_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Student {student_id} not found"
            })
            return

        # ---- Validate Tutor exists ----
        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        # ---- Validate tutor-student mapping in ----
        if not frappe.db.exists("User Courses", {"tutor_id": tutor_id, "student_id": student_id}):
            frappe.local.response.update({
                "success": False,
                "message": f"Student {student_id} is not assigned to Tutor {tutor_id}"
            })
            return

        # ---- Save Feedback ----
        feedback_doc = frappe.get_doc({
            "doctype": "Feedback",
            "student_id": student_id,
            "tutor_id": tutor_id,
            "rating": rating,
            "review": review
        })
        feedback_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        # ---- Response ----
        frappe.local.response.update({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback": {
                "feedback_id": feedback_doc.name,
                "student_id": student_id,
                "tutor_id": tutor_id,
                "rating": rating,
                "review": review
            }
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "add_feedback API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })







@frappe.whitelist(allow_guest=True)
def get_student_materials():
    """
    Fetch student materials, validate course and session, and return structured material data.
    Request body:
      
    """
    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        course_id = data.get("course_id")
        
        if not frappe.db.exists("HS Students", student_id):
            frappe.local.response.update({
                "success": False,
                "message": f"stud {student_id} not found"
            })

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

        # Dictionary to group materials by topic, subtopic, and course
        topic_dict = {}

        for material in materials:
            session_id = material.session_id

            # ---- Fetch Live Classroom data using session_id ----
            live_classroom = frappe.get_all(
                "Live Classroom",
                filters={"name": session_id}, 
                fields=["course_id"]
            )

            if live_classroom and live_classroom[0].course_id == course_id:
                # Group by topic and subtopic
                if material.topic not in topic_dict:
                    topic_dict[material.topic] = {}

                if material.subtopic not in topic_dict[material.topic]:
                    topic_dict[material.topic][material.subtopic] = []

                # Add the material to the corresponding subtopic
                material_data = {
                    "material_name": material.material_name,
                    "tutor_id": material.tutor_id,
                    "subject": material.subject,
                    "topic": material.topic,
                    "subtopic": material.subtopic,
                    "files": material.files,  # Assuming files are linked correctly in the material doctype
                    "submitted_date": material.submitted_date,
                    "session_id": material.session_id,
                    "student_id": material.student_id
                }

                # Append this material to the subtopic's data list
                topic_dict[material.topic][material.subtopic].append(material_data)

        # Structure the response data based on topic_dict
        for topic, subtopics in topic_dict.items():
            subject_data = {
                "topic": topic,
                "subTopic": []
            }

            for subtopic, materials in subtopics.items():
                subtopic_data = {
                    "title": subtopic,
                    "data": materials  # List all materials under this subtopic
                }

                subject_data["subTopic"].append(subtopic_data)

            # Add the subject data to courses data
            courses_data.append(subject_data)

        # Return the structured course and material data
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
def parent_account_delete():

    try:
        data = frappe.local.form_dict
        parent_id = data.get("parent_id")

        if not parent_id:
            frappe.local.response.update({
                "success": False,
                "message": "parent ID is required"
            })
            return

        if not frappe.db.exists("Parents", parent_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Parent {parent_id} not found"
            })
            return

        current_status = frappe.db.get_value("Parents", parent_id, "type")
        if current_status == "Unlink":
            frappe.local.response.update({
                "success": False,
                "message": f"parent {parent_id} account is already deactivated"
            })
            return

        # Update tutor status to "Unlink"
        frappe.db.set_value("Parents", parent_id, "type", "Unlink")
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": f"Parent {parent_id} account unlinked successfully",
            "tutor_id": parent_id,
            "status": "Unlink"
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Parent_account_delete API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })





@frappe.whitelist(allow_guest=True)
def get_tests_by_course(student_id=None):
    try:
        if not student_id:
            frappe.local.response.update({
                "success": False,
                "error": "student_id is required",
                "tests": []
            })
            return

        # Step 1: Fetch student's active courses
        user_courses = frappe.get_all(
            "User Courses",
            filters={"student_id": student_id, "is_active": "Active"},
            fields=["course_id"]
        )
        course_ids = [uc.course_id for uc in user_courses if uc.course_id]

        if not course_ids:
            frappe.local.response.update({
                "success": True,
                "message": "No active courses assigned to this student",
                "tests": []
            })
            return

        assigned_tests = frappe.get_all(
            "HS Student Tests",
            filters={"student_id": student_id},
            fields=["test_id"]
        )
        assigned_test_ids = {a.test_id for a in assigned_tests if a.test_id}

        tests = frappe.db.sql("""
            SELECT
                name AS test_id,
                title,
                type,
                topic,
                question_set_id,
                question_batch_id,
                total_questions,
                duration,
                general_instruction,
                valid_from,
                valid_to,
                correct_answer_mark,
                wrong_answer_mark,
                uploaded_time,
                is_active,
                is_paid,
                is_free,
                is_result_published,
                is_response_sheet_needed,
                course_id
            FROM `tabTests`
            WHERE course_id IN %(course_ids)s
              AND is_active = 1
        """, {"course_ids": tuple(course_ids)}, as_dict=True)

        unassigned_tests = [t for t in tests if t.test_id not in assigned_test_ids]

        # Step 5: Build response
        test_data = []
        for test in unassigned_tests:
            test_data.append({
                "test_id": test.get("test_id"),
                "title": test.get("title"),
                "type": test.get("type"),
                "question_set_id": test.get("question_set_id"),
                "question_batch_id": test.get("question_batch_id"),
                "total_questions": test.get("total_questions"),
                "duration": test.get("duration"),
                "topic": test.get("topic"),
                "general_instruction": test.get("general_instruction"),
                "valid_from": test.get("valid_from"),
                "valid_to": test.get("valid_to"),
                "correct_answer_mark": test.get("correct_answer_mark"),
                "wrong_answer_mark": test.get("wrong_answer_mark"),
                "uploaded_time": test.get("uploaded_time"),
                "is_active": test.get("is_active"),
                "is_paid": test.get("is_paid"),
                "is_free": test.get("is_free"),
                "is_result_published": test.get("is_result_published"),
                "is_response_sheet_needed": test.get("is_response_sheet_needed"),
                "course_id": test.get("course_id")
            })

        frappe.local.response.update({
            "success": True,
            "message": "success",
            "tests": test_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_tests_by_course API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "tests": []
        })




@frappe.whitelist(allow_guest=True)
def assign_test_to_student():
    try:
        # Fetch data from the request body
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        test_id = data.get("test_id")
        tutor_id = data.get("tutor_id")
        
        # Validate required parameters
        if not student_id or not test_id or not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": _("Student ID, Test ID, and Tutor ID are required")
            })
            return
        
        # Check if the student is already assigned to the test
        existing_record = frappe.db.exists("HS Student Tests", {
            "student_id": student_id,
            "test_id": test_id
        })
        
        if existing_record:
            frappe.local.response.update({
                "success": False,
                "message": _("The student is already assigned to this test.")
            })
            return

        # Create a new HS Student Tests record
        new_record = frappe.get_doc({
            "doctype": "HS Student Tests",
            "student_id": student_id,
            "test_id": test_id,
            "tutor_id": tutor_id
        })

        new_record.insert(ignore_permissions=True)

        frappe.local.response.update({
            "success": True,
            "message": _("Student has been successfully assigned to the test."),
            "data": {
                "student_id": student_id,
                "test_id": test_id,
                "tutor_id": tutor_id
            }
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "assign_student_to_test API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "data": {}
        })






@frappe.whitelist(allow_guest=True)
def unassign_student_from_test():
    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        test_id = data.get("test_id")

        if not student_id or not test_id:
            frappe.local.response.update({
                "success": False,
                "message": _("Student ID and Test ID are required")
            })
            return

        existing_record = frappe.db.exists("HS Student Tests", {
            "student_id": student_id,
            "test_id": test_id
        })
        
        if not existing_record:
            frappe.local.response.update({
                "success": False,
                "message": _("The student is not assigned to this test.")
            })
            return

        # Delete the assignment record from HS Student Tests
        frappe.db.delete("HS Student Tests", {
            "student_id": student_id,
            "test_id": test_id
        })

        frappe.local.response.update({
            "success": True,
            "message": _("Student has been successfully unassigned from the test."),
            "data": {
                "student_id": student_id,
                "test_id": test_id
            }
        })

    except Exception as e:
        # Handle errors and log them
        frappe.log_error(frappe.get_traceback(), "unassign_student_from_test API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "data": {}
        })






@frappe.whitelist(allow_guest=True)
def get_tutor_assigned_student_tests():
    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        tutor_id = data.get("tutor_id")

        # Validate inputs
        if not student_id or not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": _("student_id and tutor_id are required"),
                "tests": []
            })
            return

        # Step 1: Check HS Student Tests for matching records
        student_tests = frappe.db.sql(
            """
            SELECT test_id 
            FROM `tabHS Student Tests`
            WHERE student_id = %s AND tutor_id = %s
            """,
            (student_id, tutor_id),
            as_dict=True
        )

        if not student_tests:
            frappe.local.response.update({
                "success": True,
                "message": _("No tests assigned for this student and tutor"),
                "tests": []
            })
            return

        # Extract test_ids
        test_ids = [st.test_id for st in student_tests]

        # Step 2: Fetch test details from Tests doctype
        tests_data = frappe.db.sql(
            """
            SELECT
                name AS test_id,
                course_id,
                title,
                type,
                question_batch_id,
                question_set_id,
                topic,
                total_questions,
                valid_from,
                valid_to,
                duration,
                general_instruction,
                is_active,
                is_paid,
                is_free,
                is_result_published,
                is_response_sheet_needed,
                correct_answer_mark,
                wrong_answer_mark,
                uploaded_time
            FROM `tabTests`
            WHERE name IN (%s)
            """ % (", ".join(["%s"] * len(test_ids))),
            tuple(test_ids),
            as_dict=True
        )

        # Step 3: Check Test User History for attended tests
        history_map = {}
        if test_ids:
            histories = frappe.db.sql(
                """
                SELECT name AS history_id, test_id
                FROM `tabTest User History`
                WHERE student_id = %s AND test_id IN (%s)
                """ % ("%s", ", ".join(["%s"] * len(test_ids))),
                tuple([student_id] + test_ids),
                as_dict=True
            )
            for h in histories:
                history_map[h.test_id] = h.history_id

        for test in tests_data:
            test["history_id"] = history_map.get(test["test_id"]) 

        frappe.local.response.update({
            "success": True,
            "message": _("Tutor assigned tests fetched successfully"),
            "tests": tests_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_tutor_assigned_student_tests API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "tests": []
        })

