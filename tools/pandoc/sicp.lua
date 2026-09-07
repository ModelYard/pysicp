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
  -- A block the preprocessor already tagged keeps its tag.
  if block.classes:includes('syntax') then
    return block
  end

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

-- Section numbers come from each heading's own \label -- \label{Section 1.1.1}
-- -- and not from counting headings as they go past.
--
-- The distinction matters: the numbers are the original book's and are fixed,
-- while a count reflects only what happens to be in this build. Translate 1.1.5
-- before 1.1.4 and an automatic counter would quietly call it 1.1.4.
--
-- The number is put into the heading TEXT rather than left as an attribute
-- because GitHub-flavoured markdown has no syntax for header attributes, so
-- the identifier is discarded on the way out.
-- A cross-reference target, derived from the label the book already uses:
-- \label{Section 1.1.1} and \link{Section 1.1.1} both become 'section-1-1-1'.
-- Deriving it from the label rather than the heading text is what keeps a link
-- working when a section is retitled.
local function anchor(label)
  return (label:gsub('[^%w]+', '-'):gsub('^-+', ''):gsub('-+$', ''):lower())
end

function Header(el)
  if not el.identifier or el.identifier == '' then
    return el
  end

  local label = el.identifier
  local number = label:match('^[Ss]ection ([%d%.]+)$')
    or label:match('^[Cc]hapter ([%d%.]+)$')
  if number then
    el.content:insert(1, pandoc.Space())
    el.content:insert(1, pandoc.Str(number))
  end

  el.identifier = anchor(label)

  -- GitHub-flavoured markdown has no syntax for header attributes, so the
  -- identifier set here does not survive the trip through markdown -- pandoc
  -- regenerates one from the heading text at the HTML step, and every \link
  -- lands nowhere. An explicit anchor is raw HTML, which passes through
  -- untouched, so the target exists no matter what the heading is called.
  return {
    pandoc.RawBlock('html', '<a id="' .. el.identifier .. '"></a>'),
    el,
  }
end

-- \link{Section 1.1.3} reaches pandoc as a reference to '#Section 1.1.3',
-- spaces and all. Point it at the anchor emitted above.
function Link(el)
  local target = el.target:match('^#(.+)$')
  if target and target:match('%s') then
    el.target = '#' .. anchor(target)
  end
  return el
end

-- Upstream's imageFigure environment takes its caption as an argument, so
-- pandoc emits the caption text and the image jumbled into one paragraph, in
-- that order. Rebuild it as a real <figure>, image first, and give the image
-- the caption as its alt text instead of pandoc's placeholder "image".
local figure_count = 0

local function build_figure(el)
  local src, caption = nil, pandoc.List()
  for _, block in ipairs(el.content) do
    if block.t == 'Para' or block.t == 'Plain' then
      for _, inline in ipairs(block.content) do
        if inline.t == 'Image' then
          src = inline.src
        else
          caption:insert(inline)
        end
      end
    end
  end
  if not src then
    return nil
  end
  local text = pandoc.utils.stringify(pandoc.Para(caption)):gsub('^%s+', ''):gsub('%s+$', '')
  local escaped = text:gsub('&', '&amp;'):gsub('"', '&quot;'):gsub('<', '&lt;')
  -- The figure's own \label is \label{Figure \thefigure}, a counter pandoc
  -- cannot resolve, so the anchor is numbered here instead. Figures are
  -- numbered in one sequence through the book, as they are in print.
  figure_count = figure_count + 1
  local id = 'figure-1-' .. figure_count

  return pandoc.RawBlock('html', table.concat({
    '<figure class="book-figure" id="' .. id .. '">',
    '<img src="' .. src .. '" alt="' .. escaped .. '">',
    '<figcaption>' .. escaped .. '</figcaption>',
    '</figure>',
  }, '\n'))
end

function Div(el)
  -- A syntax skeleton: grammar notation, not code in either language. Tagged
  -- rather than guessed at, and marked so the copy button leaves it alone --
  -- there is nothing here a reader would type.
  if el.classes:includes('syntaxform') then
    for _, block in ipairs(el.content) do
      if block.t == 'CodeBlock' then
        -- Pandoc keeps only the first class on a code block, so 'syntax' has
        -- to carry both meanings: how to style it, and that it is not code.
        block.classes = pandoc.List({ 'syntax' })
        return block
      end
    end
    return el
  end

  -- A codeBlock that reached pandoc as a Div would have lost its line
  -- structure; fail loudly rather than ship mangled code.
  if el.classes:includes('codeBlock') then
    error('codeBlock reached pandoc as a Div -- the verbatim rewrite did not run')
  end
  if el.classes:includes('imageFigure') then
    return build_figure(el) or el
  end
  return el
end
