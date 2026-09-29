local function first_header(table_block)
  if not table_block.head or #table_block.head.rows == 0 then
    return ""
  end
  local cells = table_block.head.rows[1].cells
  if not cells or #cells == 0 then
    return ""
  end
  return pandoc.utils.stringify(cells[1].contents)
end

function Table(table_block)
  local count = #table_block.colspecs
  local header = first_header(table_block)
  local widths

  if count == 2 and header == "Objeto" then
    widths = {0.18, 0.82}
  elseif count == 2 and header == "Propriedade" then
    widths = {0.76, 0.24}
  elseif count == 3 and header == "Caso" then
    widths = {0.16, 0.36, 0.48}
  elseif count == 3 then
    widths = {0.34, 0.33, 0.33}
  elseif count == 4 then
    widths = {0.25, 0.25, 0.25, 0.25}
  else
    return table_block
  end

  for index, colspec in ipairs(table_block.colspecs) do
    table_block.colspecs[index] = {colspec[1], widths[index]}
  end
  return table_block
end

-- The Markdown source uses explicit ASCII anchors so its manually curated
-- table of contents remains stable. Pandoc preserves those HTML anchors when
-- rendering HTML, but otherwise drops them from LaTeX and generates accented
-- destination names from the headings. Convert the anchors to native PDF
-- destinations so every internal link resolves consistently.
function RawBlock(block)
  if not FORMAT:match("latex") or block.format ~= "html" then
    return block
  end

  local identifier = block.text:match('^<a id="([%w%-_]+)"></a>%s*$')
  if not identifier then
    return block
  end

  return pandoc.RawBlock("latex", "\\hypertarget{" .. identifier .. "}{}")
end

function RawInline(inline)
  if not FORMAT:match("latex") or inline.format ~= "html" then
    return inline
  end

  local identifier = inline.text:match('^<a id="([%w%-_]+)">$')
  if identifier then
    return pandoc.RawInline("latex", "\\hypertarget{" .. identifier .. "}{}")
  end

  if inline.text == "</a>" then
    return {}
  end

  return inline
end
