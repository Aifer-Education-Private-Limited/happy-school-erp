# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class HSLeadSource(Document):
    def autoname(self):
        if self.source:
            self.name = frappe.scrub(self.source)
