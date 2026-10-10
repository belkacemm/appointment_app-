from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from wtforms import DateField, SelectField, TextAreaField

class RegistrationForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8),
        ],
    )
    submit = SubmitField("Register")

class AppointmentForm(FlaskForm):
    doctor_id = SelectField(
        "Doctor",
        coerce=int,
        validators=[DataRequired()],
    )
    appointment_date = DateField(
        "Date",
        validators=[DataRequired()],
        format="%Y-%m-%d",
    )
    appointment_time = SelectField(
        "Time",
        coerce=str,
        choices=[],
        validators=[DataRequired()],
    )
    reason = TextAreaField(
        "Reason for visit",
        validators=[DataRequired()],
    )
    book_appointment = SubmitField("Book Appointment")

class AvailabilityForm(FlaskForm):
    doctor_id = SelectField(
        "Doctor",
        coerce=int,
        validators=[DataRequired()],
    )
    appointment_date = DateField(
        "Date",
        validators=[DataRequired()],
        format="%Y-%m-%d",
    )
    check_availability = SubmitField("Check Availability")    

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )
    submit = SubmitField("Login")    

class DoctorForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8),
        ],
    )
    specialization = StringField(
        "Specialization",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    submit = SubmitField("Create Doctor")

class AdminForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8),
        ],
    )
    submit = SubmitField("Create Administrator")

class AppointmentFilterForm(FlaskForm):
    doctor_id = SelectField(
        "Doctor",
        coerce=int,
        choices=[],
    )

    appointment_date = DateField(
        "Date",
        format="%Y-%m-%d",
        validators=[],
    )

    status = SelectField(
        "Status",
        choices=[
            ("", "All"),
            ("booked", "Booked"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
    )

    filter_appointments = SubmitField("Filter")
