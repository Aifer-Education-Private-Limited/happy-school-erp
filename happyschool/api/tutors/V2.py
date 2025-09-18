import frappe
import json
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def add_feedback():
    """
    Add feedback from a student.
    Request body:
        {
            "student_id": "ST001",
            "tutor_id": "TUT-0001",
            "rating": 4.5,
            "review": "Great tutor!"
        }
    """
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
        if not frappe.db.exists("Students", student_id):
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

        # ---- Validate tutor-student mapping in Students List ----
        if not frappe.db.exists("Students List", {"tutor_id": tutor_id, "student_id": student_id}):
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




import frappe
import json
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def get_student_materials():
    """
    Fetch student materials, validate course and session, and return structured material data.
    Request body:
        {
            "student_id": "ST001", 
            "course_id": "COURSE-001"
        }
    """
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

        # Dictionary to group materials by topic, subtopic, and course
        topic_dict = {}

        for material in materials:
            session_id = material.session_id

            # ---- Fetch Live Classroom data using session_id ----
            live_classroom = frappe.get_all(
                "Live Classroom",
                filters={"name": session_id},  # Correct field to refer to Live Classroom session
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
