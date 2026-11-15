# Uso de ferramentas de IA no desenvolvimento

**Ferramenta:** Claude (Anthropic), em conversa de chat com acesso a terminal.

**Quem fez o quê.** Esta é a implementação de referência do P0, preparada pelo professor
com apoio do Claude. O professor definiu o problema, o recorte do escopo e os requisitos.
O Claude escreveu o código, os testes e a documentação a partir dessas instruções.

**Etapas em que a IA foi usada**

1. Redação do primeiro script (marco Básico).
2. Refatoração em funções e escrita do tratamento de erros e dos testes (marco
   Intermediário).
3. Redação do README e dos documentos em `docs/` (marco Avançado).
4. Extração dos trechos do ROD a partir do PDF.

**O que precisou de correção.** A extração de texto do PDF perdeu o denominador das duas
fórmulas do regulamento (MP e MF). O texto ficou truncado e foi reescrito
manualmente como `MP = (2 x N1 + 3 x N2) / 5` e `MF = (MP + AF) / 2`, conferindo com o
PDF original.

**O que foi validado sem a IA.** Os testes automatizados rodam com a API simulada. As
execuções com a API real devem ser feitas e registradas por quem assina o projeto, e as
respostas devem ser conferidas contra o texto do ROD.

**Limite desta declaração.** Os resultados com a API real ainda precisam ser conferidos
pelo autor antes da entrega a estudantes. Substitua este texto pela sua declaração caso
use o projeto como entrega própria.
