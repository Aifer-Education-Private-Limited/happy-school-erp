app_name = "happyschool"
app_title = "happyschool"
app_publisher = "esra"
app_description = "happyschool"
app_email = "esrathanoona@gmail.com"
app_license = "unlicense"





# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "happyschool",
# 		"logo": "/assets/happyschool/logo.png",
# 		"title": "happyschool",
# 		"route": "/happyschool",
# 		"has_permission": "happyschool.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/happyschool/css/happyschool.css"
# app_include_js = "/assets/happyschool/js/happyschool.js"

# include js, css files in header of web template
# web_include_css = "/assets/happyschool/css/happyschool.css"
# web_include_js = "/assets/happyschool/js/happyschool.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "happyschool/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "happyschool/public/icons.svg"



permission_query_conditions = {
    "Parent Or Student Ticket":"happyschool.permissions.parent_student_ticket_permission_query"
}


doctype_js={
    "Lead": "public/js/lead.js",
    "Opportunity":"public/js/opportunity.js",
    "Quotation":"public/js/quotation.js"
    }


doc_events={
    "Lead": {
        "validate": "happyschool.happyschool.doc_events.lead.validate_salesperson_limit",
        "after_insert":"happyschool.happyschool.doc_events.lead.create_opportunity_for_lead"
    },
    "Parent Or Student Ticket":{
        "validate":"happyschool.happyschool.doctype.parent_or_student_ticket.parent_or_student_ticket.update_ticket_times"
    },
    # "Opportunity":{
    #     "before_save":"happyschool.happyschool.doc_events.opportunity.fetch_item_rate"
    # }
    # "Parents":{
    #     "after_insert":"happyschool.happyschool.doctype.parents.parents.createparent"
    # }
}
override_doctype_class={
     "Student":"happyschool.happyschool.doc_events.student.CustomStudent"
}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "happyschool.utils.jinja_methods",
# 	"filters": "happyschool.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "happyschool.install.before_install"
# after_install = "happyschool.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "happyschool.uninstall.before_uninstall"
# after_uninstall = "happyschool.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "happyschool.utils.before_app_install"
# after_app_install = "happyschool.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "happyschool.utils.before_app_uninstall"
# after_app_uninstall = "happyschool.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "happyschool.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"happyschool.tasks.all"
# 	],
# 	"daily": [
# 		"happyschool.tasks.daily"
# 	],
# 	"hourly": [
# 		"happyschool.tasks.hourly"
# 	],
# 	"weekly": [
# 		"happyschool.tasks.weekly"
# 	],
# 	"monthly": [
# 		"happyschool.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "happyschool.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "happyschool.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "happyschool.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["happyschool.utils.before_request"]
# after_request = ["happyschool.utils.after_request"]

# Job Events
# ----------
# before_job = ["happyschool.utils.before_job"]
# after_job = ["happyschool.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"happyschool.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

