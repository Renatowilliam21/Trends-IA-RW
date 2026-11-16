"""Registros: úteis para entender a execução e sem dados sensíveis."""
import logging

import requests

import rod_assistente as ra
from conftest import RespostaFalsa, corpo_ok, corpo_erro
from registro import mascarar, resumo_uso

SEGREDO = "sk-SEGREDO1234567890"
PERGUNTA = "pergunta-sigilosa-do-aluno-Maria"
RESPOSTA = "resposta-confidencial-xyz"


def rodar(trecho, monkeypatch, tmp_path, simular, resposta=None, erro=None, pergunta=PERGUNTA):
    arquivo_log = tmp_path / "logs" / "execucao.log"
    monkeypatch.setenv("OPENAI_API_KEY", SEGREDO)
    monkeypatch.setenv("ROD_LOG_ARQUIVO", str(arquivo_log))
    monkeypatch.setattr("config.load_dotenv", lambda: None)
    simular(resposta, erro=erro)
    codigo = ra.main([trecho, pergunta])
    for h in logging.getLogger("rod").handlers:
        h.flush()
    return codigo, arquivo_log.read_text(encoding="utf-8")


def test_log_de_sucesso_tem_dados_de_execucao(trecho, monkeypatch, tmp_path, simular):
    corpo = corpo_ok(RESPOSTA)
    corpo["usage"] = {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150}
    codigo, log = rodar(trecho, monkeypatch, tmp_path, simular, RespostaFalsa(corpo=corpo))
    assert codigo == 0
    for esperado in ("inicio modelo=", "trecho_chars=", "pergunta_chars=", "status=200",
                     "latencia_ms=", "sucesso", "total_tokens=150"):
        assert esperado in log


def test_log_nao_contem_segredos_nem_conteudo(trecho, monkeypatch, tmp_path, simular):
    _, log = rodar(trecho, monkeypatch, tmp_path, simular,
                   RespostaFalsa(corpo=corpo_ok(RESPOSTA)))
    assert SEGREDO not in log and "Bearer" not in log
    assert PERGUNTA not in log          # texto da pergunta
    assert RESPOSTA not in log          # texto da resposta
    assert "Art. 99" not in log         # conteúdo do trecho
    assert trecho not in log            # caminho do arquivo


def test_log_de_erro_registra_so_o_tipo(trecho, monkeypatch, tmp_path, simular):
    codigo, log = rodar(trecho, monkeypatch, tmp_path, simular,
                        RespostaFalsa(status=401, corpo=corpo_erro("invalid_api_key")))
    assert codigo == 1
    assert "status=401" in log and "falha tipo=ErroServico" in log
    assert SEGREDO not in log


def test_log_de_timeout(trecho, monkeypatch, tmp_path, simular):
    codigo, log = rodar(trecho, monkeypatch, tmp_path, simular,
                        erro=requests.exceptions.Timeout())
    assert codigo == 1 and "timeout apos" in log


def test_mascara_chaves_e_cabecalhos():
    assert "sk-ABCDEF123456" not in mascarar("erro com sk-ABCDEF123456 no meio")
    assert "token123" not in mascarar("Authorization: Bearer token123")


def test_resumo_de_uso_ignora_valores_estranhos():
    assert resumo_uso({"usage": {"total_tokens": 5, "prompt_tokens": "x"}}) == (
        "prompt_tokens=? completion_tokens=? total_tokens=5")
    assert resumo_uso({}) == "uso=indisponivel"
    assert resumo_uso(None) == "uso=indisponivel"


def test_falha_ao_gravar_log_nao_derruba_o_programa(trecho, monkeypatch, tmp_path, simular, capsys):
    bloqueio = tmp_path / "arquivo_no_lugar_de_pasta"
    bloqueio.write_text("x")
    monkeypatch.setenv("OPENAI_API_KEY", SEGREDO)
    monkeypatch.setenv("ROD_LOG_ARQUIVO", str(bloqueio / "sub" / "log.log"))
    monkeypatch.setattr("config.load_dotenv", lambda: None)
    simular(RespostaFalsa(corpo=corpo_ok(RESPOSTA)))
    assert ra.main([trecho, "Pergunta?"]) == 0
    saida = capsys.readouterr()
    assert RESPOSTA in saida.out and "Aviso" in saida.err
