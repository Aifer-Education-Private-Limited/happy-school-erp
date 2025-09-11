import frappe
from frappe.utils.password import check_password

@frappe.whitelist(allow_guest=True)
def tutor_login(email, password):
   
    try:
        tutor = frappe.db.get_value("Tutors", {"email": email}, ["name", "password"], as_dict=True)
        if not tutor:
            return {"success": False, "message": "Invalid email or password"}

        try:
            check_password("Tutors", tutor.name, password)
            verified = True
        except Exception:
            verified = (tutor.password == password)

        if not verified:
            return {"success": False, "message": "Invalid email or password"}

        tutor_doc = frappe.get_doc("Tutors", tutor.name)

        return {
            "success": True,
            "message": "Login successful",
            "tutor_id": tutor_doc.name,
        }

    except Exception as e:
        frappe.log_error(title="Tutor Login Error", message=frappe.get_traceback())
        return {"success": False, "error": str(e)}
