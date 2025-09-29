import frappe

@frappe.whitelist(allow_guest=True)
def get_students_parents_tutors(tutor_id=None, student_id=None, parent_id=None):
    try:
        if tutor_id:
            students_list = frappe.get_all(
                "Students List",
                filters={"tutor_id": tutor_id},
                fields=["student_id"]
            )

            student_details = []
            for s in students_list:
                if s.student_id:
                    student = frappe.get_doc("Student", s.student_id)
                    student_details.append(student.as_dict())

            frappe.local.response = {
                "success": True,
                "students": student_details
            }

        elif student_id or parent_id:
            tutors_list = frappe.get_all(
                "Students List",
                filters={"student_id": student_id},
                fields=["tutor_id"]
            )

            tutor_details = []
            for t in tutors_list:
                if t.tutor_id:
                    tutor = frappe.get_doc("Tutors", t.tutor_id)
                    tutor_details.append(tutor.as_dict())

            frappe.local.response = {
                "success": True,
                "tutors": tutor_details
            }

        else:
            frappe.local.response = {
                "success": False,
                "message": "Provide tutor_id or student_id/parent_id"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Students/Parents/Tutors API Error")
        frappe.local.response = {
            "success": False,
            "message": str(e)
        }

    return frappe.local.response
