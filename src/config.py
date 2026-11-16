"""Carregamento e validação da configuração de acesso ao serviço."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from erros import ErroConfiguracao

API_URL = "https://api.openai.com/v1/chat/completions"
MODELO_PADRAO = "gpt-5.6-terra"
TIMEOUT_SEGUNDOS = 30
# Em modelos com raciocínio, os tokens de "pensamento" contam neste limite.
MAX_TOKENS_SAIDA = 2048


@dataclass(frozen=True)
class Configuracao:
    """Valores usados nas chamadas. A chave nunca aparece no repr nem em logs."""

    chave: str = field(repr=False)
    modelo: str = MODELO_PADRAO
    url: str = API_URL
    timeout: int = TIMEOUT_SEGUNDOS
    max_tokens: int = MAX_TOKENS_SAIDA


def validar_chave(chave):
    """Confere a credencial localmente, sem enviá-la a ninguém."""
    chave = (chave or "").strip()
    if not chave:
        raise ErroConfiguracao(
            "Credencial ausente. Defina OPENAI_API_KEY no arquivo .env "
            "(veja .env.example)."
        )
    if any(c.isspace() for c in chave) or chave[0] in "\"'" or chave[-1] in "\"'":
        raise ErroConfiguracao(
            "A credencial em OPENAI_API_KEY contém espaços ou aspas. "
            "Cole apenas a chave, sem aspas."
        )
    if not chave.startswith("sk-"):
        raise ErroConfiguracao(
            "A credencial em OPENAI_API_KEY não tem o formato esperado "
            "(chaves da OpenAI começam com 'sk-'). Gere uma em "
            "platform.openai.com/api-keys."
        )
    return chave


def carregar_configuracao(carregar_dotenv=True):
    """Lê as variáveis de ambiente (e o .env) e devolve a configuração validada."""
    if carregar_dotenv:
        load_dotenv()
    chave = validar_chave(os.getenv("OPENAI_API_KEY"))
    modelo = (os.getenv("OPENAI_MODEL") or "").strip() or MODELO_PADRAO
    return Configuracao(chave=chave, modelo=modelo)
