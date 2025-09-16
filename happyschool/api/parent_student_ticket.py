import frappe
import json
from frappe.desk.form.assign_to import add as assign_to
from datetime import datetime
from frappe.utils import get_datetime
from frappe.desk.form.assign_to import add as assign_to
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def ticket():
    """Method to create a ticket and assign it to all users with relevant roles"""
    try:

        category = frappe.form_dict.get('category')
        parent_id=frappe.form_dict.get('parent_id')
        studentId=frappe.form_dict.get('studentId')
        course = frappe.form_dict.get('course')
        description = frappe.form_dict.get('description')
        uid=frappe.form_dict.get('uid')

        
        student_doc = frappe.db.get_value("Student", {"name": studentId}, ["name", "first_name"], as_dict=True)
        parent_doc = frappe.db.get_value("Parents", {"name": parent_id}, ["name", "first_name"], as_dict=True)

        student_id = student_doc.name if student_doc else None
        student_name = student_doc.first_name if student_doc else None
        parent_db_id = parent_doc.name if parent_doc else None
        parent_name = parent_doc.first_name if parent_doc else None



        
        if not category:
            frappe.local.response.update({
                "success": False,
                "message": {"error": "Category and mobile are required."},
                "http_status_code": 400
            })
            return

        if not student_id and not parent_db_id:
            frappe.local.response.update({
                "success": False,
                "message": "Neither a valid Student nor Parent found",
                "http_status_code": 400
            })
            return



        ticket = frappe.new_doc('Parent Or Student Ticket')
        ticket.subject = category
        ticket.parentid=parent_id
        ticket.studentid=studentId
        ticket.student_course = course

        ticket.status = "Open"
        ticket.description = description

        if student_id:
            ticket.student = student_id
        elif parent_db_id:
            ticket.parent1 = parent_db_id

        ticket.save(ignore_permissions=True)
        frappe.db.commit()
        role_map = {
            "Content Related": "CRO",
            "Mentor related": "CRO",
            "App related": "CRO",
            "Test related": "CRO",
            "Super Redressal": "CRO",
            "Course validity / extension": "CRO"
        }

        assigned_role = role_map.get(category)


        if assigned_role:
            assigned_users = frappe.get_all("Has Role", filters={"role": assigned_role}, fields=["parent"])
            user_list = [u.parent for u in assigned_users if u.parent not in ["Administrator", "Guest"]]


            valid_users = [u for u in user_list if frappe.db.exists("User", u)]


            if valid_users:

                assign_to({
                    "assign_to": valid_users,
                    "doctype": "Parent Or Student Ticket",
                    "name": ticket.name,
                    "assigned_by": student_name or parent_name
                })

            else:
                frappe.log_error(f"No valid users found for role {assigned_role}", "Ticket Assignment Warning")
        else:
            frappe.log_error(f"No role mapping found for category {category}", "Ticket Assignment Warning")


        creation_time = get_datetime(ticket.creation)
        formatted_creation = creation_time.strftime("%Y-%m-%d %H:%M")


        ticket_details = {
            "ticket_id": ticket.name,
            "category": ticket.subject,
        
            "course": ticket.student_course,
            "status": ticket.status,

            "description": ticket.description,
            "creation": formatted_creation
        }

        frappe.local.response.update({
            "message": {
                "msg": f"Ticket {ticket.name} created successfully.",
                "Ticket Details": ticket_details
            },
            "success": True,
            "http_status_code": 200
        })

    except Exception:
        frappe.log_error(title="Ticket API Error", message=frappe.get_traceback())
        frappe.local.response.update({
            "success": False,
            "message": {"error": frappe.get_traceback()},
            "http_status_code": 500
        })


@frappe.whitelist(allow_guest=True)
def get_ticket():
    try:
        parent_id = frappe.form_dict.get("parent_id")
        student_id = frappe.form_dict.get("studentId")

        filters = {}
        if parent_id:
            filters["parentid"] = parent_id   # ✅ use the exact fieldname from doctype
        elif student_id:
            filters["studentid"] = student_id # ✅ use the exact fieldname from doctype
        else:
            frappe.local.response.update({
                "success": False,
                "message": "Please provide either parent_id or studentId"
            })
            return

        tickets = frappe.get_all(
            "Parent Or Student Ticket",
            filters=filters,
            fields=[
                "name", "subject", "student", "student_course", "status",
                "description", "creation", "modified", "type",
                "progress_time", "complete_time",
                "progress_comment", "complete_comment",
                "parentid", "studentid"   # ✅ must match DB fieldnames
            ],
            order_by="creation desc"
        )

        if not tickets:
            frappe.local.response.update({
                "success": False,
                "message": "No tickets found"
            })
            return

        frappe.local.response.update({
            "success": True,
            "tickets": [
                {
                    "ticket_id": t.name,
                    "category": t.subject,
                    "course": t.student_course,
                    "status": t.status,
                    "description": t.description,
                    "progress_comment": t.progress_comment,
                    "complete": t.complete_comment,
                    "creation": t.creation,
                    "progress_time": t.progress_time or "",
                    "complete_time": t.complete_time or ""
                    
                }
                for t in tickets
            ]
        })
        return

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Get Ticket API Error")
        frappe.local.response.update({
            "success": False,
            "message": frappe.get_traceback()
        })
        return
