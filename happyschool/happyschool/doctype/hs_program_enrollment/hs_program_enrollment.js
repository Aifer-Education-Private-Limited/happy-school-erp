// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

// frappe.ui.form.on("HS Program Enrollment", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("HS Program Enrollment", {
    onload: function(frm) {
        if (!frm.doc.enrollment_date) {
            frm.set_value("enrollment_date", frappe.datetime.get_today());
        }
    },
    program:function(frm){
        if(!frm.doc.program) return;
        frappe.db.get_doc("HS Program List",frm.doc.program).then(prg=>{
            frm.set_value("project",prg.project)
        })

    },
    student: function(frm) {
        if(!frm.doc.student) return; // check if student is selected
        frappe.db.get_doc("Student", frm.doc.student).then(stu => {
            frm.set_value("student_name", stu.student_name); // make sure this is the correct fieldname
        });
    }
 
    
});
