// frappe.ui.form.on("Payment Link Items", {
//     program: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];

//         if (row.program) {
//             frappe.db.get_value("HS Program List", row.program, "session_rate")
//                 .then(r => {
//                     if (r.message && r.message.session_rate) {
//                         console.log("Fetched session_rate:", r.message.session_rate);

//                         frappe.model.set_value(cdt, cdn, "rate", r.message.session_rate);
//                         frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * r.message.session_rate);
//                     } else {
//                         console.log("No session_rate found for:", row.program);
//                     }
//                 });
//         }
//     },

//     qty: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         if (row.rate) {
//             frappe.model.set_value(cdt, cdn, "amount", (row.qty || 1) * row.rate);
//         }
//     }
// });