# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class PresalesPerson(Document):
    def autoname(self):
        if self.sales_person_name:
            self.name = frappe.scrub(self.sales_person_name)
