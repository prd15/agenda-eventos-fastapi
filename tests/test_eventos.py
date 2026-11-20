from datetime import datetime, timedelta

from app.schemas import agora


def data(dias: int, hora: int = 19) -> str:
    d = (agora() + timedelta(days=dias)).replace(hour=hora, minute=0, second=0, microsecond=0)
    return d.isoformat()


def evento(**alteracoes) -> dict:
    base = {
        "titulo": "Semana Acadêmica de ADS",
        "descricao": "Palestras e minicursos",
        "local": "Auditório IMEPAC",
        "data_inicio": data(10),
        "data_fim": data(10, hora=22),
        "categoria": "palestra",
        "capacidade": 120,
    }
    base.update(alteracoes)
    return base


def campos_com_erro(resposta) -> set[str]:
    return {e["campo"] for e in resposta.json()["erros"]}


def test_cadastrar_evento(client):
    r = client.post("/eventos", json=evento())
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] == 1
    assert corpo["titulo"] == "Semana Acadêmica de ADS"
    assert corpo["categoria"] == "palestra"


def test_cadastrar_somente_campos_obrigatorios(client):
    r = client.post("/eventos", json={"titulo": "Reunião", "local": "Sala 3", "data_inicio": data(2)})
    assert r.status_code == 201
    assert r.json()["categoria"] == "outro"
    assert r.json()["data_fim"] is None


def test_remove_espacos_das_pontas(client):
    r = client.post("/eventos", json=evento(titulo="   Hackathon   "))
    assert r.json()["titulo"] == "Hackathon"


def test_listar_vazio(client):
    r = client.get("/eventos")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_ordenado_por_data(client):
    # Cadastra fora de ordem de propósito.
    client.post("/eventos", json=evento(titulo="Terceiro", data_inicio=data(30), data_fim=None))
    client.post("/eventos", json=evento(titulo="Primeiro", data_inicio=data(1), data_fim=None))
    client.post("/eventos", json=evento(titulo="Segundo", data_inicio=data(15), data_fim=None))

    titulos = [e["titulo"] for e in client.get("/eventos").json()]
    assert titulos == ["Primeiro", "Segundo", "Terceiro"]


def test_consultar_evento(client):
    criado = client.post("/eventos", json=evento()).json()
    r = client.get(f"/eventos/{criado['id']}")
    assert r.status_code == 200
    assert r.json() == criado


def test_consultar_inexistente_retorna_404(client):
    r = client.get("/eventos/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Evento não encontrado"


def test_id_que_nao_e_numero_retorna_422(client):
    r = client.get("/eventos/abc")
    assert r.status_code == 422
    assert campos_com_erro(r) == {"evento_id"}


def test_atualizar_evento(client):
    criado = client.post("/eventos", json=evento()).json()
    novo = evento(local="Laboratório 2", capacidade=40)

    r = client.put(f"/eventos/{criado['id']}", json=novo)
    assert r.status_code == 200
    assert r.json()["local"] == "Laboratório 2"
    assert r.json()["capacidade"] == 40
    assert client.get(f"/eventos/{criado['id']}").json()["local"] == "Laboratório 2"


def test_atualizar_inexistente_retorna_404(client):
    r = client.put("/eventos/999", json=evento())
    assert r.status_code == 404


def test_atualizar_com_dados_invalidos_retorna_422(client):
    criado = client.post("/eventos", json=evento()).json()
    r = client.put(f"/eventos/{criado['id']}", json=evento(titulo=""))
    assert r.status_code == 422
    assert "titulo" in campos_com_erro(r)


def test_put_exige_o_evento_completo(client):
    criado = client.post("/eventos", json=evento()).json()
    r = client.put(f"/eventos/{criado['id']}", json={"titulo": "Só o título"})
    assert r.status_code == 422
    assert {"local", "data_inicio"} <= campos_com_erro(r)


def test_remover_evento(client):
    criado = client.post("/eventos", json=evento()).json()
    r = client.delete(f"/eventos/{criado['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/eventos/{criado['id']}").status_code == 404


def test_remover_inexistente_retorna_404(client):
    assert client.delete("/eventos/999").status_code == 404


def test_campos_obrigatorios(client):
    r = client.post("/eventos", json={})
    assert r.status_code == 422
    assert campos_com_erro(r) == {"titulo", "local", "data_inicio"}
    assert all(e["mensagem"] == "Campo obrigatório" for e in r.json()["erros"])


def test_titulo_so_com_espacos(client):
    r = client.post("/eventos", json=evento(titulo="     "))
    assert r.status_code == 422
    assert r.json()["erros"][0] == {"campo": "titulo", "mensagem": "Deve ter pelo menos 3 caracteres"}


def test_titulo_longo_demais(client):
    r = client.post("/eventos", json=evento(titulo="x" * 101))
    assert r.status_code == 422
    assert "titulo" in campos_com_erro(r)


def test_data_fim_antes_do_inicio(client):
    r = client.post("/eventos", json=evento(data_inicio=data(5, hora=20), data_fim=data(5, hora=18)))
    assert r.status_code == 422
    assert "data_fim deve ser posterior a data_inicio" in r.json()["erros"][0]["mensagem"]


def test_data_no_passado(client):
    r = client.post("/eventos", json=evento(data_inicio=data(-1), data_fim=None))
    assert r.status_code == 422
    assert r.json()["erros"][0] == {
        "campo": "data_inicio",
        "mensagem": "data_inicio não pode estar no passado",
    }


def test_data_em_formato_invalido(client):
    r = client.post("/eventos", json=evento(data_inicio="31/12/2026"))
    assert r.status_code == 422
    assert "data_inicio" in campos_com_erro(r)


def test_capacidade_fora_do_limite(client):
    r = client.post("/eventos", json=evento(capacidade=0))
    assert r.status_code == 422
    assert r.json()["erros"][0] == {"campo": "capacidade", "mensagem": "Deve ser maior ou igual a 1"}


def test_categoria_invalida(client):
    r = client.post("/eventos", json=evento(categoria="show"))
    assert r.status_code == 422
    assert "categoria" in campos_com_erro(r)


def test_data_com_fuso_horario_e_convertida(client):
    # 22h em UTC = 19h em Brasília
    utc = (agora() + timedelta(days=3)).replace(hour=22, minute=0, second=0, microsecond=0)
    r = client.post("/eventos", json=evento(data_inicio=utc.isoformat() + "Z", data_fim=None))
    assert r.status_code == 201
    assert datetime.fromisoformat(r.json()["data_inicio"]).hour == 19
