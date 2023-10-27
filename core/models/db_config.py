from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    dialect: str = "postgres"
    driver: str = "asyncpg"
    username: str
    password: str
    host: str = "localhost"
    port: int = 5430
    database: str
    echo: bool = False
