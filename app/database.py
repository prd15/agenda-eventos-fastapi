import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

# Por padrão cria o eventos.db na pasta onde a API roda.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eventos.db")

# O FastAPI pode usar a conexão em outra thread, e sem isso o SQLite reclama.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def criar_tabelas() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
