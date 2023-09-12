import asyncio
import logging
from typing import List
from aiogram import Bot

from .utils import log_message, create_user_link

from ..utils import config
from ..models import db, Calculation, Cluster, CalculationStatus, SubmitType
from ..models import User as UserModel
from ..models import TelegramUser as TelegramUserModel


CALCULATION_FINISHED = (
    'Расчёт {name} завершился. '
    'Результаты расчёта доступны по <a href="{link}">ссылке</a>'
)
CALCULATION_FINISHED_LOG = (
    'У пользователя {user} завершился расчёт {name}. '
    'Результаты расчёта доступны по <a href="{link}">ссылке</a>'
)


async def notify_on_finished(bot: Bot):
    calculations: List[Calculation] = (
        Calculation.select(
            Calculation, Cluster, UserModel, TelegramUserModel
        )
        .join(Cluster).switch(Calculation)
        .join(UserModel)
        .join(TelegramUserModel)
        .where((Calculation.status == CalculationStatus.CLOUDED.value) &
               (Calculation.submit_type == SubmitType.TELEGRAM.value))
    )
    users: List[TelegramUserModel] = [calc.user.tg_user[0]
                                      for calc in calculations]

    updated = []
    for calc, user in zip(calculations, users):
        try:
            link = config.storage.get_shared(calc.get_folder_name())

            message = await bot.send_message(
                chat_id=user.tg_id,
                text=CALCULATION_FINISHED.format(
                    name=calc.name,
                    link=link
                )
            )
            await log_message(
                bot=bot,
                text=CALCULATION_FINISHED_LOG.format(
                    user=create_user_link(
                        user=message.chat,
                        model=calc.user
                    ),
                    name=calc.name,
                    link=link
                )
            )
            calc.set_status(CalculationStatus.SENDED)
            updated.append(calc)

        except asyncio.CancelledError:
            if len(updated) > 0:
                with db.atomic():
                    Calculation.bulk_update(
                        updated,
                        fields=['status']
                    )
            raise

        except Exception as e:
            logging.error(
                'Failed to send message to user #{id}'.format(id=user.id),
                exc_info=e
            )

    if len(updated) > 0:
        with db.atomic():
            Calculation.bulk_update(
                updated,
                fields=['status']
            )
