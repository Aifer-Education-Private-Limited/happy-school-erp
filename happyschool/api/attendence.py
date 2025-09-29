import frappe
from frappe.utils import nowdate, now_datetime,format_date
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils.data import formatdate
from frappe import _




@frappe.whitelist(allow_guest=True)
def make_attendance(student_id, confirm, session_id, course_id=None, tutor_id=None, rating=None, review=None, attendance=None):
    try:
        today = nowdate()

        # Map confirm → field name
        confirm_field_map = {"0": "tutor_confirm", "1": "student_confirm", "2": "material_confirm"}
        confirm_field = confirm_field_map.get(str(confirm))
        if not confirm_field:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid confirm value. Must be 0 (tutor), 1 (student), or 2 (material)"
            })
            return

        # Map attendance numeric → label
        attendance_status = None
        if attendance is not None:
            if str(attendance) == "0":
                attendance_status = "Absent"
            elif str(attendance) == "1":
                attendance_status = "Present"
            else:
                frappe.local.response.update({
                    "success": False,
                    "message": "Invalid attendance value. Must be 0 or 1"
                })
                return

        # ---- Find existing attendance row for this student & session (prefer exact course match if provided)
        filters = {"student_id": student_id, "session_id": session_id}
        if course_id:
            filters["course_id"] = course_id

        existing_rows = frappe.get_all(
            "Std Attendance",
            filters=filters,
            fields=["name", "tutor_confirm", "student_confirm", "material_confirm", "attendance", "course_id", "date"],
            order_by="creation desc",
            limit=1
        )

        # Helper: ensure course_id (if we need to create)
        def resolve_course_id():
            if course_id:
                return course_id
            lc = frappe.db.get_value("Live Classroom", session_id, "course_id")
            return lc or None

        # ---- Update existing
        if existing_rows:
            row = existing_rows[0]
            attendance_name = row.name

            existing_value = {
                "tutor_confirm": row.tutor_confirm,
                "student_confirm": row.student_confirm,
                "material_confirm": row.material_confirm,
            }.get(confirm_field)

            if str(existing_value) == "1":
                # already confirmed — optionally update attendance label if passed
                if attendance_status and row.attendance != attendance_status:
                    frappe.db.set_value("Std Attendance", attendance_name, "attendance", attendance_status)
                    frappe.db.commit()
                frappe.local.response.update({
                    "success": True,
                    "message": f"{confirm_field} already marked",
                    "attendance_id": attendance_name,
                    "updated_confirm": 1,
                    "attendance_status": attendance_status or row.attendance
                })
                return

            # flip 0/None → 1
            frappe.db.set_value("Std Attendance", attendance_name, confirm_field, 1)
            if attendance_status:
                frappe.db.set_value("Std Attendance", attendance_name, "attendance", attendance_status)
            frappe.db.commit()

            frappe.local.response.update({
                "success": True,
                "message": f"{confirm_field} updated successfully",
                "attendance_id": attendance_name,
                "updated_confirm": 1,
                "attendance_status": attendance_status or row.attendance
            })

        else:
            # ---- No existing row
            if confirm_field != "tutor_confirm":
                # Do NOT create a new row for student/material confirmation
                frappe.local.response.update({
                    "success": False,
                    "message": "Attendance record not found for this session. Ask tutor to mark attendance first.",
                })
                return

            # Create only for tutor_confirm (first touch)
            resolved_course_id = resolve_course_id()
            doc = frappe.get_doc({
                "doctype": "Std Attendance",
                "student_id": student_id,
                "course_id": resolved_course_id,
                "date": today,
                "time": now_datetime(),
                "session_id": session_id,
                confirm_field: 1,
                "attendance": attendance_status
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

            frappe.local.response.update({
                "success": True,
                "message": f"Attendance created and {confirm_field}",
                "attendance_id": doc.name,
                "attendance_status": attendance_status
            })

        # ---- Optional feedback
        if rating is not None or review:
            # Insert only if at least one is provided; handle None gracefully
            feedback_doc = frappe.get_doc({
                "doctype": "Feedback",
                "student_id": student_id,
                "tutor_id": tutor_id,
                "rating": rating,
                "review": review
            })
            feedback_doc.insert(ignore_permissions=True)
            frappe.db.commit()

        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "make_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })

        
@frappe.whitelist(allow_guest=True)
def get_student_attendance(student_id, course_id):
    try:
        records = frappe.db.sql(
            """
            SELECT name, date, time, session_id, material_confirm, attendance
            FROM `tabStd Attendance`
            WHERE student_id = %s 
              AND course_id = %s
              AND (material_confirm = 1 OR attendance = 'Absent')
            ORDER BY date DESC
            """,
            (student_id, course_id),
            as_dict=True
        )

        formatted = []
        for r in records:
            caption = None
            if r.session_id:
                caption = frappe.db.get_value("Live Classroom", r.session_id, "caption")

            formatted.append({
                "attendance_id": r.name,
                "time": r.time,
                "date": formatdate(r.date, "dd-MM-yyyy"),
                "session_caption": caption,
                "attendance": r.attendance
            })

        frappe.local.response.update({
            "success": True,
            "data": formatted
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_student_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "data": [],
            "error": str(e)
        })


@frappe.whitelist(allow_guest=True)
def check_attendance(student_id=None):
    try:
        if not student_id:
            frappe.local.response.update({
                "success": False,
                "error": "Student ID is required",
                "data": []
            })
            return

        tutor_id = frappe.db.get_value("User Courses", {"student_id": student_id}, "tutor_id") or ""

        records = frappe.db.sql(
            """
            SELECT name, student_id, date, tutor_confirm, session_id
            FROM `tabStd Attendance`
            WHERE student_id = %s
              AND tutor_confirm = 1
              AND (student_confirm IS NULL OR student_confirm = '')
              AND (material_confirm IS NULL OR material_confirm = '')
            ORDER BY date DESC
            """,
            (student_id,),
            as_dict=True
        )

        formatted_records = []
        for r in records:
            
            session_info = {}
            if r.session_id:
                session_info = frappe.db.get_value(
                    "Live Classroom", r.session_id, ["course_id", "caption"], as_dict=True
                ) or {}

            course_id = session_info.get("course_id") or ""
            session_title = session_info.get("caption") or ""

           
            course_title = frappe.db.get_value("Courses", course_id, "title") or ""

            formatted_records.append({
                "attendance_id": r.name,
                "course_id": course_id,
                "course_title": course_title,
                "session_id": r.session_id,
                "session_title": session_title,
                "date": formatdate(r.date, "dd-MM-yyyy") if r.date else "",
                "tutor_confirm": r.tutor_confirm,
                "tutor_id": tutor_id,
            })

        frappe.local.response.update({
            "success": True,
            "data": formatted_records
        })
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_attendance API Error")
        frappe.local.response.update({
            "success": False,
            "data": [],
            "error": str(e)
        })
