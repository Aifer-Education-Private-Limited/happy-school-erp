import frappe

@frappe.whitelist(allow_guest=True)
def parent_signup_with_mobile():
    try:
        data = frappe.form_dict

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        state = data.get("state")
        dob = data.get("dob")
        token = data.get("token")
        email = data.get("email")
        authtype = data.get("authtype")
        mobile = data.get("mobile")  # <-- fetch here

        # Validation
        if not mobile:
            return {
                "success": False,
                "message": "Mobile Number is required"
            }

        if not first_name:
            return {
                "success": False,
                "message": "First Name required."
            }

        # Check if mobile already exists
        if frappe.db.exists("Parents", {"mobile_number": mobile}):
            return {
                "success": False,
                "message": "Mobile already registered."
            }

        # Create Parent record
        parent = frappe.new_doc("Parents")
        parent.first_name = first_name
        parent.last_name = last_name
        parent.state = state
        parent.email = email
        parent.date_of_birth = dob
        parent.token = token
        parent.auth_type = authtype
        parent.mobile_number = mobile
        parent.insert(ignore_permissions=True)

        frappe.db.commit()

        parent_details = {
            "parent_id": parent.name,
            "first_name": parent.first_name,
            "last_name": parent.last_name,
            "mobile_number": parent.mobile_number,
            "email": parent.email,
            "dob": parent.date_of_birth,
            "state": parent.state,
            "authtype": parent.auth_type,
        }

        return {
            "success": True,
            "message": "Signup successful.",
            "parent": parent_details
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Parent Signup Error")
        return {
            "success": False,
            "message": frappe.get_traceback()
        }
