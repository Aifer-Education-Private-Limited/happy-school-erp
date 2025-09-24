# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname


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

