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

.PHONY: help carve seed diff figures pdf section check clean distclean doctor

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

pdf:
	@mkdir -p $(OUT_DIR)
	$(LATEXMK) -outdir=$(OUT_DIR) $(BOOK)

# One section at a time. A full build is 31k lines of source; this is the edit loop.
section:
	@test -n "$(SECTION)" || { echo "usage: make section SECTION=book/ch1/01-01-01-....tex"; exit 1; }
	@mkdir -p $(OUT_DIR)
	$(LATEXMK) -outdir=$(OUT_DIR) \
		-usepretex="\newcommand{\buildSection}{$(SECTION)}" $(BOOK)

# --- the book's code -------------------------------------------------------
#
# Code in the book is included from real .py files, so it is executable and
# type-checked. This target is what keeps that promise true.

check:
	uv run pytest
	uv run mypy src/ tools/ code/
	uv run ruff check src/ tests/ tools/ code/
	uv run ruff format --check src/ tests/ tools/ code/

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
