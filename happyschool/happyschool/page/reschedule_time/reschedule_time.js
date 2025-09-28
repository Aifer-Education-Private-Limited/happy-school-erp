frappe.pages['reschedule-time'].on_page_load = function (wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Schedule Live',
        single_column: true
    });

    let $container = $(page.body).empty().append(`<div id="schedule-content"></div>`);
    $(".modal-backdrop").remove();
    $("body").removeClass("modal-open");

    const urlParams = new URLSearchParams(window.location.search);
    const enrollment_id = urlParams.get("enrollment_id");
    const child_row = urlParams.get("child_row");
    const name = urlParams.get("name");
    const student_id = urlParams.get("student_id");
    const course_id = urlParams.get("course_id");
    const subject = urlParams.get("subject");
    const session_count = urlParams.get("session_count");

    if (enrollment_id && child_row) {
        frappe.db.get_doc("HS Student Course Enrollment", enrollment_id).then(doc => {
            let childRow = doc.enrolled_programs.find(r => r.name === child_row);

            if (childRow) {
                // 🔹 Load flatpickr assets
                let assets = `
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
                    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
                `;
                $container.append(assets);

                // 🔹 Session Count
                if (session_count) {
                    $container.append(`
                        <div class="card shadow-sm p-3 mb-4">
                            <h4>Session Count: <span class="text-primary">${session_count}</span></h4>
                        </div>
                    `);
                }

                // 🔹 Main Form
                let formHtml = `
                <div class="card shadow-sm mb-4 p-3">
                    <h5>Create / schedule Live Classroom</h5>
                    <form id="live-classroom-form">
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Name</b></label>
                                <input class="form-control" name="name" value="${name}" readonly>
                            </div>
                            <div class="col-md-6"><label><b>Student ID</b></label>
                                <input class="form-control" name="student_id" value="${student_id}" readonly>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Subject</b></label>
                                <input class="form-control" name="subject" value="${subject || ''}" readonly>
                            </div>
                            <div class="col-md-6"><label><b>Course ID</b></label>
                                <input class="form-control" name="course_id" value="${course_id}" readonly>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Topic</b></label>
                                <input class="form-control" name="topic">
                            </div>
                            <div class="col-md-6"><label><b>Subtopic</b></label>
                                <input class="form-control" name="subtopic">
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-12"><label><b>Meeting Link</b></label>
                                <input class="form-control" name="meeting_link">
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Description</b></label>
                                <input class="form-control" name="description">
                            </div>
                            <div class="col-md-6"><label><b>Caption</b></label>
                                <input class="form-control" name="caption">
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Status</b></label>
                                <select class="form-control" name="status">
                                    <option value="Upcoming">Upcoming</option>
                                    <option value="Ongoing">Ongoing</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                            <div class="col-md-6"><label><b>Tutor ID</b></label>
                                <input class="form-control" name="tutor_id">
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-6"><label><b>Faculty Email</b></label>
                                <input class="form-control" name="faculty_email">
                            </div>
                            <div class="col-md-6">
                                <label><b>Thumbnail</b></label>
                                <input type="file" id="thumbnail-upload" class="form-control mb-2">
                                <input type="hidden" name="thumbnail" id="thumbnail-hidden">
                                <div id="thumbnail-preview" style="margin-top:5px;"></div>
                            </div>
                        </div>
                    </form>
                </div>`;
                $container.append(formHtml);

                // 🔹 Scheduler Section + Save + Toggle Button
                let schedulerHtml = `
                <div id="session-form" class="card shadow-sm mb-4 p-3">
                    <h5 class="mb-3">📅 Session Scheduler</h5>
                    <div class="session-row d-flex gap-5">
                        <div class="calendar-box">
                            <label><b>Select Date</b></label>
                            <input type="text" id="calendar-input" style="display:none;">
                            <div id="calendar-inline"></div>
                        </div>
                        <div class="time-box flex-shrink-1" style="min-width:220px; margin-left:40px;">
                            <label><b>From Time</b></label>
                            <input type="text" id="session-from" class="form-control mb-2">
                            <label><b>To Time</b></label>
                            <input type="text" id="session-to" class="form-control mb-2">
                            
                            <div class="d-flex justify-content-between mt-2">
                                <button type="button" id="add-session" class="btn btn-primary btn-sm">Save Session</button>
                                <button id="toggle-sessions" class="btn btn-outline-secondary btn-sm" style="width:auto; min-width:120px;">Sessions ▼</button>
                            </div>
                        </div>
                    </div>

                    <div id="saved-sessions-container" style="display:none; margin-top:15px;">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Date</th>
                                    <th>From</th>
                                    <th>To</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>`;
                $container.append(schedulerHtml);

                // ✅ Init Flatpickr with multiple date support
                let selectedDates = [];
                setTimeout(() => {
                    flatpickr("#calendar-input", {
                        dateFormat: "Y-m-d",
                        inline: true,
                        clickOpens: false,
                        appendTo: document.querySelector("#calendar-inline"),
                        mode: "multiple",
                        onChange: (dates) => {
                            selectedDates = dates.map(d => flatpickr.formatDate(d, "Y-m-d"));
                        }
                    });
                    flatpickr("#session-from", { enableTime: true, noCalendar: true, dateFormat: "H:i" });
                    flatpickr("#session-to", { enableTime: true, noCalendar: true, dateFormat: "H:i" });
                }, 300);

                // ✅ Handle thumbnail upload
                $(document).on("change", "#thumbnail-upload", function (e) {
                    let file = e.target.files[0];
                    if (!file) return;

                    let formData = new FormData();
                    formData.append("file", file, file.name);
                    formData.append("is_private", 0);

                    $.ajax({
                        url: "/api/method/upload_file",
                        type: "POST",
                        data: formData,
                        contentType: false,
                        processData: false,
                        success: function (r) {
                            if (r.message && r.message.file_url) {
                                let file_url = r.message.file_url;
                                $("#thumbnail-hidden").val(file_url);
                                $("#thumbnail-preview").html(
                                    `<img src="${file_url}" class="img-thumbnail" style="max-height:80px;">`
                                );
                                frappe.msgprint("✅ Thumbnail uploaded!");
                            } else {
                                frappe.msgprint("❌ Failed to upload thumbnail");
                            }
                        }
                    });
                });

                // 🔹 Save Session → Create multiple records
                $(document).on("click", "#add-session", function () {
                    let from_time = $('#session-from').val();
                    let to_time = $('#session-to').val();

                    if (!selectedDates.length || !from_time || !to_time) {
                        frappe.msgprint("Please pick at least one date and times.");
                        return;
                    }

                    let formData = {};
                    $('#live-classroom-form').serializeArray().forEach(item => formData[item.name] = item.value);
                    formData["thumbnail"] = $("#thumbnail-hidden").val() || "";

                    // Loop through all selected dates
                    selectedDates.forEach(date => {
                        let payload = { ...formData };
                        payload["meeting_start_time"] = date + " " + from_time;
                        payload["meeting_end_time"]   = date + " " + to_time;
                        payload["scheduled_date"]     = date;

                        frappe.call({
                            method: "happyschool.happyschool.doctype.hs_student_course_enrollment.hs_student_course_enrollment.create_live_classroom",
                            args: { data: JSON.stringify(payload) },
                            callback: function (r) {
                                if (r.message && r.message.success) {
                                    frappe.msgprint("✅ Session created for " + date);
                                    fetchSessions();
                                } else {
                                    frappe.msgprint("❌ Failed to create session for " + date);
                                }
                            }
                        });
                    });
                });

                // ✅ Fetch All Sessions
                function fetchSessions() {
                    frappe.db.get_list("Live Classroom", {
                        filters: { student_id: student_id, course_id: course_id },
                        fields: ["name", "scheduled_date", "meeting_start_time", "meeting_end_time", "status"],
                        order_by: "scheduled_date asc"
                    }).then(records => { renderSavedTable(records); });
                }

                // ✅ Render Table
                function renderSavedTable(sessions) {
                    let $savedBody = $("#saved-sessions-container tbody");
                    $savedBody.empty();
                    if (!sessions || sessions.length === 0) {
                        $savedBody.append(`<tr><td colspan="6" class="text-center">No sessions found</td></tr>`);
                    } else {
                        sessions.forEach((s, idx) => {
                            $savedBody.append(`
                                <tr>
                                    <td>${idx + 1}</td>
                                    <td>${s.scheduled_date || "-"}</td>
                                    <td>${s.meeting_start_time?.split(" ")[1] || "-"}</td>
                                    <td>${s.meeting_end_time?.split(" ")[1] || "-"}</td>
                                    <td>${s.status || "-"}</td>
                                    <td>
                                        <button class="btn btn-danger btn-sm delete-session" data-id="${s.name}">
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            `);
                        });
                    }
                }

                // Initial Fetch
                fetchSessions();

                // Toggle Button
                $(document).on("click", "#toggle-sessions", function () {
                    let $savedContainer = $("#saved-sessions-container");
                    if ($savedContainer.is(":visible")) {
                        $savedContainer.slideUp(() => {
                            let offsetTop = $("#toggle-sessions").offset().top - 150;
                            $('html, body').animate({ scrollTop: offsetTop }, 500);
                        });
                        $(this).text("Show Sessions ▼");
                    } else {
                        $savedContainer.slideDown(() => {
                            $('html, body').animate({
                                scrollTop: $savedContainer.offset().top - 50
                            }, 500);
                        });
                        $(this).text("Hide Sessions ▲");
                        fetchSessions();
                    }
                });

                // Delete Session
                $(document).on("click", ".delete-session", function () {
                    let sessionId = $(this).data("id");
                    frappe.confirm("Are you sure you want to delete this session?", function () {
                        frappe.call({
                            method: "frappe.client.delete",
                            args: { doctype: "Live Classroom", name: sessionId },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint("🗑️ Session deleted successfully");
                                    fetchSessions();
                                }
                            }
                        });
                    });
                });

            } else {
                $container.html(`<p>No child row found.</p>`);
            }
        });
    } else {
        $container.html(`<p>No parameters found in URL.</p>`);
    }
};
