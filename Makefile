# Build the Python translation of SICP.
#
# Everything runs from the repo root so that book/, code/ and vendor/ resolve
# from a single working directory. Upstream's preamble uses relative \input
# paths (\input{preamble/packages}), so vendor/sicp-latex is added to TEXINPUTS
# rather than copied.

OUT_DIR    := outputs
UPSTREAM   := vendor/sicp-latex
BOOK       := ./main.tex

# Leading "." so our own files always win: the submodule also has a main.tex,
# a buildconfig.tex and a preamble/, and without this a bare filename resolves
# to the submodule's copy -- which silently builds the ORIGINAL book instead of
# the translation. Trailing "//" searches recursively; the trailing ":"
# preserves the default path.
export TEXINPUTS := .:./$(UPSTREAM)//:

# MacTeX installs here and only adds it to PATH for newly-started shells, so a
# session that predates the install cannot see it. Exporting PATH covers recipes
# that go through a shell, but make execs metacharacter-free recipes directly
# using the PATH it started with -- so resolve the binary absolutely as well.
TEXBIN := /Library/TeX/texbin
export PATH := $(TEXBIN):$(PATH)
LATEXMK_BIN := $(if $(wildcard $(TEXBIN)/latexmk),$(TEXBIN)/latexmk,latexmk)

# Upstream's .latexmkrc sets $pdf_mode = 5, i.e. xelatex.
LATEXMK := $(LATEXMK_BIN) -xelatex -interaction=nonstopmode -halt-on-error

.PHONY: help carve seed diff figures figures-svg pictures pdf section markdown html serve check clean distclean doctor

help:
	@echo "carve     regenerate book/original/ from the pinned submodule"
	@echo "seed      copy an original into book/ to start translating it"
	@echo "          make seed SECTION=ch1/01-01-02-naming-and-the-environment.tex"
	@echo "figures   convert upstream svg figures to pdf under build/"
	@echo "pdf       build the whole book (everything in contents.tex)"
	@echo "section   build one section only"
	@echo "          make section SECTION=book/ch1/01-01-01-expressions.tex"
	@echo "diff      diff a translated section against its original"
	@echo "          make diff SECTION=ch1/01-01-01-expressions.tex"
	@echo "markdown  convert the book to GitHub-flavoured markdown"
	@echo "html      build the web edition, with REPL-aware copy buttons"
	@echo "serve     build the web edition and serve it over http"
	@echo "check     pytest + mypy + ruff over the book's code"
	@echo "doctor    report missing build dependencies"

# --- source preparation ----------------------------------------------------

carve:
	uv run python tools/carve.py --clean

seed:
	@test -n "$(SECTION)" || { echo "usage: make seed SECTION=ch1/01-01-02-....tex"; exit 1; }
	@test -f book/original/$(SECTION) || { echo "no such original: book/original/$(SECTION) (run 'make carve')"; exit 1; }
	@test ! -f book/$(SECTION) || { echo "refusing to overwrite existing book/$(SECTION)"; exit 1; }
	@mkdir -p $(dir book/$(SECTION))
	@cp book/original/$(SECTION) book/$(SECTION)
	@echo "seeded book/$(SECTION) -- now add its \\input line to contents.tex"

diff:
	@test -n "$(SECTION)" || { echo "usage: make diff SECTION=ch1/01-01-01-....tex"; exit 1; }
	@diff -u book/original/$(SECTION) book/$(SECTION) || true

# --- figures ---------------------------------------------------------------
#
# The chapters reference figures as .pdf, but upstream ships .svg and converts
# at build time -- so the conversion is required, not optional: a missing figure
# is a hard xelatex error ("Unable to load picture"), not a warning.
#
# Two departures from upstream's Makefile. Theirs shells out to inkscape, which
# is not installed here; rsvg-convert does the same job. And theirs writes the
# .pdf next to the .svg inside the repo -- we write into build/ instead, so the
# pinned submodule's working tree stays clean.
#
# The .svg files are git-lfs objects. Without git-lfs they are ~132-byte pointer
# stubs and conversion produces garbage, so check before converting.

SVGS := $(shell find $(UPSTREAM)/assets -name '*.svg' 2>/dev/null)
FIGS := $(patsubst $(UPSTREAM)/%.svg,build/%.pdf,$(SVGS))

build/%.pdf: $(UPSTREAM)/%.svg
	@head -c 40 $< | grep -q 'git-lfs' && { \
		echo "error: $< is a git-lfs pointer stub, not an image."; \
		echo "       brew install git-lfs && (cd $(UPSTREAM) && git lfs install --local && git lfs pull)"; \
		exit 1; \
	} || true
	@mkdir -p $(dir $@)
	rsvg-convert --format=pdf --output=$@ $<

figures: $(FIGS)
	@echo "converted $(words $(FIGS)) figures into build/"

# --- building --------------------------------------------------------------

pdf: $(PICTURE_PDFS)
	@mkdir -p $(OUT_DIR)
	$(LATEXMK) -outdir=$(OUT_DIR) $(BOOK)

# One section at a time. A full build is 31k lines of source; this is the edit loop.
section: $(PICTURE_PDFS)
	@test -n "$(SECTION)" || { echo "usage: make section SECTION=book/ch1/01-01-01-....tex"; exit 1; }
	@mkdir -p $(OUT_DIR)
	$(LATEXMK) -outdir=$(OUT_DIR) \
		-usepretex="\newcommand{\buildSection}{$(SECTION)}" $(BOOK)

# --- figures for the web edition -------------------------------------------
#
# The book's own figures are tikzpictures, which pandoc cannot see at all -- it
# silently produced an empty figure box. Each one is rendered to SVG here so the
# HTML edition gets the same picture from the same single source.
#
# xelatex emits .xdv rather than .dvi, so the figure is taken to PDF first and
# dvisvgm reads that; --font-format=woff embeds the glyphs, so the SVG does not
# depend on the reader having the book's fonts.

FIG_SRCS := $(shell find book/figures -name '*.tex' 2>/dev/null)
FIG_SVGS := $(patsubst book/figures/%.tex,build/figures/%.svg,$(FIG_SRCS))

build/figures/%.svg: book/figures/%.tex tools/figures/standalone-preamble.tex
	@mkdir -p $(dir $@)
	@printf '\\documentclass[border=4pt]{standalone}\n' > $@.tex
	@cat tools/figures/standalone-preamble.tex >> $@.tex
	@printf '\\begin{document}\n' >> $@.tex
	@cat $< >> $@.tex
	@printf '\n\\end{document}\n' >> $@.tex
	@$(TEXBIN)/xelatex -interaction=batchmode -halt-on-error \
		-output-directory=$(dir $@) $@.tex >/dev/null
	@$(TEXBIN)/dvisvgm --pdf --font-format=woff --output=$@ $@.pdf >/dev/null 2>&1
	@rm -f $@.tex $@.pdf $@.log $@.aux
	@echo "rendered $@"

figures-svg: $(FIG_SVGS)

# --- pictures generated by the book's own code -----------------------------
#
# Section 2.2.4's figures are output of the picture language it describes, not
# drawings of it: both editions get them from code/ch2/picture_language.py, as
# SVG for the web and PDF for print. Keep this list in step with FIGURES in
# tools/figures/picture_figures.py.

PICTURE_NAMES := wave wave-beside wave-flipped-pairs wave-right-split \
                 wave-corner-split wave-square-limit
PICTURE_PDFS  := $(addprefix build/figures/ch2/,$(addsuffix .pdf,$(PICTURE_NAMES)))
PICTURE_SVGS  := $(addprefix build/figures/ch2/,$(addsuffix .svg,$(PICTURE_NAMES)))

$(PICTURE_PDFS) $(PICTURE_SVGS) &: code/ch2/picture_language.py tools/figures/picture_figures.py
	uv run python tools/figures/picture_figures.py

pictures: $(PICTURE_PDFS) $(PICTURE_SVGS)

# --- html ------------------------------------------------------------------
#
# The .tex sources stay the single source of truth; HTML is generated. Two
# steps are non-obvious and both are load-bearing:
#
#  1. codeBlock -> verbatim, textually. Pandoc handles verbatim lexically, so
#     the rewrite CANNOT be done with a macro definition -- and without it the
#     line structure of every code block collapses.
#  2. tools/pandoc/shim.tex. Pandoc silently DELETES macros it does not know,
#     along with their arguments, so \newterm{expression} disappears mid
#     sentence with no warning. The shim defines them.

HTML_OUT  := $(OUT_DIR)/book.html
SECTIONS  := $(shell sed -n 's/^\\input{\(book\/[^}]*\)}.*/\1/p' contents.tex)

$(OUT_DIR)/book.md: contents.tex $(SECTIONS) $(UPSTREAM)/backmatter/references.tex tools/pandoc/shim.tex tools/pandoc/preprocess.py
	@mkdir -p $(OUT_DIR)
	uv run python tools/pandoc/preprocess.py $(SECTIONS) \
		$(UPSTREAM)/backmatter/references.tex \
		--shim tools/pandoc/shim.tex --out $@.tex
	pandoc -f latex -t gfm+tex_math_dollars --lua-filter=tools/pandoc/sicp.lua -o $@ $@.tex
	@rm -f $@.tex

markdown: $(OUT_DIR)/book.md
	@echo "wrote $(OUT_DIR)/book.md"

# --include-after-body puts the script INSIDE <body>. Appending it to the file
# instead leaves it after </html>, where it is a parse error the browser has to
# recover from.
html: $(OUT_DIR)/book.md $(FIG_SVGS) $(PICTURE_SVGS) tools/html/copybutton.js tools/html/book.css tools/html/after-body.html
	pandoc -f gfm+tex_math_dollars -t html5 --standalone --toc --section-divs \
		--mathml \
		--metadata title="SICP: A Python Translation" \
		--css book.css --include-after-body=tools/html/after-body.html \
		$(OUT_DIR)/book.md -o $(HTML_OUT)
	@cp tools/html/book.css tools/html/copybutton.js $(OUT_DIR)/
	@mkdir -p $(OUT_DIR)/figures && cp -R build/figures/* $(OUT_DIR)/figures/
	@echo "wrote $(HTML_OUT) -- open with 'make serve' rather than file:// if the"
	@echo "  clipboard API is unavailable in your browser"

# A real origin. Some browsers restrict clipboard access on file:// URLs.
serve: html
	@echo "serving $(OUT_DIR) at http://localhost:8000/book.html (Ctrl-C to stop)"
	@cd $(OUT_DIR) && python3 -m http.server 8000

# --- the book's code -------------------------------------------------------
#
# Code in the book is included from real .py files, so it is executable and
# type-checked. This target is what keeps that promise true.

check:
	uv run pytest
	uv run mypy src/ tools/ code/
	uv run ruff check src/ tests/ tools/ code/
	uv run ruff format --check src/ tests/ tools/ code/
	uv run python tools/lint_book_code.py

# --- housekeeping ----------------------------------------------------------

doctor:
	@echo "checking build dependencies..."
	@command -v xelatex     >/dev/null && echo "  xelatex      ok" || echo "  xelatex      MISSING  (brew install --cask mactex-no-gui, or basictex)"
	@command -v latexmk     >/dev/null && echo "  latexmk      ok" || echo "  latexmk      MISSING  (ships with mactex; basictex: tlmgr install latexmk)"
	@command -v git-lfs     >/dev/null && echo "  git-lfs      ok" || echo "  git-lfs      MISSING  (brew install git-lfs; then: cd $(UPSTREAM) && git lfs pull)"
	@command -v rsvg-convert>/dev/null && echo "  rsvg-convert ok" || echo "  rsvg-convert MISSING  (brew install librsvg)"
	@test -d $(UPSTREAM)/chapters && echo "  submodule    ok" || echo "  submodule    MISSING  (git submodule update --init)"
	@head -c 40 $(UPSTREAM)/assets/figures/chapter_1/*.svg 2>/dev/null | grep -q 'git-lfs' \
		&& echo "  figures      LFS STUBS (cd $(UPSTREAM) && git lfs pull)" \
		|| echo "  figures      ok"

clean:
	rm -rf $(OUT_DIR)

distclean: clean
	rm -rf book/original build
