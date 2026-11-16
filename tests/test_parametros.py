"""Parâmetros alterados por TOML e variáveis de ambiente, sem tocar no núcleo."""
import pytest

from config import (MAX_TOKENS_SAIDA, MODELO_PADRAO, TIMEOUT_SEGUNDOS, ARQUIVO_PADRAO,
                    carregar_configuracao, ler_arquivo_toml, montar_configuracao)
from entrada import Entrada
from erros import ErroConfiguracao
from solicitacao import montar_solicitacao

ENTRADA = Entrada(trecho="Art. 1.", pergunta="Pergunta?")


def test_padroes_sem_toml_nem_ambiente():
    cfg = montar_configuracao("sk-x", toml={}, ambiente={})
    assert (cfg.modelo, cfg.max_tokens, cfg.timeout) == (
        MODELO_PADRAO, MAX_TOKENS_SAIDA, TIMEOUT_SEGUNDOS)
    assert cfg.temperature is None and cfg.reasoning_effort is None


def test_toml_do_projeto_traz_os_mesmos_padroes():
    cfg = montar_configuracao("sk-x", toml=ler_arquivo_toml(ARQUIVO_PADRAO), ambiente={})
    assert (cfg.modelo, cfg.max_tokens, cfg.timeout) == (
        MODELO_PADRAO, MAX_TOKENS_SAIDA, TIMEOUT_SEGUNDOS)


def test_toml_sobrepoe_padroes():
    toml = {"modelo": {"nome": "m-toml"}, "geracao": {"max_tokens": 500, "temperature": 0.2,
                                                     "reasoning_effort": "low"},
            "servico": {"timeout_segundos": 10}}
    cfg = montar_configuracao("sk-x", toml=toml, ambiente={})
    assert (cfg.modelo, cfg.max_tokens, cfg.timeout, cfg.temperature,
            cfg.reasoning_effort) == ("m-toml", 500, 10, 0.2, "low")


def test_ambiente_vence_o_toml():
    toml = {"modelo": {"nome": "m-toml"}, "geracao": {"max_tokens": 500}}
    ambiente = {"OPENAI_MODEL": "m-env", "OPENAI_MAX_TOKENS": "900"}
    cfg = montar_configuracao("sk-x", toml=toml, ambiente=ambiente)
    assert cfg.modelo == "m-env" and cfg.max_tokens == 900


def test_variavel_vazia_conta_como_nao_definida():
    cfg = montar_configuracao("sk-x", toml={"modelo": {"nome": "m-toml"}},
                              ambiente={"OPENAI_MODEL": "  "})
    assert cfg.modelo == "m-toml"


@pytest.mark.parametrize(
    "ambiente, mensagem",
    [
        ({"OPENAI_MAX_TOKENS": "abc"}, "max_tokens deve ser um número inteiro"),
        ({"OPENAI_MAX_TOKENS": "0"}, "maior que zero"),
        ({"OPENAI_TIMEOUT": "-5"}, "maior que zero"),
        ({"OPENAI_TEMPERATURE": "quente"}, "temperature deve ser um número"),
        ({"OPENAI_TEMPERATURE": "3"}, "entre 0 e 2"),
        ({"ROD_LOG_NIVEL": "barulhento"}, "Nível de log inválido"),
    ],
)
def test_valores_invalidos_geram_mensagem_clara(ambiente, mensagem):
    with pytest.raises(ErroConfiguracao, match=mensagem):
        montar_configuracao("sk-x", toml={}, ambiente=ambiente)


def test_toml_com_erro_de_sintaxe(tmp_path):
    ruim = tmp_path / "ruim.toml"
    ruim.write_text("[modelo\nnome = ", encoding="utf-8")
    with pytest.raises(ErroConfiguracao, match="erro de sintaxe"):
        ler_arquivo_toml(ruim)


def test_toml_inexistente_vale_como_sem_ajustes(tmp_path):
    assert ler_arquivo_toml(tmp_path / "nao_existe.toml") == {}


def test_carregar_configuracao_le_toml_indicado(tmp_path, monkeypatch):
    toml = tmp_path / "c.toml"
    toml.write_text('[geracao]\nmax_tokens = 123\n', encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    cfg = carregar_configuracao(carregar_dotenv=False, caminho_toml=toml)
    assert cfg.max_tokens == 123


def test_solicitacao_usa_max_tokens_da_configuracao(config):
    cfg = montar_configuracao(config.chave, toml={"geracao": {"max_tokens": 321}}, ambiente={})
    assert montar_solicitacao(ENTRADA, cfg)["max_completion_tokens"] == 321


def test_solicitacao_omite_parametros_opcionais_quando_nao_definidos(config):
    corpo = montar_solicitacao(ENTRADA, config)
    assert "temperature" not in corpo and "reasoning_effort" not in corpo


def test_solicitacao_inclui_parametros_opcionais_quando_definidos():
    cfg = montar_configuracao(
        "sk-x", toml={"geracao": {"temperature": 0.5, "reasoning_effort": "low"}}, ambiente={})
    corpo = montar_solicitacao(ENTRADA, cfg)
    assert corpo["temperature"] == 0.5 and corpo["reasoning_effort"] == "low"


def test_solicitacao_nunca_leva_a_chave(config):
    assert config.chave not in str(montar_solicitacao(ENTRADA, config))
