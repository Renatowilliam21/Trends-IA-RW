"""Apresentação do resultado e das mensagens de erro ao usuário."""
import sys


def exibir_resposta(texto, saida=None):
    """Mostra a resposta do assistente na saída padrão."""
    print(texto, file=saida or sys.stdout)


def exibir_erro(erro, saida=None):
    """Mostra uma mensagem de erro curta, sem detalhes técnicos, na saída de erro."""
    print(f"Erro: {erro}", file=saida or sys.stderr)
