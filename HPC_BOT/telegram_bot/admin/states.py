from aiogram.fsm.state import StatesGroup, State


class AddOrganizationStates(StatesGroup):
    abbreviate = State()
    full_name = State()


class ManageOrganization(StatesGroup):
    manage = State()
    add_photo = State()
    change_photo = State()
    change_abbreviate = State()
    change_full_name = State()