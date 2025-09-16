// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Assessment", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Assessment", {
    onload: function(frm) {
        if (!frm.doc.date) {
            frm.set_value("date", frappe.datetime.get_today());
        }
    },
    refresh: function(frm) {
        if (!frm.custom_buttons_added) {
            frm.add_custom_button(__('WhatsApp'), function() {
                let mobileNo = frm.doc.mobile;  // Assuming Assessment has mobile number field

                // Format the number
                if (mobileNo.startsWith('+')) {
                    mobileNo = mobileNo.substring(4);
                } else if (mobileNo.includes('-')) {
                    mobileNo = mobileNo.split('-')[1];
                }

                let whatsappLink = 'https://wa.me/' + mobileNo;
                window.open(whatsappLink, '_blank');

                // Update the Lead status
                if (frm.doc.lead) {
                    frappe.call({
                        method: "frappe.client.set_value",
                        args: {
                            doctype: "Opportunity",
                            name: frm.doc.opportunity,
                            fieldname: "custom_assessment_status",
                            value: "Shared"
                        },
                        callback: function(r) {
                            frappe.show_alert({ message: "Lead status updated!", indicator: "green" });
                        }
                    });
                }
            });
            
        }
    }
}); 