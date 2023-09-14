from HPC_bot.models import *
from csv import DictReader


TABLES = [Organization, Person, User, TelegramUser, Cluster, Calculation]

db.connect()

db.drop_tables(TABLES[::-1])
db.create_tables(TABLES)

organizations = {}

with open('organizations.csv', 'r', encoding='utf-8') as orgs:
    org_reader = DictReader(orgs)

    for row in org_reader:
        organizations[row['label']] = Organization(
            name=row['name'],
            abbreviation=row['alias'],
            parent=organizations.get(row['parent'])
        )

with db.atomic():
    for org in organizations.values():
        org.save()

db.close()
