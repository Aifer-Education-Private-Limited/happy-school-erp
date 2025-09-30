import frappe
import uuid
from datetime import datetime




@frappe.whitelist(allow_guest=True)
def student_signup():
    try:
        data = frappe.form_dict

        parent_id = data.get("parent_id")
        student_name = data.get("student_name")
        mobile = data.get("mobile")
        grade = data.get("grade")
        join_date = data.get("join_date")
        password = data.get("password")
        dob = data.get("dob")
        profile = data.get("profile")

        # Check duplicate student
        if frappe.db.exists("HS Students", {"student_name": student_name, "parent_id": parent_id}):
            frappe.local.response.update ( {"success": False, "message": "Already registered"} )
            return

        # Check parent exists
        if not frappe.db.exists("Parents", {"name": parent_id}):
            frappe.local.response.update ( {"success": False, "message": f"Parent {parent_id} not found"} )
            return


        # Create student
        student = frappe.new_doc("HS Students")
        student.parent_id= parent_id
        student.student_name = student_name
        student.mobile = mobile
        student.grade = grade
        student.joinig_date= join_date
        student.password = password  
        student.dob = dob

        student.profile = profile
        student.status = "Linked"
        student.type = "Active"

        # Prevent auto Customer creation
        student.set_missing_customer_details = lambda: None

        # Save
        student.insert(ignore_permissions=True)
        frappe.db.commit()

        student_details = {
            "student_id": student.name,
            "name": student.student_name,
            "password": student.password,  
        }

        frappe.local.response.update ( {"success": True, "message": "Signup successful.", "student": student_details} )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Student Signup Error")
        frappe.local.response.update ( {"success": False, "message": "Internal server error"} )


@frappe.whitelist(allow_guest=True)
def student_login(student_id,password):
    try:
        student = frappe.db.get_value("HS Students", {"name":student_id,"password":password}, "name")
        if not student:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid id or password"
            })
            return
        
        frappe.local.response.update({
            "success": True,
            "student_id": student_id
        })
        return
    except Exception as e:
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
        return


@frappe.whitelist(allow_guest=True)
def get_student(parent_id):
    try:
        student_details = frappe.db.sql("""
            SELECT name as student_id,parent_id, student_name as full_name,joinig_date as joining_date,mobile as student_mobile_number,
                   dob,grade,password,profile
            FROM `tabHS Students`
            WHERE parent_id = %s AND status = "Linked"
            ORDER BY creation DESC
        """, parent_id, as_dict=True)

        if not student_details:
            student_details = []

        frappe.local.response.update({
            "success": True,
            "students": student_details
        })
        return

    except Exception as e:
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "students": []  
        })
        return


@frappe.whitelist(allow_guest=True)
def edit_student(student_id):
    try:
        data = frappe.form_dict  # Get submitted form data

        if not student_id:
            frappe.local.response.update({
                "success": False,
                "error": "Student id is required."
            })
            return


        # Fetch the student document
        if not frappe.db.exists("HS Students",student_id):
            frappe.local.response.update({
                "success": False,
                "error": f"Student {student_id} not found."
            })
            return

        student = frappe.get_doc("HS Students", student_id)

        # Example: Check for duplicate mobile number
        student_mobile = data.get("mobile")
        if student_mobile:
            existing_student = frappe.db.get_value(
                "HS Students",
                {"mobile": student_mobile, "name": ["!=", student_id]},
                "name"
            )
            if existing_student:
                frappe.local.response.update({
                    "success": False,
                    "error": f"Mobile number {student_mobile} already exists."
                })
                return
            student.student_mobile_number = student_mobile

        # List of editable fields
        editable_fields = [
            "student_name",
            "joinig_date",
            "dob",
            "grade",
            "mobile",
            "password",
            "profile",
            "status",
            "type",
            "parent_id"
        ]

        # Update fields from form_dict
        for field in editable_fields:
            if field in data:
                student.set(field, data.get(field) or "")

        # Save the student
        student.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.local.message_log = []

        # Prepare response similar to edit_lead
        frappe.local.response.update({
            "success": True,
            "message": f"Student {student_id} updated successfully.",
            "student": {
                "name": student.name,
                "student_name": student.student_name or "",
                "mobile": student.mobile or "",
                "join_date": student.joinig_date or "",
                "dob": student.dob or "",
                "grade": student.grade or "",
                "profile": student.profile or "",
                "status": student.status or "",
                "type": student.type or "",
                "parent_id": student.parent_id or ""
            },
            "http_status_code": 200
        })
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Edit Student Error")
        frappe.local.response.update({
            "success": False,
            "error": "An unexpected error occurred. Please contact support.",
            "http_status_code": 500
        })
        return

@frappe.whitelist(allow_guest=True)
def student_status_unlink(student_id):
    try:
        if not student_id:
            frappe.local.response.update ({
                "success": False,
                "error": "Student ID is required.",
                "http_status_code": 400
            })
            return

        # Load student doc
        student = frappe.get_doc("HS Students", student_id)

        # Update status to Unlink
        student.status = "Unlink"
        student.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.local.message_log = []

        frappe.local.response.update({
            "success": True,
        })
        return

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Student Status Unlink Error")
        frappe.local.response.update({
            "success": False,
            "error": "An unexpected error occurred. Please contact support.",
            "http_status_code": 500
        })
        return

import uuid
import frappe

@frappe.whitelist(allow_guest=True)
def create_student():
    try:
        data = frappe.form_dict

        parent_id = data.get("parent_id")
        student_name = data.get("student_name")
        mobile = data.get("mobile")
        grade = data.get("grade")
        join_date = data.get("join_date")
        dob = data.get("dob")
        profile = data.get("profile")

        # Check parent exists
        if not frappe.db.exists("Parents", {"name": parent_id}):
            frappe.local.response.update({
                "success": False,
                "message": f"Parent {parent_id} not found"
            })
            return

        # Check duplicate student
        existing_student = frappe.db.exists("HS Students", {
            "student_name": student_name,
            "parent_id": parent_id
        })
        if existing_student:
            frappe.local.response.update({
                "success": False,
                "message": "Already registered",
                "student_id": existing_student
            })
            return

        # Create student
        student = frappe.new_doc("HS Students")
        student.parent_id = parent_id
        student.student_name = student_name
        student.mobile = mobile
        student.grade = grade
        student.joinig_date = join_date
        student.password = f"{uuid.uuid4().hex[:6]}"  # random 6 char password
        student.dob = dob
        student.profile = profile
        student.status = "Linked"
        student.type = "Active"

        # Prevent auto Customer creation
        student.set_missing_customer_details = lambda: None

        # Save
        student.insert(ignore_permissions=True)
        frappe.db.commit()

        # Response details
        student_details = {
            "parent_id": student.parent_id,
            "student_id": student.name,
            "name": student.student_name,
            "mobile": student.mobile,
            "grade": student.grade,
            "joining_date": student.joinig_date,
            "date_of_birth": student.dob,
            "profile": student.profile,
            "status": student.status,
            "type": student.type
        }

        frappe.local.response.update({
            "success": True,
            "message": "Created Student Successfully",
            "student": student_details
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Student Creation Error")
        frappe.local.response.update({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        })
