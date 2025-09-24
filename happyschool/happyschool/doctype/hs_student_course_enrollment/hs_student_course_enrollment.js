// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

frappe.ui.form.on("HS Student Course Enrollment", {
	refresh(frm) {
        

	},
    student: function(frm) {
        if(!frm.doc.student) return; // check if student is selected
        frappe.db.get_doc("Student", frm.doc.student).then(stu => {
            frm.set_value("student_name", stu.student_name); // make sure this is the correct fieldname
        });
    },
    parent1: function(frm) {
        if (!frm.doc.parent1) return;
        frappe.db.get_doc("Parents", frm.doc.parent1).then(parent => {
            frm.set_value("parent_name", parent.first_name);
            frm.set_value("mobile",parent.mobile_number);
            frm.set_value("email",parent.email)
        });
    }

    
});
