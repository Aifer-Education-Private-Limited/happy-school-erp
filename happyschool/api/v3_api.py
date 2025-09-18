import frappe

@frappe.whitelist(allow_guest=True)
def get_payment_link_details(mobile=None):
    """
    API to fetch Payment Link details along with child table 'items'
    Show discount fields only if offer_applied is True.
    """
    try:
        if not mobile:
            frappe.local.response.update ({
                "success": False,
                "message": "Mobile number is required."
            })
            return

        payment_links = frappe.get_all(
            "Payment Link",
            filters={"mobile_number": mobile},
            fields=[
                "name",
                "customer_name",
                "mobile_number",
                "email_id",
                "total_fees",
                "grand_total",
                "discount_perc",
                "discount_amnt",
                "offer_applied",
                "payment_type",
                "state",
                "payment_link"
            ],
            order_by="creation desc"
        )

        if not payment_links:
            frappe.local.response.update ({
                "success": False,
                "message": "No Payment Link found."
            })
            return

        result = []
        for link in payment_links:
            items = frappe.get_all(
                "Payment Link Items",
                filters={"parent": link["name"], "parentfield": "items"},
                fields=["item_code", "program", "rate"]
            )

            mapped_items = [
                {
                    "item_code": item.get("item_code"),
                    "program": item.get("program"),
                    "fees": item.get("rate")
                } for item in items
            ]

            mapped_link = {
                "payment_id": link.get("name"),
                "mob": link.get("mobile_number"),
                "name": link.get("customer_name"),
                "email": link.get("email_id"),
                "total": link.get("total_fees"),
                "offer_applied": link.get("offer_applied"),
                "payment_type": link.get("payment_type"),
                "state": link.get("state"),
                "payment_link": link.get("payment_link"),
                "items": mapped_items
            }

            if str(link.get("offer_applied")).lower() in ["1", "true", "yes"]:
                mapped_link.update({
                    "discount_in_perc": link.get("discount_perc"),
                    "discount_in_amnt": link.get("discount_amnt"),
                    "fee_after_discount": link.get("grand_total")
                })

            result.append(mapped_link)

        frappe.local.response.update({
            "success": True,
            "message": "Payment Link(s) fetched successfully.",
            "data": result
        })
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payment_link_details error")
        frappe.local.response.update ({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        })
        return
