"""Preparação da solicitação enviada ao modelo."""

INSTRUCOES = (
    "Você é um assistente que responde perguntas sobre o Regulamento da "
    "Organização Didática (ROD) do IFCE. Responda usando SOMENTE o trecho "
    "fornecido. Cite o artigo de origem, por exemplo (Art. 99). Se a resposta "
    "não estiver no trecho, responda exatamente: "
    "'Não encontrei essa informação no trecho fornecido.' "
    "Nunca invente regras."
)


def montar_solicitacao(entrada, config):
    """Monta o corpo JSON enviado à API a partir da entrada e da configuração."""
    corpo = {
        "model": config.modelo,
        "max_completion_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {
                "role": "user",
                "content": f"TRECHO:\n{entrada.trecho}\n\nPERGUNTA: {entrada.pergunta}",
            },
        ],
    }
    # Parâmetros opcionais só vão na requisição quando definidos pelo usuário,
    # porque alguns modelos recusam valores diferentes do padrão.
    if config.temperature is not None:
        corpo["temperature"] = config.temperature
    if config.reasoning_effort is not None:
        corpo["reasoning_effort"] = config.reasoning_effort
    return corpo
