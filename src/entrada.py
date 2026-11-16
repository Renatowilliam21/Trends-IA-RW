"""Captura e validação da entrada: argumentos, pergunta e trecho do regulamento."""
import argparse
from dataclasses import dataclass

from erros import ErroEntrada

MAX_CARACTERES_TRECHO = 60_000
MAX_CARACTERES_PERGUNTA = 2_000


@dataclass(frozen=True)
class Entrada:
    trecho: str
    pergunta: str


def capturar_argumentos(argv=None):
    """Lê o caminho do arquivo e a pergunta da linha de comando."""
    analisador = argparse.ArgumentParser(
        description="Responde perguntas sobre um trecho do ROD do IFCE."
    )
    analisador.add_argument("trecho", help="arquivo .txt com o trecho do ROD")
    analisador.add_argument("pergunta", help="pergunta entre aspas")
    args = analisador.parse_args(argv)
    return args.trecho, args.pergunta


def validar_pergunta(pergunta):
    """Rejeita perguntas vazias ou longas demais e remove espaços sobrando."""
    pergunta = (pergunta or "").strip()
    if not pergunta:
        raise ErroEntrada("A pergunta não pode estar vazia.")
    if len(pergunta) > MAX_CARACTERES_PERGUNTA:
        raise ErroEntrada(
            f"A pergunta tem {len(pergunta)} caracteres; o limite é "
            f"{MAX_CARACTERES_PERGUNTA}."
        )
    return pergunta


def ler_trecho(caminho):
    """Lê o arquivo de texto com o trecho do regulamento."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            trecho = arquivo.read().strip()
    except FileNotFoundError:
        raise ErroEntrada(f"Arquivo não encontrado: {caminho}")
    except UnicodeDecodeError:
        raise ErroEntrada(f"O arquivo {caminho} não está em UTF-8.")
    except OSError as erro:
        raise ErroEntrada(f"Não foi possível ler {caminho}: {erro.strerror}")

    if not trecho:
        raise ErroEntrada(f"O arquivo {caminho} está vazio.")
    if len(trecho) > MAX_CARACTERES_TRECHO:
        raise ErroEntrada(
            f"O trecho tem {len(trecho)} caracteres; o limite é "
            f"{MAX_CARACTERES_TRECHO}. Use apenas as seções necessárias."
        )
    return trecho


def montar_entrada(caminho, pergunta):
    """Valida a pergunta e o arquivo e devolve a entrada pronta para uso."""
    pergunta = validar_pergunta(pergunta)
    return Entrada(trecho=ler_trecho(caminho), pergunta=pergunta)
