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
        parent.joindate = frappe.utils.now()
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
        # Fetch parent record with email and password
        parent = frappe.db.get_value(
            "Parents",
            {"email": email},
            ["name", "password"],
            as_dict=True
        )

        # If no parent found
        if not parent:
            frappe.local.response.update({
                "success": False,
                "message": "Account does not exist"
            })
            return

        # Check password
        if parent.password != password:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid email or password"
            })
            return

        # Success
        frappe.local.response.update({
            "success": True,
            "parent_id": parent.name,
            "message": "Login successful"
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

        print("mobile", mobile)
        print("isLogin", isLogin)
        print("auth_type", auth_type)
        print("channel", channel)

        # Case 1: If user is logging in
        if isLogin:
            if auth_type == "whatsapp":
                # Check if mobile exists in dot_users
                mobile_exists = frappe.db.sql("""
                    SELECT * 
                    FROM `tabParents`
                    WHERE mobile_number LIKE %s AND (auth_type = %s OR auth_type = 'phone')
                """, (f"%{mobile}", auth_type), as_dict=True)

                print("mobile_exists", mobile_exists)

                if mobile_exists:
                    frappe.local.response.update( {"status": True, "uid": mobile_exists[0].firebase_uid} )
                else:
                    frappe.local.response.update( {"status": False} )

            else:
                # Call OTP service
                otp_result = _send_otp(mobile, channel)
                frappe.local.response.update(otp_result)
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
                otp_result = _send_otp(mobile, channel)
                frappe.local.response.update(otp_result)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create OTP Error")
        frappe.local.response.update( {"error": True, "message": str(e)} )

@frappe.whitelist(allow_guest=True)
def verify_otp_by_otpless(mobile, otp, orderId):
    """
    Verify OTP using Otpless API and return UID if exists
    """
    try:
        editedMobile = mobile.replace("-", "").replace("+", "")
        result = _verify_otp(orderId, otp, editedMobile)

        # If OTP verified
        if result.get("isOTPVerified"):
            # Check if firebase_uid exists for this mobile
            mobile_exists = frappe.db.sql("""
                SELECT name 
                FROM `tabParents`
                WHERE mobile_number LIKE %s
            """, (f"%{mobile}",), as_dict=True)

            if mobile_exists:
                result["parent_id"] = mobile_exists[0].name
            else:
                result["parent_id"] = "xxxx"

        frappe.local.response.update(result)
        return  # Important: return nothing (None) to prevent extra wrapping


    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Verify OTP Error")
        frappe.local.response.update({
            "error": True,
            "message": str(e)
        })
        return

@frappe.whitelist(allow_guest=True)
def resend_otp(orderId):
    """
    Resend OTP using OtpLess API
    Args:
        order_id: Order ID received from previous OTP request
    """
    try:
        # Prepare request payload
        data = {"orderId": orderId}

        # Fetch credentials from environment
        # client_id = os.getenv("OTPLESS_CLIENT_ID")
        # client_secret = os.getenv("OTPLESS_CLIENT_SECRET")

        # if not client_id or not client_secret:
        #     return {"error": True, "message": "Missing OTPLESS credentials"}

        headers = {
            "Content-Type": "application/json",
        "clientId": OTPLESS_CLIENT_ID,
        "clientSecret": OTPLESS_CLIENT_SECRET,
        }

        url = "https://auth.otpless.app/auth/otp/v1/resend"
        response = requests.post(url, headers=headers, json=data)

        # ✅ Don't raise_for_status; parse JSON even on 400
        try:
            res_json = response.json()
        except Exception:
            res_json = {"error": True, "message": response.text}

        if response.status_code == 200:
            # success → return only orderId
            frappe.local.response.update(res_json)
        else:
            # failure → return full error from OTPLESS
            frappe.local.response.update({"error": True, "details": res_json})

    except requests.exceptions.HTTPError as http_err:
        frappe.local.response.update({"error": True, "message": f"HTTP error: {str(http_err)}"})
    except Exception as e:
        frappe.local.response.update({"error": True, "message": str(e)})


@frappe.whitelist(allow_guest=True)
def check_user(parent_id=None, studentId=None):
    try:
        # App version details
        app_version = {
            "ios_latest": 4003,
            "android_latest": 4003,
            "ios_minimum": 3262,
            "android_minimum": 3266,
        }

        # ✅ Case 1: Only Parent ID
        if parent_id and not studentId:
            user_data = frappe.db.sql("""
                SELECT first_name, last_name, mobile_number, email, auth_type, joindate, state, profile
                FROM `tabParents`
                WHERE name = %s
                ORDER BY joindate DESC
                LIMIT 1
            """, (parent_id,), as_dict=True)

            # format joindate
            if user_data:
                user_data[0]["joindate"] = _format_date(user_data[0].get("joindate"))

            frappe.local.response.update( {
                "success": True,
                "data": user_data,
                "app_version": app_version,
                # "ERP_API_KEY": f"Basic {frappe.conf.get('erp_auth_token')}"
            } )

            return

        # ✅ Case 2: Parent ID + studentId
        if uid and studentId:
            student_data = frappe.db.sql("""
                SELECT name, mobile, token, joindate, profile
                FROM `tabStudents`
                WHERE student_id = %s AND parent_uid = %s
                ORDER BY joindate DESC
                LIMIT 1
            """, (studentId, uid), as_dict=True)

            if student_data:
                student = student_data[0]
                student["joindate"] = _format_date(student.get("joindate"))

                # Update expired courses
                frappe.db.sql("""
                    UPDATE `tabUser Courses`
                    SET is_active = 0
                    WHERE student_id = %s
                    AND is_active = 1
                    AND expiry_date <= NOW()
                """, (studentId,))

                # Active courses
                user_courses = frappe.db.sql("""
                    SELECT course_id, expiry_date
                    FROM `tabUser Courses`
                    WHERE student_id = %s AND is_active = 1
                """, (studentId,), as_dict=True)

                # Count active courses (expiry in future)
                user_course_count = frappe.db.sql("""
                    SELECT COUNT(*) as count
                    FROM `tabUser Courses`
                    WHERE student_id = %s AND is_active = 1
                    AND expiry_date > NOW()
                """, (studentId,), as_dict=True)[0].count

                # TODO: Replace with actual DocType for streaks
                study_streak = {
                    "streak": 0,
                    "highest_streak": 0,
                    "recent_active_dates": []
                }

                # Discussion count
                discussion_count = frappe.db.count("Discussion", {"student_id": studentId})

                # Course titles
                course_ids = [c["course_id"] for c in user_courses]
                title_map = {}
                if course_ids:
                    placeholders = ", ".join(["%s"] * len(course_ids))
                    titles = frappe.db.sql(f"""
                        SELECT course_id, title
                        FROM `tabDynamic Courses`
                        WHERE course_id IN ({placeholders})
                    """, tuple(course_ids), as_dict=True)
                    for t in titles:
                        title_map[t.course_id] = t.title

                # Attach courses to student
                student["user_courses"] = []
                for c in user_courses:
                    student["user_courses"].append({
                        "course_id": c.course_id,
                        "course_expiry_date": _format_date(c.expiry_date),
                        "course_title": title_map.get(c.course_id, "")
                    })

                student["course_count"] = user_course_count
                student["userStreak"] = study_streak["streak"]
                student["discussionCount"] = discussion_count

            frappe.local.response.update( {
                "success": True,
                "data": student_data,
                "subjects": [],
                "app_version": app_version,
                "streak_time": 20,
                # "ERP_API_KEY": f"Basic {frappe.conf.get('erp_auth_token')}"
            } )

            return

        # ❌ Missing uid or studentId
        frappe.local.response.update( {"success": False, "error": "Missing uid or studentId"} )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "check_user API")
        frappe.local.response.update( {"success": False, "error": str(e)} )

    return


# # # functions # # #
def _send_otp(mobile, channel="sms"):
    editedMobile = mobile.replace("-", "")
    """Helper function to send OTP using Otpless API"""
    url = "https://auth.otpless.app/auth/otp/v1/send"
    data = {
        "phoneNumber": editedMobile,
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

def _format_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, str):
        return date_val.split(" ")[0]
    return date_val.strftime("%Y-%m-%d")