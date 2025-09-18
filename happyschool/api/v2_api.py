import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date
import requests
RAZORPAY_KEY_ID = frappe.conf.get("RAZORPAY_KEY_ID")

@frappe.whitelist(allow_guest=True)
def get_parent_home_page_details(student_id: str, parent_id: str):
    """
    API that mimics the Node.js GetUserCourseDetails response
    """

    try:

        datas = {
            "student_id": student_id,
            "parent_id": parent_id,
            "student_name": "John Doe",
            "parent_name": "Jane Doe Parent",
            "total_attendance_count": 10,
            "total_attendance_earned_count": 7,
            "overall_course_data_count": 5,
            "overall_attended_data_count": 3,
            "subject_wise_data_count": [
                {
                    "name": "Mathematics",
                    "total_data_count": 3,
                    "attended_data_count": 2
                },
                {
                    "subject_name": "English",
                    "total_data_count": 2,
                    "attended_data_count": 1
                }
            ]
        }
        #  Directly set the response object (no "message")
        frappe.local.response.update({
            "success": True,
            "datas": datas
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Parent Home Page API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
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
            fields=["title", "description", "creation"]
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
                filters= filters,
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