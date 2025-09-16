# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class Parents(Document):
    def autoname(self):
        self.name = make_autoname("PT-.YYYY.-.#####")

# @frappe.whitelist()
# def createparent(parent_id, first_name=None, last_name=None, mobile_number=None):
#     student = frappe.get_doc({
#         "doctype": "Students",
#         "parent_id": parent_id,
#         "first_name": first_name,
#         "last_name": last_name,
#         "mobile_number": mobile_number
#     })
#     student.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return student.name