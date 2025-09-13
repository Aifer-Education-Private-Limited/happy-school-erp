import frappe
import json
import base64
from datetime import datetime
from happyschool.utils.oci_storage import upload_pdf_to_oracle

@frappe.whitelist(allow_guest=True)
def submit_materials(tutor_id, subject, topic, subtopic, material_name):

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
          
            "submitted_date": datetime.now()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "assignment": assignment_array}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "submit_assignment error")
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
