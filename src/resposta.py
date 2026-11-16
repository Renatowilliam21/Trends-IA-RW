"""Tratamento da resposta: valida o formato e extrai o texto devolvido pelo modelo."""
from erros import ErroResposta


def extrair_texto(dados):
    """Devolve o texto da resposta ou levanta ErroResposta com explicação."""
    try:
        escolha = dados["choices"][0]
        mensagem = escolha["message"]
    except (KeyError, IndexError, TypeError):
        raise ErroResposta("Resposta do serviço em formato inesperado.")

    if mensagem.get("refusal"):
        raise ErroResposta("O modelo recusou-se a responder a esta pergunta.")

    texto = (mensagem.get("content") or "").strip()
    if not texto:
        if escolha.get("finish_reason") == "length":
            raise ErroResposta(
                "A resposta foi interrompida pelo limite de tokens antes de "
                "gerar texto. Tente uma pergunta mais curta."
            )
        raise ErroResposta("O serviço devolveu uma resposta vazia.")
    return texto
