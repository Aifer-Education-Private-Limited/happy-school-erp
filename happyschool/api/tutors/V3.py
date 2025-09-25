import frappe
import requests
import mimetypes
import json
from datetime import datetime
from urllib.parse import quote

ORACLE_UPLOAD_URL = frappe.conf.get("ORACLE_UPLOAD_URL")
ORACLE_AUTH_TOKEN = frappe.conf.get("ORACLE_AUTH_TOKEN")
FOLDER_NAME = "Happyschool Student Assignments"  

@frappe.whitelist(allow_guest=True)
def submit_student_assignment():
    """
    Upload student assignments and save entry in Student Assignments doctype.
    Uses Oracle Object Storage REST API (no OCI SDK).
    """
    try:
        # Extract form data
        form = frappe.local.form_dict
        tutor_id = form.get("tutor_id")
        student_id = form.get("student_id")
        assignment_name = form.get("assignment_name")
        subject = form.get("subject")
        description = form.get("description")

        if not tutor_id or not student_id:
            frappe.local.response.update({
                "success": False,
                "message": "Tutor ID and Student ID are required"
            })
            return

        if not frappe.db.exists("Tutors", tutor_id):
            frappe.local.response.update({
                "success": False,
                "message": f"Tutor {tutor_id} not found"
            })
            return

        if not frappe.db.exists("Student", student_id):
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

        assignment_files = []

        for f in uploaded_files:
            filename = f.filename
            content = f.read()

            # Detect file type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Encode folder + filename safely
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
                "file": filename,
                "url": upload_url,
                "type": mime_type
            })

        # Save to Student Assignments doctype
        doc = frappe.get_doc({
            "doctype": "HS Student Assignments",
            "tutor_id": tutor_id,
            "student_id": student_id,
            "assignment_name": assignment_name,
            "subject": subject,
            "description": description,
            "files": json.dumps(assignment_files),
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.local.response.update({
            "success": True,
            "message": "Student Assignment submitted successfully",
            "data": {
                "assignment_id": doc.name,
                "files": assignment_files
            }
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_student_assignment error")
        frappe.local.response.update({
            "success": False,
            "message": str(e)
        })
