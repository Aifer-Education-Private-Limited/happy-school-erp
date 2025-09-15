import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date


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
            "overall_course_data_count": 8,
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
        # ✅ Directly set the response object (no "message")
        frappe.local.response.update({
            "success": True,
            "datas": datas
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GetUserCourseDetails API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })