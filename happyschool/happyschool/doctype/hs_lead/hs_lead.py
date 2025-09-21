# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname

class HSLead(Document):
	def autoname(self):
		self.name = make_autoname("HS-.lead-.YYYY.-.###")
		





@frappe.whitelist()
def validate_salesperson_limit(doc, method):
    """
    Validate before saving Lead:
    A Sales Person cannot be assigned more than 5 slots
    in a single day (based on Slot Booking creation date).
    """

    for row in doc.get("custom_booking") or []:
        if row.sales_person:
            # Count how many bookings this salesperson already got today
            filters = {
                "sales_person": row.sales_person,
                "DATE(creation)": today()   # check by creation date
            }

            # Exclude current doc's rows if updating
            if doc.name and doc.name != "New Lead":
                filters["parent"] = ["!=", doc.name]

            count = frappe.db.sql("""
                SELECT COUNT(*) 
                FROM `tabSlot Booking`
                WHERE sales_person = %s
                  AND DATE(creation) = %s
                  AND parent != %s
            """, (row.sales_person, today(), doc.name if doc.name else ""), as_list=True)[0][0]

            # Add this new booking row
            count += 1

            if count > 5:
                frappe.throw(
                    f"Sales Person {row.sales_person} already has 5 bookings assigned today. "
                    "You cannot assign more."
                )

@frappe.whitelist()
def create_opportunity_for_lead(doc, method):
    opportunity = frappe.get_doc({
        "doctype": "HS Opportunity",

        # --- Required standard fields ---

        # --- Custom fields ---
        "custom_lead": doc.name,
        "custom_student_name": doc.custom_student_name,
        "custom_mobile": doc.custom_mobile_number,
        "custom_gradeclass": doc.custom_gradeclass,
        "custom_curriculum": doc.custom_board,
        "custom_sales_person": doc.custom_sales_person,
		"parent_name":doc.first_name
    })

    opportunity.insert(ignore_permissions=True)
