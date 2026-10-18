from datetime import date, datetime, time

from booking.extensions import db
from booking.models import Appointment
from booking.routes import (
    generate_time_slots,
    get_available_time_slots,
)

def test_booked_time_is_excluded(app, users):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
    )

    db.session.add(appointment)
    db.session.commit()

    available_slots = get_available_time_slots(
        users["doctor"].id,
        date(2099, 5, 20),
    )

    assert time(9, 0) not in available_slots
    assert time(9, 30) in available_slots

def test_cancelled_time_is_available_again(app, users):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
        status="booked",
    )

    db.session.add(appointment)
    db.session.commit()

    appointment.status = "cancelled"
    db.session.commit()

    available_slots = get_available_time_slots(
        users["doctor"].id,
        date(2099, 5, 20),
    )

    assert time(9, 0) in available_slots

def test_different_doctor_can_use_same_time_slot(app, users):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
        status="booked",
    )

    db.session.add(appointment)
    db.session.commit()

    other_doctor = users["doctor2"]

    available_slots = get_available_time_slots(
        other_doctor.id,
        date(2099, 5, 20),
    )

    assert time(9, 0) in available_slots

def test_past_time_slots_are_excluded_today(app, users, monkeypatch):
    from booking import routes

    today = date.today()

    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime.combine(today, time(10, 15))

    monkeypatch.setattr(routes, "datetime", FakeDateTime)

    available_slots = get_available_time_slots(
        users["doctor"].id,
        today,
    )

    assert time(9, 0) not in available_slots
    assert time(10, 0) not in available_slots
    assert time(10, 30) in available_slots

def test_doctor_cannot_access_appointment_booking(
    app, client, users
):
    with client:
        # Log in as the doctor
        response = client.post(
            "/login",
            data={
                "email": users["doctor"].email,
                "password": "test-password",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Try to access the patient booking page
        response = client.get(
            "/appointment",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.location.endswith("/doctor-appointments")

def test_patient_cannot_book_an_already_booked_slot(
    app, client, users
):
    from datetime import date, time

    from booking.extensions import db
    from booking.models import Appointment

    appointment_date = date(2099, 5, 20)
    appointment_time = time(9, 0)

    # Arrange: book the slot before the patient submits a request.
    existing_appointment = Appointment(
        patient_id=users["second_patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason="Existing appointment",
        status="booked",
    )
    db.session.add(existing_appointment)
    db.session.commit()

    # Log in as another patient.
    login_response = client.post(
        "/login",
        data={
            "email": users["patient"].email,
            "password": "test-password",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Act: attempt to book the same doctor's time slot.
    response = client.post(
        "/appointment",
        data={
            "doctor_id": str(users["doctor"].id),
            "appointment_date": "2099-05-20",
            "appointment_time": "09:00",
            "reason": "Another appointment",
            "book_appointment": "Book Appointment",
        },
        follow_redirects = False
    )

    # Assert: the route rejects the duplicate booking.
    assert response.status_code == 200
    assert b"This time slot is no longer available." in response.data

    matching_appointments = Appointment.query.filter_by(
        doctor_id=users["doctor"].id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status="booked",
    ).all()

    assert len(matching_appointments) == 1

def test_patient_can_cancel_own_appointment(app, client, users):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
        status="booked",
    )

    db.session.add(appointment)
    db.session.commit()

    appointment_id = appointment.id

    # Log in as the patient who owns the appointment.
    client.post(
        "/login",
        data={
            "email": users["patient"].email,
            "password": "test-password",
        },
        follow_redirects=True,
    )

    # Cancel the appointment.
    response = client.post(
        f"/appointment/{appointment_id}/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your appointment was cancelled successfully." in response.data

    # Confirm that the cancellation was saved in the database.
    cancelled_appointment = db.session.get(
        Appointment,
        appointment_id,
    )

    assert cancelled_appointment.status == "cancelled"

def test_patient_cannot_cancel_another_patients_appointment(
    app, client, users
):
    appointment = Appointment(
        patient_id=users["second_patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Another patient's appointment",
        status="booked",
    )

    db.session.add(appointment)
    db.session.commit()

    appointment_id = appointment.id

    # Log in as a different patient.
    client.post(
        "/login",
        data={
            "email": users["patient"].email,
            "password": "test-password",
        },
        follow_redirects=True,
    )

    # Attempt to cancel the other patient's appointment.
    response = client.post(
        f"/appointment/{appointment_id}/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        b"You are not authorized to cancel this appointment."
        in response.data
    )

    # Confirm that the appointment remains booked.
    appointment = db.session.get(Appointment, appointment_id)
    assert appointment.status == "booked"

def test_patient_cannot_cancel_already_cancelled_appointment(
    app, client, users
):
    appointment = Appointment(
        patient_id=users["patient"].id,
        doctor_id=users["doctor"].id,
        appointment_date=date(2099, 5, 20),
        appointment_time=time(9, 0),
        reason="Routine checkup",
        status="cancelled",
    )

    db.session.add(appointment)
    db.session.commit()

    appointment_id = appointment.id

    # Log in as the patient who owns the appointment.
    client.post(
        "/login",
        data={
            "email": users["patient"].email,
            "password": "test-password",
        },
        follow_redirects=True,
    )

    # Attempt to cancel the appointment again.
    response = client.post(
        f"/appointment/{appointment_id}/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"This appointment cannot be cancelled." in response.data

    # Confirm the appointment remains cancelled.
    appointment = db.session.get(Appointment, appointment_id)
    assert appointment.status == "cancelled"

def test_cannot_cancel_nonexistent_appointment(app, client, users):
    # Log in as a patient.
    client.post(
        "/login",
        data={
            "email": users["patient"].email,
            "password": "test-password",
        },
        follow_redirects=True,
    )

    # Use an ID that does not exist in the database.
    response = client.post(
        "/appointment/999999/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Appointment not found." in response.data