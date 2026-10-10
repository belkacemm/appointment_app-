from datetime import datetime
from flask_login import UserMixin
from .extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    specialization = db.Column(db.String(100))

    appointments_as_patient = db.relationship(
        "Appointment",
        foreign_keys="Appointment.patient_id",
        back_populates="patient",
    )
    appointments_as_doctor = db.relationship(
        "Appointment",
        foreign_keys="Appointment.doctor_id",
        back_populates="doctor",
    )

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )
    appointment_date = db.Column(
        db.Date,
        nullable=False,
    )
    appointment_time = db.Column(
        db.Time,
        nullable=False,
    )
    reason = db.Column(
        db.Text,
        nullable=False,
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="booked",
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    patient = db.relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="appointments_as_patient",
    )
    doctor = db.relationship(
        "User",
        foreign_keys=[doctor_id],
        back_populates="appointments_as_doctor",
    )
    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id",
            "appointment_date",
            "appointment_time",
            name="uq_doctor_appointment_slot",
        ),
    )