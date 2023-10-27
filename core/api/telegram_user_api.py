from core.api.db_api import BaseAPI
from core.models import User, TelegramUser
from core.models.body import Body
from core.models.response import APIResponse
from core.models.status_codes import Status, Code


class TelegramUserAPI(BaseAPI):
    async def createTelegramUser(self, telegram_id: int | str, user: int | User):
        if type(user) not in (int, User):
            return APIResponse(
                status=Status.ERROR,
                body=Body(code=Code.BAD_PARAMETERS, param="user"),
            )

        user_id = user
        if type(user) == User:
            user_id = user.id

        async with self.session_factory.begin() as session:
            user_duplicate = self._checkDuplicates(User, session, id=user_id)
            if not user_duplicate:
                return APIResponse(
                    status=Status.ERROR,
                    body=Body(code=Code.DATA_NOT_FOUND, param="user"),
                )

            telegram_user_duplicate = self._checkDuplicates(
                TelegramUser, session, telegram_id=telegram_id
            )
            if telegram_user_duplicate:
                return APIResponse(
                    status=Status.ERROR,
                    body=Body(code=Code.ALREADY_EXIST, param="telegram_id"),
                )

            insert_stmt = self._createInsertStatement(
                TelegramUser, telegram_id=telegram_id, user_id=user_id
            )
            return await self._insertStatement(TelegramUser, insert_stmt, session)
