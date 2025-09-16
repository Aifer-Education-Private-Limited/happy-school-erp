frappe.pages['tutor-assignment-'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tutor Assignment ',
		single_column: true
	});
	// Add timer and questions container, hidden by default
	$(page.body).append('<button id="start-exam-btn" class="btn btn-success" style="margin-bottom:20px;">Start Exam</button>');
	$(page.body).append('<div id="exam-timer" style="font-size:1.5em;font-weight:bold;margin-bottom:10px;display:none;"></div>');
	$(page.body).append('<div id="questions-container" style="display:none;"></div>');

	function start_timer(duration, on_expire) {
	    const endTime = Date.now() + duration * 1000;
	    const timer_interval = setInterval(function () {
	        const now = Date.now();
	        let remaining = Math.max(0, Math.floor((endTime - now) / 1000));

	        const hours = String(Math.floor(remaining / 3600)).padStart(2, '0');
	        const minutes = String(Math.floor((remaining % 3600) / 60)).padStart(2, '0');
	        const seconds = String(remaining % 60).padStart(2, '0');

	        $('#exam-timer').text(`Time Remaining: ${hours}:${minutes}:${seconds}`);

	        if (remaining <= 0) {
	            clearInterval(timer_interval);
	            $('#exam-timer').text("Time's up!");
	            on_expire();
	        }
	    }, 1000);
	    return timer_interval;
	}

	function render_questions() {
	    frappe.call({
	        method: "frappe.client.get_list",
	        args: {
	            doctype: "Tutor Assessment Question",
	            fields: ["name", "question", "a", "b", "c", "d"],
	            limit_page_length: 10 // adjust as needed
	        },
	        callback: function(r) {
	            if (r.message && r.message.length) {
	                const questions = r.message.map(q => ({
	                    q: q.question,
	                    choices: [q.a, q.b, q.c, q.d]
	                }));

	                let current = 0;
	                const answers = {};
	                let submitted = false;

	                function submit_exam() {
	                    if (submitted) return;
	                    submitted = true;
	                    frappe.msgprint("Time's up or submitted!<br>Answers: " + JSON.stringify(answers));
	                    $('#questions-container').html('<div class="alert alert-info">Exam submitted.</div>');
	                }

	                function show_question(idx) {
	                    if (submitted) return;
	                    const q = questions[idx];
	                    let html = `
	                        <div class="card mb-3">
	                            <div class="card-body">
	                                <h5 class="card-title">Question ${idx + 1} of ${questions.length}</h5>
	                                <p class="card-text"><b>${q.q}</b></p>
	                                <form id="question-form">
	                                    ${q.choices.map((choice, i) => `
    <div class="form-check mb-2">
        <div style="display: flex; align-items: center;">
            <input class="form-check-input" type="radio" name="answer" id="choice_${i}" value="${String.fromCharCode(65 + i)}" ${answers[idx] === String.fromCharCode(65 + i) ? 'checked' : ''}>
            <label class="form-check-label ms-2" for="choice_${i}">${String.fromCharCode(65 + i)}</label>
        </div>
        <div style="margin-left: 2rem;">
            <span>${choice}</span>
        </div>
    </div>
`).join('')}
	                                </form>
	                                <div class="mt-3" style="display:flex;gap:1rem;">
	                                    <button type="button" class="btn btn-secondary" id="prev-btn" ${idx === 0 ? 'disabled' : ''}>Previous</button>
	                                    <button type="button" class="btn btn-secondary" id="next-btn" ${idx === questions.length - 1 ? 'disabled' : ''}>Next</button>
	                                    ${idx === questions.length - 1 ? '<button type="button" class="btn btn-primary" id="submit-btn">Submit</button>' : ''}
	                                </div>
	                            </div>
	                        </div>
	                    `;
	                    $('#questions-container').html(html);

	                    $('#question-form input[name="answer"]').on('change', function() {
	                        answers[idx] = $(this).val();
	                    });

	                    $('#prev-btn').on('click', function() {
	                        if (current > 0) {
	                            current--;
	                            show_question(current);
	                        }
	                    });
	                    $('#next-btn').on('click', function() {
	                        if (current < questions.length - 1) {
	                            current++;
	                            show_question(current);
	                        }
	                    });
	                    $('#submit-btn').on('click', function() {
	                        submit_exam();
	                    });
	                }

	                show_question(current);

	                // Start 5 min timer (300 seconds)
	                start_timer(300, submit_exam);
	            } else {
	                $('#questions-container').html('<div class="alert alert-warning">No questions found.</div>');
	            }
	        }
	    });
	}

	// Show exam only after clicking start
	$('#start-exam-btn').on('click', function() {
	    $(this).hide();
	    $('#exam-timer').show();
	    $('#questions-container').show();
	    render_questions();
	});

	// Initial render
}