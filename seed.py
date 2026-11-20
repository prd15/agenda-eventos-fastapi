# Eventos de exemplo para a demonstração.
#   python seed.py          -> só insere se o banco estiver vazio
#   python seed.py --reset  -> apaga tudo e insere de novo

import sys
from datetime import timedelta

from sqlmodel import Session, delete, select

from app.database import criar_tabelas, engine
from app.models import Categoria, Evento
from app.schemas import agora


def em(dias: int, hora: int, minuto: int = 0):
    return (agora() + timedelta(days=dias)).replace(hour=hora, minute=minuto, second=0, microsecond=0)


EXEMPLOS = [
    Evento(
        titulo="Workshop de APIs com FastAPI",
        descricao="Construção de uma API REST do zero, com validação e documentação automática.",
        local="Laboratório de Informática 3",
        data_inicio=em(7, 19), data_fim=em(7, 22),
        categoria=Categoria.workshop, capacidade=30,
    ),
    Evento(
        titulo="Palestra: carreira em desenvolvimento back-end",
        local="Auditório IMEPAC",
        data_inicio=em(3, 20), data_fim=em(3, 21, 30),
        categoria=Categoria.palestra, capacidade=150,
    ),
    Evento(
        titulo="Reunião do grupo do Trabalho Final",
        descricao="Ensaio da apresentação antes da gravação.",
        local="Microsoft Teams",
        data_inicio=em(1, 21),
        categoria=Categoria.reuniao,
    ),
    Evento(
        titulo="Hackathon de Automação com Python",
        local="Bloco B",
        data_inicio=em(21, 8), data_fim=em(21, 18),
        categoria=Categoria.outro, capacidade=60,
    ),
]


def main() -> None:
    criar_tabelas()
    with Session(engine) as session:
        if "--reset" in sys.argv:
            session.exec(delete(Evento))
            session.commit()
        if session.exec(select(Evento)).first() is not None:
            print("O banco já tem eventos. Use --reset para recriar os exemplos.")
            return
        session.add_all(EXEMPLOS)
        session.commit()
        print(f"{len(EXEMPLOS)} eventos de exemplo cadastrados.")


if __name__ == "__main__":
    main()
