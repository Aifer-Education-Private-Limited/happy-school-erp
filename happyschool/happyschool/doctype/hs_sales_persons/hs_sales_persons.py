# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname



class HSSalesPersons(Document):
    def autoname(self):
        if self.sales_person:
            self.name = frappe.scrub(self.sales_person)
