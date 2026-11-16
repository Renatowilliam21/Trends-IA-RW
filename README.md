# Assistente do ROD (P0 Primeiro fluxo com LLM)

Aplicação de linha de comando em Python que responde perguntas sobre um trecho do
Regulamento da Organização Didática (ROD) do IFCE, citando o artigo de origem. Se a
resposta não estiver no trecho, ela diz que não encontrou, em vez de inventar.

**Problema em uma frase:** estudantes e servidores têm dificuldade para localizar regras
em documentos institucionais longos.

## Requisitos

- Python 3.11 ou superior (usa o módulo `tomllib`). Versões testadas em `docs/ambiente.md`.
- Git
- Uma chave de API da OpenAI (https://platform.openai.com/api-keys), com crédito na conta de desenvolvedor. A assinatura do ChatGPT não inclui acesso à API.

## Instalação

Linux ou macOS:

```bash
git clone https://github.com/Renatowilliam21/Trends-IA-RW.git
cd Trends-IA-RW
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
git clone https://github.com/Renatowilliam21/Trends-IA-RW.git
cd Trends-IA-RW
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.

## Configuração

**1. Credencial (obrigatória).** Crie o arquivo `.env` a partir do modelo e coloque a sua
chave, que começa com `sk-`, sem aspas e sem espaços:

```bash
cp .env.example .env              # Windows: copy .env.example .env
```

```text
OPENAI_API_KEY=sk-...sua-chave...
```

Se ao executar aparecer "Credencial ausente", a chave ainda não foi preenchida ou o arquivo
não foi salvo (o `.env.example` vem com `OPENAI_API_KEY=` vazio).

O `.env` está no `.gitignore` e nunca deve ser enviado ao GitHub. A chave é lida somente
dele (ou do ambiente), nunca do `configuracao.toml`.

**2. Parâmetros (opcional).** O arquivo `configuracao.toml` guarda os parâmetros sem
segredos. Altere ali, sem mexer no código. Uma variável de ambiente (ou uma linha no
`.env`) tem prioridade sobre o arquivo.

| Parâmetro | `configuracao.toml` | Variável | Padrão |
| --- | --- | --- | --- |
| Modelo | `[modelo] nome` | `OPENAI_MODEL` | `gpt-5.6-terra` |
| Limite de tokens de saída | `[geracao] max_tokens` | `OPENAI_MAX_TOKENS` | 2048 |
| Temperatura (opcional) | `[geracao] temperature` | `OPENAI_TEMPERATURE` | não enviada |
| Esforço de raciocínio (opcional) | `[geracao] reasoning_effort` | `OPENAI_REASONING_EFFORT` | não enviado |
| Tempo limite da chamada (s) | `[servico] timeout_segundos` | `OPENAI_TIMEOUT` | 30 |
| Nível do registro | `[registro] nivel` | `ROD_LOG_NIVEL` | INFO |
| Arquivo de registro | `[registro] arquivo` | `ROD_LOG_ARQUIVO` | `logs/assistente.log` |

Os nomes de modelos mudam com frequência e nem todo modelo aceita todos os parâmetros. Se
a API recusar um parâmetro, a mensagem de erro mostra o motivo. Para outro arquivo de
parâmetros, use `ROD_CONFIG=caminho/do/arquivo.toml`.

## Execução

```bash
python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média mínima para aprovação direta na graduação?"
```

Exemplo de saída esperada (o texto exato pode variar entre execuções):

```text
Média parcial (MP) igual ou superior a 7,0, com frequência de pelo menos 75% (Art. 99).
```

Trechos disponíveis em `dados/`:

| Arquivo | Conteúdo | Artigos |
| --- | --- | --- |
| `rod_avaliacao.txt` | Avaliação em cursos de créditos por disciplina | 97 a 100 |
| `rod_segunda_chamada.txt` | Segunda chamada | 110 a 112 |
| `rod_trancamento.txt` | Trancamento de matrícula e de disciplina | 149 a 155 |

Você pode usar qualquer outro `.txt` de até 60 mil caracteres.

## Estrutura do código

| Módulo | Responsabilidade |
| --- | --- |
| `src/entrada.py` | captura dos argumentos e validação da pergunta e do arquivo |
| `src/config.py` | carregamento e validação da configuração (padrões, `configuracao.toml`, ambiente) e da credencial |
| `src/solicitacao.py` | preparação da solicitação enviada ao modelo |
| `src/cliente.py` | chamada ao modelo e tradução das falhas de rede e HTTP |
| `src/resposta.py` | tratamento da resposta (vazia, recusada, formato inesperado) |
| `src/apresentacao.py` | exibição da resposta e das mensagens de erro |
| `src/registro.py` | registros da execução, sem dados sensíveis |
| `src/rod_assistente.py` | orquestra as etapas acima (ponto de entrada) |
| `src/erros.py` | tipos de erro previstos |

## Registros

Cada execução grava linhas simples em `logs/assistente.log` (pasta ignorada pelo Git, com
rotação de 200 KB). Exemplo:

```text
2026-11-15 21:40:02 INFO rod inicio modelo=gpt-5.6-terra trecho_chars=3210 pergunta_chars=58 max_tokens=2048 temperature=None reasoning_effort=None
2026-11-15 21:40:09 INFO rod.cliente resposta status=200 latencia_ms=7312
2026-11-15 21:40:09 INFO rod sucesso resposta_chars=142 prompt_tokens=1022 completion_tokens=310 total_tokens=1332
```

O arquivo `logs/assistente.log` só é criado na primeira execução com configuração válida.

O registro **não** guarda chave, cabeçalhos, texto da pergunta, conteúdo do trecho, texto
da resposta nem caminhos de arquivo. Só tamanhos, status, tempo, contagem de tokens e o
tipo do erro. Há testes automatizados que verificam isso (`tests/test_registro.py`).

## Erros e mensagens

O programa encerra com código 1 e uma mensagem em português, sem traceback e sem mostrar
a credencial. Exemplos:

```text
$ python src/rod_assistente.py dados/rod_avaliacao.txt "   "
Erro: A pergunta não pode estar vazia.

$ python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média?"   # sem .env
Erro: Credencial ausente. Defina OPENAI_API_KEY no arquivo .env (veja .env.example).

$ python src/rod_assistente.py dados/rod_avaliacao.txt "Qual a média?"   # chave key_...
Erro: A credencial em OPENAI_API_KEY não tem o formato esperado (chaves da OpenAI começam com 'sk-'). Gere uma em platform.openai.com/api-keys.
```

Outros casos tratados: credencial recusada pelo serviço, modelo inexistente, falta de
crédito, limite de uso, serviço indisponível, falta de conexão, timeout, resposta vazia,
recusa do modelo e resposta fora do formato.

## Testes

Há dois tipos, e eles não se misturam:

| Tipo | Comando | Usa a API? | Precisa de chave? |
| --- | --- | --- | --- |
| Simulados (padrão) | `python -m pytest` | Não, `requests.post` é substituído | Não |
| Reais (opcional) | `python -m pytest -m real` | Sim, gera custo pequeno | Sim, com crédito |

Os testes simulados demonstram credencial ausente, credencial inválida, indisponibilidade,
timeout, falha de comunicação e resposta inesperada. Os testes reais e as execuções
manuais com a API real estão registrados em `docs/testes.md`.

## Documentação

- `docs/testes.md`: testes simulados e reais, casos de sucesso e de falha
- `docs/ambiente.md`: versões do Python e das bibliotecas
- `docs/validacao-ambiente.md`: validação em ambiente limpo, problemas encontrados e correções
- `docs/decisoes.md`: principais decisões de projeto
- `docs/uso-de-ia.md`: como ferramentas de IA foram usadas no desenvolvimento

## Limitações

- O trecho inteiro vai no prompt. Não há busca em vários documentos.
- Respostas de LLM podem errar. Confira sempre o artigo citado no texto original.
- O ROD usado é o de 2015 (Resolução Consup nº 35). Verifique se continua em vigor.
