import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date
# import razorpay
import requests
# Fetch Razorpay Key ID and Secret from the configuration
RAZORPAY_KEY_ID = frappe.conf.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = frappe.conf.get("RAZORPAY_KEY_SECRET")

# razorpay_client = razorpay.Client(auth=("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"))

# print("razorpay_client", razorpay_client)



@frappe.whitelist(allow_guest=True)
def get_parent_home_page_details(student_id: str, parent_id: str):
    """
    Parent Home Page API with proper filtering:
    - Student & Parent names
    - Attendance counts
    - Only active courses from User Courses
    - Only active tests assigned via HS Student Tests
    - Course-wise test counts (total & attended)
    """
    try:
        if not student_id or not parent_id:
            frappe.local.response.update({
                "success": False,
                "datas": []
            })
            return

        # -------- 1. Student & Parent names --------
        student_name = frappe.db.get_value("Student", student_id, "student_name") or "Unknown Student"
        parent_name = frappe.db.get_value("Parents", parent_id, "first_name") or "Unknown Parent"

        # -------- 2. Attendance counts --------
        total_attendance_count = frappe.db.count("Std Attendance", {"student_id": student_id})
        total_attendance_earned_count = frappe.db.count("Std Attendance", {
            "student_id": student_id,
            "attendance": "Present"
        })

        # -------- 3. Get only ACTIVE courses assigned to this student --------
        user_courses = frappe.db.sql("""
            SELECT course_id 
            FROM `tabUser Courses`
            WHERE student_id = %s
              AND is_active = 'Active'
        """, (student_id,), as_dict=True)
        valid_course_ids = [row.course_id for row in user_courses]

        overall_course_data_count = 0
        overall_attended_data_count = 0
        subject_wise_data_count = []

        if valid_course_ids:
            # -------- 4. Get all assigned tests for this student --------
            assigned_tests = frappe.db.sql("""
                SELECT test_id
                FROM `tabHS Student Tests`
                WHERE student_id = %s
            """, (student_id,), as_dict=True)
            assigned_test_ids = [row.test_id for row in assigned_tests]

            if assigned_test_ids:
                # -------- 5. Group by course, but only within ACTIVE courses & ACTIVE tests --------
                course_tests = frappe.db.sql("""
                    SELECT t.course_id, c.title AS course_name, COUNT(t.name) AS total_tests
                    FROM `tabTests` t
                    INNER JOIN `tabCourses` c ON c.name = t.course_id
                    WHERE t.name IN %(test_ids)s
                      AND t.course_id IN %(valid_courses)s
                      AND t.is_active = 1
                    GROUP BY t.course_id, c.title
                """, {
                    "test_ids": tuple(assigned_test_ids),
                    "valid_courses": tuple(valid_course_ids)
                }, as_dict=True)

                for row in course_tests:
                    cid = row.course_id
                    cname = row.course_name
                    total_data_count = row.total_tests

                    # Attended tests for this course
                    attended = frappe.db.sql("""
                        SELECT COUNT(DISTINCT tuh.test_id) AS attended_count
                        FROM `tabTest User History` tuh
                        INNER JOIN `tabTests` t ON t.name = tuh.test_id
                        WHERE tuh.student_id = %s
                          AND t.course_id = %s
                          AND t.is_active = 1
                    """, (student_id, cid), as_dict=True)
                    attended_data_count = attended[0].attended_count if attended else 0

                    # Update totals
                    overall_course_data_count += total_data_count
                    overall_attended_data_count += attended_data_count

                    subject_wise_data_count.append({
                        "course_id": cid,
                        "name": cname,
                        "total_data_count": total_data_count,
                        "attended_data_count": attended_data_count
                    })

        # -------- Final response --------
        datas = {
            "student_id": student_id,
            "parent_id": parent_id,
            "student_name": student_name,
            "parent_name": parent_name,
            "total_attendance_count": total_attendance_count,
            "total_attendance_earned_count": total_attendance_earned_count,
            "overall_course_data_count": overall_course_data_count,
            "overall_attended_data_count": overall_attended_data_count,
            "subject_wise_data_count": subject_wise_data_count
        }

        frappe.local.response.update({
            "success": True,
            "datas": datas
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_parent_home_page_details API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e),
            "datas": []
        })


@frappe.whitelist(allow_guest=True)
def get_announcements_by_student_or_parent():
    """
    Fetch announcements and events based on student_id or parent_id.
    If student_id is passed -> audience_type "Student" and "Both" + events for student.
    If parent_id is passed -> audience_type "Parent" and "Both" + events for parent (or linked students).
    
    Request body:
        {
            "student_id": "ST001",
            "parent_id": "PR001"
        }
    """
    try:
        data = frappe.local.form_dict
        student_id = data.get("student_id")
        parent_id = data.get("parent_id")

        if not student_id and not parent_id:
            frappe.local.response.update({
                "success": False,
                "message": "Either Student ID or Parent ID is required",
                "announcements": [],
                "events": []
            })
            return

        # --------------------------
        # Announcements
        # --------------------------
        filters = {}
        if student_id:
            filters["audience_type"] = ["in", ["Student", "Both"]]
            filters["student_id"] = student_id
        if parent_id:
            filters["audience_type"] = ["in", ["Parent", "Both"]]
            filters["parent_id"] = parent_id

        announcements = frappe.get_all(
            "Announcement",
            filters=filters,
            fields=["title", "description", "creation"]
        )

        # --------------------------
        # Events
        # --------------------------
        events_data = []
        events = []

        if student_id:
            events = frappe.get_all(
                "Events",
                filters={"student_id": student_id},
                fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
            )

        elif parent_id:
            # If events are directly linked to parent
            events = frappe.get_all(
                "Events",
                filters={"parent_id": parent_id},
                fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
            )

            # If events are linked via student, get student_ids for this parent
            if not events:
                student_list = frappe.get_all(
                    "Student",
                    filters={"parent_id": parent_id},
                    fields=["name"]
                )
                student_ids = [s.name for s in student_list]

                if student_ids:
                    events = frappe.get_all(
                        "Events",
                        filters={"student_id": ["in", student_ids]},
                        fields=["title","description","event_date", "start_time", "end_time", "meeting_link", "expiry_date"]
                    )

        for event in events:
            events_data.append({
                "title": event.title,
                "description": event.description,
                "event_date": event.event_date,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "meeting_link": event.meeting_link,
                "expiry_date": event.expiry_date
            })

        # --------------------------
        # Response
        # --------------------------
        frappe.local.response.update({
            "success": True,
            "message": "Announcements and events fetched successfully",
            "announcements": announcements,
            "events": events_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_announcements_by_student_or_parent API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


@frappe.whitelist(allow_guest=True)
def get_razorpay_key():
    """Return Razorpay Key ID for client-side integration"""
    try:
        frappe.local.response.update( {
            "success": True,
            "key": RAZORPAY_KEY_ID
        } )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Razorpay Key API Error")
        frappe.local.response.update( {
            "success": False,
            "error": str(e)
        } )


@frappe.whitelist(allow_guest=True)
def checkout(
    txn_id=None,
    amount=None,
    firebase_uid=None,
    name=None,
    email=None,
    course_id=None,
    time=None,
    title=None,
    payable=None,
    terms=None,
    state=None,
    project=None,
    discount=None,
    promoCode=None,
    offerType=None,
    erpCode=None,
    payment_link=None,
    pincode=None,
    mobile=None
):
    try:
        # ✅ Ensure firebase_uid is provided
        if not firebase_uid:
            frappe.local.response.update({
                "success": False,
                "message": "Firebase UID is required"
            })
            return

        # ✅ Default values
        if not payment_link:
            payment_link = 0
        if not offerType:
            offerType, discount, promoCode = "", 0, ""

        # ✅ Generate unique name
        unique_name = frappe.generate_hash(length=12)

        # ✅ Insert into table
        frappe.db.sql("""
            INSERT INTO `tabHS Transactions`
            (name, txn_id, amount, payable, products, email, customer_name, parent_id, time, state,
             item_code, refferal_code, discount, offer_type, erp_code, payment_link, mobile)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            unique_name, txn_id, amount, payable, course_id, email, name, firebase_uid,
            time, state, project, promoCode, discount, offerType,
            erpCode, payment_link, mobile
        ))

        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": "Checkout data saved successfully"
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Checkout API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


@frappe.whitelist(allow_guest=True)
def get_transaction_by_txn_id(txn_id=None):
    try:
        frappe.local.response.update( {
            "success": True,
            "transactions": frappe.get_all("HS Transactions", filters={"txn_id": txn_id}, fields=["*"])
        } )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Transactions Using Txn ID API Error")
        frappe.local.response.update( {
            "success": False,
            "error": str(e)
        } )


