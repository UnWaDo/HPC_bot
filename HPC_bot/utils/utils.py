from datetime import datetime, timedelta


def get_month_start() -> datetime:
    return (datetime.utcnow() - timedelta(days=30)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
