from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "stockscreener",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.prices",
        "app.tasks.fundamentals",
        "app.tasks.technicals",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Refresh EOD prices: daily at 4:30 PM IST (Mon–Fri)
    "refresh-eod-prices-nse": {
        "task": "app.tasks.prices.refresh_eod_prices",
        "schedule": crontab(hour=16, minute=30, day_of_week="1-5"),
        "args": (["NSE", "BSE"],),
    },
    "refresh-eod-prices-us": {
        "task": "app.tasks.prices.refresh_eod_prices",
        "schedule": crontab(hour=2, minute=0, day_of_week="2-6"),  # after NYSE close
        "args": (["NYSE", "NASDAQ"],),
    },
    # Compute technicals: daily after price refresh
    "compute-technicals-nse": {
        "task": "app.tasks.technicals.compute_all_technicals",
        "schedule": crontab(hour=17, minute=0, day_of_week="1-5"),
        "args": (["NSE", "BSE"],),
    },
    # Refresh fundamentals: weekly Sunday 2 AM
    "refresh-fundamentals": {
        "task": "app.tasks.fundamentals.refresh_all_fundamentals",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),
    },
}
