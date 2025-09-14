import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date

@frappe.whitelist(allow_guest=True)
def get_home_page_details(student_id: str):
    """
    API that mimics the Node.js GetUserCourseDetails response
    """

    try:
        # 1. Fetch enrolled courses
        user_courses = frappe.db.sql("""
            SELECT course_id, expiry_date
            FROM `tabUser Courses`
            WHERE student_id=%s
            AND is_active= "Active"
        """, student_id, as_dict=True)

        Course, upcoming = [], []

        if user_courses:
            course_ids = [c["course_id"] for c in user_courses]

            # 2. Dynamic Courses
            dynamic_courses = frappe.db.sql("""
                SELECT course_id, title, subject, image,
                       language_of_instruction, description,
                       details, ask_doubt_number
                FROM `tabCourses`
                WHERE course_id IN %(course_ids)s
            """, {"course_ids": tuple(course_ids)}, as_dict=True)

            for course in dynamic_courses:
                Course.append({
                    "course_id": course["course_id"],
                    "title": course["title"],
                    "subject": course["subject"],
                    "image": f"http://happyschool.localhost:8000/{course['image']}",
                    "language_of_instruction": course["language_of_instruction"],
                    "description": course["description"],
                    "details": course["details"],
                    "ask_doubt_number": course["ask_doubt_number"],
                    "total_item_count": 0,
                    "total_attended_count": 0
                })

            upcoming_live = frappe.db.sql("""
                SELECT topic, subtopic, meeting_link, caption, description,
                       student_id, faculty_email, meeting_start_time, meeting_end_time,
                       thumbnail, status, scheduled_date
                FROM `tabLive Classroom`
                WHERE student_id = %s AND status = "Upcoming"
            """, student_id, as_dict=True)

            for live in upcoming_live:
                upcoming.append({
                    "topic": live["topic"],
                    "subtopic": live["subtopic"],
                    "meeting_link": live["meeting_link"],
                    "caption": live["caption"],
                    "description": live["description"],
                    "student_id": live["student_id"],
                    "faculty_email": live["faculty_email"],
                    "meeting_start_time": live["meeting_start_time"],
                    "meeting_end_time": live["meeting_end_time"],
                    "thumbnail": f"http://happyschool.localhost:8000/{live['thumbnail']}",
                    "status": live["status"],
                    "scheduled_date": live["scheduled_date"]
                })

        # ✅ Directly set the response object (no "message")
        frappe.local.response.update({
            "success": True,
            "upcoming_data": upcoming,
            "datas": Course
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GetUserCourseDetails API Error")
        frappe.local.response.update({
            "success": False,
            "error": str(e)
        })


@frappe.whitelist(allow_guest=True)
def fetch_states():
    try:
        data = [
            "Andaman and Nicobar Islands",
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chandigarh",
            "Chhattisgarh",
            "Dadra and Nagar Haveli & Daman and Diu",
            "Delhi",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jammu and Kashmir",
            "Jharkhand",
            "Karnataka",
            "Kerala",
            "Ladakh",
            "Lakshadweep",
            "Madhya Pradesh",
            "Maharashtra",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Odisha",
            "Other Territory",
            "Puducherry",
            "Punjab",
            "Rajasthan",
            "Sikkim",
            "Tamil Nadu",
            "Telangana",
            "Tripura",
            "Uttar Pradesh",
            "Uttarakhand",
            "West Bengal",
            "Others"
        ]

        frappe.local.response.update( {
            "success": True,
            "data": data
        } )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Fetch States API Error")
        frappe.local.response.update( {
            "success": False,
            "error": str(e)
        } )


@frappe.whitelist(allow_guest=True)
def classroom_details(student_id=None):
    try:
        if not student_id:
            return {"success": False, "error": "student_id is required"}

        upcoming, ongoing, past = [], [], []

        # ✅ Fetch live classroom details using student_id
        query = """
            SELECT name, subject, topic, subtopic, meeting_link, caption, description,
                   faculty_email, meeting_start_time, meeting_end_time, thumbnail,
                   status, tutor_id, scheduled_date
            FROM `tabLive Classroom`
            WHERE student_id = %s
              AND status IN ('Upcoming', 'Ongoing', 'Completed')
        """
        data = frappe.db.sql(query, (student_id,), as_dict=True)

        now = datetime.now()

        for row in data:
            raw_start = row.get("meeting_start_time")
            raw_end = row.get("meeting_end_time")
            raw_date = row.get("scheduled_date")

            start_time = parse_datetime_safe(raw_start)
            end_time = parse_datetime_safe(raw_end)

            state = row.get("status")

            # --- Auto-update state ---
            if state == "Upcoming":
                if start_time and end_time:
                    if start_time > now:
                        state = "Upcoming"
                    elif start_time <= now <= end_time:
                        state = "Ongoing"
                    else:
                        state = "Completed"
            elif state == "Ongoing":
                if end_time and now > end_time:
                    state = "Completed"

            # ✅ Update DB if status changed
            if state != row["status"]:
                frappe.db.sql(
                    """UPDATE `tabLive Classroom`
                       SET status=%s WHERE name=%s""",
                    (state, row["name"])
                )
                frappe.db.commit()

            # --- Format for frontend (date + time) ---
            row["meeting_start_time"] = format_datetime(start_time, "dd-MM-yyyy hh:mm a") if start_time else None
            row["meeting_end_time"]   = format_datetime(end_time, "dd-MM-yyyy hh:mm a") if end_time else None
            row["scheduled_date"]     = format_date(raw_date) if raw_date else None
            row["status"]             = state

            # ✅ Append to correct list
            if state == "Upcoming":
                upcoming.append(row)
            elif state == "Ongoing":
                ongoing.append(row)
            else:
                past.append(row)

        # ✅ Final Response
        return {
            "success": True,
            "data": {
                "ongoing": ongoing,
                "upcoming": upcoming,
                "past": past
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ClassroomDetails API Error")
        return {"success": False, "error": str(e)}








### Functions ###

def parse_datetime_safe(dt):
    """Try parsing datetime in both dd-mm-YYYY and YYYY-mm-dd formats"""
    if not dt:
        return None
    dt_str = str(dt).strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None  # if nothing works

def format_time_to_ampm(dt):
    """Format datetime to 3:30 PM style"""
    parsed = parse_datetime_safe(dt)
    return parsed.strftime("%I:%M %p") if parsed else None

def format_date(dt):
    """Format datetime to Monday, Jan 15 style"""
    if not dt:
        return None
    try:
        return datetime.strptime(str(dt), "%d-%m-%Y").strftime("%A, %b %d")
    except Exception:
        try:
            return datetime.strptime(str(dt), "%Y-%m-%d").strftime("%A, %b %d")
        except Exception:
            return None