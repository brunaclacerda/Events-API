"""
From Dev to Prod 2 – Events API Testing
Goal: Add a basic automated test suite for your Events API.
"""

import requests

# 3. Core Integration Tests (Happy Path)


def test_health_endpoint_returns_healthy(endpoints):
    """
    Test:
        1. Health / Status endpoint
    """
    response = requests.get(endpoints["health"], timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user_creates_new_user(endpoints, user_params):
    """
    Test:
        2. User registration
    """
    response = requests.post(endpoints["register"], json=user_params, timeout=5)

    assert response.status_code == 201, (
        f"Test new user register failed with HTTP {response.status_code}"
    )

    payload = response.json()
    assert "message" in payload, "API response without message."
    assert "user" in payload, "API response without user object."
    assert payload["user"]["username"] == user_params["username"], (
        f"Username expected: {user_params['username']}."
        f"Received: {payload['user']['username']}"
    )


def test_login_returns_jwt_token(endpoints, registred_user):
    """
    Test:
        3. User login
    """
    response = requests.post(
        endpoints["login"],
        json={
            "username": registred_user["username"],
            "password": registred_user["password"],
        },
        timeout=5,
    )

    assert response.status_code == 200, (
        f"Test user login failed with HTTP {response.status_code}"
    )

    payload = response.json()
    assert "access_token" in payload, "API response without access_token"
    assert "user" in payload, "API response without user object."
    assert payload["user"]["username"] == registred_user["username"], (
        f"Username expected: {registred_user['username']}."
        f"Received: {payload['user']['username']}"
    )


def test_create_event_requires_auth_and_succeeds_with_token(
    endpoints, authenticated_client
):
    """
    Test:
        4. Create event (authenticated)
    """
    event = {
        "title": "Web-Shooter Calibration & Donut Party",
        "description": "Emergency calibration of the new neo-polymeric web fluid."
        "Mandatory attendance for anyone who clogged their shooters on the last"
        " mission. (Tony, I'm looking at you.)",
        "date": "2026-07-20T20:00:00",
        "location": "Avengers Compound, Sub-Level 3 Science Lab",
        "capacity": 12,
        "is_public": False,
        "requires_admin": True,
    }
    response = authenticated_client.post(endpoints["events"], json=event, timeout=5)

    assert response.status_code == 201, (
        f"Test create private event with auth failed with HTTP {response.status_code}"
    )
    payload = response.json()
    invalid_event = next(
        (
            (key, value)
            for key, value in event.items()
            if key not in payload or payload[key] != value
        ),
        None,
    )

    assert invalid_event is None, (
        f"Invalid value for {invalid_event[0]}. Expected: {invalid_event[1]}. "
        f"Received: {payload.get(invalid_event[0], None)}"
    )


def test_rsvp_to_public_event_succeeds_without_auth(endpoints, public_event):
    """
    Test:
        5. RSVP to a public event
    """
    response = requests.post(
        f"{endpoints['rsvp']}{public_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 201, (
        f"Test RSVP to a public event without auth failed with HTTP {response.status_code}"
    )

    payload = response.json()
    assert public_event["id"] == payload["event_id"]
    assert payload["attending"] is True

    response = requests.get(f"{endpoints['rsvp']}{public_event['id']}", timeout=5)
    assert response.json()["event"].get("rsvp_count", 0) == 1, (
        "RSVP without updating event RSVP count."
    )


def test_rsvp_to_public_event_succeeds_with_auth(
    endpoints, public_event, authenticated_client, registred_user
):
    """
    Test RSVP to a public event with authentication.
    """
    response = authenticated_client.post(
        f"{endpoints['rsvp']}{public_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 201, (
        f"Test RSVP to a public event failed with auth with HTTP {response.status_code}"
    )

    payload = response.json()
    assert public_event["id"] == payload["event_id"]
    assert registred_user["id"] == payload["user_id"]
    assert payload["attending"] is True


def test_cancel_rsvp_to_public_event_succeeds(
    endpoints, public_event, authenticated_client
):
    """
    Test to cancel a RSVP to a public event with authentication.
    """
    response = authenticated_client.post(
        f"{endpoints['rsvp']}{public_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 201, (
        f"Test RSVP to a public event with auth failed with HTTP {response.status_code}"
    )

    response = authenticated_client.post(
        f"{endpoints['rsvp']}{public_event['id']}",
        json={"attending": False},
        timeout=5,
    )

    assert response.status_code == 200, (
        f"Test Cancel RSVP to a public event failed with HTTP {response.status_code}"
    )
    payload = response.json()
    assert public_event["id"] == payload["event_id"]
    assert payload["attending"] is False

    response = requests.get(f"{endpoints['rsvp']}{public_event['id']}", timeout=5)
    assert response.status_code == 200, (
        f"Test Get RSVPs for an event expected HTTP 200, got {response.status_code}"
    )
    rsvp = response.json()
    assert "event" in rsvp, "Expected event key in the response."
    assert "attendees" in rsvp["event"], "Expected attendees key in event response."
    assert len(rsvp["event"]["attendees"]) == 0, (
        "Expected no attendees after cancellation."
    )


# 4. Error / Edge‑Case Tests


def test_register_duplicate_username_and_fails(endpoints, registred_user):
    """
    Test:
        1. Duplicate username registration
    """
    response = requests.post(
        endpoints["register"],
        json={
            "username": registred_user["username"],
            "password": registred_user["password"],
        },
        timeout=5,
    )

    assert response.status_code == 400, (
        "Expected duplicate username registration to return HTTP 400, "
        f"got {response.status_code}"
    )


def test_create_event_without_auth_and_fails(endpoints):
    """
    Test:
        2. Create event without auth
    """
    event = {
        "title": "Python Meetup",
        "description": "Monthly Python developer meetup",
        "date": "2026-01-15T18:00:00",
        "location": "Tech Hub, Room 101",
        "capacity": 50,
        "is_public": True,
        "requires_admin": False,
    }
    response = requests.post(endpoints["events"], json=event, timeout=5)

    assert response.status_code == 401, (
        "Test event creation without authentication expected HTTP 401, got "
        f"{response.status_code}"
    )


def test_rsvp_non_public_event_without_auth(endpoints, private_event):
    """
    Test to RSVP a non-public event without authentication.
    """
    response = requests.post(
        f"{endpoints['rsvp']}{private_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 401, (
        "Test RSVP to a non-public event without auth expected HTTP 401, "
        f"got {response.status_code}"
    )

    assert response.json().get("error", None), "Expected error message."


def test_rsvp_admin_event_without_auth(endpoints, admin_event):
    """
    Test to RSVP an event that requires admin access without being logged in.
    """
    response = requests.post(
        f"{endpoints['rsvp']}{admin_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 401, (
        f"Test RSVP to a admin event without auth with HTTP {response.status_code}"
    )

    assert response.json().get("error", None), "Expected error message."


def test_rsvp_admin_event_without_admin_access(
    endpoints, admin_event, authenticated_client
):
    """
    Test to RSVP an event that requires admin access without having them.
    """
    response = authenticated_client.post(
        f"{endpoints['rsvp']}{admin_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 403, (
        f"Test RSVP to a admin event without admin access with HTTP {response.status_code}"
    )

    assert response.json().get("error", None), "Expected error message."


def test_rsvp_not_found_event(endpoints, authenticated_client):
    """
    Test to RSVP an nonexistent event .
    """
    response = authenticated_client.post(
        f"{endpoints['rsvp']}999999999",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 404, (
        f"Test RSVP to nonexistent event with HTTP {response.status_code}"
    )


def test_rsvp_fully_booked_event(endpoints, fully_booked_event):
    """
    Test to RSVP an event at its full capacity.
    """
    response = requests.post(
        f"{endpoints['rsvp']}{fully_booked_event['id']}",
        json={"attending": True},
        timeout=5,
    )

    assert response.status_code == 400, (
        f"Test RSVP to a fully booked event failed with HTTP {response.status_code}"
    )

    assert response.json().get("error", None), "Expected error message."


def test_cancel_rsvp_fully_booked_event(
    endpoints, authenticated_client, fully_booked_event
):
    """
    Test to cancel RSVP of a fully booked event.
    """
    response = authenticated_client.post(
        f"{endpoints['rsvp']}{fully_booked_event['id']}",
        json={"attending": False},
        timeout=5,
    )
    assert response.status_code == 200, (
        f"Test update RSVP to a fully booked event failed with HTTP {response.status_code}"
    )
