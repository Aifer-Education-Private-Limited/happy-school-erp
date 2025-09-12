import frappe
import json
import base64
from datetime import datetime
from happyschool.utils.oci_storage import upload_pdf_to_oracle

@frappe.whitelist(allow_guest=True)
def submit_assignment(tutor_id, subject, topic, subtopic, material_name):
    """
    API to submit assignments and store them in Materials Doctype
    Accepts multipart/form-data file uploads (no base64).
    Args (in request.form):
        tutor_id: Tutor ID (Link to Tutors)
        subject: Subject name
        topic: Assignment topic
        subtopic: Assignment subtopic
        material_name: Material name
    Files:
        files[]: One or more files to be uploaded
    """
    try:
        # Extract form data
        form = frappe.local.form_dict
        tutor_id = form.get("tutor_id")
        subject = form.get("subject")
        topic = form.get("topic")
        subtopic = form.get("subtopic")
        material_name = form.get("material_name")

        # Extract uploaded files
        uploaded_files = frappe.request.files.getlist("files")
        if not uploaded_files:
            return {"success": False, "error": "No files uploaded"}

        folder_name = frappe.conf.get("oci_materials_folder")
        if not folder_name:
            return {"success": False, "error": "Missing oci_materials_folder in site_config.json"}

        assignment_array = []

        # Loop through each uploaded file
        for f in uploaded_files:
            filename = f.filename
            content = f.read()  # read binary content

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

        # Insert into Materials Doctype
        doc = frappe.get_doc({
            "doctype": "Materials",
            "tutor_id": tutor_id,
            "subject": subject,
            "topic": topic,
            "subtopic": subtopic,
            "material_name": material_name,
            "files": json.dumps(assignment_array),
            "status": 0,
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "assignment": assignment_array}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_assignment error")
        return {"success": False, "error": str(e)}
    