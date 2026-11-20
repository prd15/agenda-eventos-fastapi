from enum import Enum

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


class Categoria(str, Enum):
    palestra = "palestra"
    workshop = "workshop"
    reuniao = "reuniao"
    outro = "outro"


# Modelo com table=True não valida nada, então as regras ficam em schemas.py.
class Evento(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100)
    descricao: str | None = Field(default=None, max_length=500)
    local: str = Field(max_length=120)
    # Sem fuso: a data já chega aqui no horário de Brasília.
    data_inicio: NaiveDatetime = Field(index=True)
    data_fim: NaiveDatetime | None = None
    categoria: Categoria = Categoria.outro
    capacidade: int | None = None
