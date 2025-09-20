# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname


class HSOpportunity(Document):
	def autoname(self):
		self.name = make_autoname("HS-.OPP-.YYYY.-.###")
