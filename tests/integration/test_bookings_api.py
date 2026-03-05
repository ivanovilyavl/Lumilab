import pytest
from datetime import date, time, datetime, timedelta, timezone

from db.models import Master, Service, ScheduleTemplate, Booking


@pytest.fixture
async def seeded_db(db_session):
    """Create a master with service and schedule for testing."""
    master = Master(
        telegram_id=999,
        username="test_master",
        display_name="Test Master",
        niche="beauty",
        referral_code="TESTREF",
        is_onboarded=True,
        subscription_status="trial",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
    )
    db_session.add(master)
    await db_session.flush()

    service = Service(
        master_id=master.id,
        name="Test Service",
        price=1000,
        duration_min=30,
    )
    db_session.add(service)

    # Schedule: today's weekday is working
    db_session.add(ScheduleTemplate(
        master_id=master.id,
        day_of_week=date.today().weekday(),
        start_time=time(10, 0),
        end_time=time(18, 0),
        slot_step_min=30,
        is_working=True,
    ))

    await db_session.commit()
    return master, service


@pytest.mark.asyncio
async def test_create_booking_success(api_client, seeded_db):
    master, service = seeded_db
    response = await api_client.post("/api/bookings", json={
        "master_id": master.id,
        "service_id": service.id,
        "date": str(date.today()),
        "start_time": "14:00",
        "client_name": "Test Client",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["master_name"] == "Test Master"
    assert data["service_name"] == "Test Service"


@pytest.mark.asyncio
async def test_create_booking_double(api_client, seeded_db):
    master, service = seeded_db
    payload = {
        "master_id": master.id,
        "service_id": service.id,
        "date": str(date.today()),
        "start_time": "15:00",
        "client_name": "Client 1",
    }
    # First booking — OK
    r1 = await api_client.post("/api/bookings", json=payload)
    assert r1.status_code == 200

    # Same slot — conflict
    payload["client_name"] = "Client 2"
    r2 = await api_client.post("/api/bookings", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_create_booking_nonexistent_master(api_client):
    response = await api_client.post("/api/bookings", json={
        "master_id": 99999,
        "service_id": 1,
        "date": str(date.today()),
        "start_time": "10:00",
        "client_name": "Nobody",
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_booking(api_client, seeded_db):
    master, service = seeded_db
    # Create
    r = await api_client.post("/api/bookings", json={
        "master_id": master.id,
        "service_id": service.id,
        "date": str(date.today()),
        "start_time": "16:00",
        "client_name": "Check Status",
    })
    booking_id = r.json()["id"]

    # Get
    r2 = await api_client.get(f"/api/bookings/{booking_id}")
    assert r2.status_code == 200
    assert r2.json()["status"] == "pending"
