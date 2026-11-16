"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Usa a API REST de Chat Completions da OpenAI.

Uso:
    python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média para aprovação?"
"""
import sys

import requests
from dotenv import load_dotenv

from config import (  # noqa: F401  (nomes reexportados)
    API_URL,
    MAX_TOKENS_SAIDA,
    MODELO_PADRAO,
    TIMEOUT_SEGUNDOS,
    carregar_configuracao,
)
from entrada import (  # noqa: F401  (nomes reexportados)
    MAX_CARACTERES_TRECHO,
    capturar_argumentos,
    ler_trecho,
    montar_entrada,
    validar_pergunta,
)
from erros import ErroAssistente
from solicitacao import INSTRUCOES, montar_solicitacao  # noqa: F401

def _detalhe_do_erro(resposta):
    """Texto do erro devolvido pela API, em minúsculas, ou '' se não houver."""
    try:
        erro = resposta.json().get("error", {}) or {}
        partes = [str(erro.get("code", "")), str(erro.get("type", "")),
                  str(erro.get("message", ""))]
        return " ".join(partes).lower()
    except (ValueError, AttributeError, TypeError):
        return ""


def chamar_llm(corpo, config):
    """Envia a requisição e devolve o JSON da resposta, tratando falhas."""
    cabecalhos = {
        "Authorization": f"Bearer {config.chave}",
        "Content-Type": "application/json",
    }
    try:
        resposta = requests.post(
            config.url, json=corpo, headers=cabecalhos, timeout=config.timeout
        )
    except requests.exceptions.Timeout:
        raise ErroAssistente(
            f"O serviço não respondeu em {config.timeout} segundos. "
            "Tente novamente."
        )
    except requests.exceptions.ConnectionError:
        raise ErroAssistente("Sem conexão com o serviço. Verifique sua internet.")

    status = resposta.status_code
    detalhe = _detalhe_do_erro(resposta)
    if status in (401, 403):
        raise ErroAssistente("Chave de acesso inválida ou sem permissão.")
    if status == 404 or "model_not_found" in detalhe:
        raise ErroAssistente(
            f"Modelo '{corpo.get('model')}' não encontrado ou sem acesso. "
            "Confira OPENAI_MODEL no .env."
        )
    if status == 429 and "insufficient_quota" in detalhe:
        raise ErroAssistente(
            "Sem crédito na conta da API. A assinatura do ChatGPT não inclui a "
            "API: adicione crédito em platform.openai.com."
        )
    if status == 429:
        raise ErroAssistente("Limite de uso excedido. Aguarde e tente de novo.")
    if status >= 500:
        raise ErroAssistente("O serviço está indisponível no momento.")
    if status != 200:
        raise ErroAssistente(f"Requisição recusada pelo serviço (HTTP {status}).")

    try:
        return resposta.json()
    except ValueError:
        raise ErroAssistente("Resposta do serviço em formato inesperado.")


def extrair_texto(dados):
    """Extrai o texto da resposta e valida o formato esperado."""
    try:
        escolha = dados["choices"][0]
        mensagem = escolha["message"]
    except (KeyError, IndexError, TypeError):
        raise ErroAssistente("Resposta do serviço em formato inesperado.")

    if mensagem.get("refusal"):
        raise ErroAssistente("O modelo recusou-se a responder a esta pergunta.")

    texto = (mensagem.get("content") or "").strip()
    if not texto:
        if escolha.get("finish_reason") == "length":
            raise ErroAssistente(
                "A resposta foi interrompida pelo limite de tokens antes de "
                "gerar texto. Tente uma pergunta mais curta."
            )
        raise ErroAssistente("O serviço devolveu uma resposta vazia.")
    return texto


def responder(caminho, pergunta, config=None):
    """Fluxo completo: valida entradas, consulta o LLM e devolve o texto."""
    entrada = montar_entrada(caminho, pergunta)
    config = config or carregar_configuracao(carregar_dotenv=False)
    corpo = montar_solicitacao(entrada, config)
    return extrair_texto(chamar_llm(corpo, config))


def main(argv=None):
    load_dotenv()
    caminho, pergunta = capturar_argumentos(argv)
    try:
        print(responder(caminho, pergunta))
    except ErroAssistente as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
