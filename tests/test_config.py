"""Configuração: credencial ausente e inválida (testes simulados, sem rede)."""
import pytest

from config import MODELO_PADRAO, carregar_configuracao, validar_chave
from erros import ErroConfiguracao


def test_credencial_ausente(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ErroConfiguracao, match="Credencial ausente"):
        carregar_configuracao(carregar_dotenv=False)


def test_credencial_vazia():
    with pytest.raises(ErroConfiguracao, match="Credencial ausente"):
        validar_chave("   ")


@pytest.mark.parametrize("chave", ["key_abc123", "abc123", "Bearer sk-abc"])
def test_credencial_com_formato_invalido(chave):
    with pytest.raises(ErroConfiguracao, match="formato|espaços"):
        validar_chave(chave)


def test_credencial_com_aspas():
    with pytest.raises(ErroConfiguracao, match="aspas"):
        validar_chave('"sk-abc"')


def test_mensagem_de_erro_nao_expoe_a_chave():
    with pytest.raises(ErroConfiguracao) as erro:
        validar_chave("key_segredo123")
    assert "segredo123" not in str(erro.value)


def test_configuracao_valida_e_modelo_padrao(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    cfg = carregar_configuracao(carregar_dotenv=False)
    assert cfg.chave == "sk-teste" and cfg.modelo == MODELO_PADRAO


def test_modelo_vem_do_ambiente(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.setenv("OPENAI_MODEL", "modelo-x")
    assert carregar_configuracao(carregar_dotenv=False).modelo == "modelo-x"


def test_repr_da_configuracao_nao_mostra_a_chave(config):
    assert "sk-chave-de-teste" not in repr(config)
