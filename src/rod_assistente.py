"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Marco Básico: fluxo completo em um único arquivo (API REST do Gemini).
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
MODELO = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

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
        "system_instruction": {"parts": [{"text": INSTRUCOES}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"TRECHO:\n{trecho}\n\nPERGUNTA: {pergunta}"}],
            }
        ],
        "generationConfig": {"maxOutputTokens": 2048},
    }
    cabecalhos = {
        "x-goog-api-key": os.getenv("GEMINI_API_KEY"),
        "content-type": "application/json",
    }

    resposta = requests.post(API_URL.format(modelo=MODELO), json=corpo, headers=cabecalhos)
    dados = resposta.json()
    print(dados["candidates"][0]["content"]["parts"][0]["text"])


if __name__ == "__main__":
    main()
