import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date
# import razorpay
import requests
# Fetch Razorpay Key ID and Secret from the configuration
RAZORPAY_KEY_ID = frappe.conf.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = frappe.conf.get("RAZORPAY_KEY_SECRET")

razorpay_client = razorpay.Client(auth=("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"))

print("razorpay_client", razorpay_client)

@frappe.whitelist(allow_guest=True)
def get_parent_home_page_details(student_id: str, parent_id: str):
    """
    API that mimics the Node.js GetUserCourseDetails response
    """

    try:
        if not student_id and not parent_id:
            frappe.local.response.update({
                "success": False,
                "datas": []
            })
            return

        datas = {
            "student_id": student_id,
            "parent_id": parent_id,
            "student_name": "John Doe",
            "parent_name": "Jane Doe Parent",
            "total_attendance_count": 10,
            "total_attendance_earned_count": 7,
            "overall_course_data_count": 5,
            "overall_attended_data_count": 3,
            "subject_wise_data_count": [
                {
                    "name": "Mathematics",
                    "total_data_count": 3,
                    "attended_data_count": 2
                },
                {
                    "name": "English",
                    "total_data_count": 2,
                    "attended_data_count": 1
                }
            ]
        }
        #  Directly set the response object (no "message")
        frappe.local.response.update({
            "success": True,
            "datas": datas
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Parent Home Page API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
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
    counselling_qns=None,
    mobile=None
):
    try:
        # ✅ Ensure firebase_uid is provided
        if not firebase_uid:
            frappe.local.response.update( {
                "success": False,
                "message": "Firebase UID is required"
            } )
            return

        # ✅ Default values
        if not payment_link:
            payment_link = 0
        if not offerType:
            offerType, discount, promoCode = "", 0, ""

        # ✅ Ensure counselling_qns is JSON string
        # counselling_qns = json.dumps(counselling_qns) if counselling_qns else "[]"

        # ✅ Generate unique name
        unique_name = frappe.generate_hash(length=12)

        # ✅ Insert into table
        frappe.db.sql("""
            INSERT INTO `tabHS Transactions`
            (name, txn_id, amount, payable, products, email, customer_name, parent_id, time, state,
             item_code, refferal_code, discount, offer_type, erp_code, payment_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            unique_name, txn_id, amount, payable, course_id, email, name, firebase_uid,
            time, state, project, promoCode, discount, offerType,
            erpCode, payment_link
        ))
        frappe.db.commit()

        frappe.local.response.update( {
            "success": True,
            "message": "Checkout data saved successfully"
        } )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Checkout API Error")
        frappe.local.response.update( {
            "success": False,
            "message": str(e)
        } )

