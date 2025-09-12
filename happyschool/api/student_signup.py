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
        type_status=data.get("type")
    

        if not mobile:
            frappe.local.response.update ({
                "success": False,
                "message": "Mobile Number is required"
            })
            return

        if frappe.db.exists("Students",{"mobile":mobile}):
            frappe.local.response.update ({
                "success": False,
                "message": "Already registered"
            })
            return

        if not frappe.db.exists("Students",{"parent_id":parent_id}):
            frappe.local.response.update({
                "success":False,
                "message":f"parent {parent_id} not exist"
            })
            return
        
        student=frappe.new_doc("Students")
        student.parent_id=parent_id
        student.student_name=student_name
        student.mobile=mobile
        student.grade=grade
        student.join_date=join_date
        student.password=password
        student.dob=dob
        student.profile=profile
        student.status="Linked"
        student.type=type_status if type_status else "Active"
        student.insert(ignore_permissions=True)
        frappe.db.commit()

        student_details={
            "student_id":student.name,
            "name":student.student_name,
            "mobile":student.mobile,
            "grade":student.grade,
            "join_date":student.join_date,
            "password":student.password,
            "dob":student.dob,
            "profile":student.profile,
            "status":student.status,
            "type":student.type
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



