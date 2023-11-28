from aiogram import Router

adminRouter = Router(name="admin")

GET_ORGANIZATIONS_COMMAND = "/getorg"

SUPPORTED_IMAGE_FORMATS = ["jpeg", "jpg", "png"]  # Только маленькими буквами!