-- Pandoc filter for the HTML build.
--
-- Three jobs: preserve which lines are interpreter OUTPUT, tag REPL
-- transcripts, and make section labels into valid HTML ids.

-- Upstream marks interpreter output with the listings escape character:
--   (+ 137 349)
--   ~\textit{486}~
-- That markup is the ONLY thing distinguishing input from output in a Scheme
-- transcript -- Scheme has no prompt. Discarding it (rendering `486` as a
-- plain line) makes output indistinguishable from something you would type,
-- and the copy button then has no way to leave it out. So it is translated
-- into markup rather than stripped: `go` is the conventional highlighter class
-- for "generic output".
local OUTPUT_LINE = '^%s*~\\textit{(.-)}~%s*$'

local function html_escape(s)
  return (s:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'))
end

-- A transcript is a block with at least one line opening with the primary
-- prompt. `pycon` is the conventional class for a Python console session.
local function is_repl(text)
  return text:match('^>>> ') ~= nil or text:match('\n>>> ') ~= nil
end

local function has_marked_output(text)
  return text:find('~\\textit', 1, true) ~= nil
end

function CodeBlock(block)
  local class = is_repl(block.text) and 'pycon' or 'scheme'

  if not has_marked_output(block.text) then
    if #block.classes == 0 then block.classes:insert(class) end
    return block
  end

  -- Emit raw HTML so individual lines can carry markup; a pandoc CodeBlock is
  -- plain text and cannot. The newline lives INSIDE the span, so removing an
  -- output line removes its line break too and leaves no blank gap behind.
  local parts = {}
  local body = block.text:gsub('\n$', '')
  for line in (body .. '\n'):gmatch('([^\n]*)\n') do
    local output = line:match(OUTPUT_LINE)
    if output then
      parts[#parts + 1] = '<span class="go">' .. html_escape(output) .. '\n</span>'
    else
      parts[#parts + 1] = html_escape(line) .. '\n'
    end
  end

  return pandoc.RawBlock(
    'html',
    '<pre class="' .. class .. '"><code>' .. table.concat(parts) .. '</code></pre>'
  )
end

-- Pandoc turns \label{Section 1.1.1} into an identifier containing spaces,
-- which is not a usable HTML id or fragment link.
function Header(el)
  if el.identifier and el.identifier ~= '' then
    el.identifier = el.identifier:gsub('%s+', '-'):lower()
  end
  return el
end

-- A codeBlock that reached pandoc as a Div would have lost its line structure;
-- fail loudly rather than ship mangled code.
function Div(el)
  if el.classes:includes('codeBlock') then
    error('codeBlock reached pandoc as a Div -- the verbatim rewrite did not run')
  end
  return el
end
