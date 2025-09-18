# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class StdAttendance(Document):
	pass

from frappe.model.naming import make_autoname

class StdAttendance(frappe.model.document.Document):
    def autoname(self):
        self.name = make_autoname("PST-.YYYY.-.#####")