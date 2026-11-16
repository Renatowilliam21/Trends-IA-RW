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
    return {"choices": [{"message": {"role": "assistant", "content": texto},
                         "finish_reason": "stop"}]}


def corpo_erro(codigo, mensagem="erro"):
    return {"error": {"code": codigo, "type": codigo, "message": mensagem}}


@pytest.fixture
def trecho(tmp_path):
    arquivo = tmp_path / "trecho.txt"
    arquivo.write_text("Art. 99. Média parcial igual ou superior a 7,0.", encoding="utf-8")
    return str(arquivo)


@pytest.fixture(autouse=True)
def chave(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "chave-de-teste")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)


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
    mensagens = capturado["json"]["messages"]
    assert mensagens[0]["role"] == "system"
    assert "Art. 99" in mensagens[1]["content"] and "Qual a média?" in mensagens[1]["content"]
    assert capturado["headers"]["Authorization"] == "Bearer chave-de-teste"
    assert capturado["json"]["model"] == ra.MODELO_PADRAO
    assert capturado["json"]["max_completion_tokens"] == ra.MAX_TOKENS_SAIDA
    assert capturado["url"] == ra.API_URL
    assert capturado["timeout"] == ra.TIMEOUT_SEGUNDOS


def test_modelo_vem_da_variavel_de_ambiente(monkeypatch, trecho):
    monkeypatch.setenv("OPENAI_MODEL", "modelo-x")
    capturado = {}
    simular(monkeypatch, RespostaFalsa(corpo=corpo_ok("ok")), capturar=capturado)
    ra.responder(trecho, "Pergunta?")
    assert capturado["json"]["model"] == "modelo-x"


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
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(ra.ErroAssistente, match="Chave de acesso ausente"):
        ra.responder(trecho, "Pergunta?")


@pytest.mark.parametrize(
    "status, corpo, trecho_da_mensagem",
    [
        (401, corpo_erro("invalid_api_key"), "inválida"),
        (403, corpo_erro("forbidden"), "inválida"),
        (404, corpo_erro("model_not_found"), "não encontrado"),
        (429, corpo_erro("rate_limit_exceeded"), "Limite de uso"),
        (429, corpo_erro("insufficient_quota"), "Sem crédito"),
        (503, {}, "indisponível"),
        (400, corpo_erro("invalid_request_error"), "HTTP 400"),
    ],
)
def test_erros_http(monkeypatch, trecho, status, corpo, trecho_da_mensagem):
    simular(monkeypatch, RespostaFalsa(status=status, corpo=corpo))
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
        RespostaFalsa(corpo={"choices": []}),
        RespostaFalsa(corpo=corpo_ok("   ")),
        RespostaFalsa(corpo={"choices": [{"message": {"content": None},
                                          "finish_reason": "length"}]}),
        RespostaFalsa(corpo={"choices": [{"message": {"content": None,
                                                      "refusal": "não posso"},
                                          "finish_reason": "stop"}]}),
    ],
)
def test_resposta_fora_do_formato(monkeypatch, trecho, resposta):
    simular(monkeypatch, resposta)
    with pytest.raises(ra.ErroAssistente):
        ra.responder(trecho, "Pergunta?")


def test_main_devolve_codigo_1_e_mensagem_sem_traceback(capsys):
    codigo = ra.main(["nao_existe.txt", "Pergunta?"])
    saida = capsys.readouterr()
    assert codigo == 1
    assert "Erro:" in saida.err and "Traceback" not in saida.err
