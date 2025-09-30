# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname


class Assessment(Document):
    def autoname(self):
        self.name = make_autoname("HS-.ASMT-.YYYY.-.###")

    def after_insert(self):
        """
        After creating an Assessment, link it to the Opportunity.
        """
        if self.opportunity:  # assuming you have a link field to Opportunity
            try:
                frappe.db.set_value(
                    "HS Opportunity",
                    self.opportunity,
                    "assessment",  # the field in Opportunity to store Assessment name
                    self.name
                )
            except Exception as e:
                frappe.log_error(message=str(e), title="Failed to link Assessment to Opportunity")