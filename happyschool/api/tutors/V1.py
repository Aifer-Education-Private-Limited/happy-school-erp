import json
from datetime import datetime
from happyschool.utils.oci_storage import upload_pdf_to_oracle
from frappe.utils import today, getdate

import frappe, json

@frappe.whitelist(allow_guest=True)
def submit_materials():
    """
    Upload materials and save entry in Materials doctype.
    Validates that the student belongs to the tutor using Students List.
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

        if not tutor_id or not student_id:
            return {"success": False, "error": "Tutor ID and Student ID are required"}

        # ---- Validate tutor exists ----
        if not frappe.db.exists("Tutors", tutor_id):
            return {"success": False, "error": f"Tutor {tutor_id} not found"}

        # ---- Validate student exists ----
        if not frappe.db.exists("Students", student_id):
            return {"success": False, "error": f"Student {student_id} not found"}

        # ---- Validate tutor-student relation ----
        if not frappe.db.exists("Students List", {"tutor_id": tutor_id, "student_id": student_id}):
            return {
                "success": False,
                "error": f"Student {student_id} is not assigned to Tutor {tutor_id}"
            }

        # ---- Extract uploaded files ----
        uploaded_files = frappe.request.files.getlist("files")
        if not uploaded_files:
            return {"success": False, "error": "No files uploaded"}

        # ---- Get OCI folder ----
        folder_name = frappe.conf.get("oci_materials_folder")
        if not folder_name:
            return {"success": False, "error": "Missing oci_materials_folder in site_config.json"}

        assignment_array = []

        # ---- Upload each file ----
        for f in uploaded_files:
            filename = f.filename
            content = f.read()

            file_dict = {"filename": filename, "content": content}

            result = upload_pdf_to_oracle(
                file_dict,
                folder_name=folder_name,
                material_name=material_name
            )

            assignment_array.append({
                "file": result["objectName"],
                "url": result["fileUrl"]
            })

        doc = frappe.get_doc({
            "doctype": "Materials",
            "tutor_id": tutor_id,
            "student_id": student_id,   
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "material_name": material_name,
            "files": json.dumps(assignment_array),
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "assignment": assignment_array}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_materials error")
        return {"success": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def student_list():
    """
    Get all student details under a given tutor.
    Request body:
        {
            "tutor_id": "TUT-0001"
        }
    """
    try:
        # Parse request body
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

        # Fetch student links for tutor
        student_links = frappe.get_all(
            "Students List",
            filters={"tutor_id": tutor_id},
            fields=["student_id", "subject"]
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
            if frappe.db.exists("Students", link.student_id):
                student_doc = frappe.get_doc("Students", link.student_id)
                students_data.append({
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("student_name"),
                    "grade": student_doc.get("grade"),
                    "mobile": student_doc.get("mobile"),
                    "profile":student_doc.get("profile"),
                    "join_date":student_doc.get("join_date"),
                    "subject": link.subject
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
    Get tutor profile details with sessions completed & active students.
    Request body:
        {
            "tutor_id": ""
        }
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
            "rating":""
        }

        completed_sessions = 0
        live_classes = frappe.get_all("Live Classroom", fields=["student_id"])

        for lc in live_classes:
            student_id = lc.student_id
            if not student_id:
                continue

            if frappe.db.exists("Students List", {"tutor_id": tutor_id, "student_id": student_id}):
                completed_sessions += 1

        tutor_data["sessions_completed"] = completed_sessions

        active_students = 0
        student_links = frappe.get_all("Students List", filters={"tutor_id": tutor_id}, fields=["student_id"])

        for link in student_links:
            if frappe.db.exists("Students", {"name": link.student_id, "type": "Active"}):
                active_students += 1

        tutor_data["active_students"] = active_students

        # ---- Final Response ----
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
            if s.student_id and frappe.db.exists("Students", s.student_id):
                student_doc = frappe.get_doc("Students", s.student_id)
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

        # Check tutor exists
        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

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
            if s.student_id and frappe.db.exists("Students", s.student_id):
                student_doc = frappe.get_doc("Students", s.student_id)
                student_info = {
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("student_name"),
                    "profile": student_doc.get("profile"),
                    "grade": student_doc.get("grade")
                }

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
                "material_upload": material_status
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
                if frappe.db.exists("Students", student_id):
                    student_doc = frappe.get_doc("Students", student_id)
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
            fields=["scheduled_date"]
        )

        live_classes_today = 0
        for lc in live_classes_raw:
            if lc.scheduled_date:
                if getdate(lc.scheduled_date) == today_date:
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

        # ---- Upcoming Classes ----
        upcoming_classes_raw = frappe.get_all(
            "Live Classroom",
            filters={"tutor_id": tutor_id, "status": "Upcoming"},
            fields=["name", "topic", "subtopic", "meeting_start_time", "student_id", "scheduled_date"]
        )

        upcoming_classes = []
        for c in upcoming_classes_raw:
            student_info = {}
            if c.student_id and frappe.db.exists("Students", c.student_id):
                student_doc = frappe.get_doc("Students", c.student_id)
                student_info = {
                    "student_id": student_doc.name,
                    "student_name": student_doc.get("student_name"),
                    "grade": student_doc.get("grade")
                }

            upcoming_classes.append({
                "class_id": c.name,
                "topic": c.topic,
                "subtopic": c.subtopic,
                "start_time": c.meeting_start_time,
                "scheduled_date": c.scheduled_date,
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
            "upcoming_classes": upcoming_classes,
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
