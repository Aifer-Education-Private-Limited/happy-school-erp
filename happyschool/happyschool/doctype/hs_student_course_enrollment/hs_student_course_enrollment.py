# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HSStudentCourseEnrollment(Document):
	pass


@frappe.whitelist()
def get_program_details(program):
    """Fetch project from HS Program List and session_count from User Courses via Courses."""
    # ✅ If your child table program field is linked to HS Program List (Link field), `program` will already be the name (primary key).
    project = frappe.db.get_value("HS Program List", {"name": program}, "project")

    # ✅ Here, if your Courses doctype uses title = program name, this is fine.
    # If instead HS Program List has a course_id field, you should fetch from there.
    course_id = frappe.db.get_value("Courses", {"title": program}, "course_id")

    session_count = 0
    if course_id:
        session_count = frappe.db.get_value("User Courses", {"course_id": course_id}, "session_count") or 0

    return {
        "project": project,
        "session_count": session_count
    }


@frappe.whitelist()
def get_program_enrollment_details(program_enrollment_id):
    """Fetch date from HS Program Enrollment."""
    # ✅ Changed to enrollment_date based on your field name
    date = frappe.db.get_value("HS Program Enrollment", {"name": program_enrollment_id}, "enrollment_date")
    return {"date": date}

@frappe.whitelist()
def get_live_classroom(student_id, course_id):
    """Fetch Live Classroom details by student_id & course_id"""
    frappe.logger().info(f"Searching Live Classroom for student_id={student_id}, course_id={course_id}")

    data = frappe.get_all(
        "Live Classroom",
        filters={
            "student_id": student_id.strip(),
            "course_id": course_id.strip()
        },
        fields=[
            "name", "subject", "topic", "subtopic", "meeting_link","description","caption","student_id",
            "meeting_start_time", "meeting_end_time", "status", "tutor_id","course_id","faculty_email",
            "status","thumbnail","scheduled_date"
        ]
    )
    frappe.logger().info(f"Found {len(data)} records: {data}")
    return data or []



import frappe
from frappe.utils import now

@frappe.whitelist()
def create_live_classroom(data):
    """
    Create a new Live Classroom session
    Args:
        data (str): JSON string with session details
    Returns:
        dict: success flag and name of created document
    """
    import json

    try:
        payload = json.loads(data)

        # Required fields
        student_id = payload.get("student_id")
        course_id = payload.get("course_id")
        meeting_start_time = payload.get("meeting_start_time")
        meeting_end_time = payload.get("meeting_end_time")
        scheduled_date = payload.get("scheduled_date")

        if not (student_id and course_id and meeting_start_time and meeting_end_time and scheduled_date):
            frappe.throw("Missing required fields: student_id, course_id, meeting_start_time, meeting_end_time, scheduled_date")

        # Create Live Classroom document
        live_class = frappe.get_doc({
            "doctype": "Live Classroom",
            "student_id": student_id,
            "course_id": course_id,
            "subject": payload.get("subject"),
            "topic": payload.get("topic"),
            "subtopic": payload.get("subtopic"),
            "meeting_link": payload.get("meeting_link"),
            "description": payload.get("description"),
            "caption": payload.get("caption"),
            "status": payload.get("status", "Upcoming"),
            "tutor_id": payload.get("tutor_id"),
            "faculty_email": payload.get("faculty_email"),
            "thumbnail": payload.get("thumbnail"),
            "meeting_start_time": meeting_start_time,
            "meeting_end_time": meeting_end_time,
            "scheduled_date": scheduled_date
        })

        live_class.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "name": live_class.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_live_classroom Error")
        return {
            "success": False,
            "error": str(e)
        }
