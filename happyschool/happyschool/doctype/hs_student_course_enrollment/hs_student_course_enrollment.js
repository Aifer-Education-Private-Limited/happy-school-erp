// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt
frappe.ui.form.on('HS Enrolled Details', {
    reschedule: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frappe.db.get_value("Courses", {"title": row.program}, "course_id")
            .then(r => {
                const course_id = r.message.course_id || "";
                const queryParams = new URLSearchParams({
                    enrollment_id: frm.doc.name,
                    child_row: row.name,
                    student_id: frm.doc.student,
                    course_id: course_id,
                    subject: row.program,   // pass program as subject
                    name: frm.doc.student_name,  
                    session_count: row.session_count     // pass child row name
                });
                window.location.href = `/app/reschedule-time?${queryParams}`;
            });
    },
    program_enrollment: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.program_enrollment) return;

        frappe.call({
            method: "happyschool.happyschool.doctype.hs_student_course_enrollment.hs_student_course_enrollment.get_program_enrollment_details",
            args: {
                program_enrollment_id: row.program_enrollment
            },
            callback: function(r) {
                if (r.message && r.message.date) {
                    frappe.model.set_value(cdt, cdn, "date", r.message.date);
                }
            }
        });
    },

    program: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.program) return;

        frappe.call({
            method: "happyschool.happyschool.doctype.hs_student_course_enrollment.hs_student_course_enrollment.get_program_details",
            args: {
                program: row.program
            },
            callback: function(r) {
                if (r.message) {
                    if (r.message.project) {
                        frappe.model.set_value(cdt, cdn, "project", r.message.project);
                    }
                    frappe.model.set_value(cdt, cdn, "session_count", r.message.session_count || 0);
                }
            }
        });
    }
});

frappe.ui.form.on("HS Student Course Enrollment", {
    
    student: function(frm) {
        if(!frm.doc.student) return; // check if student is selected
        frappe.db.get_doc("HS Students", frm.doc.student).then(stu => {
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
    },


    

});


