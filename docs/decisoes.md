# Decisões de projeto

**LLM e interface.** Usei a API REST Chat Completions da OpenAI, chamada diretamente com a
biblioteca `requests`, e não um SDK. Assim o código mostra o que trafega na requisição
(endpoint, cabeçalhos, corpo, códigos de status), que é o foco da competência C03. O
modelo é configurável pela variável `OPENAI_MODEL`, porque os nomes mudam com frequência.

**Escopo do problema.** O assistente recebe um único trecho do ROD e uma pergunta. Busca
em vários documentos, upload de PDF e interface web ficam fora do P0, porque exigiriam
divisão do texto e busca por similaridade, assunto de projetos seguintes.

**Prompt.** A instrução de sistema obriga a responder só com o trecho, citar o artigo e
usar uma frase fixa quando a informação não existe. A frase fixa torna o caso "não
encontrei" fácil de testar e de reconhecer.

**Limite de tokens de saída.** Uso `max_completion_tokens` igual a 2048, e não um valor
pequeno. Em modelos com raciocínio, os tokens de "pensamento" contam nesse limite, e um
limite baixo pode gerar resposta vazia.

**Formato da resposta.** Texto livre com a citação do artigo entre parênteses. Descartei
JSON porque a saída é lida por uma pessoa e a validação de estrutura traria complexidade
sem ganho para este caso.

**Organização em módulos.** Cada responsabilidade (entrada, configuração, solicitação,
chamada ao modelo, resposta e apresentação) tem seu módulo, e `rod_assistente.py` só
orquestra. Assim cada parte é testada isolada e uma troca de provedor mexe quase só em
`config.py`, `solicitacao.py`, `cliente.py` e `resposta.py`.

**Parâmetros fora do núcleo.** Modelo, limite de tokens, tempo limite, temperatura,
esforço de raciocínio e nível de log ficam em `configuracao.toml`, com variáveis de ambiente
por cima. A ordem é padrão do código, depois TOML, depois ambiente. Escolhi TOML porque
`tomllib` já vem no Python 3.11 e não exige biblioteca nova. Temperatura e esforço de
raciocínio só entram na requisição quando definidos, porque alguns modelos recusam valores
diferentes do padrão. O núcleo (`solicitacao.py`) apenas lê a configuração.

**Registros.** O log guarda só o que ajuda a entender a execução: modelo, tamanhos em
caracteres, parâmetros, status HTTP, latência, contagem de tokens e tipo do erro. Não guarda
chave, pergunta, trecho, resposta nem caminho de arquivo, porque a pergunta de um aluno ou
servidor pode conter dado pessoal. O texto das mensagens de erro também fica de fora (uma
delas inclui o caminho do arquivo). Um filtro mascara padrões parecidos com chave como
segunda barreira, e testes automatizados verificam que nada disso vaza.

**Validação local da credencial.** Antes de qualquer chamada, `config.py` confere se a
credencial existe, não tem aspas ou espaços e começa com `sk-`. Isso dá uma mensagem
clara sem gastar uma requisição. A credencial recusada pelo serviço (HTTP 401 ou 403) é
tratada à parte em `cliente.py`. Em nenhum caso a chave aparece em mensagens, em `repr` da
configuração ou no corpo da requisição.

**Tratamento de falhas.** Toda falha prevista vira uma subclasse de `ErroAssistente`
(`ErroEntrada`, `ErroConfiguracao`, `ErroServico`, `ErroResposta`) com mensagem em
português. O programa encerra com código 1 e sem traceback. Cobri chave ausente ou
inválida, modelo inexistente, falta de conexão, tempo esgotado, limite de uso, falta de
crédito na conta, indisponibilidade, recusa do modelo, entrada vazia e resposta fora do
formato. A OpenAI usa o mesmo HTTP 429 para limite de taxa e para falta de crédito, então
o código lê o corpo do erro para distinguir os dois.

**Segredos.** A chave fica só em variável de ambiente, lida do `.env`, que está no
`.gitignore`. O repositório traz apenas o `.env.example`.

**Testes.** Os testes automatizados simulam a API com `monkeypatch`. Eles são rápidos,
gratuitos e reproduzíveis. Os testes reais ficam atrás do marcador `real` e só rodam com
`pytest -m real`. A qualidade das respostas é verificada em execuções manuais registradas
em `docs/testes.md`.

**Limite do trecho.** 60 mil caracteres, para caber com folga na janela de contexto e
evitar custo inesperado. O programa recusa trechos maiores com uma mensagem orientando o
usuário a recortar o texto.
