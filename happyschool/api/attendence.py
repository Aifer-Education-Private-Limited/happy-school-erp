import frappe
from frappe.utils import nowdate, now_datetime,format_date
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils.data import formatdate


@frappe.whitelist(allow_guest=True) 
def make_attendance(student_id, course_id,confirm):
    today = nowdate()

    existing = frappe.db.exists(
        "Std Attendance",
        {"student_id": student_id, "course_id": course_id, "date": today}
    )

    if existing:
        return {"success": False, "message": "Attendance already marked for today"}

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

    return {"success": True, "message": "Attendance Marked Successfully", "attendance_id": doc.name}



@frappe.whitelist(allow_guest=True)
def get_student_attendance(student_id, course_id):
    try:
        # Only fetch rows where confirm = 2
        records = frappe.db.sql(
            """
            SELECT name, date, confirm
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
            return {"success": False, "message": "Attendance  Not Yet Confirmed"}

        formatted = []
        for r in records:
            formatted.append({
                "name": r.name,
                "date": format_date(r.date, "dd-MM-yyyy"),
                "confirm": r.confirm
            })

        return {"success": True, "data": formatted}

    except Exception as e:
        frappe.log_error(title="get_student_attendance", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}




@frappe.whitelist(allow_guest=True)
def check_attendance(student_id=None, course_id=None):
    """
    Fetch student attendance records where confirm = 0.
    Optional filters: student_id and course_id.
    """

    try:
        if not student_id or not course_id:
            return {"success": False, "error": "Student ID and Course ID are required"}

        # Fetch attendance records with confirm = 0
        records = frappe.db.sql(
            """
            SELECT name, student_id, course_id, date, confirm ,session_id
            FROM `tabStd Attendance`
            WHERE student_id = %s
              AND course_id = %s
              AND confirm = 0
            ORDER BY date DESC
            """,
            (student_id, course_id),
            as_dict=True
        )

        if not records:
            return {"success": False, "message": "No unconfirmed attendance records found"}

        # Format the date nicely
        formatted_records = []
        for r in records:
            formatted_records.append({
                "name": r.name,
                "student_id": r.student_id,
                "course_id": r.course_id,
                "date": formatdate(r.date, "dd-MM-yyyy"),
                "session_id" : r.session_id,
                "confirm": r.confirm
            })

        return {"success": True, "data": formatted_records}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_attendance API Error")
        return {"success": False, "error": str(e)}
