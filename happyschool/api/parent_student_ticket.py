import frappe
import json
from frappe.desk.form.assign_to import add as assign_to
from datetime import datetime
from frappe.utils import get_datetime
from frappe.desk.form.assign_to import add as assign_to
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def ticket(mobile):
    """Method to create a ticket and assign it to all users with relevant roles"""
    try:

        category = frappe.form_dict.get('category')
        ticket_type = frappe.form_dict.get('type')
        course = frappe.form_dict.get('course')
        description = frappe.form_dict.get('description')
        uid=frappe.form_dict.get('uid')

        
        student = frappe.db.get_value("Students", {"mobile": mobile}, ["name", "student_name"], as_dict=True)
        parent = frappe.db.get_value("Parents", {"mobile_number": mobile}, ["name", "first_name"], as_dict=True)

        student_id = student.name if student else None
        student_name = student.student_name if student else None
        parent_id = parent.name if parent else None
        parent_name = parent.first_name if parent else None



        
        if not category or not mobile:
            frappe.local.response.update({
                "success": False,
                "message": {"error": "Category and mobile are required."},
                "http_status_code": 400
            })
            return

        if ticket_type == "Student" and not student_id:
            frappe.local.response.update({
                "success": False,
                "message": "Student not found",
                "http_status_code": 400
            })
            return

        # If type is Parent but no parent found
        if ticket_type == "Parent" and not parent_id:
            frappe.local.response.update({
                "success": False,
                "message": "Parent not found",
                "http_status_code": 400
            })
            return

        ticket = frappe.new_doc('Parent Or Student Ticket')
        ticket.subject = category
        ticket.type=ticket_type
        ticket.user_id = uid
        ticket.student_course = course
        ticket.mobile = mobile
        ticket.status = "Open"
        ticket.description = description

        if ticket_type == "Student":
            ticket.student = student_id
        elif ticket_type == "Parent":
            ticket.parent1= parent_id

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
            "type":ticket.type,
            "uid": ticket.user_id,
            "course": ticket.student_course,
            "status": ticket.status,
            "mobile": ticket.mobile,
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
def get_ticket(uid):
    try:
        # Fetch all tickets for the given uid, ordered by creation desc
        tickets = frappe.get_all(
            "Parent Or Student Ticket",
            filters={"user_id": uid},
            fields=["name", "subject", "student", "student_course", "status", "description", "creation", "modified","type",
            "progress_time","complete_time","progress_comment","complete_comment"],
            order_by="creation desc"
        )

        if not tickets:
            return {
                "success": False,
                "message": f"No tickets found for uid: {uid}"
            }

        return {
            "success": True,
            "tickets": [
                {
                    "ticket_id": t.name,
                    "category": t.subject,
                    "type":t.type,
                    "course": t.student_course,
                    "status": t.status,
                    "description": t.description,
                    "progress_comment":t.progress_comment,
                    "complete":t.complete_comment,
                    "creation": t.creation,
                    "progress_time": t.progress_time or "" ,
                    "complete_time": t.complete_time or ""
                }
                for t in tickets
            ]
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Get Ticket API Error")
        return {
            "success": False,
            "message": frappe.get_traceback()
        }
