from celery import Celery
from celery.schedules import crontab

from shared.config import settings

app = Celery("zapisbot")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Europe/Moscow"

app.autodiscover_tasks(["worker.tasks"])

# Celery Beat schedule
app.conf.beat_schedule = {
    "send-reminders-24h": {
        "task": "worker.tasks.reminders.send_reminders_24h",
        "schedule": 3600.0,  # every hour
    },
    "send-reminders-2h": {
        "task": "worker.tasks.reminders.send_reminders_2h",
        "schedule": 900.0,  # every 15 min
    },
    "check-trial-expiry": {
        "task": "worker.tasks.subscription.check_trial_expiry",
        # Daily at 09:00 MSK. crontab is wall-clock based so beat restarts
        # cannot indefinitely postpone the run (unlike a raw interval).
        "schedule": crontab(hour=9, minute=0),
    },
    "mark-subscription-expired": {
        "task": "worker.tasks.subscription.mark_subscription_expired",
        "schedule": 3600.0,  # every hour
    },
    "apply-referral-bonuses": {
        "task": "worker.tasks.subscription.apply_referral_bonuses",
        "schedule": 600.0,  # every 10 min
    },
    "aggregate-analytics": {
        "task": "worker.tasks.analytics.aggregate_analytics",
        "schedule": 3600.0,  # every hour
    },
    "weekly-digest": {
        "task": "worker.tasks.analytics.send_weekly_digest",
        # Every Monday at 10:00 MSK. A raw 7-day interval never fired in
        # practice: beat's run-state isn't persisted across restarts, so any
        # redeploy within the week reset the countdown. crontab is wall-clock
        # based and always fires at the next matching time.
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
    },
    "auto-cancel-pending": {
        "task": "worker.tasks.reminders.auto_cancel_pending",
        "schedule": 600.0,  # every 10 min
    },
    "cleanup-old-messages": {
        "task": "worker.tasks.reminders.cleanup_old_messages",
        # Daily at 04:00 MSK (wall-clock based, restart-safe).
        "schedule": crontab(hour=4, minute=0),
    },
}
