frappe.ready(function () {
    const style = document.createElement('style');
    style.innerHTML = `
        [data-doctype="Web Form"] .page-content-wrapper .container .page_content {
            max-width: 1000px !important;
            margin-top: 20px !important;    
        }
        
        [data-doctype="Web Form"] .page-content-wrapper .container .page_content h1 {
        color: #28a745 !important;
        }
            [data-doctype="Web Form"] .page-content-wrapper .container .page_content .web-form-header .web-form-head .title .web-form-actions .btn 
            {
                background-color: #157347 !important;
                border-color: #157347 !important;
                color: white !important;
            }
    `;
    document.head.appendChild(style);

    // Hide element with class 'web-footer'
    $('.web-footer').hide();
});