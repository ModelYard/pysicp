-- Project-local Neovim settings (loaded via 'exrc'; Neovim will ask once to
-- trust this file).
--
-- Why this exists: this project builds through a Makefile rather than plain
-- latexmk -- it carves upstream sections, converts figures, and sets TEXINPUTS
-- to reach into vendor/sicp-latex. Compilation is therefore delegated rather
-- than disabled, so VimTeX's `<localleader>ll` still builds the book.
--
-- The generic compiler runs from the project root, which is the directory
-- holding main.tex -- the repo root -- so a plain `make` is correct.

vim.g.vimtex_compiler_method = 'generic'
vim.g.vimtex_compiler_generic = {
  command = 'make pdf',
}

-- The build writes its log to outputs/main.log at the repo root rather than
-- next to main.tex, so VimTeX cannot find it to populate the quickfix list.
-- Suppress the empty-quickfix churn; read errors from the make output instead.
vim.g.vimtex_quickfix_mode = 0
