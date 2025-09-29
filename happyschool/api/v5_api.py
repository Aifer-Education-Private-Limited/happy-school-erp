import frappe

@frappe.whitelist(allow_guest=True)
def get_students_parents_tutors(tutor_id=None, student_id=None, parent_id=None, course_id=None):
    try:
        if tutor_id:
            # Get students linked to tutor
            students_list = frappe.get_all(
                "Students List",
                filters={"tutor_id": tutor_id},
                fields=["student_id"]
            )

            student_details = []

            parent_details = []

            for s in students_list:
                if s.student_id:
                    student = frappe.get_value(
                        "Student",
                        s.student_id,
                        ["name as id", "first_name", "student_name", "custom_parent_id", "custom_profile"],
                        as_dict=True
                    )
                    student["chat_subject"] = f"{tutor_id}_{s.student_id}"
                    student_details.append(student)

                    # Fetch parent for each student separately
                    if student.get("custom_parent_id"):
                        try:
                            parent = frappe.get_value(
                                "Parents",
                                student["custom_parent_id"],
                                ["name as id", "first_name", "last_name", "profile"],
                                as_dict=True
                            )
                            if parent:
                                parent["student_id"] = student.get("name")
                                parent["student_name"] = student.get("student_name") or student.get("first_name")
                                parent["chat_subject"] = f"{tutor_id}_{s.student_id}"
                                parent_details.append(parent)
                        except frappe.DoesNotExistError:
                            continue

            frappe.local.response.update({
                "success": True,
                "students": student_details,
                "parents": parent_details
            })

        elif student_id or parent_id:
            # Build filters based on presence of parent_id
            if parent_id:
                filters = {"student_id": student_id}
            else:
                filters = {"student_id": student_id, "subject": course_id}

            tutors_list = frappe.get_all(
                "Students List",
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

            frappe.local.response.update({
                "success": True,
                "tutors": tutor_details
            })

        else:
            frappe.local.response.update({
                "success": False,
                "message": "Provide tutor_id or student_id/parent_id"
            })


    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Students/Parents/Tutors API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)

