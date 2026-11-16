"""Chamada ao modelo: envia a solicitação e traduz as falhas em mensagens claras."""
import logging
import time

import requests

from erros import ErroServico

log = logging.getLogger("rod.cliente")


def _detalhe_do_erro(resposta):
    """Texto do erro devolvido pela API, em minúsculas, ou '' se não houver."""
    try:
        erro = resposta.json().get("error", {}) or {}
        partes = [
            str(erro.get("code", "")),
            str(erro.get("type", "")),
            str(erro.get("message", "")),
        ]
        return " ".join(partes).lower()
    except (ValueError, AttributeError, TypeError):
        return ""


def _mensagem_curta(resposta, limite=200):
    """Mensagem de erro da API (ajuda a achar um parâmetro recusado), truncada."""
    try:
        mensagem = str(resposta.json().get("error", {}).get("message", "")).strip()
    except (ValueError, AttributeError, TypeError):
        return ""
    return mensagem[:limite]


def chamar_modelo(corpo, config):
    """Envia a requisição e devolve o JSON da resposta, tratando falhas.

    A credencial vai apenas no cabeçalho Authorization e nunca em mensagens.
    """
    cabecalhos = {
        "Authorization": f"Bearer {config.chave}",
        "Content-Type": "application/json",
    }
    inicio = time.perf_counter()
    try:
        resposta = requests.post(
            config.url, json=corpo, headers=cabecalhos, timeout=config.timeout
        )
    except requests.exceptions.Timeout:
        log.warning("timeout apos %ss", config.timeout)
        raise ErroServico(
            f"O serviço não respondeu em {config.timeout} segundos. "
            "Tente novamente."
        )
    except requests.exceptions.ConnectionError:
        log.warning("falha de conexao")
        raise ErroServico("Sem conexão com o serviço. Verifique sua internet.")
    except requests.exceptions.RequestException:
        log.warning("falha de comunicacao")
        raise ErroServico("Falha de comunicação com o serviço. Tente novamente.")

    status = resposta.status_code
    log.info("resposta status=%s latencia_ms=%d", status,
             (time.perf_counter() - inicio) * 1000)
    detalhe = _detalhe_do_erro(resposta)
    if status in (401, 403):
        raise ErroServico(
            "Credencial inválida ou sem permissão. Confira OPENAI_API_KEY no .env."
        )
    if status == 404 or "model_not_found" in detalhe:
        raise ErroServico(
            f"Modelo '{corpo.get('model')}' não encontrado ou sem acesso. "
            "Confira OPENAI_MODEL no .env."
        )
    if status == 429 and "insufficient_quota" in detalhe:
        raise ErroServico(
            "Sem crédito na conta da API. A assinatura do ChatGPT não inclui a "
            "API: adicione crédito em platform.openai.com."
        )
    if status == 429:
        raise ErroServico("Limite de uso excedido. Aguarde e tente de novo.")
    if status >= 500:
        raise ErroServico(
            "O serviço está indisponível no momento. Tente novamente mais tarde."
        )
    if status != 200:
        motivo = _mensagem_curta(resposta)
        sufixo = f": {motivo}" if motivo else "."
        raise ErroServico(f"Requisição recusada pelo serviço (HTTP {status}){sufixo}")

    try:
        return resposta.json()
    except ValueError:
        raise ErroServico("Resposta do serviço em formato inesperado.")
