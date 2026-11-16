# Registro de testes

## 1. Testes simulados (sem rede, sem chave)

Executar com `python -m pytest`. Resultado na criação deste documento: 73 testes passando.
A API é substituída por uma função falsa (`monkeypatch` em `requests.post`).

| Arquivo | O que demonstra |
| --- | --- |
| `test_config.py` | credencial ausente, vazia, com aspas, com formato inválido; chave nunca exposta |
| `test_entrada.py` | pergunta vazia ou longa, arquivo inexistente, vazio, fora de UTF-8 ou grande demais |
| `test_cliente.py` | credencial recusada (401/403), modelo inexistente, limite de uso, falta de crédito, serviço indisponível, timeout, falha de comunicação |
| `test_resposta.py` | resposta vazia, recusada, truncada ou em formato inesperado |
| `test_parametros.py` | parâmetros pelo TOML e pelo ambiente, prioridade, valores inválidos, parâmetros opcionais na solicitação |
| `test_registro.py` | log com dados úteis e sem chave, pergunta, trecho, resposta ou caminho; falha ao gravar o log |
| `test_fluxo.py` | fluxo completo, código de saída 1 e mensagens sem traceback |

## 1.1 Testes reais automatizados (opcionais)

Executar com `python -m pytest -m real`. Chamam a OpenAI de verdade (3 chamadas, custo
mínimo): resposta com citação, resposta "não encontrei" e credencial inexistente recusada
pelo serviço. Resultado em 15/11/2026: 3 passaram em 134 s no total. Uma chamada isolada, medida depois pelo registro, levou 3,6 s; a causa dos 134 s não foi investigada.

## 2. Testes manuais com a API real (execução por linha de comando)

Executados em 15/11/2026, na branch `openai`, com o modelo padrão (`gpt-5.6-terra`).
Cada resposta foi conferida contra o texto do ROD (Resolução Consup nº 35/2015).

Comando base: `python src/rod_assistente.py <arquivo> "<pergunta>"`

| # | Tipo | Arquivo | Pergunta | Resultado esperado | Resultado obtido | Passou? |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Sucesso | `rod_avaliacao.txt` | Qual a média mínima para aprovação direta na graduação? | MP igual ou superior a 7,0 e frequência de 75% (Art. 99) | MP mínima de 7,0 e frequência de 75%, citando o Art. 99, II | Sim |
| M2 | Sucesso | `rod_avaliacao.txt` | Como se calcula a média parcial? | MP = (2 x N1 + 3 x N2) / 5 (Art. 98) | Fórmula correta, com pesos 2 e 3, citando os Arts. 97 (§ 1º) e 98 | Sim |
| M3 | Sucesso (duas passagens) | `rod_avaliacao.txt` | Tirei MP 5,6. O que acontece? | Faz avaliação final; MF = (MP + AF) / 2; aprovação com MF de 5,0 ou mais (Art. 100) | Respondeu para curso técnico e para graduação: avaliação final, MF = (MP + AF) / 2 e aprovação com MF de 5,0 ou mais. Citou o Art. 100 e o § 4º, mas não o § 5º | Sim, com ressalva |
| M4 | Sucesso | `rod_segunda_chamada.txt` | Em quanto tempo posso pedir segunda chamada? | Até 5 dias letivos após a primeira (Art. 110) | Até 5 dias letivos após a primeira avaliação, citando o Art. 110 | Sim |
| M5 | Sucesso | `rod_trancamento.txt` | Quando posso trancar uma disciplina? | Nos primeiros 30 dias, mantendo 12 créditos, fora do 1º período (Art. 155) | Primeiros 30 dias, mínimo de 12 créditos, fora do 1º período, sem reprovação na disciplina e por requerimento à coordenação. Citou o Art. 155 e os §§ 1º a 4º | Sim |
| M6 | Falha esperada | `rod_avaliacao.txt` | Qual o valor da bolsa de monitoria? | "Não encontrei essa informação no trecho fornecido." | "Não encontrei essa informação no trecho fornecido." | Sim |
| M7 | Falha esperada | `nao_existe.txt` | Qualquer pergunta | Mensagem "Arquivo não encontrado" e código de saída 1 | Validado em teste automatizado | Sim |
| M8 | Falha esperada | `rod_avaliacao.txt` | (chave removida do `.env`) | Mensagem "Credencial ausente" | Validado em teste simulado e visto na prática (versão do marco Básico) | Sim |
| M9 | Falha esperada | `rod_avaliacao.txt` | (chave que não começa com `sk-`) | Mensagem "Credencial inválida ou sem permissão" | Mensagem exibida, sem traceback | Sim |

Observações:

- **M3:** a pergunta não dizia o tipo de curso, e o modelo cobriu os dois casos do Art. 100. A resposta está correta, mas o § 5º, que fixa a média final de 5,0, só aparece de forma indireta.
- **Acentos no terminal do Windows:** ao redirecionar a saída no PowerShell, os acentos podem aparecer trocados (por exemplo, `mÚdia`). É um problema de codificação do terminal, e o texto devolvido pelo programa está correto. Para evitar, rode `$env:PYTHONUTF8 = "1"` antes de executar.
