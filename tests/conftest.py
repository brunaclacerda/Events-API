from datetime import datetime

import pytest
import requests

from models import User

BASE_URL = "http://localhost:5000"
ENDPOINTS = {
    "health": f"{BASE_URL}/api/health",
    "register": f"{BASE_URL}/api/auth/register",
    "login": f"{BASE_URL}/api/auth/login",
    "events": f"{BASE_URL}/api/events",
    "rsvp": f"{BASE_URL}/api/rsvps/event/",
}


def new_user_params():
    ts = datetime.timestamp(datetime.now())
    return {"username": f"peter_park_{ts}", "password": "19700529"}


def create_user():
    new_user_dict = new_user_params()
    response = requests.post(ENDPOINTS["register"], json=new_user_dict, timeout=5)

    assert response.status_code == 201, (
        f"Test new user register failed with HTTP {response.status_code}"
    )

    payload = response.json()
    assert "user" in payload, "API response without user object."
    saved_user = payload["user"].copy()
    saved_user["password"] = new_user_dict["password"]
    return saved_user


@pytest.fixture(scope="session")
def user_params():
    return new_user_params()


@pytest.fixture(scope="session")
def user(user_params):
    new_user = User(username=user_params["username"])
    new_user.set_password(user_params["password"])
    return new_user


@pytest.fixture(scope="session")
def endpoints():
    return ENDPOINTS


@pytest.fixture(scope="session")
def registred_user():
    return create_user()


@pytest.fixture
def authenticated_client(registred_user):

    with requests.Session() as client:
        response = client.post(ENDPOINTS["login"], json=registred_user, timeout=5)

        assert response.status_code == 200, (
            f"Test user login failed with HTTP {response.status_code}"
        )

        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest.fixture
def public_event(authenticated_client):

    event = {
        "title": "Stark Expo VIP Afterparty & Suit Roast",
        "description": "Open bar, live DJ, and a live demonstration of why Mark LXXXV "
        "beats whatever shiny nonsense Rhodey is currently flying. "
        "Dress code: Billionaire casual. Leave the hammers and shields at the coat check.",
        "date": "2026-12-05T22:00:00",
        "location": "Stark Tower Penthouse, Manhattan",
        "capacity": 500,
        "is_public": True,
        "requires_admin": False,
    }
    response = authenticated_client.post(ENDPOINTS["events"], json=event, timeout=5)

    assert response.status_code == 201, (
        f"Public event setup failed. Expected HTTP 201, got {response.status_code}"
    )
    payload = response.json()
    assert payload["is_public"] is True

    return payload


@pytest.fixture
def private_event(authenticated_client):

    event = {
        "title": "Black Widow & Cap: Unofficial Sparring & Coffee",
        "description": "Just a few rounds on the mat to stay sharp before we grab "
        "coffee and complain about how nobody knows how to use a floppy disk anymore.",
        "date": "2026-11-24T07:00:00",
        "location": "Avengers Compound, Main Gymnasium",
        "capacity": 4,
        "is_public": False,
        "requires_admin": False,
    }
    response = authenticated_client.post(ENDPOINTS["events"], json=event, timeout=5)

    assert response.status_code == 201, (
        f"Private event setup failed. Expected HTTP 201, got {response.status_code}"
    )
    payload = response.json()
    assert payload["is_public"] is False

    return payload


@pytest.fixture
def admin_event(authenticated_client):

    event = {
        "title": "SMASHING THINGS & TACO TUESDAY",
        "description": "HULK SMASH OLD ULTRON BOTS. THEN WE EAT TACOS. PUNY BANNERS NOT INVITED. BRING EXTRA SALSA.",
        "date": "2026-11-17T18:00:00",
        "location": "Avengers Compound, Reinforced Training Pit (Sub-Level 5)",
        "capacity": 6,
        "is_public": False,
        "requires_admin": True,
    }
    response = authenticated_client.post(ENDPOINTS["events"], json=event, timeout=5)

    assert response.status_code == 201, (
        f"Event creation failed with HTTP {response.status_code}"
    )
    payload = response.json()
    assert payload["requires_admin"] is True

    return payload


@pytest.fixture
def fully_booked_event(authenticated_client):
    event = {
        "title": "Sunset Rooftop Archery & Pizza",
        "description": "Just two bows, a stack of trick arrows, a couple of cold sodas,"
        " and a large pepperoni pizza. No world-ending threats allowed. "
        "(Kate, don't forget the boomerang arrow.)",
        "date": "2026-11-21T17:30:00",
        "location": "Clint Barton's Apartment Rooftop, Brooklyn",
        "capacity": 1,
        "is_public": True,
        "requires_admin": False,
    }

    response = authenticated_client.post(ENDPOINTS["events"], json=event, timeout=5)

    assert response.status_code == 201, (
        f"Event creation failed with HTTP {response.status_code}"
    )
    event_created = response.json()
    assert event_created["capacity"] == 1

    response = authenticated_client.post(
        f"{ENDPOINTS['rsvp']}{event_created['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 201, (
        f"Test RSVP to a public event failed with auth with HTTP {response.status_code}"
    )

    return event_created
