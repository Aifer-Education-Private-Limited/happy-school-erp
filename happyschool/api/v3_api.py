import frappe
from frappe.utils import today, nowdate

@frappe.whitelist(allow_guest=True)
def get_payment_link_details(mobile=None):
    """
    API to fetch Payment Link details along with child tables 'items' and 'fees_structure'.
    Show discount fields only if offer_applied is True.
    """
    try:
        if not mobile:
            frappe.local.response.update({
                "success": False,
                "message": "Mobile number is required."
            })
            return

        payment_links = frappe.get_all(
            "HS Payment Link",  # removed extra space
            filters={"mobile_number": mobile},
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
#         mobile_no = format_mobile_number(mobile_no)
#         program = data.get("program")
#         installment = data.get("installment")
#         discount_name = data.get("discount_name")
#         discount_code = data.get("discount_code")
#         txn_id = data.get("txn_id")

#         # Fetch Student and Customer details
#         parent_id = frappe.db.get_value("Parents", {"mobile_number": mobile_no}, "name")
#         if not parent_id:
#             return {"success": False, "error": "Could not find student"}

#         customer = frappe.db.get_value("Parents", parent_id, "customer")

#         if not frappe.db.get_value("Fees", {
#             "student": student_id,
#             "docstatus": 1,
#             "outstanding_amount": [">", 0]
#         }):
#             return {"success": False, "error": "Could not find unpaid student"}

#         # Create Sales Invoice
#         sales_invoice = frappe.new_doc('Sales Invoice')
#         sales_invoice.customer = customer
#         sales_invoice.student = student_id
#         sales_invoice.program = program
#         sales_invoice.is_pos = 1
#         sales_invoice.txn_id = txn_id
#         sales_invoice.posting_date = today()

#         # Apply Discount
#         amount = data.get("amount")
#         if discount_code:
#             sales_invoice.discount_name = discount_name if discount_name else frappe.db.get_value("Fee Structure Discount",{"parent": frappe.db.get_value("Fee Structure", {'program': program, "docstatus": 1, "default": True}),"code": discount_code},"discount_name")
#             discount_percentage = flt(frappe.db.get_value(
#                 "Fee Structure Discount",
#                 {
#                     "parent": frappe.db.get_value("Fee Structure", {'program': program, "docstatus": 1, "default": True}),
#                     "code": discount_code
#                 },
#                 "discount_percentage")
#             )
#             if discount_percentage:
#                 amount = flt(amount / (1 - (discount_percentage / 100)))
#                 sales_invoice.apply_discount_on = "Net Total"
#                 sales_invoice.additional_discount_percentage = flt(discount_percentage)
#                 sales_invoice._discount_applied = discount_code

#         if program:
#             label = frappe.db.get_value("Program", {"name": program}, "label")
#             sales_invoice.label = label


#         # Add Fee Item
#         sales_invoice.append('items', {
#             'item_code': 'FEES',
#             'description': f"{program} {installment}",
#             'qty': 1,
#             'rate': amount
#         })
#         sales_invoice.installment = installment

#         # Assign Sales Person
#         sales_person = get_student_sales_person(mobile_no)
#         if sales_person:
#             sales_invoice.append('sales_team', {
#                 "sales_person": sales_person,
#                 "allocated_percentage": 100
#             })

#         # Add Mode of Payment
#         sales_invoice.append('payments', {
#             "mode_of_payment": "Wire Transfer",
#             "amount": flt(data.get("amount")),
#             "account": frappe.db.get_value("Mode of Payment Account", {"parent": "Wire Transfer"}, "default_account")
#         })

#         # **Fetch and Set Lead Source**
#         lead_id = frappe.db.get_value("Student", {"name": student_id}, "lead")
#         if lead_id:
#             lead_source = frappe.db.get_value("Lead", lead_id, "source")
#             if lead_source:
#                 sales_invoice.lead_source = lead_source  # Set the lead source
#                 frappe.logger().info(f"Lead Source set: {lead_source}")

#             new_source = frappe.db.get_value("Lead", lead_id, "new_source")
#             if new_source:
#                 sales_invoice.new_source = new_source  # Set the lead source
#                 frappe.logger().info(f"New Source set: {new_source}")

#         program_fees = frappe.db.get_value("Fee Structure", {"default": 1, "program": program}, "total_amount")
#         if program_fees:
#             sales_invoice.program_fees = program_fees
#             frappe.logger().info(f"Program Fees set: {program_fees}")


#         # Calculate Taxes and Submit
#         sales_invoice.set_missing_values()
#         sales_invoice.calculate_taxes_and_totals()
#         sales_invoice.submit()

#         return download_pdf(sales_invoice.doctype, sales_invoice.name)

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(str(frappe.get_traceback()), "Make Fee Payment")
#         create_request_log(
#             data=json.loads(frappe.request.data),
#             request_description="Make Fee Payment",
#             service_name="Aifer",
#             request_headers=frappe.request.headers,
#             error=str(e),
#             status="Failed"
#         )
#         return {"success": False, "error": str(e)}

# def format_mobile_number(number):
# 	try:
# 		import phonenumbers
# 		parsed_number = phonenumbers.parse(number)
# 		country_code = parsed_number.country_code
# 		number = re.sub('[^0-9]', '', number)
# 		if country_code:
# 			number = number.replace(str(country_code),'',1)
# 			return f"+{country_code}-{number}"
# 	except Exception as e:
# 		frappe.throw(_("Missing Country Code"))
