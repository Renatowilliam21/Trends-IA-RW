"""Chamada ao modelo: envia a solicitação e traduz as falhas em mensagens claras."""
import requests

from erros import ErroServico


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


def chamar_modelo(corpo, config):
    """Envia a requisição e devolve o JSON da resposta, tratando falhas.

    A credencial vai apenas no cabeçalho Authorization e nunca em mensagens.
    """
    cabecalhos = {
        "Authorization": f"Bearer {config.chave}",
        "Content-Type": "application/json",
    }
    try:
        resposta = requests.post(
            config.url, json=corpo, headers=cabecalhos, timeout=config.timeout
        )
    except requests.exceptions.Timeout:
        raise ErroServico(
            f"O serviço não respondeu em {config.timeout} segundos. "
            "Tente novamente."
        )
    except requests.exceptions.ConnectionError:
        raise ErroServico("Sem conexão com o serviço. Verifique sua internet.")
    except requests.exceptions.RequestException:
        raise ErroServico("Falha de comunicação com o serviço. Tente novamente.")

    status = resposta.status_code
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
        raise ErroServico(f"Requisição recusada pelo serviço (HTTP {status}).")

    try:
        return resposta.json()
    except ValueError:
        raise ErroServico("Resposta do serviço em formato inesperado.")
