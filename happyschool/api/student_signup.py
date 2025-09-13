import frappe


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
        status=data.get("status")
        type_status=data.get("type")
        email=data.get("email")
    

        if not mobile:
            frappe.local.response.update ({
                "success": False,
                "message": "Mobile Number is required"
            })
            return

        if frappe.db.exists("Student",{"student_mobile_number":mobile}):
            frappe.local.response.update ({
                "success": False,
                "message": "Already registered"
            })
            return

        if not frappe.db.exists("Parents",{"name":parent_id}):
            frappe.local.response.update({
                "success":False,
                "message":f"parent {parent_id} not exist"
            })
            return
        
        student=frappe.new_doc("Student")
        student.custom_parent_id=parent_id
        student.first_name=student_name
        student.student_mobile_number=mobile
        student.custom_grade=grade
        student.joining_date=join_date
        student.custom_password=password
        student.date_of_birth=dob
        student.custom_profile=profile
        student.custom_status=status if status else "Linked"
        student.custom_type=type_status if type_status else "Active"
        student.student_email_id=email
        # Insert as Administrator
        frappe.set_user("Administrator")
        student.insert(ignore_permissions=True)
        frappe.db.commit()

        # Reset user to the original session user
        frappe.set_user(frappe.session.user)


        student_details={
            "student_id":student.name,
            "name":student.first_name,
            "mobile":student.student_mobile_number,
            "grade":student.custom_grade,
            "join_date":student.joining_date,
            "password":student.custom_password,
            "dob":student.date_of_birth,
            "profile":student.custom_profile,
            "status":student.custom_status,
            "email":student.student_email_id,
            "type":student.custom_type
        }

        frappe.local.response.update({
            "success": True,
            "message": "Signup successful.",
            "parent": student_details
        })
        return
        

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Student Signup Error")
        frappe.local.response.update ({
            "success": False,
            "message": frappe.get_traceback()
        })
        return

@frappe.whitelist(allow_guest=True)
def student_login(mobile,password):
    try:
        student = frappe.db.get_value("Students", {"mobile":mobile,"password":password}, "name")
        if not student:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid mobile or password"
            })
            return
        
        
        frappe.local.response.update({
            "success": True     
        })
        return
    except Exception as e:
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
        return



