frappe.ui.form.on("Payment Link Items", {
    program: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.program) {
            frappe.db.get_value("HS Program List", row.program, "session_rate")
                .then(r => {
                    if (r.message && r.message.session_rate) {
                        frappe.model.set_value(cdt, cdn, "rate", r.message.session_rate);
                        frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * r.message.session_rate);
                        frm.trigger("calculate_totals");
                    }
                });
        }
    },

    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * row.rate);
            frm.trigger("calculate_totals");
        }
    }
});

frappe.ui.form.on('HS Payment Link', {
    onload_post_render: function(frm) {
        toggle_fields_by_offer_type(frm);
        if (!frm.doc.custom_paid) {
            frm.set_value("custom_paid", 0);
        }
        toggle_balance_field(frm);
        frm.trigger('calculate_totals');
    },
    offer_applied: function(frm) {
        toggle_offer_fields(frm);
    },
    onload:function(frm){
        toggle_offer_fields(frm);
    },
    refresh:function(frm){
        toggle_offer_fields(frm);
    },

    discount_perc: function(frm) { frm.trigger('calculate_totals'); },
    discount_amnt: function(frm) { frm.trigger('calculate_totals'); },
    customer_payment: function(frm) { frm.trigger('calculate_totals'); },

    calculate_totals: function(frm) {
        // 1) totals and discount
        let total_fees = 0;
        (frm.doc.items || []).forEach(row => total_fees += parseFloat(row.amount || 0));
    
        let discount_amount = 0;
        if (frm.doc.discount_perc) {
            discount_amount = (total_fees * parseFloat(frm.doc.discount_perc || 0)) / 100;
        } else if (frm.doc.discount_amnt) {
            discount_amount = parseFloat(frm.doc.discount_amnt || 0);
        }
    
        let amount_after_discount = total_fees - discount_amount;
        let grand_total = amount_after_discount;
    
        // 2) balance logic
        let custom_paid = parseFloat(frm.doc.custom_paid || 0);
        let customer_payment = parseFloat(frm.doc.customer_payment || 0);
    
        let balance_preview = 0;  // default = 0
        if (customer_payment > 0) {
            balance_preview = grand_total - (custom_paid + customer_payment);
        }
    
        frm.set_value("total_fees", total_fees);
        frm.set_value("amount_after_discount", amount_after_discount);
        frm.set_value("grand_total", grand_total);
        frm.set_value("balance", balance_preview);
    
        toggle_balance_field(frm);
    },
    

    // This runs client-side just before save. It updates the child table, increments custom_paid,
    // resets customer_payment to 0 and sets the final balance.
    before_save: function(frm) {
        let payment = parseFloat(frm.doc.customer_payment || 0);
        if (payment <= 0) return;

        // 1) compute new cumulative paid
        let new_custom_paid = parseFloat(frm.doc.custom_paid || 0) + payment;

        // 2) add a child row to the fees table properly
        let row = frm.add_child('fess_structure');   // change to 'fees_structure' if that's your field
        row.date = frappe.datetime.get_today();
        row.customer_paid = payment;
        row.balance_amount = (parseFloat(frm.doc.grand_total || 0) - new_custom_paid);

        frm.refresh_field('fess_structure');

        // 3) update cumulative paid + reset the transient payment
        frm.set_value('custom_paid', new_custom_paid);
        frm.set_value('customer_payment', 0);

        // 4) final balance after saving
        frm.set_value('balance', (parseFloat(frm.doc.grand_total || 0) - new_custom_paid));
    },
    onload: function(frm) {
        if (!frm.doc.date) {
            frm.set_value("date", frappe.datetime.get_today());
        }
    },
    after_save: function(frm) {
        if (frm.doc.payment_type) {
            let base_url = `https://happyschool.app/complete-payment/`;
            let payment_link = `${base_url}${frm.doc.name}`;

            // Set payment_link field without triggering another save
            frm.set_value("payment_link", payment_link, false, true); // false=don’t trigger change, true=refresh field
        }
    }
});
function toggle_offer_fields(frm) {
    const show = frm.doc.offer_applied === "True";

    frm.set_df_property('discount_perc', 'hidden', !show);
    frm.set_df_property('discount_amnt', 'hidden', !show);

    // Reset values when hidden
    if (!show) {
        frm.set_value('discount_perc', 0);
        frm.set_value('discount_amnt', 0);
    }
}
