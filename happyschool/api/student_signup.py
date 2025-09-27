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
        if frappe.db.exists("Student", {"student_name": student_name, "parent_id": parent_id}):
            frappe.local.response.update ( {"success": False, "message": "Already registered"} )
            return

        # Check parent exists
        if not frappe.db.exists("Parents", {"name": parent_id}):
            frappe.local.response.update ( {"success": False, "message": f"Parent {parent_id} not found"} )
            return


        # Create student
        student = frappe.new_doc("Student")
        student.custom_parent_id= parent_id
        student.first_name = student_name
        student.student_mobile_number = mobile
        student.custom_grade = grade
        student.joining_date= join_date
        student.custom_password = password  
        student.date_of_birth = dob
        student.student_email_id = f"{uuid}@example.com"

        student.custom_profile = profile
        student.custom_status = "Linked"
        student.custom_type = "Active"

        # Prevent auto Customer creation
        student.set_missing_customer_details = lambda: None

        # Save
        student.insert(ignore_permissions=True)
        frappe.db.commit()

        student_details = {
            "student_id": student.name,
            "name": student.first_name,
            "password": student.custom_password,  
        }

        frappe.local.response.update ( {"success": True, "message": "Signup successful.", "student": student_details} )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Student Signup Error")
        frappe.local.response.update ( {"success": False, "message": "Internal server error"} )


@frappe.whitelist(allow_guest=True)
def student_login(student_id,password):
    try:
        student = frappe.db.get_value("Student", {"name":student_id,"custom_password":password}, "name")
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
            SELECT name as student_id, custom_parent_id as parent_id, first_name as full_name, joining_date, student_mobile_number,
                   date_of_birth as dob, custom_grade as grade, custom_password as password, custom_profile as profile
            FROM `tabStudent`
            WHERE custom_parent_id = %s AND custom_status = "Linked"
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
        if not frappe.db.exists("Student",student_id):
            frappe.local.response.update({
                "success": False,
                "error": f"Student {student_id} not found."
            })
            return

        student = frappe.get_doc("Student", student_id)

        # Example: Check for duplicate email
        student_email = data.get("student_email_id")
        if student_email:
            existing_student = frappe.db.get_value(
                "Student",
                {"student_email_id": student_email, "name": ["!=", student_id]},
                "name"
            )
            if existing_student:
                frappe.local.response.update({
                    "success": False,
                    "error": f"Email ID {student_email} already exists."
                })
                return
            student.student_email_id = student_email

        # Example: Check for duplicate mobile number
        student_mobile = data.get("student_mobile_number")
        if student_mobile:
            existing_student = frappe.db.get_value(
                "Student",
                {"student_mobile_number": student_mobile, "name": ["!=", student_id]},
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
            "first_name",
            "joining_date",
            "date_of_birth",
            "custom_grade",
            "custom_password",
            "custom_profile",
            "custom_status",
            "custom_type",
            "custom_parent_id"
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
                "first_name": student.first_name or "",
                "student_email_id": student.student_email_id or "",
                "student_mobile_number": student.student_mobile_number or "",
                "joining_date": student.joining_date or "",
                "date_of_birth": student.date_of_birth or "",
                "custom_grade": student.custom_grade or "",
                "custom_profile": student.custom_profile or "",
                "custom_status": student.custom_status or "",
                "custom_type": student.custom_type or "",
                "custom_parent_id": student.custom_parent_id or ""
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
        student = frappe.get_doc("Student", student_id)

        # Update status to Unlink
        student.custom_status = "Unlink"
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
            frappe.local.response.update ( {"success": False, "message": f"Parent {parent_id} not found"} )
            return

        existing_student = frappe.db.exists("Student", {
            "first_name":student_name,
            "custom_parent_id": parent_id
        },"name")
        if existing_student:
            frappe.local.response.update({
                "success": False,
                "message": "Already registered",
                "student_id": existing_student        
            })
            return
        


        # Create student
        student = frappe.new_doc("Student")
        student.custom_parent_id = parent_id
        student.first_name = student_name
        student.student_mobile_number = mobile
        student.custom_grade = grade
        student.joining_date = join_date
        student.custom_password = f"{uuid.uuid4().hex[:6]}"
        student.date_of_birth = dob
        student.custom_profile = profile
        student.student_email_id = f"student_{uuid.uuid4().hex[:6]}@example.com"
        student.custom_status = "Linked"
        student.custom_type = "Active"

        # Prevent auto Customer creation
        student.set_missing_customer_details = lambda: None

        # Save
        student.insert(ignore_permissions=True)
        frappe.db.commit()
        

        student_details = {
            "parent_id":student.custom_parent_id,
            "student_id": student.name,
            "name": student.first_name,
            "mobile":student.student_mobile_number,
            "grade":student.custom_grade,
            "joining_date":student.joining_date,
            "date_of_birth": student.date_of_birth,
            "profile":student.custom_profile,
            "status":student.custom_status,
            "type":student.custom_type
        }

        frappe.local.response.update ( {"success": True, "message": "Created Student Successfully", "student": student_details} )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Student Creation Error")
        frappe.local.response.update ( {"success": False, "message": "Internal server error"} )

