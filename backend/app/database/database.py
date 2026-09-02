from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

from app.core.config import settings


if settings.DATABASE_TRUSTED_CONNECTION.lower() == "yes":
    connection_string = (
        f"DRIVER={{{settings.DATABASE_DRIVER}}};"
        f"SERVER={settings.DATABASE_SERVER};"
        f"DATABASE={settings.DATABASE_NAME};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )
else:
    connection_string = (
        f"DRIVER={{{settings.DATABASE_DRIVER}}};"
        f"SERVER={settings.DATABASE_SERVER};"
        f"DATABASE={settings.DATABASE_NAME};"
        f"UID={settings.DATABASE_USERNAME};"
        f"PWD={settings.DATABASE_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )


DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()