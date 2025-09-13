import frappe


from education.education.doctype.student.student import Student

class CustomStudent(Student):
    def validate_user(self):
        # prevent creating User
        return

    def set_missing_customer_details(self):
        # completely skip creating Customer
        return

    def create_customer(self):
        # override to do nothing
        return
