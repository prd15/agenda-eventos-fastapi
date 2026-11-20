from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Categoria

FUSO = ZoneInfo("America/Sao_Paulo")


def agora() -> datetime:
    return datetime.now(FUSO).replace(tzinfo=None)


class EventoEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=100, examples=["Semana Acadêmica de ADS"])
    descricao: str | None = Field(default=None, max_length=500, examples=["Palestras e minicursos"])
    local: str = Field(min_length=2, max_length=120, examples=["Auditório IMEPAC"])
    data_inicio: datetime = Field(examples=["2026-12-05T19:00:00"])
    data_fim: datetime | None = Field(default=None, examples=["2026-12-05T22:00:00"])
    categoria: Categoria = Categoria.outro
    capacidade: int | None = Field(default=None, ge=1, le=10_000, examples=[120])

    # Tira os espaços antes de medir o tamanho, assim "   " não passa.
    @field_validator("titulo", "local", "descricao", mode="before")
    @classmethod
    def remover_espacos(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    # Data com fuso (ex.: terminando em Z) vira horário de Brasília.
    @field_validator("data_inicio", "data_fim")
    @classmethod
    def normalizar_fuso(cls, valor: datetime | None) -> datetime | None:
        if valor is not None and valor.tzinfo is not None:
            return valor.astimezone(FUSO).replace(tzinfo=None)
        return valor

    # Essa regra usa dois campos, por isso roda depois que o modelo inteiro foi lido.
    @model_validator(mode="after")
    def validar_periodo(self):
        if self.data_fim is not None and self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio")
        return self


# Data no passado só é barrada no cadastro; um evento antigo ainda pode ser corrigido no PUT.
class EventoCriar(EventoEntrada):
    @field_validator("data_inicio")
    @classmethod
    def nao_pode_ser_passado(cls, valor: datetime) -> datetime:
        if valor.tzinfo is not None:
            valor = valor.astimezone(FUSO).replace(tzinfo=None)
        if valor < agora():
            raise ValueError("data_inicio não pode estar no passado")
        return valor


# O PUT troca o evento inteiro, então valem as mesmas regras do cadastro (menos a da data).
class EventoAtualizar(EventoEntrada):
    pass


class EventoSaida(EventoEntrada):
    model_config = ConfigDict(from_attributes=True)  # monta a resposta direto do objeto do banco

    id: int


class ErroCampo(BaseModel):
    campo: str = Field(examples=["titulo"])
    mensagem: str = Field(examples=["Deve ter pelo menos 3 caracteres"])


# Formato do 422 que o main.py devolve (aparece assim no Swagger).
class ErroValidacao(BaseModel):
    detail: str = Field(examples=["Dados inválidos"])
    erros: list[ErroCampo]
