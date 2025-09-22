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

    return { "tutor_exam": tutor_exam.tutor_exam_table,
             "name": tutor_exam.name }

@frappe.whitelist()
def submit_tutor_exam(exam_name, answers):
    tutor_exam = frappe.get_doc("Tutor Exam Result", exam_name)
    answers = frappe.parse_json(answers)
    score = 0
    for i, entry in enumerate(tutor_exam.tutor_exam_table):
        entry.tutor_answer = answers.get(str(i))
        if entry.tutor_answer == entry.answer:
            score += 1
    tutor_exam.score = score
    tutor_exam.save(ignore_permissions=True)
    return {"score": score, "total": len(tutor_exam.tutor_exam_table)}