# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TestUserAnswers(Document):
	pass

import frappe

from frappe.model.naming import make_autoname

class TestUserAnswers(frappe.model.document.Document):
    def autoname(self):
        # Only 3 digits instead of 5
        self.name = make_autoname("PST-.YYYY.-.###")