# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today
from frappe.utils import formatdate

from frappe.model.naming import make_autoname

class HSLead(Document):
    def autoname(self):
        self.name = make_autoname("HS-.lead-.YYYY.-.###")

    def before_insert(self):
         # Check for duplicate mobile number
        if self.custom_mobile_number:
            exists = frappe.db.exists("HS Lead", {"custom_mobile_number": self.custom_mobile_number})
            if exists:
                frappe.throw(_("A Lead with mobile number {0} already exists").format(self.custom_mobile_number))

        # Set default pipeline values when creating a new lead
        if not self.custom_pipeline_status:
            self.custom_pipeline_status = "Prospect"
        if not self.custom_pipeline_sub_status:
            self.custom_pipeline_sub_status = "Open"

    def before_save(self):

        if self.get("custom_booking") and len(self.custom_booking) > 0:
            # Only set to Assessment Booked if no status is set yet
            if not self.custom_pipeline_status or self.custom_pipeline_status == "Prospect":
                self.custom_pipeline_status = "Assessment Booked"
                self.custom_pipeline_sub_status = ""
        else:
            # Default values for new leads without bookings
            if not self.custom_pipeline_status:
                self.custom_pipeline_status = "Prospect"
            if not self.custom_pipeline_sub_status:
                self.custom_pipeline_sub_status = "Open"


    def on_update(self):
        try:
            old_doc = self.get_doc_before_save()

            if self.presales_person and (
                not old_doc or self.presales_person != old_doc.presales_person
            ):
                sales_person_user = frappe.db.get_value(
                    "HS Sales Persons",
                    self.presales_person,
                    "user"
                )

                if sales_person_user:
                    notif = frappe.get_doc({
                        "doctype": "Notification Log",
                        "for_user": sales_person_user,
                        "subject": f"New Lead Assigned: {self.name}",
                        "email_content": f"You have been assigned a new Lead {self.name}.",
                        "type": "Alert",
                        "document_type": "HS Lead",
                        "document_name": self.name
                    })
                    notif.insert(ignore_permissions=True)
                    frappe.db.commit()  # ensure it is saved immediately

                    # Debug log
                    frappe.logger().info(f"Notification sent to {sales_person_user} for Lead {self.name}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "HS Lead Notification Error")
    

# @frappe.whitelist()
# def validate_salesperson_limit(doc, method):
#     """
#     Validate before saving Lead:
#     A Sales Person cannot be assigned more than 5 slots
#     in a single day (based on Slot Booking creation date).
#     """

#     for row in doc.get("custom_booking") or []:
#         if row.sales_person:
#             # Count how many bookings this salesperson already got today
#             filters = {
#                 "sales_person": row.sales_person,
#                 "DATE(creation)": today()   # check by creation date
#             }

#             # Exclude current doc's rows if updating
#             if doc.name and doc.name != "New Lead":
#                 filters["parent"] = ["!=", doc.name]

#             count = frappe.db.sql("""
#                 SELECT COUNT(*) 
#                 FROM `tabSlot Booking`
#                 WHERE sales_person = %s
#                   AND DATE(creation) = %s
#                   AND parent != %s
#             """, (row.sales_person, today(), doc.name if doc.name else ""), as_list=True)[0][0]

#             # Add this new booking row
#             count += 1

#             if count > 5:
#                 frappe.throw(
#                     f"Sales Person {row.sales_person} already has 5 bookings assigned today. "
#                     "You cannot assign more."
#                 )

@frappe.whitelist()
def check_salesperson_daily_limit(sales_person, parent=None):
    """
    Check if Sales Person already has 5 or more bookings today.
    """
    if not sales_person:
        return {"limit_exceeded": False}

    today_date = today()

    count = frappe.db.sql("""
        SELECT COUNT(*)
        FROM `tabSlot Booking`
        WHERE sales_person = %s
          AND DATE(creation) = %s
          AND (parent != %s OR %s IS NULL)
    """, (sales_person, today_date, parent, parent), as_list=True)[0][0]

    return {"limit_exceeded": count >= 5, "count": count}

@frappe.whitelist()
def create_or_update_opportunity_for_lead(doc, method):
    # Only proceed if child table exists and has at least one row
    if not getattr(doc, "custom_booking", None) or len(doc.custom_booking) == 0:
        return  # Do nothing if no booking added

    # Fetch the latest slot (take the first one here, change logic if needed)
    latest_slot = doc.custom_booking[0]
    slot_date = latest_slot.slot_date
    slot_time = latest_slot.from_time

    formatted_date = formatdate(slot_date, "dd-MM-yyyy") if slot_date else None

    # Check if opportunity already exists for this lead
    opportunity_name = frappe.db.get_value("HS Opportunity", {"custom_lead": doc.name}, "name")

    if opportunity_name:
        # Update existing opportunity
        opportunity = frappe.get_doc("HS Opportunity", opportunity_name)
        opportunity.custom_student_name = doc.custom_student_name
        opportunity.custom_mobile = doc.custom_mobile_number
        opportunity.custom_gradeclass = doc.custom_gradeclass
        opportunity.custom_curriculum = doc.custom_board
        opportunity.custom_sales_person = doc.custom_sales_person
        opportunity.parent_name = doc.first_name
        opportunity.email = doc.email
        opportunity.category=doc.category
        if slot_date or slot_time:
            opportunity.schedule_time = f"{slot_time}"
            opportunity.schedule_date = formatted_date

        opportunity.save(ignore_permissions=True)

    else:
        # Create new opportunity
        opportunity = frappe.get_doc({
            "doctype": "HS Opportunity",
            "custom_lead": doc.name,
            "custom_student_name": doc.custom_student_name,
            "custom_mobile": doc.custom_mobile_number,
            "custom_gradeclass": doc.custom_gradeclass,
            "custom_curriculum": doc.custom_board,
            "custom_sales_person": doc.custom_sales_person,
            "email": doc.email,
            "category":doc.category,
            "parent_name": doc.first_name,
            "schedule_date": formatted_date,
            "schedule_time": f"{slot_time}" if slot_time else None
        })
        opportunity.insert(ignore_permissions=True)



@frappe.whitelist()
def check_salesperson_conflict(sales_person, slot_date, from_time, parent=None, rowname=None):
    """
    Check if the given salesperson is already booked for the same slot_date and time.
    """
    if not (sales_person and slot_date and from_time):
        return {"conflict": False}

    # Check existing rows in Slot Booking child table
    conflict = frappe.db.sql("""
        SELECT parent, name
        FROM `tabSlot Booking`
        WHERE sales_person = %s
          AND slot_date = %s
          AND from_time = %s
          AND parenttype = 'HS Lead'
          AND (parent != %s OR %s IS NULL)
          AND (name != %s OR %s IS NULL)
        LIMIT 1
    """, (sales_person, slot_date,from_time, parent, parent, rowname, rowname))

    return {"conflict": bool(conflict)}

