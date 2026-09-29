# Tese associada

**Título:** *Negociação própria do emissor sob assimetria informacional: uma
arquitetura regulatória de capacidade, disclosure e aprendizagem de mercado*

**Autor:** Matheus Turra Malucelli  
**Ano:** 2026

Arquivos:

- `thesis.pdf`: versão oficial para leitura, citação e distribuição;
- `thesis.md`: fonte editorial em Markdown; sua renderização direta no GitHub pode diferir da composição oficial;
- `thesis.tex`: fonte LaTeX gerada para reprodução do PDF;
- `table_widths.lua`: filtro do Pandoc que mantém as tabelas dentro da largura útil da página.

Para regenerar o PDF com a mesma composição das tabelas:

```bash
pandoc thesis.md \
  -f gfm+tex_math_dollars \
  --standalone \
  --lua-filter=table_widths.lua \
  --pdf-engine=xelatex \
  -V papersize:a4 \
  -V geometry:margin=2.5cm \
  -V mainfont="DejaVu Serif" \
  -V sansfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  -M author="Matheus Turra Malucelli" \
  -M date="2026" \
  -o thesis.pdf
```

O texto da tese é disponibilizado sob a licença Creative Commons Atribuição
4.0 Internacional (CC BY 4.0). O código do Lab possui licença independente,
Apache 2.0, conforme o arquivo `LICENSE` na raiz do repositório.

Os dados, cenários, fórmulas, parâmetros e especificações pré-carregados no Lab
são fixtures de demonstração e teste visual. Não constituem recomendação
regulatória, calibração empírica ou evidência de viabilidade.
