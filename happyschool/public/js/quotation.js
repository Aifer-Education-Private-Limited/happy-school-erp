frappe.ui.form.on("Quotation", {
    refresh: function(frm) {
       

            frm.add_custom_button(__('Payment'), function() {
                const customer_name = frm.doc.customer_name || "";
                const date = frm.doc.transaction_date || "";
                const valid_til = frm.doc.valid_till || "";
                const total_quantity = frm.doc.total_qty || 0;
                const total = frm.doc.total || 0;
                const grand_total = frm.doc.grand_total || 0;

                const fields = [
                    { label: 'Customer Name', fieldname: 'customer_name', fieldtype: 'Data', default: customer_name, read_only: 1 },
                    { label: 'Date', fieldname: 'transaction_date', fieldtype: 'Date', default: date, read_only: 1 },
                    { label: 'Valid Till', fieldname: 'valid_till', fieldtype: 'Date', default: valid_til, read_only: 1 },
                    { label: 'Total Quantity', fieldname: 'total_qty', fieldtype: 'Float', default: total_quantity, read_only: 1 },
                    { fieldtype: 'Column Break' },
                    { label: 'Total', fieldname: 'total', fieldtype: 'Currency', default: total, read_only: 1 },
                    { label: 'Grand Total', fieldname: 'grand_total', fieldtype: 'Currency', default: grand_total, read_only: 1 },
                    
                ];

                if (frm.doc.items && frm.doc.items.length) {
                    frm.doc.items.forEach(function(row, i) {
                        fields.push({
                            label: `Item `,
                            fieldname: `item`,
                            fieldtype: 'Link',
                            options: 'Item',
                            default: row.item_code,
                            read_only: 1
                        });
                        fields.push({
                            label: `Program `,
                            fieldname: `program`,
                            fieldtype: 'Link',
                            options: 'Program',
                            read_only: 1
                        });
                    });
                }

                const dialog = new frappe.ui.Dialog({
                    title: __('Payment'),
                    fields: fields,
                    primary_action_label: __('Submit'),
                    primary_action(values) {
                        frappe.msgprint(__('Payment submitted: ') + JSON.stringify(values));
                        dialog.hide();
                    }
                });

                dialog.show();

                // Fetch programs for each item
                if (frm.doc.items && frm.doc.items.length) {
                    frm.doc.items.forEach(function(row, i) {
                        if (row.item_code) {
                            frappe.db.get_value("Item", row.item_code, "custom_program")
                                .then(r => {
                                    if (r && r.message && r.message.custom_program) {
                                        dialog.set_value(`program`, r.message.custom_program);
                                    } else {
                                        dialog.set_value(`program`, "N/A");
                                    }
                                });
                        }
                    });
                }
            });
        }
    
});
