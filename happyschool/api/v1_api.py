import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_home_page_details(student_id: str):
    """
    API that mimics the Node.js GetUserCourseDetails response
    """

    try:
        # 1. Fetch enrolled courses
        user_courses = frappe.db.sql("""
            SELECT course_id, expiry_date
            FROM `tabUser Courses`
            WHERE student_id=%s
            AND is_active= "Active"
        """, student_id, as_dict=True)

        Course, upcoming = [], []

        if user_courses:
            course_ids = [c["course_id"] for c in user_courses]

            # 2. Dynamic Courses
            dynamic_courses = frappe.db.sql("""
                SELECT course_id, title, subject, image,
                       language_of_instruction, description,
                       details, ask_doubt_number
                FROM `tabCourses`
                WHERE course_id IN %(course_ids)s
            """, {"course_ids": tuple(course_ids)}, as_dict=True)

            for course in dynamic_courses:
                Course.append({
                    "course_id": course["course_id"],
                    "title": course["title"],
                    "subject": course["subject"],
                    "image": f"http://happyschool.localhost:8000/{course['image']}",
                    "language_of_instruction": course["language_of_instruction"],
                    "description": course["description"],
                    "details": course["details"],
                    "ask_doubt_number": course["ask_doubt_number"],
                    "total_item_count": 0,
                    "total_attended_count": 0
                })

            upcoming_live = frappe.db.sql("""
                SELECT topic, subtopic, meeting_link, caption, description,
                       student_id, faculty_email, meeting_start_time, meeting_end_time,
                       thumbnail, status, scheduled_date
                FROM `tabLive Classroom`
                WHERE student_id = %s AND status = "Upcoming"
            """, student_id, as_dict=True)

            for live in upcoming_live:
                upcoming.append({
                    "topic": live["topic"],
                    "subtopic": live["subtopic"],
                    "meeting_link": live["meeting_link"],
                    "caption": live["caption"],
                    "description": live["description"],
                    "student_id": live["student_id"],
                    "faculty_email": live["faculty_email"],
                    "meeting_start_time": live["meeting_start_time"],
                    "meeting_end_time": live["meeting_end_time"],
                    "thumbnail": f"http://happyschool.localhost:8000/{live['thumbnail']}",
                    "status": live["status"],
                    "scheduled_date": live["scheduled_date"]
                })

        # ✅ Directly set the response object (no "message")
        frappe.local.response.update({
            "success": True,
            "upcoming_data": upcoming,
            "datas": Course
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GetUserCourseDetails API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })
