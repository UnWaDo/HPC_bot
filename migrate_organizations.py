import asyncio
from HPC_bot.models import Organization, sessionmaker, engine
from csv import DictReader

organizations = {}


async def main():
    with open('organizations.csv', 'r', encoding='utf-8') as orgs:
        org_reader = DictReader(orgs)

        for row in org_reader:
            organizations[row['label']] = Organization(
                name=row['name'],
                abbreviation=row['alias'],
                parent=organizations.get(row['parent']))

    async with sessionmaker() as session:
        async with session.begin():

            session.add_all(organizations.values())

            await session.commit()

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
