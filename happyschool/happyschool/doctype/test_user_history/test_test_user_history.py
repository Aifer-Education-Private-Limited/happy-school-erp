# Copyright (c) 2025, esra and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase


class TestTestUserHistory(FrappeTestCase):
	pass

import frappe

from frappe.model.naming import make_autoname

class TestTestUserHistory(frappe.model.document.Document):
    def autoname(self):
        # Only 3 digits instead of 5
        self.name = make_autoname("PST-.YYYY.-.###")