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
    Parent Home Page API:
    - Student & Parent names
    - Attendance counts
    - All active courses from User Courses
    - Course-wise test counts (total & attended) — even if 0
    - Student-wide completed & scheduled sessions
    """
    try:
        if not student_id or not parent_id:
            frappe.local.response.update({
                "success": False,
                "datas": []
            })
            return

        # -------- 1. Student & Parent names --------
        student_name = frappe.db.get_value("HS Students", student_id, "student_name") or "Unknown Student"
        parent_name = frappe.db.get_value("Parents", parent_id, "first_name") or "Unknown Parent"

        # -------- 2. Attendance counts --------
        total_attendance_count = frappe.db.count("Std Attendance", {"student_id": student_id})
        total_attendance_earned_count = frappe.db.count("Std Attendance", {
            "student_id": student_id,
            "attendance": "Present"
        })

        # -------- 3. Active courses from User Courses --------
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
            # Loop through every active course from User Courses
            for cid in valid_course_ids:
                cname = frappe.db.get_value("Courses", cid, "title") or "Unknown Course"

                # Total tests assigned in this course (active only)
                total_data_count = frappe.db.count("Tests", {
                    "course_id": cid,
                    "is_active": 1
                })

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

                # Update overall totals
                overall_course_data_count += total_data_count
                overall_attended_data_count += attended_data_count

                subject_wise_data_count.append({
                    "course_id": cid,
                    "name": cname,
                    "total_data_count": total_data_count,
                    "attended_data_count": attended_data_count
                })

        # -------- 4. Student-wide session counts --------
        completed_sessions_count = frappe.db.count("Live Classroom", {
            "student_id": student_id,
            "status": "Completed"
        })

        scheduled_sessions_count = frappe.db.count("Live Classroom", {
            "student_id": student_id,
            "status": ["in", ["Upcoming", "Ongoing"]]
        })
        total_live_sessions = frappe.db.count("Live Classroom", {
                    "student_id": student_id,
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
            "completed_sessions_count": completed_sessions_count,
            "scheduled_sessions_count": scheduled_sessions_count,
            "total_live_sessions":total_live_sessions,
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
        # Announcements (audience_type-aware)
        # --------------------------
        ann_filters = {}
        if student_id:
            ann_filters["audience_type"] = ["in", ["Student", "Both"]]
            ann_filters["student_id"] = student_id
        if parent_id:
            ann_filters["audience_type"] = ["in", ["Parent", "Both"]]
            ann_filters["parent_id"] = parent_id

        announcements = frappe.get_all(
            "Announcement",
            filters=ann_filters,
            fields=["title", "description", "creation"]
        ) or []

        # --------------------------
        # Events (audience_type-aware)
        # --------------------------
        from datetime import datetime

        def fmt_time(val):
            """Return time as 'H:MM AM/PM' (e.g., '4:05 PM')."""
            if not val:
                return None
            try:
                if hasattr(val, "strftime"):
                    return val.strftime("%I:%M %p").lstrip("0")
                s = str(val).strip()
                s = s.split(".")[0]  # drop microseconds if present
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try:
                        dt = datetime.strptime(s, fmt)
                        return dt.strftime("%I:%M %p").lstrip("0")
                    except ValueError:
                        continue
                return s
            except Exception:
                return str(val)

        events_data = []
        events = []

        if student_id:
            # Events specifically for the student and audience Student/Both
            events = frappe.get_all(
                "Events",
                filters={
                    "audience_type": ["in", ["Student", "Both"]],
                    "student_id": student_id
                },
                fields=[
                    "title", "description", "event_date",
                    "start_time", "end_time", "meeting_link", "expiry_date"
                ]
            ) or []

        elif parent_id:
            # 1) Direct parent events with audience Parent/Both
            events = frappe.get_all(
                "Events",
                filters={
                    "audience_type": ["in", ["Parent", "Both"]],
                    "parent_id": parent_id
                },
                fields=[
                    "title", "description", "event_date",
                    "start_time", "end_time", "meeting_link", "expiry_date"
                ]
            ) or []

            # 2) If none, fall back to events attached to the parent's students
            if not events:
                # Use custom_parent_id (as used elsewhere in your project)
                student_list = frappe.get_all(
                    "HS Students",
                    filters={"parent_id": parent_id},
                    fields=["name"]
                ) or []
                student_ids = [s.name for s in student_list]

                if student_ids:
                    events = frappe.get_all(
                        "Events",
                        filters={
                            "audience_type": ["in", ["Parent", "Both"]],
                            "student_id": ["in", student_ids]
                        },
                        fields=[
                            "title", "description", "event_date",
                            "start_time", "end_time", "meeting_link", "expiry_date"
                        ]
                    ) or []

        for ev in events:
            events_data.append({
                "title": ev.title,
                "description": ev.description,
                "event_date": ev.event_date,   # keep date as-is
                "start_time": fmt_time(ev.start_time),
                "end_time": fmt_time(ev.end_time),
                "meeting_link": ev.meeting_link,
                "expiry_date": ev.expiry_date
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
            "message": str(e),
            "announcements": [],
            "events": []
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
    mobile=None,
    discountPerc=None,
    programDatas=None,
    studentName=None,
    grade=None
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
             item_code, refferal_code, discount, offer_type, erp_code, payment_link, mobile, discount_perc, program_datas, student_name, grade)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            unique_name, txn_id, amount, payable, course_id, email, name, firebase_uid,
            time, state, project, promoCode, discount, offerType,
            erpCode, payment_link, mobile, discountPerc, programDatas, studentName, grade
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


