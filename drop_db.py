from HPC_bot.models import *


TABLES = [Organization, Person, User, TelegramUser, Cluster, Calculation]

db.connect()

db.drop_tables(TABLES[::-1])

db.close()
