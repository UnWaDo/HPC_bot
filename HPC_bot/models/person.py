from typing import Optional, Tuple, TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel, sessionmaker
from .organization import Organization

if TYPE_CHECKING:
    from .user import User


class Person(BaseDBModel):
    __tablename__ = 'person'

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))

    registered: Mapped[bool] = mapped_column(default=False)
    approved: Mapped[bool] = mapped_column(default=False)

    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id'),
                                                 nullable=True)
    organization: Mapped[Organization] = relationship(back_populates='persons',
                                                      lazy='joined')

    user: Mapped['User'] = relationship(back_populates='person')

    async def update_from_raw_data(
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
            organizations = await Organization.find_similar(organization)

            if len(organizations) == 1:
                if (self.organization is None) or (self.organization.id
                                                   != organizations[0].id):
                    self.organization = organizations[0]

                result[2] = self.organization.abbreviation
            else:
                result[2] = ''

        if any(x is not None and x != '' for x in result):
            async with sessionmaker() as session:
                async with session.begin():
                    self.approved = False

                    session.add(self)
                    await session.commit()

        return tuple(result)
