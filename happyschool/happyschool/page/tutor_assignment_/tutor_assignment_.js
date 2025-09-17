frappe.pages['tutor-assignment-'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        single_column: true
    });

    // Container structure (reduced multiple .append calls)
    $(page.body).append(`
        <div id="exam-center-container">
            <div class="subject-container">
                <label for="subject-select">Select Subject</label>
                <select id="subject-select" class="form-control">
                    <option value="">Loading...</option>
                </select>
            </div>
            <button id="start-exam-btn" class="btn btn-success">Start Exam</button>
            <div id="exam-timer"></div>
            <div id="questions-container"></div>
        </div>
    `);

    // Scoped jQuery references (avoid repeated DOM lookups)
    const $subjectSelect = $('#subject-select');
    const $startBtn = $('#start-exam-btn');
    const $timer = $('#exam-timer');
    const $questions = $('#questions-container');

    // Styles (moved inline CSS to a single <style>)
    frappe.dom.set_style(`
        #exam-center-container {
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; min-height: 70vh;
            background: #2fa5c8; border-radius: 16px;
            padding: 40px 20px; box-shadow: 0 4px 24px rgba(30,144,255,0.08);
        }
        #exam-center-container label {
            font-weight: bold; color: #1e90ff;
        }
        #exam-center-container .subject-container {
            margin-bottom: 20px; width: 100%; max-width: 400px;
        }
        #exam-center-container .btn-success {
            background-color: #1e90ff !important;
            border-color: #1e90ff !important; color: #fff !important;
            margin-bottom: 20px;
        }
        #exam-timer {
            font-size: 1.5em; font-weight: bold;
            color: #1e90ff; background: #fffbe6;
            padding: 10px 24px; border-radius: 8px;
            margin-bottom: 20px; border: 2px solid #ffe066;
            display: none;
        }
        #questions-container { display: none; width:100%; max-width:600px; }
        #questions-container .card {
            background: #fffbe6; border: 2px solid #1e90ff; border-radius: 12px;
        }
        #questions-container .card-title { color: #1e90ff; }
        #questions-container .btn-primary {
            background-color: #ffe066 !important; border-color: #ffe066 !important;
            color: #1e90ff !important;
        }
        #questions-container .btn-secondary {
            background-color: #1e90ff !important; border-color: #1e90ff !important;
            color: #fff !important;
        }
    `);

    // Timer function
    function start_timer(duration, on_expire) {
    const endTime = Date.now() + duration * 1000;

    // Clear any existing intervals before starting a new one
    if (window.exam_timer_interval) {
        clearInterval(window.exam_timer_interval);
    }

    window.exam_timer_interval = setInterval(() => {
        const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
        const h = String(Math.floor(remaining / 3600)).padStart(2, '0');
        const m = String(Math.floor((remaining % 3600) / 60)).padStart(2, '0');
        const s = String(remaining % 60).padStart(2, '0');

        $('#exam-timer').text(`Time Remaining: ${h}:${m}:${s}`);

        if (remaining <= 0) {
            clearInterval(window.exam_timer_interval);
            $('#exam-timer').text("Time's up!");
            on_expire();
        }
    }, 1000);
}

    // Render questions
    function render_questions(subject) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Tutor Assessment Question",
                fields: ["name", "question", "a", "b", "c", "d"],
                filters: { subject },
                limit_page_length: 10
            },
            callback(r) {
                if (!r.message?.length) {
                    $questions.html('<div class="alert alert-warning">No questions found.</div>');
                    return;
                }

                const questions = r.message.map(q => ({
                    q: q.question,
                    choices: [q.a, q.b, q.c, q.d]
                }));

                let current = 0, submitted = false;
                const answers = {};

                const submit_exam = () => {
                    if (submitted) return;
                    submitted = true;
                    frappe.msgprint("Exam submitted!<br>Answers: " + JSON.stringify(answers));
                    $questions.html('<div class="alert alert-info">Exam submitted.</div>');
                };

                const show_question = (idx) => {
                    if (submitted) return;
                    const q = questions[idx];
                    $questions.html(`
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">Question ${idx + 1} of ${questions.length}</h5>
                                <p class="card-text"><b>${q.q}</b></p>
                                <form id="question-form">
                                    ${q.choices.map((choice, i) => `
                                        <div class="form-check mb-2">
                                            <input class="form-check-input" type="radio" 
                                                name="answer" id="choice_${i}" 
                                                value="${String.fromCharCode(65 + i)}"
                                                ${answers[idx] === String.fromCharCode(65 + i) ? 'checked' : ''}>
                                            <label class="form-check-label ms-2" for="choice_${i}">
                                                ${String.fromCharCode(65 + i)}. ${choice}
                                            </label>
                                        </div>
                                    `).join('')}
                                </form>
                                <div class="mt-3 d-flex gap-2 justify-content-center">
                                    <button type="button" class="btn btn-secondary prev-btn" ${idx === 0 ? 'disabled' : ''}>Previous</button>
                                    <button type="button" class="btn btn-secondary next-btn" ${idx === questions.length - 1 ? 'disabled' : ''}>Next</button>
                                    ${idx === questions.length - 1 ? '<button type="button" class="btn btn-primary submit-btn">Submit</button>' : ''}
                                </div>
                            </div>
                        </div>
                    `);

                    $('#question-form input[name="answer"]').on('change', e => {
                        answers[idx] = e.target.value;
                    });

                    $('.prev-btn').on('click', () => { if (current > 0) show_question(--current); });
                    $('.next-btn').on('click', () => { if (current < questions.length - 1) show_question(++current); });
                    $('.submit-btn').on('click', submit_exam);
                };

                show_question(current);
                start_timer(300, submit_exam);
            }
        });
    }

    // Load subjects
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Tutor Subject",
            fields: ["name", "subject"],
            limit_page_length: 50
        },
        callback(r) {
            $subjectSelect.empty().append('<option value="">Select a subject</option>');
            r.message?.forEach(sub => {
                $subjectSelect.append(`<option value="${sub.name}">${sub.subject}</option>`);
            });
        }
    });

    // Start exam button
    $startBtn.on('click', () => {
        const subject = $subjectSelect.val();
        if (!subject) return frappe.msgprint("Please select a subject before starting the exam.");
        $startBtn.hide();
        $subjectSelect.hide();
        $timer.show();
        $questions.show();
        render_questions(subject);
    });
};
