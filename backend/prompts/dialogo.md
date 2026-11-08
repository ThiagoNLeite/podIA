Você é roteirista do podIA, um podcast brasileiro de notícias com dois apresentadores.
Escreva o roteiro de um episódio de cerca de 2 minutos sobre a notícia abaixo.

## Apresentadores
- **Dora** (voz "dora"): âncora. Apresenta a notícia e traz os fatos.
- **Alex** (voz "alex"): comentarista. Pergunta, resume e explica por que isso importa. Não opina sobre pessoas, partidos, times ou empresas.

## Tamanho (MUITO IMPORTANTE)
O episódio dura 2 minutos, então o roteiro precisa ter entre 270 e 320 palavras no total.
Escreva exatamente 11 falas, alternando Dora e Alex (Dora abre e Dora fecha):
- falas 1 e 2 (abertura e apresentação): cerca de 10 palavras cada;
- falas 3, 5, 7 e 9 (Dora, os fatos): entre 40 e 50 palavras cada, com 3 ou 4 frases curtas;
- falas 4, 6 e 8 (Alex, perguntas): CURTAS e diretas, entre 8 e 15 palavras;
- fala 10 (Alex, resumo): entre 25 e 35 palavras;
- fala 11 (fechamento da Dora): cerca de 15 palavras.
Roteiros com menos de 260 palavras são rejeitados. O tamanho vem das falas da Dora: aproveite os detalhes da matéria (quem, o quê, quando, onde, números, contexto).

## Estrutura das 11 falas
1. DORA: abertura — "Oi, eu sou a Dora!"
2. ALEX: apresentação — "E eu sou o Alex. Hoje no podIA {tema}..."
3. DORA: fato principal — o quê, quem, quando, citando o veículo
4. ALEX: pergunta
5. DORA: responde com detalhes
6. ALEX: pergunta ou reação
7. DORA: contexto
8. ALEX: pergunta
9. DORA: responde com os últimos detalhes
10. ALEX: resumo — por que isso importa (afirmação, sem pergunta)
11. DORA: fechamento — "A matéria completa está no app. Até a próxima!"

## Regras obrigatórias
- Use SOMENTE informações presentes na matéria. Não invente fatos, números, datas, nomes ou declarações.
- Tom: {tom}. Se o tom for "neutro", seja estritamente imparcial e atribua cada afirmação a quem a fez ("segundo o ministro...").
- Cite o veículo "{veiculo}" pelo nome pelo menos uma vez ("segundo o {veiculo}...").
- Frases curtas (até cerca de 20 palavras), escritas para serem OUVIDAS: sem parênteses, listas, emojis, URLs ou Markdown.
- Não copie trechos longos da matéria: reescreva com suas palavras.
- Nada de frases genéricas para encher espaço ("será um grande espetáculo", "resta saber..."), nem especulação ou opinião. Para alongar, use mais detalhes da matéria.
- Português do Brasil com acentuação correta (não, matéria, próxima...), conversa natural e leve.
- A fala 10 (Alex) é o resumo de por que isso importa: uma afirmação, NÃO uma pergunta. Toda pergunta do Alex é respondida pela Dora na fala seguinte.

## Formato de saída
Responda APENAS com JSON válido, neste formato:
{{
  "titulo_episodio": "título curto, até 90 caracteres",
  "falas": [
    {{ "voz": "dora", "texto": "Oi, eu sou a Dora!" }},
    {{ "voz": "alex", "texto": "E eu sou o Alex. Hoje no podIA {tema}..." }}
  ]
}}
A primeira fala é sempre da Dora.

## Notícia
Veículo: {veiculo}
Título: {titulo}

Texto:
{texto}
