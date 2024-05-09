from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseDBModel, sessionmaker

if TYPE_CHECKING:
    from .person import Person


class Organization(BaseDBModel):
    __tablename__ = 'organization'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True)
    abbreviation: Mapped[str] = mapped_column(String(15), unique=True)

    parent_id: Mapped[int] = mapped_column(ForeignKey('organization.id'))

    parent: Mapped['Organization'] = relationship('Organization',
                                                  back_populates='children',
                                                  remote_side=[id])
    children: Mapped[List['Organization']] = relationship(
        'Organization', back_populates='parent')

    persons: Mapped[List['Person']] = relationship(
        back_populates='organization')

    @staticmethod
    async def find_similar(name: str) -> List['Organization']:
        async with sessionmaker() as session:
            async with session.begin():
                statement = select(Organization).where(
                    or_(
                        Organization.name.ilike(f'%{name}%'),
                        Organization.abbreviation.ilike(f'%{name}%'),
                    ))

                result = await session.execute(statement)
                return result.scalars().all()

    def __str__(self) -> str:
        return f'{self.name} ({self.abbreviation})'
