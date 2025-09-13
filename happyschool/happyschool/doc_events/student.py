import frappe


from education.education.doctype.student.student import Student

class CustomStudent(Student):
    def validate_user(self):
        # prevent creating User
        return
        