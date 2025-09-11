# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime
from frappe.utils import get_datetime

class ParentOrStudentTicket(Document):
    def autoname(self):
        self.name = make_autoname("PST-.YYYY.-.#####")

    def after_insert(self):
        # Convert string to datetime
        creation_datetime = get_datetime(self.creation)
        # Format without microseconds
        formatted_time = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.db_set("creation_time", formatted_time)
		

        try:
            # Assign notification to the first user from role mapping
            role_map = {
                "Content Related": "CRO",
                "Mentor related": "CRO",
                "App related": "CRO",
                "Test related": "CRO",
                "Super Redressal": "CRO",
                "Course validity / extension": "CRO"
            }

            assigned_role = role_map.get(self.subject)
            assigned_user = None

            if assigned_role:
                assigned_users = frappe.get_all("Has Role", filters={"role": assigned_role}, fields=["parent"])
                valid_users = [u.parent for u in assigned_users if u.parent not in ["Administrator", "Guest"]]

                if valid_users:
                    assigned_user = valid_users[0]  # pick first user

            if assigned_user:
                notif = frappe.get_doc({
                    "doctype": "Notification Log",
                    "for_user": assigned_user,  # must be a valid User email
                    "subject": f"New {self.type} ticket- {self.subject}",
                    "email_content": f"You have a new request for {self.subject}.",
                    "type": "Alert",
                    "document_type": "Parent Or Student Ticket",
                    "document_name": self.name
                })
                notif.insert(ignore_permissions=True)
            else:
                frappe.log_error("No valid user found for notification", "Notification Error")

        except Exception:
            frappe.log_error(frappe.get_traceback(), "Error in after_insert Notification")



@frappe.whitelist()
def update_ticket_times(doc, method):
    # If status is Progress, always update Progress Time
    if doc.status == "Progress":
        doc.progress_time = now_datetime()

    # If status is Complete, always update Complete Time
    if doc.status == "Complete":
        doc.complete_time = now_datetime()
