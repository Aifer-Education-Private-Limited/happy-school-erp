import frappe
from frappe.utils import nowdate, now_datetime,format_date
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils.data import formatdate




@frappe.whitelist(allow_guest=True) 
def make_attendance(student_id, course_id, confirm):
    try:
        today = nowdate()

        # Check if attendance already exists for today
        existing = frappe.db.get_value(
            "Std Attendance",
            {"student_id": student_id, "course_id": course_id, "date": today},
            ["name", "confirm"]
        )

        if existing:
            attendance_name, existing_confirm = existing

            if str(existing_confirm) == str(confirm):
                # Confirm value is same → nothing to update
                frappe.local.response.update({
                    "success": False,
                    "message": "Attendance already marked for today"
                })
                return
            else:
                # Confirm value changed → update the record
                frappe.db.set_value(
                    "Std Attendance",
                    attendance_name,
                    "confirm",
                    confirm
                )
                frappe.db.commit()

                frappe.local.response.update({
                    "success": True,
                    "message": "Attendance updated successfully",
                    "attendance_id": attendance_name,
                    "updated_confirm": confirm
                })
                return

        # If no existing record → create new attendance
        doc = frappe.get_doc({
            "doctype": "Std Attendance",
            "student_id": student_id,
            "course_id": course_id,
            "date": today,
            "time": now_datetime(),
            "confirm": confirm
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": "Attendance marked successfully",
            "attendance_id": doc.name
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "make_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })


@frappe.whitelist(allow_guest=True)
def get_student_attendance(student_id, course_id):
    try:
        # Only fetch rows where confirm = 2
        records = frappe.db.sql(
            """
            SELECT name, date, confirm, time
            FROM `tabStd Attendance`
            WHERE student_id = %s 
              AND course_id = %s
              AND confirm = 2
            ORDER BY date DESC
            """,
            (student_id, course_id),
            as_dict=True
        )

        if not records:
            frappe.local.response.update({
                "success": False,
                "message": "Attendance Not Yet Confirmed"
            })
            return

        # Format the data
        formatted = []
        for r in records:
            formatted.append({
                "attendance_id": r.name,
                "time":r.time,
                "date": formatdate(r.date, "dd-MM-yyyy"),
                "confirm": r.confirm
            })

        frappe.local.response.update({
            "success": True,
            "data": formatted
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_student_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })

import frappe
from frappe.utils.data import formatdate

@frappe.whitelist(allow_guest=True)
def check_attendance(student_id=None):
    """
    Fetch student attendance records where confirm = 0 for a student.
    Includes course title and session (live classroom) title.
    """
    try:
        if not student_id:
            frappe.local.response.update({
                "success": False,
                "error": "Student ID is required"
            })
            return

        # Fetch attendance records with confirm = 0
        records = frappe.db.sql(
            """
            SELECT name, student_id, course_id, date, confirm, session_id
            FROM `tabStd Attendance`
            WHERE student_id = %s
              AND confirm = 0
            ORDER BY date DESC
            """,
            (student_id,),
            as_dict=True
        )

        if not records:
            frappe.local.response.update({
                "success": False,
                "message": "No unconfirmed attendance records found"
            })
            return

        formatted_records = []
        for r in records:
            # Fetch course title
            course_title = frappe.db.get_value("Courses", r.course_id, "title") or ""

            # Fetch session/live classroom title
            session_title = frappe.db.get_value("Live Classroom", r.session_id, "caption") or ""

            formatted_records.append({
                "attendance_id": r.name,
                "course_id": r.course_id,
                "course_title": course_title,
                "session_id": r.session_id,
                "session_title": session_title,
                "date": formatdate(r.date, "dd-MM-yyyy"),
                "confirm": r.confirm
            })

        frappe.local.response.update({
            "success": True,
            "data": formatted_records
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })
