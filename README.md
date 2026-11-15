# Assistente do ROD (P0 Primeiro fluxo com LLM)

Aplicação de linha de comando em Python que responde perguntas sobre um trecho do
Regulamento da Organização Didática (ROD) do IFCE, citando o artigo de origem. Se a
resposta não estiver no trecho, ela diz que não encontrou, em vez de inventar.

**Problema em uma frase:** estudantes e servidores têm dificuldade para localizar regras
em documentos institucionais longos.

## Requisitos

- Python 3.10 ou superior
- Uma chave de API do Gemini, gerada no Google AI Studio (https://aistudio.google.com/apikey)

## Instalação

```bash
git clone https://github.com/Renatowilliam21/Trends-IA-RW.git
cd Trends-IA-RW
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
```

Abra o `.env` e preencha `GEMINI_API_KEY` com a sua chave. Opcionalmente, defina `GEMINI_MODEL` para trocar o modelo (padrão: `gemini-3.5-flash-lite`). Os nomes de modelos do Gemini mudam com frequência; se aparecer "Modelo não encontrado", consulte a lista atual na documentação do Gemini API. O arquivo `.env` está no
`.gitignore` e não deve ser enviado ao GitHub.

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

## Testes

```bash
python -m pytest
```

Os testes usam a API simulada e não precisam de chave. Os casos executados com a API real
estão em `docs/testes.md`.

## Documentação

- `docs/testes.md`: casos de sucesso e de falha
- `docs/decisoes.md`: principais decisões de projeto
- `docs/uso-de-ia.md`: como ferramentas de IA foram usadas no desenvolvimento

## Limitações

- O trecho inteiro vai no prompt. Não há busca em vários documentos.
- Respostas de LLM podem errar. Confira sempre o artigo citado no texto original.
- O ROD usado é o de 2015 (Resolução Consup nº 35). Verifique se continua em vigor.
