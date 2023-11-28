from enum import Enum


class AdminMenuCallbacksData(Enum):
    MAIN: str = "AdminMenu.MAIN"


class OrganizationsCallbackData(Enum):
    MAIN: str = "Organization.MAIN"
    ALL_ORGANIZATION_LIST: str = "Organization.ALL_ORGANIZATION_LIST"
    ADD_ORGANIZATION: str = "Organization.ADD_ORGANIZATION"
    CHOOSE_ORGANIZATION: str = "Organization.CHOOSE_ORGANIZATION"
    ADD_PHOTO: str = "Organization.ADD_PHOTO"
    CHANGE_PHOTO: str = "Organization.CHANGE_PHOTO"
    CHANGE_ABBREVIATE: str = "Organization.CHANGE_ABBREVIATE"
    CHANGE_FULL_NAME: str = "Organization.CHANGE_FULL_NAME"
    GET_USERS_BY_ORGANIZATION: str = "Organization.GET_USERS_BY_ORGANIZATION"
    BACK_TO_ORGANIZATION_MENU: str = "Organization.BACK_TO_ORGANIZATION_MENU"


class UsersCallbackData(Enum):
    MAIN: str = "Users.MAIN"
    ALL_USERS_LIST: str = "Users.ALL_USERS_LIST"
    CHOOSE_USER: str = "Users.CHOOSE_USER"
    BACK_TO_USERS_MENU: str = "Users.BACK_TO_USER_MENU"


class MailingCallbackData(Enum):
    MAIN: str = "Mailing.MAIN"
