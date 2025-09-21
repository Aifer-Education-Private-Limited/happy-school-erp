import frappe
from frappe.utils import today, nowdate
import json
from frappe.utils import flt, today

from frappe import _  
@frappe.whitelist(allow_guest=True)
def get_payment_link_details(payment_id):
    """
    API to fetch Payment Link details along with child tables 'items' and 'fees_structure'.
    Show discount fields only if offer_applied is True.
    """
    try:
        if not payment_id:
            frappe.local.response.update({
                "success": False,
                "message": "payment id is required."
            })
            return

        payment_links = frappe.get_all(
            "HS Payment Link",  # removed extra space
            filters={"name": payment_id},
            fields=[
                "name",
                "customer_name",
                "mobile_number",
                "email_id",
                "total_fees",
                "state",
                "date",
                "grand_total",
                "discount_perc",
                "discount_amnt",
                "offer_applied",
                "payment_type",

                "payment_link"
            ],
            order_by="creation desc"
        )

        if not payment_links:
            frappe.local.response.update({
                "success": False,
                "message": "No Payment Link found."
            })
            return

        result = []
        for link in payment_links:
            # Fetch items child table
            items = frappe.get_all(
                "Payment Link Items",
                filters={"parent": link["name"], "parentfield": "items"},
                fields=["program", "qty", "rate", "amount"]
            )

            mapped_items = [
                {
                    "program": item.get("program"),
                    "qty": item.get("qty"),
                    "fees": item.get("rate")  # fixed missing comma
                } for item in items
            ]

            # Fetch fees_structure child table
            fees_structure = frappe.get_all(
                "HS Fees Structure",
                filters={"parent": link["name"], "parentfield": "fess_structure"},
                fields=["date", "customer_paid", "balance_amount"]
            )

            mapped_fees_structure = [
                {
                    "date": fs.get("date"),
                    "customer_paid": fs.get("customer_paid"),
                    "balance_amount": fs.get("balance_amount")
                } for fs in fees_structure
            ]

            mapped_link = {
                "payment_id": link.get("name"),
                "mob": link.get("mobile_number"),
                "name": link.get("customer_name"),
                "email": link.get("email_id"),
                "total": link.get("total_fees"),
                "grand_total": link.get("grand_total"),
                "offer_applied": link.get("offer_applied"),
                "payment_type": link.get("payment_type"),
                "state": link.get("state"),
                "payment_link": link.get("payment_link"),
                "items": mapped_items,
                "fees_structure": mapped_fees_structure
            }

            if str(link.get("offer_applied")).lower() in ["1", "true", "yes"]:
                mapped_link.update({
                    "discount_in_perc": link.get("discount_perc"),
                    "discount_in_amnt": link.get("discount_amnt"),
                })

            result.append(mapped_link)

        frappe.local.response.update({
            "success": True,
            "message": "Payment Link fetched successfully.",
            "data": result
        })
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payment_link_details error")
        frappe.local.response.update({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        })
        return

@frappe.whitelist(allow_guest=True)
def create_program_enrollment(student_id, program, academic_year):
    try:
        if not student_id:
            frappe.local.response.update({
                "success": False,
                "message": "Student_id is required"
            })
            return
        if not program:
            frappe.local.response.update({
                "success": False,
                "message": "Program is required."
            })
            return
        if not academic_year:
            frappe.local.response.update({
                "success": False,
                "message": "Academic year is required."
            })
            return
        if not frappe.db.exists("Student", {"name": student_id}):
            frappe.local.response.update({
                "success": False,
                "message": f"{student_id} not found"
            })
            return
        if not frappe.db.exists("Program", {"name": program}):
            frappe.local.response.update({
                "success": False,
                "message": f"{program} not found"
            })
            return
        if not frappe.db.exists("Academic Year", {"name": academic_year}):
            frappe.local.response.update({
                "success": False,
                "message": f"{academic_year} not found"
            })
            return

        existing = frappe.db.exists(
            "Program Enrollment",
            {
                "student": student_id,
                "program": program,
                "academic_year": academic_year
            }
        )
        if existing:
            frappe.local.response.update({
                "success": False,
                "message": "Student is already enrolled in this program and academic year"
            })
            return

        todays_date = nowdate()
        doc = frappe.new_doc("Program Enrollment")
        doc.student = student_id
        doc.program = program
        doc.academic_year = academic_year
        doc.enrollment_date = todays_date
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        enrollment_details = {
            "student_name": doc.student_name,
            "program": doc.program,
            "academic_year": doc.academic_year,
            "enrollment_date": doc.enrollment_date
        }

        frappe.local.response.update({
            "success": True,
            "message": "Created program enrollment successfully",
            "enrollments": enrollment_details
        })
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Program Enrollment Creation Error")
        frappe.local.response.update({
            "success": False,
            "message": "Internal server error"
        })

# @frappe.whitelist(methods=["POST"], allow_guest=True)
# def make_fee_payment():
#     try:
#         data = json.loads(frappe.request.data)
#         mobile_no = data.get("mobile_no")
#         # mobile_no = format_mobile_number(mobile_no)
#         # installment = data.get("installment")
#         programs = data.get("programs")
#         txn_id = data.get("txn_id")
#         type_invoice=data.get("type")
#         discount_in_perc=data.get("discount_perc")
#         discount_in_amnt=data.get("discount_amnt")
#         # Apply Discount
#         amount = data.get("amount")

#         # Fetch Student and Customer details
#         parent_id = frappe.db.get_value("Parents", {"mobile_number": mobile_no}, "name")
#         if not parent_id:
#             return {"success": False, "error": "Could not find student"}

#         customer = frappe.db.get_value("Parents", parent_id, "customer")

        
#         # Create Sales Invoice
#         sales_invoice = frappe.new_doc('Sales Invoice')
#         sales_invoice.customer = customer
#         sales_invoice.custom_parent = parent_id
#         sales_invoice.is_pos = 1
#         sales_invoice.additional_discount_percentage=discount_in_perc
#         sales_invoice.discount_amount=discount_in_amnt
#         sales_invoice.custom_txn_id = txn_id
#         sales_invoice.posting_date = today()
#         sales_invoice.custom_type=type_invoice
        
#         if programs:
#             for prog in programs:
#                 sales_invoice.append("custom_hs_program", {
#                     "program": prog.get("program"),
#                     "qty": prog.get("qty") or 1,
#                     "rate": flt(prog.get("rate")) or 0
#                 })

#         # Add Fee Item
#         sales_invoice.append('items', {
#             'item_code': 'FEES',
#             'qty': 1,
#             'rate': amount
#         })
#         # sales_invoice.installment = installment

#         # Add Mode of Payment
#         # sales_invoice.append('payments', {
#         #     "mode_of_payment": "Wire Transfer",
#         #     "amount": flt(data.get("amount")),
#         #     "account": frappe.db.get_value("Mode of Payment Account", {"parent": "Wire Transfer"}, "default_account")
#         # })

#         # **Fetch and Set Lead Source**
#         lead_id = frappe.db.get_value("Parents", {"name": parent_id}, "lead_id")
#         if lead_id:
#             lead_source = frappe.db.get_value("HS Lead", lead_id, "source")
#             if lead_source:
#                 sales_invoice.custom_lead_source = lead_source  # Set the lead source
#                 frappe.logger().info(f"Lead Source set: {lead_source}")

        
#         # Calculate Taxes and Submit
#         sales_invoice.submit()
#         doc={
#             "id":sales_invoice.name,
#             "type":sales_invoice.custom_type,
#             "customer":sales_invoice.customer,
#             "discount":sales_invoice.additional_discount_percentage,
#             "programs":sales_invoice.custom_hs_program,
#             "items":sales_invoice.items
#         }

#         return {
#             "success":True,
#             "details":doc
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(str(frappe.get_traceback()), "Make Fee Payment")
#         return {"success": False, "error": str(e)}

        
# def format_mobile_number(number):
#     try:
#         parsed_number = phonenumbers.parse(number)
#         country_code = parsed_number.country_code
#         number = re.sub('[^0-9]', '', number)
#         if country_code:
#             number = number.replace(str(country_code),'',1)
#             return f"+{country_code}-{number}"
#     except Exception as e:
#         frappe.throw(_("Missing Country Code"))
