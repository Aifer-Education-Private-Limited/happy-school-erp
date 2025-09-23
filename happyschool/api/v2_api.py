import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date
import requests
RAZORPAY_KEY_ID = frappe.conf.get("RAZORPAY_KEY_ID")


@frappe.whitelist(allow_guest=True)
def get_parent_home_page_details(student_id: str, parent_id: str):
    """
    API: Returns Parent Home Page details dynamically
    """
    try:
        if not student_id or not parent_id:
            frappe.local.response.update({
                "success": False,
                "datas": []
            })
            return

        # -------- 1. Student & Parent names --------
        student_name = frappe.db.get_value("Student", student_id, "student_name") or "Unknown Student"
        parent_name = frappe.db.get_value("Parents", parent_id, "first_name") or "Unknown Parent"

        # -------- 2. Attendance counts --------
        total_attendance_count = frappe.db.count("Std Attendance", {"student_id": student_id})
        total_attendance_earned_count = frappe.db.count("Std Attendance", {
            "student_id": student_id,
            "attendance": "Present"
        })

        # -------- 3. Fetch all courses of student --------
        courses = frappe.db.sql("""
            SELECT course_id
            FROM `tabUser Courses`
            WHERE student_id = %s
        """, (student_id,), as_dict=True)

        course_ids = [c.course_id for c in courses] if courses else []

        overall_course_data_count = 0
        overall_attended_data_count = 0
        subject_wise_data_count = []

        if course_ids:
            # -------- 4. Count total tests in all courses --------
            tests = frappe.db.sql("""
                SELECT name, course_id
                FROM `tabTests`
                WHERE course_id IN %(course_ids)s
                  AND is_active = 1
            """, {"course_ids": tuple(course_ids)}, as_dict=True)

            overall_course_data_count = len(tests)

            # -------- 5. Attended tests --------
            attended = frappe.db.sql("""
                SELECT test_id
                FROM `tabTest User History`
                WHERE student_id = %s
            """, (student_id,), as_dict=True)

            attended_ids = {a.test_id for a in attended}
            overall_attended_data_count = len(attended_ids)

            # -------- 6. Subject-wise counts --------
            for cid in course_ids:
                course_tests = [t for t in tests if t.course_id == cid]
                course_test_ids = {t.name for t in course_tests}
                attended_in_course = len(course_test_ids & attended_ids)

                subject_wise_data_count.append({
                    "name": cid,  # or fetch course name if you have it
                    "total_data_count": len(course_tests),
                    "attended_data_count": attended_in_course
                })

        # -------- Final response --------
        datas = {
            "student_id": student_id,
            "parent_id": parent_id,
            "student_name": student_name,
            "parent_name": parent_name,
            "total_attendance_count": total_attendance_count,
            "total_attendance_earned_count": total_attendance_earned_count,
            "overall_course_data_count": overall_course_data_count,
            "overall_attended_data_count": overall_attended_data_count,
            "subject_wise_data_count": subject_wise_data_count
        }

        frappe.local.response.update({
            "success": True,
            "datas": datas
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_parent_home_page_details API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "datas": []
        })


@frappe.whitelist(allow_guest=True)
def get_announcements_by_student_or_parent():
    """
    Fetch announcements and events based on student_id or parent_id.
    If student_id is passed -> audience_type "Student" and "Both" + events for student.
    If parent_id is passed -> audience_type "Parent" and "Both" + events for parent (or linked students).
    
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
                "message": "Either Student ID or Parent ID is required",
                "announcements": [],
                "events": []
            })
            return

        # --------------------------
        # Announcements
        # --------------------------
        filters = {}
        if student_id:
            filters["audience_type"] = ["in", ["Student", "Both"]]
            filters["student_id"] = student_id
        if parent_id:
            filters["audience_type"] = ["in", ["Parent", "Both"]]
            filters["parent_id"] = parent_id

        announcements = frappe.get_all(
            "Announcement",
            filters=filters,
            fields=["title", "description", "creation"]
        )

        # --------------------------
        # Events
        # --------------------------
        events_data = []
        events = []

        if student_id:
            events = frappe.get_all(
                "Events",
                filters={"student_id": student_id},
                fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
            )

        elif parent_id:
            # If events are directly linked to parent
            events = frappe.get_all(
                "Events",
                filters={"parent_id": parent_id},
                fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
            )

            # If events are linked via student, get student_ids for this parent
            if not events:
                student_list = frappe.get_all(
                    "Student",
                    filters={"parent_id": parent_id},
                    fields=["name"]
                )
                student_ids = [s.name for s in student_list]

                if student_ids:
                    events = frappe.get_all(
                        "Events",
                        filters={"student_id": ["in", student_ids]},
                        fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
                    )

        for event in events:
            events_data.append({
                "title": event.title,
                "description": event.description,
                "event_date": event.event_date,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "meeting_link": event.meeting_link,
                "expiry_date": event.expiry_date
            })

        # --------------------------
        # Response
        # --------------------------
        frappe.local.response.update({
            "success": True,
            "message": "Announcements and events fetched successfully",
            "announcements": announcements,
            "events": events_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_announcements_by_student_or_parent API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


@frappe.whitelist(allow_guest=True)
def get_razorpay_key ():
    try:
        frappe.local.response.update({
            "success": True,
            "key": RAZORPAY_KEY_ID
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Razorpay Key API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })