from abc import ABC
from typing import Optional, List, Any
from typing import Union

from sqlalchemy import Select, select, insert, Insert, update, delete, Update, Delete
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from HPC_BOT.database_api.api.enum.methods import Method
from HPC_BOT.database_api.settings import engine_url, echo
from .responce_model.body import Body
from .responce_model.code import Code
from .responce_model.responce import APIResponse
from .responce_model.status import Status


class BaseAPI(ABC):
    def __init__(self):
        self.engine = create_async_engine(url=engine_url, echo=echo)

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _validate_model_attribute(model_attribute: Any, value: Any) -> bool:
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

    def _create_statement(
        self, model: DeclarativeBase, method: Method, values: dict = None, **kwargs
    ) -> Union["Select", "Update", "Delete", "Insert"]:
        """
        Method for creating a select, update or delete statement automatically validates arguments and their values,
        if the argument does not exist or its value does not match the type specified in the database,
        then it will not be added to the statement.

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param method: Method for sql query, from enum Methods
        :param values: Dictionary with new values for the UPDATE method, for example {"name": "new_name"}
        (updating name field with new value "new_name")
        :param kwargs: custom filters for the query are validated in accordance with the table model
        :return: Union[<class 'sqlalchemy.Select'>, <class 'sqlalchemy.Update'>, <class 'sqlalchemy.Delete'>]
        """
        if method == Method.SELECT:
            statement = select(model)
        elif method == Method.UPDATE:
            statement = update(model)
        elif method == Method.DELETE:
            statement = delete(model)
        elif method == Method.INSERT:
            statement = insert(model)
        else:
            raise ValueError(
                'Method for statement must be "select", "update" or "delete"'
            )

        values_dict = dict()
        if method == Method.UPDATE and isinstance(values, dict):
            validated_values = dict()
            for attribute, value in values.items():
                model_attribute = model.__dict__.get(attribute, None)
                print(model_attribute, value)
                if self._validate_model_attribute(model_attribute, value):
                    validated_values[attribute] = value
            statement = statement.values(**validated_values).returning(model)

        for attribute, value in kwargs.items():
            model_attribute = model.__dict__.get(attribute, None)
            if self._validate_model_attribute(model_attribute, value):
                if isinstance(statement, Insert):
                    values_dict[attribute] = value
                else:
                    statement = statement.where(model_attribute == value)

        if isinstance(statement, Insert):
            return statement.values(**values_dict).returning(model)

        if isinstance(statement, Delete):
            statement = statement.returning(model)

        return statement

    async def _insert_model(
        self, model: DeclarativeBase, session: AsyncSession, **kwargs
    ) -> Optional[DeclarativeBase]:
        """
        Method for insert row in some table in database

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param session: SQLAlchemy async session
        :param kwargs: The values for new row on database table, pass strict typing and validation
        :return: New row object with data if insert was successful else None
        """
        insert_statement = self._create_statement(model, Method.INSERT, **kwargs)
        result = (await session.execute(insert_statement)).scalars().one_or_none()
        return result

    async def _delete_models(
        self, model: DeclarativeBase, session: AsyncSession, **kwargs
    ) -> Optional[List[DeclarativeBase]]:
        """
        Method for deleting one or more rows in database table

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param session: SQLAlchemy async session
        :param kwargs: The values for the selected rows are then deleted
        :return: A list with objects that have been deleted, if nothing has been deleted, then None
        """

        delete_statement = self._create_statement(
            model, Method.DELETE, **kwargs
        )
        result = (await session.execute(delete_statement)).scalars().all()
        return result if len(result) else None

    async def _update_models(
        self, model: DeclarativeBase, session: AsyncSession, values: dict, **kwargs
    ) -> Optional[List[DeclarativeBase]]:
        """

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param session: SQLAlchemy async session
        :param values:
        :param kwargs:
        :return:
        """
        update_statement = self._create_statement(model, Method.UPDATE, values, **kwargs)
        result = (await session.execute(update_statement)).scalars().all()
        return result if len(result) else None

    async def _get_models(
        self,
        model: DeclarativeBase,
        session: AsyncSession,
        one: bool = False,
        statement: Select = None,
        **kwargs
    ) -> Optional[Union[List["DeclarativeBase"], "DeclarativeBase"]]:
        """
        Method for select rows from database table

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param session: SQLAlchemy async session
        :param one: if True, method returns only one result
        :param statement: if you want to get models using not the built-in kwargs filters, but your own statement
        :param kwargs: Filters for selecting models by parameters are strictly typed and validated
        :return: if nothing suitable is found returns None, if one = True returns the string object,
         otherwise returns a list of string objects
        """
        if not isinstance(statement, Select):
            statement = self._create_statement(model, Method.SELECT, **kwargs)
        scalar = await session.scalars(statement)
        if one:
            return scalar.one_or_none()
        else:
            result = scalar.all()
            return result if len(result) else None

    async def _check_duplicates(
        self, model: DeclarativeBase, session: AsyncSession, **kwargs
    ) -> bool:
        """
        Method to check the occurrence of rows with such data

        :param model: SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param session: SQLAlchemy async session
        :param kwargs: Filters are similar to 'self._get_models' method
        :return: If there is a row with such data in the database, True is returned, otherwise False
        """

        duplicate = await self._get_models(model, session, one=True, **kwargs)
        if isinstance(duplicate, model):
            return True

        return False

    async def _id_to_model(
        self, model_type: DeclarativeBase, model_id: int, session: AsyncSession
    ) -> Optional[DeclarativeBase]:
        """
        method for converting id to SQLAlchemy model

        :param model_type:  SQLAlchemy table model, for determining which table to select from, as well as validating arguments
        :param model_id: SQLAlchemy model ID (primary key)
        :param session: SQLAlchemy async session
        :return: If there is such an id in the database, it returns the object of the string, otherwise None
        """
        if isinstance(model_id, int):
            model = await self._get_models(
                model_type, session, one=True, id=model_id
            )
            if isinstance(model, model_type):
                return model


    @property
    def bad_params(self) -> APIResponse:
        return APIResponse(status=Status.ERROR, body=Body(code=Code.BAD_PARAMETERS))

    @property
    def bad_response(self) -> APIResponse:
        return APIResponse(status=Status.ERROR, body=Body(code=Code.BAD_RESPONSE))

    @property
    def data_not_found(self) -> APIResponse:
        return APIResponse(status=Status.ERROR, body=Body(code=Code.DATA_NOT_FOUND))

    @property
    def already_exist(self) -> APIResponse:
        return APIResponse(status=Status.OK, body=Body(code=Code.ALREADY_EXIST))

    @staticmethod
    def success(model: Any = None, response_data: Any = None) -> APIResponse:
        return APIResponse(status=Status.OK, body=Body(code=Code.SUCCESS, model=model, response_data=response_data))

    @staticmethod
    def not_unique_data(data: Any) -> APIResponse:
        return APIResponse(status=Status.OK, body=Body(code=Code.NOT_UNIQUE_DATA, response_data=data))

    def _check_result_model(self, model, model_type) -> APIResponse:
        if isinstance(model, model_type):
            return self.success(model=model)
        else:
            return self.bad_response