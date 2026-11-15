"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Marco Básico: fluxo completo em um único arquivo.
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.anthropic.com/v1/messages"
MODELO = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

INSTRUCOES = (
    "Você é um assistente que responde perguntas sobre o Regulamento da "
    "Organização Didática (ROD) do IFCE. Responda usando SOMENTE o trecho "
    "fornecido. Cite o artigo de origem, por exemplo (Art. 99). Se a resposta "
    "não estiver no trecho, responda exatamente: "
    "'Não encontrei essa informação no trecho fornecido.' "
    "Nunca invente regras."
)


def main():
    caminho = sys.argv[1]
    pergunta = sys.argv[2]

    with open(caminho, encoding="utf-8") as arquivo:
        trecho = arquivo.read()

    corpo = {
        "model": MODELO,
        "max_tokens": 600,
        "system": INSTRUCOES,
        "messages": [
            {
                "role": "user",
                "content": f"TRECHO:\n{trecho}\n\nPERGUNTA: {pergunta}",
            }
        ],
    }
    cabecalhos = {
        "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    resposta = requests.post(API_URL, json=corpo, headers=cabecalhos)
    dados = resposta.json()
    print(dados["content"][0]["text"])


if __name__ == "__main__":
    main()
