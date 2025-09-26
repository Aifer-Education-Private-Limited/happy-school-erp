# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import  frappe

class HSStudentAssignments(Document):
	pass

from frappe.model.naming import make_autoname

class HSStudentAssignments(frappe.model.document.Document):
    def autoname(self):
        # Only 3 digits instead of 5
        self.name = make_autoname("HSA-.YYYY.-.###")