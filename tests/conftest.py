import pytest
from booking import create_app
from booking.extensions import db
from booking.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def users(app):
    patient = User(
        name="Test Patient",
        email="patient@example.com",
        password=generate_password_hash("test-password"),
        role="patient",
    )

    second_patient = User(
        name="Second Patient",
        email="patient2@example.com",
        password=generate_password_hash("test-password"),
        role="patient",
    )

    doctor = User(
        name="Test Doctor",
        email="doctor@example.com",
        password=generate_password_hash("test-password"),
        role="doctor",
        specialization="General Practice",
    )

    doctor2 = User(
           name="Test Doctor2",
           email="doctor2@example.com",
           password=generate_password_hash("test-password"),
           role="doctor",
           specialization="General Practice",
       )

    db.session.add_all([patient, second_patient, doctor, doctor2])
    db.session.commit()

    return {
        "patient": patient,
        "second_patient": second_patient,
        "doctor": doctor,
        "doctor2": doctor2,
    }
