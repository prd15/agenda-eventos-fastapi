from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Evento
from app.schemas import ErroValidacao, EventoAtualizar, EventoCriar, EventoSaida

router = APIRouter(prefix="/eventos", tags=["Eventos"])

# Toda rota que pede SessionDep já recebe a sessão aberta pelo get_session.
SessionDep = Annotated[Session, Depends(get_session)]

ERRO_404 = {404: {"description": "Evento não encontrado"}}
ERRO_422 = {422: {"model": ErroValidacao, "description": "Dados inválidos"}}


def buscar_ou_404(session: Session, evento_id: int) -> Evento:
    evento = session.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return evento


@router.get("", response_model=list[EventoSaida], summary="Listar eventos ordenados por data")
def listar_eventos(session: SessionDep):
    consulta = select(Evento).order_by(Evento.data_inicio, Evento.id)
    return session.exec(consulta).all()


@router.get("/{evento_id}", response_model=EventoSaida, responses=ERRO_404 | ERRO_422, summary="Consultar um evento")
def consultar_evento(evento_id: int, session: SessionDep):
    return buscar_ou_404(session, evento_id)


@router.post("", response_model=EventoSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_422, summary="Cadastrar um evento")
def cadastrar_evento(dados: EventoCriar, session: SessionDep):
    # Se chegou aqui, os dados já passaram pela validação.
    evento = Evento(**dados.model_dump())
    session.add(evento)
    session.commit()
    session.refresh(evento)  # pega o id que o banco gerou
    return evento


@router.put("/{evento_id}", response_model=EventoSaida, responses=ERRO_404 | ERRO_422, summary="Atualizar um evento")
def atualizar_evento(evento_id: int, dados: EventoAtualizar, session: SessionDep):
    evento = buscar_ou_404(session, evento_id)
    for campo, valor in dados.model_dump().items():
        setattr(evento, campo, valor)
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


@router.delete(
    "/{evento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERRO_404 | ERRO_422,
    summary="Remover um evento",
)
def remover_evento(evento_id: int, session: SessionDep):
    evento = buscar_ou_404(session, evento_id)
    session.delete(evento)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
