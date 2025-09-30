# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class StudentsList(Document):
	pass

from frappe.model.naming import make_autoname

class StudentsList(frappe.model.document.Document):
    def autoname(self):
        self.name = make_autoname("PST-.YY.-.###")
