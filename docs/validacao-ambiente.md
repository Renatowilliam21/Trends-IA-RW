# Validação em ambiente limpo

Objetivo: confirmar que uma pessoa que não participou do projeto consegue clonar, instalar,
configurar e executar usando apenas o README.

## Validação 1: Linux, clone novo e ambiente virtual novo (15/11/2026)

Executada por Claude (assistente de IA usado no desenvolvimento), seguindo o README passo a
passo em duas versões do Python. Cada rodada usou um `git clone` novo e um `python -m venv`
novo, sem reaproveitar nada do ambiente de desenvolvimento.

| Passo do README | Python 3.11.18 | Python 3.13.18 |
| --- | --- | --- |
| `git clone` + `python3 -m venv .venv` + `pip install -r requirements.txt` | OK | OK |
| `python -m pytest` | 73 passaram | 73 passaram |
| Executar sem `.env` | "Credencial ausente", código 1 | igual |
| `.env` copiado do exemplo, chave vazia | "Credencial ausente", código 1 | igual |
| Chave `key_abc` (formato errado) | "não tem o formato esperado", código 1 | igual |
| Chave `sk-` falsa, sem acesso à rede | "Sem conexão com o serviço", código 1 | igual |
| Log gerado em `logs/assistente.log` | linhas de início, conexão e falha, sem a chave | igual |

**Limite desta validação:** o ambiente de teste não tem acesso à API da OpenAI nem chave
real. Por isso a chamada real não foi exercitada aqui. Ela foi validada no computador do
autor (Windows), conforme `docs/testes.md`.

### Problema encontrado e correção

- **O que aconteceu:** com a credencial ausente, o terminal mostrava uma linha solta,
  `falha tipo=ErroConfiguracao`, antes da mensagem de erro esperada. O registro ainda não
  estava configurado quando o erro ocorreu, e o Python imprimiu o aviso por conta própria.
- **Por que os testes não pegaram:** o pytest captura os logs, o que esconde esse efeito.
- **Correção:** um handler nulo no logger do projeto (`src/registro.py`) e um teste novo que
  executa o programa em processo separado e confere que a saída de erro tem uma única linha
  (`test_programa_real_sem_credencial_mostra_so_a_mensagem_de_erro`). O teste foi conferido:
  falha sem a correção e passa com ela.
- **Commit:** `fix: evita linha de log solta no terminal quando a configuracao falha`.

## Validação 2: Windows, ambiente novo, pelo autor

Para executar no computador do autor, em uma pasta nova, usando só o README:

```powershell
cd $HOME\Documents
git clone https://github.com/Renatowilliam21/Trends-IA-RW.git validacao-limpa
cd validacao-limpa
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
copy .env.example .env
notepad .env
python src\rod_assistente.py dados\rod_avaliacao.txt "Qual a média mínima para aprovação direta na graduação?"
```

Resultado em 15/11/2026, Windows, Python 3.14.3, pasta nova `validacao-limpa`:

| Passo | Resultado |
| --- | --- |
| `git clone`, `python -m venv`, `pip install -r requirements.txt` | OK |
| `python -m pytest` | 74 passaram |
| Pergunta real sobre a média mínima (chave `sk-` válida) | Resposta correta: 7,0 e frequência de 75%, citando o Art. 99, II |
| `logs\assistente.log` | 3 linhas: início, `status=200 latencia_ms=3645` e sucesso com `total_tokens=776`. Sem chave e sem o texto da pergunta |

### Dificuldade encontrada e ajuste

- **O que aconteceu:** na primeira tentativa o programa respondeu "Credencial ausente" e a
  pasta `logs` não existia. A chave ainda não tinha sido preenchida no `.env` (o arquivo
  copiado do exemplo vem com `OPENAI_API_KEY=` vazio). O comportamento do programa estava
  correto, e a mensagem foi clara, mas o README não deixava explícito que o log só é criado
  depois que a configuração é aceita.
- **Ajuste:** o README ganhou uma observação sobre esses dois pontos (README, seção
  Configuração).
- **Nota sobre tempo:** a chamada isolada levou 3,6 s. No registro dos testes reais, o total
  de 134 s para 3 chamadas não foi investigado. Não se deve atribuí-lo ao modelo sem medir.

## Validação 3: outra pessoa

Opcional e recomendada: pedir a um colega que siga apenas o README e anotar aqui as
dificuldades que ele relatar.
