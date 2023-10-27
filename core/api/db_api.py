from asyncio import current_task
from typing import Optional, List, Tuple, Any

from sqlalchemy import Select, select, insert, Insert
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from core.models.body import Body
from core.models.response import APIResponse
from core.models.status_codes import Status, Code
from core.utils import Config


class BaseAPI:
    def __new__(cls):
        """
        Singleton pattern
        """
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.__init__()
        return it

    def __init__(self):
        self.engine = create_async_engine(
            url=Config.databaseUrl, echo=Config.databaseConfig.echo
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )
        return session

    async def session_dependency(self) -> "AsyncSession":
        async with self.session_factory() as session:
            yield session
            await session.close()

    async def scoped_session_dependency(self) -> "AsyncSession":
        session = self.get_scoped_session()
        yield session
        await session.close()

    @staticmethod
    def _validateModelAttribute(model_attribute: Any, value: Any) -> bool:
        """
        Method for verifying the correspondence of this data type with the data type in the database

        :param model_attribute: argument corresponding to the field in the database table
        :param value: the value of the argument is needed to check the correspondence of types
        :return: True if argument validating success, otherwise False
        """
        if model_attribute is not None and model_attribute.type.python_type == type(
            value
        ):
            return True

        return False

    def _createSelectStatement(self, model: DeclarativeBase, **kwargs) -> "Select":
        """
        Method for creating a select statement automatically validates arguments and their values,
        if the argument does not exist or its value does not match the type specified in the database,
        then it will not be added to the statement.

        :param model: sqlalchemy table model, for determining which table to select from, as well as validating arguments
        :param kwargs: custom filters for the query are validated in accordance with the table model
        :return: :class: 'sqlalchemy.Select' object
        """

        select_statement = select(model)
        for attribute, value in kwargs.items():
            model_attribute = model.__dict__.get(attribute, None)
            if self._validateModelAttribute(model_attribute, value):
                select_statement = select_statement.where(model_attribute == value)
        return select_statement

    def _createInsertStatement(self, model: DeclarativeBase, **kwargs):
        values_dict = dict()

        for attribute, value in kwargs.items():
            model_attribute = model.__dict__.get(attribute, None)
            if self._validateModelAttribute(model_attribute, value):
                values_dict[attribute] = value

        return insert(model).values(**values_dict).returning(model)

    async def _getModel(
        self, model: DeclarativeBase, session: AsyncSession = None, **kwargs
    ) -> Optional["DeclarativeBase"]:
        select_statement = self._createSelectStatement(model, **kwargs)

        if isinstance(session, AsyncSession):
            result = await session.scalar(select_statement)
        else:
            async with self.session_factory.begin() as session:
                result = await session.scalar(select_statement)

        if isinstance(result, model):
            return result

        return None

    async def _getModels(
        self, model: DeclarativeBase, session: AsyncSession = None, **kwargs
    ) -> Optional[List["DeclarativeBase"]]:
        def validateResult(fetchList: List[Tuple["DeclarativeBase"]]):
            validatedList = list()

            for one in fetchList:
                if len(one) != 0 and isinstance(one[0], model):
                    validatedList.append(one)

            return validatedList

        select_statement = self._createSelectStatement(model, **kwargs)

        if isinstance(session, AsyncSession):
            exc = await session.execute(select_statement)
        else:
            async with self.session_factory.begin() as session:
                exc = await session.execute(select_statement)

        resultList = exc.fetchall()
        if resultList:
            return validateResult(resultList)

        return None

    @staticmethod
    async def _insertStatement(
        model: DeclarativeBase, statement: Insert, session: AsyncSession
    ) -> APIResponse:
        cursor = await session.execute(statement)
        await session.commit()

        result = cursor.scalar()

        if isinstance(result, model):
            return APIResponse(status=Status.OK, body=Body(code=Code.SUCCESS_CREATED))
        else:
            return APIResponse(status=Status.ERROR, body=Body(code=Code.BAD_RESPONSE))

    async def _checkDuplicates(
        self, model: DeclarativeBase, session: AsyncSession = None, **kwargs
    ) -> bool:
        duplicate = self._getModel(model, session, **kwargs)
        if isinstance(duplicate, model):
            return True
        return False
