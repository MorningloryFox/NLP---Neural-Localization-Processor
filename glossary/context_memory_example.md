# Exemplo de context_memory.txt com Extração Estruturada

Este arquivo é gerado automaticamente por `extract_key_points()` após cada capítulo traduzido.

## Estrutura do Arquivo

Cada seção de capítulo é separada por `---` e contém 3 blocos de informação:

```
[PERSONAGENS]
- Nome (Gênero): Descrição/Papel

[CENÁRIO/TEMPO]
Mudanças de local, períodos ou saltos significativos

[ITENS]
- Nome do Item: Descrição/Relevância
```

## Exemplo Real

### Capítulo 1

---
[PERSONAGENS]
- Tanjiro (Masculino): Protagonista, vendedor de carvão que descobre poder demoníaco
- Nezuko (Feminino): Irmã transformada em demônio, mas retém humanidade
- Giyu Tomioka (Masculino): Espadachim misterioso que treina Tanjiro

[CENÁRIO/TEMPO]
Mudança: Vilarejo montanhoso → Floresta noturna (mesma noite)
Período: Era Taisho, noite de lua cheia

[ITENS]
- Katana de Agua (Hinokami Kagura): Técnica de respiração única para Tanjiro
- Máquina de Carvão: Fornecimento familiar (motivo de ser vendedor)

---

### Capítulo 2

---
[PERSONAGENS]
- Sakonji Urokodaki (Masculino): Treinador de Tanjiro, ex-samurai aposentado
- Zenitsu (Masculino): Garoto covarde com habilidade de respiração do trovão
- Inosuke (Masculino): Guerreiro selvagem e agressivo

[CENÁRIO/TEMPO]
Mudança: Floresta → Montanha de Treinamento (2 anos depois)
Período: Era Taisho, primavera do 3º ano

[ITENS]
- Técnica de Respiração da Água: Treino intenso por 2 anos
- Demônios de Treinamento: Derrotas sucessivas contra oponentes fracos

---

### Capítulo 3

---
[PERSONAGENS]
- Kanao Tsuyuri (Feminino): Garota silenciosa com olhos reflexivos
- Shinobu Kocho (Feminino): Guerreira elegante, especialista em veneno
- Giyu Tomioka (Masculino): Reaparece com nova informação crítica

[CENÁRIO/TEMPO]
Mudança: Montanha → Primeira Vila Demoniaca (noite)
Período: Era Taisho, outono (6 meses depois do treinamento)

[ITENS]
- Katana de Aço Vermelho: Arma forjada especialmente para derrotar demônios
- Corpo de Demônio de Nível Superior: Primeira batalha real contra inimigo poderoso

---

## Como o Modelo (Gemini Pro) Usa Isso

Quando `context_memory.txt` é lido e passado como contexto para o próximo capítulo:

```
Contexto anterior:
---
[PERSONAGENS]
- Tanjiro (Masculino): Protagonista, vendedor de carvão que descobre poder demoníaco
- Nezuko (Feminino): Irmã transformada em demônio, mas retém humanidade
...
[CENÁRIO/TEMPO]
...
[ITENS]
...
---

[Texto do próximo capítulo aqui]
```

O modelo pode então:
1. **Manter coerência de gênero**: Sabe que Nezuko é Feminino, Tanjiro é Masculino
2. **Evitar confusão de cenários**: Sabe que saiu da montanha na cap anterior
3. **Referenciar itens corretamente**: Sabe que Tanjiro adquiriu a Katana de Aço Vermelho
4. **Manter consistência de personagens**: Evita "regenerar" nomes ou papéis

## Benefício Real

Sem extração estruturada:
> "No capítulo anterior, alguém derrotou um demônio"
> (vago, pode confundir gênero, evento, item conquistado)

Com extração estruturada:
> "[PERSONAGENS] Tanjiro (Masculino): Derrota demônios com espada"
> "[ITENS] - Katana de Aço Vermelho: Usada para derrotar demônios de nível superior"
> (claro, específico, impossível confundir)

## Versões Futuras

Possíveis melhorias:
- [ ] Adicionar coluna "Relacionamentos" (ex: "Tanjiro confia em Giyu")
- [ ] Detectar arcos narrativos ("Arco do Treinamento", "Arco da Missão")
- [ ] Pré-processar com NLP para extração de Named Entities (NER)
- [ ] Sumarização automática de 5+ capítulos em uma visão geral
