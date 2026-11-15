# Registro de testes

## 1. Testes automatizados (API simulada)

Executar com `python -m pytest`. Resultado na criação deste documento: 18 testes
passando. Cobrem 3 casos de sucesso e 15 de falha (entrada, arquivo, chave, HTTP,
rede e formato da resposta).

## 2. Testes manuais com a API real

Preencha a coluna "Resultado obtido" depois de executar cada comando e confira a
resposta contra o ROD.

Comando base: `python src/rod_assistente.py <arquivo> "<pergunta>"`

| # | Tipo | Arquivo | Pergunta | Resultado esperado | Resultado obtido | Passou? |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Sucesso | `rod_avaliacao.txt` | Qual a média mínima para aprovação direta na graduação? | MP igual ou superior a 7,0 e frequência de 75% (Art. 99) | A preencher | |
| M2 | Sucesso | `rod_avaliacao.txt` | Como se calcula a média parcial? | MP = (2 x N1 + 3 x N2) / 5 (Art. 98) | A preencher | |
| M3 | Sucesso (duas passagens) | `rod_avaliacao.txt` | Tirei MP 5,6. O que acontece? | Faz avaliação final; MF = (MP + AF) / 2; aprovação com MF de 5,0 ou mais (Art. 100) | A preencher | |
| M4 | Sucesso | `rod_segunda_chamada.txt` | Em quanto tempo posso pedir segunda chamada? | Até 5 dias letivos após a primeira (Art. 110) | A preencher | |
| M5 | Sucesso | `rod_trancamento.txt` | Quando posso trancar uma disciplina? | Nos primeiros 30 dias, mantendo 12 créditos, fora do 1º período (Art. 155) | A preencher | |
| M6 | Falha esperada | `rod_avaliacao.txt` | Qual o valor da bolsa de monitoria? | "Não encontrei essa informação no trecho fornecido." | A preencher | |
| M7 | Falha esperada | `nao_existe.txt` | Qualquer pergunta | Mensagem "Arquivo não encontrado" e código de saída 1 | Validado em teste automatizado | Sim |
| M8 | Falha esperada | `rod_avaliacao.txt` | (chave removida do `.env`) | Mensagem "Chave de acesso ausente" | Validado em teste automatizado | Sim |
