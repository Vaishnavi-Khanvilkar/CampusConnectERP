from flask import Flask, render_template, request,redirect,url_for,session,send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date

app = Flask(__name__)

app.secret_key = "campusconnect_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campusconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config["PROFILE_UPLOAD_FOLDER"] = "static/uploads/profile"

db = SQLAlchemy()
db.init_app(app)
# ---------------- MODELS ----------------


class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    prn = db.Column(db.String(50), unique=True)

    email = db.Column(db.String(100))

    department = db.Column(db.String(100))

    semester = db.Column(db.String(20))

    attendance = db.Column(db.Integer, default=0)

    assignments = db.Column(db.Integer, default=0)
    
    username = db.Column(db.String(100), unique=True)
    
    password = db.Column(db.String(100))


class Attendance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    subject = db.Column(db.String(100))
    total_classes = db.Column(db.Integer)
    attended_classes = db.Column(db.Integer)

    student = db.relationship(
        "Student",
        backref="attendance_records"
    )

class Notice(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))

class Event(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100))
    event_date = db.Column(db.String(50))
    venue = db.Column(db.String(100))
    description = db.Column(db.Text)

class Assignment(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    title = db.Column(db.String(100))
    due_date = db.Column(db.String(50))
    status = db.Column(db.String(50))
    file = db.Column(db.String(100))

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    department = db.Column(db.String(100))
    subject = db.Column(db.String(100))

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    

    
# ---------------- ROUTES ----------------



@app.route("/")
def home():

    return render_template('index.html')

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route('/student', methods=['GET', 'POST'])
def student():

    error = None

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        student = Student.query.filter_by(
            username=username,
            password=password
        ).first()

        if student:

            session["student_id"] = student.id

            return redirect("/student_dashboard")

        else:
            error = "Invalid Username or Password"

    return render_template("student_login.html", error=error)

@app.route("/student_dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    notice_list = Notice.query.all()
    event_list = Event.query.all()

    overall_attendance = student.attendance

    return render_template(
        "student_dashboard.html",
        student=student,
        overall_attendance=overall_attendance,
        assignments=Assignment.query.count(),
        notices=notice_list,
        events=event_list
    )

@app.route("/student_logout")
def student_logout():

    session.pop("student_id", None)

    return redirect("/student")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    message = None

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        if student.password == old_password:

            student.password = new_password
            db.session.commit()

            message = "Password changed successfully."

        else:

            message = "Current password is incorrect."

    return render_template(
        "student_change_password.html",
        student=student,
        message=message
    )
    
@app.route("/student_profile")
def student_profile():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    return render_template(
        "student_profile.html",
        student=student
    )    


@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    
    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        teacher = Teacher.query.filter_by(
            username=username,
            password=password
        ).first()

        if teacher:

            session["teacher_id"] = teacher.id

            return redirect("/teacher_dashboard")

        else:
            error = "Invalid Username or Password"

    return render_template(
        "teacher_login.html",
        error=error
    )
    
@app.route("/teacher_logout")
def teacher_logout():

    session.pop("teacher_id", None)

    return redirect("/teacher")

@app.route("/teacher_dashboard")
def teacher_dashboard():

    # Check teacher login
    if "teacher_id" not in session:

        return redirect(url_for("teacher"))


    # Get logged-in teacher
    teacher = Teacher.query.get(session["teacher_id"])


    # If teacher does not exist
    if teacher is None:

        session.pop("teacher_id", None)

        return redirect(url_for("teacher"))


    # Dashboard statistics

    students = Student.query.count()

    assignments = Assignment.query.count()

    notices = Notice.query.all()

    events = Event.query.all()


    # Render teacher dashboard

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        students=students,
        assignments=assignments,
        notices=notices,
        events=events
    )
    
@app.route("/teacher_change_password", methods=["GET", "POST"])
def teacher_change_password():

    if "teacher_id" not in session:
        return redirect("/teacher")

    teacher = Teacher.query.get(session["teacher_id"])

    message = None

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        if teacher.password == old_password:

            teacher.password = new_password
            db.session.commit()

            message = "Password changed successfully."

        else:

            message = "Current password is incorrect."

    return render_template(
        "teacher_change_password.html",
        teacher=teacher,
        message=message
    )
    
@app.route("/teacher_profile")
def teacher_profile():

    if "teacher_id" not in session:
        return redirect("/teacher")

    teacher = Teacher.query.get(session["teacher_id"])

    return render_template(
        "teacher_profile.html",
        teacher=teacher
    )
    

@app.route('/admin', methods=['GET','POST'])
def admin():

    error = None

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":

            session["admin"] = username

            return redirect("/admin_dashboard")

        else:
            error = "Invalid Admin Login"


    return render_template(
        "admin_login.html",
        error=error
    )
    
@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")
    
    return render_template(
        "admin_dashboard.html",
        students=Student.query.count(),
        teachers=Teacher.query.count(),
        assignments=Assignment.query.count(),
        notices=Notice.query.count(),
        events=Event.query.count()
    )   


@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin")


@app.route('/add_student', methods=['GET','POST'])
def add_student():
    if "admin" not in session:
        return redirect("/admin")
    if request.method == "POST":

        name = request.form['name']
        prn = request.form['prn']
        email = request.form['email']
        department = request.form['department']
        semester = request.form['semester']

        student = Student(
            name=request.form["name"],
            email=request.form["email"],
            department=request.form["department"],
            semester=request.form["semester"],
            prn=request.form["prn"],
            username=request.form["username"],
            password=request.form["password"]
        )
        db.session.add(student)
        db.session.commit()

        return redirect('/admin_dashboard')

    return render_template("add_student.html")


@app.route("/add_notice", methods=["GET", "POST"])
def add_notice():

    if "admin" not in session:
        return redirect("/admin")
    
    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        notice = Notice(
            title=title,
            description=description
        )

        db.session.add(notice)
        db.session.commit()

        return redirect("/admin_dashboard")

    return render_template("add_notice.html")


@app.route("/view_students")
def view_students():
    if "admin" not in session:
        return redirect("/admin")

    if "admin" not in session:
        return redirect("/admin")

    search = request.args.get("search")

    if search:

        students = Student.query.filter(
            (Student.name.contains(search)) |
            (Student.prn.contains(search))
        ).all()

    else:

        students = Student.query.all()

    return render_template(
        "view_students.html",
        students=students
    )
    
    
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    
    if "admin" not in session:
        return redirect("/admin")
    
    student = Student.query.get_or_404(id)

    if request.method == "POST":

        student.name = request.form["name"]
        student.prn = request.form["prn"]
        student.email = request.form["email"]
        student.department = request.form["department"]
        student.semester = request.form["semester"]

        db.session.commit()

        return redirect("/view_students")

    return render_template(
        "edit_student.html",
        student=student
    )
    
@app.route("/delete_student/<int:id>")
def delete_student(id):
    
    if "admin" not in session:
        return redirect("/admin")
    
    student = Student.query.get_or_404(id)

    db.session.delete(student)
    db.session.commit()

    return redirect("/view_students")    
    

@app.route("/attendance")
def attendance():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    attendance = Attendance.query.filter_by(
        student_id=student.id
    ).all()

    overall_attendance = student.attendance

    return render_template(
        "attendance.html",
        attendance=attendance,
        overall_attendance=overall_attendance,
        student=student
    )


@app.route("/notices")
def notices():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    notice_list = Notice.query.all()

    return render_template(
        "notices.html",
        student=student,
        notices=notice_list
    )



@app.route("/view_notices")
def view_notices():

    if "admin" not in session:
        return redirect("/admin")

    search = request.args.get("search")

    if search:
        notices = Notice.query.filter(
            Notice.title.contains(search)
        ).all()
    else:
        notices = Notice.query.all()

    return render_template(
        "view_notices.html",
        notices=notices
    )


@app.route("/edit_notice/<int:id>", methods=["GET", "POST"])
def edit_notice(id):

    if "admin" not in session:
        return redirect("/admin")

    notice = Notice.query.get_or_404(id)

    if request.method == "POST":

        notice.title = request.form["title"]
        notice.description = request.form["description"]

        db.session.commit()

        return redirect("/view_notices")

    return render_template(
        "edit_notice.html",
        notice=notice
    )
    
    
@app.route("/delete_notice/<int:id>")
def delete_notice(id):

    # Allow both Admin and Teacher
    if "admin" not in session and "teacher_id" not in session:
        return redirect("/teacher")

    notice = Notice.query.get_or_404(id)

    db.session.delete(notice)
    db.session.commit()

    # Return to the correct page
    if "teacher_id" in session:
        return redirect(url_for("teacher_notices"))

    return redirect(url_for("view_notices"))


@app.route("/events")
def events():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    event_list = Event.query.all()

    return render_template(
        "events.html",
        student=student,
        events=event_list
    )
    
    
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():

    if "admin" not in session:
        return redirect("/admin")
    
    if request.method == "POST":

        event = Event(
            event_name=request.form["event_name"],
            event_date=request.form["event_date"],
            venue=request.form["venue"],
            description=request.form["description"]
        )

        db.session.add(event)
        db.session.commit()

        return redirect('/view_events')

    return render_template("add_event.html",current_date=date.today().isoformat())


@app.route("/view_events")
def view_events():

    if "admin" not in session:
        return redirect("/admin")

    search = request.args.get("search")

    if search:
        events = Event.query.filter(
            Event.event_name.contains(search)
        ).all()
    else:
        events = Event.query.all()

    return render_template(
        "view_events.html",
        events=events
    )


@app.route("/edit_event/<int:id>", methods=["GET", "POST"])
def edit_event(id):

    if "admin" not in session:
        return redirect("/admin")

    event = Event.query.get_or_404(id)

    if request.method == "POST":
        event.event_name = request.form["event_name"]
        event.event_date = request.form["event_date"]
        event.venue = request.form["venue"]
        event.description = request.form["description"]

        db.session.commit()

        return redirect("/view_events")

    return render_template(
        "edit_events.html",
        event=event
    )


@app.route('/delete_event/<int:id>')
def delete_event(id):

    if "admin" not in session:
        return redirect("/admin")
    
    event = Event.query.get_or_404(id)

    db.session.delete(event)
    db.session.commit()

    return redirect('/view_events')


    
@app.route("/add_attendance", methods=["GET", "POST"])
def add_attendance():

    if "teacher_id" not in session:
        return redirect("/teacher")

    students = Student.query.all()

    if request.method == "POST":

        student_id = request.form["student_id"]
        subject = request.form["subject"]
        attendance_status = request.form["attendance"]

        # Find existing attendance record
        attendance = Attendance.query.filter_by(
            student_id=student_id,
            subject=subject
        ).first()

        # If no record exists for this subject
        if attendance is None:

            attendance = Attendance(
                student_id=student_id,
                subject=subject,
                total_classes=1,
                attended_classes=1 if attendance_status == "Present" else 0
            )

            db.session.add(attendance)

        # If record already exists
        else:

            attendance.total_classes += 1

            if attendance_status == "Present":
                attendance.attended_classes += 1

        # Update student's overall attendance
        student = Student.query.get(student_id)

        records = Attendance.query.filter_by(
            student_id=student_id
        ).all()

        total = sum(
            record.total_classes
            for record in records
        )

        attended = sum(
            record.attended_classes
            for record in records
        )

        if total > 0:
            student.attendance = round(
                (attended / total) * 100
            )
        else:
            student.attendance = 0

        db.session.commit()

        return redirect("/teacher_dashboard")

    return render_template(
        "add_attendance.html",
        students=students
    )
    
@app.route("/view_attendance")
def view_attendance():

    if "admin" not in session:
        return redirect("/admin")

    attendance = Attendance.query.all()

    return render_template(
        "view_attendance.html",
        attendance=attendance
    )

@app.route("/edit_attendance/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):

    if "admin" not in session:
        return redirect("/admin")

    record = Attendance.query.get_or_404(id)

    if request.method == "POST":

        record.subject = request.form["subject"]
        record.total_classes = request.form["total_classes"]
        record.attended_classes = request.form["attended_classes"]

        db.session.commit()

        return redirect("/view_attendance")

    return render_template(
        "edit_attendance.html",
        attendance=record
    )

@app.route("/delete_attendance/<int:id>")
def delete_attendance(id):

    if "admin" not in session:
        return redirect("/admin")

    record = Attendance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    return redirect("/view_attendance")

@app.route("/upload_assignment", methods=["GET","POST"])
def upload_assignment():

    if "teacher_id" not in session:
        return redirect("/teacher")
    
    if request.method == "POST":

        subject = request.form["subject"]
        title = request.form["title"]
        due_date = request.form["due_date"]
        status = request.form["status"]


        file = request.files["file"]

        filename = file.filename

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        file.save(filepath)


        new_assignment = Assignment(
            subject=subject,
            title=title,
            due_date=due_date,
            status=status,
            file=filename
        )

        db.session.add(new_assignment)

        # Increase assignment count for all students
        students = Student.query.all()
        for student in students:
            student.assignments += 1

        db.session.commit()
        

        return render_template(
            "upload_assignment.html",
            message="Assignment Uploaded Successfully"
        )


    return render_template("upload_assignment.html")

@app.route("/teacher_assignments")
def teacher_assignments():

    if "teacher_id" not in session:
        return redirect("/teacher")

    assignments = Assignment.query.all()

    return render_template(
        "teacher_assignments.html",
        assignments=assignments
    )


@app.route("/add_assignment", methods=["GET", "POST"])
def add_assignment():
    
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":

        subject = request.form["subject"]
        title = request.form["title"]
        due_date = request.form["due_date"]
        status = request.form["status"]

        assignment = Assignment(
            subject=subject,
            title=title,
            due_date=due_date,
            status=status
        )

        db.session.add(assignment)
        db.session.commit()

        return redirect("/view_assignments")

    return render_template("add_assignment.html")

@app.route("/view_assignments")
def view_assignments():

    if "admin" not in session:
        return redirect("/admin")

    search = request.args.get("search")

    if search:
        assignments = Assignment.query.filter(
            (Assignment.subject.contains(search)) |
            (Assignment.title.contains(search))
        ).all()
    else:
        assignments = Assignment.query.all()

    return render_template(
        "view_assignments.html",
        assignments=assignments
    )

@app.route("/edit_assignment/<int:id>", methods=["GET", "POST"])
def edit_assignment(id):
    
    if "admin" not in session:
        return redirect("/admin")

    assignment = Assignment.query.get_or_404(id)

    if request.method == "POST":

        assignment.subject = request.form["subject"]
        assignment.title = request.form["title"]
        assignment.due_date = request.form["due_date"]
        assignment.status = request.form["status"]

        db.session.commit()

        return redirect("/view_assignments")

    return render_template(
        "edit_assignment.html",
        assignment=assignment
    )

@app.route("/delete_assignment/<int:id>")
def delete_assignment(id):
    
    if "admin" not in session:
        return redirect("/admin")

    assignment = Assignment.query.get_or_404(id)

    db.session.delete(assignment)
    db.session.commit()

    return redirect("/view_assignments")


@app.route("/post_notice", methods=["GET","POST"])
def post_notice():

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        new_notice = Notice(
            title=title,
            description=description
        )

        db.session.add(new_notice)
        db.session.commit()

        return redirect(url_for("teacher_notices"))

    return render_template("post_notice.html")

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    
    if "admin" not in session:
        return redirect("/admin")
    
    if request.method == "POST":
        teacher = Teacher(
            name=request.form["name"],
            email=request.form["email"],
            department=request.form["department"],
            subject=request.form["subject"],
            username=request.form["username"],
            password=request.form["password"]
        )

        db.session.add(teacher)
        db.session.commit()

        return redirect("/view_teacher")

    return render_template("add_teacher.html")

@app.route("/view_teacher")
def view_teachers():
    
    if "admin" not in session:
        return redirect("/admin")
    
    teachers = Teacher.query.all()
    return render_template(
        "view_teacher.html",
        teachers=teachers
    )

@app.route("/edit_teacher/<int:id>", methods=["GET", "POST"])
def edit_teacher(id):
    
    if "admin" not in session:
        return redirect("/admin")
    
    teacher = Teacher.query.get_or_404(id)

    if request.method == "POST":
        teacher.name = request.form["name"]
        teacher.email = request.form["email"]
        teacher.department = request.form["department"]
        teacher.subject = request.form["subject"]
        teacher.username = request.form["username"]
        teacher.password = request.form["password"]
        
        db.session.commit()
        return redirect("/view_teacher")

    return render_template("edit_teacher.html", teacher=teacher)


@app.route("/delete_teacher/<int:id>")
def delete_teacher(id):
    
    if "admin" not in session:
        return redirect("/admin")
    
    teacher = Teacher.query.get_or_404(id)

    db.session.delete(teacher)
    db.session.commit()

    return redirect("/view_teacher")

@app.route("/teacher_events")
def teacher_events():

    if "teacher_id" not in session:
        return redirect("/teacher")

    teacher = Teacher.query.get(session["teacher_id"])

    events = Event.query.all()

    return render_template(
        "teacher_events.html",
        teacher=teacher,
        events=events
    )
    
@app.route("/teacher_notices")
def teacher_notices():

    if "teacher_id" not in session:
        return redirect("/teacher")

    teacher = Teacher.query.get(session["teacher_id"])

    notices = Notice.query.all()

    return render_template(
        "teacher_notices.html",
        teacher=teacher,
        notices=notices
    )   


from flask import send_from_directory

@app.route("/download_assignment/<filename>")
def download_assignment(filename):

    if (
        "admin" not in session and
        "teacher_id" not in session and
        "student_id" not in session
    ):
        return redirect("/")

    return send_from_directory(
        "static/uploads",
        filename,
        as_attachment=True
    )
    
@app.route("/assignments")
def student_assignments():

    if "student_id" not in session:
        return redirect("/student")

    student = Student.query.get(session["student_id"])

    assignments = Assignment.query.all()

    return render_template(
        "assignments.html",
        student=student,
        assignments=assignments
    )


# ---------------- DATABASE ----------------



if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        # ---------------- Sample Student ----------------
        if Student.query.count() == 0:

            student = Student(
                name="Vaishnavi Khanvilkar",
                prn="PRN001",
                email="vaishnavi@gmail.com",
                department="Computer Engineering",
                semester="5",
                attendance=92,
                assignments=3,
                username="student",
                password="student123"
            )

            db.session.add(student)
            db.session.commit()

        student = Student.query.first()

        # ---------------- Notices ----------------

        if Notice.query.count() == 0:

            db.session.add(Notice(
                title="Exam schedule released",
                description="Semester exam timetable has been published."
            ))

            db.session.add(Notice(
                title="Holiday notice",
                description="College will remain closed on announced holiday."
            ))

            db.session.add(Notice(
                title="New assignment uploaded",
                description="New assignments are available."
            ))

        # ---------------- Events ----------------

        if Event.query.count() == 0:

            db.session.add(Event(
                event_name="Technical Event",
                event_date="25 July 2026",
                venue="College Auditorium",
                description="Technical seminar for Computer Engineering students."
            ))

            db.session.add(Event(
                event_name="Sports Day",
                event_date="30 July 2026",
                venue="College Ground",
                description="Annual Sports Competition."
            ))

        # ---------------- Attendance ----------------

        if Attendance.query.count() == 0:

            db.session.add(Attendance(
                student_id=student.id,
                subject="Operating System",
                total_classes=50,
                attended_classes=46
            ))

            db.session.add(Attendance(
                student_id=student.id,
                subject="Cloud Computing",
                total_classes=45,
                attended_classes=40
            ))

            db.session.add(Attendance(
                student_id=student.id,
                subject="Java",
                total_classes=50,
                attended_classes=47
            ))

        # ---------------- Assignments ----------------

        if Assignment.query.count() == 0:

            db.session.add(Assignment(
                subject="Operating System",
                title="Process Scheduling",
                due_date="15 July 2026",
                status="Pending",
                file="os_assignment.pdf"
            ))

            db.session.add(Assignment(
                subject="Cloud Computing",
                title="AWS Introduction",
                due_date="18 July 2026",
                status="Submitted",
                file="aws_intro.pdf"
            ))

            db.session.add(Assignment(
                subject="Computer Network",
                title="OSI Model",
                due_date="20 July 2026",
                status="Not Started",
                file="osi_model.pdf"
            ))

            db.session.commit()
        app.run(debug=True)