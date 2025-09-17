

import frappe
import json
from datetime import datetime

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

        # Dictionary to group materials by topic, subtopic, and course
        topic_dict = {}

        for material in materials:
            session_id = material.session_id

            live_classroom = frappe.get_all(
                "Live Classroom",
                filters={"name": session_id},  # Correct field to refer to Live Classroom session
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
                    "files": material.files,  # Assuming files are linked correctly in the material doctype
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



