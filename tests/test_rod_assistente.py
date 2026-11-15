"""Testes com a API simulada: não gastam chamadas nem precisam de chave real."""
import pytest
import requests

import rod_assistente as ra


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
    return {"candidates": [{"content": {"parts": [{"text": texto}]}, "finishReason": "STOP"}]}


@pytest.fixture
def trecho(tmp_path):
    arquivo = tmp_path / "trecho.txt"
    arquivo.write_text("Art. 99. Média parcial igual ou superior a 7,0.", encoding="utf-8")
    return str(arquivo)


@pytest.fixture(autouse=True)
def chave(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)


def simular(monkeypatch, resposta=None, erro=None, capturar=None):
    def falso_post(url, json=None, headers=None, timeout=None):
        if capturar is not None:
            capturar.update(url=url, json=json, headers=headers, timeout=timeout)
        if erro:
            raise erro
        return resposta

    monkeypatch.setattr(ra.requests, "post", falso_post)


# ---------- sucesso ----------

def test_resposta_com_citacao(monkeypatch, trecho):
    simular(monkeypatch, RespostaFalsa(corpo=corpo_ok("7,0 (Art. 99).")))
    assert ra.responder(trecho, "Qual a média?") == "7,0 (Art. 99)."


def test_requisicao_contem_trecho_pergunta_e_chave(monkeypatch, trecho):
    capturado = {}
    simular(monkeypatch, RespostaFalsa(corpo=corpo_ok("ok")), capturar=capturado)
    ra.responder(trecho, "Qual a média?")
    conteudo = capturado["json"]["contents"][0]["parts"][0]["text"]
    assert "Art. 99" in conteudo and "Qual a média?" in conteudo
    assert capturado["headers"]["x-goog-api-key"] == "chave-de-teste"
    assert ra.MODELO_PADRAO in capturado["url"]
    assert capturado["url"].endswith(":generateContent")
    assert capturado["timeout"] == ra.TIMEOUT_SEGUNDOS


def test_resposta_de_nao_encontrado_e_repassada(monkeypatch, trecho):
    msg = "Não encontrei essa informação no trecho fornecido."
    simular(monkeypatch, RespostaFalsa(corpo=corpo_ok(msg)))
    assert ra.responder(trecho, "Qual o valor da bolsa de monitoria?") == msg


# ---------- falhas ----------

def test_pergunta_vazia(trecho):
    with pytest.raises(ra.ErroAssistente, match="pergunta"):
        ra.responder(trecho, "   ")


def test_arquivo_inexistente():
    with pytest.raises(ra.ErroAssistente, match="não encontrado"):
        ra.responder("nao_existe.txt", "Pergunta?")


def test_arquivo_vazio(tmp_path):
    vazio = tmp_path / "vazio.txt"
    vazio.write_text("", encoding="utf-8")
    with pytest.raises(ra.ErroAssistente, match="vazio"):
        ra.responder(str(vazio), "Pergunta?")


def test_trecho_longo_demais(tmp_path):
    longo = tmp_path / "longo.txt"
    longo.write_text("a" * (ra.MAX_CARACTERES_TRECHO + 1), encoding="utf-8")
    with pytest.raises(ra.ErroAssistente, match="limite"):
        ra.responder(str(longo), "Pergunta?")


def test_chave_ausente(monkeypatch, trecho):
    monkeypatch.delenv("GEMINI_API_KEY")
    with pytest.raises(ra.ErroAssistente, match="Chave de acesso ausente"):
        ra.responder(trecho, "Pergunta?")


@pytest.mark.parametrize(
    "status, trecho_da_mensagem",
    [(401, "inválida"), (403, "inválida"), (404, "não encontrado"), (429, "Limite de uso"), (503, "indisponível"), (400, "HTTP 400")],
)
def test_erros_http(monkeypatch, trecho, status, trecho_da_mensagem):
    simular(monkeypatch, RespostaFalsa(status=status, corpo={}))
    with pytest.raises(ra.ErroAssistente, match=trecho_da_mensagem):
        ra.responder(trecho, "Pergunta?")


def test_timeout(monkeypatch, trecho):
    simular(monkeypatch, erro=requests.exceptions.Timeout())
    with pytest.raises(ra.ErroAssistente, match="não respondeu"):
        ra.responder(trecho, "Pergunta?")


def test_sem_conexao(monkeypatch, trecho):
    simular(monkeypatch, erro=requests.exceptions.ConnectionError())
    with pytest.raises(ra.ErroAssistente, match="Sem conexão"):
        ra.responder(trecho, "Pergunta?")


@pytest.mark.parametrize(
    "resposta",
    [
        RespostaFalsa(json_invalido=True),
        RespostaFalsa(corpo={"candidates": []}),
        RespostaFalsa(corpo=corpo_ok("   ")),
        RespostaFalsa(corpo={"candidates": [{"finishReason": "MAX_TOKENS"}]}),
    ],
)
def test_resposta_fora_do_formato(monkeypatch, trecho, resposta):
    simular(monkeypatch, resposta)
    with pytest.raises(ra.ErroAssistente):
        ra.responder(trecho, "Pergunta?")


def test_chave_invalida_vem_como_http_400(monkeypatch, trecho):
    erro = {"error": {"status": "INVALID_ARGUMENT", "message": "API key not valid."}}
    simular(monkeypatch, RespostaFalsa(status=400, corpo=erro))
    with pytest.raises(ra.ErroAssistente, match="inválida"):
        ra.responder(trecho, "Pergunta?")


def test_pergunta_bloqueada_pelo_servico(monkeypatch, trecho):
    corpo = {"promptFeedback": {"blockReason": "SAFETY"}}
    simular(monkeypatch, RespostaFalsa(corpo=corpo))
    with pytest.raises(ra.ErroAssistente, match="bloqueada"):
        ra.responder(trecho, "Pergunta?")


def test_ignora_partes_de_raciocinio(monkeypatch, trecho):
    corpo = {"candidates": [{"content": {"parts": [
        {"text": "pensando...", "thought": True},
        {"text": "7,0 (Art. 99)."},
    ]}}]}
    simular(monkeypatch, RespostaFalsa(corpo=corpo))
    assert ra.responder(trecho, "Pergunta?") == "7,0 (Art. 99)."


def test_modelo_vem_da_variavel_de_ambiente(monkeypatch, trecho):
    monkeypatch.setenv("GEMINI_MODEL", "modelo-x")
    capturado = {}
    simular(monkeypatch, RespostaFalsa(corpo=corpo_ok("ok")), capturar=capturado)
    ra.responder(trecho, "Pergunta?")
    assert "models/modelo-x:generateContent" in capturado["url"]


def test_main_devolve_codigo_1_e_mensagem_sem_traceback(capsys):
    codigo = ra.main(["nao_existe.txt", "Pergunta?"])
    saida = capsys.readouterr()
    assert codigo == 1
    assert "Erro:" in saida.err and "Traceback" not in saida.err
