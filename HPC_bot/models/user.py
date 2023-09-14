from datetime import datetime
from typing import List, TYPE_CHECKING
from peewee import IntegerField, ForeignKeyField, BooleanField, Check
from peewee import DoesNotExist


from .base_model import db, BaseDBModel
from .person import Person
from .organization import Organization

if TYPE_CHECKING:
    from .calculation import Calculation


NEWLY_REGISTERED_LIMIT = 5
APPROVED_BASE_LIMIT = 25


class User(BaseDBModel):
    calculation_limit = IntegerField(
        constraints=[Check('calculation_limit >= 0')]
    )
    blocked = BooleanField(default=False)
    access_level = IntegerField(default=1000)

    person = ForeignKeyField(
        model=Person,
        backref='user'
    )

    class Meta:
        table_name = 'hpc_user'

    @staticmethod
    def register(
        first_name: str,
        last_name: str,
        organization: Organization = None
    ) -> 'User':
        person = Person.create(
            first_name=first_name,
            last_name=last_name,
            organization=organization,
            registered=True
        )
        return User.create(
            calculation_limit=NEWLY_REGISTERED_LIMIT,
            person=person
        )

    @staticmethod
    def approve(id: int) -> 'User':
        users = User.select(User, Person).join(Person).where(User.id == id)

        if len(users) == 0:
            return None

        user = users[0]  # type: User

        if user.person.approved:
            return None

        user.person.approved = True
        user.calculation_limit = APPROVED_BASE_LIMIT

        with db.atomic():
            user.person.save()
            user.save()

        return user

    @staticmethod
    def block(id: int) -> 'User':
        try:
            user = User.get_by_id(id)  # type: User
        except DoesNotExist:
            return None

        if user.blocked:
            return None

        user.blocked = True
        user.save()

        return user

    @staticmethod
    def unblock(id: int) -> 'User':
        try:
            user = User.get_by_id(id)  # type: User
        except DoesNotExist:
            return None

        if not user.blocked:
            return None

        user.blocked = False
        user.save()

        return user

    def get_calculations(self, since: datetime = None) -> List['Calculation']:
        if since is None:
            return self.calculations

        return list(filter(
            lambda x: x.start_datetime >= since,
            self.calculations
        ))
