"""Fluxo completo e apresentação (API simulada)."""
import rod_assistente as ra
from conftest import RespostaFalsa, corpo_ok


def test_fluxo_com_citacao(trecho, config, simular):
    capturado = {}
    simular(RespostaFalsa(corpo=corpo_ok("7,0 (Art. 99).")), capturar=capturado)
    assert ra.responder(trecho, "Qual a média?", config) == "7,0 (Art. 99)."
    usuario = capturado["json"]["messages"][1]["content"]
    assert "Art. 99" in usuario and "Qual a média?" in usuario
    assert capturado["json"]["messages"][0]["role"] == "system"


def test_resposta_de_nao_encontrado_e_repassada(trecho, config, simular):
    msg = "Não encontrei essa informação no trecho fornecido."
    simular(RespostaFalsa(corpo=corpo_ok(msg)))
    assert ra.responder(trecho, "Qual o valor da bolsa?", config) == msg


def test_main_sucesso(trecho, monkeypatch, simular, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.setattr("config.load_dotenv", lambda: None)
    simular(RespostaFalsa(corpo=corpo_ok("Resposta (Art. 99).")))
    assert ra.main([trecho, "Pergunta?"]) == 0
    assert capsys.readouterr().out.strip() == "Resposta (Art. 99)."


def test_main_sem_credencial(trecho, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("config.load_dotenv", lambda: None)
    assert ra.main([trecho, "Pergunta?"]) == 1
    saida = capsys.readouterr()
    assert "Credencial ausente" in saida.err and "Traceback" not in saida.err


def test_main_pergunta_vazia_nao_chama_o_servico(trecho, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    assert ra.main([trecho, "  "]) == 1
    assert "vazia" in capsys.readouterr().err


def test_main_arquivo_inexistente(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    assert ra.main(["nao_existe.txt", "Pergunta?"]) == 1
    saida = capsys.readouterr()
    assert "não encontrado" in saida.err and "Traceback" not in saida.err


def test_programa_real_sem_credencial_mostra_so_a_mensagem_de_erro(tmp_path):
    """Roda o programa em processo separado: o pytest esconde logs soltos, o terminal não."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    ambiente = dict(os.environ, OPENAI_API_KEY="", ROD_LOG_ARQUIVO=str(tmp_path / "l.log"))
    trecho = tmp_path / "t.txt"
    trecho.write_text("Art. 1. Texto.", encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, str(raiz / "src" / "rod_assistente.py"), str(trecho), "Pergunta?"],
        capture_output=True, text=True, env=ambiente, cwd=tmp_path,
    )
    assert resultado.returncode == 1
    linhas = [l for l in resultado.stderr.splitlines() if l.strip()]
    assert len(linhas) == 1 and linhas[0].startswith("Erro: Credencial ausente")
