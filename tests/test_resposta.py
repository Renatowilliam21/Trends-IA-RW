"""Tratamento da resposta: vazia, recusada ou em formato inesperado."""
import pytest

from conftest import corpo_ok
from erros import ErroResposta
from resposta import extrair_texto


def test_extrai_texto():
    assert extrair_texto(corpo_ok("  7,0 (Art. 99).  ")) == "7,0 (Art. 99)."


@pytest.mark.parametrize(
    "dados, mensagem",
    [
        (None, "formato inesperado"),
        ({}, "formato inesperado"),
        ({"choices": []}, "formato inesperado"),
        ({"choices": [{}]}, "formato inesperado"),
        (corpo_ok("   "), "vazia"),
        ({"choices": [{"message": {"content": None}, "finish_reason": "length"}]},
         "limite de tokens"),
        ({"choices": [{"message": {"content": None, "refusal": "não posso"}}]},
         "recusou"),
    ],
)
def test_respostas_problematicas(dados, mensagem):
    with pytest.raises(ErroResposta, match=mensagem):
        extrair_texto(dados)
