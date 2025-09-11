// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Parent Or Student Ticket", {
// 	refresh(frm) {

// 	},
// });
let temp_comment = null; // temporary storage

frappe.ui.form.on('Parent Or Student Ticket', {
    refresh(frm){
        toggle_fields_by_type(frm);

    },
    type(frm){
        toggle_fields_by_type(frm)
    },
    status(frm) {
        const new_status = frm.doc.status;

        if (['Progress', 'Complete'].includes(new_status)) {
            frappe.prompt(
                [
                    {
                        label: 'Comment',
                        fieldname: 'comment',
                        fieldtype: 'Small Text'
                    },
                ],
                function (values) {
                    temp_comment = values.comment; // store temporarily

                    
                    if (new_status === 'Progress') {
                        frm.set_value('progress_comment', temp_comment);
                    } else if (new_status === 'Complete') {
                        frm.set_value('complete_comment', temp_comment);
                    }
                },
                'Add Comment',
                'Submit'
            );
        } else {
            temp_comment = null; // reset if not progress or complete
        }
    },

    validate(frm) {
        const new_status = frm.doc.status;

        if (['Progress', 'Complete'].includes(new_status)) {
            if (!temp_comment) {
                frappe.throw(__('Please provide a comment for this status.'));
            }
            
        }
    }
});

function toggle_fields_by_type(frm) {
    const type = frm.doc.type;

    // Show Student only if type = "Student"
    frm.set_df_property('student', 'hidden', type !== "Student");

    // Show Parent only if type = "Parent"
    frm.set_df_property('parent1', 'hidden', type !== "Parent");
}
