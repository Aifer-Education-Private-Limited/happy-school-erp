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
    payment_type: function(frm) {
        if (frm.doc.payment_type === "Full Payment") {
            // Set customer_payment = grand_total
            let total = parseFloat(frm.doc.grand_total || 0);
            frm.set_value("customer_payment", total);

            // Update child table balance to 0
            if (frm.doc.fess_structure && frm.doc.fess_structure.length > 0) {
                frm.doc.fess_structure[0].customer_paid = total;
                frm.doc.fess_structure[0].balance_amount = 0;
                frm.refresh_field("fess_structure");
            }
            
            // Also update main balance field
            frm.set_value("balance", 0);

        } else if (frm.doc.payment_type === "Custom Payment") {
            // Reset customer_payment so user can type manually
            frm.set_value("customer_payment", 0);

            // Keep balance as per entered amount
            frm.trigger("calculate_totals");
        }
    },
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = (parseFloat(row.session_count || 0) * parseFloat(row.rate || 0));

        frm.refresh_field('items');
        frm.trigger('calculate_totals');  // recalc totals & balance
    },
    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = (parseFloat(row.session_count || 0) * parseFloat(row.rate || 0));

        frm.refresh_field('items');
        frm.trigger('calculate_totals');
    },
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
        // Only add button if payment_link exists
        if (frm.doc.payment_link) {
            let $wrapper = frm.fields_dict['payment_link'].$wrapper;

            // Prevent adding multiple buttons
            if ($wrapper.find('.copy-btn').length === 0) {
                let $btn = $(`
                    <a class="btn btn-xs btn-default copy-btn" 
                       style="margin-left:5px;" 
                       title="Copy to clipboard">
                       <i class="fa fa-clipboard"></i>
                    </a>
                `);

                $btn.on('click', function() {
                    copyToClipboard(frm.doc.payment_link);
                });

                $wrapper.append($btn);
            }
        }

    },

    discount_perc: function(frm) { frm.trigger('calculate_totals'); },
    discount_amnt: function(frm) { frm.trigger('calculate_totals'); },
    customer_payment: function(frm) { frm.trigger('calculate_totals'); },

    calculate_totals: function(frm) {
        // 1) Calculate total fees from items
        let total_fees = 0;
        (frm.doc.items || []).forEach(row => {
            total_fees += parseFloat(row.amount || 0);
        });
    
        // 2) Apply discount only if applicable
        let discount_amount = 0;
        if (frm.doc.discount_perc && parseFloat(frm.doc.discount_perc) > 0) {
            discount_amount = (total_fees * parseFloat(frm.doc.discount_perc || 0)) / 100;
        } else if (frm.doc.discount_amnt && parseFloat(frm.doc.discount_amnt) > 0) {
            discount_amount = parseFloat(frm.doc.discount_amnt || 0);
        }
    
        // 3) Only set amount_after_discount if discount exists
        let amount_after_discount = null;
        if (discount_amount > 0) {
            amount_after_discount = total_fees - discount_amount;
        }
    
        // If discount, grand_total = discounted value, else grand_total = total_fees
        let grand_total = (amount_after_discount !== null) ? amount_after_discount : total_fees;
    
        // 4) Set calculated values
        frm.set_value("total_fees", total_fees);
        frm.set_value("amount_after_discount", amount_after_discount);
        frm.set_value("grand_total", grand_total);
    
        // 5) Balance handling (preview only)
        let balance_preview = 0;
        let custom_paid = parseFloat(frm.doc.custom_paid || 0);
        let customer_payment = parseFloat(frm.doc.customer_payment || 0);
    
        if (frm.doc.payment_type === "Custom Payment") {
            balance_preview = grand_total - (custom_paid + customer_payment);
        } else if (frm.doc.payment_type === "Full Payment") {
            balance_preview = 0;
        }
    
        frm.set_value("balance", balance_preview);
    
        toggle_balance_field(frm);
    },



    
    before_save: function(frm) {
        let payment = parseFloat(frm.doc.customer_payment || 0);
        if (payment <= 0) return;

        let new_custom_paid = parseFloat(frm.doc.custom_paid || 0) + payment;

        // Clear old rows
        frm.clear_table('fess_structure');

        // Add only one row (fresh data on save)
        let row = frm.add_child('fess_structure');
        row.date = frappe.datetime.get_today();
        row.customer_paid = payment;
        row.balance_amount = (parseFloat(frm.doc.grand_total || 0) - new_custom_paid);

        // ✅ Corrected fieldname here
        frm.refresh_field('fess_structure');

        frm.set_value('custom_paid', new_custom_paid);
        frm.set_value('customer_payment', 0);
        frm.set_value('balance', (parseFloat(frm.doc.grand_total || 0) - new_custom_paid));
    },
    
    onload: function(frm) {
        if (!frm.doc.date) {
            frm.set_value("date", frappe.datetime.get_today());
        }
    },
    after_save: function(frm) {
        if (frm.doc.payment_type && !frm.doc.payment_link) {
            let base_url = `https://happyschool.app/complete-payment/`;
            let payment_link = `${base_url}${frm.doc.name}`;
    
            // Set the field
            frm.set_value("payment_link", payment_link);
    
            // // Save again to persist
            frm.save();
        }
    },
    
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
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            frappe.show_alert({ message: 'Copied to clipboard!', indicator: 'green' });
        }).catch(err => {
            frappe.show_alert({ message: 'Failed to copy!', indicator: 'red' });
            console.error("Clipboard error:", err);
        });
    } else {
        // Fallback for older browsers
        const tempInput = document.createElement('input');
        tempInput.value = text;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand('copy');
        document.body.removeChild(tempInput);
        frappe.show_alert({ message: 'Copied to clipboard!', indicator: 'green' });
    }
}