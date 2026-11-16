"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Usa a API REST de Chat Completions da OpenAI.

Uso:
    python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média para aprovação?"
"""
import sys

import requests  # noqa: F401  (usado pelos testes que simulam a API)

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
from cliente import chamar_modelo
from erros import ErroAssistente
from solicitacao import INSTRUCOES, montar_solicitacao  # noqa: F401

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
    return extrair_texto(chamar_modelo(corpo, config))


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
