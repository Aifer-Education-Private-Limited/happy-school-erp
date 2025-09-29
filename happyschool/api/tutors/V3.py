import frappe
import requests
import mimetypes
import json
from datetime import datetime
from urllib.parse import quote
from frappe.utils import now_datetime


ORACLE_UPLOAD_URL = frappe.conf.get("ORACLE_UPLOAD_URL")
ORACLE_AUTH_TOKEN = frappe.conf.get("ORACLE_AUTH_TOKEN")
FOLDER_NAME = "Happyschool Student Assignments"  


@frappe.whitelist(allow_guest=True)
def submit_student_assignment_by_tutor():
    """
    Tutor uploads assignments for a student.
    Files are uploaded to Oracle Object Storage.
    Entry is created in HS Student Assignments doctype.
    """
    try:
        form = frappe.local.form_dict
        tutor_id = form.get("tutor_id")
        student_id = form.get("student_id")
        assignment_name = form.get("assignment_name")
        course_id = form.get("course_id")
        topic = form.get("topic")
        subtopic = form.get("subtopic")
        type = form.get("type")
        description = form.get("description")

        # ---------- Validations ----------
        if not tutor_id or not student_id or not course_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID, Student ID and Course ID are required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        if not frappe.db.exists("HS Students", student_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Student {student_id} not found"
            })
            return

        enrolled = frappe.db.exists(
            "User Courses",
            {"student_id": student_id, "course_id": course_id, "is_active": "Active"}
        )
        if not enrolled:
            frappe.local.response.update({
                "success": False,
                "message": f"Student {student_id} is not enrolled in course {course_id}"
            })
            return

        uploaded_files = frappe.request.files.getlist("files")
        if not uploaded_files:
            frappe.local.response.update({
                "success": False,
                "message": "No files uploaded"
            })
            return

        assignment_files = []

        for f in uploaded_files:
            filename = f.filename
            content = f.read()

            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            folder_encoded = quote(FOLDER_NAME)
            filename_encoded = quote(filename)

            upload_url = f"{ORACLE_UPLOAD_URL.rstrip('/')}/{folder_encoded}/{filename_encoded}"

            headers = {
                "Authorization": ORACLE_AUTH_TOKEN,
                "Content-Type": mime_type
            }

            response = requests.put(upload_url, headers=headers, data=content)

            if response.status_code not in [200, 201]:
                frappe.local.response.update({
                    "success": False,
                    "message": f"Upload failed for {filename}: {response.text}"
                })
                return

            assignment_files.append({
                "url": upload_url,
                "type":mime_type
            })

        # ---------- Save Assignment ----------
        doc = frappe.get_doc({
            "doctype": "HS Student Assignments",
            "tutor_id": tutor_id,
            "student_id": student_id,
            "assignment_name": assignment_name,
            "course_id": course_id,
            "topic": topic,
            "subtopic": subtopic,
            "type": type,
            "description": description,
            "files": json.dumps(assignment_files),
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": "Student Assignment submitted successfully",
            "assignment_id": doc.name,
             "file_type": assignment_files[0]["type"] if assignment_files else None

        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_student_assignment_by_tutor error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })



FOLDER_NAME = "Happyschool Student Submitted Assignments"  


@frappe.whitelist(allow_guest=True)
def submit_student_assignment_answer():
    """
    API for students to submit answers for tutor-assigned assignments.
    Uploads files to Oracle and saves entry in HS Student Submitted Assignments.
    """
    try:
        # Extract form data
        form = frappe.local.form_dict
        assignment_id = form.get("assignment_id")
        student_id = form.get("student_id")
        tutor_id = form.get("tutor_id")

        if not assignment_id :
            frappe.local.response.update({
                "success": False,
                "message": "Assignment ID and Student ID are required"
            })
            return

        # Validate assignment & student
        if not frappe.db.exists("HS Student Assignments", assignment_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Assignment {assignment_id} not found"
            })
            return

        if not frappe.db.exists("HS Students", student_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Student {student_id} not found"
            })
            return

        uploaded_files = frappe.request.files.getlist("files")
        if not uploaded_files:
            frappe.local.response.update({
                "success": False,
                "message": "No files uploaded"
            })
            return

        file_array = []

        for f in uploaded_files:
            filename = f.filename
            content = f.read()

            # Detect file type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Safe URL
            folder_encoded = quote(FOLDER_NAME)
            filename_encoded = quote(filename)
            upload_url = f"{ORACLE_UPLOAD_URL.rstrip('/')}/{folder_encoded}/{filename_encoded}"

            headers = {
                "Authorization": ORACLE_AUTH_TOKEN,
                "Content-Type": mime_type
            }

            response = requests.put(upload_url, headers=headers, data=content)

            if response.status_code not in [200, 201]:
                frappe.local.response.update({
                    "success": False,
                    "message": f"Upload failed for {filename}: {response.text}"
                })
                return

            file_array.append({
                "file": filename,
                "url": upload_url,
                "type": mime_type
            })

        doc = frappe.get_doc({
            "doctype": "HS Student Submitted Assignments",
            "assignment_id": assignment_id,
            "student_id":student_id,
            "tutor_id":tutor_id,
            "files": json.dumps(file_array),
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": "Assignment submitted successfully",
            "submission_id": doc.name,
            "file_type": file_array[0]["type"] if file_array else None
                
            

        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_student_assignment_answer error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })





@frappe.whitelist(allow_guest=True)
def list_assignments(role=None, tutor_id=None, student_id=None, course_id=None):
    """
    One API → 2 behaviors:
      - role="student": fetch tutor assignments (HS Student Assignments) for this student (optionally filter by course_id),
                        also include submission status & feedback if student submitted
      - role="tutor": fetch student submitted assignments (HS Student Submitted Assignments) for this tutor+student,
                      enriched with assignment details (from HS Student Assignments)
    """

    try:
        if not role:
            frappe.local.response.update({
                "success": False,
                "message": "Role is required (student/tutor)"
            })
            return

        data = []

        # ---------------- STUDENT SIDE ----------------
        if role.lower() == "student":
            if not student_id:
                frappe.local.response.update({
                    "success": False,
                    "message": "student_id is required for role=student"
                })
                return

            filters = {"student_id": student_id}
            if course_id:
                filters["course_id"] = course_id

            assignments = frappe.get_all(
                "HS Student Assignments",
                filters=filters,
                fields=[
                    "name as assignment_id",
                    "tutor_id",
                    "course_id",
                    "assignment_name",
                    "topic",
                    "subtopic",
                    "type",
                    "files",
                    "description",
                    "creation"
                ],
                order_by="creation desc"
            )

            for a in assignments:
                files = []
                if a.files:
                    try:
                        files_list = json.loads(a.files)
                        files = [
                            {"url": f.get("url"), "type": f.get("type")}
                            for f in files_list if f.get("url")
                        ]
                    except Exception:
                        pass

                # --- Check if student has submitted ---
                submission = frappe.db.get_value(
                    "HS Student Submitted Assignments",
                    {"assignment_id": a.assignment_id, "student_id": student_id},
                    ["status", "feedback", "creation as submitted_date"],
                    as_dict=True
                )

                if submission:
                    status = submission.status or "Pending"
                    feedback = submission.feedback or ""
                    submitted_date = submission.submitted_date
                else:
                    status = "Not Submitted"
                    feedback = ""
                    submitted_date = None

                data.append({
                    "assignment_id": a.assignment_id,
                    "tutor_id": a.tutor_id,
                    "course_id": a.course_id,
                    "assignment_name": a.assignment_name,
                    "topic": a.topic,
                    "subtopic": a.subtopic,
                    "type":a.type,
                    "files": files,
                    "description": a.description,
                    "given_date": a.creation,
                    "status": status,
                    "feedback": feedback,
                    "submitted_date": submitted_date
                })

        # ---------------- TUTOR SIDE ----------------
        elif role.lower() == "tutor":
            if not tutor_id or not student_id:
                frappe.local.response.update({
                    "success": False,
                    "message": "tutor_id and student_id are required for role=tutor"
                })
                return

            submissions = frappe.get_all(
                "HS Student Submitted Assignments",
                filters={"student_id": student_id},
                fields=["name as submission_id", "assignment_id", "student_id", "files", "status", "feedback", "creation"],
                order_by="creation desc"
            )

            for s in submissions:
                files = []
                if s.files:
                    try:
                        files_list = json.loads(s.files)
                        files = [
                            {"url": f.get("url"), "type": f.get("type")}
                            for f in files_list if f.get("url")
                        ]
                    except Exception:
                        pass

                assignment_details = frappe.db.get_value(
                    "HS Student Assignments",
                    {"name": s.assignment_id, "tutor_id": tutor_id},
                    ["assignment_name", "topic", "subtopic","type", "course_id"],
                    as_dict=True
                )

                if not assignment_details:
                    continue

                data.append({
                    "submission_id": s.submission_id,
                    "assignment_id": s.assignment_id,
                    "status": s.status,
                    "feedback": s.feedback or "",
                    "student_id": s.student_id,
                    "assignment_name": assignment_details.assignment_name,
                    "topic": assignment_details.topic,
                    "subtopic": assignment_details.subtopic,
                    "type":assignment_details.type,
                    "course_id": assignment_details.course_id,
                    "files": files,
                    "submitted_date": s.creation
                })

        else:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid role. Must be student or tutor"
            })
            return

        frappe.local.response.update({
            "success": True,
            "role": role,
            "data": data,
            "count": len(data),
            "server_time": now_datetime()
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "list_assignments API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e),
            "data": []
        })




@frappe.whitelist(allow_guest=True)
def update_assignment_status(submission_id=None, tutor_id=None, status=None, feedback=None):
    """
    Tutor updates the status of a student's submitted assignment.
    - submission_id: ID from HS Student Submitted Assignments
    - tutor_id: must match the tutor of the assignment
    - status: "Completed" / "Rework"
    - feedback: optional text feedback for the student
    """
    try:
        if not submission_id or not tutor_id or not status:
            frappe.local.response.update({
                "success": False,
                "message": "submission_id, tutor_id and status are required"
            })
            return

        if status not in ["Completed", "Rework"]:
            frappe.local.response.update({
                "success": False,
                "message": "Invalid status. Must be 'Completed' or 'Rework'"
            })
            return

        # Fetch submission
        submission = frappe.get_doc("HS Student Submitted Assignments", submission_id)

        # Ensure tutor matches assignment tutor
        assignment_tutor = frappe.db.get_value("HS Student Assignments", submission.assignment_id, "tutor_id")
        if assignment_tutor != tutor_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor mismatch. You are not allowed to update this submission."
            })
            return

        # Update status + feedback
        submission.status = status
        if feedback:
            submission.feedback = feedback
        submission.reviewed_date = now_datetime()
        submission.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": f"Assignment status updated to {status}",
            "data": {
                "submission_id": submission_id,
                "assignment_id": submission.assignment_id,
                "status": submission.status,
                "feedback": submission.feedback or "",
                "reviewed_date": submission.reviewed_date
            }
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_assignment_status API Error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
