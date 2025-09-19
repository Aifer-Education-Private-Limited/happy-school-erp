import frappe
from frappe.utils import nowdate, now_datetime,format_date
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils.data import formatdate

@frappe.whitelist(allow_guest=True)
def make_attendance(student_id, confirm, session_id,course_id=None, tutor_id=None, rating=None, review=None, attendance=None):
    try:
        today = nowdate()

        # Map confirm → field name
        confirm_field_map = {
            "0": "tutor_confirm",
            "1": "student_confirm",
            "2": "material_confirm"
        }
        confirm_field = confirm_field_map.get(str(confirm))

        if not confirm_field:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid confirm value. Must be 0, 1, or 2"
            })
            return

        # Map attendance value → field string
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

        # Check if attendance already exists
        existing = frappe.db.get_value(
            "Std Attendance",
            {"student_id": student_id, "course_id": course_id, "date": today, "session_id": session_id},
            ["name", "tutor_confirm", "student_confirm", "material_confirm", "attendance"]
        )

        if existing:
            attendance_name, existing_tutor, existing_student, existing_material, existing_attendance = existing

            # Only update confirm field if current value is 0
            existing_value = {
                "tutor_confirm": existing_tutor,
                "student_confirm": existing_student,
                "material_confirm": existing_material,
            }.get(confirm_field)

            if str(existing_value) == "1":
                frappe.local.response.update({
                    "success": False,
                    "message": f"Attendance already marked for {confirm_field}",
                    "attendance_status": existing_attendance
                })
                return
            else:
                # Update status from 0 → 1
                frappe.db.set_value("Std Attendance", attendance_name, confirm_field, 1)
                if attendance_status:
                    frappe.db.set_value("Std Attendance", attendance_name, "attendance", attendance_status)
                frappe.db.commit()

                frappe.local.response.update({
                    "success": True,
                    "message": f"{confirm_field} updated successfully to 1",
                    "attendance_id": attendance_name,
                    "updated_confirm": 1,
                    "attendance_status": attendance_status
                })
        else:
            # New record: set the field to 1
            doc = frappe.get_doc({
                "doctype": "Std Attendance",
                "student_id": student_id,
                "course_id": course_id,
                "date": today,
                "time": now_datetime(),
                confirm_field: 1,  # set status to 1 directly
                "session_id": session_id,
                "attendance": attendance_status
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

            frappe.local.response.update({
                "success": True,
                "message": f"Attendance marked successfully in {confirm_field} with status 1",
                "attendance_id": doc.name,
                "attendance_status": attendance_status
            })

        # Insert Feedback if rating & review provided
        if rating and review:
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
        # Fetch all records for the student and course
        records = frappe.db.sql(
            """
            SELECT name, date, time, session_id, material_confirm, attendance
            FROM `tabStd Attendance`
            WHERE student_id = %s 
              AND course_id = %s
              AND (material_confirm = 2 OR attendance = 'Absent')
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
        
        # Get the tutor_id assigned to this student from Students List
        tutor_id = frappe.db.get_value("Students List", {"student_id": student_id}, "tutor_id") or ""

        records = frappe.db.sql(
            """
            SELECT name, student_id, course_id, date, tutor_confirm, session_id
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
            # Fetch course title
            course_title = frappe.db.get_value("Courses", r.course_id, "title") or ""

            # Fetch session/live classroom caption
            session_title = frappe.db.get_value("Live Classroom", r.session_id, "caption") or ""

            formatted_records.append({
                "attendance_id": r.name,
                "course_id": r.course_id,
                "course_title": course_title,
                "session_id": r.session_id,
                "session_title": session_title,
                "date": formatdate(r.date, "dd-MM-yyyy"),
                "tutor_confirm": r.tutor_confirm,
                "tutor_id": tutor_id ,
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
