# Issuer Protocol Lab
![Companhia e mercado sob supervisão regulatória](docs/assets/capa.png)

Protótipo executável do laboratório de protocolos de negociação do emissor.

**Autor:** Matheus Turra Malucelli  
**Copyright:** © 2026 Matheus Turra Malucelli

Este repositório reúne a implementação executável, o estado demonstrativo,
a especificação técnica e a tese que fundamenta o mecanismo.

[Leia o artigo de apresentação](docs/ARTIGO.md)

> **[Abrir a tese — PDF](docs/thesis/thesis.pdf)**

O PDF também é preservado em [`docs/thesis/thesis.pdf`](docs/thesis/thesis.pdf),
com as fontes Markdown e TeX no mesmo diretório.

## Conteúdo do repositório

- `issuer_lab/`: aplicação Streamlit e motor do protocolo;
- `tests/`: testes automatizados;
- `data/sources/`: dados demonstrativos importáveis;
- `lab_state.json`: estado inicial para exploração visual;
- `lab_spec.md`: especificação técnica do Lab;
- `thesis.pdf`: cópia da versão oficial da tese para acesso direto;
- `docs/thesis/`: tese em PDF e respectivos arquivos-fonte;
- `run_lab.bat`: preparação automática do ambiente e inicialização no Windows;
- `LICENSE` e `NOTICE`: licença Apache 2.0 do código;
- `THESIS_LICENSE.md`: licença CC BY 4.0 da tese;
- `CITATION.cff`: metadados de citação do projeto.

## Instalação

### Windows — execução automática

Dê dois cliques em `run_lab.bat`. Na primeira execução, o script cria `.venv`,
instala `requirements.txt` e abre o Streamlit. Nas execuções seguintes, ele
abre diretamente o Lab. Se `requirements.txt` mudar, as dependências são
atualizadas automaticamente.

### Instalação manual

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate`.

## Executar

```bash
streamlit run issuer_lab/frontend_app.py
```

## Testes

```bash
python -m pytest -q
```

Os arquivos importáveis pelo Data Builder ficam em `data/sources/`.

## Fluxo conceitual

- **Dados e Variáveis** formam a base analítica compartilhada. Ela fornece valores para a companhia do cenário, mas não integra a identidade de uma especificação.
- **Cenários** são trajetórias exógenas de ordens, identificadas por companhia e estratégia. Cada cenário oferece uma prévia completa com qualquer especificação selecionada.
- **Especificações** contêm somente regras de Memória, Capacidade e Intrawindow. Cada especificação oferece uma prévia completa com qualquer cenário selecionado.
- Uma especificação começa como rascunho com autosave e, quando concluída, recebe um fingerprint. Ela pode ser reaberta e corrigida sob a mesma identidade ou duplicada quando a intenção for criar uma alternativa.
- **Comparar** é uma aba principal com dois contrafactuais controlados e domínios invertidos. Em várias especificações para um cenário fixo, o eixo usa quantidades de ações: a trajetória solicitada é comum e cada especificação projeta seus Q e H absolutos, preservando também os percentuais como metadados. Em vários cenários para uma especificação fixa, cada cenário é normalizado pelo H resolvido para sua companhia: H aparece em 100%, Q usa o percentual compartilhado e os valores absolutos permanecem na legenda e nos tooltips. O eixo temporal permanece travado entre zero e o último passo, enquanto zoom e navegação atuam somente no eixo vertical. A tabela de parâmetros mostra H absoluto, Q absoluto e percentual, memória, Hmax e saturação. A tabela de resultados separa alertas intraday da decisão de divulgação no fechamento.

O estado distribuído já traz um conjunto de revisão reproduzível: oito especificações concluídas e treze cenários de PETR4, MGLU3, VALE3 e KEPL3. Os exemplos isolam mudanças em Q, capacidade, memória e saturação, enquanto os cenários representam estratégias exógenas em diferentes escalas de liquidez. O cenário **PETR4 · Venda líquida até o limite** testa Net negativo, cruzamento de Q net−, saturação de H net− e rejeição parcial.

Todos os dados, cenários, fórmulas, parâmetros e especificações pré-carregados são **fixtures de demonstração e teste visual**. Eles não representam calibração empírica, configuração plausível, recomendação regulatória ou evidência de viabilidade; os dados disponíveis são insuficientes para sustentar qualquer dessas interpretações.

## Modelo de dados

- `main_id` define o universo de companhias disponível aos cenários.
- Os campos de ações em tesouraria e preço de referência são definidos globalmente em **Variáveis → Mapeamentos semânticos**. Eles também podem ser atribuídos ao revisar uma coluna na aba **Dados**. Intrawindow e Cenários apenas consomem esses vínculos; overrides experimentais de Treasury continuam locais e explícitos.
- Mapeamentos semânticos são gravados atomicamente no estado da base. Uma escolha explícita vazia permanece vazia após reiniciar.
- O estado persistente dos mapeamentos e dos cenários é separado das chaves temporárias dos widgets. Trocar de aba pode desmontar os controles do Streamlit sem apagar o preço de referência, Treasury, companhia, estratégia ou descrição salvos.
- Toda coluna adicionada à tabela-base é um dado observado disponível às fórmulas.
- Variáveis são conceitos calculados; não existem primitivas predefinidas como `ADV`.
- Memória e capacidade H são configuradas por funções explícitas; H e sua progressão ficam na mesma aba.
- Todo o projeto é salvo automaticamente em `lab_state.json`, que separa base analítica, cenários, especificações, avaliações e estado da interface.
- Os botões **↶ Desfazer** e **↷ Refazer** atuam somente no contexto aberto. Base/Variáveis, cada cenário e cada especificação em rascunho possuem históricos independentes de até 20 revisões.
- Treasury é um mapeamento semântico explícito para uma coluna numérica ou um override manual. A escolha permanece sob controle do usuário.
- O preço de referência é um mapeamento semântico da base analítica. A companhia resolve esse preço, preenche novas ordens e permite reaplicá-lo à trajetória inteira; cada ordem permanece editável.
- Linhas de ordem incompletas permanecem no editor durante o preenchimento. A prévia usa somente ordens com quantidade e preço positivos e orienta o usuário quando ainda não existe nenhuma ordem completa.
- Pré-requisitos ausentes são mostrados como orientação na própria interface e bloqueiam somente a execução dependente, sem expor traceback ao usuário.
- O limite de posição própria é opcional e experimental. Quando habilitado, restringe H net+ pelo espaço entre Treasury e o percentual configurado de um campo de referência; H net− continua limitado pelo estoque disponível.
- Em Intrawindow, Q gera um alerta ao emissor. A obrigação de disclosure é avaliada sobre Gross e Net finais no fechamento; H permanece o hard cap durante todo o pregão.
- Ordens de cenário que excedem H são preenchidas parcialmente até o primeiro limite vinculante. A quantidade solicitada permanece registrada, o residual fica explicitamente não executado e o resultado separa **capacidade máxima atingida** de **divulgação no fechamento**.
- Nos gráficos, a linha sólida representa somente o estado executado. Uma extensão vermelha tracejada e um `×` mostram onde a ordem solicitada chegaria acima de 100% de H; essa parcela é intenção rejeitada e nunca integra o estado regulatório.
- Em comparações com cenários de comprimentos diferentes, o último estado é prolongado até o maior passo com linha pontilhada e menor opacidade. Esse trecho significa **sem nova ordem · estado preservado**, não uma nova execução.
- O comparativo usa diretamente as seleções principais de cenários e especificações; não há uma segunda seleção de séries. O zoom é exclusivamente vertical, mantendo o eixo de passos travado entre zero e o último período comparado. Quando há mais de uma companhia, o ticker integra o nome da série.
- Colunas textuais e datas podem coexistir na base; apenas campos realmente usados em cálculos precisam ser numéricos.
- Dados observados aceitam descrição opcional, reutilizada em tooltips, dependências e auditoria.
- Descrições de dados observados e de variáveis podem ser revisadas depois da criação sem remover a coluna ou recriar a fórmula.
- Cenários saem de uso por arquivamento recuperável. O seletor, o formulário e o aviso **Editando agora** apontam para a mesma identidade; cenários arquivados podem ser restaurados pela própria biblioteca.
- Alterações de Q persistem atomicamente com os mapeamentos de Treasury e do limite opcional de posição, evitando que um rerun apague campos independentes da especificação.
- O editor de ordens troca sua revisão interna depois de inclusões estruturais e persiste a nova linha antes do rerun, evitando a perda da primeira edição.
- A interface não depende mais do módulo legado `formula_ui` durante a inicialização.

## Citação

Ao utilizar o Lab em pesquisa, artigo, apresentação ou implementação derivada, cite:

> Malucelli, Matheus Turra. *Issuer Protocol Lab: laboratório regulatório para negociação própria do emissor sob assimetria informacional*. 2026.

Os metadados estruturados estão disponíveis em `CITATION.cff`.

## Licenciamento

O código do Issuer Protocol Lab é disponibilizado sob a **Apache License 2.0**. Consulte `LICENSE` e `NOTICE`.

A tese associada, **Negociação própria do emissor sob assimetria informacional: uma arquitetura regulatória de capacidade, disclosure e aprendizagem de mercado**, é disponibilizada separadamente sob **CC BY 4.0**. Consulte `THESIS_LICENSE.md`.

Dados e materiais de terceiros não são relicenciados pelo projeto e permanecem sujeitos aos termos de suas fontes. Os fixtures pré-carregados servem exclusivamente para demonstração e teste visual; não constituem recomendação regulatória ou calibração empírica.