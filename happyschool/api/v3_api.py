import frappe
from frappe.utils import today, nowdate
import json
from frappe.integrations.utils import create_request_log
from frappe.utils import flt, today

from frappe import _  
@frappe.whitelist(allow_guest=True)
def get_payment_link_details(payment_id):
   
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
                "lead",
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
                "custom_paid",
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
            parent=frappe.db.get_value("Parents",{"mobile_number":link.get("mobile_number")},"name")
            parent_email=frappe.db.get_value("Parents",{"mobile_number":link.get("mobile_number")},"email")
            parent_firstname=frappe.db.get_value("Parents",{"mobile_number":link.get("mobile_number")},"first_name")
            parent_lastname=frappe.db.get_value("Parents",{"mobile_number":link.get("mobile_number")},"last_name")
            student_name=frappe.db.get_value("HS Lead",{"name":link.get("lead")},"custom_student_name")
            grade=frappe.db.get_value("HS Lead",{"name":link.get("lead")},"custom_gradeclass")
            board=frappe.db.get_value("HS Lead",{"name":link.get("lead")},"custom_board")
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
                    "fees": item.get("rate"),
                    "amount": item.get("amount")         # fixed missing comma
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
                "parent_id":parent,
                "payment_id": link.get("name"),
                "mob": link.get("mobile_number"),
                "parent_name": f"{parent_firstname} {parent_lastname}",
                "student_name":student_name,
                "grade":grade,
                "board":board,
                "email": parent_email,
                "total": link.get("total_fees"),
                "grand_total": link.get("grand_total"),
                "offer_applied": link.get("offer_applied"),
                "payment_type": link.get("payment_type"),
                "state": link.get("state"),
                "last_customer_paid":link.get("custom_paid"),
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
def create_program_enrollment():
    from frappe.utils import today
    try:
        data = json.loads(frappe.request.data)
        student_id = data.get("student_id")
        program = data.get("program")

        student = frappe.db.get_value("Student", {"name": student_id}, "name")
        if not student:
            frappe.local.response.update({
                "success": False,
                "message": "Could not find student"
            })
            return
        student_name=frappe.db.get_value("Student",{"name":student_id},"first_name")
        project=frappe.db.get_value("HS Program List",{"program":program},"project")
        program_enrollment = frappe.new_doc("HS Program Enrollment")
        program_enrollment.student = student_id
        program_enrollment.student_name=student_name
        program_enrollment.program = program
        program_enrollment.project=project
        program_enrollment.academic_year = frappe.db.get_single_value('Education Settings', 'current_academic_year')
        program_enrollment.enrollment_date = today()
        program_enrollment.save(ignore_permissions=True)
        frappe.db.commit()


        enroll = {
            "program": program_enrollment.program,
            "student_id": program_enrollment.student,
            "student_name": student_name,
            "academic_year": program_enrollment.academic_year,
            "project": project,
            "enrollment_date": program_enrollment.enrollment_date
            }

        frappe.local.response.update({
            "success": True,
            "message": "Student Enrolled",
            "program_enrollment": enroll
        })
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "program enrollment  error")
        frappe.local.response.update({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        })
        return
    

@frappe.whitelist(allow_guest=True)
def check_program_enrollment():

    data = json.loads(frappe.request.data)
    student_id = data.get("student_id")
    program_name = data.get("program")

    if not student_id or not program_name:
        return {
            "status": "error",
            "message": _("Student Id and program name are required.")
        }

    try:
        student = frappe.db.get_value("Student", {"name": student_id}, "name")

        if not student:
            return {
                "status": "success",
                "exists": False,
                "message": _("No student found with the given stduent id")
            }

        enrollment_exists = frappe.db.exists("HS Program Enrollment", {
            "student": student,
            "program": program_name
        })

        return {
            "status": "success",
            "exists": bool(enrollment_exists)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

@frappe.whitelist(methods=["POST"], allow_guest=True)
def make_fee_payment():
    try:
        data = json.loads(frappe.request.data)
        mobile_no = data.get("mobile_no")
        # mobile_no = format_mobile_number(mobile_no)
        # installment = data.get("installment")
        programs = data.get("programs")
        txn_id = data.get("txn_id")
        type_invoice=data.get("type_invoice")
        discount_in_perc=data.get("discount_perc")
        discount_in_amnt=data.get("discount_amnt")
        # Apply Discount
        amount = data.get("amount")
        if type_invoice != "Happy School":
            return {
                "success": False,
                "error": f"Invalid invoice type '{type_invoice}'."
        }

        # Fetch Student and Customer details
        parent_id = frappe.db.get_value("Parents", {"mobile_number": mobile_no}, "name")
        if not parent_id:
            return {"success": False, "error": "Could not find parent"}

        customer = frappe.db.get_value("Parents", parent_id, "customer")
        template_name = frappe.db.get_value(
            "Sales Taxes and Charges Template",
            {"title":"Output GST In-state"},  # or use "name" field if you know exact
            "name"
        )

        if not template_name:
            frappe.throw("Sales Taxes and Charges Template 'Output GST In-state' not found")


        # Create Sales Invoice
        sales_invoice = frappe.new_doc('Sales Invoice')
        sales_invoice.customer = customer
        sales_invoice.custom_parent = parent_id
        sales_invoice.is_pos = 1
        sales_invoice.additional_discount_percentage = flt(discount_in_perc) if discount_in_perc else 0
        sales_invoice.discount_amount = flt(discount_in_amnt) if discount_in_amnt else 0
        sales_invoice.custom_txn_id = txn_id
        sales_invoice.posting_date = today()
        sales_invoice.taxes_and_charges=template_name
        sales_invoice.custom_type=type_invoice
        sales_invoice.set_taxes()
        
        if programs:
            for prog in programs:
                program_name = prog.get("program")
                qty = flt(prog.get("qty") or 1)

                # Fetch rate from HS Program List
                rate = frappe.db.get_value("HS Program List", {"program": program_name}, "session_rate")
                if rate is None:
                    frappe.throw(f"Program '{program_name}' not found in HS Program List")

                rate = flt(rate)
                amount_val = rate * qty  

                sales_invoice.append("custom_hs_items", {
                    "program": program_name,
                    "qty": qty,
                    "rate": rate,
                    "amount": amount_val
                })



        # Add Fee Item
        sales_invoice.append('items', {
            'item_code': 'OFFER',
            'qty': 1,
            'rate': amount
        })
        # sales_invoice.installment = installment

        # Add Mode of Payment
        sales_invoice.append('payments', {
            "mode_of_payment": "Wire Transfer",
            "amount": flt(data.get("amount")),
            "account": frappe.db.get_value("Mode of Payment Account", {"parent": "Wire Transfer"}, "default_account")
        })

        # **Fetch and Set Lead Source**
        lead_id = frappe.db.get_value("HS Lead", {"custom_mobile_number":mobile_no },"source")
        sales_invoice.custom_lead_source = lead_id  
        frappe.logger().info(f"Lead Source set: {lead_id}")

        
        # Calculate Taxes and Submit
        sales_invoice.submit()

        programs_data = [
            {
                "program": row.program,
                "rate": row.rate,
                "qty": row.qty,
                "amount":row.amount
            }
            for row in sales_invoice.custom_hs_items
        ]

        items_data = [
            {
                "item_code": row.item_code,
                "qty": row.qty,
                "rate": row.rate
            }
            for row in sales_invoice.items
        ]
        doc={
            "id":sales_invoice.name,
            "type":sales_invoice.custom_type,
            "customer":sales_invoice.customer,
            "discount_perc":sales_invoice.additional_discount_percentage,
            "discount_amnt":sales_invoice.discount_amount,
            "programs": programs_data,
            "items":items_data
        }

        return {
            "success":True,
            "details":doc
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(str(frappe.get_traceback()), "Make Fee Payment")
        return {"success": False, "error": str(e)}

        
@frappe.whitelist(methods=["POST"], allow_guest=True)
def make_transactions():
	try:
		data = json.loads(frappe.request.data)
		payment_id = data.get("payment_id")
		razorpay_id = data.get("razorpay_order_id")
		amount = data.get("amount")
		email = data.get("email")
		contact = data.get("contact")
		created_at = data.get("created_at")
		status = data.get("status")

		if not all([payment_id, razorpay_id, amount, email, contact, created_at, status]):
			return {"success": False, "error": "Missing required parameters"}

		if frappe.db.exists('HS Transactions', {'payment_id': payment_id, 'razorpay_order_id': razorpay_id}):
			return {"success": False, "error": "Transaction already exists"}

		transaction = frappe.new_doc('HS Payment Transactions')
		transaction.payment_id = payment_id
		transaction.razorpay_order_id = razorpay_id
		transaction.amount = amount
		transaction.email = email
		transaction.contact = contact
		transaction.created_at = created_at
		transaction.status = status
		transaction.insert(ignore_permissions=True)

		return {
			"success": True,
			"message": "Transaction Created",
			"transaction": transaction.name,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "make_transactions API Error")
		return {
			"success": False,
			"error": str(e),
		}

@frappe.whitelist(allow_guest=True)
def student_course_enrollment():
    try:
        data = json.loads(frappe.request.data)

        parent_id = data.get("parent_id")
        student_id = data.get("student_id")
        program = data.get("program")
        project = data.get("project")
        grade=data.get("grade")
        board=data.get("board")
        program_enrollment_id = data.get("program_enrollment_id")
        date=data.get("program_enroll_date")

        if not student_id or not program:
            return {
                "status": "error",
                "message": "Student and Program are required."
            }

        # Fetch details
        parent_first_name = frappe.db.get_value("Parents", {"name": parent_id}, "first_name") or ""
        parent_last_name = frappe.db.get_value("Parents", {"name": parent_id}, "last_name") or ""
        parent_name = f"{parent_first_name} {parent_last_name}".strip()
        student_name = frappe.db.get_value("Student", {"name": student_id}, "first_name")
        mobile=frappe.db.get_value("Parents",{"name":parent_id},"mobile_number")
        email=frappe.db.get_value("Parents",{"name":parent_id},"email")

        # 🔹 Step 1: Check if a Student Course Enrollment already exists
        existing_enrollment = frappe.db.get_value(
            "HS Student Course Enrollment", {"student": student_id}, "name"
        )

        if existing_enrollment:
            # 🔹 Step 2: Load existing document and append child row
            enrollment_doc = frappe.get_doc("HS Student Course Enrollment", existing_enrollment)
            enrollment_doc.append("enrolled_programs", {
                "program_enrollment": program_enrollment_id,
                "program": program,
                "project": project,
                "date":date
            })
            enrollment_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "success",
                "message": "Program added to existing student enrollment.",
                "enrollment_id": enrollment_doc.name,
                "program_enrollment_id": program_enrollment_id
            }

        else:
            # 🔹 Step 3: Create new Student Course Enrollment
            new_doc = frappe.new_doc("HS Student Course Enrollment")
            new_doc.parent1=parent_id
            new_doc.student = student_id
            new_doc.mobile=mobile
            new_doc.email=email
            new_doc.grade=grade
            new_doc.board=board
            new_doc.posting_date=today()
            new_doc.student_name = student_name
            new_doc.parent = parent_id
            new_doc.parent_name = parent_name
            new_doc.status = "Active"

            new_doc.append("enrolled_programs", {
                "program_enrollment": program_enrollment_id,
                "program": program,
                "project": project,
                "date":date
            })

            new_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "success",
                "message": "New student course enrollment created.",
                "enrollment_id": new_doc.name,
                "program_enrollment_id": program_enrollment_id
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "student_course_enrollment API Error")
        return {
            "status": "error",
            "message": str(e)
        }
