import pytest
from booking import create_app
from booking.extensions import db
from booking.models import User

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
        password="test-password-hash",
        role="patient",
    )

    second_patient = User(
        name="Second Patient",
        email="patient2@example.com",
        password="test-password-hash",
        role="patient",
    )

    doctor = User(
        name="Test Doctor",
        email="doctor@example.com",
        password="test-password-hash",
        role="doctor",
        specialization="General Practice",
    )

    db.session.add_all([patient, second_patient, doctor])
    db.session.commit()

    return {
        "patient": patient,
        "second_patient": second_patient,
        "doctor": doctor,
    }
