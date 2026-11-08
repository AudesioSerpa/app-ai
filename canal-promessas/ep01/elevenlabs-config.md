# Episódio 01 — Configuração do ElevenLabs

## Arquivos para gerar
A narração está dividida em **13 blocos**, na pasta `narracao/`. Gere **um áudio por bloco** e salve com o mesmo nome:

| Bloco | Parte | Palavras | Caracteres |
|---|---|---|---|
| bloco-01 | Gancho | 241 | 1.449 |
| bloco-02 | Oração de bênção | 274 | 1.551 |
| bloco-03 | Apresentação | 89 | 576 |
| bloco-04 | O mundo da época: Filipos | 440 | 2.712 |
| bloco-05 | Paulo chega e Lídia | 475 | 2.785 |
| bloco-06 | A escrava, a prisão e o carcereiro + pedido de inscrição | 578 | 3.515 |
| bloco-07 | A igreja que dava do que faltava | 425 | 2.633 |
| bloco-08 | Paulo preso em Roma e Epafrodito | 435 | 2.688 |
| bloco-09 | A carta e a promessa | 385 | 2.425 |
| bloco-10 | O significado e o detalhe escondido | 443 | 2.640 |
| bloco-11 | As quatro atitudes | 531 | 3.269 |
| bloco-12 | Oração final | 280 | 1.677 |
| bloco-13 | Encerramento | 261 | 1.534 |
| **Total** | | **4.857** | **~29.500** |

**Duração estimada:** de 34 a 38 minutos de áudio (depende da voz e da velocidade). Com as pausas entre blocos, o vídeo passa de 35 minutos.

Salve os áudios como `bloco-01.mp3`, `bloco-02.mp3`… e me envie todos. Eu monto o vídeo encaixando cada bloco nas suas cenas.

---

## Configuração (Eleven Multilingual v2)

| Opção | Valor | Por quê |
|---|---|---|
| **Modelo** | Eleven Multilingual v2 | Melhor qualidade em português e aceita a tag de pausa |
| **Voz** | Narrador em português do Brasil, grave e acolhedor | Use **sempre a mesma voz** nos 13 blocos |
| **Velocidade (Speed)** | **0,92** (entre 0,90 e 0,95) | Ritmo calmo de documentário, bom para a TV |
| **Stability** | **50%** (entre 45% e 55%) | Abaixo de 40% a voz varia demais; acima de 65% fica robótica |
| **Similarity** | **75%** | Fiel à voz sem gerar chiado |
| **Style Exaggeration** | **0% a 10%** | Valores altos deixam a voz instável em textos longos |
| **Speaker Boost** | **Ligado** | Voz mais presente, clara acima da música |
| **Formato de saída** | MP3 44,1 kHz 192 kbps (ou WAV, se o seu plano permitir) | Qualidade para a TV |

**Importante:** depois de acertar a configuração no bloco 1, **não mexa mais** até terminar o bloco 13. Assim a voz fica igual no vídeo inteiro.

---

## Pausas

O texto já vem com as pausas marcadas assim:

```
<break time="1.5s" />
```

- O Multilingual v2 **lê essa tag como silêncio**. Ela não é falada.
- Pausas de **1,0 s**: respiro entre ideias.
- Pausas de **1,5 s**: depois de uma pergunta ao espectador ou de uma cena forte.
- Pausas de **2,0 a 2,5 s**: antes e depois do versículo principal, e nas orações.
- O máximo aceito é **3 segundos** por tag. Pausas maiores (entre blocos e na vinheta) eu coloco na edição.
- As **reticências (...)** e os **pontos finais** também criam pausas naturais. Por isso o texto tem frases curtas.

### Se algo der errado
- **A voz acelerou ou ficou estranha depois de uma pausa:** gere o bloco de novo. Se continuar, troque a tag por reticências (`...`).
- **A voz leu "break" em voz alta:** você não está no Multilingual v2. Confira o modelo.
- **Está usando o Eleven v3?** O v3 **não aceita** a tag `<break>`. Apague as tags e deixe só as reticências, ou use as tags de áudio do v3 (por exemplo `[pause]`).
- **Uma frase saiu sem emoção:** gere de novo só aquele bloco. Cada geração tem uma pequena variação.

---

## Pronúncia: já preparada no texto
- Os **números estão escritos por extenso** ("ano cinquenta", "quarenta e dois antes de Cristo") para a IA não ler errado.
- A referência está escrita como **"Filipenses, capítulo quatro, versículo dezenove"**, em vez de "4:19".
- A palavra grega está escrita do jeito que se fala: **"pleróo"**.
- Nomes que vale conferir no primeiro áudio: **Epafrodito, Tiatira, Trôade, Neápolis, Samotrácia, Via Egnácia, Luciano de Samósata**. Se algum sair errado, use o dicionário de pronúncia do ElevenLabs ou escreva o nome do jeito que se fala.

---

## Conferência antes de me enviar
- [ ] Os 13 blocos com a mesma voz e a mesma configuração
- [ ] Nenhuma tag lida em voz alta
- [ ] O versículo principal (bloco 09) com a pausa antes e depois
- [ ] Os nomes próprios pronunciados corretamente
- [ ] Os arquivos nomeados de `bloco-01` a `bloco-13`
