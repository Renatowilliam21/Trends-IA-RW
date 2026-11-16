"""Assistente do ROD: responde perguntas usando apenas um trecho do regulamento.

Este módulo só orquestra as etapas. Cada responsabilidade tem seu módulo:
entrada.py, config.py, solicitacao.py, cliente.py, resposta.py e apresentacao.py.

Uso:
    python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média para aprovação?"
"""
import logging
import sys

from apresentacao import exibir_erro, exibir_resposta
from cliente import chamar_modelo
from config import carregar_configuracao
from entrada import capturar_argumentos, montar_entrada
from erros import ErroAssistente
from registro import configurar_registro, resumo_uso
from resposta import extrair_texto
from solicitacao import montar_solicitacao


def responder(caminho, pergunta, config=None):
    """Executa o fluxo completo e devolve o texto da resposta."""
    entrada = montar_entrada(caminho, pergunta)
    config = config or carregar_configuracao(carregar_dotenv=False)
    corpo = montar_solicitacao(entrada, config)
    dados = chamar_modelo(corpo, config)
    return extrair_texto(dados)


def main(argv=None):
    caminho, pergunta = capturar_argumentos(argv)
    try:
        config = carregar_configuracao(carregar_dotenv=True)
        log = configurar_registro(config)
        entrada = montar_entrada(caminho, pergunta)
        log.info(
            "inicio modelo=%s trecho_chars=%d pergunta_chars=%d max_tokens=%s "
            "temperature=%s reasoning_effort=%s",
            config.modelo, len(entrada.trecho), len(entrada.pergunta),
            config.max_tokens, config.temperature, config.reasoning_effort,
        )
        corpo = montar_solicitacao(entrada, config)
        dados = chamar_modelo(corpo, config)
        texto = extrair_texto(dados)
        log.info("sucesso resposta_chars=%d %s", len(texto), resumo_uso(dados))
        exibir_resposta(texto)
    except ErroAssistente as erro:
        logging.getLogger("rod").error("falha tipo=%s", type(erro).__name__)
        exibir_erro(erro)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
