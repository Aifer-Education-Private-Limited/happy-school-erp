// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Parents", {
	refresh(frm){
        toggle_fields_by_type(frm);

    },
    type(frm){
        toggle_fields_by_type(frm)
    },
});
function toggle_fields_by_type(frm) {
    const type = frm.doc.auth_type;

    // Show Student only if type = "Student"
    frm.set_df_property('password', 'hidden', (type === "phone" || type === "whatsapp")); 
}
