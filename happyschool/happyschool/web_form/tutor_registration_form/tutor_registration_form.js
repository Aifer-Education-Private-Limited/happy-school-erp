frappe.ready(function () {
    const style = document.createElement('style');
    style.innerHTML = `
        .web-form {
			background-color: #2fa5c8 !important;
			color: #ffffff;
}
        .web-form input.form-control, 
        .web-form select.form-control, 
        .web-form textarea.form-control {
            border: 2px solid #007bff !important;
            background-color: #f9f9f9 !important;
        }
        .web-form .btn-primary {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
        }
        .web-form-header {
            background-color: #e9b42c !important;
        }
        .web-form-title .ellipsis {
			color: #862f7e !important;
        }
        [data-doctype="Web Form"] .page-content-wrapper .container .page_content {
            max-width: 1000px !important;
            margin: auto !important;
        }
    `;
    document.head.appendChild(style);
});