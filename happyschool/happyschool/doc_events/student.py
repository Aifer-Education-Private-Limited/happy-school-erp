import frappe

from frappe.model.naming import make_autoname
from education.education.doctype.student.student import Student

class CustomStudent(Student):
    def validate_user(self):
        # prevent creating User
        return
    def autoname(self):
        # Override naming series with STU###
        self.name = make_autoname("STD.###")
        

