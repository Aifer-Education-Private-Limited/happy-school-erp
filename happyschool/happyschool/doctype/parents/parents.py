# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class Parents(Document):
    def autoname(self):
        self.name = make_autoname("PT-.YYYY.-.#####")

    def after_insert(self):
        create_customer(self,"after_insert")




@frappe.whitelist()
def create_customer(doc,method):

    full_name = " ".join(filter(None, [doc.first_name, doc.last_name]))

    if frappe.db.exists("Customer", {"custom_parent": doc.name}):
        customer_name = frappe.db.get_value("Customer", {"custom_parent": doc.name}, "name")

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": full_name or doc.name,   
        "customer_group": "Student",              
        "customer_type": "Individual"              
    })
   

    customer.insert(ignore_permissions=True)
    doc.customer = customer.name
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    