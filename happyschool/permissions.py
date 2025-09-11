import frappe
from frappe.utils.user import get_users_with_role


@frappe.whitelist()
def parent_student_ticket_permission_query(user=None):
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return "1=1"  # Admin sees all

    # Escape to avoid SQL injection
    user = frappe.db.escape(user)

    conditions = []

    # Owner condition
    conditions.append(f"`tabParent Or Student Ticket`.`owner` = {user}")

    # Assigned in ToDo (main access control)
    conditions.append(f"""
        EXISTS(
            SELECT 1 FROM `tabToDo`
            WHERE `tabToDo`.`reference_type` = 'Parent Or Student Ticket'
              AND `tabToDo`.`reference_name` = `tabParent Or Student Ticket`.`name`
              AND `tabToDo`.`allocated_to` = {user}
        )
    """)

    # In Notification Log (optional)
    conditions.append(f"""
        EXISTS(
            SELECT 1 FROM `tabNotification Log`
            WHERE `tabNotification Log`.`document_type` = 'Parent Or Student Ticket'
              AND `tabNotification Log`.`document_name` = `tabParent Or Student Ticket`.`name`
              AND `tabNotification Log`.`for_user` = {user}
        )
    """)

    return " OR ".join(conditions)

