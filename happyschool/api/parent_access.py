import frappe
from frappe.utils.password import set_encrypted_password
import requests
OTPLESS_CLIENT_ID = frappe.conf.get("OTPLESS_CLIENT_ID")
OTPLESS_CLIENT_SECRET = frappe.conf.get("OTPLESS_CLIENT_SECRET")\

@frappe.whitelist(allow_guest=True)
def parent_signup():
    try:
        data = frappe.form_dict

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        state=data.get("state")
        dob=data.get("dob")
        authtype=data.get("authtype")
        profile=data.get("profile")
        email = data.get("email")
        mobile = data.get("mobile")
        password = data.get("password")
        

        if not email:
            frappe.local.response.update({
                "success":False,
                "message":"email is required"
            })
            return

        # Validation
        if not first_name or not last_name:
            frappe.local.response.update ({
                "success": False,
                "message": "First Name and Last Name is required."
            })
            return

        # Check if mobile already exists
        if frappe.db.exists("Parents", {"mobile_number": mobile}):
            frappe.local.response.update({
                "success": False,
                "message": "Mobile already registered."
            })
            return

        # Check if email already exists
        if frappe.db.exists("Parents", {"email": email}):
            frappe.local.response.update ({
                "success": False,
                "message": "Email already registered."
            })
            return

        # Create Parent record
        parent = frappe.new_doc("Parents")
        parent.first_name = first_name
        parent.last_name = last_name
        parent.email = email
        parent.password=password
        parent.state=state
        parent.date_of_birth=dob
        parent.profile=profile
        parent.auth_type=authtype
        parent.mobile_number = mobile
        parent.insert(ignore_permissions=True)


        frappe.db.commit()

        parent_id = parent.name

        frappe.local.response.update ({
            "success": True,
            "message": "Signup successful.",
            "parent_id": parent_id
        })
        return 
        

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Parent Signup Error")
        frappe.local.response.update ({
            "success": False,
            "message": frappe.get_traceback()
        })
        return

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
        return
    except Exception as e:
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
        return


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
            frappe.local.response.update({
                "success": False,
                "message": "Mobile Number is required"
            })
            return
        if not first_name:
            frappe.local.response.update({
                "success": False,
                "message": "First Name required."
            })
            return

        # Check if mobile already exists
        if frappe.db.exists("Parents", {"mobile": mobile}):
            frappe.local.response.update({
                "success": False,
                "message": "Mobile already registered."
            })
            return

                # Check if email already exists
        if frappe.db.exists("Parents", {"email": email}):
            frappe.local.response.update ({
                "success": False,
                "message": "Email already registered."
            })
            return

        # Create Parent record
        parent = frappe.new_doc("Parents")
        parent.first_name = first_name
        parent.last_name = last_name
        parent.state = state
        parent.email = email
        parent.date_of_birth = dob
        parent.token = token
        parent.auth_type = authtype
        parent.mobile = mobile
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

        frappe.local.response.update({
            "success": True,
            "message": "Signup successful.",
            "parent": parent_details
        })
        return

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Parent Signup Error")
        frappe.local.response.update({
            "success": False,
            "message": frappe.get_traceback()
        })
        return

@frappe.whitelist(allow_guest=True)
def generate_otp_by_otpless(mobile, isLogin=False, auth_type=None, channel="sms"):
    """
    API equivalent to CreateOTPByOtpLess (Node.js)
    """
    try:
        isLogin = True if str(isLogin).lower() in ["true", "1"] else False

        print(OTPLESS_CLIENT_ID, OTPLESS_CLIENT_SECRET, "OTPLESS_CLIENT_ID")

        # Case 1: If user is logging in
        if isLogin:
            if auth_type == "whatsapp":
                # Check if mobile exists in dot_users
                mobile_exists = frappe.db.sql("""
                    SELECT name 
                    FROM `tabParents`
                    WHERE mobile_number LIKE %s AND (auth_type = %s OR auth_type = 'phone')
                """, (f"%{mobile}", auth_type), as_dict=True)

                if mobile_exists:
                    frappe.local.response.update( {"status": True, "uid": mobile_exists[0].firebase_uid} )
                else:
                    frappe.local.response.update( {"status": False} )

            else:
                # Call OTP service
                return _send_otp(mobile, channel)

        # Case 2: New registration
        else:
            mobile_exists = frappe.db.sql("""
                SELECT name
                FROM `tabParents`
                WHERE mobile_number LIKE %s
            """, (f"%{mobile}",), as_dict=True)

            if mobile_exists:
                frappe.local.response.update( {"message": "Phone number already in use by another account"} )
            else:
                return _send_otp(mobile, channel)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create OTP Error")
        frappe.local.response.update( {"error": True, "message": str(e)} )

@frappe.whitelist(allow_guest=True)
def verify_otp_by_otpless(mobile, otp, orderId):
    """
    Verify OTP using Otpless API and return UID if exists
    """
    try:
        result = _verify_otp(orderId, otp, mobile)

        # If OTP verified
        if result.get("isOTPVerified"):
            # Check if firebase_uid exists for this mobile
            mobile_exists = frappe.db.sql("""
                SELECT firebase_uid 
                FROM `tabDot Users`
                WHERE mobile_number LIKE %s
            """, (f"%{mobile}",), as_dict=True)

            if mobile_exists:
                result["uid"] = mobile_exists[0].firebase_uid
            else:
                result["uid"] = "xxxx"

        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Verify OTP Error")
        return {"error": True, "message": str(e)}




# # # functions # # #
def _send_otp(mobile, channel="sms"):
    """Helper function to send OTP using Otpless API"""
    url = "https://auth.otpless.app/auth/otp/v1/send"
    data = {
        "phoneNumber": mobile,
        "otpLength": 6,
        "channel": channel,
        "expiry": 60
    }
    headers = {
        "Content-Type": "application/json",
        "clientId": OTPLESS_CLIENT_ID,
        "clientSecret": OTPLESS_CLIENT_SECRET,
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def _verify_otp(orderId, otp, mobile):
    """Helper to call Otpless Verify API"""
    url = "https://auth.otpless.app/auth/otp/v1/verify"
    data = {
        "orderId": orderId,
        "phoneNumber": mobile,
        "otp": otp
    }
    headers = {
        "Content-Type": "application/json",
        "clientId": OTPLESS_CLIENT_ID,
        "clientSecret": OTPLESS_CLIENT_SECRET,
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()