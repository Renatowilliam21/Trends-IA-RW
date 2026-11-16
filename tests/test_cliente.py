"""Chamada ao modelo: autenticação, disponibilidade e comunicação (API simulada)."""
import pytest
import requests

from cliente import chamar_modelo
from conftest import RespostaFalsa, corpo_erro, corpo_ok
from erros import ErroServico

CORPO = {"model": "m", "messages": []}


def test_envia_credencial_apenas_no_cabecalho(config, simular):
    capturado = {}
    simular(RespostaFalsa(corpo=corpo_ok("ok")), capturar=capturado)
    chamar_modelo(CORPO, config)
    assert capturado["headers"]["Authorization"] == "Bearer sk-chave-de-teste"
    assert "sk-chave-de-teste" not in str(capturado["json"])
    assert capturado["url"] == config.url and capturado["timeout"] == config.timeout


@pytest.mark.parametrize(
    "status, corpo, mensagem",
    [
        (401, corpo_erro("invalid_api_key"), "Credencial inválida"),
        (403, corpo_erro("forbidden"), "Credencial inválida"),
        (404, corpo_erro("model_not_found"), "não encontrado"),
        (429, corpo_erro("rate_limit_exceeded"), "Limite de uso"),
        (429, corpo_erro("insufficient_quota"), "Sem crédito"),
        (500, {}, "indisponível"),
        (503, {}, "indisponível"),
        (400, corpo_erro("invalid_request_error"), "HTTP 400"),
    ],
)
def test_erros_http(config, simular, status, corpo, mensagem):
    simular(RespostaFalsa(status=status, corpo=corpo))
    with pytest.raises(ErroServico, match=mensagem):
        chamar_modelo(CORPO, config)


def test_credencial_invalida_nao_expoe_a_chave(config, simular):
    simular(RespostaFalsa(status=401, corpo=corpo_erro("invalid_api_key")))
    with pytest.raises(ErroServico) as erro:
        chamar_modelo(CORPO, config)
    assert "sk-chave-de-teste" not in str(erro.value)


@pytest.mark.parametrize(
    "excecao, mensagem",
    [
        (requests.exceptions.Timeout(), "não respondeu"),
        (requests.exceptions.ConnectionError(), "Sem conexão"),
        (requests.exceptions.RequestException(), "Falha de comunicação"),
    ],
)
def test_falhas_de_rede(config, simular, excecao, mensagem):
    simular(erro=excecao)
    with pytest.raises(ErroServico, match=mensagem):
        chamar_modelo(CORPO, config)


def test_resposta_que_nao_e_json(config, simular):
    simular(RespostaFalsa(json_invalido=True))
    with pytest.raises(ErroServico, match="formato inesperado"):
        chamar_modelo(CORPO, config)


def test_erro_400_mostra_motivo_da_api(config, simular):
    simular(RespostaFalsa(status=400, corpo=corpo_erro(
        "unsupported_value", "temperature nao suportada por este modelo")))
    with pytest.raises(ErroServico, match="HTTP 400.*temperature nao suportada"):
        chamar_modelo(CORPO, config)
