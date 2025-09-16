frappe.pages['job-application-port'].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    single_column: true
  });

  $(frappe.render_template("job_application_port", {})).appendTo(page.body);
  $(wrapper).on("click", ".nav-link", function (e) {
    e.preventDefault();
    let tabId = $(this).data("tab");
    $(wrapper).find(".nav-link").removeClass("active");
    $(wrapper).find(".tab-pane").addClass("d-none").removeClass("active");
    $(this).addClass("active");
    $(wrapper).find("#" + tabId).removeClass("d-none").addClass("active");

    // frappe.call({
    //     method: "happyschool.api.get_tab_data", // Change to your actual API method
    //     args: { tab: tabId },
    //     callback: function(r) {
    //         // You can update the tab content here if needed
    //         // Example: $(wrapper).find("#" + tabId).html(r.message);
    //         console.log("API response for", tabId, r.message);
    //     }
    // });
  });
};
