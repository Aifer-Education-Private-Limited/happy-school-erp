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
