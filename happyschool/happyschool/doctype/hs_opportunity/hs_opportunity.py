# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname
from frappe.core.doctype.communication.email import make



class HSOpportunity(Document):
	def autoname(self):
		self.name = make_autoname("HS-.OPP-.YYYY.-.###")

	def after_insert(doc):
		try:
			if doc.custom_lead:
				lead = frappe.get_doc("HS Lead", doc.custom_lead)

				if lead.custom_sales_person:
					sales_person_user = frappe.db.get_value(
						"HS Sales Persons", lead.custom_sales_person, "user"
					)

					if sales_person_user:
						notif = frappe.get_doc({
							"doctype": "Notification Log",
							"for_user": sales_person_user,
							"subject": f"New Opportunity Assigned: {doc.name}",
							"email_content": f"You have been assigned a new opportunity from lead {lead.name}.",
							"type": "Alert",
							"document_type": "HS Opportunity",
							"document_name": doc.name
						})
						notif.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "HS Opportunity Notification Error")



import frappe

import frappe

@frappe.whitelist()
def send_assessment_email(docname, meet_link, schedule_time):
    doc = frappe.get_doc("HS Opportunity", docname)

    if not doc.email:
        frappe.throw("No email set for this Opportunity!")

    subject = "Assessment Session for Your Child"

    # HTML Email Template
    message = f"""
		<p>Dear Parent,</p>

		<p>We are happy to inform you that we are ready to conduct the assessment session for your child. Kindly use the link below to join the session at the scheduled time.</p>

		<p>
			Google Meet Link: <a href="{meet_link}">{meet_link}</a>
		</p>

		<p><strong>Scheduled Time:</strong> {schedule_time}</p>

		<p>If you have any questions or need assistance, feel free to reach out.</p>

		"""

    # Send email
    frappe.sendmail(
        recipients=doc.email,
        subject=subject,
        message=message,
        reference_doctype="HS Opportunity",
        reference_name=docname
    )
