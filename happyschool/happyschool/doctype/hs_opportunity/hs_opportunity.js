
frappe.ui.form.on("HS Opportunity", {
    onload: function(frm) {
        // Reload browser only when entering this form for the first time
        // Prevent infinite loop by checking URL param
        if (!frm.doc.__islocal && !window.location.href.includes("force_reload=1")) {
            // Append a marker to URL so next load skips reload
            let url = window.location.href;
            if (url.indexOf("?") > -1) {
                url += "&force_reload=1";
            } else {
                url += "?force_reload=1";
            }
            window.location.replace(url);
        }
    },
  
    
    refresh: function(frm) {
        
        
        if (!frm.fields_dict.pipeline_html) return;

        const pipeline_html = frm.get_field("pipeline_html").$wrapper;

        // -----------------------
        // Pipeline HTML
        // -----------------------
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

        <div class="pipeline-container">
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
                    <div class="text">Assessment</div>
                    <div class="sub-steps" id="followup-sub-steps">
                        <div class="sub-step" data-value="FollowUp"><span class="icon">F</span><div class="text">FollowUp</div></div>
                        <div class="sub-step" data-value="Scheduled"><span class="icon">S</span><div class="text">Scheduled</div></div>
                        <div class="sub-step" data-value="Completed"><span class="icon">C</span><div class="text">Completed</div></div>
                        <div class="sub-step" data-value="Report Shared"><span class="icon">RS</span><div class="text">Report Shared</div></div>
                        <div class="sub-step" data-value="Maybe Later"><span class="icon">ML</span><div class="text">Maybe Later</div></div>
                        <div class="sub-step" data-value="Lost"><span class="icon">L</span><div class="text">Lost</div></div>
                    </div>
                </div>

                <div id="enrolled-step" class="pipeline-step">
                    <span class="icon">E</span>
                    <div class="text">Enrolled</div>
                </div>
            </div>
        </div>
        `;

        pipeline_html.html(html);

        // -----------------------
        // Function to update colors
        // -----------------------
        function updateActiveState() {
            $(".pipeline-step").removeClass("active");
            $(".sub-step").removeClass("green grey");

            const status = frm.doc.pipeline_status;
            const sub_status = frm.doc.custom_sub_status;

            if (status === "Prospect") {
                $("#prospect-step").addClass("active");
                $("#prospect-sub-steps .sub-step").each(function() {
                    const val = $(this).data("value");
                    if(val === sub_status) $(this).addClass("green");
                    else $(this).addClass("grey");
                });
            } else if (status === "Assessment") {
                $("#follow-up-step").addClass("active");
                $("#followup-sub-steps .sub-step").each(function() {
                    const val = $(this).data("value");
                    if(val === sub_status) $(this).addClass("green");
                    else $(this).addClass("grey");
                });
            } else if (status === "Enrolled") {
                $("#enrolled-step").addClass("active");
            }
        }

        updateActiveState();

        // -----------------------
        // Dialog popup for any click
        // -----------------------
        function openDialog(step) {
            let current = frm.doc.custom_sub_status || (step === "Prospect" ? "Open" : "FollowUp");
            let options = [];

            if(step === "Prospect") options = ["Open","Connected","Not Connected"];
            else if(step === "Assessment") options = ["Assessment","Scheduled","Completed","Report Shared","Maybe Later","Lost","DS","LP","FollowUp"];

            let d = new frappe.ui.Dialog({
                title: `Select ${step} Status`,
                fields:[
                    {label:"Sub Status", fieldname:"sub_status", fieldtype:"Select", options: options, reqd:1, default: current},
                    {label:"Remarks", fieldname:"remarks", fieldtype:"Small Text"}
                ],
                primary_action(values){
                    frm.set_value("pipeline_status", step);
                    frm.set_value("custom_sub_status", values.sub_status);
                    frm.set_value("opportunity_remarks", values.remarks);
                    

                    frm.add_child("opp_remarks",{
                        status: step,
                        sub_status: values.sub_status,
                        remarks: values.remarks,
                        user: frappe.session.user,
                        date: frappe.datetime.now_datetime()
                    });
                    frm.refresh_field("opp_remarks");
                    frm.save().then(() => {
                        frm.reload_doc().then(() => {
                            updateActiveState();   // redraw with fresh values
                        });
                    });
                    d.hide();
                }
            });
            d.show();
        }

        // -----------------------
        // Click handlers for steps and sub-steps
        // -----------------------
        $("#prospect-step, #prospect-sub-steps .sub-step").on("click", function(){ openDialog("Prospect"); });
        $("#follow-up-step, #followup-sub-steps .sub-step").on("click", function(){ openDialog("Assessment"); });
        $("#enrolled-step").on("click", function(){
            frm.set_value("pipeline_status","Enrolled");
            frm.set_value("custom_sub_status","");
            updateActiveState();
            frm.save();
        });

        // -----------------------
        // Add custom buttons (only once)
        // -----------------------
       
            frm.custom_buttons_added = true;

            frm.add_custom_button("Schedule Assessment", function(){
                if(!frm.doc.email){
                    frappe.msgprint({title:"Email Required", message:"Please set an email to schedule assessment.", indicator:"red"});
                    return;
                }

                frappe.db.get_value('HS Sales Persons', frm.doc.sales_person, 'meet_link').then(r => {
                    const meet_link = r.message ? r.message.meet_link : '';
                    const time = frm.doc.schedule_date + " " + frm.doc.schedule_time;

                    let d = new frappe.ui.Dialog({
                        title:"Schedule Assessment",
                        fields:[
                            {label:"Google Meet Link", fieldname:"google_meet_link", fieldtype:"Data", default: meet_link},
                            {label:"Schedule Time", fieldname:"schedule_time", fieldtype:"Data", default: time}
                        ],
                        primary_action_label:"Send",
                        primary_action(values){
                            frappe.call({
                                method: "happyschool.happyschool.doctype.hs_opportunity.hs_opportunity.send_assessment_email",
                                args: {docname: frm.doc.name, meet_link: values.google_meet_link, schedule_time: values.schedule_time},
                                callback: function(){
                                    frappe.msgprint("Email sent successfully!");
                                    frm.save();

                                    // WhatsApp
                                    let mobile = frm.doc.custom_mobile;
                                    if(mobile){
                                        mobile = mobile.replace(/\D/g,'');
                                        const message = `Dear Parent,\nGoogle Meet Link: ${values.google_meet_link}\nScheduled Time: ${values.schedule_time}`;
                                        window.open(`https://wa.me/${mobile}?text=${encodeURIComponent(message)}`, "_blank");
                                    }
                                    d.hide();
                                }
                            });
                        }
                    });
                    d.show();
                });
            });

            if(!frm.is_new()){
                frm.add_custom_button("Assessment", function(){
                    frappe.new_doc("Assessment", {
                        lead: frm.doc.custom_lead,
                        opportunity: frm.doc.name,
                        student_name: frm.doc.custom_student_name,
                        gradeclass: frm.doc.custom_gradeclass,
                        curriculum: frm.doc.custom_curriculum,
                        mobile: frm.doc.custom_mobile

                    });
                });

                frm.add_custom_button("Payment", function(){
                    frappe.new_doc("HS Payment Link", {
                        lead: frm.doc.custom_lead,
                        opportunity: frm.doc.name,
                        mobile_number: frm.doc.custom_mobile,
                        customer_name: frm.doc.parent_name,
                        email_id: frm.doc.email
                    });
                });
            }
    },

    after_save: function(frm){
        // Refresh to update buttons and pipeline
        frm.trigger("refresh");
    }
});
