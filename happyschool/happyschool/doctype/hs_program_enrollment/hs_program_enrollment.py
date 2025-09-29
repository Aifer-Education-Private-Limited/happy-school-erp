# Copyright (c) 2025, esra and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today
from frappe.model.naming import make_autoname

class HSProgramEnrollment(Document):
	def autoname(self):
		self.name = make_autoname("HS-.ENR-.YYYY.-.###")