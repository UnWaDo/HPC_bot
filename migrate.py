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
    Organization.bulk_create(organizations.values())

with db.atomic():
    Organization.bulk_update(list(filter(
        lambda x: x.parent is not None,
        organizations.values())),
        fields=['parent']
    )

p1 = TelegramUser.register(tg_id=1, first_name='Igor', last_name='Mezentsev')
p2 = TelegramUser.register(tg_id=2, first_name='Lol', last_name='asd')
p3 = TelegramUser.register(
    tg_id=3, first_name='asdasd', last_name='Mezeasdntsev')
p4 = TelegramUser.register(
    tg_id=4, first_name='Kringe', last_name='Meze14123123ntsev')
c1 = Cluster.create(label='kiae', name='kiae')
Calculation.new_calculation('lol', p1.user, SubmitType.TELEGRAM, c1)
Calculation.new_calculation('lol', p2.user, SubmitType.TELEGRAM, c1)
Calculation.new_calculation('lol', p2.user, SubmitType.TELEGRAM, c1)
Calculation.new_calculation('lol', p4.user, SubmitType.TELEGRAM, c1)
db.close()
