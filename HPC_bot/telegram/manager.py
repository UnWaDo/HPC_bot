import logging
from typing import List

from aiogram import Bot
from sqlalchemy import or_, select

from ..models import Calculation, CalculationStatus, SubmitType
from ..models import TelegramUser as TelegramUserModel
from ..models import sessionmaker
from ..utils import config
from .utils import create_user_link, log_message

CALCULATION_FAILED_TO_UPLOAD = (
    'Ошибка при загрузке расчёта {name}. '
    'Повторите попытку позже или обратитесь к администратору')

CALCULATION_FAILED_TO_UPLOAD_LOG = (
    'Ошибка при загрузке расчёта {name} у пользователя {user}')

CALCULATION_FINISHED = (
    'Расчёт {name} завершился. '
    'Результаты расчёта доступны по <a href="{link}">ссылке</a>')

CALCULATION_FINISHED_LOG = (
    'У пользователя {user} завершился расчёт {name}. '
    'Результаты расчёта доступны по <a href="{link}">ссылке</a>')


async def notify_on_finished(bot: Bot):

    query = select(Calculation).where(
        Calculation.submit_type == SubmitType.TELEGRAM).where(
            or_(Calculation.status == CalculationStatus.CLOUDED,
                Calculation.status == CalculationStatus.FAILED_TO_UPLOAD))

    async with sessionmaker() as session:
        async with session.begin():
            result = await session.execute(query)

            calculations = result.scalars().all()

    users: List[TelegramUserModel] = [
        calc.user.tg_user for calc in calculations
    ]

    updated = []
    for calc, user in zip(calculations, users):
        user.user = calc.user

        if calc.get_status() == CalculationStatus.FAILED_TO_UPLOAD:
            text = CALCULATION_FAILED_TO_UPLOAD.format(name=calc.name)
            log_text = CALCULATION_FAILED_TO_UPLOAD_LOG.format(
                user=create_user_link(model=user), name=calc.name)
            calc.set_status(CalculationStatus.SENDED)

        else:
            link = await config.storage.get_shared(calc.get_folder_name())

            text = CALCULATION_FINISHED.format(name=calc.name, link=link)
            log_text = CALCULATION_FINISHED_LOG.format(
                user=create_user_link(model=user), name=calc.name, link=link)
            calc.set_status(CalculationStatus.SENDED)

        updated.append(calc)

        try:
            message = await bot.send_message(chat_id=user.tg_id, text=text)
            await log_message(bot=bot, text=log_text)
        except Exception as e:
            logging.error(
                'Failed to send message to user #{id}'.format(id=user.id),
                exc_info=e)

    if updated:
        async with sessionmaker() as session:
            async with session.begin():
                for update in updated:
                    session.add(update)

                await session.commit()
