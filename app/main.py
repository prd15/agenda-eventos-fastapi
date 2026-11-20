from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from app.database import criar_tabelas
from app.routers import eventos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda uma vez, quando o servidor sobe.
    criar_tabelas()
    yield


app = FastAPI(
    title="Agenda de Eventos",
    description=(
        "API REST de cadastro de eventos feita com FastAPI para o Trabalho Final de "
        "Tópicos Especiais em ADS (IMEPAC). A documentação desta página é gerada "
        "automaticamente a partir do código."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(eventos.router)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse(url="/docs")


# O FastAPI devolve os erros de validação com as mensagens do Pydantic, em inglês.
# Aqui o status continua 422, mas cada erro sai como {campo, mensagem} em português.
def traduzir(erro: dict) -> str:
    tipo = erro["type"]
    ctx = erro.get("ctx", {})
    if tipo == "missing":
        return "Campo obrigatório"
    if tipo == "string_too_short":
        return f"Deve ter pelo menos {ctx.get('min_length')} caracteres"
    if tipo == "string_too_long":
        return f"Deve ter no máximo {ctx.get('max_length')} caracteres"
    if tipo == "string_type":
        return "Deve ser um texto"
    if tipo == "greater_than_equal":
        return f"Deve ser maior ou igual a {ctx.get('ge')}"
    if tipo == "less_than_equal":
        return f"Deve ser menor ou igual a {ctx.get('le')}"
    if tipo in ("int_parsing", "int_type", "int_from_float"):
        return "Deve ser um número inteiro"
    if tipo.startswith("datetime") or tipo.startswith("date"):
        return "Data e hora inválidas. Use o formato AAAA-MM-DDTHH:MM:SS"
    if tipo == "enum":
        return f"Valor inválido. Opções aceitas: {ctx.get('expected')}"
    if tipo in ("json_invalid", "model_attributes_type", "dict_type"):
        return "O corpo da requisição deve ser um JSON válido"
    if tipo == "value_error":
        return str(ctx.get("error", erro["msg"]))
    return erro["msg"]


@app.exception_handler(RequestValidationError)
async def erro_de_validacao(request: Request, exc: RequestValidationError):
    erros = []
    for erro in exc.errors():
        # loc vem tipo ("body", "titulo"); o primeiro item é só de onde veio o dado.
        partes = [str(p) for p in erro["loc"][1:]]
        erros.append({"campo": ".".join(partes) or "corpo", "mensagem": traduzir(erro)})
    return JSONResponse(
        status_code=422,
        content={"detail": "Dados inválidos", "erros": erros},
    )
