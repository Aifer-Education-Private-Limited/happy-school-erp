# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HSStudentSubmittedAssignments(Document):
	pass

import frappe
from frappe.model.naming import make_autoname

class HSStudentSubmittedAssignments(frappe.model.document.Document):
    def autoname(self):
        self.name = make_autoname("SSA-.YYYY.-.###")