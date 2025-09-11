import frappe
from frappe.utils import today


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





# import frappe

# @frappe.whitelist()
# def update_salesperson_from_child(lead_name):
#     """
#     Take first sales_person from child table (custom_booking)
#     and set it in parent sales_person field.
#     """
#     lead = frappe.get_doc("Lead", lead_name)

#     if lead.custom_booking and lead.custom_booking[0].sales_person:
#         lead.sales_person = lead.custom_booking[0].sales_person
#         lead.save(ignore_permissions=True)
#         frappe.db.commit()
#         return {"status": "success", "sales_person": lead.sales_person}
    
#     return {"status": "failed", "message": "No sales_person found in child table"}
