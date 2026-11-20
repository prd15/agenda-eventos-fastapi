# Agenda de Eventos · API REST com FastAPI

Trabalho Final de **Tópicos Especiais em Análise e Desenvolvimento de Sistemas** (IMEPAC, 2026/2), Tema 2: **FastAPI**.

A aplicação é o CRUD de eventos pedido no enunciado (seção 4.1), o mesmo implementado pelos grupos de Flask e Django, para que a turma compare como cada framework resolve o mesmo problema.

## Integrantes

| Nome completo |
|---|
| Fernando Donizetti Peixoto Júnior |
| Gustavo Machado Maia Barra |
| Lucas Lemos Barbosa |
| Newton Pinto Filho |
| Pedro Henrique Silva Fernandes |
| Thalía Rodrigues Alcântara |

## Tecnologias

| Biblioteca | Papel no projeto |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Framework web: rotas, injeção de dependências, documentação automática |
| [Pydantic](https://docs.pydantic.dev/) | Validação e conversão dos dados de entrada e saída |
| [SQLModel](https://sqlmodel.tiangolo.com/) | Mapeamento da tabela `evento` (sobre o SQLAlchemy) |
| SQLite | Banco de dados em arquivo (`eventos.db`), já vem com o Python |
| [Uvicorn](https://www.uvicorn.org/) | Servidor ASGI que executa a API |
| pytest | Testes automatizados |

## Como executar

Requisito: **Python 3.11 ou mais recente** (a versão do FastAPI usada não instala no 3.10). Confira com `python --version`.

```bash
# 1. Baixar o projeto
git clone https://github.com/prd15/agenda-eventos-fastapi.git
cd agenda-eventos-fastapi

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux ou macOS:
source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. (Opcional) Cadastrar eventos de exemplo
python seed.py

# 5. Subir a API
uvicorn app.main:app --reload
```

Com o servidor no ar:

- **Swagger (testar a API pelo navegador):** http://127.0.0.1:8000/docs
- **ReDoc (documentação em formato de leitura):** http://127.0.0.1:8000/redoc
- **Especificação OpenAPI em JSON:** http://127.0.0.1:8000/openapi.json

A raiz `http://127.0.0.1:8000/` redireciona para o Swagger.

> No Windows, se o PowerShell bloquear o `Activate.ps1`, rode antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou use o `cmd` com `.venv\Scripts\activate.bat`.

## Endpoints

| Método | Rota | O que faz | Sucesso | Erros |
|---|---|---|---|---|
| GET | `/eventos` | Lista os eventos ordenados por `data_inicio` | 200 | |
| GET | `/eventos/{id}` | Consulta um evento | 200 | 404, 422 |
| POST | `/eventos` | Cadastra um evento | 201 | 422 |
| PUT | `/eventos/{id}` | Atualiza um evento (envia o evento completo) | 200 | 404, 422 |
| DELETE | `/eventos/{id}` | Remove um evento | 204 | 404 |

### Exemplo de cadastro

`POST /eventos`

```json
{
  "titulo": "Semana Acadêmica de ADS",
  "descricao": "Palestras e minicursos",
  "local": "Auditório IMEPAC",
  "data_inicio": "2026-12-05T19:00:00",
  "data_fim": "2026-12-05T22:00:00",
  "categoria": "palestra",
  "capacidade": 120
}
```

Resposta `201 Created`: o mesmo objeto com o `id` gerado.

### Validações

| Campo | Obrigatório | Regra |
|---|---|---|
| `titulo` | sim | 3 a 100 caracteres; espaços nas pontas são removidos, então `"   "` é recusado |
| `descricao` | não | até 500 caracteres |
| `local` | sim | 2 a 120 caracteres |
| `data_inicio` | sim | data e hora no formato ISO (`AAAA-MM-DDTHH:MM:SS`); no cadastro, não pode estar no passado |
| `data_fim` | não | se informada, precisa ser posterior a `data_inicio` |
| `categoria` | não | `palestra`, `workshop`, `reuniao` ou `outro` (padrão) |
| `capacidade` | não | número inteiro de 1 a 10.000 |

Datas enviadas com fuso (por exemplo `2026-12-05T22:00:00Z`) são convertidas para o horário de Brasília.

Quando algum dado é inválido, a API responde **422** com as mensagens em português:

```json
{
  "detail": "Dados inválidos",
  "erros": [
    { "campo": "titulo", "mensagem": "Deve ter pelo menos 3 caracteres" },
    { "campo": "capacidade", "mensagem": "Deve ser maior ou igual a 1" }
  ]
}
```

## Testes

```bash
pytest -v
```

São 23 testes em `tests/test_eventos.py`, cobrindo os cinco endpoints, os casos de 404 e cada regra de validação. Eles usam um banco SQLite em memória, então não alteram o `eventos.db`.

## Estrutura

```
agenda-eventos-fastapi/
├── app/
│   ├── main.py            # cria a aplicação, registra as rotas e traduz os erros 422
│   ├── database.py        # conexão com o SQLite e sessão por requisição
│   ├── models.py          # tabela Evento
│   ├── schemas.py         # modelos Pydantic de entrada e saída, com as validações
│   └── routers/
│       └── eventos.py     # os cinco endpoints
├── tests/
│   ├── conftest.py        # banco em memória para os testes
│   └── test_eventos.py
├── seed.py                # eventos de exemplo (python seed.py --reset recria)
├── requirements.txt
└── pytest.ini
```

## Como uma requisição percorre o código

1. O Uvicorn recebe a requisição HTTP e entrega ao FastAPI (padrão ASGI).
2. O FastAPI encontra a rota em `routers/eventos.py`.
3. A dependência `get_session` abre uma sessão com o banco.
4. O corpo JSON é validado e convertido pelo modelo Pydantic (`EventoCriar` ou `EventoAtualizar`). Se algo estiver errado, a função nem é chamada e a resposta é 422.
5. A função da rota grava ou lê o evento com o SQLModel.
6. O retorno é convertido para JSON no formato de `EventoSaida`.

## Referências

- FastAPI. Documentação oficial. Disponível em: https://fastapi.tiangolo.com/
- Pydantic. Documentação oficial. Disponível em: https://docs.pydantic.dev/
- SQLModel. Documentação oficial. Disponível em: https://sqlmodel.tiangolo.com/
- Uvicorn. Documentação oficial. Disponível em: https://www.uvicorn.org/
- OpenAPI Initiative. OpenAPI Specification. Disponível em: https://spec.openapis.org/oas/latest.html
