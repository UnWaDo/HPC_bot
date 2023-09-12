from datetime import datetime


def get_month_start() -> datetime:
    return datetime.utcnow().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
