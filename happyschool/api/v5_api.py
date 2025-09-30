import frappe

@frappe.whitelist(allow_guest=True)
def get_students_parents_tutors(tutor_id=None, student_id=None, parent_id=None, course_id=None):
    try:
        if tutor_id:
            students_list = frappe.get_all(
                "User Courses",
                filters={"tutor_id": tutor_id},
                fields=["student_id"]
            )

            student_details = []
            parent_details = []

            for s in students_list:
                if s.student_id:
                    student = frappe.get_value(
                        "HS Students",
                        s.student_id,
                        ["name as id", "student_name", "parent_id", "profile"],
                        as_dict=True
                    )
                    student["chat_subject"] = f"{tutor_id}_{s.student_id}"
                    student_details.append(student)

                    if student.get("parent_id"):
                        try:
                            parent = frappe.get_value(
                                "Parents",
                                student["parent_id"],
                                ["name as id", "first_name", "last_name", "profile"],
                                as_dict=True
                            )
                            if parent:
                                parent["student_id"] = student.get("id")
                                parent["student_name"] = student.get("student_name")
                                parent["chat_subject"] = f"{tutor_id}_{s.student_id}"
                                parent_details.append(parent)
                        except frappe.DoesNotExistError:
                            continue

            frappe.local.response.update( {
                "success": True,
                "students": student_details,
                "parents": parent_details
            } )
            return

        elif student_id or parent_id:
            filters = {"student_id": student_id} if parent_id else {"student_id": student_id, "course_id": course_id}

            tutors_list = frappe.get_all(
                "User Courses",
                filters=filters,
                fields=["tutor_id"]
            )

            tutor_details = []
            for t in tutors_list:
                if t.tutor_id:
                    tutor = frappe.get_value(
                        "Tutors",
                        t.tutor_id,
                        ["name as id", "tutor_name", "subject"],
                        as_dict=True
                    )
                    tutor["chat_subject"] = f"{t.tutor_id}_{student_id or ''}"
                    tutor_details.append(tutor)

            frappe.local.response.update( {
                "success": True,
                "tutors": tutor_details
            } )
            return

        else:
            frappe.local.response.update( {
                "success": False,
                "message": "Provide tutor_id or student_id/parent_id"
            } )
            return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Students/Parents/Tutors API Error")
        frappe.local.response.update( {
            "success": False,
            "message": str(e)
        } )
        return
