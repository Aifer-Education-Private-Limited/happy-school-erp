import frappe

import frappe

# @frappe.whitelist()
# def fetch_item_rate(doc, method):
#     for row in doc.items:
#         if row.item_code:
#             rate = frappe.db.get_value(
#                 "Item Price",
#                 {"item_code": row.item_code},
#                 "price_list_rate"
#             )
#             if rate:
#                 row.rate = rate 