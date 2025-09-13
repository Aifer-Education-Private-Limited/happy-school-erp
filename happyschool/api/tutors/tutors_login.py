import frappe

@frappe.whitelist(allow_guest=True)
def tutor_login(email, password):
    """
    Authenticate tutor using Tutors doctype with Data field password (plain text)
    """
    try:
        tutor = frappe.db.get_value("Tutors", {"email": email}, ["name", "email", "password"], as_dict=True)
        if not tutor:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid email or password"
            })
            return

        # Compare plain text password
        if tutor.password != password:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid email or password"
            })
            return

        # Success
        frappe.local.response.update({
            "success": True,
            "message": "Login successful",
            "tutor_id": tutor.name,
        })

    except Exception as e:
        frappe.log_error(title="Tutor Login Error", message=frappe.get_traceback())
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })



@frappe.whitelist(allow_guest=True)
def check_user_by_tutor(tutor_id=None):
    
   
    try:
        app_version = {
            "ios_latest": 4003,
            "android_latest": 4003,
            "ios_minimum": 3262,
            "android_minimum": 3266,
        }

        if not tutor_id:
                  frappe.local.response.update({"success": False, "error": "Missing tutor_id"})

        tutor_data = frappe.db.sql("""
            SELECT name as tutor_id, tutor_name, phone, email, subject
            FROM `tabTutors`
            WHERE name = %s
            LIMIT 1
        """, (tutor_id,), as_dict=True)

        frappe.local.response.update({
            "success": True,
            "data": tutor_data,
            "app_version": app_version,
            # "ERP_API_KEY": f"Basic {frappe.conf.get('erp_auth_token')}"
            "ERP_API_KEY":"MTYxZDczZTJjNDA1NGY5OmY5MGY4ZWJmYWQ4NGFjOA=="

        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_user API error")
        frappe.local.response.update({"success": False, "error": str(e)})  