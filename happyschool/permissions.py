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


@frappe.whitelist()
def salesperson_opportunity_permission_query(user=None):
    if not user:
        user = frappe.session.user

    # Administrator → all opportunities
    if user == "Administrator":
        return "1=1"

    # HS Sales Manager role → all opportunities
    if "HS Sales Manager" in frappe.get_roles(user):
        return "1=1"

    # Escape user for SQL
    user_escaped = frappe.db.escape(user)

    conditions = []

    # Allow owner of the record
    conditions.append(f"`tabHS Opportunity`.`owner` = {user_escaped}")

    # Check if user is a salesperson
    sales_person = frappe.db.get_value("HS Sales Persons", {"user": user}, "name")
    if sales_person:
        conditions.append(f"`tabHS Opportunity`.`custom_sales_person` = {frappe.db.escape(sales_person)}")

    # Combine conditions with OR
    return " OR ".join(conditions) if conditions else "0=1"
    
@frappe.whitelist()
def lead_user_permission_query(user=None):
    if not user:
        user = frappe.session.user

    # Administrator sees everything
    if user == "Administrator":
        return "1=1"

    # Check if user has HS Sales Manager role
    if "HS Sales Manager" in frappe.get_roles(user):
        return "1=1"

    # Check if user is a Sales Person
    sales_person = frappe.db.get_value("HS Sales Persons", {"user": user}, "name")
    if sales_person:
        # Salesperson can see leads assigned to them
        return f"`tabHS Lead`.`presales_person` = '{sales_person}'"

    # Default: user can only see their own leads
    return f"`tabHS Lead`.`owner` = '{user}'"
