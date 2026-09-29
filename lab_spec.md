# Issuer Protocol --- Especificação Consolidada do Laboratório

## 0. Função deste documento

Este documento especifica o laboratório regulatório derivado da tese
**Negociação própria do emissor sob assimetria informacional**. Sua
função é transformar a arquitetura conceitual em um sistema executável,
auditável e falsificável.

O laboratório não existe para demonstrar que a proposta funciona. Existe
para descobrir **se** funciona, **onde** funciona, **por que** funciona,
**como** quebra e quais propriedades são responsáveis por cada
resultado.

A implementação deve derivar desta especificação. Quando uma
implementação exigir uma exceção que não possa ser explicada pela
arquitetura, a exceção é tratada como evidência de lacuna conceitual,
não como justificativa para alterar silenciosamente o modelo.

> **A tese define a ontologia. O laboratório explora especificações e
> calibrações. Os resultados podem rejeitar ambas.**

O laboratório começa determinístico. Microestrutura e agentes
adaptativos são adicionados apenas depois que a máquina regulatória
puder ser executada, reproduzida e quebrada sem agentes sofisticados.

Os dados, cenários, fórmulas, parâmetros e especificações distribuídos
com a aplicação são fixtures de demonstração e teste visual. Eles não
constituem estimativas empíricas, calibração plausível, sugestão
regulatória ou evidência de viabilidade. Os dados atualmente disponíveis
são insuficientes para sustentar qualquer dessas interpretações.

------------------------------------------------------------------------

# I. Objetivo científico

## 1. Pergunta principal

Existe uma região de configurações regulatórias em que uma companhia
aberta consegue negociar ações de própria emissão sob vantagem
informacional de forma economicamente relevante sem produzir
deterioração inaceitável de integridade, liquidez, descoberta
descentralizada de preço ou explorabilidade estrutural?

Se `Θ` representa o espaço de configurações e `Θᵥ` a região considerada
viável, o laboratório deve admitir explicitamente:

> **Θᵥ pode ser vazio.**

Nenhum componente do software deve pressupor que existe uma calibração
correta.

## 2. Princípio adversarial

A principal propriedade-alvo do desenho é:

> **Nenhuma estratégia exploratória deve conseguir escala relevante sem
> consumir capacidade, assumir risco econômico, deixar rastro observável
> ou destruir a própria capacidade futura.**

Essa frase não corresponde a um teste booleano isolado. O laboratório
deve decompor a propriedade em métricas observáveis e procurar
violações.

Uma estratégia é especialmente preocupante quando combina:

-   baixo custo econômico;
-   baixo risco;
-   alta escalabilidade;
-   repetibilidade;
-   baixa observabilidade;
-   preservação da capacidade de repetir a estratégia;
-   retorno derivado principalmente de uma propriedade mecânica do
    protocolo.

O objetivo não é impedir lucro. Companhia e mercado podem ganhar
dinheiro. O objetivo é detectar **exploits estruturais**.

## 3. Dois pares de ação e reação

O laboratório deve modelar duas direções estratégicas:

**Companhia → mercado**

A companhia pode explorar informação, capacidade, timing, disclosure,
Treasury, impacto de preço, reputação e reação esperada do mercado.

**Mercado → companhia**

O mercado pode aprender, copiar, antecipar, contrariar, retirar
liquidez, ampliar spreads, explorar restrições regulatórias da companhia
ou tentar encurralá-la.

O protocolo deve ser testado contra comportamento racional dos dois
lados, não contra cooperação presumida.

Em fases posteriores:

> `companhia adapta → mercado adapta → companhia readapta → mercado readapta`

O regulador ocupa um terceiro nível: modifica a regra observando como os
dois lados respondem.

------------------------------------------------------------------------

# II. Separação entre arquitetura, especificação e calibração

## 4. Arquitetura

São conceitos estruturais do regime:

-   Gross e Net são objetos diferentes;
-   existem `H_gross`, `H_net+` e `H_net−`;
-   H é hard cap;
-   Q gera alerta quantitativo intraday, é avaliado sobre o estado consolidado no corte para disclosure e `Q ≤ H`;
-   U mede utilização relativa de H;
-   SELL é limitado pela Treasury;
-   Treasury não pode ser negativa;
-   reversão não restitui Gross;
-   disclosure altera o estado observável, mas não deve reciclar
    capacidade de forma incompatível com a topologia temporal;
-   decay atua sobre estados de memória/informação, não diretamente
    sobre H;
-   Fato Relevante permanece evento externo à máquina de capacidade;
-   o regime-base não permite exposição derivativa da companhia ao preço
    da própria ação;
-   o ticker/emissor é a unidade regulada; setor pode fornecer
    variáveis, mas não recebe H.

Essas propriedades não são sliders.

## 5. Especificação

São hipóteses substituíveis:

-   função de cada H;
-   definição de H₀ e Hmax;
-   função de saturação;
-   função de decay;
-   transformação `U → estado futuro`;
-   uso ou não de `I_issuer`;
-   uso ou não de `I_market`;
-   uso ou não de `A_gross`;
-   bônus moderado por plano público voluntário;
-   efeito de persistência direcional;
-   efeito de reversão;
-   assimetria entre capacidade BUY e SELL;
-   topologia calendarizada ou rolling;
-   eventual intervalo adicional de reação C;
-   regra exata de cut-off do disclosure após Q;
-   variáveis de familiaridade e reputação quando agentes forem
    introduzidos.

## 6. Calibração

São valores ou parâmetros numéricos:

-   H₀;
-   Hmax;
-   `ρ = Q/H`;
-   T;
-   parâmetros de saturação;
-   parâmetros de decay;
-   intensidade do bônus de plano;
-   velocidade de progressão de H;
-   degradação por reversão;
-   escalas de liquidez;
-   parâmetros de impacto;
-   parâmetros comportamentais dos agentes.

Nenhum valor deve ser rotulado como "ótimo" sem critério e evidência
explícitos.

------------------------------------------------------------------------

# III. Núcleo de estado

## 7. Estado do emissor

O engine deve representar o estado de um emissor `i` no instante `t` por
um objeto explícito e serializável.

### 7.1. Identidade e mercado

Campos mínimos:

-   `issuer_id`;
-   `ticker`;
-   timestamp;
-   preço de referência;
-   total de ações emitidas;
-   ações em circulação;
-   ADV/ADTV;
-   turnover;
-   free float;
-   volatilidade;
-   spread, quando disponível;
-   depth, quando disponível;
-   capitalização, quando disponível;
-   demais variáveis primitivas habilitadas.

Todo dado deve carregar proveniência.

Total emitido, ações em circulação, free float e Treasury são campos semânticos distintos. Vale `ações emitidas = ações em circulação + Treasury` e `free float ≤ ações em circulação`; em geral, `free float + Treasury` não representa o total emitido.

### 7.2. Posição física

-   `treasury`;
-   `treasury_max` ou limite físico/societário aplicável;
-   caixa ou restrição financeira, se a especificação utilizar;
-   posição inicial da janela.

Restrições mínimas:

> `Treasury ≥ 0`

> `SELL ≤ Treasury disponível`

Não existe short verdadeiro da própria ação no regime-base.

### 7.3. Capacidade

O estado deve armazenar separadamente:

-   `H_gross_calculated` e `H_gross_effective`;
-   `H_net_plus_calculated` e `H_net_plus_effective`;
-   `H_net_minus_calculated` e `H_net_minus_effective`;
-   H₀ correspondente a cada dimensão;
-   Hmax correspondente a cada dimensão;
-   capacidade consumida;
-   capacidade residual.

A capacidade de uma dimensão nunca deve ser inferida implicitamente de
outra.

H calculado é o resultado da função da especificação. H efetivo aplica
as restrições físicas e societárias externas à função. No mínimo:

`H_net_minus_effective = min(H_net_minus_calculated, treasury_available)`

Um limite de posição própria pode restringir `H_net_plus_effective`
quando a especificação experimental o habilitar.

### 7.4. Thresholds

-   `Q_gross`;
-   `Q_net_plus`;
-   `Q_net_minus`;
-   `rho_gross`;
-   `rho_net_plus`;
-   `rho_net_minus`.

A relação típica é:

`Q_j = rho_j × H_j`, com `0 < rho_j ≤ 1`.

Q é trigger, não quantidade executada.

No baseline intrawindow, cruzar Q durante a sessão gera alerta e registro auditável. A obrigação quantitativa de disclosure é decidida no fechamento a partir de Gross, Net+ e Net− consolidados. Gross não retorna abaixo do limiar; uma exposição Net pode cruzar Q e recuar antes do corte sem produzir disclosure por essa dimensão.

### 7.5. Execução acumulada

Por janela:

-   BUY acumulado;
-   SELL acumulado;
-   Gross acumulado;
-   Net acumulado;
-   Net positivo relevante;
-   Net negativo relevante;
-   VWAP de BUY;
-   VWAP de SELL;
-   timestamps das execuções;
-   custo/receita;
-   implementation shortfall quando houver microestrutura.

Definições:

`Gross = BUY + SELL`

`Net = BUY − SELL`

Uma reversão pode reduzir Net, mas não Gross.

Cada ordem deve preservar quantidade solicitada, quantidade executada e
quantidade rejeitada. Se a solicitação exceder qualquer capacidade
residual ou restrição física, o engine executa somente a maior parcela
simultaneamente admissível e registra o residual com o primeiro limite
vinculante. A parcela rejeitada não altera Gross, Net, Treasury, U ou a
memória futura.

### 7.6. Utilização

Para cada dimensão:

`U_j = execução_relevante_j / H_j`

Devem existir, quando aplicáveis:

-   `U_gross`;
-   `U_net_plus`;
-   `U_net_minus`.

U é intensidade normalizada da ação, não "informação verdadeira" sobre
fundamentos.

### 7.7. Estados de memória e informação

O engine deve permitir estados modulares, incluindo:

-   `I_issuer_plus`;
-   `I_issuer_minus`;
-   `I_market`;
-   `A_gross`;
-   persistência direcional;
-   frequência/intensidade de reversão;
-   histórico de disclosures;
-   familiaridade operacional.

Esses estados devem ser independentes o suficiente para serem removidos
sem quebrar a ontologia central.

### 7.8. Plano público voluntário

O laboratório deve permitir um objeto `PublicPlan`, opcional, com pelo
menos:

-   existência;
-   direção ou escopo, quando aplicável;
-   quantidade ou valor máximo anunciado;
-   duração;
-   data de anúncio;
-   data de expiração;
-   utilização acumulada do plano;
-   status.

A companhia **não é obrigada pelo modelo a anunciar um plano de
recompra**.

Se uma especificação usar o plano como input de H, o efeito deve ser
parametrizado como bônus moderado ou outra função explicitamente
limitada.

Invariante de desenho:

> **anunciar X não concede automaticamente H = X.**

O plano pode reduzir surpresa e justificar ajuda limitada à capacidade
inicial. A continuidade da progressão deve depender de outros estados,
especialmente execução efetiva, conforme a especificação testada.

------------------------------------------------------------------------

# IV. Variable Builder

## 8. Contrato de uma variável

Toda variável usada pelo laboratório deve ser um objeto com metadados, e
não apenas um número.

Campos recomendados:

-   `id`;
-   nome;
-   descrição econômica;
-   categoria;
-   fonte;
-   unidade;
-   frequência;
-   timestamp;
-   transformação;
-   normalização;
-   bounds;
-   lag;
-   política de missing data;
-   cobertura;
-   confiabilidade/proveniência;
-   valor bruto;
-   valor transformado.

Categorias mínimas:

-   mercado;
-   posição;
-   execução;
-   informação/memória;
-   plano público;
-   histórico;
-   externa;
-   experimental.

## 9. Variáveis primitivas

Candidatas iniciais:

-   ADV/ADTV;
-   turnover;
-   free float;
-   preço;
-   volatilidade;
-   spread;
-   depth;
-   Treasury;
-   Treasury disponível;
-   capitalização;
-   caixa, se habilitado;
-   commodity;
-   câmbio;
-   juros;
-   existência e dimensão de plano público.

Nenhuma relação causal é presumida pelo fato de uma variável existir no
catálogo.

## 10. Variáveis derivadas

Candidatas:

-   `U_gross`;
-   `U_net+`;
-   `U_net−`;
-   `I_issuer+`;
-   `I_issuer−`;
-   `I_market`;
-   `A_gross`;
-   persistência direcional;
-   reversão;
-   churn;
-   familiaridade;
-   idade do último disclosure;
-   utilização do plano público.

## 11. Transformações

O builder deve permitir comparar, pelo menos:

-   identidade;
-   normalização min/max;
-   razão contra uma base;
-   log;
-   potência;
-   função linear limitada;
-   piecewise;
-   função saturante;
-   função convexa;
-   função côncava;
-   min;
-   max;
-   clamp;
-   composição explícita.

Cada transformação deve ser inspecionável. Expressões livres podem
existir, mas devem ser avaliadas por parser restrito e nunca por `eval`.

------------------------------------------------------------------------

# V. H Builder

## 12. Três pipelines independentes

O laboratório deve possuir pipelines separadas:

`H_gross = F_gross(estado, variáveis selecionadas)`

`H_net+ = F_plus(estado, variáveis selecionadas)`

`H_net− = F_minus(estado, variáveis selecionadas)`

Uma alteração em uma pipeline não deve modificar silenciosamente as
outras.

## 13. H₀ e Hmax

Cada dimensão deve possuir:

-   referência estrutural H₀;
-   teto Hmax;
-   H calculado;
-   H efetivo após restrições físicas.

Uma representação conceitual possível é:

`H_calculated = H₀ + s × (Hmax − H₀)`

onde `s` é uma escala produzida pela especificação.

Isso é uma família de funções, não a fórmula obrigatória.

## 14. Progressão por persistência

O laboratório deve permitir testar se execuções direcionais sucessivas
produzem crescimento de H:

-   linear;
-   côncavo;
-   convexo/acelerado;
-   saturante;
-   piecewise;
-   nenhum crescimento.

A hipótese de crescimento acelerado deve ser testada especialmente
contra dois problemas opostos:

1.  **rampa excessivamente lenta:** uma companhia com programa
    economicamente razoável precisa realizar número absurdo de pequenas
    operações apenas para "aquecer" H;
2.  **ratchet explorável:** executar passa a ser uma forma barata de
    fabricar capacidade futura.

Persistência não deve ser interpretada automaticamente como acerto
fundamental.

## 15. Reversão

O laboratório deve permitir especificações em que uma mudança de
direção:

-   não altera H futuro além do consumo de Gross;
-   reduz parcialmente a progressão acumulada na direção anterior;
-   reduz capacidade inicial na direção oposta;
-   reinicia parcialmente um estado de persistência;
-   produz efeito dependente da velocidade/intensidade da reversão.

O objetivo é estudar o trade-off:

> impedir captura trivial do próprio sinal sem tornar a companhia
> regulatoriamente incapaz de sair de uma posição legítima.

O mercado não deve receber, por desenho, uma forma trivial de encurralar
a companhia apenas porque conhece suas restrições de reversão.

## 16. Churn

Uma sequência de BUY/SELL alternados pode gerar Gross alto e Net baixo.

O laboratório deve impedir mecanicamente que offset de Net apague Gross.

Também deve testar se qualquer variável de atividade, como `A_gross`,
cria incentivo perverso:

> churn → atividade observada → H futuro maior.

`A_gross` deve poder ser completamente desligado. Se existir, uma
especificação conservadora é permitir efeito apenas sobre `H_gross`,
nunca automaticamente sobre capacidade líquida.

------------------------------------------------------------------------

# VI. Q, T, disclosure e tempo

## 17. Q

Para cada dimensão, Q responde:

> a partir de que intensidade a atividade deve gerar alerta e ser
> submetida à avaliação quantitativa no corte?

Q não é hard cap. H é hard cap.

Atravessar Q deve criar `QCrossed`. Se uma dimensão Net retornar abaixo do limiar, deve criar `QReturnedBelow`. O cruzamento permanece no log; a obrigação pública não é irrevogável e será decidida no corte.

## 18. Conteúdo do disclosure

O laboratório deve distinguir:

-   threshold que disparou a obrigação;
-   execução efetivamente acumulada no cut-off.

O disclosure não deve registrar falsamente "execução = Q" quando a
companhia executou mais do que Q antes do cut-off.

Baseline de informação a testar:

-   BUY acumulado;
-   SELL acumulado;
-   Gross;
-   Net;
-   U relevante;
-   período;
-   preço/VWAP quando aplicável;
-   capacidade H relevante;
-   trigger que causou o disclosure.

A tese não exige divulgação da informação privada ou da tese de
valuation que motivou a operação.

O fato público é a ação econômica da companhia. A inferência pertence ao
mercado.

## 19. W e T

W é a janela regulatória iniciada pela primeira execução elegível. H, Q e T pertencem à mesma W: H é calculado e travado na abertura; Q é definido sobre os H da janela; e T começa a correr com a abertura e limita sua duração.

T é o **prazo temporal máximo de W e trigger temporal de disclosure**, não "um pregão".

O laboratório deve aceitar T em unidades flexíveis, inclusive:

-   dias;
-   uma semana;
-   quinze dias;
-   um mês;
-   outras durações experimentais.

Função:

> **T impede silêncio prolongado; Q impede intensidade excessiva sem
> disclosure.**

No baseline, a confirmação de Q no corte ou o vencimento de T produz disclosure e encerra W. Capacidade não utilizada expira, e a próxima W só pode começar no pregão seguinte.

## 20. Cut-off e decisão de disclosure

O baseline avalia Q no fechamento da sessão. O engine registra cruzamentos intraday como alertas, permite execução residual até H e compara os valores consolidados com Q no corte. Para Gross, o cruzamento persiste porque a dimensão é acumulativa. Para Net+ e Net−, uma operação oposta pode afastar a exposição do limiar antes do fechamento.

Outros cortes podem ser estudados como especificações alternativas, mas devem declarar se avaliam pico intraday, primeira ultrapassagem ou posição consolidada. Essas grandezas não podem ser tratadas como equivalentes.

## 21. Topologia rolling

No modelo rolling:

-   a primeira execução elegível abre W;
-   execuções posteriores pertencem à mesma W até seu encerramento;
-   não existem W sobrepostas para o mesmo emissor;
-   T é contado a partir da primeira execução;
-   o corte pode confirmar disclosure por Q antes do prazo máximo T e encerrar W;
-   o vencimento de T também produz disclosure e encerra W;
-   o encerramento produz transição explícita de estado;
-   a próxima W só pode nascer no pregão seguinte.

Risco a testar: exploração das transições endógenas e inferência do
estado privado da janela.

## 22. Topologia calendarizada

No modelo calendarizado:

-   a primeira execução elegível ativa W;
-   H é calculado e travado para W;
-   além de Q e T, uma fronteira pública de calendário pode antecipar o encerramento;
-   execução consome capacidade dentro de W;
-   disclosure e encerramento não reciclam H no mesmo pregão;
-   a fronteira externa é pública e previsível.

Risco a testar: sazonalidade, antecipação e exploração do relógio
regulatório.

## 23. Intervalo adicional C

C é uma hipótese opcional de intervalo adicional sem nova intervenção
após determinado disclosure/transição.

O laboratório deve permitir `C = 0`.

C não deve ser introduzido como necessidade estrutural. Sua utilidade
deve ser demonstrada por testes.

------------------------------------------------------------------------

# VII. State Engine determinístico

## 24. Eventos

O núcleo deve ser event-driven. Eventos mínimos:

-   `MarketSnapshotUpdated`;
-   `PublicPlanAnnounced`;
-   `PublicPlanExpired`;
-   `WindowOpened`;
-   `OrderSubmitted`;
-   `TradeExecuted`;
-   `QCrossed`;
-   `QReturnedBelow`;
-   `HExhausted`;
-   `DisclosureEvaluated`;
-   `DisclosurePublished`;
-   `WindowClosed`;
-   `StateRecalculated`;
-   `DecayApplied`;
-   `RelevantFactObserved`;
-   `SessionOpened`;
-   `SessionClosed`.

Eventos devem ser imutáveis depois de registrados.

## 25. Transição

Toda mudança de estado deve poder ser descrita como:

`S_t + evento + regra → S_t+1`

Cada transição deve registrar:

-   estado anterior;
-   evento;
-   configuração ativa;
-   definição e fingerprint da função usada;
-   estado posterior;
-   invariantes avaliados;
-   warnings;
-   motivo da transição.

## 26. Reprodutibilidade

Uma simulação deve ser reproduzível a partir de:

-   estado inicial;
-   dataset/snapshot;
-   configuração;
-   sequência de eventos;
-   seed, quando houver aleatoriedade;
-   fingerprint do engine.

O mesmo input deve produzir o mesmo output no modo determinístico.

------------------------------------------------------------------------

# VIII. Invariantes

## 27. Invariantes mecânicos obrigatórios

O test suite deve garantir, no mínimo:

1.  `Treasury ≥ 0`.
2.  SELL nunca excede Treasury disponível.
3.  Não existe short próprio no regime-base.
4.  `Gross = BUY + SELL`.
5.  `Net = BUY − SELL`.
6.  Reversão não restitui Gross.
7.  `Gross_W ≤ H_gross`.
8.  Net positivo relevante não excede `H_net+`.
9.  Net negativo relevante não excede `H_net−`.
10. `Q_j ≤ H_j`.
11. Cruzar Q intraday não substitui a avaliação consolidada no corte.
12. Alertas de cruzamento e retorno abaixo de Q permanecem auditáveis.
13. Fragmentação de ordens não reinicia Q.
14. Fragmentação de ordens não reinicia H.
15. Disclosure não recicla capacidade dentro da mesma janela/ciclo
    quando a topologia proíbe.
16. H da janela corrente não é retroativamente alterado por informação
    produzida dentro da própria janela, salvo se uma especificação
    declarar explicitamente uma transição permitida.
17. SELL não cria Treasury.
18. Fato Relevante não concede/reset H automaticamente.
19. Plano público não concede H ilimitado.
20. Derivativos próprios permanecem fora do regime-base.
21. Terceiro lucrar ou perder não altera H por padrão.
22. Estados futuros são calculados apenas em transições autorizadas.

## 28. Invariantes de auditabilidade

-   nenhuma execução sem timestamp;
-   nenhuma mudança de H sem causa registrada;
-   nenhuma variável sem proveniência;
-   nenhuma função de H sem definição e fingerprint da configuração;
-   nenhum disclosure sem conteúdo reconstruível;
-   nenhuma transição silenciosa;
-   nenhum clamp oculto;
-   nenhuma correção automática de input sem warning.

------------------------------------------------------------------------

# IX. Trajectory Runner

## 29. Objetivo

Antes de modelar comportamento estratégico, o laboratório deve executar
trajetórias deliberadas para entender a máquina.

Uma trajetória é uma sequência explícita de ações e eventos.

## 30. Biblioteca mínima de trajetórias

### Persistência

-   BUY;
-   BUY → BUY;
-   BUY → BUY → BUY → BUY;
-   SELL persistente a partir de Treasury positiva.

### Reversão

-   BUY → SELL;
-   BUY → BUY → SELL;
-   BUY → BUY → BUY → SELL;
-   BUY → SELL → BUY → SELL.

### Churn

-   Gross alto, Net próximo de zero;
-   alternância de pequenas ordens;
-   alternância próxima aos thresholds Q.

### Inatividade

-   execução seguida de silêncio;
-   decay longo;
-   expiração por T;
-   janela sem utilização adicional.

### Thresholds

-   execução em `Q − ε`;
-   execução em Q;
-   execução em `Q + ε`;
-   execução até H;
-   várias ordens cuja soma cruza Q.

### Treasury

-   Treasury = 0;
-   Treasury próxima do máximo;
-   SELL até zerar Treasury;
-   BUY próximo do limite físico.

### Plano público

-   sem plano;
-   plano pequeno;
-   plano grande com bônus limitado;
-   anúncio sem execução;
-   execução parcial;
-   expiração;
-   anúncio exagerado usado para tentar obter capacidade.

### Escala anual

Cenário obrigatório:

> companhia pretende recomprar R\$100 milhões ao longo de um ano.

Variar:

-   H₀;
-   Hmax;
-   progressão;
-   Q/H;
-   T;
-   liquidez;
-   plano público;
-   frequência de execução.

Objetivo: medir se o protocolo permite execução economicamente razoável
sem exigir "capacity heating" artificial.

------------------------------------------------------------------------

# X. Specification Runner

## 31. Comparação ceteris paribus

O laboratório deve permitir rodar a mesma trajetória, dataset e estado
inicial contra várias especificações.

Exemplos:

-   H linear × H acelerado;
-   com × sem plano público;
-   com × sem `I_market`;
-   com × sem `A_gross`;
-   reversão neutra × reversão degradante;
-   Q/H baixo × alto;
-   T curto × longo;
-   calendarizado × rolling.

A comparação deve identificar exatamente quais diferenças de regra
produziram diferenças de resultado.

## 32. Sweep paramétrico

O sistema deve aceitar:

-   grid search;
-   random search;
-   Latin hypercube ou método equivalente posteriormente;
-   otimização/adversarial search posteriormente.

O objetivo inicial não é "achar o ótimo", mas mapear:

-   regiões estáveis;
-   regiões inviáveis;
-   fronteiras;
-   descontinuidades;
-   parâmetros irrelevantes;
-   interações inesperadas.

------------------------------------------------------------------------

# XI. Métricas

## 33. Companhia

Métricas mínimas:

-   capacidade total disponível;
-   capacidade efetivamente utilizada;
-   tempo para executar objetivo econômico;
-   quantidade de janelas necessárias;
-   quantidade de disclosures;
-   custo de implementação;
-   slippage;
-   retorno de Treasury;
-   exposição;
-   capital comprometido;
-   capacidade futura preservada/destruída;
-   custo de reversão;
-   distância entre objetivo anual e execução possível;
-   previsibilidade operacional.

## 34. Mercado

Quando microestrutura existir:

-   spread;
-   depth;
-   volume;
-   impacto temporário;
-   impacto permanente;
-   volatilidade;
-   liquidez retirada após sinal;
-   velocidade de incorporação;
-   overshooting;
-   reversão;
-   participação de market makers;
-   concentração de P&L;
-   produção independente de informação.

## 35. Informação e aprendizagem

-   intensidade do sinal;
-   familiaridade;
-   reação condicionada ao histórico do emissor;
-   erro de inferência;
-   tempo de aprendizado;
-   reputação;
-   diferença entre reação inicial e reação após repetição;
-   capacidade preditiva do histórico de BUY/SELL;
-   dependência do preço em relação ao sinal do emissor.

## 36. Exploitability

Toda estratégia adversarial deve produzir um perfil:

-   P&L;
-   capital em risco;
-   H consumido;
-   Gross consumido;
-   tempo necessário;
-   número de disclosures;
-   observabilidade;
-   capacidade futura perdida;
-   possibilidade de repetição;
-   sensibilidade à resposta do outro lado.

Uma métrica composta de exploit pode ser criada para exploração, mas não
deve substituir os componentes.

------------------------------------------------------------------------

# XII. Testes adversariais

## 37. Companhia contra o protocolo

Testar explicitamente:

-   fragmentação para evitar Q;
-   ficar em `Q − ε`;
-   churn para fabricar estado;
-   plano público inflado para obter H;
-   execução mínima repetida para aquecer H;
-   BUY persistente apenas para aumentar capacidade;
-   BUY para produzir reação seguido de SELL;
-   repetição `BUY → repricing → SELL`;
-   alternância para reconstruir capacidade líquida;
-   exploração de reset;
-   exploração de T;
-   exploração da diferença entre H_gross e H_net;
-   tentativa de usar Treasury como canal de arbitragem regulatória.

## 38. Mercado contra a companhia

Testar:

-   copy trading;
-   front-running baseado apenas em informação pública e previsível;
-   retirada coordenada/independente de liquidez;
-   ampliação de spread;
-   contrarian trading;
-   venda contra BUY do emissor;
-   exploração de conhecimento sobre H residual;
-   exploração de incapacidade regulatória de reversão;
-   tentativa de encurralar companhia com H_net− reduzido;
-   antecipação de disclosure por relógio calendarizado;
-   inferência de abertura/fechamento de W rolling.

## 39. Signal fabrication

Cenário central:

1.  companhia não possui convicção fundamental positiva;
2.  executa BUY porque espera que sua identidade gere repricing;
3.  mercado reage;
4.  companhia tenta vender Treasury mais caro.

Comparar com:

1.  companhia possui convicção econômica genuína;
2.  executa BUY;
3.  mercado reprifica;
4.  companhia considera o novo preço caro e realiza parte da posição.

O engine não deve fingir observar intenção. O objetivo é verificar se
**padrões comportamentais e custos estruturais** tornam a primeira
estratégia barata, escalável e repetível.

Testar como defesas:

-   Gross não restituível;
-   H incremental;
-   progressão dependente de persistência;
-   degradação por reversão;
-   H_net− inicial reduzido após BUY persistente;
-   disclosure;
-   aprendizagem do mercado;
-   reputação;
-   limites de Treasury.

------------------------------------------------------------------------

# XIII. Microestrutura

## 40. Entrada da microestrutura

A microestrutura só deve ser acoplada depois que o state engine passar
nos invariantes.

Componentes:

-   limit order book simplificado;
-   bid/ask;
-   depth;
-   market/limit orders;
-   price-time priority;
-   market makers;
-   impacto;
-   cancelamento/retirada de liquidez;
-   diferentes regimes de liquidez.

## 41. Identificação do emissor

O laboratório deve distinguir claramente:

-   informação privada da companhia;
-   ação identificada da companhia;
-   disclosure agregado do protocolo.

O mercado não recebe automaticamente a tese de valuation da companhia.

O dado observável é algo como:

> "o emissor comprou/vendeu determinada quantidade sob determinada
> capacidade."

A interpretação é produzida pelos agentes.

------------------------------------------------------------------------

# XIV. Laboratório multiagente

## 42. Agentes mínimos

-   emissor;
-   market makers;
-   investidores informados;
-   investidores menos informados;
-   arbitradores;
-   traders direcionais;
-   terceiros sofisticados;
-   regulador.

## 43. Estrutura de agente

Cada agente deve possuir:

-   estado observado;
-   informação privada, quando aplicável;
-   objetivo;
-   restrições;
-   política;
-   heurísticas explícitas;
-   memória;
-   expectativa sobre outros agentes;
-   ação;
-   resultado;
-   atualização da heurística.

As heurísticas aprendidas devem ser registradas. O laboratório não deve
depender exclusivamente de políticas opacas.

## 44. Racionalidade

Começar com agentes simples.

Depois adicionar uma camada de **racionalidade adversarial extrema**
como stress test:

-   emissor procura melhor resposta;
-   mercado procura melhor resposta;
-   ambos conhecem as regras;
-   ambos aprendem.

Racionalidade perfeita é um caso limite para descobrir exploits, não uma
afirmação sobre comportamento humano real.

## 45. Aprendizagem e meta

O sistema deve observar:

`parâmetros → incentivos → estratégias → aprendizagem → meta → equilíbrio/ciclo/instabilidade`

Resultados possíveis incluem:

-   equilíbrio relativamente estável;
-   múltiplos equilíbrios;
-   ciclos;
-   corrida adaptativa;
-   colapso de liquidez;
-   sinal progressivamente ignorado;
-   sinal excessivamente dominante;
-   regime economicamente inútil;
-   exploit persistente.

------------------------------------------------------------------------

# XV. Regulador como experimentador

## 46. Papel

O regulador não é inicialmente um agente que "vence" o jogo. É o
operador do espaço experimental.

Ele deve poder:

-   criar configuração;
-   duplicar configuração;
-   alterar uma hipótese;
-   executar a mesma trajetória;
-   comparar resultados;
-   observar violações;
-   registrar hipótese;
-   modificar parâmetro;
-   rerodar;
-   comparar delta.

## 47. Registro de experimento

Cada experimento deve registrar:

-   ID;
-   pergunta;
-   hipótese;
-   baseline;
-   configuração alternativa;
-   dataset;
-   trajetória/agentes;
-   seed;
-   métricas escolhidas;
-   resultados;
-   invariantes;
-   warnings;
-   interpretação humana;
-   status: suporta / enfraquece / inconclusivo / rejeita hipótese.

O laboratório deve preservar resultados negativos.

------------------------------------------------------------------------

# XVI. Arquitetura de software recomendada

## 48. Camadas

### `domain/`

Objetos econômicos e regulatórios puros:

-   IssuerState;
-   MarketState;
-   Treasury;
-   Capacity;
-   Threshold;
-   Window;
-   Disclosure;
-   PublicPlan;
-   Execution;
-   Event.

Sem dependência de UI.

### `variables/`

-   catálogo;
-   transforms;
-   normalização;
-   proveniência;
-   derived variables;
-   missing-data policies.

### `capacity/`

-   H builders;
-   H₀;
-   Hmax;
-   saturation;
-   persistence;
-   reversal;
-   plan bonus.

### `engine/`

-   state machine;
-   event processing;
-   invariants;
-   temporal topology;
-   disclosure;
-   decay.

### `experiments/`

-   trajectories;
-   sweeps;
-   comparison;
-   adversarial scenarios;
-   experiment registry.

### `market/`

Fase posterior:

-   book;
-   execution;
-   impact;
-   liquidity;
-   market makers.

### `agents/`

Fase posterior:

-   issuer;
-   investors;
-   arbitrageurs;
-   regulator;
-   learning/heuristics.

### `data/`

-   adapters;
-   snapshots;
-   provenance;
-   CVM;
-   market data;
-   synthetic fixtures.

### `api/`

Contrato entre engine e frontend.

### `tests/`

-   invariants;
-   trajectories;
-   regression;
-   property-based;
-   adversarial;
-   reproducibility.

------------------------------------------------------------------------

# XVII. Contrato mínimo entre frontend e engine

## 49. Regra fundamental

O frontend não calcula a regra regulatória.

Ele:

-   edita configurações;
-   envia experimentos;
-   recebe estados/resultados;
-   visualiza;
-   compara;
-   audita.

Toda lógica econômica deve existir no engine.

## 50. Objetos de API conceituais

### DataSnapshot

Contém dados observados, mapeamentos semânticos, proveniência e data de
referência. Treasury e preço de referência pertencem ao snapshot, não à
especificação.

### Specification

Contém:

-   topologia;
-   H builders;
-   variáveis habilitadas;
-   Q;
-   T;
-   C;
-   disclosure;
-   decay;
-   plano;
-   reversão;
-   limites.

### Scenario

Contém:

-   emissor;
-   nome da estratégia;
-   trajetória exógena de ordens;
-   horizonte;
-   seed.

### Run

Contém:

-   data_snapshot_id;
-   specification_id;
-   scenario_id;
-   engine_fingerprint;
-   event log;
-   state history;
-   metrics;
-   invariant results;
-   warnings.

### Comparison

Contém:

-   runs comparadas;
-   variáveis alteradas;
-   deltas;
-   métricas;
-   fronteiras.

------------------------------------------------------------------------

# XVIII. Frontend: diretriz de reaproveitamento

## 51. Base visual

A implementação anterior deve servir como **referência de
apresentação**, especialmente a bancada do regulador.

São propriedades úteis a preservar conceitualmente:

-   regulador como página principal;
-   configuração selecionável e duplicável;
-   edição à esquerda e consequência viva à direita;
-   atualização imediata ao alterar parâmetros;
-   comparação de múltiplas configurações;
-   aprofundamento por ticker;
-   timeline/auditoria;
-   dados de mercado com proveniência;
-   separação visual entre configuração, comportamento e auditoria;
-   painéis com scroll independente;
-   ausência de botão "Aplicar" quando a atualização pode ser
    determinística e imediata.

O frontend antigo **não é referência semântica**. Conceitos históricos
como Dmax, progressão antiga, janelas intraday e cooldown antigo não
devem sobreviver apenas porque já possuem widgets.

O reaproveitamento deve ser:

> **layout e interação primeiro; semântica somente quando ainda
> coincidir com a tese.**

## 52. Nova bancada do regulador

A bancada deve evoluir naturalmente para:

**Painel esquerdo --- construção da regra**

-   dataset/snapshot;
-   Variable Builder;
-   H_gross Builder;
-   H_net+ Builder;
-   H_net− Builder;
-   Q/T/topologia;
-   plano público;
-   persistência/reversão;
-   configuração do experimento.

**Painel direito --- referência viva**

-   capacidades resultantes;
-   trajetória;
-   Gross/Net;
-   Treasury;
-   U;
-   Q/disclosures;
-   estados informacionais;
-   comparação com baseline;
-   invariantes;
-   warnings;
-   audit trail.

O objetivo é manter a qualidade de apresentação do protótipo sem deixar
que sua arquitetura antiga determine o novo modelo.

------------------------------------------------------------------------

# XIX. Ordem de implementação

## 53. Milestone 1 --- domínio e invariantes

Entregáveis:

-   modelos de estado;
-   eventos;
-   Gross/Net;
-   Treasury;
-   H triplo;
-   Q/U;
-   test suite de invariantes;
-   serialização;
-   fixtures sintéticos.

Critério de saída: trajetórias simples reproduzíveis e invariantes
verdes.

## 54. Milestone 2 --- Variable/H Lab

Entregáveis:

-   catálogo de variáveis;
-   transformações;
-   três H builders;
-   H₀/Hmax;
-   saturação;
-   persistência;
-   reversão;
-   plano público;
-   provenance;
-   comparação de funções.

Critério de saída: mesma trajetória executável sob várias especificações
com diff explicável.

## 55. Milestone 3 --- tempo e disclosure

Entregáveis:

-   calendarizado;
-   rolling;
-   Q;
-   T;
-   cut-off configurável;
-   C opcional;
-   reset/transição;
-   disclosure auditável.

Critério de saída: fragmentação e timing não quebram invariantes.

## 56. Milestone 4 --- Trajectory/Adversarial Lab

Entregáveis:

-   biblioteca de trajetórias;
-   cenário R\$100m/ano;
-   churn;
-   reversão;
-   Q−ε;
-   signal fabrication;
-   plan gaming;
-   sweeps;
-   métricas de exploitability.

Critério de saída: capacidade de identificar automaticamente estratégias
estruturalmente suspeitas sem classificá-las juridicamente como
manipulação.

## 57. Milestone 5 --- integração do frontend

Entregáveis:

-   nova bancada do regulador;
-   builders;
-   comparação;
-   trajetória;
-   auditoria;
-   provenance;
-   warnings.

Critério de saída: nenhuma regra econômica importante existe apenas no
frontend.

## 58. Milestone 6 --- microestrutura

Entregáveis:

-   book;
-   execução;
-   spread/depth;
-   market makers;
-   impacto;
-   retirada de liquidez.

## 59. Milestone 7 --- multiagente

Entregáveis:

-   agentes;
-   heurísticas;
-   aprendizado;
-   best responses;
-   cold start;
-   familiaridade;
-   reputação;
-   meta;
-   regulador experimental.

------------------------------------------------------------------------

# XX. Critérios de qualidade

## 60. Explicabilidade

Para qualquer valor de H, o usuário deve conseguir responder:

> "Por que H é este valor?"

O sistema deve mostrar a cadeia:

`dados → variáveis → transformações → função → clamps/limites → H`

## 61. Auditabilidade

Para qualquer resultado:

> "Que eventos produziram este estado?"

A resposta deve ser reconstruível do event log.

## 62. Falsificabilidade

O software deve facilitar resultados como:

-   "esta variável não ajuda";
-   "esta progressão cria exploit";
-   "este H₀ torna o regime inútil";
-   "esta reversão permite que o mercado encurrale o emissor";
-   "Q não adiciona benefício nesta região";
-   "a topologia rolling piora o equilíbrio";
-   "não encontramos Θᵥ".

## 63. Ausência de precisão inventada

Defaults numéricos devem ser marcados como:

-   pedagógicos;
-   experimentais;
-   derivados de dado;
-   derivados de precedente;
-   calibrados.

Nunca misturar categorias.

## 64. Determinismo antes de inteligência

Nenhum agente de IA deve ser necessário para validar a máquina básica.

## 65. Complexidade precisa se justificar

Uma variável ou mecanismo adicional permanece apenas se melhorar pelo
menos uma dimensão relevante:

-   estabilidade;
-   integridade;
-   utilidade econômica;
-   explicabilidade;
-   robustez;
-   resistência a exploit;
-   qualidade informacional.

Caso contrário, deve ser removível.

------------------------------------------------------------------------

# XXI. Definition of Done do laboratório-base

O laboratório-base estará pronto para a fase multiagente quando for
possível:

1.  criar um emissor sintético ou carregar um snapshot real;
2.  construir separadamente H_gross, H_net+ e H_net−;
3.  habilitar/desabilitar variáveis;
4.  escolher funções e parâmetros;
5.  escolher calendarizado ou rolling;
6.  configurar Q, T e cut-off;
7.  executar BUY/SELL em trajetórias arbitrárias;
8.  observar Gross, Net, Treasury, U e H ao longo do tempo;
9.  produzir disclosures;
10. aplicar decay;
11. testar plano público;
12. testar persistência e reversão;
13. executar o cenário de R\$100m/ano;
14. executar churn e signal fabrication;
15. comparar especificações ceteris paribus;
16. fazer sweeps;
17. detectar violações de invariantes;
18. medir custo, escala, observabilidade e repetibilidade de exploits;
19. reconstruir qualquer resultado pelo audit trail;
20. exportar configuração, eventos, resultados e métricas de forma
    reproduzível.

Quando isso existir, a pergunta deixa de ser "conseguimos implementar a
tese?" e passa a ser a pergunta científica relevante:

> **Que comportamento emerge quando agentes econômicos começam a
> explorar essa máquina?**
