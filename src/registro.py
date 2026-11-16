"""Registros simples da execução, sem dados sensíveis.

O que é registrado: data e hora, modelo, tamanhos (em caracteres) da pergunta e do
trecho, parâmetros de geração, status HTTP, latência, contagem de tokens usados e o
tipo de erro.

O que NUNCA é registrado: chave de acesso, cabeçalhos, texto da pergunta, conteúdo do
trecho, texto da resposta, caminhos de arquivos e mensagens de erro do usuário.
Como defesa extra, um filtro mascara qualquer padrão parecido com chave.
"""
import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import RAIZ_PROJETO

NOME = "rod"
PADROES_SECRETOS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{6,}"),
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
)


def mascarar(texto):
    """Troca por [OCULTO] qualquer trecho que pareça uma chave ou token."""
    for padrao in PADROES_SECRETOS:
        texto = padrao.sub("[OCULTO]", texto)
    return texto


class FiltroDeSegredos(logging.Filter):
    def filter(self, record):
        record.msg = mascarar(record.getMessage())
        record.args = ()
        return True


def configurar_registro(config):
    """Cria o logger do projeto, gravando em arquivo com rotação (200 KB, 2 cópias)."""
    logger = logging.getLogger(NOME)
    logger.setLevel(config.log_nivel)
    logger.propagate = False
    for antigo in list(logger.handlers):
        antigo.close()
        logger.removeHandler(antigo)

    caminho = Path(config.log_arquivo)
    if not caminho.is_absolute():
        caminho = RAIZ_PROJETO / caminho
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            caminho, maxBytes=200_000, backupCount=2, encoding="utf-8"
        )
    except OSError:
        print("Aviso: não foi possível gravar o registro de execução.", file=sys.stderr)
        handler = logging.NullHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    handler.addFilter(FiltroDeSegredos())
    logger.addHandler(handler)
    return logger


def resumo_uso(dados):
    """Contagem de tokens informada pela API (apenas números), ou 'indisponivel'."""
    uso = dados.get("usage") if isinstance(dados, dict) else None
    if not isinstance(uso, dict):
        return "uso=indisponivel"
    campos = ("prompt_tokens", "completion_tokens", "total_tokens")
    valores = [uso.get(c) if isinstance(uso.get(c), int) else "?" for c in campos]
    return " ".join(f"{c}={v}" for c, v in zip(campos, valores))
