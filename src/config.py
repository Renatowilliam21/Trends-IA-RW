"""Carregamento e validação da configuração.

Ordem de prioridade (a última vence):
    1. valores padrão deste módulo;
    2. arquivo configuracao.toml (parâmetros, sem segredos);
    3. variáveis de ambiente (inclui o arquivo .env).
A credencial vem somente de OPENAI_API_KEY, nunca do arquivo TOML.
"""
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from erros import ErroConfiguracao

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_PADRAO = RAIZ_PROJETO / "configuracao.toml"

API_URL = "https://api.openai.com/v1/chat/completions"
MODELO_PADRAO = "gpt-5.6-terra"
TIMEOUT_SEGUNDOS = 30
# Em modelos com raciocínio, os tokens de "pensamento" contam neste limite.
MAX_TOKENS_SAIDA = 2048
NIVEIS_DE_LOG = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass(frozen=True)
class Configuracao:
    """Valores usados nas chamadas. A chave nunca aparece no repr nem em logs."""

    chave: str = field(repr=False)
    modelo: str = MODELO_PADRAO
    url: str = API_URL
    timeout: int = TIMEOUT_SEGUNDOS
    max_tokens: int = MAX_TOKENS_SAIDA
    temperature: float | None = None
    reasoning_effort: str | None = None
    log_nivel: str = "INFO"
    log_arquivo: str = "logs/assistente.log"


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


def ler_arquivo_toml(caminho):
    """Lê o TOML de parâmetros. Arquivo ausente vale como 'sem ajustes'."""
    caminho = Path(caminho)
    if not caminho.exists():
        return {}
    try:
        with open(caminho, "rb") as arquivo:
            return tomllib.load(arquivo)
    except tomllib.TOMLDecodeError as erro:
        raise ErroConfiguracao(
            f"O arquivo {caminho.name} tem erro de sintaxe: {erro}"
        )
    except OSError as erro:
        raise ErroConfiguracao(f"Não foi possível ler {caminho.name}: {erro.strerror}")


def _inteiro_positivo(valor, nome):
    try:
        numero = int(str(valor).strip())
    except ValueError:
        raise ErroConfiguracao(f"{nome} deve ser um número inteiro (recebido: {valor!r}).")
    if numero < 1:
        raise ErroConfiguracao(f"{nome} deve ser maior que zero (recebido: {numero}).")
    return numero


def _temperatura(valor):
    try:
        numero = float(str(valor).strip())
    except ValueError:
        raise ErroConfiguracao(f"temperature deve ser um número (recebido: {valor!r}).")
    if not 0 <= numero <= 2:
        raise ErroConfiguracao(f"temperature deve estar entre 0 e 2 (recebido: {numero}).")
    return numero


def _texto_opcional(valor):
    valor = str(valor).strip() if valor is not None else ""
    return valor or None


def montar_configuracao(chave, toml=None, ambiente=None):
    """Combina padrões, TOML e variáveis de ambiente em uma Configuracao validada."""
    toml = toml or {}
    ambiente = os.environ if ambiente is None else ambiente

    def escolher(variavel, secao, nome):
        """Variável de ambiente vence o TOML; vazio conta como 'não definido'."""
        valor = ambiente.get(variavel)
        if valor is not None and str(valor).strip() != "":
            return valor
        return toml.get(secao, {}).get(nome)

    modelo = _texto_opcional(escolher("OPENAI_MODEL", "modelo", "nome")) or MODELO_PADRAO
    max_tokens = escolher("OPENAI_MAX_TOKENS", "geracao", "max_tokens")
    timeout = escolher("OPENAI_TIMEOUT", "servico", "timeout_segundos")
    temperatura = escolher("OPENAI_TEMPERATURE", "geracao", "temperature")
    esforco = escolher("OPENAI_REASONING_EFFORT", "geracao", "reasoning_effort")
    nivel = _texto_opcional(escolher("ROD_LOG_NIVEL", "registro", "nivel")) or "INFO"
    arquivo = _texto_opcional(escolher("ROD_LOG_ARQUIVO", "registro", "arquivo"))

    nivel = nivel.upper()
    if nivel not in NIVEIS_DE_LOG:
        raise ErroConfiguracao(
            f"Nível de log inválido: {nivel!r}. Use um de: {', '.join(NIVEIS_DE_LOG)}."
        )

    return Configuracao(
        chave=chave,
        modelo=modelo,
        max_tokens=_inteiro_positivo(max_tokens, "max_tokens")
        if max_tokens is not None else MAX_TOKENS_SAIDA,
        timeout=_inteiro_positivo(timeout, "timeout_segundos")
        if timeout is not None else TIMEOUT_SEGUNDOS,
        temperature=_temperatura(temperatura) if temperatura is not None else None,
        reasoning_effort=_texto_opcional(esforco),
        log_nivel=nivel,
        log_arquivo=arquivo or "logs/assistente.log",
    )


def carregar_configuracao(carregar_dotenv=True, caminho_toml=None):
    """Lê o .env, o TOML e o ambiente e devolve a configuração validada."""
    if carregar_dotenv:
        load_dotenv()
    chave = validar_chave(os.getenv("OPENAI_API_KEY"))
    caminho = caminho_toml or os.getenv("ROD_CONFIG") or ARQUIVO_PADRAO
    return montar_configuracao(chave, ler_arquivo_toml(caminho))
