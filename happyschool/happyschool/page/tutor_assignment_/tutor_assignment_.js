frappe.pages['tutor-assignment-'].on_page_load = function (wrapper) {
    new TutorAssignmentPage(wrapper);
};

class TutorAssignmentPage {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            single_column: true
        });
        this.answers = {};
        this.current = 0;
        this.submitted = false;
        this.questions = [];
        this.subjects = [];
        this.timer_duration = 300; // seconds

        this.setup_dom();
        this.load_subjects();
        this.bind_events();
    }

    setup_dom() {
        // Main container
        this.$container = $('<div id="exam-center-container"></div>').appendTo(this.page.body);

        // Subject select (Frappe control)
        this.subject_control = frappe.ui.form.make_control({
            parent: this.$container[0],
            df: {
                fieldtype: 'Select',
                label: 'Select Subject',
                fieldname: 'subject_select',
                options: ['Loading...'],
                reqd: 1
            },
            render_input: true
        });

        // Start button
        this.$startBtn = $('<button class="btn btn-success">Start Exam</button>').appendTo(this.$container);

        // Timer
        this.$timer = $('<div id="exam-timer" style="display:none"></div>').appendTo(this.$container);

        // Questions container
        this.$questions = $('<div id="questions-container" style="display:none"></div>').appendTo(this.$container);

        // Styles
        frappe.dom.set_style(`
            #exam-center-container {
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: 70vh;
                border-radius: 16px;
                padding: 40px 20px; box-shadow: 0 4px 24px rgba(30,144,255,0.08);
            }
            #exam-center-container label { font-weight: bold; }
            #exam-center-container .btn-success {
                background-color: #1e90ff !important;
                border-color: #1e90ff !important; color: #fff !important;
                margin-bottom: 20px;
            }
            #exam-timer {
                font-size: 1.5em; font-weight: bold;
                padding: 10px 24px; border-radius: 8px;
                margin-bottom: 20px; border: 2px solid #ffe066;
                display: none;
            }
            #questions-container { display: none; width:100%; max-width:600px; }
            #questions-container .card { border: 2px solid #1e90ff; border-radius: 12px; }
            #questions-container .card-title { color: #1e90ff; }
        `);
    }

    bind_events() {
        this.$startBtn.on('click', () => this.start_exam());
    }

    load_subjects() {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Tutor Subject",
                fields: ["name", "subject"],
                limit_page_length: 50
            },
            callback: (r) => {
                this.subjects = r.message || [];
                const options = ['Select a subject', ...this.subjects.map(sub => sub.subject)];
                this.subject_control.df.options = options;
                this.subject_control.refresh();
            }
        });
    }

    start_exam() {
        const subject_label = this.subject_control.get_value();
        if (!subject_label || subject_label === 'Select a subject') {
            frappe.msgprint("Please select a subject before starting the exam.");
            return;
        }
        const subject = this.subjects.find(sub => sub.subject === subject_label)?.name;
        if (!subject) {
            frappe.msgprint("Invalid subject selected.");
            return;
        }
        this.$startBtn.hide();
        $(this.subject_control.$wrapper).hide();
        this.$timer.show();
        this.$questions.show();
        this.block_navigation(); // Block navigation
        this.render_questions(subject);
    }

    block_navigation() {
        // Block refresh/close
        window.addEventListener('beforeunload', this.beforeUnloadHandler);
        // Block browser back
        window.history.pushState(null, '', window.location.href);
        window.addEventListener('popstate', this.popStateHandler);
    }

    beforeUnloadHandler(e) {
        e.preventDefault();
        e.returnValue = '';
    }

    popStateHandler(e) {
        window.history.pushState(null, '', window.location.href);
        frappe.msgprint('You cannot leave the exam page until you submit.');
    }

    submit_exam() {
        if (this.submitted) return;
        this.submitted = true;
        this.unblock_navigation(); // Unblock navigation
        frappe.msgprint("Exam submitted!<br>Answers: " + JSON.stringify(this.answers));
        this.$questions.html('<div class="alert alert-info">Exam submitted.</div>');
    }

    unblock_navigation() {
        window.removeEventListener('beforeunload', this.beforeUnloadHandler);
        window.removeEventListener('popstate', this.popStateHandler);
    }

    start_timer(duration, on_expire) {
        const endTime = Date.now() + duration * 1000;
        if (window.exam_timer_interval) clearInterval(window.exam_timer_interval);

        window.exam_timer_interval = setInterval(() => {
            const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
            const h = String(Math.floor(remaining / 3600)).padStart(2, '0');
            const m = String(Math.floor((remaining % 3600) / 60)).padStart(2, '0');
            const s = String(remaining % 60).padStart(2, '0');
            this.$timer.text(`Time Remaining: ${h}:${m}:${s}`);
            if (remaining <= 0) {
                clearInterval(window.exam_timer_interval);
                this.$timer.text("Time's up!");
                on_expire();
            }
        }, 1000);
    }

    render_questions(subject) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Tutor Assessment Question",
                fields: ["name", "question", "a", "b", "c", "d"],
                filters: { subject },
                limit_page_length: 10
            },
            callback: (r) => {
                if (!r.message?.length) {
                    this.$questions.html('<div class="alert alert-warning">No questions found.</div>');
                    return;
                }
                this.questions = r.message.map(q => ({
                    q: q.question,
                    choices: [q.a, q.b, q.c, q.d]
                }));
                this.current = 0;
                this.submitted = false;
                this.answers = {};
                this.show_question(this.current);
                this.start_timer(this.timer_duration, () => this.submit_exam());
            }
        });
    }

    show_question(idx) {
        if (this.submitted) return;
        const q = this.questions[idx];
        this.$questions.html(`
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">Question ${idx + 1} of ${this.questions.length}</h5>
                    <p class="card-text"><b>${q.q}</b></p>
                    <form id="question-form">
                        ${q.choices.map((choice, i) => `
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="radio" 
                                    name="answer" id="choice_${i}" 
                                    value="${String.fromCharCode(65 + i)}"
                                    ${this.answers[idx] === String.fromCharCode(65 + i) ? 'checked' : ''}>
                                <label class="form-check-label ms-2" for="choice_${i}">
                                    ${String.fromCharCode(65 + i)}. ${choice}
                                </label>
                            </div>
                        `).join('')}
                    </form>
                    <div class="mt-3 d-flex gap-2 justify-content-center">
                        <button type="button" class="btn btn-secondary prev-btn" ${idx === 0 ? 'disabled' : ''}>Previous</button>
                        <button type="button" class="btn btn-secondary next-btn" ${idx === this.questions.length - 1 ? 'disabled' : ''}>Next</button>
                        ${idx === this.questions.length - 1 ? '<button type="button" class="btn btn-primary submit-btn">Submit</button>' : ''}
                    </div>
                </div>
            </div>
        `);

        $('#question-form input[name="answer"]').on('change', e => {
            this.answers[idx] = e.target.value;
        });

        $('.prev-btn').on('click', () => { if (this.current > 0) this.show_question(--this.current); });
        $('.next-btn').on('click', () => { if (this.current < this.questions.length - 1) this.show_question(++this.current); });
        $('.submit-btn').on('click', () => this.submit_exam());
    }
}


