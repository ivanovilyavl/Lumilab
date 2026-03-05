from datetime import time

from api.routers.slots import generate_slots, overlaps, time_to_minutes


def test_generate_slots_basic():
    """30-min step, 30-min service, 10:00-12:00 = 4 slots."""
    slots = generate_slots(time(10, 0), time(12, 0), 30, 30)
    assert len(slots) == 4
    assert slots[0] == (time(10, 0), time(10, 30))
    assert slots[-1] == (time(11, 30), time(12, 0))


def test_generate_slots_60min_service():
    """30-min step, 60-min service, 10:00-12:00 = 3 slots."""
    slots = generate_slots(time(10, 0), time(12, 0), 30, 60)
    assert len(slots) == 3
    assert slots[0] == (time(10, 0), time(11, 0))
    assert slots[-1] == (time(11, 0), time(12, 0))


def test_generate_slots_no_room():
    """Service longer than working window = no slots."""
    slots = generate_slots(time(10, 0), time(10, 30), 30, 60)
    assert slots == []


def test_time_to_minutes():
    assert time_to_minutes(time(10, 30)) == 630
    assert time_to_minutes(time(0, 0)) == 0


class FakeBooking:
    def __init__(self, start: time, end: time):
        self.start_time = start
        self.end_time = end


def test_overlaps_true():
    booked = [FakeBooking(time(10, 0), time(11, 0))]
    assert overlaps(time(10, 30), time(11, 30), booked) is True


def test_overlaps_false():
    booked = [FakeBooking(time(10, 0), time(11, 0))]
    assert overlaps(time(11, 0), time(12, 0), booked) is False


def test_overlaps_exact_boundary():
    """Slot starts exactly when booking ends — no overlap."""
    booked = [FakeBooking(time(10, 0), time(10, 30))]
    assert overlaps(time(10, 30), time(11, 0), booked) is False
