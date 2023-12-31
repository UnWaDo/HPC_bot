from datetime import datetime, timedelta
from peewee import fn, JOIN
from typing import Iterable, Union

from . import User, TelegramUser, Person, Calculation, Organization
from .user import User


def get_all_with_calcs(since: datetime = None,
                       remove_blocked: bool = False) -> Iterable[TelegramUser]:
    if since is not None:
        calculations = Calculation.select(Calculation).where(
            (Calculation.start_datetime >= since))
    else:
        calculations = Calculation.select(Calculation)

    select = (
        TelegramUser.select(TelegramUser, User, Person,
                            fn.COUNT(calculations.c.id).alias('num_calc'))
        .join(User)
        .join(Person)
        .join(calculations, JOIN.LEFT_OUTER,
              on=(calculations.c.user_id == User.id))
        .group_by(TelegramUser, User, Person))

    if remove_blocked:
        select = select.where(~User.blocked)
    return select


def search_users(
    last_name: str = None,
    first_name: str = None,
    organization: str = None
) -> Iterable[TelegramUser]:
    select = (
        TelegramUser.select(
            TelegramUser,
            User,
            Person,
            Organization,
        )
        .join(User)
        .join(Person)
        .join(Organization, JOIN.LEFT_OUTER)
    )
    if last_name is not None:
        select = select.where(Person.last_name.ilike(last_name))
    if first_name is not None:
        select = select.where(Person.first_name.ilike(first_name))
    if organization is not None:
        select = select.where(
            Organization.name.ilike(organization) |
            Organization.abbreviation.ilike(organization)
        )
    return select


def get_tg_user(tg_id: int = None, user_id: int = None) -> TelegramUser:
    if tg_id is None and user_id is None:
        return None

    select = (
        TelegramUser.select(
            TelegramUser,
            User,
            Person,
            Organization,
        )
        .join(User)
        .join(Person)
        .join(Organization, JOIN.LEFT_OUTER)
    )
    if tg_id is not None:
        select = select.where(TelegramUser.tg_id == tg_id)
    if user_id is not None:
        select = select.where(User.id == user_id)

    return select.get_or_none()


def get_tg_user_with_calcs(
    tg_id: int = None,
    user_id: int = None,
    since: datetime = None
) -> TelegramUser:

    if tg_id is None and user_id is None:
        return None

    if since is not None:
        calculations = Calculation.select(Calculation).where(
            (Calculation.start_datetime >= since)
        )
    else:
        calculations = Calculation.select(Calculation)

    select = (
        TelegramUser.select(
            TelegramUser,
            User,
            Person,
            Organization,
            fn.COUNT(calculations.c.id).alias('num_calc')
        )
        .join(User)
        .join(Person)
        .join(Organization, JOIN.LEFT_OUTER)
        .join(
            calculations,
            JOIN.LEFT_OUTER,
            on=(calculations.c.user_id == User.id)
        )
        .group_by(TelegramUser, User, Person, Organization)
    )
    if tg_id is not None:
        select = select.where(TelegramUser.tg_id == tg_id)
    if user_id is not None:
        select = select.where(User.id == user_id)

    return select.get_or_none()
