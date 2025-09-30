import frappe

def get_context(context):
    # If user is not logged in, redirect to login page
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # If logged in, pass user details to template
    context.title = "Secure Page"
    context.username = frappe.session.user
    context.fullname = frappe.db.get_value("User", frappe.session.user, "full_name")


@frappe.whitelist()
def create_tutor_exam(subject):
    check_user = frappe.db.get_value("Tutor Profile", {"user": frappe.session.user})
    if not check_user:
        frappe.throw("Please complete your Tutor Profile before taking the exam.")
    
    questions = frappe.get_all("Tutor Assessment Question", filters={"subject": subject}, 
                               fields=["name", "question", "answer", "a", "b", "c", "d"])
    tutor_exam_exists = frappe.db.exists("Tutor Exam Result", {"tutor": check_user, "subject": subject})
    if tutor_exam_exists:
        frappe.throw("You have already taken the exam for this subject.")
    
    tutor_exam = frappe.new_doc("Tutor Exam Result")
    tutor_exam.tutor = check_user
    tutor_exam.subject = subject
    tutor_exam.date = frappe.utils.nowdate()
    for qt in questions:
        tutor_exam.append("tutor_exam_table", {
            "question_name": qt.name,
            "question": qt.question,
            "answer": qt.answer,
            "a": qt.a,
            "b": qt.b,
            "c": qt.c,
            "d": qt.d
        })
    tutor_exam.insert(ignore_permissions=True)
    # tutor_exam.submit()
    return { "tutor_exam": tutor_exam.tutor_exam_table,
             "name": tutor_exam.name }

@frappe.whitelist()
def submit_tutor_exam(exam_name, answers, time):
    tutor_exam = frappe.get_doc("Tutor Exam Result", exam_name)
    answers = frappe.parse_json(answers)
    score = 0
    for i, entry in enumerate(tutor_exam.tutor_exam_table):
        entry.tutor_answer = answers.get(str(i))
        if entry.tutor_answer == entry.answer:
            score += 1
    # get 90% of score
    total_questions = len(tutor_exam.tutor_exam_table)
    passing_score = int(0.9 * total_questions)
    tu_pro = frappe.get_doc("Tutor Profile", {"user": frappe.session.user})
    
    if score >= passing_score:
        is_pass = "Pass"
        tu_pro.status = "Exam Passed"
    else:
        is_pass = "Failed"
        tu_pro.status = "Exam Failed"
    tu_pro.save(ignore_permissions=True)
    settings = frappe.get_single("Happy School Setting")
    time = round(settings.exam_time - float(time)/60,2)   
    tutor_exam.time_taken = time
    tutor_exam.total_score = score
    tutor_exam.save(ignore_permissions=True)
    tutor_exam.submit()
    return {
        "score": score,
        "total": total_questions,
        "passing_score": passing_score,
        "is_pass": is_pass
    }


@frappe.whitelist()
def get_tutor_settings():
    settings = frappe.get_single("Happy School Setting")
    if settings.exam_time <= 0:
        frappe.throw("Exam Time is Not Set in Happy School Setting.")
    exam_time = settings.exam_time * 60
    return {
        "exam_time": exam_time
    }
