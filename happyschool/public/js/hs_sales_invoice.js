frappe.ui.form.on("Payment Link Items", {
    program: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.program) {
            frappe.db.get_value("HS Program List", row.program, "session_rate")
                .then(r => {
                    if (r.message && r.message.session_rate) {
                        frappe.model.set_value(cdt, cdn, "rate", r.message.session_rate);
                        frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * r.message.session_rate);
                       
                    }
                });
        }
    },

    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * row.rate);
            
        }
    }
});
frappe.ui.form.on("Sales Invoice", {
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value("Parents", { customer: frm.doc.customer }, "name")
                .then(r => {
                    if (r && r.message && r.message.name) {
                        frm.set_value("custom_parent", r.message.name);
                    } else {
                        frappe.msgprint("No Parent found for this Customer");
                        frm.set_value("custom_parent", null);
                    }
                });
        }
    }
});

