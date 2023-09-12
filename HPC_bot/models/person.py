from typing import Optional, Tuple
from peewee import CharField, ForeignKeyField, BooleanField

from .base_model import BaseDBModel
from .organization import Organization


class Person(BaseDBModel):
    first_name = CharField(50)
    last_name = CharField(50)

    registered = BooleanField(default=False)
    approved = BooleanField(default=False)

    organization = ForeignKeyField(
        model = Organization,
        backref = 'persons',
        null = True
    )

    
    def update_from_raw_data(
        self,
        first_name: str = None,
        last_name: str = None,
        organization: str = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        result = [None, None, None]

        if first_name is not None:
            first_name = first_name.strip()
        if last_name is not None:
            last_name = last_name.strip()
        if organization is not None:
            organization = organization.strip()

        if first_name is not None and first_name != '':
            self.first_name = first_name
            result[0] = self.first_name

        if last_name is not None and last_name != '':
            self.last_name = last_name
            result[1] = self.last_name

        if organization is not None and organization != '':
            organizations = Organization.find_similar(organization)

            if len(organizations) == 1:
                self.organization = organizations[0]
                result[2] = self.organization.abbreviation
            else:
                result[2] = ''

        if any(x is not None and x != '' for x in result):
            self.approved = False

            self.save()

        return tuple(result)
