import frappe

def get_context(context):
    # If user is not logged in, redirect to login page
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # If logged in, pass user details to template
    context.title = "Secure Page"
    context.username = frappe.session.user
    context.fullname = frappe.db.get_value("User", frappe.session.user, "full_name")


@frappe.whitelist()
def add_demo_url(url):
    check_user = frappe.db.get_value("Tutor Profile", {"user": frappe.session.user})
    if not check_user:
        frappe.throw("Please complete your Tutor Profile before adding a demo URL.")
    tutor_profile = frappe.get_doc("Tutor Profile", check_user)
    tutor_profile.demo_url = url
    tutor_profile.status = "Interview Pending"
    tutor_profile.save(ignore_permissions=True)

@frappe.whitelist()
def get_existing_demo_url():
    tu_pro = frappe.get_doc("Tutor Profile", {"user": frappe.session.user})
    if not tu_pro.demo_url:
        return None
    return tu_pro.demo_url

@frappe.whitelist()
def get_tutor_status():
    tutor_profile = frappe.get_doc("Tutor Profile", {"user": frappe.session.user})
    return tutor_profile.status