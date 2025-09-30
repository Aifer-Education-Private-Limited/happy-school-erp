import frappe
from datetime import datetime
from frappe.utils import get_datetime, format_datetime, format_date
import frappe
from frappe.utils import getdate, today
from dateutil.relativedelta import relativedelta



@frappe.whitelist(allow_guest=True)
def get_home_page_details(student_id: str):
    """
    Home page details:
      - Active & inactive courses (with test counts, attendance, weeks since joining, assignment %, completion %)
      - Upcoming live classes
    """
    try:
        # 1. Fetch ALL enrolled courses (both active & inactive)
        user_courses = frappe.db.sql("""
            SELECT course_id, expiry_date, admission_date, is_active
            FROM `tabUser Courses`
            WHERE student_id=%s
        """, student_id, as_dict=True)

        active_courses, inactive_courses, upcoming = [], [], []

        if user_courses:
            course_ids = [c["course_id"] for c in user_courses]

            # 2. Fetch course details
            dynamic_courses = frappe.db.sql("""
                SELECT name as course_id, title, subject, image,
                       language_of_instruction, description,
                       details, ask_doubt_number
                FROM `tabCourses`
                WHERE name IN %(course_ids)s
            """, {"course_ids": tuple(course_ids)}, as_dict=True)

            # Map admission_date & status by course_id
            admission_map = {c.course_id: c.admission_date for c in user_courses}
            status_map = {c.course_id: c.is_active for c in user_courses}

            for course in dynamic_courses:
                course_id = course["course_id"]

                # --- Count total assigned tests ---
                assigned_test_ids = frappe.db.sql_list("""
                    SELECT test_id
                    FROM `tabHS Student Tests`
                    WHERE student_id=%s
                """, (student_id,))

                if assigned_test_ids:
                    total_item_count = frappe.db.count("Tests", {
                        "name": ["in", assigned_test_ids],
                        "course_id": course_id,
                        "is_active": 1
                    })
                else:
                    total_item_count = 0

                # --- Attended tests ---
                attended_test_ids = frappe.db.sql("""
                    SELECT tuh.test_id
                    FROM `tabTest User History` tuh
                    INNER JOIN `tabTests` t ON t.name = tuh.test_id
                    WHERE tuh.student_id=%s AND t.course_id=%s
                """, (student_id, course_id), as_dict=True)
                total_attended_count = len(attended_test_ids)

                # --- Attendance ---
                present_count = frappe.db.count("Std Attendance", {
                    "student_id": student_id,
                    "course_id": course_id,
                    "attendance": "Present"
                })
                absent_count = frappe.db.count("Std Attendance", {
                    "student_id": student_id,
                    "course_id": course_id,
                    "attendance": "Absent"
                })
                total_sessions = present_count + absent_count
                attendance_percentage = int(round((present_count / total_sessions * 100))) if total_sessions > 0 else 0

                # --- Weeks since joining ---
                weeks_completed = 0
                admission_date = admission_map.get(course_id)
                if admission_date:
                    join_date = getdate(admission_date)
                    today_date = getdate(today())
                    delta = relativedelta(today_date, join_date)
                    weeks_completed = (delta.years * 52) + (delta.months * 4) + (delta.days // 7)

                # --- Assignments ---
                total_assignments = frappe.db.count("HS Student Assignments", {
                    "student_id": student_id,
                    "course_id": course_id
                })

                submitted_assignments = frappe.db.sql("""
                    SELECT COUNT(sub.name) AS cnt
                    FROM `tabHS Student Submitted Assignments` sub
                    INNER JOIN `tabHS Student Assignments` assign
                        ON assign.name = sub.assignment_id
                    WHERE sub.student_id = %s
                      AND assign.course_id = %s
                """, (student_id, course_id), as_dict=True)[0].cnt or 0

                assignment_percentage = int(round((submitted_assignments / total_assignments * 100))) if total_assignments > 0 else 0

                # --- Live Sessions ---
                total_live_sessions = frappe.db.count("Live Classroom", {
                    "student_id": student_id,
                    "course_id": course_id
                })

                completed_live_sessions = frappe.db.count("Live Classroom", {
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": "Completed"
                })
                scheduled_live_sessions = frappe.db.count("Live Classroom", {
                    "student_id": student_id,
                    "course_id": course_id,
                    "status": ["!=", "Completed"]
                })

                completion_percentage = int(round((completed_live_sessions / total_live_sessions * 100))) if total_live_sessions > 0 else 0

                course_data = {
                    "course_id": course_id,
                    "title": course["title"],
                    "subject": course["subject"],
                    "image": f"http://happyschool.localhost:8000/{course['image']}" if course.get("image") else None,
                    "language_of_instruction": course["language_of_instruction"],
                    "description": course["description"],
                    "details": course["details"],
                    "ask_doubt_number": course["ask_doubt_number"],
                    "total_item_count": total_item_count,
                    "total_attended_count": total_attended_count,
                    "attendance_percentage": attendance_percentage,
                    "total_weeks_completed": weeks_completed,
                    "assignment_percentage": assignment_percentage,
                    "completed_live_sessions": completed_live_sessions,
                    "scheduled_live_sessions": scheduled_live_sessions,
                    "total_live_sessions":total_live_sessions,
                    # "completion_percentage": completion_percentage,
                    "status": status_map.get(course_id, "Inactive")  
                }

                if status_map.get(course_id) == "Active":
                    active_courses.append(course_data)
                else:
                    inactive_courses.append(course_data)

            # 3. Upcoming live classes (only for active)
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
                    "thumbnail": f"http://happyschool.localhost:8000/{live['thumbnail']}" if live.get("thumbnail") else None,
                    "status": live["status"],
                    "scheduled_date": live["scheduled_date"]
                })

        frappe.local.response.update({
            "success": True,
            "upcoming_data": upcoming,
            "active_courses": active_courses,
            "inactive_courses": inactive_courses
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
            frappe.local.response.update( {"success": False, "error": "student_id is required"} )

        upcoming, ongoing, past = [], [], []

        # Fetch live classroom details using student_id
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
        frappe.local.response.update( {
            "success": True,
            "data": {
                "ongoing": ongoing,
                "upcoming": upcoming,
                "past": past
            }
        } )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "ClassroomDetails API Error")
        frappe.local.response.update( {"success": False, "error": str(e)} )








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