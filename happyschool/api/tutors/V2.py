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

        # ---- Fetch materials related to the student ----
        materials = frappe.get_all(
            "Materials",
            filters={"student_id": student_id},
            fields=["name", "subject", "topic", "subtopic", "material_name", "session_id"]
        )

        courses_data = []

        for material in materials:
            session_id = material.session_id

            # ---- Fetch Live Classroom data using session_id ----
            live_classroom = frappe.get_all(
                "Live Classroom",
                filters={"name": session_id},  # Correct field to refer to Live Classroom session
                fields=["course_id"]
            )

            if live_classroom and live_classroom[0].course_id == course_id:
                # ---- Fetch course details from the Courses table ----
                course_details = frappe.get_doc("Courses", course_id)

                # Add course data
                subject_data = {
                    "subject": material.subject,  # Use material subject here
                    "topics": [],  # Initialize topics list
                }

                # ---- Add topic and subtopics under the course ----
                topic_data = {
                    "topic_name": material.topic,  # Directly use topic from materials
                    "subtopics": []
                }

                # ---- Add subtopics under the topic ----
                subtopic_data = {
                    "subtopic_name": material.subtopic,  # Directly use subtopic from materials
                    "data": []  # Materials will be added here
                }

                # ---- Add materials to the subtopic ----
                material_data = {
                    "material_name": material.material_name,
                    "student_id": student_id,
                    "grade": "A",  # Example: Get grade from the student courses data
                    "status": "Active",  # Example: Get student status
                    "course_details": {
                        "course_id": course_details.course_id,
                        "title": course_details.title,
                        "subject": course_details.subject,
                        "status": course_details.status,
                        "language_of_instruction": course_details.language_of_instruction,
                        "description": course_details.description,
                        "details": course_details.details,
                        "ask_doubt_number": course_details.ask_doubt_number,
                        "expiry_date": course_details.expiry_date,
                        "label": course_details.label,
                        "image": course_details.image
                    }
                }

                # Add material data to the subtopic
                subtopic_data["data"].append(material_data)

                # Add subtopic data to topic data
                topic_data["subtopics"].append(subtopic_data)

                # Add topic data to subject data
                subject_data["topics"].append(topic_data)

                # Add subject data to the courses list
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
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Parents", parent_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {parent_id} not found"
            })
            return

        current_status = frappe.db.get_value("Parents", parent_id, "type")
        if current_status == "Unlink":
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {parent_id} account is already deactivated"
            })
            return

        # Update tutor status to "Unlink"
        frappe.db.set_value("Tutors", parent_id, "type", "Unlink")
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": f"Tutor {parent_id} account unlinked successfully",
            "tutor_id": parent_id,
            "status": "Unlink"
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "tutor_account_delete API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
