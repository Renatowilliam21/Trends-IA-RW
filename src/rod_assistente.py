"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Marco Básico: fluxo completo em um único arquivo (API REST da OpenAI).
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.openai.com/v1/chat/completions"
MODELO = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")

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
        "max_completion_tokens": 2048,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {"role": "user", "content": f"TRECHO:\n{trecho}\n\nPERGUNTA: {pergunta}"},
        ],
    }
    cabecalhos = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }

    resposta = requests.post(API_URL, json=corpo, headers=cabecalhos)
    dados = resposta.json()
    print(dados["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
