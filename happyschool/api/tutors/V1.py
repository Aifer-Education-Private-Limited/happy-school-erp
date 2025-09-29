import frappe
import json
import requests
import mimetypes
from datetime import datetime
# from happyschool.utils.oci_storage import upload_pdf_to_oracle
from frappe.utils import today, getdate
import frappe
from frappe.utils import nowdate, get_first_day, get_last_day


ORACLE_UPLOAD_URL = frappe.conf.get("ORACLE_UPLOAD_URL")
ORACLE_AUTH_TOKEN = frappe.conf.get("ORACLE_AUTH_TOKEN")
FOLDER_NAME = "Happyschool Materials"  

@frappe.whitelist(allow_guest=True)
def submit_materials():
    """
    Upload materials and save entry in Materials doctype.
    Uses Oracle Object Storage REST API (no OCI SDK).
    Supports multiple file types.
    """
    try:
        # Extract form data
        form = frappe.local.form_dict
        tutor_id = form.get("tutor_id")
        subject = form.get("subject")
        topic = form.get("topic")
        subtopic = form.get("subtopic")
        material_name = form.get("material_name")
        student_id = form.get("student_id")
        session_id = form.get("session_id")

        if not tutor_id or not student_id:
            frappe.local.response.update( {"success": False, "message": "Tutor ID and Student ID are required"})

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update( {"success": False, "message": f"Tutor {tutor_id} not found"} )

        if not frappe.db.exists("Students List", {"tutor_id": tutor_id, "student_id": student_id}):
            frappe.local.response.update( {
                "success": False,
                "message": f"Student {student_id} is not assigned to Tutor {tutor_id}"
            } )

        uploaded_files = frappe.request.files.getlist("files")
        if not uploaded_files:
            frappe.local.response.update( {"success": False, "message": "No files uploaded"} )

        assignment_array = []

        for f in uploaded_files:
            filename = f.filename
            content = f.read()

            # Detect file type automatically
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Upload to Oracle REST API (inside folder)
            upload_url = f"{ORACLE_UPLOAD_URL}{FOLDER_NAME}/{filename}"
            headers = {
                "Authorization": ORACLE_AUTH_TOKEN,
                "Content-Type": mime_type
            }

            response = requests.put(upload_url, headers=headers, data=content)

            if response.status_code not in [200, 201]:
                frappe.local.response.update( {
                    "success": False,
                    "message": f"Upload failed for {filename}: {response.text}"
                } )

            file_url = upload_url 

            assignment_array.append({
                "file": filename,
                "url": file_url,
                "type": mime_type
            })

        # Save to Materials doctype
        doc = frappe.get_doc({
            "doctype": "Materials",
            "tutor_id": tutor_id,
            "student_id": student_id,
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "material_name": material_name,
            "session_id": session_id,
            "files": json.dumps(assignment_array),
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update( {"success": True, "message": "Materials submitted successfully"} )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_materials error")
        frappe.local.response.update( {"success": False, "message": str(e)} )







@frappe.whitelist(allow_guest=True)
def student_list():
    """
    Get all student details under a given tutor,
    including assigned, completed, pending test counts,
    assignment completion percentage, and subject.
    """
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        # Fetch tutor's student links
        student_links = frappe.get_all(
            "Students List",
            filters={"tutor_id": tutor_id},
            fields=["student_id", "course_id"]
        )

        if not student_links:
            frappe.local.response.update({
                "success": True,
                "tutor_id": tutor_id,
                "students": []
            })
            return

        students_data = []
        for link in student_links:
            student_id = link.student_id
            course_id = link.course_id

            if not frappe.db.exists("HS Students", student_id):
                continue

            student_doc = frappe.get_doc("HS Students", student_id)

            # ✅ Fetch subject from Courses
            subject = frappe.db.get_value("Courses", course_id, "subject") or ""

            # -------- Tests data --------
            assigned_tests = frappe.db.sql("""
                SELECT st.test_id
                FROM `tabHS Student Tests` st
                INNER JOIN `tabTests` t ON st.test_id = t.name
                WHERE st.student_id = %s
                  AND st.tutor_id = %s
                  AND t.course_id = %s
            """, (student_id, tutor_id, course_id), as_dict=True)

            assigned_test_ids = [t.test_id for t in assigned_tests]

            completed_tests = []
            if assigned_test_ids:
                completed_tests = frappe.get_all(
                    "Test User History",
                    filters={"student_id": student_id, "test_id": ["in", assigned_test_ids]},
                    fields=["test_id"]
                )
            completed_test_ids = [t.test_id for t in completed_tests]

            pending_count = len(assigned_test_ids) - len(completed_test_ids)

            # -------- Assignments data --------
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

            assignment_percentage = (
                int(round((submitted_assignments / total_assignments * 100)))
                if total_assignments > 0 else 0
            )

            # -------- Student info --------
            students_data.append({
                "student_id": student_doc.name,
                "student_name": student_doc.get("student_name"),
                "grade": student_doc.get("grade"),
                "mobile": student_doc.get("mobile"),
                "profile": student_doc.get("profile"),
                "join_date": student_doc.get("joining_date"),
                "course_id": course_id,
                "subject": subject,
                "assigned_count": len(assigned_test_ids),
                "completed_count": len(completed_test_ids),
                "pending_count": pending_count,
                "total_assignments": total_assignments,
                "submitted_assignments": submitted_assignments,
                "assignment_percentage": assignment_percentage
            })

        frappe.local.response.update({
            "success": True,
            "tutor_id": tutor_id,
            "students": students_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "student_list API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })



@frappe.whitelist(allow_guest=True)
def tutor_profile():
    """
    Get tutor profile details with sessions completed, pending, and monthly stats.
    """
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        tutor_doc = frappe.get_doc("Tutors", tutor_id)

        tutor_data = {
            "tutor_id": tutor_doc.name,
            "tutor_name": tutor_doc.get("tutor_name"),
            "profile": tutor_doc.get("profile"),
            "email": tutor_doc.get("email"),
            "location": tutor_doc.get("location"),
            "phone": tutor_doc.get("phone"),
            "rating": ""
        }

        # ✅ Total Completed Sessions
        completed_sessions = frappe.db.count(
            "Live Classroom",
            {"tutor_id": tutor_id, "status": "Completed"}
        )
        tutor_data["sessions_completed"] = completed_sessions

        # ✅ Pending Sessions
        pending_sessions = frappe.db.count(
            "Live Classroom",
            {"tutor_id": tutor_id, "status": "Scheduled"}
        )
        tutor_data["sessions_pending"] = pending_sessions

        # ✅ Monthly Completed Sessions (only current month)
        today = nowdate()
        start_date = get_first_day(today)
        end_date = get_last_day(today)

        monthly_completed = frappe.db.count(
            "Live Classroom",
            {
                "tutor_id": tutor_id,
                "status": "Completed",
                "scheduled_date": ["between", [start_date, end_date]]
            }
        )
        tutor_data["monthly_sessions_completed"] = monthly_completed

        # ✅ Students Count
        students_count = frappe.db.count("Students List", {"tutor_id": tutor_id})
        tutor_data["students_count"] = students_count

        frappe.local.response.update({
            "success": True,
            "tutor_profile": tutor_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "tutor_profile API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


@frappe.whitelist(allow_guest=True)
def scheduled_session():
    """
    Get scheduled sessions for a tutor (only Ongoing or Upcoming).
    If student_id is passed, filter by that student too.
    Request body:
        {
            "tutor_id": "TUT-0001",
            "student_id": "ST003"   # optional
        }
    """
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")
        student_id = data.get("student_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        # ---- Build filters ----
        filters = {"tutor_id": tutor_id, "status": ["in", ["Ongoing", "Upcoming"]]}
        if student_id:
            filters["student_id"] = student_id

        # Fetch sessions
        sessions = frappe.get_all(
            "Live Classroom",
            filters=filters,
            fields=[
                "name", "subject", "topic", "subtopic",
                "meeting_link", "caption", "description",
                "student_id", "faculty_email",
                "meeting_start_time", "meeting_end_time",
                "status", "scheduled_date", "thumbnail"
            ]
        )

        session_data = []
        for s in sessions:
            student_info = {}
            if s.student_id and frappe.db.exists("HS Students", s.student_id):
                student_doc = frappe.get_doc("HS Students", s.student_id)
                student_info = {
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("student_name"),
                    "profile": student_doc.get("profile"),
                    "grade": student_doc.get("grade")
                }

            session_data.append({
                "session_id": s.name,
                "subject": s.subject,
                "topic": s.topic,
                "subtopic": s.subtopic,
                "meeting_link": s.meeting_link,
                "caption": s.caption,
                "description": s.description,
                "faculty_email": s.faculty_email,
                "meeting_start_time": s.meeting_start_time,
                "meeting_end_time": s.meeting_end_time,
                "status": s.status,
                "scheduled_date": s.scheduled_date,
                "thumbnail": s.thumbnail,
                "student": student_info
            })

        frappe.local.response.update({
            "success": True,
            "tutor_id": tutor_id,
            "student_id": student_id if student_id else None,
            "sessions": session_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "scheduled_session API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })


@frappe.whitelist(allow_guest=True)
def completed_live_sessions():
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")
        student_id = data.get("student_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        # Filters for completed sessions
        filters = {"tutor_id": tutor_id, "status": "Completed"}
        if student_id:
            filters["student_id"] = student_id

        sessions = frappe.get_all(
            "Live Classroom",
            filters=filters,
            fields=[
                "name", "subject", "topic", "subtopic",
                "meeting_link", "caption", "description",
                "student_id", "faculty_email",
                "meeting_start_time", "meeting_end_time",
                "status", "scheduled_date", "thumbnail"
            ]
        )

        session_data = []
        for s in sessions:
            # ---- Get Student Info ----
            student_info = {}
            if s.student_id and frappe.db.exists("HS Students", s.student_id):
                student_doc = frappe.get_doc("HS Students", s.student_id)
                student_info = {
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("student_name"),
                    "profile": student_doc.get("profile"),
                    "grade": student_doc.get("grade")
                }

            # ---- Attendance Check ----
            attendance_record = frappe.db.get_value(
                "Std Attendance",
                {"student_id": s.student_id, "session_id": s.name},
                "attendance"
            )

            # If no attendance or marked absent → skip this session
            if not attendance_record or attendance_record == "Absent":
                continue

            # ---- Check Material Upload ----
            material_status = "Material Pending"
            if frappe.db.exists("Materials", {"tutor_id": tutor_id, "session_id": s.name}):
                material_status = "Material Uploaded"

            # ---- Session Details ----
            session_data.append({
                "session_id": s.name,
                "subject": s.subject,
                "topic": s.topic,
                "subtopic": s.subtopic,
                "meeting_link": s.meeting_link,
                "caption": s.caption,
                "description": s.description,
                "faculty_email": s.faculty_email,
                "meeting_start_time": s.meeting_start_time,
                "meeting_end_time": s.meeting_end_time,
                "status": s.status,
                "scheduled_date": s.scheduled_date,
                "thumbnail": s.thumbnail,
                "student": student_info,
                "material_upload": material_status,
                "attendance": attendance_record  # Will always be "Present"
            })

        frappe.local.response.update({
            "success": True,
            "tutor_id": tutor_id,
            "student_id": student_id if student_id else None,
            "sessions": session_data
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "completed_live_sessions API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })




@frappe.whitelist(allow_guest=True)
def get_feedback():
 
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        feedbacks = frappe.get_all(
            "Feedback",
            filters={"tutor_id": tutor_id},
            fields=["name", "student_id", "tutor_id", "rating", "review", "creation"]
        )

        valid_feedbacks = []
        for fb in feedbacks:
            student_id = fb.student_id
            if not student_id:
                continue

            if frappe.db.exists("Students List", {"tutor_id": tutor_id, "student_id": student_id}):
                student_info = {}
                if frappe.db.exists("HS Students", student_id):
                    student_doc = frappe.get_doc("HS Students", student_id)
                    student_info = {
                        "student_name": student_doc.get("student_name"),
                        "profile": student_doc.get("profile"),
                       
                    }

                valid_feedbacks.append({
                    "feedback_id": fb.name,
                    "student": student_info,
                    "rating": fb.rating,
                    "review": fb.review,
                    "creation": fb.creation
                })

        frappe.local.response.update({
            "success": True,
            "tutor_id": tutor_id,
            "feedbacks": valid_feedbacks
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_feedback API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })




@frappe.whitelist(allow_guest=True)
def tutor_home():
    """
    Tutor home dashboard API
    """
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        # ---- Tutor Info ----
        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        tutor_doc = frappe.get_doc("Tutors", tutor_id)
        tutor_info = {
            "tutor_id": tutor_doc.name,
            "tutor_name": tutor_doc.get("tutor_name"),
            "profile": tutor_doc.get("profile")
        }

        # ---- Students Count ----
        students_count = frappe.db.count("Students List", {"tutor_id": tutor_id})

        today_date = getdate(today())
        live_classes_raw = frappe.get_all(
            "Live Classroom",
            filters={"tutor_id": tutor_id},
            fields=["meeting_start_time"]
        )

        live_classes_today = 0
        for lc in live_classes_raw:
            if lc.meeting_start_time:
                if getdate(lc.meeting_start_time) == today_date:
                    live_classes_today += 1

        # ---- Feedback (Avg Rating) ----
        feedbacks = frappe.get_all(
            "Feedback",
            filters={"tutor_id": tutor_id},
            fields=["rating"]
        )
        avg_rating = 0
        if feedbacks:
            total_rating = sum([float(f.rating) for f in feedbacks if f.rating])
            avg_rating = round(total_rating / len(feedbacks), 1)

        upcoming_classes_raw = frappe.get_all(
            "Live Classroom",
            filters={"tutor_id": tutor_id, "status": "Ongoing"},
            fields=["name", "topic", "subtopic", "meeting_start_time", "student_id", "scheduled_date" ,"meeting_link", "caption", "description","meeting_start_time","meeting_end_time","thumbnail","scheduled_date", "course_id","tutor_id","faculty_email"]
        )

        upcoming_classes = []
        for c in upcoming_classes_raw:
            student_info = {}
            if c.student_id and frappe.db.exists("HS Students", c.student_id):
                student_doc = frappe.get_doc("HS Students", c.student_id)
                student_info = {
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("first_name"),
                    "grade": student_doc.get("grade")
                }

            upcoming_classes.append({
                "class_id": c.name,
                "topic": c.topic,
                "subtopic": c.subtopic,
                "start_time": c.meeting_start_time,
                "scheduled_date": c.scheduled_date,
                "meeting_link" : c.meeting_link,
                "caption" : c.caption,
                "description": c.description,
                "meeting_start_time": c.meeting_start_time,
                "meeting_end_time" :c.meeting_end_time,
                "thumbnail" :c.thumbnail,
                "scheduled_date" :c.scheduled_date,
                "tutor_id":c.tutor_id,
                "course_id" : c.course_id,
                "faculty_email":c.faculty_email,
                "student": student_info
            })
            
        completed_sessions = frappe.get_all(
            "Live Classroom",
            filters={"tutor_id": tutor_id, "status": "Completed"},
            fields=["name"]
        )

        pending_uploads = 0
        for cs in completed_sessions:
            if not frappe.db.exists("Materials", {"tutor_id": tutor_id, "session_id": cs.name}):
                pending_uploads += 1
        frappe.local.response.update({
            "success": True,
            "tutor_info": tutor_info,
            "students_count": students_count,
            "live_classes_today": live_classes_today,
            "feedback_avg": avg_rating,
            "ongoing_classes": upcoming_classes,
            "pending_uploads": pending_uploads  

        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "tutor_home API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })




@frappe.whitelist(allow_guest=True)
def tutor_account_delete():

  
    try:
        data = frappe.local.form_dict
        tutor_id = data.get("tutor_id")

        if not tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID is required"
            })
            return

        # Check tutor exists
        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        # Check if the tutor's status is already "Unlink"
        current_status = frappe.db.get_value("Tutors", tutor_id, "type")
        if current_status == "Unlink":
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} account is already deactivated"
            })
            return

        # Update tutor status to "Unlink"
        frappe.db.set_value("Tutors", tutor_id, "type", "Unlink")
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": f"Tutor {tutor_id} account unlinked successfully",
            "tutor_id": tutor_id,
            "status": "Unlink"
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "tutor_account_delete API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
