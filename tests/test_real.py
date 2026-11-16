"""Testes REAIS: chamam a API da OpenAI. Não rodam por padrão.

Uso: pytest -m real   (precisa de OPENAI_API_KEY válida e crédito na conta)
"""
import os

import pytest

import rod_assistente as ra
from config import carregar_configuracao
from erros import ErroServico

pytestmark = pytest.mark.real
TRECHO = os.path.join(os.path.dirname(__file__), "..", "dados", "rod_avaliacao.txt")


def test_pergunta_com_resposta_no_trecho():
    resposta = ra.responder(TRECHO, "Qual a média mínima para aprovação direta na graduação?",
                            carregar_configuracao())
    assert "7" in resposta and "99" in resposta


def test_pergunta_sem_resposta_no_trecho():
    resposta = ra.responder(TRECHO, "Qual o valor da bolsa de monitoria?",
                            carregar_configuracao())
    assert "Não encontrei" in resposta


def test_credencial_invalida_e_recusada_pelo_servico():
    """Chave com formato válido, mas inexistente: o serviço deve responder 401."""
    from config import Configuracao
    with pytest.raises(ErroServico, match="Credencial inválida"):
        ra.responder(TRECHO, "Pergunta?", Configuracao(chave="sk-chave-que-nao-existe"))
