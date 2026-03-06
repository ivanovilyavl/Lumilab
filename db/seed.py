"""Seed development database with test data."""
import asyncio
import random
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Base,
    Booking,
    Event,
    Master,
    Payment,
    Referral,
    ScheduleTemplate,
    Service,
)
from db.session import engine, async_session


EVENT_TYPES = [
    "master_registered",
    "master_onboarded",
    "service_created",
    "schedule_set",
    "link_shared",
    "miniapp_opened",
    "booking_created",
    "booking_confirmed",
    "booking_cancelled",
    "trial_started",
    "subscription_activated",
    "subscription_expired",
    "referral_used",
]

SERVICES_DATA = {
    "beauty": [
        ("Стрижка женская", 2500, 60),
        ("Стрижка мужская", 1500, 30),
        ("Окрашивание", 5000, 120),
        ("Маникюр", 2000, 60),
        ("Педикюр", 2500, 75),
        ("Укладка", 1800, 45),
    ],
    "tutor": [
        ("Урок английского", 2000, 60),
        ("Урок математики", 1800, 60),
        ("Подготовка к ЕГЭ", 2500, 90),
        ("Разговорный клуб", 1000, 45),
    ],
    "trainer": [
        ("Персональная тренировка", 3000, 60),
        ("Стретчинг", 1500, 45),
        ("Групповая тренировка", 800, 60),
        ("Составление программы", 5000, 90),
        ("Онлайн-тренировка", 2000, 60),
    ],
}

STATUSES = ["pending", "confirmed", "cancelled", "completed", "no_show"]
CLIENT_NAMES = [
    "Анна", "Мария", "Елена", "Ольга", "Наталья",
    "Дмитрий", "Алексей", "Сергей", "Андрей", "Иван",
    "Екатерина", "Татьяна", "Юлия", "Светлана", "Ирина",
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        now = datetime.utcnow()

        # ── Master 1: trial ──
        m1 = Master(
            telegram_id=100001,
            username="beauty_anna",
            display_name="Анна Красотка",
            bio="Мастер маникюра и стилист. 5 лет опыта.",
            niche="beauty",
            referral_code="ANNA2024",
            is_onboarded=True,
            subscription_status="trial",
            trial_ends_at=now + timedelta(days=10),
        )
        db.add(m1)

        # ── Master 2: active ──
        m2 = Master(
            telegram_id=100002,
            username="tutor_sergey",
            display_name="Сергей Преподаватель",
            bio="Репетитор по английскому. IELTS 8.5.",
            niche="tutor",
            referral_code="SERG2024",
            is_onboarded=True,
            subscription_status="active",
            subscription_ends_at=now + timedelta(days=25),
        )
        db.add(m2)

        # ── Master 3: expired ──
        m3 = Master(
            telegram_id=100003,
            username="trainer_max",
            display_name="Макс Тренер",
            bio="Фитнес-тренер. Сертифицированный нутрициолог.",
            niche="trainer",
            referral_code="MAX2024",
            is_onboarded=True,
            subscription_status="expired",
            trial_ends_at=now - timedelta(days=5),
        )
        db.add(m3)
        await db.flush()

        # ── Services ──
        masters_data = [
            (m1, "beauty"),
            (m2, "tutor"),
            (m3, "trainer"),
        ]
        all_services = []
        for master, niche in masters_data:
            for i, (name, price, duration) in enumerate(SERVICES_DATA[niche]):
                svc = Service(
                    master_id=master.id,
                    name=name,
                    price=price,
                    duration_min=duration,
                    sort_order=i,
                )
                db.add(svc)
                all_services.append(svc)
        await db.flush()

        # ── Schedules: Mon-Fri 10:00-19:00 ──
        for master, _ in masters_data:
            for day in range(5):  # Mon-Fri
                db.add(ScheduleTemplate(
                    master_id=master.id,
                    day_of_week=day,
                    start_time=time(10, 0),
                    end_time=time(19, 0),
                    slot_step_min=30,
                    is_working=True,
                ))

        # ── Bookings ──
        for master, niche in masters_data:
            master_services = [s for s in all_services if s.master_id == master.id]
            for _ in range(random.randint(7, 12)):
                svc = random.choice(master_services)
                bdate = date.today() + timedelta(days=random.randint(-14, 14))
                hour = random.randint(10, 17)
                minute = random.choice([0, 30])
                end_min = hour * 60 + minute + svc.duration_min

                db.add(Booking(
                    master_id=master.id,
                    service_id=svc.id,
                    client_name=random.choice(CLIENT_NAMES),
                    client_phone=f"+7999{random.randint(1000000, 9999999)}",
                    client_telegram_id=random.randint(200000, 299999),
                    booking_date=bdate,
                    start_time=time(hour, minute),
                    end_time=time(end_min // 60, end_min % 60),
                    status=random.choice(STATUSES),
                    source=random.choice(["miniapp", "bot", "manual"]),
                ))

        # ── Referrals ──
        db.add(Referral(referrer_id=m1.id, referred_id=m2.id, bonus_applied=True, bonus_days=7))
        db.add(Referral(referrer_id=m2.id, referred_id=m3.id, bonus_applied=False, bonus_days=7))

        # ── Payment for active master ──
        db.add(Payment(
            master_id=m2.id,
            tribute_payment_id="tribute_test_001",
            amount_rub=199,
            status="paid",
            period_start=now - timedelta(days=5),
            period_end=now + timedelta(days=25),
        ))

        # ── Events (200+) ──
        for master, _ in masters_data:
            for _ in range(70):
                db.add(Event(
                    master_id=master.id,
                    event_type=random.choice(EVENT_TYPES),
                    payload={},
                    created_at=now - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                    ),
                ))

        await db.commit()
        print("Seed complete: 3 masters, services, schedules, bookings, referrals, 210+ events")


if __name__ == "__main__":
    asyncio.run(seed())
