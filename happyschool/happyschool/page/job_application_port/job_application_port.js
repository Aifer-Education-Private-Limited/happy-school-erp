frappe.pages['job-application-port'].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    single_column: true
  });

  // Render template first
  $(frappe.render_template("job_application_port", {})).appendTo(page.body);

  // Run all functions after template is loaded
  user_setup(wrapper);
  setup_tab_navigation(wrapper);
  setup_button_navigation(wrapper);
};
function user_setup(wrapper) {
  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "User",
      name: frappe.session.user
    },
    callback: function (r) {
      if (r.message) {
        let user_info = r.message;
        $(wrapper).find("#user_full_name").text(user_info.full_name || "");
        $(wrapper).find("#user_email").text(user_info.email || "");
        $(wrapper).find("#user_phone").text(user_info.phone || "");
      }
    }
  });
}
// Tab navigation function
function setup_tab_navigation(wrapper) {
  $(wrapper).on("click", ".nav-link", function (e) {
    e.preventDefault();
    let tabId = $(this).data("tab");
    $(wrapper).find(".nav-link").removeClass("active");
    $(wrapper).find(".tab-pane").addClass("d-none").removeClass("active");
    $(this).addClass("active");
    $(wrapper).find("#" + tabId).removeClass("d-none").addClass("active");
    // Optionally call API here
    // frappe.call({...});
  });
}

// Button navigation function
function setup_button_navigation(wrapper) {
  $(wrapper).on("click", "#btn-tab1", function () {
    // frappe.set_route("/tutor-registration-form");
  //  window.location.href = "/tutor-registration-form";
   window.open("/tutor-registration-form", "_self");

  });
  $(wrapper).on("click", "#btn-tab2", function () {
    frappe.set_route("/tutor-assignment-");
  });
  
  
  $(wrapper).on("click", "#btn-tab3", function () {
    new frappe.ui.FileUploader({
            doctype: "Tutor Profile",   // target doctype
            docname: "tet32",          // target document name
        });
  });
  
  
  $(wrapper).on("click", "#btn-tab4", function () {
    frappe.set_route("support-ticket");
  });

}
