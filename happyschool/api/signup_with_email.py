import frappe
from frappe.utils.password import set_encrypted_password

@frappe.whitelist(allow_guest=True)
def parent_signup():
    try:
        data = frappe.form_dict

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        state=data.get("state")
        dob=data.get("dob")
        authtype=data.get("authtype")
        token=data.get("token")
        email = data.get("email")
        mobile_number = data.get("mobile_number")
        password = data.get("password")

        if not email:
            return{
                "success":False,
                "message":"email is required"
            }

        # Validation
        if not first_name:
            return {
                "success": False,
                "message": "First Name is required."
            }

        # Check if email already exists
        if frappe.db.exists("Parents", {"email": email}):
            return {
                "success": False,
                "message": "Email already registered."
            }

        # Create Parent record
        parent = frappe.new_doc("Parents")
        parent.first_name = first_name
        parent.last_name = last_name
        parent.email = email
        parent.password=password
        parent.state=state
        parent.date_of_birth=dob
        parent.token=token
        parent.auth_type=authtype
        parent.mobile_number = mobile_number
        parent.insert(ignore_permissions=True)


        frappe.db.commit()

        parent_details = {
            "parent_id":parent.name,
            "first_name": parent.first_name,
            "last_name": parent.last_name,
            "email": parent.email,
            "mobile_number": parent.mobile_number,
            "dob":parent.date_of_birth,
            "state":parent.state,
            "authtype":parent.auth_type,

        }

        frappe.local.response.update ({
            "success": True,
            "message": "Signup successful.",
            "parent_id": parent_details
        })
            
        

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Parent Signup Error")
        frappe.local.response.update ({
            "success": False,
            "message": frappe.get_traceback()
        })

@frappe.whitelist(allow_guest=True)
def login_with_email(email, password):
    try:
        parent = frappe.db.get_value("Parents", {"email": email}, "name")
        if not parent:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid email or password"
            })
            return
        
        
        frappe.local.response.update({
            "success": True     
        })
    except Exception as e:
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })

