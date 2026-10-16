from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from .extensions import db
from .forms import RegistrationForm, AppointmentForm, LoginForm, AvailabilityForm, DoctorForm, AdminForm, AppointmentFilterForm
from .models import User, Appointment
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time, date

main = Blueprint("main", __name__)

def generate_time_slots():
    return [time(9,0), 
            time(9,30), 
            time(10,0), 
            time(10,30),
            time(11,0),
            time(11,30),
            time(13,0),
            time(13,30),
            time(14,0),
            time(14,30),
            time(15,0),
            time(15,30),
            time(16,0),
            time(16,30),
            ]

def get_available_time_slots(doctor_id, appointment_date):
    booked_times = {
        appointment.appointment_time
        for appointment in Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status="booked",
        ).all()
    }

    available_slots = [
        slot
        for slot in generate_time_slots()
        if slot not in booked_times
    ]

    # If the selected date is today,
    # remove times that have already passed.
    if appointment_date == date.today():
        current_time = datetime.now().time()

        available_slots = [
            slot
            for slot in available_slots
            if slot > current_time
        ]

    return available_slots

@main.route("/")
def home():
    return redirect(url_for("main.login"))

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = User.query.filter_by(
            email=email
        ).first()
        if existing_user:
            form.email.errors.append(
                "An account with this email already exists."
            )
            return render_template(
                "register.html",
                form=form,
            )
        user = User(
            name=form.name.data.strip(),
            email=email,
            password=generate_password_hash(
                form.password.data
            ),
            role="patient",
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("main.home"))
    return render_template(
        "register.html",
        form=form,
    )


@main.route("/appointment", methods=["GET", "POST"])
@login_required
def appointment():
    if current_user.role != "patient":
        flash(
            "Only patients can book appointments.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    availability_form = AvailabilityForm()
    appointment_form = AppointmentForm()
    appointment_form.appointment_time.choices = []
    doctors = User.query.filter_by(role="doctor").all()
    doctor_choices = [
        (
            doctor.id,
            f"{doctor.name} - {doctor.specialization}",
        )
        for doctor in doctors
    ]
    availability_form.doctor_id.choices = doctor_choices
    appointment_form.doctor_id.choices = doctor_choices
    available_times = []
    # -------------------------
    # STEP 1: Check availability
    # -------------------------
    if (availability_form.check_availability.data and not appointment_form.book_appointment.data):
        if availability_form.validate():
            selected_doctor = availability_form.doctor_id.data
            selected_date = availability_form.appointment_date.data
            available_times = get_available_time_slots(
                selected_doctor,
                selected_date,
            )
            appointment_form.doctor_id.data = selected_doctor
            appointment_form.appointment_date.data = selected_date
            appointment_form.appointment_time.choices = [
                (slot.strftime("%H:%M"), slot.strftime("%I:%M %p"))
                for slot in available_times
            ]
            if not available_times:
                flash(
                    "No available time slots remain for the selected date.",
                    "warning",
                )
        else:
            flash("Please select a valid doctor and date.", "warning")
    # -------------------------
    # STEP 2: Book appointment
    # -------------------------
    if appointment_form.book_appointment.data:
        appointment_form.appointment_time.choices = [
            (
                slot.strftime("%H:%M"),
                slot.strftime("%I:%M %p"),
            )
            for slot in generate_time_slots()
        ]
        if appointment_form.validate():
            allowed_times = generate_time_slots()
            selected_time = datetime.strptime(
                appointment_form.appointment_time.data,
                "%H:%M",
                ).time()
            if selected_time not in allowed_times:
                appointment_form.appointment_time.errors.append(
                "Invalid appointment time."
                )
                return render_template(
                    "appointment.html",
                    availability_form=availability_form,
                    appointment_form=appointment_form,
                    available_times=[],
                    )
            selected_time = datetime.strptime(
                appointment_form.appointment_time.data,
                "%H:%M",
            ).time()
            existing_appointment = Appointment.query.filter_by(
                doctor_id=appointment_form.doctor_id.data,
                appointment_date=appointment_form.appointment_date.data,
                appointment_time=selected_time,
                status="booked",
            ).first()
            if existing_appointment:
                appointment_form.appointment_time.errors.append(
                    "This time slot is no longer available."
                )
                return render_template(
                    "appointment.html",
                    availability_form=availability_form,
                    appointment_form=appointment_form,
                    available_times=generate_time_slots(),
                )
            appointment = Appointment(
                patient_id=current_user.id,
                doctor_id=appointment_form.doctor_id.data,
                appointment_date=appointment_form.appointment_date.data,
                appointment_time=selected_time,
                reason=appointment_form.reason.data,
            )
            db.session.add(appointment)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                appointment_form.appointment_time.errors.append(
                    "This time slot was just booked by another patient."
                )
                return render_template(
                    "appointment.html",
                    availability_form=availability_form,
                    appointment_form=appointment_form,
                    available_times=[],
                )
            flash(
                "Your appointment was booked successfully.",
                "success",
            )
            return redirect(url_for("main.appointment"))
        return render_template(
            "appointment.html",
            availability_form=availability_form,
            appointment_form=appointment_form,
            available_times=[],
        )
    # -------------------------
    # GET request
    # -------------------------
    return render_template(
        "appointment.html",
        availability_form=availability_form,
        appointment_form=appointment_form,
        available_times=available_times,
    )

@main.route("/my-appointments")
@login_required
def my_appointments():
    if current_user.role != "patient":
        flash(
            "Only patients can access their appointments.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(
        Appointment.appointment_date,
        Appointment.appointment_time,
    ).all()
    return render_template(
        "my_appointments.html",
        appointments=appointments,
    )

@main.route("/appointment/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    appointment = db.session.get(
        Appointment,
        appointment_id,
    )
    if appointment is None:
        flash(
            "Appointment not found.",
            "danger",
        )
        return redirect(url_for("main.my_appointments"))
    if appointment.patient_id != current_user.id:
        flash(
            "You are not authorized to cancel this appointment.",
            "danger",
        )
        return redirect(url_for("main.my_appointments"))
    if appointment.status != "booked":
        flash(
            "This appointment cannot be cancelled.",
            "danger",
        )
        return redirect(url_for("main.my_appointments"))
    appointment.status = "cancelled"
    db.session.commit()
    flash(
        "Your appointment was cancelled successfully.",
        "success",
    )
    return redirect(url_for("main.my_appointments"))

@main.route(
    "/appointment/<int:appointment_id>/confirm",
    methods=["POST"],
)
@login_required
def confirm_appointment(appointment_id):
    if current_user.role != "doctor":
        flash(
            "Only doctors can confirm appointments.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    appointment = db.session.get(
        Appointment,
        appointment_id,
    )
    if appointment is None:
        flash(
            "Appointment not found.",
            "danger",
       )
        return redirect(url_for("main.doctor_appointments"))
    if appointment.doctor_id != current_user.id:
        flash(
            "You are not authorized to confirm this appointment.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    if appointment.status != "booked":
        flash(
            "This appointment cannot be confirmed.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    appointment.status = "confirmed"
    db.session.commit()
    flash(
        "Appointment confirmed successfully.",
        "success",
    )
    return redirect(url_for("main.doctor_appointments"))

@main.route(
    "/appointment/<int:appointment_id>/complete",
    methods=["POST"],
)
@login_required
def complete_appointment(appointment_id):
    if current_user.role != "doctor":
        flash(
            "Only doctors can complete appointments.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    appointment = db.session.get(
        Appointment,
        appointment_id,
    )
    if appointment is None:
        flash(
            "Appointment not found.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    if appointment.doctor_id != current_user.id:
        flash(
            "You are not authorized to complete this appointment.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    if appointment.status != "confirmed":
        flash(
            "Only confirmed appointments can be completed.",
            "danger",
        )
        return redirect(url_for("main.doctor_appointments"))
    appointment.status = "completed"
    db.session.commit()
    flash(
        "Appointment completed successfully.",
        "success",
    )
    return redirect(url_for("main.doctor_appointments"))

@main.route("/doctor-appointments")
@login_required
def doctor_appointments():
    if current_user.role != "doctor":
        flash(
            "You are not authorized to access this page.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).order_by(
        Appointment.appointment_date,
        Appointment.appointment_time,
    ).all()
    return render_template(
        "doctor_appointments.html",
        appointments=appointments,
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(
            user.password,
            form.password.data
            ):
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("main.admin_dashboard"))
            if user.role == "doctor":
                return redirect(url_for("main.doctor_appointments"))
            return redirect(url_for("main.appointment"))
        form.email.errors.append(
            "Invalid email or password."
        )
    return render_template(
        "login.html",
        form=form,
    )

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@main.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash(
            "Only administrators can access this page.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    return render_template(
        "admin_dashboard.html",
    )

@main.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != "admin":
        flash(
            "Only administrators can access this page.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    users = User.query.order_by(
        User.name
    ).all()
    return render_template(
        "admin_users.html",
        users=users,
    )

@main.route("/admin/users/create-doctor", methods=["GET", "POST"])
@login_required
def create_doctor():
    if current_user.role != "admin":
        flash(
            "Only administrators can create doctors.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    form = DoctorForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = User.query.filter_by(
            email=email
        ).first()
        if existing_user:
            form.email.errors.append(
                "A user with this email already exists."
            )
            return render_template(
                "create_doctor.html",
                form=form,
            )
        doctor = User(
            name=form.name.data.strip(),
            email=email,
            password=generate_password_hash(
                form.password.data
            ),
            role="doctor",
            specialization=form.specialization.data.strip(),
        )
        db.session.add(doctor)
        db.session.commit()
        flash(
            "Doctor created successfully.",
            "success",
        )
        return redirect(url_for("main.admin_users"))
    return render_template(
        "create_doctor.html",
        form=form,
    )

@main.route("/admin/users/create-admin", methods=["GET", "POST"])
@login_required
def create_admin():
    if current_user.role != "admin":
        flash(
            "Only administrators can create administrators.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    form = AdminForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = User.query.filter_by(
            email=email
        ).first()
        if existing_user:
            form.email.errors.append(
                "A user with this email already exists."
            )
            return render_template(
                "create_admin.html",
                form=form,
            )
        admin = User(
            name=form.name.data.strip(),
            email=email,
            password=generate_password_hash(
                form.password.data
            ),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        flash(
            "Administrator created successfully.",
            "success",
        )
        return redirect(url_for("main.admin_users"))
    return render_template(
        "create_admin.html",
        form=form,
    )

@main.route("/admin/appointments", methods=["GET", "POST"])
@login_required
def admin_appointments():
    if current_user.role != "admin":
        flash(
            "Only administrators can access this page.",
            "danger",
        )
        return redirect(url_for("main.appointment"))
    form = AppointmentFilterForm()
    doctors = User.query.filter_by(
        role="doctor"
    ).order_by(
        User.name
    ).all()
    form.doctor_id.choices = [
        (0, "All Doctors")
    ] + [
        (doctor.id, doctor.name)
        for doctor in doctors
    ]
    query = Appointment.query
    if request.method == "POST":
        if form.doctor_id.data != 0:
            query = query.filter(
                Appointment.doctor_id
                == form.doctor_id.data
            )
        if form.appointment_date.data:
            query = query.filter(
                Appointment.appointment_date
                == form.appointment_date.data
            )
        if form.status.data:
            query = query.filter(
                Appointment.status
                == form.status.data
            )
    appointments = query.order_by(
        Appointment.appointment_date,
        Appointment.appointment_time,
    ).all()
    return render_template(
        "admin_appointments.html",
        form=form,
        appointments=appointments,
    )
