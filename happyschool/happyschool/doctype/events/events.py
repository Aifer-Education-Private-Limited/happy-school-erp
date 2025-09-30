# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Events(Document):
	pass

import frappe 
from frappe.model.naming import make_autoname

class Announcement(frappe.model.document.Document):
    def autoname(self):
        self.name = make_autoname("EVT-.YYYY.-.#####")