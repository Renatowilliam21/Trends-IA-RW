"""Apoio comum aos testes: API simulada e configuração de teste."""
import pytest
import requests

import cliente
from config import Configuracao


class RespostaFalsa:
    def __init__(self, status=200, corpo=None, json_invalido=False):
        self.status_code = status
        self._corpo = corpo
        self._json_invalido = json_invalido

    def json(self):
        if self._json_invalido:
            raise ValueError("json inválido")
        return self._corpo


def corpo_ok(texto):
    return {"choices": [{"message": {"role": "assistant", "content": texto},
                         "finish_reason": "stop"}]}


def corpo_erro(codigo, mensagem="erro"):
    return {"error": {"code": codigo, "type": codigo, "message": mensagem}}


@pytest.fixture
def config():
    return Configuracao(chave="sk-chave-de-teste")


@pytest.fixture
def trecho(tmp_path):
    arquivo = tmp_path / "trecho.txt"
    arquivo.write_text("Art. 99. Média parcial igual ou superior a 7,0.", encoding="utf-8")
    return str(arquivo)


@pytest.fixture
def simular(monkeypatch):
    """Substitui requests.post por uma função falsa. Nenhuma chamada real é feita."""
    def _simular(resposta=None, erro=None, capturar=None):
        def falso_post(url, json=None, headers=None, timeout=None):
            if capturar is not None:
                capturar.update(url=url, json=json, headers=headers, timeout=timeout)
            if erro:
                raise erro
            return resposta
        monkeypatch.setattr(cliente.requests, "post", falso_post)
    return _simular
