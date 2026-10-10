from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from booking.extensions import db
from booking.models import Appointment


def test_appointment_relationships(app, users):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
    )

    db.session.add(appointment)
    db.session.commit()

    saved = db.session.get(Appointment, appointment.id)

    assert saved.patient.name == "Test Patient"
    assert saved.doctor.name == "Test Doctor"
    assert saved.status == "booked"


def test_doctor_cannot_have_duplicate_time_slot(app, users):
    appointment_date = date(2099, 5, 20)

    first = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=appointment_date,
        appointment_time=time(9, 0),
        reason="First appointment",
    )

    db.session.add(first)
    db.session.commit()

    second = Appointment(
        patient_id=users["second_patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=appointment_date,
        appointment_time=time(9, 0),
        reason="Second appointment",
    )

    db.session.add(second)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()