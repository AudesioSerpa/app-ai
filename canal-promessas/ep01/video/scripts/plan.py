"""Plano de cenas do episódio 01.

Cada cena começa no momento em que a narração diz a frase-âncora (anchor).
kind:
  img  -> foto real do Wikimedia Commons (queries tentadas em ordem)
  vid  -> vídeo real do Wikimedia Commons
  map:NOME -> mapa animado desenhado no Remotion
  fx:NOME  -> peça gráfica (texto/animação) desenhada no Remotion
Overlays (referências, lugares, títulos) ficam em OVERLAYS.
"""

S = []  # (bloco, anchor, kind, queries)


def sc(b, anchor, kind, *queries):
    S.append({"block": b, "anchor": anchor, "kind": kind, "queries": list(queries)})


# ---------- BLOCO 01 — Gancho ----------
sc(1, "Talvez você esteja assistindo", "img", "bills invoices paper desk", "paper money coins table")
sc(1, "Uma conta que já venceu", "img", "Brazilian real banknotes coins", "coins in hand")
sc(1, "Talvez você trabalhe o mês inteiro", "img", "city at night window lights", "night city skyline lights")
sc(1, "Eu quero que você saiba", "vid", "sunrise timelapse", "clouds timelapse sky")
sc(1, "Existe uma frase na Bíblia", "img", "Papyrus 46", "Chester Beatty papyrus Pauline epistles")
sc(1, "Essa frase não foi escrita num palácio", "img", "Palatine Hill palace ruins Rome", "Domus Augustana")
sc(1, "Ela foi escrita por um homem preso", "img", "Roman iron shackles chains ancient", "ancient iron chains museum")
sc(1, "Hoje você vai conhecer essa história", "img", "Via Egnatia Philippi road", "Via Egnatia")
sc(1, "Vai conhecer uma empresária", "img", "Tyrian purple dyed wool", "murex purple dye")
sc(1, "e um mensageiro que quase morreu", "img", "Roman road landscape Greece", "ancient Roman road stones")
sc(1, "E no final, eu vou te mostrar", "img", "Codex Sinaiticus Philippians", "Greek New Testament manuscript")
sc(1, "Mas antes de começar", "vid", "candle flame", "candle burning dark")

# ---------- BLOCO 02 — Oração de bênção ----------
sc(2, "Se você puder, para um instante", "vid", "sunrise over field timelapse", "sunrise timelapse")
sc(2, "Fecha os olhos, se puder", "img", "praying hands", "hands folded prayer")
sc(2, "Tu conheces o nome dela", "img", "family dinner table home", "family meal table")
sc(2, "Senhor, eu Te peço pela pessoa que está desempregada", "img", "job seekers queue employment office", "office worker desk paperwork")
sc(2, "Eu Te peço pela pessoa que trabalha muito", "img", "construction worker hands", "worker hands tools")
sc(2, "Eu Te peço pela mãe e pelo pai", "img", "bread loaves on table", "fresh bread")
sc(2, "Tu és o Deus que alimentou", "img", "Sinai desert landscape", "Negev desert")
sc(2, "Eu Te peço por quem está endividado", "img", "man sitting alone bench thinking", "lonely man window")
sc(2, "Abençoa o trabalho das mãos", "img", "street market vendor fruits stall", "small shop owner")
sc(2, "E, acima de tudo, Pai", "vid", "sun rays through clouds", "clouds timelapse sunset")
sc(2, "Agora... eu quero te levar", "img", "Philippi archaeological site panorama", "Philippi Greece ruins")

# ---------- BLOCO 03 — Apresentação ----------
sc(3, "Neste documentário", "img", "open Bible old", "old Bible open pages")
sc(3, "Segundo: o que aquelas pessoas fizeram", "img", "Philippi basilica ruins", "Philippi Basilica B")
sc(3, "Então se acomoda aí", "img", "cup of coffee table morning", "coffee cup")
sc(3, "Este é o primeiro episódio", "fx:titulo-serie")

# ---------- BLOCO 04 — O mundo da época ----------
sc(4, "Vamos voltar no tempo", "map:macedonia")
sc(4, "Imagine uma estrada larga", "img", "Via Egnatia Kavala stones", "Via Egnatia ruts")
sc(4, "Por ela passam soldados", "img", "Roman legionary reenactment", "Roman soldiers reenactment")
sc(4, "E no caminho dessa estrada", "img", "Philippi theatre", "Ancient theatre of Philippi")
sc(4, "O nome vem de Filipe", "img", "Philip II of Macedon gold stater coin", "Philip II of Macedon")
sc(4, "que era cobiçada por causa das minas de ouro", "img", "Mount Pangaion", "Pangaion Hills")
sc(4, "Você percebe? Desde o começo", "img", "ancient gold coins hoard", "gold stater coins")
sc(4, "Séculos depois, nos campos ao redor", "img", "plain of Philippi landscape", "Drama plain Greece")
sc(4, "No ano quarenta e dois antes de Cristo", "img", "Augustus of Prima Porta", "Augustus bust")
sc(4, "Depois da vitória, Roma transformou Filipos", "img", "Philippi forum ruins", "Roman forum Philippi")
sc(4, "Ser uma colônia romana era um privilégio", "img", "Latin inscription Philippi", "Roman inscription stone Latin")
sc(4, "As autoridades andavam acompanhadas", "img", "fasces lictors relief", "lictors relief")
sc(4, "O livro de Atos dos Apóstolos registra", "img", "Philippi archaeological site", "Philippi ruins columns")
sc(4, "Agora, para um pouco e pensa comigo", "img", "Roman slaves relief", "ancient Roman relief workers")
sc(4, "Talvez você saiba bem o que é isso", "img", "crowded street people walking city", "people crowd street")
sc(4, "E havia mais um detalhe importante", "img", "ancient synagogue ruins", "Sardis synagogue")
sc(4, "O que havia era um lugar de oração", "vid", "river flowing water", "stream flowing forest")
sc(4, "Guarda esse rio na memória", "img", "Zygaktis river Philippi", "Krenides river")

# ---------- BLOCO 05 — Paulo chega e Lídia ----------
sc(5, "Mas como Paulo foi parar em Filipos", "img", "Saint Paul icon", "Apostle Paul painting")
sc(5, "E as portas iam se fechando", "img", "old wooden door closed", "ancient door")
sc(5, "Foi assim com Paulo. Até que eles chegaram a Trôade", "img", "Alexandria Troas ruins", "Alexandria Troas")
sc(5, "Um homem da Macedônia estava de pé", "img", "Vision of Saint Paul Macedonian", "Paul vision Macedonia")
sc(5, "Eles não discutiram", "map:troade-filipos")
sc(5, "Ficaram alguns dias na cidade", "img", "Philippi ruins sunset", "Philippi archaeological site")
sc(5, "Ali encontraram algumas mulheres reunidas", "vid", "river water flowing", "creek flowing")
sc(5, "E uma delas se chamava Lídia", "img", "Lydia baptistery Philippi", "Baptistery of Lydia")
sc(5, "Lídia não era de Filipos", "img", "Thyatira ruins Akhisar", "Akhisar Thyatira")
sc(5, "Para você entender o que isso significa", "img", "murex shells", "Bolinus brandaris shells")
sc(5, "O corante era tão valioso", "img", "purple silk fabric", "Tyrian purple fabric")
sc(5, "Lídia era, como a gente diria hoje", "img", "Roman merchant relief", "ancient Roman shop relief")
sc(5, "Paulo começou a falar sobre Jesus", "img", "Saint Lydia icon", "Lydia of Thyatira")
sc(5, "E então ela fez uma coisa", "img", "Roman house atrium", "Roman villa atrium")
sc(5, "Repara nisso. A primeira coisa", "img", "ancient Roman table bread fresco", "Roman fresco bread")
sc(5, "Guarda essa imagem", "img", "Roman villa mosaic floor", "Roman mosaic")

# ---------- BLOCO 06 — A serva, a prisão e o carcereiro ----------
sc(6, "Mas nem todo mundo em Filipos", "img", "Philippi agora ruins", "Philippi market ruins")
sc(6, "Havia na cidade uma serva", "img", "Pythia Delphi", "ancient Greek oracle painting")
sc(6, "Durante muitos dias, ela seguiu Paulo", "img", "Paul exorcism Philippi", "Saint Paul Philippi painting")
sc(6, "Agora presta atenção na reação", "img", "Roman denarius coins", "Roman silver coins")
sc(6, "Eles agarraram Paulo e Silas", "img", "Philippi forum", "Roman forum ruins")
sc(6, "A multidão se levantou contra eles", "img", "Paul and Silas beaten Philippi", "Paul and Silas")
sc(6, "Imagina essa cena", "img", "dark dungeon stone", "prison cell stone ancient")
sc(6, "Eu sei o que muita gente faria", "img", "Paul and Silas in prison", "Paul Silas prison painting")
sc(6, "De repente, um grande terremoto", "img", "fallen columns earthquake ruins", "toppled columns ruins")
sc(6, "O carcereiro acordou", "img", "Paul and Silas jailer", "conversion of the jailer Philippi")
sc(6, "Naquela mesma madrugada", "img", "ancient baptismal font", "early christian baptistery")
sc(6, "Agora olha quem fazia parte", "img", "early Christian fresco catacomb meal", "agape feast fresco")
sc(6, "No dia seguinte, Paulo e Silas foram soltos", "img", "Philippi ruins morning", "Philippi Greece")
sc(6, "E antes de continuar, um pedido rápido", "img", "Philippi landscape", "Kavala Greece landscape")

# ---------- BLOCO 07 — A igreja que dava do que faltava ----------
sc(7, "Paulo saiu de Filipos", "map:filipos-corinto")
sc(7, "Lá, ele começou a pregar de novo", "img", "Roman Forum Thessaloniki", "Ancient Agora Thessaloniki")
sc(7, "E, para não ser peso para ninguém", "img", "leather craftsman tools", "leatherworking hands")
sc(7, "Mas Paulo não estava sozinho", "img", "ancient Roman purse coins", "leather pouch coins")
sc(7, "Uma e outra vez", "img", "old letter scroll", "papyrus letter ancient")
sc(7, "E quando Paulo seguiu viagem e chegou a Corinto", "img", "Temple of Apollo Corinth", "Ancient Corinth")
sc(7, "Agora... você pode estar pensando", "img", "Macedonia village Greece old houses", "Greek village stone houses")
sc(7, "Anos depois, quando Paulo organizou uma oferta", "img", "Jerusalem old city", "Jerusalem view")
sc(7, "Profunda pobreza", "img", "old wrinkled hands", "elderly hands")
sc(7, "Para um pouco e pensa nisso", "img", "hands giving coins", "giving hands")
sc(7, "Essa não era uma igreja que dava do que sobrava", "img", "barley bread loaves", "rustic bread")
sc(7, "Talvez agora você esteja se perguntando", "img", "sunset over fields Greece", "wheat field sunset")

# ---------- BLOCO 08 — Paulo preso em Roma e Epafrodito ----------
sc(8, "Passam-se cerca de dez anos", "map:jerusalem-roma")
sc(8, "Enfrentou um naufrágio", "img", "Shipwreck of Saint Paul painting", "Saint Paul shipwreck Malta")
sc(8, "O livro de Atos conta que, em Roma", "img", "Roman insula Ostia", "Ostia Antica insula")
sc(8, "Agora pensa na situação", "img", "Roman soldier relief", "Trajan column soldiers")
sc(8, "E no mundo romano, o preso", "img", "Roman bread loaf Pompeii", "carbonized bread Pompeii")
sc(8, "E ainda havia o aluguel", "img", "Roman street Pompeii", "Pompeii street")
sc(8, "E lá em Filipos, a notícia chegou", "img", "oil lamp ancient Roman", "Roman oil lamp")
sc(8, "Eles não eram ricos", "img", "hands holding coins", "coins in palm")
sc(8, "E escolheram um homem para levar", "img", "Philippi ruins dawn", "Philippi Greece")
sc(8, "O nome dele tem uma origem curiosa", "img", "Aphrodite statue", "Venus de Milo")
sc(8, "E a viagem de Filipos até Roma", "map:filipos-roma")
sc(8, "Em algum momento dessa missão", "vid", "rain falling", "rain on road")
sc(8, "Para e imagina", "img", "Via Appia Antica", "Appian Way")
sc(8, "Mas a história de Epafrodito não termina", "vid", "sunrise timelapse", "sunrise clouds")
sc(8, "Repara como Deus cuida", "img", "Roman Forum panorama", "Forum Romanum")
sc(8, "Paulo recebeu a oferta", "img", "Saint Paul writing epistles painting", "Paul writing letter painting")
sc(8, "E naquela casa alugada", "img", "papyrus scroll", "ancient scroll")

# ---------- BLOCO 09 — A carta e a promessa ----------
sc(9, "A carta aos Filipenses é uma das cartas", "img", "Papyrus 46 folio", "P46 papyrus")
sc(9, "Um homem acorrentado mandando os livres", "img", "iron chain closeup", "old chain")
sc(9, "E perto do final da carta", "img", "Codex Alexandrinus", "Greek uncial manuscript")
sc(9, "Você conhece esse versículo", "img", "mountain summit sunrise", "mountain sunrise")
sc(9, "E então ele explica o que aquela oferta", "img", "ancient account tablet", "wax tablet Roman")
sc(9, "E então ele escreve", "vid", "incense smoke", "smoke rising")
sc(9, "Cheiro de suavidade", "img", "ancient altar incense", "Roman altar")
sc(9, "E logo depois, vem a promessa", "fx:versiculo")

# ---------- BLOCO 10 — O significado e o detalhe escondido ----------
sc(10, "Agora você entende", "img", "Papyrus 46", "Chester Beatty Library papyrus")
sc(10, "E repara: ele diz", "img", "Paul and Silas in prison", "Saint Paul prison")
sc(10, "E a palavra \"suprirá\"", "fx:pleroo")
sc(10, "E sabe o que é mais bonito", "img", "water pouring jug", "water jar pouring")
sc(10, "Mas lá no começo, eu te prometi", "fx:das-segundo")
sc(10, "Imagina um homem milionário", "img", "gold coins treasure", "coin hoard gold")
sc(10, "Paulo está dizendo: a medida", "vid", "clouds timelapse", "sky clouds")
sc(10, "Mas preste atenção em outra palavra", "img", "basket of bread", "bread basket")
sc(10, "E sabe como Paulo tinha tanta certeza", "img", "Philippi basilica", "Philippi ruins")
sc(10, "Agora vem a pergunta", "img", "road through fields", "country road")
sc(10, "Mas a história da igreja de Filipos mostra", "fx:quatro-atitudes")

# ---------- BLOCO 11 — As quatro atitudes ----------
sc(11, "A primeira atitude", "fx:atitude-1")
sc(11, "Lembra? Profunda pobreza", "img", "seeds in hand", "hand holding seeds")
sc(11, "Paulo responde, numa carta", "img", "sowing seeds field farmer", "farmer sowing")
sc(11, "Repara: Deus dá pão", "img", "wheat ears", "wheat field")
sc(11, "E dar não começa com um valor grande", "img", "food donation groceries", "food bank volunteers")
sc(11, "A segunda atitude", "fx:atitude-2")
sc(11, "Jesus ensinou", "img", "calendar wall", "old calendar")
sc(11, "E aqui vai um passo prático", "img", "envelopes money savings", "coin jar savings")
sc(11, "A terceira atitude", "fx:atitude-3")
sc(11, "A oferta dos filipenses não era", "img", "ancient Roman road", "Via Egnatia")
sc(11, "Pensa comigo: o que vem primeiro", "img", "sunrise over road", "road sunrise")
sc(11, "E a quarta atitude", "fx:atitude-4")
sc(11, "E a Bíblia faz um alerta sério", "img", "pile of money banknotes", "banknotes")
sc(11, "Contentamento não é conformismo", "img", "family table thanksgiving meal", "family dinner")
sc(11, "E sabe o que eu acho mais bonito", "img", "open hands", "hands open palms")
sc(11, "Então, vamos resumir", "fx:resumo-atitudes")
sc(11, "Foi assim que viveu aquela igreja", "img", "Philippi ruins sunset", "Philippi archaeological site")

# ---------- BLOCO 12 — Oração final ----------
sc(12, "Agora, eu quero orar com você", "vid", "candle flame", "candle")
sc(12, "Tu és o mesmo Deus que abriu o coração de Lídia", "vid", "river flowing", "stream water")
sc(12, "Tu és o mesmo Deus que fez Paulo e Silas", "img", "Paul and Silas in prison", "prison stone dark")
sc(12, "Tu és o mesmo Deus que transformou", "img", "family dinner table", "bread table")
sc(12, "Tu viste Epafrodito", "img", "Via Appia Antica", "Roman road")
sc(12, "Senhor, Tu viste uma igreja pobre", "img", "Philippi basilica ruins", "Philippi ruins")
sc(12, "Eu entrego a Ti as minhas necessidades", "img", "praying hands", "prayer hands")
sc(12, "O meu Deus... segundo as Suas riquezas", "vid", "sunrise timelapse", "sun rays clouds")

# ---------- BLOCO 13 — Encerramento ----------
sc(13, "Hoje você caminhou pelas ruas de Filipos", "img", "Philippi theatre", "Philippi ruins")
sc(13, "Sentou na beira do rio com Lídia", "img", "Lydia baptistery Philippi", "river Philippi")
sc(13, "Viajou com Epafrodito", "img", "Via Egnatia", "Roman road")
sc(13, "Da próxima vez que você ler", "img", "Papyrus 46", "papyrus")
sc(13, "A igreja de Filipos mandou uma oferta", "img", "sailing ship sunset sea", "Adriatic sea sunset")
sc(13, "E me conta aqui nos comentários", "img", "hands helping", "helping hand")
sc(13, "No próximo episódio", "img", "flour in bowl", "flour")
sc(13, "Até que um estrangeiro bateu à porta", "img", "old wooden door", "ancient door")
sc(13, "A viúva de Sarepta", "fx:proximo")


# Overlays: referências bíblicas, lugares/datas e títulos de seção.
# (bloco, anchor, tipo, texto, duração em segundos)
OVERLAYS = [
    (1, "Existe uma frase na Bíblia", "ref", "Filipenses 4:19", 7),
    (1, "Existe uma frase na Bíblia", "credit", "Papiro 46 · c. 200 d.C. · um dos manuscritos mais antigos das cartas de Paulo", 7),
    (4, "Vamos voltar no tempo", "title", "O mundo da época", 5),
    (4, "E no caminho dessa estrada", "place", "Filipos · Macedônia", 6),
    (4, "No ano quarenta e dois antes de Cristo", "place", "Batalha de Filipos · 42 a.C.", 6),
    (4, "O livro de Atos dos Apóstolos registra", "ref", "Atos 16:12", 7),
    (5, "Mas como Paulo foi parar em Filipos", "title", "Paulo chega à Macedônia", 5),
    (5, "Um homem da Macedônia estava de pé", "ref", "Atos 16:9", 7),
    (5, "Lídia não era de Filipos", "place", "Tiatira · Ásia Menor", 6),
    (5, "Paulo começou a falar sobre Jesus", "ref", "Atos 16:14-15", 7),
    (6, "Mas nem todo mundo em Filipos", "title", "A prisão à meia-noite", 5),
    (6, "Havia na cidade uma serva", "ref", "Atos 16:16-19", 7),
    (6, "Eu sei o que muita gente faria", "ref", "Atos 16:25", 7),
    (6, "E eles responderam", "ref", "Atos 16:31", 7),
    (7, "Paulo saiu de Filipos", "title", "A igreja que dava do que faltava", 5),
    (7, "E, para não ser peso para ninguém", "ref", "1 Tessalonicenses 2:9", 7),
    (7, "Na carta aos Filipenses, Paulo lembra", "ref", "Filipenses 4:16", 7),
    (7, "E quando Paulo seguiu viagem e chegou a Corinto", "ref", "2 Coríntios 11:9", 7),
    (7, "E Paulo faz uma declaração impressionante", "ref", "Filipenses 4:15", 7),
    (7, "Em muita prova de tribulação", "ref", "2 Coríntios 8:2-3", 9),
    (8, "Passam-se cerca de dez anos", "title", "Acorrentado em Roma", 5),
    (8, "O livro de Atos conta que, em Roma", "ref", "Atos 28:16, 20 · Efésios 6:20", 8),
    (8, "Um escritor do segundo século", "credit", "Luciano de Samósata, A Morte de Peregrino, 12-13", 7),
    (8, "Paulo o chama de", "ref", "Filipenses 2:25", 7),
    (8, "Em algum momento dessa missão", "ref", "Filipenses 2:27-30", 8),
    (9, "A carta aos Filipenses é uma das cartas", "title", "A carta e a promessa", 5),
    (9, "Paulo escreve: \"Regozijai-vos", "ref", "Filipenses 4:4", 7),
    (9, "Ele escreve: \"Ora, muito me regozijei", "ref", "Filipenses 4:10", 7),
    (9, "porque já aprendi a contentar-me", "ref", "Filipenses 4:11-13", 9),
    (9, "E continua: \"Todavia", "ref", "Filipenses 4:14", 6),
    (9, "Ele diz: \"Não que procure dádivas", "ref", "Filipenses 4:17", 7),
    (9, "E então ele escreve", "ref", "Filipenses 4:18", 8),
    (10, "E a palavra \"suprirá\"", "credit", "Concordância de Strong · G4137", 8),
    (11, "Jesus disse: \"Dai", "ref", "Lucas 6:38", 7),
    (11, "Paulo responde, numa carta", "ref", "2 Coríntios 9:10", 7),
    (11, "A Bíblia diz que Deus ama", "ref", "2 Coríntios 9:7", 6),
    (11, "Jesus ensinou", "ref", "Lucas 16:10", 7),
    (11, "Jesus disse: \"Mas buscai", "ref", "Mateus 6:33", 7),
    (11, "Paulo disse: \"aprendi", "ref", "Filipenses 4:11", 6),
    (11, "E a Bíblia faz um alerta sério", "ref", "1 Timóteo 6:10", 7),
    (12, "Agora, eu quero orar com você", "title", "Oração", 5),
    (12, "O meu Deus... segundo as Suas riquezas", "ref", "Filipenses 4:19", 10),
    # chamadas discretas (só aparecem se showCta = true)
    (6, "se inscreve no canal e deixa o seu like", "cta", "Curta  ·  Inscreva-se", 6),
    (13, "E se inscreve no canal", "cta", "Curta  ·  Inscreva-se", 6),
]

# Marcas de tempo para animações internas (bloco, frase, nome)
CUES = [
    (9, "\"O meu Deus, segundo as suas riquezas", "versiculo"),
    (10, "Paulo não diz que Deus vai suprir", "das"),
    (10, "Ele diz que Deus vai suprir", "segundo"),
    (10, "Parece pequeno", "segundo-fim"),
    (11, "Dar, mesmo tendo pouco", "r1"),
    (11, "Ser constante. Colocar", "r2"),
    (11, "Colocar o Reino em primeiro lugar", "r3"),
    (11, "E aprender o contentamento", "r4"),
    (13, "A viúva de Sarepta", "sarepta"),
]
