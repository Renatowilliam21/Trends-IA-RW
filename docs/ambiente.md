# Ambiente: versões do Python e das bibliotecas

## Python

| Item | Versão |
| --- | --- |
| Mínima exigida | 3.11 (o código usa `tomllib`, que entrou na biblioteca padrão nessa versão) |
| Testada no Windows (máquina do autor) | 3.14.3 |
| Testada em Linux, ambiente limpo | 3.11.18 e 3.13.18 |

## Bibliotecas

Declaradas em `requirements.txt` com faixas de versão. Versões instaladas nos ambientes
limpos de validação (Linux, `pip install -r requirements.txt` em 15/11/2026):

| Biblioteca | Faixa declarada | Instalada na validação | Uso |
| --- | --- | --- | --- |
| requests | `>=2.31,<3` | 2.34.2 | chamada HTTP à API da OpenAI |
| python-dotenv | `>=1.0,<2` | 1.2.4 | leitura do arquivo `.env` |
| pytest | `>=8.0,<10` | 9.2.0 | testes automatizados |

Dependências indiretas instaladas junto com o `requests`: urllib3 2.8.0, certifi 2026.10.23,
charset-normalizer 3.5.2 e idna 3.20.

Não há SDK da OpenAI: a chamada é feita por REST, com `requests`.

## Serviço externo

API Chat Completions da OpenAI (`https://api.openai.com/v1/chat/completions`). O modelo
padrão é `gpt-5.6-terra` e pode ser trocado em `configuracao.toml`. Nomes de modelos mudam
com frequência; confira a lista atual na documentação da OpenAI.

## Como registrar as versões do seu ambiente

```bash
python --version
pip freeze
```
