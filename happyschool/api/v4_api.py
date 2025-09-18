

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

