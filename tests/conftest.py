import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


@pytest.fixture
def client():
    # Cada teste começa com um banco em memória vazio. O StaticPool segura uma
    # conexão só; sem ele, cada conexão nova abriria outro banco, sem as tabelas.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def session_de_teste():
        with Session(engine) as session:
            yield session

    # Troca o banco de verdade pelo de teste sem mexer nas rotas.
    app.dependency_overrides[get_session] = session_de_teste
    yield TestClient(app)
    app.dependency_overrides.clear()
