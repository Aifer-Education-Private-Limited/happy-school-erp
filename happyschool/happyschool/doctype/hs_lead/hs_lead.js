// Copyright (c) 2025, esra and contributors
// For license information, please see license.txt

// -----------------------
// Slot Booking validation
// -----------------------
frappe.ui.form.on("Slot Booking", {
    sales_person: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.sales_person || !row.slot_date || !row.from_time) return;

        // Conflict check
        frappe.call({
            method: "happyschool.happyschool.doctype.hs_lead.hs_lead.check_salesperson_conflict",
            args: {
                sales_person: row.sales_person,
                slot_date: row.slot_date,
                from_time: row.from_time,
                parent: frm.doc.name,
                rowname: row.name
            },
            callback: function(r) {
                if (r.message && r.message.conflict) {
                    frappe.msgprint({
                        title: "Assessment Booking Error",
                        indicator: "red",
                        message: __("This Sales Person is already booked for this date and time.")
                    });
                    frappe.model.set_value(cdt, cdn, "sales_person", "");
                }
            }
        });

        // Daily limit check
        let booking = locals[cdt][cdn];
        if (!booking.sales_person) return;

        frappe.call({
            method: "happyschool.happyschool.doctype.hs_lead.hs_lead.check_salesperson_daily_limit",
            args: {
                sales_person: booking.sales_person,
                parent: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.limit_exceeded) {
                    frappe.msgprint({
                        title: "Daily Limit Reached",
                        indicator: "red",
                        message: __(
                            `Sales Person ${booking.sales_person} already has ${r.message.count} bookings today. Limit is 5.`
                        )
                    });
                    frappe.model.set_value(cdt, cdn, "sales_person", "");
                }
            }
        });
    }
});


frappe.ui.form.on("HS Lead", {
    onload: function(frm) {
        // Reload browser only when entering this form for the first time
        if (!frm.doc.__islocal && !window.location.href.includes("force_reload=1")) {
            let url = window.location.href;
            url += url.indexOf("?") > -1 ? "&force_reload=1" : "?force_reload=1";
            window.location.replace(url);
        }
    },

    refresh: function(frm) {
        // Render pipeline visuals and attach click handlers
        renderPipeline(frm);
        updateActiveState(frm);
        setupPipelineClicks(frm); // Ensure clicks work

        // Add Open Opportunity button
        if (!frm.custom_opportunity_button_added) {
            frm.custom_opportunity_button_added = true;
            frm.add_custom_button("Open Opportunity", function() {
                frappe.db.get_value("HS Opportunity", {"custom_lead": frm.doc.name}, "name")
                .then(r => {
                    let opp_name = r.message ? r.message.name : null;
                    if (opp_name) {
                        frappe.set_route("Form", "HS Opportunity", opp_name);
                    } else {
                        frappe.new_doc("HS Opportunity", {
                            custom_lead: frm.doc.name,
                            custom_student_name: frm.doc.custom_student_name,
                            custom_mobile: frm.doc.custom_mobile,
                            custom_gradeclass: frm.doc.custom_gradeclass,
                            custom_curriculum: frm.doc.custom_board,
                            custom_sales_person: frm.doc.custom_sales_person,
                            parent_name: frm.doc.first_name,
                            email: frm.doc.email
                        });
                    }
                });
            });
            frm.add_custom_button("Whatsapp",function(){
                let mobileNo = frm.doc.custom_mobile_number;  // get from field

                if (!mobileNo) {
                    frappe.msgprint("No mobile number found");
                    return;
                }
            
                // Clean the number
                mobileNo = mobileNo.toString().trim();
            
                // Remove all non-numeric characters (like +, -, space, etc.)
                mobileNo = mobileNo.replace(/\D/g, "");
            
                // If number length is 10 (Indian local), prepend +91
                if (mobileNo.length === 10) {
                    mobileNo = "91" + mobileNo;
                }
            
                let whatsappLink = "https://wa.me/" + mobileNo;
                window.open(whatsappLink, "_blank");
            })
        }
    },

    before_save:function(frm){
        if (frm.doc.custom_booking && frm.doc.custom_booking.length > 0) {
            frm.doc.custom_booking.forEach(row => {
                if (row.sales_person) frm.set_value("custom_sales_person", row.sales_person);
                if (row.slot_date) frm.set_value("custom_assigned_date", row.slot_date);
            });
        }
    }
});

// -----------------------
// Pipeline rendering
// -----------------------
function renderPipeline(frm) {
    if (!frm.fields_dict.custom_pipeline_html) return;
    const pipeline_html = frm.get_field("custom_pipeline_html").$wrapper;

    const html = `
    <style>
        .pipeline-container { display:flex; flex-direction:column; margin:30px 0; width:100%; }
        .pipeline-main { display:flex; justify-content:space-between; width:100%; position:relative; margin-bottom:30px; }
        .pipeline-step { text-align:center; cursor:pointer; flex:1; position:relative; }
        .pipeline-step .icon { display:inline-block; width:50px; height:50px; border-radius:50%; line-height:50px; background:#ddd; margin-bottom:8px; transition:all 0.3s ease; }
        .pipeline-step.active .icon { background:#27ae60; color:white; font-weight:bold; }
        .pipeline-main:before { content:""; position:absolute; top:25px; left:0; right:0; height:2px; background:#ddd; }
        .sub-steps { display:flex; justify-content:center; gap:10px; margin-top:10px; }
        .sub-step { text-align:center; cursor:pointer; }
        .sub-step .icon { display:inline-block; width:35px; height:35px; line-height:35px; border-radius:50%; background:#ddd; color:white; font-size:12px; margin-bottom:5px; transition:all 0.3s ease; }
        .sub-step.green .icon { background:#27ae60; color:white; font-weight:bold; }
        .sub-step.grey .icon { background:#bbb; color:white; }
        .sub-step .text { font-size:10px; margin-top:2px; }
    </style>

    <div class="pipeline-container" id="pipeline-wrapper">
        <div class="pipeline-main">
            <div id="prospect-step" class="pipeline-step">
                <span class="icon">P</span>
                <div class="text">Prospect</div>
                <div class="sub-steps" id="prospect-sub-steps">
                    <div class="sub-step" data-value="Connected"><span class="icon">C</span><div class="text">Connected</div></div>
                    <div class="sub-step" data-value="Not Connected"><span class="icon">NC</span><div class="text">Not Connected</div></div>
                </div>
            </div>

            <div id="follow-up-step" class="pipeline-step">
                <span class="icon">F</span>
                <div class="text">Follow Up</div>
                <div class="sub-steps" id="followup-sub-steps">
                    <div class="sub-step" data-value="Interested"><span class="icon">I</span><div class="text">Interested</div></div>
                    <div class="sub-step" data-value="Not Interested"><span class="icon">NI</span><div class="text">Not Interested</div></div>
                    <div class="sub-step" data-value="Maybe Later"><span class="icon">ML</span><div class="text">Maybe Later</div></div>
                    <div class="sub-step" data-value="Disqualified"><span class="icon">D</span><div class="text">Disqualified</div></div>
                </div>
            </div>

            <div id="enrolled-step" class="pipeline-step">
                <span class="icon">E</span>
                <div class="text">Assessment Booked</div>
            </div>
        </div>
    </div>
    `;
    pipeline_html.html(html);
}

// -----------------------
// Pipeline coloring
// -----------------------
function updateActiveState(frm) {
    $(".pipeline-step").removeClass("active");
    $(".sub-step").removeClass("green grey");

    const status = frm.doc.custom_pipeline_status;
    const sub_status = frm.doc.custom_pipeline_sub_status;

    if (status === "Prospect") {
        $("#prospect-step").addClass("active");
        $("#prospect-sub-steps .sub-step").each(function() {
            const val = $(this).data("value");
            if(val === sub_status) $(this).addClass("green");
            else $(this).addClass("grey");
        });
    } else if (status === "Follow Up") {
        $("#follow-up-step").addClass("active");
        $("#followup-sub-steps .sub-step").each(function() {
            const val = $(this).data("value");
            if(val === sub_status) $(this).addClass("green");
            else $(this).addClass("grey");
        });
    } else if (status === "Assessment Booked") {
        $("#enrolled-step").addClass("active");
    }
}

// -----------------------
// Pipeline click handlers
// -----------------------
function setupPipelineClicks(frm) {
    const wrapper = $("#pipeline-wrapper");
    if (wrapper.data("clicks-bound")) return; // prevent multiple bindings
    wrapper.data("clicks-bound", true);

    // Prospect
    wrapper.on("click", "#prospect-step", function () {
        const current = frm.doc.custom_pipeline_sub_status || "Open";
        const dialog = new frappe.ui.Dialog({
            title: "Select Prospect Status",
            fields: [
                { label: "Sub Status", fieldname: "sub_status", fieldtype: "Select",
                  options: ["Open", "Connected", "Not Connected"], reqd: 1, default: current },
                { label: "Remarks", fieldname: "remarks", fieldtype: "Small Text" },
            ],
            primary_action(values) {
                if(values){
                    frm.set_value("custom_pipeline_status", "Prospect");
                    frm.set_value("custom_pipeline_sub_status", values.sub_status);
                    frm.set_value("custom_remarks", values.remarks);

                    frm.add_child("lead_remarks", {
                        status: "Prospect",
                        sub_status: values.sub_status,
                        remarks: values.remarks,
                        user: frappe.session.user,
                        date: frappe.datetime.now_datetime(),
                    });

                    frm.refresh_field("lead_remarks");
                    renderPipeline(frm);
                    updateActiveState(frm);
                    frm.save();
                    dialog.hide();
                }
            }
        });
        dialog.show();
    });

    // Follow Up
    wrapper.on("click", "#follow-up-step", function () {
        const dialog = new frappe.ui.Dialog({
            title: "Select Follow Up Status",
            fields: [
                { label: "Select Follow Up Status", fieldname: "follow_up_status", fieldtype: "Select",
                  options: ["Open","Interested","Not Interested","Maybe Later","Disqualified"], reqd: 1 },
                { label: "Follow Up Date", fieldname: "followup_date", fieldtype: "Datetime" },
                { label: "Remarks", fieldname: "remarks", fieldtype: "Small Text" },
            ],
            primary_action(values){
                if(values){
                    frm.set_value("custom_pipeline_status", "Follow Up");
                    frm.set_value("custom_pipeline_sub_status", values.follow_up_status);
                    frm.set_value("custom_followup_date", values.followup_date);
                    frm.set_value("custom_remarks", values.remarks);

                    frm.add_child("lead_remarks", {
                        status: "Follow Up",
                        sub_status: values.follow_up_status,
                        remarks: values.remarks,
                        user: frappe.session.user,
                        date: frappe.datetime.now_datetime(),
                    });

                    frm.refresh_field("lead_remarks");
                    renderPipeline(frm);
                    updateActiveState(frm);
                    frm.save();
                    dialog.hide();
                }
            }
        });
        dialog.show();
    });

    // Assessment Booked
    wrapper.on("click", "#enrolled-step", function(){
        frm.set_value("custom_pipeline_status","Assessment Booked");
        frm.set_value("custom_pipeline_sub_status","");
        renderPipeline(frm);
        updateActiveState(frm);
        frm.save();
    });
}
