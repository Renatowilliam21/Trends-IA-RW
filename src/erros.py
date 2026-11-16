"""Erros previstos do assistente, todos com mensagem pensada para o usuário final."""


class ErroAssistente(Exception):
    """Falha prevista. A mensagem explica o que aconteceu e o que fazer."""


class ErroConfiguracao(ErroAssistente):
    """Configuração de acesso ausente ou inválida."""


class ErroEntrada(ErroAssistente):
    """Pergunta ou arquivo de entrada inválido."""


class ErroServico(ErroAssistente):
    """Falha de comunicação, autenticação ou disponibilidade do serviço."""


class ErroResposta(ErroAssistente):
    """Resposta vazia, bloqueada ou em formato inesperado."""
