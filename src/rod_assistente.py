"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Usa a API REST de Chat Completions da OpenAI.

Uso:
    python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média para aprovação?"
"""
import argparse
import os
import sys

import requests
from dotenv import load_dotenv

API_URL = "https://api.openai.com/v1/chat/completions"
MODELO_PADRAO = "gpt-5.6-terra"
TIMEOUT_SEGUNDOS = 30
MAX_CARACTERES_TRECHO = 60_000
# Em modelos com raciocínio, os tokens de "pensamento" contam neste limite.
MAX_TOKENS_SAIDA = 2048

INSTRUCOES = (
    "Você é um assistente que responde perguntas sobre o Regulamento da "
    "Organização Didática (ROD) do IFCE. Responda usando SOMENTE o trecho "
    "fornecido. Cite o artigo de origem, por exemplo (Art. 99). Se a resposta "
    "não estiver no trecho, responda exatamente: "
    "'Não encontrei essa informação no trecho fornecido.' "
    "Nunca invente regras."
)


class ErroAssistente(Exception):
    """Falha prevista, com mensagem pensada para o usuário final."""


def ler_trecho(caminho):
    """Lê o arquivo de texto com o trecho do regulamento."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            trecho = arquivo.read().strip()
    except FileNotFoundError:
        raise ErroAssistente(f"Arquivo não encontrado: {caminho}")
    except UnicodeDecodeError:
        raise ErroAssistente(f"O arquivo {caminho} não está em UTF-8.")
    except OSError as erro:
        raise ErroAssistente(f"Não foi possível ler {caminho}: {erro.strerror}")

    if not trecho:
        raise ErroAssistente(f"O arquivo {caminho} está vazio.")
    if len(trecho) > MAX_CARACTERES_TRECHO:
        raise ErroAssistente(
            f"O trecho tem {len(trecho)} caracteres; o limite é "
            f"{MAX_CARACTERES_TRECHO}. Use apenas as seções necessárias."
        )
    return trecho


def validar_pergunta(pergunta):
    """Rejeita perguntas vazias e devolve o texto sem espaços sobrando."""
    pergunta = (pergunta or "").strip()
    if not pergunta:
        raise ErroAssistente("A pergunta não pode estar vazia.")
    return pergunta


def obter_chave():
    """Lê a chave da API do ambiente (nunca do código)."""
    chave = os.getenv("OPENAI_API_KEY", "").strip()
    if not chave:
        raise ErroAssistente(
            "Chave de acesso ausente. Defina OPENAI_API_KEY no arquivo .env "
            "(veja .env.example)."
        )
    return chave


def montar_requisicao(trecho, pergunta, modelo):
    """Monta o corpo JSON enviado à API."""
    return {
        "model": modelo,
        "max_completion_tokens": MAX_TOKENS_SAIDA,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {"role": "user", "content": f"TRECHO:\n{trecho}\n\nPERGUNTA: {pergunta}"},
        ],
    }


def _detalhe_do_erro(resposta):
    """Texto do erro devolvido pela API, em minúsculas, ou '' se não houver."""
    try:
        erro = resposta.json().get("error", {}) or {}
        partes = [str(erro.get("code", "")), str(erro.get("type", "")),
                  str(erro.get("message", ""))]
        return " ".join(partes).lower()
    except (ValueError, AttributeError, TypeError):
        return ""


def chamar_llm(corpo, chave):
    """Envia a requisição e devolve o JSON da resposta, tratando falhas."""
    cabecalhos = {
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
    }
    try:
        resposta = requests.post(
            API_URL, json=corpo, headers=cabecalhos, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.Timeout:
        raise ErroAssistente(
            f"O serviço não respondeu em {TIMEOUT_SEGUNDOS} segundos. "
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


def responder(caminho, pergunta, modelo=None):
    """Fluxo completo: valida entradas, consulta o LLM e devolve o texto."""
    pergunta = validar_pergunta(pergunta)
    trecho = ler_trecho(caminho)
    chave = obter_chave()
    modelo = modelo or os.getenv("OPENAI_MODEL", MODELO_PADRAO)
    corpo = montar_requisicao(trecho, pergunta, modelo)
    return extrair_texto(chamar_llm(corpo, chave))


def main(argv=None):
    load_dotenv()
    analisador = argparse.ArgumentParser(
        description="Responde perguntas sobre um trecho do ROD do IFCE."
    )
    analisador.add_argument("trecho", help="arquivo .txt com o trecho do ROD")
    analisador.add_argument("pergunta", help="pergunta entre aspas")
    args = analisador.parse_args(argv)

    try:
        print(responder(args.trecho, args.pergunta))
    except ErroAssistente as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
