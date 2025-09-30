frappe.pages['job-application-port'].on_page_load = function (wrapper) {
    new JobApplicationPortPage(wrapper);
};

class JobApplicationPortPage {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            single_column: true
        });
        $(frappe.render_template("job_application_port", {})).appendTo(this.page.body);
        
        this.user_setup();
        this.setup_tab_navigation();
        this.setup_button_navigation();
    }

    user_setup() {
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "User",
                name: frappe.session.user
            },
            callback: (r) => {
                if (r.message) {
                    let user_info = r.message;
                    $(this.wrapper).find("#user_full_name").text(user_info.full_name || "");
                    $(this.wrapper).find("#user_email").text(user_info.email || "");
                    $(this.wrapper).find("#user_phone").text(user_info.phone || "");
                }
            }
        });
    }

    setup_tab_navigation() {
        $(this.wrapper).on("click", ".nav-link", (e) => {
            e.preventDefault();
            let tabId = $(e.currentTarget).data("tab");
            $(this.wrapper).find(".nav-link").removeClass("active");
            $(this.wrapper).find(".tab-pane").addClass("d-none").removeClass("active");
            $(e.currentTarget).addClass("active");
            $(this.wrapper).find("#" + tabId).removeClass("d-none").addClass("active");
            // Optionally call API here
        });
    }

    setup_button_navigation() {
        $(this.wrapper).on("click", "#btn-tab1", () => {
            window.open("/tutor-registration-form", "_self");
        });
        $(this.wrapper).on("click", "#btn-tab2", () => {
            frappe.set_route("/tutor-assignment-");
        });
        $(this.wrapper).on("click", "#btn-tab3", () => {
            const videoUrl = $(this.wrapper).find("#video-url-input").val();
            if (videoUrl) {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "Tutor Profile",
                        name: "tet32",
                        fieldname: "video_url",
                        value: videoUrl
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint("Video URL updated successfully!");
                        } else {
                            frappe.msgprint("Failed to update Video URL.");
                        }
                    }
                });
            } else {
                frappe.msgprint("Please enter a video URL.");
            }
        });
        $(this.wrapper).on("click", "#btn-tab4", () => {
            frappe.set_route("support-ticket");
        });
    }
}
