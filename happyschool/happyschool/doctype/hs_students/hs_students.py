# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class HSStudents(Document):
    def autoname(self):
        # This will generate ST001, ST002, ST003...
        self.name = make_autoname("STD.###")
