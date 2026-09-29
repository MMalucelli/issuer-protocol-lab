# Negociação própria do emissor sob assimetria informacional

## Uma arquitetura regulatória de capacidade, disclosure e aprendizagem de mercado

**Autor:** Matheus Turra Malucelli  
**Ano:** 2026

### Resumo

Esta tese investiga se uma companhia aberta poderia negociar ações de própria emissão mesmo enquanto possui vantagem informacional sobre si mesma sem receber capacidade ilimitada e opaca de explorar essa vantagem. A proposta não busca eliminar a assimetria informacional, mas disciplinar sua utilização por meio de limites distintos de intervenção e posição, disclosure condicionado à utilização da capacidade, memória informacional e aprendizagem do mercado. O desenho persegue simultaneamente três ganhos institucionais: melhorar a alocação de capital, tornar observável a expressão econômica da informação privada do emissor e oferecer maior previsibilidade jurídica para negociação de boa-fé dentro de um regime especial verificável. A arquitetura é deliberadamente parametrizável e falsificável: sua contribuição é decompor o problema em objetos econômicos e regulatórios explícitos, distinguir invariantes de hipóteses de especificação e tornar possível testar se existe alguma configuração em que a capacidade economicamente relevante do emissor seja compatível com integridade, liquidez e descoberta descentralizada de preço.

**Palavras-chave:** negociação de ações próprias; recompra de ações; assimetria informacional; microestrutura de mercado; disclosure; regulação financeira; descoberta de preço.

© 2026 Matheus Turra Malucelli. Este texto é disponibilizado sob a licença [Creative Commons Atribuição 4.0 Internacional — CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br). A licença exige atribuição adequada, indicação de alterações e referência à licença.

---

## Sumário

### [I. Problema, tese e escopo](#i-problema-tese-e-escopo)
1. [A provocação institucional](#1-a-provocacao-institucional)  
2. [A tese econômica](#2-a-tese-economica)  
3. [Ganhos pretendidos: alocação, informação e segurança jurídica](#3-ganhos-pretendidos-alocacao-informacao-e-seguranca-juridica)  
4. [O que o protocolo não pretende fazer](#4-o-que-o-protocolo-nao-pretende-fazer)  

### [II. Ontologia econômica do mecanismo](#ii-ontologia-economica-do-mecanismo)
5. [A unidade regulada e o estado do emissor](#5-a-unidade-regulada-e-o-estado-do-emissor)  
6. [Gross e Net: intervenção e posição](#6-gross-e-net-intervencao-e-posicao)  
7. [Treasury e o lado SELL](#7-treasury-e-o-lado-sell)  
8. [H: capacidade especial de negociação](#8-h-capacidade-especial-de-negociacao)  
9. [H₀, $H_{\max}$ e a escala da capacidade](#9-h0-hmax-e-a-escala-da-capacidade)  
10. [Q: alerta quantitativo e avaliação de disclosure](#10-q-quando-a-utilizacao-da-capacidade-obriga-disclosure)  
11. [U: utilização como intensidade observável do sinal](#11-u-utilizacao-como-intensidade-observavel-do-sinal)  
12. [Informação produzida pelo emissor, informação do mercado e atividade Gross](#12-informacao-produzida-pelo-emissor-informacao-do-mercado-e-atividade-gross)  
13. [Decay, memória e saturação](#13-decay-memoria-e-saturacao)  

### [III. Tempo, disclosure e transição de estado](#iii-tempo-disclosure-e-transicao-de-estado)
14. [W: janela regulatória, disclosure e transição de estado](#14-w-janela-regulatoria-disclosure-e-transicao-de-estado)  
15. [Modelo temporal rolling](#15-modelo-temporal-rolling)  
16. [Modelo temporal calendarizado](#16-modelo-temporal-calendarizado)  
17. [Duas topologias temporais para o mesmo mecanismo](#17-o-que-realmente-diferencia-as-duas-branches)  
18. [Intervalos de reação, reversão e Fato Relevante](#18-cooldown-reversao-e-fato-relevante)  

### [IV. Informação, aprendizagem e integridade](#iv-informacao-aprendizagem-e-integridade)
19. [A companhia como trader identificável e potencialmente informado](#19-a-companhia-como-trader-identificavel-e-potencialmente-informado)  
20. [Reputação, antecipação e reflexividade](#20-reputacao-antecipacao-e-reflexividade)  
21. [Saliência, familiaridade e aprendizagem do sinal](#21-o-risco-de-o-sinal-quebrar-o-mercado)  
22. [Captura parcial de valor, fabricação de sinal e fronteira da manipulação](#22-manipulacao-gross-e-transferencia-de-valor-a-terceiros)  
23. [Disciplina endógena, desenho adversarial e enforcement ex post](#23-disciplina-endogena-e-enforcement-ex-post)  

### [V. Especificação, calibração e laboratório regulatório](#v-especificacao-calibracao-e-laboratorio-regulatorio)
24. [Arquitetura, especificação e calibração](#24-arquitetura-especificacao-e-calibracao)  
25. [Observabilidade externa e flexibilidade operacional](#25-observabilidade-externa-e-flexibilidade-operacional)  
26. [Variáveis modulares e Variable Builder](#26-variaveis-modulares-e-variable-builder)  
27. [Invariantes e espaço experimental](#27-invariantes-e-espaco-experimental)  
28. [Critério de viabilidade](#28-criterio-de-viabilidade)  

### [VI. Evidência, precedentes e validação](#vi-evidencia-precedentes-e-validacao)
29. [O que a literatura já permite afirmar](#29-o-que-a-literatura-ja-permite-afirmar)  
30. [O que precedentes regulatórios sustentam — e o que não sustentam](#30-o-que-precedentes-regulatorios-sustentam-e-o-que-nao-sustentam)  
31. [Casos administrativos como testes de realidade](#31-casos-administrativos-como-testes-de-realidade)  
32. [Estratégia de validação e laboratório multiagente](#32-estrategia-de-validacao-e-laboratorio-multiagente)  

### [VII. Conclusão](#vii-conclusao)
33. [O que esta tese estabelece](#33-o-que-esta-tese-estabelece)  
34. [Conclusão conceitual](#34-conclusao-conceitual)  
35. [Referências](#35-referencias)  

---

<a id="i-problema-tese-e-escopo"></a>
# I. Problema, tese e escopo

<a id="1-a-provocacao-institucional"></a>
## 1. A provocação institucional

Uma companhia aberta pode conhecer mudanças relevantes em seu próprio estado econômico antes que o restante do mercado consiga incorporá-las ao preço. Essa assimetria não é uma anomalia: ela decorre do fato de que a companhia produz, observa e interpreta informação interna sobre si mesma.

O problema aparece quando essa companhia quer negociar ações de própria emissão. Imagine que WXYZ3 esteja sendo negociada a R$ 20 e que a administração, por razões que ainda não são públicas, decida comprar. No mercado ordinário, os demais participantes observam fluxo comprador, mas não necessariamente sabem que a própria WXYZ está por trás dele.

A intervenção institucional proposta é simples em sua origem: **quando o emissor negociar a própria ação dentro do regime especial, sua atuação deixa de ser anônima**. O mercado secundário continua sendo o mesmo; não se cria um book separado. O que muda é que a participação do emissor passa a ser atribuível e submetida a limites próprios.

Em termos intuitivos, o mercado poderia saber que:

> **COMPANHIA WXYZ — BUY — quantidade executada — preço**

ou que:

> **COMPANHIA WXYZ — SELL — quantidade executada — preço**

Isso não revela a informação privada que motivou a decisão. Revela outra coisa: **a própria companhia decidiu comprometer capital naquela direção**. O mercado continua livre para interpretar esse comportamento como sinal informacional, alocação de caixa, necessidade de financiamento, erro de administração ou qualquer outra hipótese compatível com os dados.

Essa camada não substitui Fato Relevante. Obrigações de divulgação material continuam existindo segundo sua própria lógica. A operação identificada responde a uma pergunta diferente: não necessariamente *o que aconteceu dentro da companhia?*, mas *o que a companhia decidiu fazer economicamente?*

O regime jurídico brasileiro trata negociação de ações de própria emissão e negociação na pendência de informação relevante não divulgada como matérias reguladas, hoje principalmente pelas Resoluções CVM 77 e 44 ([CVM, 2022](#ref-1); [CVM, 2021](#ref-2)). Esta tese não descreve o regime vigente como autorização para a companhia “fazer insider trading”. A proposta é deliberadamente contrafactual: pergunta como deveria ser desenhada uma exceção regulatória específica se quiséssemos permitir que o emissor utilizasse economicamente parte de sua vantagem informacional sem conceder a ele capacidade ilimitada e opaca de exploração dessa vantagem.

A pergunta deixa de ser apenas:

> **Quando o emissor deve ser impedido de negociar?**

para se tornar:

> **Existe uma arquitetura em que o emissor possa negociar mesmo possuindo vantagem informacional sobre si próprio, preservando capacidade economicamente relevante de agir sem excluir indefinidamente o restante do mercado da descoberta de preço?**

A mudança altera o objeto regulatório. Em vez de tentar eliminar a assimetria antes da negociação, o protocolo tenta controlar **como ela pode ser exercida, quanto pode ser exercida e que informação a própria utilização dessa capacidade deve devolver ao mercado**.

A cadeia causal que será formalizada nas seções seguintes é:

> convicção privada → decisão econômica → execução identificável → utilização mensurável de capacidade → eventual disclosure formal → atualização do estado informacional → reação do mercado

A companhia continua sabendo mais. A diferença é que sua ação deixa de ser silenciosa e ilimitada.

Essa é a premissa institucional que orienta o restante da tese: a companhia pode ser a primeira a saber e a primeira a agir, mas não deve conseguir capturar sozinha todo o ajuste de preço produzido por sua vantagem. Sua execução pode iniciar a descoberta; a escala, o disclosure e o tempo precisam preservar espaço para que o mercado também reaja, interprete e negocie.

---

<a id="2-a-tese-economica"></a>
## 2. A tese econômica

A hipótese central pode ser expressa sem álgebra sofisticada:

> **A vantagem informacional não é, por si só, o objeto que o mecanismo tenta eliminar. O objeto é a exclusividade com que essa vantagem pode ser monetizada.**

A companhia pode ser a primeira a saber e a primeira a agir, mas não deve receber capacidade indefinida para ser a única participante da descoberta de preço que sua própria informação produz.

A arquitetura procura, portanto, combinar três propriedades:

1. capacidade economicamente relevante para o emissor;
2. produção progressiva de informação observável para o mercado;
3. segurança jurídica ex ante para operações de boa-fé, condicionada a limites verificáveis de intervenção, posição e disclosure.

A existência simultânea dessas propriedades é hipótese, não conclusão.

Chamemos de **Θ** o conjunto de configurações possíveis do mecanismo e de **Θᵥ** a região que satisfaz critérios mínimos de viabilidade econômica e integridade de mercado. A pergunta é simplesmente:

> **Θᵥ é vazio ou existe pelo menos uma configuração viável?**

Nada nesta tese exige que Θᵥ seja diferente de vazio. Se toda configuração que preserve utilidade econômica para a companhia produzir deterioração inaceitável de liquidez, manipulação, reflexividade ou transferência de valor, a hipótese institucional deve ser rejeitada.

---

<a id="3-ganhos-pretendidos-alocacao-informacao-e-seguranca-juridica"></a>
## 3. Ganhos pretendidos: alocação, informação e segurança jurídica

A proposta só é economicamente interessante se entregar algo além de transparência formal. Ela busca combinar três ganhos que hoje entram em tensão: **capacidade de alocação de capital pelo emissor, produção de informação para o mercado e maior previsibilidade jurídica para a própria negociação**.

O primeiro ganho é permitir que a companhia coloque patrimônio corporativo em uma decisão sobre o próprio ativo. Se comprar barato, o benefício pertence à companhia e, indiretamente, aos seus acionistas; se comprar caro, o patrimônio corporativo absorve a perda. No lado vendedor, a companhia pode reduzir Treasury quando essa decisão fizer sentido econômico, sempre limitada ao estoque de ações que efetivamente possui. A tese não presume que BUY signifique subavaliação nem que SELL signifique sobreavaliação. Essas interpretações pertencem ao mercado.

O segundo ganho é informacional. A operação deixa um rastro atribuível: direção, quantidade, preço, utilização da capacidade e histórico. O emissor não precisa revelar seu raciocínio privado para que sua decisão econômica se torne um dado adicional da descoberta de preço. A proposta procura fazer com que o mercado não seja completamente excluído enquanto a companhia exerce sua vantagem.

O terceiro ganho é jurídico. A segurança jurídica é um pilar, não um efeito colateral. O regime especial pretende substituir parte de uma fronteira dependente de estado informacional e interpretação ex post por uma fronteira operacional mais explícita: capacidade disponível, utilização, triggers de disclosure, posição de Treasury e invariantes verificáveis. A companhia que opere de boa-fé dentro do regime deve conseguir saber ex ante quais condições tornam sua atuação admissível.

Isso não cria imunidade. Fraude, manipulação, coordenação artificial, informação falsa e outras condutas abusivas permanecem sujeitas a supervisão e julgamento. O safe harbour proposto é **condicionado ao protocolo**: reduz incerteza sobre a possibilidade de o emissor negociar enquanto possui vantagem informacional, sem transformar conformidade mecânica em licença para manipular o mercado.

Esses três ganhos podem entrar em conflito. Capacidade demais pode excluir o mercado; disclosure demais ou cedo demais pode tornar a capacidade economicamente inútil; limites mal desenhados podem criar estratégias mecânicas de exploração; segurança jurídica excessivamente ampla pode proteger condutas que deveriam continuar investigáveis. A arquitetura existe para tornar esses trade-offs explícitos e testáveis.

---

<a id="4-o-que-o-protocolo-nao-pretende-fazer"></a>
## 4. O que o protocolo não pretende fazer

O protocolo não pretende tornar participantes igualmente informados, igualmente inteligentes ou igualmente capazes de interpretar fluxo.

Ele também não pretende substituir as regras de Fato Relevante, legalizar negociação de administradores ou controladores pessoas físicas, eliminar investigação de manipulação ou declarar legítima qualquer operação realizada pela companhia.

O regime especial seria restrito ao emissor negociando ações de própria emissão dentro de regras públicas específicas.

A companhia não seria obrigada a divulgar imediatamente **por que** decidiu comprar ou vender. Seu raciocínio permanece privado. O mercado recebe sua ação, a intensidade dessa ação e o histórico produzido pelo protocolo.

A participação no regime-base pressupõe ainda um perímetro instrumental estreito. A companhia não poderia combinar a capacidade especial sobre a ação com exposição derivativa ao preço da própria ação. A razão é econômica: permitir simultaneamente capacidade regulatória especial sobre o subjacente e payoff alavancado ou não linear sobre o próprio sinal abriria um segundo canal de monetização não disciplinado pela posição física.

Essa proibição é uma escolha conservadora de desenho. O safe harbour europeu para programas de recompra também delimita sua exceção à negociação das próprias ações sob condições específicas; isso serve como precedente de perímetro estreito, não como demonstração de que nossa proibição seja ótima ([European Commission, 2016](#ref-3)).

---

<a id="ii-ontologia-economica-do-mecanismo"></a>
# II. Ontologia econômica do mecanismo

<a id="5-a-unidade-regulada-e-o-estado-do-emissor"></a>
## 5. A unidade regulada e o estado do emissor

A capacidade pertence ao **ticker/emissor**, não ao setor.

Para cada emissor i e cada janela regulatória n, o protocolo calcula três capacidades:

- **$H_{\mathrm{gross}}$**: capacidade total de intervenção;
- **$H_{\mathrm{net}+}$**: capacidade de aumentar a posição própria;
- **$H_{\mathrm{net}-}$**: capacidade de reduzir a posição própria.

Essas capacidades são funções de um estado observável e regulatoriamente definido. Esse estado pode conter características do ativo, posição de Treasury, memória informacional, utilização histórica e variáveis externas selecionadas.

A tese não fixa uma única equação para H. Ela fixa o **significado econômico** de cada dimensão e as propriedades que qualquer função escolhida deve preservar.

Essa distinção é importante. O protocolo não precisa decidir hoje quanto peso atribuir à volatilidade ou à profundidade, nem se determinada variável externa deve sequer integrar o cálculo. Essas são decisões de especificação e calibração. A ontologia vem antes.

---

<a id="6-gross-e-net-intervencao-e-posicao"></a>
## 6. Gross e Net: intervenção e posição

Definimos, em cada janela:

> **Gross = BUY + SELL**

> **Net = BUY − SELL**

Exemplo simples:

| BUY | SELL | Gross | Net |
|---:|---:|---:|---:|
| 100 | 0 | 100 | +100 |
| 0 | 100 | 100 | −100 |
| 100 | 100 | 200 | 0 |

O terceiro caso é o motivo de a separação ser necessária. Net igual a zero não significa ausência de atuação no mercado.

**Gross mede intensidade de intervenção.** Uma companhia que compra e vende repetidamente pode afetar liquidez, fluxo, expectativa e preço mesmo terminando sem alteração líquida de posição.

**Net mede alteração de exposição econômica.** É a dimensão mais diretamente relacionada à captura de vantagem informacional por construção ou redução de posição.

A associação principal é, portanto:

> $H_{\mathrm{gross}}$ → disciplina principalmente intervenção e risco microestrutural

> $H_{\mathrm{net}}$ → disciplina principalmente alteração posicional sob vantagem informacional

As dimensões se sobrepõem, mas não são substitutas.

Uma reversão não restitui Gross. Se a companhia compra 100 e depois vende 100, ela pode voltar ao Net inicial, mas consumiu 200 unidades de intervenção. Essa propriedade é uma defesa natural contra estratégias de alternância: trocar de direção pode reabrir espaço posicional, mas nunca apaga o custo regulatório da atividade já realizada.

---

<a id="7-treasury-e-o-lado-sell"></a>
## 7. Treasury e o lado SELL

O regime-base não permite short verdadeiro da companhia em sua própria ação.

Portanto:

> **Treasury ≥ 0**

> **SELL ≤ ações disponíveis em Treasury**

O lado vendedor significa redução de ações previamente mantidas em tesouraria, não criação de exposição econômica negativa.

Três grandezas patrimoniais devem permanecer distintas. **Ações emitidas** abrangem as ações em circulação e as ações mantidas em tesouraria. **Ações em circulação** excluem Treasury. **Free float** corresponde apenas à parcela das ações em circulação efetivamente disponível para negociação dispersa no mercado. Portanto:

> **ações emitidas = ações em circulação + Treasury**

> **free float ≤ ações em circulação**

Em geral, free float somado a Treasury não corresponde ao total emitido, porque ações em circulação podem permanecer com controladores, administradores ou outros blocos não integrantes do free float. O protocolo deve receber essas grandezas como dados separados, com proveniência e data de referência próprias.

Isso torna $H_{\mathrm{net}}$ assimétrico por construção. Podemos ter $H_{\mathrm{net}+}$ e $H_{\mathrm{net}-}$ diferentes, porque comprar e vender partem de restrições físicas distintas.

É útil normalizar a posição de Treasury entre 0 e 1. No extremo inferior, não existe ação disponível para venda; no extremo superior, não existe espaço físico adicional para aquisição dentro do limite societário considerado. Assim:

> Treasury = 0 → capacidade SELL líquida deve convergir a zero

> Treasury = limite máximo → capacidade BUY líquida deve convergir a zero

A posição física é diferente da informação. Mesmo um sinal informacional extremamente forte não pode criar ações em Treasury que não existem nem ampliar um limite societário por construção.

Também não se presume que SELL signifique necessariamente visão negativa sobre o valor da ação. A companhia pode vender para financiar projetos, restaurar free float, desfazer recompra anterior ou realocar capital. O mercado aprende o significado empírico desse comportamento ao longo do tempo.

---

<a id="8-h-capacidade-especial-de-negociacao"></a>
## 8. H: capacidade especial de negociação

H é o orçamento regulatório de utilização da vantagem especial concedida ao emissor.

A arquitetura possui três H porque existem três perguntas diferentes:

> **Quanto a companhia pode mexer no próprio mercado?** → $H_{\mathrm{gross}}$

> **Quanto pode aumentar sua posição?** → $H_{\mathrm{net}+}$

> **Quanto pode reduzir sua posição?** → $H_{\mathrm{net}-}$

H é um **hard cap**. A execução não pode ultrapassá-lo dentro da janela aplicável. Se uma ordem excede a capacidade residual, executa-se apenas a maior parcela simultaneamente compatível com $H_{\mathrm{gross}}$, $H_{\mathrm{net}+}$, $H_{\mathrm{net}-}$ e as restrições físicas aplicáveis. O residual não executado permanece registrado como ordem rejeitada, acompanhado da quantidade e do limite vinculante. Solicitação, execução e rejeição são objetos distintos.

A função que calcula H pode ser representada abstratamente como:

> **H = função(estado do ticker, posição, informação, variáveis regulatórias selecionadas)**

Características setoriais podem integrar os inputs da função de H quando forem economicamente relevantes. Ainda assim, elas apenas ajudam a caracterizar o estado do ticker: a capacidade resultante é individualizada e pertence ao emissor avaliado, não ao setor como unidade regulada.

A função também não precisa ser puramente multiplicativa. O laboratório poderá testar multiplicação, adição, funções limitadas, min/max, regras por faixas ou outras composições, desde que preservem os invariantes da arquitetura.

Um **plano público voluntário de recompra** pode ser tratado como variável candidata de H, e não como obrigação estrutural do regime. A lógica é limitada: ao anunciar previamente uma intenção agregada — por exemplo, adquirir até determinado montante ao longo de um ano — a companhia reduz parte da surpresa informacional da primeira execução. Uma especificação pode reconhecer esse pré-disclosure com aumento moderado da capacidade inicial. O valor anunciado, porém, **não se converte em capacidade automática**. A continuidade da escala depende de execução efetiva e das demais regras do protocolo. Se o plano aumenta H, quanto aumenta e sob quais limites são questões de especificação e calibração.

---

<a id="9-h0-hmax-e-a-escala-da-capacidade"></a>
## 9. H₀, $H_{\max}$ e a escala da capacidade

Para tornar a dinâmica inteligível, é útil separar três ideias.

**H₀** é uma referência estrutural ou neutra para o ticker. Ela pode depender de características como volume, profundidade, spread, free float, turnover e volatilidade. H₀ não é um piso garantido.

**$H_{\max}$** é uma capacidade máxima admissível sob determinada especificação, mantidas constantes as demais restrições. É o teto para o qual o componente informacional poderia empurrar H — não uma capacidade automaticamente concedida.

**H calculado** é a capacidade produzida pela função para o estado atual, antes das restrições físicas externas à função.

Uma forma conceitual simples é:

> **H calculado = H₀ + escala informacional × ($H_{\max}$ − H₀)**

A “escala informacional” varia entre uma condição neutra e uma condição máxima. A função exata não é fixada aqui.

A representação separa duas decisões. Primeiro define-se o intervalo economicamente admissível entre uma capacidade neutra e uma capacidade máxima. Depois define-se como o estado informacional move H dentro desse intervalo.

A capacidade efetivamente disponível resulta da aplicação das restrições físicas ao H calculado. No lado vendedor:

> **$H_{\mathrm{net}-}$ efetivo = min($H_{\mathrm{net}-}$ calculado, Treasury disponível)**

No lado comprador, uma especificação pode ainda limitar $H_{\mathrm{net}+}$ pelo espaço remanescente até um limite societário ou regulatório de posição própria. Essa trava adicional pertence ao espaço experimental; a impossibilidade de vender mais ações do que a Treasury disponível pertence à arquitetura.

Uma função saturante é uma candidata natural porque impede que H cresça indefinidamente. Ela também pode representar retornos marginais decrescentes de sinais repetidos na mesma direção — vários disclosures semelhantes podem acrescentar progressivamente menos informação nova —, mas essa interpretação **não define** o conceito de saturação. É uma hipótese adicional sobre a forma do mapeamento entre informação e capacidade.

H₀ e $H_{\max}$ permanecem objetos de calibração. Um H₀ muito pequeno pode tornar o regime pouco útil no curto prazo, embora a necessidade de entrar gradualmente seja parte deliberada da arquitetura. Essa progressão não deve responder a um sinal mínimo ou meramente mecânico: a escala futura deve depender de utilização relevante da capacidade e de execução observável. Assim, o risco de “aquecer” H por pequenas operações artificiais é tratado pela própria regra de progressão, e não pela concessão de uma capacidade inicial maior. Um H₀ excessivo, por outro lado, pode conceder grande vantagem antes que o emissor tenha produzido informação compensatória. O mesmo vale para a distância entre H₀ e $H_{\max}$.

A velocidade de aproximação entre H₀ e $H_{\max}$ também é substantiva. Uma progressão lenta demais pode impedir uma companhia que pretende executar uma alocação economicamente relevante ao longo de meses de atingir escala útil; uma progressão rápida demais pode permitir que pequenas operações iniciais fabriquem capacidade desproporcional. Por isso o laboratório deve testar crescimento linear, acelerado e saturante, inclusive especificações em que **persistência direcional coerente acelera a liberação de capacidade** sem tornar execução passada um direito automático a H futuro.

Reversões podem receber tratamento assimétrico. É plausível testar se uma mudança de BUY para SELL degrada parcialmente a capacidade acumulada na direção anterior e/ou faz $H_{\mathrm{net}-}$ recomeçar de uma base menor, preservada a possibilidade legítima de realizar Treasury. Essa fricção pode dificultar a sequência BUY → reação do mercado → SELL em escala simétrica imediata. Ela não é canonizada como regra: se excessiva, pode permitir que o próprio mercado encurrale a companhia ao explorar sua dificuldade regulatória de saída.

---

<a id="10-q-quando-a-utilizacao-da-capacidade-obriga-disclosure"></a>
## 10. Q: alerta quantitativo e avaliação de disclosure

H responde “quanto pode executar”. Q responde “a partir de que intensidade a atividade deve ser sinalizada ao emissor e submetida à avaliação quantitativa de disclosure no corte aplicável”.

Para cada dimensão pode existir um par Q/H:

| Dimensão | Limiar de disclosure | Limite rígido |
|---|---|---|
| intervenção | $Q_{\mathrm{gross}}$ | $H_{\mathrm{gross}}$ |
| posição BUY | $Q_{\mathrm{net}+}$ | $H_{\mathrm{net}+}$ |
| posição SELL | $Q_{\mathrm{net}-}$ | $H_{\mathrm{net}-}$ |

Economicamente, há duas famílias de fronteira — intervenção e posição — e, operacionalmente, a fronteira posicional pode ser direcional.

Q pode ser representado como uma proporção de H:

> **Q = ρ × H**, com 0 < ρ ≤ 1.

Se ρ = 1, o limiar quantitativo coincide com o esgotamento da capacidade. Se ρ < 1, a atividade entra na região de alerta antes do limite rígido.

Isso cria uma região residual:

> **Q < execução ≤ H**

Atingir Q não interrompe imediatamente a execução. Q é um **limiar informacional**, enquanto H continua sendo o limite de execução.

A semântica de Q possui dois momentos distintos:

1. **alerta intraday:** ao alcançar Q, a infraestrutura informa o emissor e registra a ultrapassagem de forma auditável;
2. **avaliação no corte:** no encerramento da sessão ou em outro corte público definido pela especificação, os valores consolidados são comparados com Q para determinar a obrigação de disclosure.

Além dessa fronteira quantitativa existe um **trigger temporal T**, detalhado na Parte III. T é a duração máxima de W, a janela regulatória iniciada pela primeira execução. Q e T cumprem funções complementares e podem encerrar W: Q reage à intensidade da utilização; T impede que atividade abaixo do limiar permaneça indefinidamente sem disclosure.

Essa separação é necessária porque Gross e Net possuem propriedades temporais diferentes. Gross é cumulativo dentro da janela: BUY e SELL aumentam Gross, e uma operação oposta não desfaz a ultrapassagem de $Q_{\mathrm{gross}}$. Net representa posição e pode recuar. Se Net+ ultrapassa $Q_{\mathrm{net}+}$ e uma venda posterior reduz a exposição para abaixo do limiar antes do corte, não há disclosure quantitativo por Net+ naquele fechamento. O alerta intraday permanece no registro de auditoria, mas não é convertido retroativamente em obrigação pública.

> **Ultrapassar Q net durante a sessão gera alerta; terminar acima de Q net no corte gera disclosure.**

> **Ultrapassar Q gross não é reversível por operação oposta, porque Gross acumula as duas pernas.**

A distinção possui uma função anti-avoidance importante. Se Q fosse sempre igual a H, a companhia poderia encontrar valor em permanecer repetidamente em H − ε e esperar apenas o trigger temporal. Com Q abaixo de H, evitar a avaliação quantitativa exige abrir mão de parcela material da capacidade disponível. A reversibilidade de Net não apaga a intervenção necessária para produzir a ida e a volta, porque ambas continuam consumindo Gross.

Assim, ρ controla quanto da capacidade pode ser utilizada antes que a atividade entre na região de alerta e possa produzir obrigação quantitativa no corte.

Nenhum valor específico de ρ é proposto nesta etapa.

Quando o disclosure é devido, ele não deve fingir que a execução foi exatamente Q nem limitar-se a dizer que “Q foi ultrapassado”. Q define a fronteira de avaliação. A quantidade informacionalmente relevante é a **execução consolidada efetiva no momento de corte**, da qual deriva U. Assim, uma especificação-base deve distinguir: a ultrapassagem intraday gera alerta; a condição consolidada no corte determina a obrigação; e o disclosure informa quanto foi efetivamente executado.

---

<a id="11-u-utilizacao-como-intensidade-observavel-do-sinal"></a>
## 11. U: utilização como intensidade observável do sinal

Q define **quando alertar e em que fronteira avaliar** o disclosure. U ajuda a representar **quanto da capacidade foi efetivamente utilizada**.

Para cada dimensão $j$:

> **$U_j = \dfrac{\text{execução relevante}_j}{H_j}$**

Logo, U varia de 0 a 1 dentro da capacidade permitida.

No lado posicional, é útil separar direções:

> **$U_{\mathrm{net}+}$ = Net positivo / $H_{\mathrm{net}+}$**

> **$U_{\mathrm{net}-}$ = |Net negativo| / $H_{\mathrm{net}-}$**

U não é “informação” em si. É uma medida normalizada da intensidade da decisão observável do emissor em relação à capacidade que ele tinha disponível. Em uma representação simplificada, a execução observável produz U; uma função de atualização interpreta essa intensidade juntamente com direção, tempo e demais características da execução; e o resultado altera a memória informacional I. Portanto, U é um input da atualização e não precisa ser o multiplicador direto de informação.

O estado informacional futuro deve ter origem em comportamento observável. Como a execução do emissor é identificável no regime especial, a atualização pode utilizar a trajetória executada consolidada mesmo quando ela não produz disclosure quantitativo adicional por Q. O disclosure formal agrega, certifica e devolve informação segundo o protocolo; não é a única forma pela qual a atuação se torna observável. A cadeia é:

> H disponível → execução identificável → U observado → eventual disclosure formal → atualização de informação → decay ao longo do tempo → H futuro

Uma companhia que utiliza 5% de sua capacidade e uma companhia que utiliza 95% não precisam produzir o mesmo sinal, mesmo que ambas tenham negociado na mesma direção.

A função que transforma U em atualização informacional é experimental. Ela pode ser linear, côncava, convexa, saturante ou depender de outras características da execução. O protocolo apenas exige que a hipótese seja declarada e testável.

No caso de churn, Gross pode ser elevado enquanto Net é próximo de zero. Isso significa que $U_{\mathrm{gross}}$ pode ser alto e $U_{\mathrm{net}}$ baixo. Essa diferença é precisamente o que permite separar informação sobre **atividade** de informação sobre **comprometimento posicional**.

---

<a id="12-informacao-produzida-pelo-emissor-informacao-do-mercado-e-atividade-gross"></a>
## 12. Informação produzida pelo emissor, informação do mercado e atividade Gross

A palavra “informação” pode designar fenômenos economicamente diferentes. A arquitetura os separa explicitamente.

Em síntese, três objetos podem alimentar o estado futuro. **$I_{\mathrm{issuer}}$** guarda a memória associada às decisões observáveis do emissor; **$I_{\mathrm{market}}$** representa informação econômica já disponível externamente; e **$A_{\mathrm{gross}}$** pode registrar, de forma opcional, a atividade bruta atribuível à companhia. U funciona como uma medida de intensidade utilizada na atualização desses estados, sobretudo de $I_{\mathrm{issuer}}$, mas não se confunde com nenhum deles.

<a id="12-1-i-issuer-informacao-produzida-pela-acao-divulgada-do-emissor"></a>
### 12.1. $I_{\mathrm{issuer}}$: informação revelada pela ação observável do emissor

$I_{\mathrm{issuer}}$ representa o estado informacional associado ao histórico observável de comprometimento posicional da companhia, composto pelas execuções identificáveis e pelos disclosures formais aplicáveis. A expressão “informação produzida pelo emissor” deve ser entendida com cuidado: o protocolo não transforma BUY em afirmação de subavaliação nem SELL em afirmação de sobreavaliação. O dado produzido é a própria ação econômica observável; a inferência sobre fundamentos e valuation é produzida pelo mercado.

Ele pode ser direcional:

- **$I_{\mathrm{issuer}+}$**: memória informacional associada a BUY líquido;
- **$I_{\mathrm{issuer}-}$**: memória informacional associada a SELL líquido.

Sua atualização pode depender de $U_{\mathrm{net}}$, da mudança efetiva de Treasury, do tempo e de outras características da execução.

Não se exige que $I_{\mathrm{issuer}+}$ e $I_{\mathrm{issuer}-}$ se cancelem. Uma companhia pode ter histórico informativo relevante nas duas direções. Alternância continua custosa por Gross e pode ser limitada por **saturação**, que contempla a perda de valor marginal de sinais repetidos na mesma direção, e por **decay**, que representa a depreciação do valor informacional passado ao longo do tempo quando o sinal não é renovado. As formas específicas desses mecanismos são apresentadas na seção seguinte.

<a id="12-2-i-market-informacao-ja-disponivel-externamente"></a>
### 12.2. $I_{\mathrm{market}}$: informação já disponível externamente

$I_{\mathrm{market}}$ representa informação sobre o estado econômico da companhia que o mercado consegue observar **independentemente das operações do emissor**.

Exemplos possíveis incluem preços de commodities, câmbio, juros ou outras externalidades diretamente relacionadas ao negócio.

$I_{\mathrm{market}}$ não é “crédito ganho pela companhia”. É uma medida candidata da quantidade ou qualidade de informação econômica que já está fora da companhia.

A hipótese é que maior observabilidade externa possa reduzir a assimetria marginal exclusiva do emissor e, portanto, justificar — em alguma especificação — maior flexibilidade operacional. Essa última passagem precisa ser testada; não é automática.

<a id="12-3-a-gross-informacao-opcional-derivada-da-atividade-bruta"></a>
### 12.3. $A_{\mathrm{gross}}$: informação opcional derivada da atividade bruta

Além da memória direcional associada à posição líquida, o laboratório pode testar uma variável opcional chamada **$A_{\mathrm{gross}}$**. Ela representa um estado informacional derivado da atividade Gross divulgada: não diz que a companhia aumentou ou reduziu sua exposição, apenas registra que houve atividade bruta atribuível ao emissor.

A lógica é:

> atividade Gross divulgada → possível informação sobre comportamento → $A_{\mathrm{gross}}$

Mas o regulador pode decidir que puro churn não merece capacidade futura alguma. Nesse caso:

> **$A_{\mathrm{gross}}$ = 0**

Outra especificação pode permitir que $A_{\mathrm{gross}}$ afete apenas $H_{\mathrm{gross}}$, e não $H_{\mathrm{net}}$. Isso é particularmente atraente porque mantém separado o valor informacional de “a companhia esteve muito ativa” do valor informacional de “a companhia assumiu posição líquida”.

A arquitetura não canoniza $A_{\mathrm{gross}}$. Ela apenas deixa explícita a hipótese para que possa ser incluída ou removida.

---

<a id="13-decay-memoria-e-saturacao"></a>
## 13. Decay, memória e saturação

Decay ocorre sobre **informação**, não sobre H.

Se nenhum novo sinal relevante surgir, a informação produzida por uma operação antiga tende a perder capacidade explicativa sobre o estado econômico atual da companhia.

Assim:

> $I_{\mathrm{issuer}}$ elevado hoje → tempo sem novo sinal → $I_{\mathrm{issuer}}$ converge gradualmente ao estado neutro

H muda posteriormente porque é recalculado a partir de um estado informacional diferente. Não existe necessidade de escrever “H decai”.

A forma temporal do decay é desconhecida. Pode ser exponencial, hiperbólica, logística, piecewise ou empiricamente estimada. A tese exige apenas uma propriedade mínima: sem nova evidência, a memória informacional não deve permanecer máxima indefinidamente.

Saturação responde a outra pergunta: **qual é o limite do efeito que informação acumulada pode exercer sobre H?**

Se H₀ é a referência neutra e $H_{\max}$ o teto admissível, a informação deve mapear H para algum ponto dentro desse intervalo. A função pode possuir retornos marginais decrescentes, mas isso é uma propriedade candidata, não uma definição necessária.

Essa separação produz quatro objetos distintos:

- H₀: referência estrutural;
- $H_{\max}$: teto de capacidade sob a especificação;
- I: estado informacional;
- decay: envelhecimento de I.

Ela evita que “memória”, “capacidade” e “saturação” sejam tratados como sinônimos.

---

<a id="iii-tempo-disclosure-e-transicao-de-estado"></a>
# III. Tempo, disclosure e transição de estado

<a id="14-w-janela-regulatoria-disclosure-e-transicao-de-estado"></a>
## 14. W: janela regulatória, disclosure e transição de estado

O tempo do protocolo é organizado por **W**, a janela regulatória dentro da qual a atuação do emissor é acumulada e avaliada. W não é apenas um intervalo de calendário: é o universo comum ao qual pertencem H, Q e T.

- **H pertence a W:** a capacidade é calculada na abertura da janela, permanece travada durante sua vigência e é consumida pelas execuções nela realizadas;
- **Q pertence a W:** o limiar quantitativo é definido sobre os H daquela janela e determina quando a utilização entra na região de alerta e de avaliação de disclosure;
- **T pertence a W:** o prazo começa com a abertura da janela, limita sua duração e funciona como trigger temporal de disclosure caso Q não a encerre antes.

No baseline, a primeira execução elegível do emissor abre $W_n$. Antes dela não existe capacidade temporal sendo consumida nem relógio T em curso. A partir dela, todas as execuções elegíveis do mesmo emissor são atribuídas a $W_n$ até seu encerramento.

O protocolo possui, portanto, dois gatilhos complementares de devolução de informação. **Q** reage à intensidade da utilização; **T** impede que uma janela permaneça aberta indefinidamente com atividade abaixo de Q. Se o corte aplicável confirmar a condição de Q, o disclosure quantitativo é devido e fecha W. Se Q não produzir esse encerramento, o vencimento de T aciona o disclosure temporal e também fecha W.

A ultrapassagem intraday de Q continua sendo alerta, não encerramento automático. Para $Q_{\mathrm{gross}}$, a ultrapassagem persiste até o corte porque Gross não diminui. Para $Q_{\mathrm{net}+}$ e $Q_{\mathrm{net}-}$, uma operação oposta pode devolver a exposição para baixo do limiar antes da consolidação. Nesse caso, não há fechamento de W por Q, embora a ultrapassagem e sua reversão permaneçam no registro auditável.

Quando Q é confirmado, a execução não precisa ter parado exatamente no limiar. A companhia pode ter utilizado a capacidade residual até H antes do corte, mas Q não cria capacidade nova nem recicla a parcela consumida. O disclosure informa **o que foi efetivamente executado em W** — direção, quantidades, utilização e demais campos do protocolo —, e não uma quantidade ficticiamente igual a Q.

O fechamento da sessão é o corte público do baseline. Ele separa o alerta operacional da obrigação pública, incorpora a trajetória completa de Net e impede que o disclosure reabra capacidade no mesmo fluxo intraday. Encerrada $W_n$, o estado é atualizado; a capacidade não utilizada expira; e $W_{n+1}$ pode começar **no pregão seguinte**, nunca no mesmo pregão do disclosure que fechou a janela anterior.

Em forma compacta:

> primeira execução → abertura de $W_n$ e início de T → consumo de H e monitoramento de Q → corte → fechamento por Q ou T → disclosure → atualização do estado → elegibilidade de $W_{n+1}$ no pregão seguinte

Não existem janelas sobrepostas para o mesmo emissor.

---

<a id="15-modelo-temporal-rolling"></a>
## 15. Modelo temporal rolling

O modelo **rolling** é a expressão mais direta desse ciclo. A primeira execução elegível abre $W_n$ e inicia a contagem de T naquele instante. Se Q não fechar a janela antes, T vence após a duração especificada, independentemente de fronteiras comuns do calendário.

Esse desenho faz o relógio acompanhar a atividade efetiva do emissor. Uma companhia inativa não mantém W artificialmente aberta; companhias que começam a operar em momentos diferentes possuem janelas distintas. O mercado observa as execuções e os disclosures do protocolo sem precisar tratar a abertura administrativa de W como um evento econômico separado.

Após o encerramento:

> $W_n$ → disclosure por Q ou T → atualização de estado → cálculo de $H_{n+1}$ → $W_{n+1}$ elegível no pregão seguinte

Q continua necessário mesmo com T. Sem a fronteira quantitativa, o emissor poderia consumir parcela muito elevada de H logo após a abertura e devolver informação apenas no prazo máximo. Q antecipa o encerramento quando a intensidade da utilização assim exige.

---

<a id="16-modelo-temporal-calendarizado"></a>
## 16. Modelo temporal calendarizado

O modelo **calendarizado** mantém a primeira execução como ato que ativa W, mas ancora seu limite externo em um ciclo público previamente conhecido — por exemplo, semana, quinzena ou mês regulatório. Se nenhuma operação ocorrer, não existe W ativa; se a companhia operar, a janela se encerra no primeiro evento entre a confirmação de Q, o vencimento de T e a fronteira calendarizada aplicável.

A vantagem é a previsibilidade: mercado e emissor conhecem antecipadamente o limite máximo do ciclo. O custo potencial é que essa fronteira se torna informação estratégica. Participantes podem adaptar liquidez, ordens e antecipação à proximidade do corte. Sazonalidade microestrutural em torno dessas datas é, portanto, uma hipótese a ser testada.

Como no rolling, H permanece fixo enquanto W está aberta, a execução consome capacidade e nenhum disclosure recicla H dentro da mesma janela.

---

<a id="17-o-que-realmente-diferencia-as-duas-branches"></a>
## 17. Duas topologias temporais para o mesmo mecanismo

Os modelos calendarizado e rolling implementam o mesmo motor econômico:

> estado → primeira execução e abertura de W → cálculo e trava de H → execução → U → alerta Q → fechamento por Q ou T → disclosure → atualização de informação → novo estado → novo H

A diferença é **como o tempo delimita uma janela regulatória**.

Nos dois modelos, a primeira execução ativa W e Q pode encerrá-la. A diferença está na âncora temporal remanescente. No rolling, T é contado exclusivamente a partir da primeira execução. No calendarizado, W também se submete a uma fronteira pública externa, que pode antecipar seu encerramento.

Essa separação é útil porque permite comparar as duas topologias mantendo constantes função de H, parâmetros, agentes e condições de mercado. O modelo calendarizado oferece fronteiras temporais simples e públicas; o rolling reduz a dependência de um relógio comum, mas introduz transições endógenas associadas à própria atividade do emissor. Nenhum dos dois é tratado como superior a priori.

---

<a id="18-cooldown-reversao-e-fato-relevante"></a>
## 18. Intervalos de reação, reversão e Fato Relevante

Além das janelas W e do prazo T, o desenho pode testar a necessidade de um **intervalo adicional sem nova intervenção do emissor** após determinado disclosure. Chamemos esse intervalo opcional de **C**.

C existe para responder a uma pergunta empírica: a fronteira temporal já criada pelo disclosure e pela próxima sessão oferece tempo suficiente para que o mercado reaja, ou é necessário reservar um período adicional? Se a própria separação entre sessões for suficiente, C pode ser zero. Se não for, valores positivos podem ser testados. A tese não presume antecipadamente que esse intervalo adicional seja necessário.

A reversão de direção é um problema relacionado, mas distinto. Uma companhia pode comprar e posteriormente vender ações em Treasury por mudança de avaliação, necessidade de caixa, realização de valor ou outra razão econômica legítima. Ao mesmo tempo, reversões muito rápidas podem ser utilizadas para tentar monetizar a reação produzida pela própria atuação identificada.

A primeira proteção é estrutural: **reversão não restitui Gross**. Comprar e depois vender pode reduzir Net, mas consome intervenção nas duas pernas. O laboratório pode ainda testar uma fricção direcional específica, como degradação parcial da capacidade futura após reversão ou um intervalo mínimo antes da direção oposta. Essas alternativas pertencem ao espaço experimental porque uma trava excessiva também cria risco: terceiros podem explorar o fato de que o emissor ficou previsivelmente preso a uma direção.

Fato Relevante permanece externo à máquina do protocolo. Sua divulgação pode alterar radicalmente a interpretação das operações anteriores e o valor da informação privada remanescente, mas não produz automaticamente bônus, reset ou novo H. As obrigações jurídicas de Fato Relevante continuam existindo por sua própria lógica ([CVM, 2021](#ref-2)).

---

<a id="iv-informacao-aprendizagem-e-integridade"></a>
# IV. Informação, aprendizagem e integridade

<a id="19-a-companhia-como-trader-identificavel-e-potencialmente-informado"></a>
## 19. A companhia como trader identificável e potencialmente informado

A proposta depende de uma ideia já central à teoria de microestrutura: **ordens e transações podem carregar informação**.

Glosten e Milgrom mostram, em um modelo clássico de market making com traders heterogeneamente informados, que a presença de traders com informação superior gera componente de seleção adversa no spread e que preços de transação transmitem informação. Hasbrouck trata empiricamente o efeito informacional de trades por meio de seu impacto permanente sobre preços e encontra relações entre tamanho do trade, impacto e spread ([Glosten e Milgrom, 1985](#ref-4); [Hasbrouck, 1991](#ref-5)).

Esta tese adiciona uma característica institucional incomum: o trader potencialmente informado não é apenas inferido estatisticamente. **Sua identidade como emissor é pública.**

Isso pode tornar a ação da companhia um sinal particularmente forte.

O protocolo não revela a informação privada subjacente. Ele revela comportamento econômico padronizado: direção, intensidade, utilização da capacidade, timing e histórico.

Investidores sofisticados já dedicam recursos à inferência de informação a partir de fluxo, trades e mudanças de quotes. O mecanismo proposto não cria do zero essa atividade. Ele altera a qualidade e a atribuição de uma fonte específica de fluxo ao tornar pública a identidade do emissor.

> **O dado pode ser democratizado; a capacidade de interpretá-lo continua competitiva.**

---

<a id="20-reputacao-antecipacao-e-reflexividade"></a>
## 20. Reputação, antecipação e reflexividade

O protocolo não converte reputação em pontuação regulatória. Reputação é uma crença endógena do mercado formada a partir do histórico público:

> emissor X comprou → quanto comprou → quanto de H utilizou → o que aconteceu depois → como se comportou em reversões → como o mercado reagiu

Se BUY de determinada companhia historicamente precede informação econômica positiva, participantes podem reagir mais rapidamente a novos BUYs. Se a companhia alterna repetidamente entre BUY e SELL após reações fortes, o mercado também pode aprender a descontar, contrariar ou punir esse padrão. Isso não é, por si só, abuso. É aprendizagem.

A companhia também observa o mercado. O protocolo contém, portanto, dois pares simultâneos de ação e reação:

> **companhia → mercado:** execução, sinal observável, reação de preço e liquidez

> **mercado → companhia:** antecipação, arbitragem, spreads, reação ao histórico e alteração do custo de entrada ou saída

O desenho não deve presumir cooperação de nenhum dos lados. Uma companhia racional procura a melhor política permitida pelo protocolo; participantes racionais procuram explorar tanto a informação da companhia quanto as restrições que o próprio protocolo lhe impõe. Uma regra que torne reversão excessivamente difícil, por exemplo, pode permitir que terceiros negociem sabendo que o emissor está regulatoriamente encurralado.

Por isso, comportamento estratégico não é uma anomalia a ser removida do modelo. É parte do objeto. O regulador deve perguntar como a companhia poderia explorar mercado e protocolo e, simetricamente, como o mercado poderia sufocar ou explorar a companhia.

---

<a id="21-o-risco-de-o-sinal-quebrar-o-mercado"></a>
## 21. Saliência, familiaridade e aprendizagem do sinal

O protocolo cria deliberadamente um sinal potencialmente poderoso:

> **trader identificado + provável vantagem informacional + direção + intensidade de utilização da capacidade**

A intensidade desse sinal pode depender não apenas de U e da reputação do emissor, mas também da **raridade do próprio evento**. Uma primeira operação identificada sob um regime novo pode produzir estardalhaço, overshooting e proteção agressiva de market makers. O mesmo U, depois de dezenas de interações observadas, pode receber interpretação muito diferente. Familiaridade institucional e familiaridade operacional são, portanto, dimensões distintas.

Isso não transforma choque informacional em defeito por definição. Saliência não é manipulação; volatilidade não é necessariamente falha; overreaction inicial não implica desequilíbrio permanente. Uma trajetória plausível é:

> operação identificada rara → reação excessiva → companhia e mercado observam o resultado → agentes recalibram → novas operações recebem interpretação menos mecânica → possível estabilização

Também é possível que a estabilização não ocorra. Market makers podem reduzir liquidez, seguidores podem amplificar excessivamente o sinal, reputação pode gerar múltiplos equilíbrios ou a identificação do emissor pode dominar a produção independente de informação. A existência de aprendizagem saudável é hipótese de validação, não premissa.

Os mecanismos apresentados na seção 19 tornam ambos os resultados plausíveis: a identificação de um trader potencialmente informado pode ampliar proteção contra seleção adversa, enquanto sua presença também pode fornecer contraparte e liquidez. A evidência específica sobre recompras, discutida na seção 29, encontra sinais diferentes conforme mercado e amostra. O efeito líquido não pode ser presumido pela arquitetura.

O protocolo não pretende escolher a reação correta do mercado. Arbitradores, market makers, especuladores e investidores podem copiar, contrariar ou ignorar o emissor. O objetivo é preservar condições para que essas respostas existam e sejam aprendidas.

Grossman e Stiglitz mostram, em contexto mais geral, por que mercados perfeitamente informacionalmente eficientes são incompatíveis com incentivos para aquisição custosa de informação ([Grossman e Stiglitz, 1980](#ref-6)). Esta tese não aplica o modelo deles mecanicamente ao protocolo; utiliza-o como lembrete de que **mais informação pública não é automaticamente equivalente a uma estrutura informacional melhor**.

A questão de viabilidade é dinâmica: a saliência inicial converge para um processo informacional administrável ou destrói liquidez, executabilidade ou descoberta descentralizada de preço antes que o aprendizado ocorra?

---

<a id="22-manipulacao-gross-e-transferencia-de-valor-a-terceiros"></a>
## 22. Captura parcial de valor, fabricação de sinal e fronteira da manipulação

O dado divulgado pelo protocolo é “a companhia comprou” ou “a companhia vendeu”, acompanhado de quantidade e utilização de capacidade. Ele **não** é “a companhia declarou que está barato” ou “a companhia declarou que está caro”. O valuation permanece uma inferência dos participantes.

A companhia continua podendo capturar parte da alta que ajudou a antecipar. Ela compra enquanto o preço ainda não incorporou integralmente sua informação; se estiver correta, a posição em Treasury se valoriza. O protocolo não elimina esse retorno — eliminá-lo retiraria parte substancial do incentivo econômico para participar do regime.

O que o protocolo procura impedir é a captura **integral e unilateral** do movimento. Para aumentar a posição, a companhia consome H; ao utilizar parcela relevante, aproxima-se de Q e antecipa o disclosure; ao atingir Q ou T, fecha W e precisa aguardar a próxima janela; e, uma vez identificada, sua atuação pode alterar preço e liquidez contra as execuções seguintes. Quanto maior a tentativa de monetizar a vantagem, maior a parcela da própria informação devolvida ao mercado e menor o espaço para continuar executando antes da reação. Essa é uma propriedade autorregulatória pretendida da arquitetura, não uma garantia já demonstrada.

Essa estrutura permite separar duas situações. Na primeira, a companhia assume posição econômica genuína, o mercado participa do repricing e, em estado posterior de preço e informação, a companhia realiza parte de Treasury. O ganho corporativo pode coexistir com participação de terceiros na descoberta de preço. Se a decisão estiver errada, o patrimônio da própria companhia absorve a perda e o histórico público pode reduzir a credibilidade de sinais futuros.

Na segunda situação, a finalidade econômica predominante da operação é fabricar percepção artificial de demanda, convicção ou valor para induzir terceiros a negociar e monetizar a reação produzida. A execução pode ser real e ainda assim levantar problema de manipulação. H, Q, T e a identificação do emissor não tornam intenção manipulativa impossível; procuram limitar sua escala, elevar seu custo e tornar a trajetória reconstruível.

A arquitetura não pretende resolver intenção por álgebra. Gross impede que BUY e SELL sucessivos apaguem a intervenção realizada; H limita escala em W; Q e T encerram a janela e disciplinam a devolução informacional; Treasury limita SELL físico; reversões permanecem observáveis; e especificações de H podem tornar persistência econômica mais capaz de gerar escala do que alternância estratégica.

Isso conduz a uma premissa de elaboração do sistema:

> **Nenhuma estratégia exploratória deve conseguir escala relevante sem consumir capacidade, assumir risco econômico, deixar rastro observável ou destruir a própria capacidade futura.**

A premissa é um alvo de convergência, não uma promessa de impossibilidade de exploit. Se uma estratégia barata, escalável e repetível permite extrair valor porque o protocolo garante mecanicamente a reação de terceiros, existe uma fragilidade estrutural. Se a exploração exige capital, Gross, tempo, risco de mercado e perda de opcionalidade futura, a própria dinâmica pode discipliná-la.

Essa disciplina pode vir também do mercado. Uma companhia que repetidamente tente explorar BUY → valorização → SELL pode ensinar participantes a não seguir o próximo BUY, a operar contra ele ou a alterar spreads e profundidade. A exploração pode, assim, reduzir a eficácia futura da própria exploração. A engenharia deve **fortalecer**, e não substituir, esse mecanismo endógeno sempre que possível.

Também importa observar terceiros. Participantes que inferem publicamente o sinal competem informacionalmente; participantes que antecipam ordens futuras por acesso indevido apresentam problema diferente, potencialmente envolvendo vazamento ou front running. Investigações sérias podem exigir dados não públicos de ordens, cancelamentos, contrapartes e lead-lag.

---

<a id="23-disciplina-endogena-e-enforcement-ex-post"></a>
## 23. Disciplina endógena, desenho adversarial e enforcement ex post

Parte das propriedades desejadas pode ser imposta mecanicamente:

> Gross não pode ultrapassar $H_{\mathrm{gross}}$.

> Net positivo não pode ultrapassar $H_{\mathrm{net}+}$.

> Net negativo não pode ultrapassar $H_{\mathrm{net}-}$.

> SELL não pode ultrapassar Treasury disponível.

> Operação oposta não apaga Gross consumido.

Essas restrições não são punições. São invariantes do regime.

A primeira forma de disciplina é endógena:

> uso da capacidade → consumo de H → alerta Q → fechamento de W por Q ou T → disclosure → reação e aprendizagem do mercado

A segunda é jurídica e supervisória:

> conduta → investigação → interpretação → eventual sanção

A primeira não substitui a segunda. Manipulação, fraude, coordenação, vazamento, informação falsa e estratégias não antecipadas continuam exigindo julgamento. Da mesma forma, conformidade mecânica com H, Q e T não deve funcionar como escudo para uma conduta cuja natureza econômica seja manipulativa.

Dois princípios de desenho seguem dessa separação:

> **Invariante quando possível; supervisão quando necessária; julgamento quando inevitável.**

> **Sempre que possível, a arquitetura deve fortalecer mecanismos endógenos de disciplina em vez de substituí-los por proibições ex ante.**

O protocolo deve ser desenhado contra o comportamento racional dos dois lados, e não a partir da expectativa de comportamento cooperativo. O teste adversarial relevante pergunta simultaneamente qual seria a melhor exploração disponível à companhia e qual seria a melhor resposta do mercado às ações e restrições da companhia.

---

<a id="v-especificacao-calibracao-e-laboratorio-regulatorio"></a>
# V. Especificação, calibração e laboratório regulatório

<a id="24-arquitetura-especificacao-e-calibracao"></a>
## 24. Arquitetura, especificação e calibração

A tese distingue três camadas.

### Arquitetura

Define o significado dos objetos:

- W como janela regulatória à qual pertencem H, Q e T;
- Gross e Net;
- $H_{\mathrm{gross}}$, $H_{\mathrm{net}+}$ e $H_{\mathrm{net}-}$;
- Q como limiar de alerta e avaliação no corte;
- U como utilização relativa;
- Treasury;
- abertura de W pela primeira execução, encerramento por Q ou T e transição para a janela seguinte;
- informação e decay;
- topologia Calendar ou Rolling.

### Especificação

Escolhe como os objetos se relacionam:

- quais variáveis entram em H;
- como U atualiza $I_{\mathrm{issuer}}$;
- se existe $A_{\mathrm{gross}}$;
- como $I_{\mathrm{market}}$ é representado;
- qual função de saturação é usada;
- como decay funciona;
- como H₀ e $H_{\max}$ são definidos;
- se plano público voluntário produz bônus moderado de capacidade inicial;
- como persistência e reversão afetam a progressão direcional de H.

### Calibração

Escolhe ou estima valores:

- tamanho de H₀;
- $H_{\max}$;
- ρ = Q/H;
- duração T;
- parâmetros de decay;
- sensibilidade de H à informação;
- neutralidade de Treasury;
- pesos ou funções das variáveis externas;
- bônus por plano público, se existir;
- aceleração de H por persistência;
- degradação de capacidade por reversão, se existir.

A arquitetura pode estar madura enquanto especificação e calibração permanecem abertas. Isso não é deficiência; é condição para que a hipótese possa ser testada sem inventar precisão.

O laboratório acrescenta uma quarta distinção metodológica, sem alterar essas três camadas. Um **cenário** descreve uma trajetória exógena de ordens associada a uma companhia e a uma estratégia. Uma **especificação** contém as relações formais de memória, capacidade e intrawindow. Uma **avaliação** aplica uma especificação a um cenário a partir de um snapshot de dados:

> **resultado = F(snapshot de dados, cenário, especificação)**

Cada avaliação elementar corresponde a uma combinação especificação × cenário. Comparações agregam essas avaliações de duas formas controladas: várias especificações sobre um cenário fixo, ou vários cenários sob uma especificação fixa. Essa separação permite alterar a estratégia de ordens mantendo a regra constante, ou alterar a regra mantendo a trajetória solicitada constante. O cenário não contém Q, H ou disclosure; esses objetos são resolvidos pela especificação e pelo estado da companhia.

---

<a id="25-observabilidade-externa-e-flexibilidade-operacional"></a>
## 25. Observabilidade externa e flexibilidade operacional

Esta seção retoma $I_{\mathrm{market}}$, apresentado na seção 12.2, e desloca a discussão da ontologia para a especificação. A vantagem informacional do emissor não precisa ter a mesma intensidade em todos os ativos ou estados do mercado.

Parte da informação economicamente relevante de uma companhia pode ser inferida por terceiros a partir de variáveis públicas. Uma empresa fortemente dependente de commodity cotada, câmbio ou juros pode estar exposta a choques que o mercado observa em tempo real.

Isso não elimina informação privada. A companhia continua conhecendo contratos, custos, produtividade, estratégia, hedge, execução e inúmeras outras variáveis internas.

A hipótese é marginal:

> **maior observabilidade externa → potencialmente menor parcela da informação economicamente relevante exclusiva ao emissor → possibilidade de flexibilização de H**

A última seta não deve ser presumida.

Setor pode servir como proxy grosseira quando características melhores não estiverem disponíveis, mas a preferência metodológica é decompor a ideia em variáveis objetivas quando possível: exposição a commodity, sensibilidade cambial, dependência de preços públicos, concentração geográfica ou outras externalidades mensuráveis.

O setor não recebe capacidade. O ticker recebe H.

---

<a id="26-variaveis-modulares-e-variable-builder"></a>
## 26. Variáveis modulares e Variable Builder

A existência de interações plausíveis cuja relevância ainda é desconhecida cria um problema metodológico: ignorá-las pode empobrecer o modelo; incorporá-las definitivamente pode transformar especulação em regra.

A solução proposta é modularidade experimental.

> **Quando a análise identifica uma interação economicamente plausível, mas não fornece evidência suficiente para transformá-la em regra, o mecanismo pode torná-la uma hipótese modular e testável.**

O laboratório deve separar:

> **dados → variáveis → função de H**

Dados representam fatos observados e não pertencem à especificação. Treasury, preço de referência, ações emitidas, ações em circulação e free float devem ser mapeados semanticamente no snapshot da companhia. A especificação pode selecionar variáveis derivadas desses dados e definir como elas entram em H, mas não pode transformar uma posição física observada em parâmetro discricionário da própria regra.

Uma variável pode vir de dados nativos do mecanismo, dados de mercado ou fonte externa. Ela pode possuir transformação, normalização, lag, bounds, frequência e política de missing data explicitamente documentados.

Exemplos de variáveis primitivas:

- ADTV;
- depth;
- spread;
- free float;
- volatilidade;
- Treasury;
- preço de commodity;
- câmbio;
- existência e dimensão de plano público voluntário.

Exemplos derivados:

- utilização U;
- exposição externa estimada;
- estado informacional $I_{\mathrm{issuer}}$;
- estado de atividade $A_{\mathrm{gross}}$;
- persistência direcional;
- frequência de reversão;
- familiaridade histórica do mercado com operações identificadas.

Cada função de H deve ser uma pipeline independente. O regulador pode testar, por exemplo:

> $H_{\mathrm{net}+}$ = função(H₀, $I_{\mathrm{issuer}+}$, posição)

contra:

> $H_{\mathrm{net}+}$ = função(H₀, $I_{\mathrm{issuer}+}$, posição, $I_{\mathrm{market}}$)

ou testar $H_{\mathrm{gross}}$ com e sem $A_{\mathrm{gross}}$.

A modularidade não é feature creep. Ela existe para tornar **barato rejeitar hipóteses**.

Se uma variável não melhora a estabilidade, a explicabilidade ou o desempenho do mecanismo, ela deve poder ser removida sem alterar a ontologia central.

---

<a id="27-invariantes-e-espaco-experimental"></a>
## 27. Invariantes e espaço experimental

Algumas propriedades pertencem à arquitetura e não devem ser tratadas como sliders arbitrários:

| Propriedade | Status |
|---|---|
| Gross e Net são distintos | estrutural |
| $H_{\mathrm{gross}}$, $H_{\mathrm{net}+}$ e $H_{\mathrm{net}-}$ são capacidades separadas | estrutural |
| H é hard cap | estrutural |
| ordens acima dos limites têm execução parcial e residual rejeitado | estrutural |
| Q gera alerta intraday e é avaliado no corte para disclosure | estrutural |
| Q ≤ H | estrutural |
| SELL ≤ Treasury | estrutural |
| Treasury não pode ficar negativa | estrutural |
| reversão não restitui Gross | estrutural |
| H, Q e T são resolvidos dentro de W | estrutural |
| disclosure confirmado por Q ou acionado por T encerra W | estrutural |
| uma nova W não começa antes do pregão seguinte | baseline estrutural |
| decay atua sobre informação, não diretamente sobre H | estrutural |
| Fato Relevante não reseta automaticamente H | baseline estrutural |
| derivativos sobre a própria ação ficam fora do regime especial | baseline estrutural |

Outras propriedades pertencem ao espaço experimental:

- valor de Q/H;
- H₀ e $H_{\max}$;
- função de H;
- função U → $I_{\mathrm{issuer}}$;
- forma do decay;
- forma da saturação;
- existência de $A_{\mathrm{gross}}$;
- uso de $I_{\mathrm{market}}$;
- variáveis externas;
- duração T;
- modelo calendarizado versus modelo rolling;
- eventual intervalo adicional de reação C;
- bônus moderado por plano público;
- velocidade e forma de crescimento de H com execuções sucessivas;
- degradação parcial de H após reversão;
- assimetria de capacidade na direção oposta;
- familiaridade e taxa-base de operações identificadas.

Essa separação impede que o laboratório vire um ambiente em que “qualquer coisa vale”.

---

<a id="28-criterio-de-viabilidade"></a>
## 28. Critério de viabilidade

O protocolo não precisa maximizar uma função escalar única de bem-estar para ser testável.

É suficiente definir um vetor de resultados e restrições mínimas.

Do lado da companhia, interessam pelo menos:

- capacidade economicamente útil de execução;
- custo de implementação;
- retorno da Treasury;
- flexibilidade de capital allocation;
- previsibilidade e segurança jurídica para operações de boa-fé.

Do lado do mercado:

- spread;
- depth;
- volume;
- impacto de preço;
- velocidade e qualidade da descoberta de preço;
- concentração de ganhos;
- comportamento de market makers;
- estabilidade e reflexividade;
- capacidade de terceiros explorarem o mecanismo.

A região viável Θᵥ existe apenas se alguma configuração preservar utilidade econômica para a companhia sem violar critérios mínimos de integridade e funcionamento de mercado.

A tese não deve ser defendida contra o resultado de Θᵥ vazio.

---

<a id="vi-evidencia-precedentes-e-validacao"></a>
# VI. Evidência, precedentes e validação

<a id="29-o-que-a-literatura-ja-permite-afirmar"></a>
## 29. O que a literatura já permite afirmar

A literatura não fornece sinal único para o efeito de recompras sobre liquidez.

Brockman e Chung, usando mais de cinco mil recompras efetivamente identificadas em Hong Kong, encontraram evidência de timing gerencial e deterioração de algumas medidas de liquidez durante períodos de recompra, incluindo spreads maiores e menor profundidade ([Brockman e Chung, 2001](#ref-7)).

Hillert, Maug e Obernberger, analisando 50.204 meses de recompra realizada nos Estados Unidos entre 2004 e 2010, encontraram efeito oposto em sua amostra: recompras podem melhorar liquidez, inclusive porque a companhia atua como fornecedora de liquidez quando outros investidores desejam vender ([Hillert, Maug e Obernberger, 2016](#ref-8)).

Ginglinger e Hamon encontram efeitos adversos sobre liquidez em dados franceses e interpretam boa parte da atuação como contrarian trading e suporte de preço ([Ginglinger e Hamon, 2007](#ref-9)).

Portanto:

> **o emissor pode simultaneamente ser fonte de seleção adversa e fonte de liquidez. O sinal líquido é empírico e dependente do contexto.**

Isso é importante porque a tese nunca deve assumir “presença do emissor reduz liquidez” como premissa. Spread, depth, volume, impacto e comportamento de market makers são outputs.

A literatura de microestrutura acrescenta outro ponto: trades carregam informação e participantes ajustam preços e quotes em resposta ao risco de negociar contra agentes informados ([Glosten e Milgrom, 1985](#ref-4); [Hasbrouck, 1991](#ref-5)). Isso torna plausível tanto o benefício informacional quanto o risco de amplificação do sinal identificado do emissor.

Uma análise exploratória dos Formulários de Referência da CVM enviados para esta pesquisa também sugere que programas de recompra não são meramente autorizações dormentes. Nos FREs de 2021 e 2022, aproximadamente três quartos dos registros de programas com quantidade prevista apresentavam alguma quantidade efetivamente adquirida; entre os programas que executaram, a mediana de execução ficou próxima de dois terços da quantidade prevista. As tabelas de movimentação de Treasury também mostram aquisição e alienação efetivas por um conjunto material de companhias. Esses dados são úteis para estabelecer **familiaridade institucional e execução agregada**, mas não permitem reconstruir de forma limpa e padronizada a frequência por sessão. Programa relativamente comum não implica execução diária relativamente comum.

Essa lacuna é relevante para estimar a saliência inicial do regime, mas não invalida sua arquitetura conceitual. A frequência operacional sob o protocolo será também parcialmente endógena a H, Q, T, à duração dos programas e às decisões das próprias companhias.

---

<a id="30-o-que-precedentes-regulatorios-sustentam-e-o-que-nao-sustentam"></a>
## 30. O que precedentes regulatórios sustentam — e o que não sustentam

A proposta não surgiu de uma tentativa de copiar um regime existente. Ainda assim, alguns componentes possuem paralelos institucionais úteis.

Nos Estados Unidos, a Rule 10b-18 da SEC estabelece condições de safe harbour para recompras, incluindo restrição de volume. A SEC explica que a limitação — em geral 25% do ADTV — busca impedir que o emissor domine o mercado de suas próprias ações e comprometa a percepção do mercado como mecanismo independente de formação de preço ([SEC, 2002](#ref-10)).

Na União Europeia, o Regulamento Delegado 2016/1052 também estabelece condições de preço e volume; o emissor não pode, para fins do safe harbour, comprar em um dia mais de 25% do volume médio diário no venue. O regulamento exige reporte e divulgação das transações do programa até o fim da sétima sessão de mercado após a execução ([European Commission, 2016](#ref-3)).

Esses regimes mostram que **capacidade quantitativa de intervenção, timing de disclosure e perímetro instrumental são objetos regulatórios reais**.

Eles não possuem nossa arquitetura completa.

Em particular:

- o limite de volume existente não é $H_{\mathrm{gross}}$ no sentido adaptativo desta tese;
- não há nosso $H_{\mathrm{net}}$ direcional;
- não há nossa função U → I → H futuro;
- o disclosure europeu por prazo após execução é mais próximo de um trigger temporal do que de Q;
- não há nosso Q como threshold de utilização que produz mudança de estado;
- não há nosso H progressivo baseado em informação devolvida ao mercado.

Portanto, convergência de componentes não é identidade de mecanismo.

No Brasil, a própria CVM abriu a Consulta Pública SDM 04/2025 para discutir ajustes na Resolução 77 com foco em negociação de ações de própria emissão, apoiada em análise de impacto regulatório sobre recompra e liquidez e em comparações internacionais ([CVM, 2025](#ref-11)). Isso não valida a proposta, mas confirma a atualidade institucional do problema.

---

<a id="31-casos-administrativos-como-testes-de-realidade"></a>
## 31. Casos administrativos como testes de realidade

Casos reais são úteis não para provar a tese, mas para impedir que ela seja construída sobre uma imagem excessivamente limpa do mercado. O exercício é contrafactual: primeiro se apresenta o que foi publicamente discutido no processo; depois se pergunta quais informações, limites e registros existiriam se o protocolo estivesse disponível. O resultado jurídico histórico não é reescrito, e a aplicação hipotética do protocolo não presume culpa nem inocência.

**Kepler Weber.** A área técnica da CVM propôs responsabilização da companhia e de seu diretor de relações com investidores pela aquisição, em nome da companhia, de 112 mil ações de própria emissão entre 13 e 27 de julho de 2022, dentro do período de vedação anterior à divulgação do ITR. O processo foi encerrado por Termo de Compromisso, sem julgamento de mérito ([CVM, 2023a](#ref-12)). A distribuição das aquisições por múltiplos pregões mostra por que a unidade temporal economicamente relevante não precisa coincidir com um único dia.

No universo do protocolo, a primeira aquisição abriria W; H limitaria a escala disponível naquela janela; Q ou T determinariam o momento de devolução informacional; e eventual continuidade ocorreria apenas em janelas posteriores. O mercado observaria que a própria Kepler Weber estava comprando, sem receber automaticamente a informação privada que motivava a decisão. O caso deixa de ser apenas um problema binário de permissão ou proibição e passa a ser também um teste de capacidade, duração, disclosure e reconstrução da trajetória.

**JBS, FB Participações e J&F.** O processo examinou negócios realizados pela JBS S.A. e por sua então controladora, FB Participações S.A., com ações JBSS3. Os acusados eram Joesley Batista, Wesley Batista e J&F Investimentos S.A., sucessora da FB Participações; a JBS era parte central dos fatos, mas não figurava entre os acusados desse processo. A decisão condenou a J&F, nessa qualidade de sucessora, porque a FB vendeu ações da JBS durante período vedado pelo programa de recompra da companhia. Joesley, Wesley e J&F foram absolvidos das imputações de insider trading e manipulação relacionadas às operações examinadas ([CVM, 2023b](#ref-13)). A distinção é precisamente o que torna o caso útil: negociação, informação, intenção e manipulação não podem ser inferidas umas das outras de maneira automática.

Sob o protocolo, a identificação do emissor, o consumo de H, os alertas de Q, o fechamento de W e a trilha de execuções tornariam observável uma parcela maior da conduta econômica. Isso não resolveria por fórmula a existência de informação privilegiada ou intenção manipulativa, nem afastaria proibições jurídicas externas ao regime. Permitiria, contudo, separar com mais clareza o que foi solicitado, executado, divulgado e economicamente capturado.

**JSL e Haitong.** Em processo relacionado a negócios com JSLG3 realizados durante programa de recompra, a área técnica da CVM formulou acusações de manipulação contra a companhia e participantes ligados à execução, além de prática não equitativa atribuída a participantes da Haitong que teriam se antecipado à atuação esperada da JSL. O processo foi objeto de Termos de Compromisso; esse desfecho não equivale a julgamento de mérito ou admissão das acusações ([CVM, 2018](#ref-14)).

O caso mostra que o fluxo esperado do emissor pode tornar-se objeto econômico para terceiros. No protocolo, a atuação identificada não eliminaria vazamento, coordenação ou antecipação indevida; criaria, porém, uma referência pública comum e uma trilha que separa atividade Gross, posição Net, contrapartes, timing e reação. Também mostra por que **Net = 0 não elimina relevância de Gross**: compras e vendas podem se compensar na posição final e ainda assim produzir intervenção, sinal e oportunidade de exploração.

O comparativo contrafactual pode ser resumido assim:

| Caso | Problema que tensiona a arquitetura | O que o protocolo tornaria observável ou limitado |
|---|---|---|
| Kepler Weber | recompras distribuídas por múltiplos pregões | abertura e encerramento de W, consumo de H e disclosures sucessivos |
| JBS e FB/J&F | dificuldade de separar negociação, informação e intenção ex post | identidade, utilização, trajetória executada e momento dos disclosures, sem automatizar o julgamento jurídico |
| JSL/Haitong | manipulação alegada e antecipação do fluxo do emissor por terceiros | Gross, Net, timing, reação e trilha auditável para investigar exploração e coordenação |

Os casos reforçam duas perguntas do laboratório:

> terceiros conseguem capturar sistematicamente valor antecipando a companhia?

> a companhia consegue usar a reação de terceiros ao próprio sinal como fonte de retorno independente da informação fundamental?

---

<a id="32-estrategia-de-validacao-e-laboratorio-multiagente"></a>
## 32. Estratégia de validação e laboratório multiagente

A validação deve ocorrer em camadas.

<a id="32-1-testes-de-invariantes"></a>
### 32.1. Testes de invariantes

Primeiro, verificar propriedades mecânicas: Treasury nunca negativa, SELL limitado ao estoque, Gross não apagado por reversão, Q não excedendo H, execução aceita nunca ultrapassando os limites simultaneamente aplicáveis, residual excedente sendo rejeitado e registrado, alertas intraday permanecendo auditáveis, disclosure quantitativo sendo decidido pela condição consolidada no corte, Q ou T encerrando W, capacidade não sendo reciclada dentro da janela encerrada e a próxima W tornando-se elegível apenas a partir do pregão seguinte.

<a id="32-2-testes-de-trajetoria"></a>
### 32.2. Testes de trajetória

Depois, estudar o mecanismo sem agentes sofisticados:

- BUY persistente;
- SELL persistente;
- alternância;
- churn;
- inatividade;
- decay;
- saturação;
- proximidade dos extremos de Treasury;
- Q baixo versus Q alto;
- H₀ próximo versus distante de $H_{\max}$;
- crescimento linear versus acelerado de H;
- reversão com e sem degradação de capacidade;
- plano público com e sem bônus inicial;
- regimes de baixa e alta familiaridade operacional.

É nessa fase que um exemplo numérico completo deve ser construído. Ele não será apresentado como calibração realista, mas como **exemplo pedagógico executável** para transformar a sopa de símbolos em uma trajetória concreta: H inicial, execução, U, alerta Q, consolidação no fechamento, decisão de disclosure, atualização de I, decay e novo H.

<a id="32-3-implementacao-de-referencia"></a>
### 32.3. Implementação de referência: Issuer Protocol Lab

O **Issuer Protocol Lab** implementa a primeira camada determinística da estratégia de validação. Sua função é tornar a máquina regulatória executável, comparável e auditável antes da introdução de microestrutura ou agentes adaptativos. Ele não demonstra que a arquitetura é desejável, não estima uma calibração ótima e não substitui validação empírica.

O Lab organiza o experimento em cinco tipos de objeto:

| Objeto | Função |
|---|---|
| dados | snapshot observado da companhia, com identificação e proveniência |
| variáveis | transformações declaradas dos dados primitivos ou de outras variáveis |
| cenário | trajetória exógena de ordens de uma companhia |
| especificação | regras de memória, capacidade e intrawindow |
| avaliação | resultado elementar de uma combinação especificação × cenário; comparativos reúnem várias avaliações mantendo um dos domínios fixo |

Cada cenário registra companhia, estratégia e sequência de ordens solicitadas. Cada especificação reúne fórmulas e parâmetros substituíveis para sinal, atualização da memória, decay, H₀, $H_{\max}$, saturação e Q/H. A separação é deliberada: cenários podem ser reutilizados entre especificações, e especificações podem ser avaliadas contra diferentes cenários sem incorporar a estratégia de ordens à regra regulatória.

Uma avaliação determinística segue o ciclo:

> snapshot e mapeamentos semânticos → primeira execução e abertura de W → cálculo e trava dos H da janela → submissão das ordens → execução ou rejeição parcial → alertas intraday de Q → consolidação no fechamento → encerramento por Q ou T e disclosure → atualização do estado

Os H permanecem travados durante a janela avaliada. Cada ordem é confrontada simultaneamente com $H_{\mathrm{gross}}$, $H_{\mathrm{net}+}$, $H_{\mathrm{net}-}$ e as restrições físicas aplicáveis. Quando a quantidade solicitada não é integralmente admissível, o engine executa a parcela possível e registra o residual rejeitado e sua causa. A trajetória regulatória contém apenas quantidades executadas; intenções rejeitadas permanecem disponíveis para auditoria, mas não alteram o estado.

O comparativo implementa dois contrafactuais controlados. Em **uma especificação contra vários cenários**, cada trajetória é normalizada pelo H resolvido para a própria companhia, permitindo comparar utilização relativa; os valores absolutos permanecem como metadados. Em **um cenário contra várias especificações**, o eixo utiliza quantidades absolutas de ações, porque cada especificação produz seus próprios H e Q sobre a mesma trajetória solicitada. A simetria metodológica consiste em manter um domínio fixo e variar o outro, não em impor a mesma normalização aos dois casos.

Cada resultado preserva a configuração utilizada, a trajetória solicitada, a trajetória executada, os alertas, a decisão de disclosure, as parcelas rejeitadas e os invariantes avaliados. Especificações concluídas recebem identidade reproduzível; alterações posteriores devem permanecer distinguíveis de execuções anteriores. Essa rastreabilidade permite reconstruir por que uma ordem foi executada, limitada ou rejeitada e quais regras produziram cada capacidade.

Os dados, cenários, fórmulas, parâmetros e especificações distribuídos previamente com o Lab são **fixtures de demonstração e teste visual**. Eles existem para exercitar caminhos do sistema, tornar diferenças observáveis e revelar inconsistências mecânicas. Não constituem estimativas empíricas, calibração plausível, recomendação regulatória ou evidência de que os valores escolhidos pertençam a uma região viável. Os dados atualmente disponíveis são insuficientes para sustentar qualquer dessas interpretações.

O estágio implementado deve, portanto, ser entendido como validação de consistência interna. Ele permite testar invariantes, semântica temporal, composição de fórmulas, limites físicos, reprodutibilidade e trajetórias extremas. Não permite concluir sobre spread, depth, impacto de preço, descoberta descentralizada, comportamento estratégico, welfare ou equilíbrio de mercado. Essas perguntas pertencem às camadas seguintes.

<a id="32-4-variable-h-lab"></a>
### 32.4. Variable/H Lab

O laboratório de variáveis permite comparar especificações de H mantendo o restante do mecanismo constante. Sua função é descobrir quais componentes acrescentam valor e quais apenas aumentam complexidade.

<a id="32-5-microestrutura"></a>
### 32.5. Microestrutura

Em seguida entram book, spread, depth, impacto, market makers e diferentes condições de liquidez.

<a id="32-6-agentes-adaptativos"></a>
### 32.6. Agentes adaptativos

Os agentes adaptativos ainda **não integram a implementação de referência**. Faltam dados públicos suficientemente granulares para estimar suas heurísticas e falta um baseline regulatório observado que permita distinguir aprendizagem plausível de comportamento arbitrariamente programado. Essa ausência deve ser tratada como limite atual da validação, não escondida como funcionalidade futura já resolvida.

Ainda assim, um laboratório multiagente é um instrumento possível e importante para testar a regulação antes de expor o mercado real ao mecanismo. Em vez de “lançar a bomba” e aprender apenas depois da adoção, o regulador pode construir companhias, market makers, investidores informados e menos informados, arbitradores, traders direcionais, terceiros sofisticados e um regulador fictícios, submetendo-os a diferentes especificações e condições de mercado.

Cada agente deve possuir heurísticas explícitas e capacidade de aprender com o regime. O objetivo não é apenas encontrar uma estratégia vencedora, mas entender **por que ela surgiu, qual parâmetro permitiu sua exploração e como o equilíbrio mudou depois que outros agentes aprenderam**.

Uma camada adversarial deve aproximar o caso limite de agentes altamente racionais: a companhia procura a política ótima dadas as regras e a reação esperada do mercado; participantes procuram a resposta ótima dadas as ações da companhia e as restrições que o protocolo lhe impõe. A dinâmica é iterativa: companhia adapta → mercado adapta → companhia readapta. O objetivo não é assumir racionalidade perfeita como descrição empírica, mas utilizá-la como stress test contra exploits estruturais.

O laboratório deve incluir cold start e adoção gradual. Um regime inicialmente raro pode produzir sinal muito mais saliente do que um regime já familiar. A validação deve observar se aprendizagem reduz overreaction, se market makers retiram liquidez antes da estabilização, se reputações heterogêneas geram equilíbrios distintos e se a companhia consegue realizar valor após repricing sem transformar o mecanismo em estratégia mecânica de fabricação de sinal.

O regulador também é experimentador. Ele compara configurações, não apenas pontos isolados, observa fronteiras de trade-off e procura configurações em que nenhuma estratégia exploratória consiga escala relevante sem pagar em capacidade, risco, observabilidade ou opcionalidade futura.

A implementação faz parte da metodologia da tese porque força decisões semânticas que o texto pode esconder. Se implementar o protocolo exigir exceções ad hoc que não derivam da arquitetura, isso é evidência de que a formalização ainda possui lacunas.

O laboratório integra a estratégia de validação da proposta: seus resultados relevantes devem ser incorporados à avaliação empírica do mecanismo, em vez de tratados como etapa externa à tese.

---

<a id="vii-conclusao"></a>
# VII. Conclusão

<a id="33-o-que-esta-tese-estabelece"></a>
## 33. O que esta tese estabelece

Esta tese não estabelece que o mecanismo é superior ao regime vigente.

Sua hipótese normativa é justamente investigar se a companhia pode receber liberdade para negociar mesmo quando possui informação privada, sem produzir lesão sistemática aos demais participantes. Essa liberdade não significa ausência de regras: significa dispensar uma proibição geral ou uma autorização individual, analisada caso a caso, quando a operação respeita W, H, Q, T, Treasury, disclosure e os demais invariantes do regime. A tese não presume que essa compatibilidade exista; ela constrói o teste capaz de aceitá-la ou rejeitá-la.

Não estabelece que disclosure elimina manipulação.

Não estabelece que lucro da Treasury seja sinônimo de welfare.

Não estabelece que maior observabilidade externa justifique automaticamente H maior.

Não estabelece que o modelo calendarizado seja superior ao rolling ou vice-versa.

Não estabelece valores ótimos para H, Q, T, decay ou qualquer outro parâmetro.

Ela estabelece algo mais limitado:

> **é possível decompor o problema da negociação própria do emissor sob assimetria informacional em uma arquitetura explícita de capacidade, posição, intervenção, utilização, disclosure, memória e aprendizagem suficientemente precisa para ser testada e rejeitada.**

A decomposição central é:

> Gross → intensidade de intervenção

> Net → alteração de posição

> W → janela regulatória comum a H, Q e T

> H → capacidade máxima

> Q → limiar de alerta e avaliação quantitativa no corte

> U → intensidade relativa da utilização

> $I_{\mathrm{issuer}}$ → memória informacional revelada pela ação observável do emissor

> $I_{\mathrm{market}}$ → informação economicamente relevante já observável externamente

> decay → envelhecimento da informação

> Treasury → restrição física da posição

> reputação → interpretação endógena do mercado, não parâmetro oficial

> segurança jurídica → previsibilidade ex ante para negociação de boa-fé dentro do regime, sem imunidade a manipulação

A partir dessa ontologia, diferentes especificações podem ser comparadas sem mudar a pergunta econômica.

---

<a id="34-conclusao-conceitual"></a>
## 34. Conclusão conceitual

A proposta parte de uma inversão simples.

A companhia não precisa deixar de conhecer melhor a si mesma para que o mercado seja protegido. Talvez seja possível permitir que ela utilize parte dessa vantagem, desde que a capacidade seja limitada e sua utilização produza informação observável em ritmo suficiente para impedir exclusividade indefinida.

> **A vantagem não é o problema. O problema é a forma como ela é exercida.**

A companhia pode ganhar se suas decisões forem boas e pode perder se forem ruins. O ganho pretendido não é permitir que ela capture sozinha todo o movimento, mas preservar a possibilidade de obter **parte** da valorização que ajudou a antecipar enquanto o mercado recebe o sinal, reage e participa do restante da descoberta de preço. Decisões bem-sucedidas podem preservar mais recursos corporativos para decisões futuras; decisões ruins consomem patrimônio e deterioram credibilidade.

Essa consequência só é aceitável com a segunda metade da arquitetura.

A companhia não recebe o direito de transformar informação privada em vantagem ilimitada; não recebe o direito de apagar intervenção por meio de reversão; não recebe derivativos para alavancar o próprio sinal; e não recebe garantia de que o mercado permanecerá passivo enquanto ela opera. Ao tentar ampliar a captura, consome H, aproxima-se de Q, antecipa o encerramento de W e revela mais da própria decisão. A arquitetura procura transformar escala em informação antes que o emissor consiga excluir o mercado do ajuste inteiro.

Ao contrário, sua atuação passa a produzir um histórico que outros participantes podem observar, interpretar, antecipar e eventualmente explorar.

O terceiro ganho pretendido é jurídico: uma companhia que negocia de boa-fé dentro do regime deve poder conhecer ex ante as condições operacionais que tornam sua atuação admissível, sem que o simples fato de conhecer melhor a própria realidade econômica transforme toda decisão de timing em uma zona de incerteza. Essa previsibilidade não protege fraude ou manipulação; ela delimita o espaço legítimo de atuação.

Isso cria uma tensão deliberada:

> **a companhia pode ser a primeira a saber e a primeira a agir — mas não pode ser a única a participar da descoberta de preço que sua informação produz.**

O desenho também assume explicitamente que nenhum conjunto finito de regras elimina toda margem estratégica. Sua premissa é mais exigente e mais realista: **nenhuma estratégia exploratória deve conseguir escala relevante sem consumir capacidade, assumir risco econômico, deixar rastro observável ou destruir a própria capacidade futura.** O mercado participa dessa disciplina ao aprender, antecipar, contrariar e precificar o comportamento do emissor.

A maior ameaça à proposta talvez seja justamente o sucesso desse mecanismo informacional. Se a ação identificada do emissor se tornar um sinal excessivamente dominante, o protocolo pode deteriorar liquidez, criar reflexividade, reduzir produção independente de informação ou permitir que reputação substitua fundamentos no curto prazo.

Por isso a pergunta final não é “como calibrar H para funcionar?”.

É:

> **Existe alguma região de desenho em que a companhia preserve capacidade economicamente relevante e juridicamente previsível de agir, o mercado preserve capacidade economicamente relevante de descobrir preço por conta própria, e a informação revelada pela atuação do emissor ajude mais do que desorganize esse processo?**

Se a resposta experimental for não, a arquitetura deve ser rejeitada.

Se for sim, então a negociação própria do emissor pode deixar de ser tratada apenas como fonte de conflito e passar também a ser investigada como instrumento de alocação de capital e produção de informação — sem exigir que a assimetria informacional desapareça antes que qualquer decisão econômica possa ocorrer.

Essa é a hipótese que o laboratório precisa tentar destruir.

---

<a id="35-referencias"></a>
## 35. Referências

<a id="ref-1"></a>
**Comissão de Valores Mobiliários (2022).** Resolução CVM nº 77, de 29 de março de 2022 — negociação de ações e aquisição de debêntures de própria emissão.  
[Acessar fonte](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol077.html)

<a id="ref-2"></a>
**Comissão de Valores Mobiliários (2021).** Resolução CVM nº 44, de 23 de agosto de 2021 — ato ou fato relevante e negociação na pendência de informação relevante não divulgada.  
[Acessar fonte](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol044.html)

<a id="ref-3"></a>
**European Commission (2016).** Commission Delegated Regulation (EU) 2016/1052, especialmente arts. 2 e 3 — disclosure, preço e limite de 25% do volume médio diário para o safe harbour de recompra.  
[Acessar fonte](https://eur-lex.europa.eu/eli/reg_del/2016/1052)

<a id="ref-4"></a>
**Glosten, L. R.; Milgrom, P. R. (1985).** *Bid, ask and transaction prices in a specialist market with heterogeneously informed traders*. Journal of Financial Economics, 14(1), 71–100.  
[Acessar fonte](https://doi.org/10.1016/0304-405X(85)90044-3)

<a id="ref-5"></a>
**Hasbrouck, J. (1991).** *Measuring the Information Content of Stock Trades*. The Journal of Finance, 46(1), 179–207.  
[Acessar fonte](https://doi.org/10.1111/j.1540-6261.1991.tb03749.x)

<a id="ref-6"></a>
**Grossman, S. J.; Stiglitz, J. E. (1980).** *On the Impossibility of Informationally Efficient Markets*. American Economic Review, 70(3), 393–408.  
[Acessar fonte](https://www.jstor.org/stable/1805228)

<a id="ref-7"></a>
**Brockman, P.; Chung, D. Y. (2001).** *Managerial timing and corporate liquidity: evidence from actual share repurchases*. Journal of Financial Economics, 61(3), 417–448.

<a id="ref-8"></a>
**Hillert, A.; Maug, E.; Obernberger, S. (2016).** *Stock Repurchases and Liquidity*. Journal of Financial Economics, 119(1), 186–209.

<a id="ref-9"></a>
**Ginglinger, E.; Hamon, J. (2007).** *Actual share repurchases, timing and liquidity*. Journal of Banking & Finance, 31(3), 915–938.

<a id="ref-10"></a>
**U.S. Securities and Exchange Commission (2002).** Rule 10b-18 and Purchases of Certain Equity Securities by the Issuer and Others — discussão da condição de volume e do limite de 25% do ADTV.  
[Acessar fonte](https://www.sec.gov/rules-regulations/2002/12/rule-10b-18-purchases-certain-equity-securities-issuer-others)

<a id="ref-11"></a>
**Comissão de Valores Mobiliários (2025).** Consulta Pública SDM 04/2025 — ajustes na Resolução CVM 77 com foco em negociação de ações de própria emissão.  
[Acessar fonte](https://conteudo.cvm.gov.br/cvm_institucional/audiencias_publicas/ap_sdm/2025/sdm0425.html)

<a id="ref-12"></a>
**Comissão de Valores Mobiliários (2023a).** Termo de Compromisso no PAS CVM 19957.014436/2022-29 — aquisição de ações de própria emissão pela Kepler Weber S.A. no período anterior à divulgação do ITR.  
[Acessar fonte](https://www.gov.br/cvm/pt-br/assuntos/noticias/2023/cvm-aceita-proposta-conjunta-de-mais-de-r-900-mil-apresentada-por-kepler-weber-s-a-e-seu-diretor-de-relacoes-com-investidores)

<a id="ref-13"></a>
**Comissão de Valores Mobiliários (2023b).** Julgamento de processos envolvendo empresas do grupo JBS e seus executivos — decisões sobre período vedado, uso de informação privilegiada e manipulação.  
[Acessar fonte](https://www.gov.br/cvm/pt-br/assuntos/noticias/2023/cvm-conclui-julgamento-de-processos-envolvendo-empresas-do-grupo-jbs-e-seus-executivos)

<a id="ref-14"></a>
**Comissão de Valores Mobiliários (2018).** Apreciação de propostas de Termo de Compromisso no PAS 19957.010277/2017-26 — operações com JSLG3 durante programa de recompra e antecipação atribuída a participantes da Haitong.  
[Acessar fonte](https://conteudo.cvm.gov.br/decisoes/2018/20180814_R1/20180814_D1023.html)

---

### Nota epistemológica

As referências acima cumprem funções diferentes. Literatura de microestrutura sustenta a plausibilidade de trades carregarem informação e de seleção adversa afetar formação de preços. Estudos de recompra mostram que o sinal de liquidez não é único. Regras dos Estados Unidos, União Europeia e Brasil demonstram que volume, timing, disclosure e negociação própria são objetos regulatórios reais. Nenhuma dessas fontes demonstra que a arquitetura proposta seja superior ao regime vigente ou que exista Θᵥ não vazio.

A validade institucional da proposta depende, portanto, de confrontar a arquitetura com implementação, dados e comportamento estratégico.
