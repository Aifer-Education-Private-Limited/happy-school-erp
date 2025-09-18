frappe.ui.form.on("Quotation", {
    refresh: function (frm) {
        frm.add_custom_button(__('Payment'), function () {
            const customer_name = frm.doc.customer_name || "";
            const date = frm.doc.transaction_date || "";
            const valid_til = frm.doc.valid_till || "";
            const total_quantity = frm.doc.total_qty || 0;
            const total = frm.doc.total || 0;
            const grand_total = frm.doc.grand_total || 0;
            const discount_percentage = frm.doc.additional_discount_percentage || 0;
            const discount_amount = frm.doc.discount_amount || 0;
            const lead = frm.doc.party_name;

            const fields = [];

            // First column: Item, Program, Program Rate
            if (frm.doc.items && frm.doc.items.length) {
                frm.doc.items.forEach(function (row, i) {
                    fields.push(
                        {
                            label: `Item ${i + 1}`,
                            fieldname: `item_${i + 1}`,
                            fieldtype: 'Link',
                            options: 'Item',
                            default: row.item_code,
                            read_only: 1
                        },
                        {
                            label: `Program ${i + 1}`,
                            fieldname: `program_${i + 1}`,
                            fieldtype: 'Link',
                            options: 'Program',
                            read_only: 1
                        },
                        {
                            label: `Program Rate ${i + 1}`,
                            fieldname: `rate_${i + 1}`,
                            fieldtype: 'Currency',
                            read_only: 1
                        }
                    );
                });
            }

            // Column break
            fields.push({ fieldtype: 'Column Break' });

            // Second column: totals
            fields.push(
                { label: 'Total Quantity', fieldname: 'total_qty', fieldtype: 'Float', default: total_quantity, read_only: 1 },
                { label: 'Offer', fieldname: 'offer', fieldtype: 'Check', default: 0 },
                { label: 'Additional Discount Percentage', fieldname: 'discount_perc', fieldtype: 'Float', default: discount_percentage, depends_on: 'eval:doc.offer==1', read_only: 1 },
                { label: 'Additional Discount Amount', fieldname: 'discount_amnt', fieldtype: 'Float', default: discount_amount, depends_on: 'eval:doc.offer==1', read_only: 1 },
                { label: 'Total', fieldname: 'total', fieldtype: 'Currency', default: total, read_only: 1 },
                { label: 'Grand Total', fieldname: 'grand_total', fieldtype: 'Currency', default: grand_total, read_only: 1 },
                { label: 'Payment Type', fieldname: 'payment_type', fieldtype: 'Select', options: '\nFull Payment\nCustom Payment', default: "" },
                { label: 'Payment Link', fieldname: 'payment_link', fieldtype: 'Small Text', default: "", read_only: 1 }
            );

            // Add general info at the top
            fields.unshift(
                { label: 'Customer Name', fieldname: 'customer_name', fieldtype: 'Data', default: customer_name, read_only: 1 },
                { label: 'Date', fieldname: 'transaction_date', fieldtype: 'Date', default: date, read_only: 1 },
                { label: 'Valid Till', fieldname: 'valid_till', fieldtype: 'Date', default: valid_til, read_only: 1 },
                { label: 'Mobile Number', fieldname: 'mob_no', fieldtype: 'Data', default: '', read_only: 1 },
                { label: 'Email', fieldname: 'email', fieldtype: 'Data', default: '', read_only: 1 },
                { 
                    label: 'State', 
                    fieldname: 'state', 
                    fieldtype: 'Select', 
                    options: `
                        Andhra Pradesh
                        Arunachal Pradesh
                        Assam
                        Bihar
                        Chhattisgarh
                        Goa
                        Gujarat
                        Haryana
                        Himachal Pradesh
                        Jharkhand
                        Karnataka
                        Kerala
                        Madhya Pradesh
                        Maharashtra
                        Manipur
                        Meghalaya
                        Mizoram
                        Nagaland
                        Odisha
                        Punjab
                        Rajasthan
                        Sikkim
                        Tamil Nadu
                        Telangana
                        Tripura
                        Uttar Pradesh
                        Uttarakhand
                        West Bengal
                        Delhi
                        Jammu and Kashmir
                        Ladakh
                        Puducherry
                        Chandigarh
                        Dadra and Nagar Haveli and Daman and Diu
                        Lakshadweep
                        Andaman and Nicobar Islands
                        `, 
                    default: ''
                }

            );

            const dialog = new frappe.ui.Dialog({
                title: __('Payment'),
                fields: fields,
                primary_action_label: __('Submit'),
                primary_action(values) {
                    const link = values.payment_link || "";

                    if (!link) {
                        frappe.msgprint(__('No payment link generated.'));
                        return;
                    }

                    
                    const item_rows = [];
                    if (frm.doc.items && frm.doc.items.length) {
                        frm.doc.items.forEach(function (row, i) {
                            item_rows.push({
                                item_code: values[`item_${i + 1}`],
                                program: values[`program_${i + 1}`],
                                rate: values[`rate_${i + 1}`]
                            });
                        });
                    }

                    
                    frappe.call({
                        method: "frappe.client.insert",
                        args: {
                            doc: {
                                doctype: "Payment Link",
                                lead: frm.doc.party_name,                // link back to Quotation
                                customer_name: values.customer_name,
                                mobile_number: values.mob_no,
                                total_qty: values.total_qty,
                                offer_applied: values.offer ? "True" : "False",
                                total_fees: values.total,
                                grand_total:values.grand_total,
                                discount_perc:values.discount_perc,
                                discount_amnt:values.discount_amnt,
                                email_id: values.email,
                                state:values.state,
                                payment_type: values.payment_type,
                                payment_link: values.payment_link,
                                items: item_rows // assumes Payment Link has a child table "items"
                            }
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Payment Link document created: ') + r.message.name);
                                // also update Quotation field if needed
                                if (frm.doc.docstatus === 0) {
                                    frm.set_value("custom_payment_link", link);
                                    frm.save();
                                } else if (frm.doc.docstatus === 1) {
                                    frappe.db.set_value("Quotation", frm.doc.name, "custom_payment_link", link);
                                }
                            }
                        }
                    });

                    dialog.hide();
                }
            });

            dialog.show();

            if (lead) {
                frappe.db.get_value("Lead", lead, ["custom_mobile_number", "custom_student_email"])
                    .then(r => {
                        if (r && r.message) {
                            if (r.message.custom_mobile_number) {
                                dialog.set_value("mob_no", r.message.custom_mobile_number);
                            }
                            if (r.message.custom_student_email) {
                                dialog.set_value("email", r.message.custom_student_email);
                            }
                        }
                    });
            }

            // Fetch program & rate for each item
            if (frm.doc.items && frm.doc.items.length) {
                frm.doc.items.forEach(function (row, i) {
                    if (row.item_code) {
                        frappe.db.get_value("Item", row.item_code, "custom_program")
                            .then(r => {
                                dialog.set_value(`program_${i + 1}`, r.message.custom_program || "N/A");
                            });

                        frappe.db.get_value("Item Price", { item_code: row.item_code }, "price_list_rate")
                            .then(r => {
                                dialog.set_value(`rate_${i + 1}`, r.message.price_list_rate || 0);
                            });
                    }
                });
            }

            // Payment type onchange → generate dummy link
            dialog.fields_dict.payment_type.df.onchange = function () {
                const selected = dialog.get_value("payment_type");
                if (selected === "Full Payment") {
                    dialog.set_value("payment_link", "https://dummy-payment.com/full");
                } else if (selected === "Custom Payment") {
                    dialog.set_value("payment_link", "https://dummy-payment.com/custom");
                } else {
                    dialog.set_value("payment_link", "");
                }
                dialog.refresh();
            };
        });
    }
});
