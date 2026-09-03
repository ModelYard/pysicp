# Structure and Interpretation of Computer Programs
## A Python Translation

*A faithful, section-following translation of Abelson and Sussman's* Structure and Interpretation of Computer Programs, *rendered in Python.*

Derived from *Structure and Interpretation of Computer Programs*, second edition, by Harold Abelson and Gerald Jay Sussman with Julie Sussman (MIT Press). The original text is licensed CC BY-SA 4.0; this translation is likewise released under CC BY-SA 4.0.

---

## Preface

Python has won.

We will not say what "won" means, because the essay that follows does not depend on the answer, and defining it starts an argument that costs a reader and settles nothing. Pick your own sense — most-taught, most-hired, most-imported, the default second language of every adjacent field. Any of them will do. The premise this book actually needs is smaller and harder to dispute: Python is where the students are. If you are going to teach someone the deep structure of computation today, you will teach it to someone who already writes Python, or wishes they did.

That is a change from the world this book was written in, and the institution that wrote it noticed first. MIT built *Structure and Interpretation of Computer Programs* as the spine of 6.001, taught it in Scheme for a quarter of a century, and then, around 2008, moved away from it. The replacement was Python-based and organized around robotics and signals — and the rationale, in Gerald Sussman's own account, was not that Python is prettier. It was that the *nature of engineering had changed*. In 1980, programming meant building a system you understood completely out of primitives you specified completely; SICP's build-it-from-nothing pedagogy mirrored that world exactly. By 2008, engineering had become the *investigation* of large systems and libraries that nobody fully understands — you poke at a black box, observe its behavior, compose it with other black boxes. Python-with-batteries fits that world. The curriculum reorganized around empirical investigation of given systems, and it did so for a serious reason.

We concede the gain completely. Investigating systems you did not build is a real skill, arguably *the* modern one, and a curriculum is right to teach it.

But something was pushed downstream, and downstream is where things become optional. The computational meta-theory that SICP front-loaded — the theory of computation, the metacircular evaluator, the register machine, the reduction of the entire tower of abstraction to a substrate you construct yourself — became the content of later, elective courses that most students never take. That is a real loss, and we want to name it precisely rather than mourn it vaguely: **in a world where everyone treats systems as opaque, the person who can drop to the substrate has a rarer and higher-leverage skill, not an obsolete one.** The shift to systems-investigation does not make the meta-theory less valuable. It makes it scarce. Scarcity is not the same as obsolescence, and mistaking the one for the other is how a discipline forgets how its own machines work.

So this book is an attempt to regain what was set aside — but in the language the students actually have. That turns out to be less of a compromise than it sounds, because Python, examined closely, is a Lisp in other clothing. This should be defended lightly and scoped precisely, and Peter Norvig has already done most of the work: first-class functions, closures, lambda, the higher-order operations, dynamic dispatch, the read-eval-print loop, and a couple of core data structures rich enough to build everything else on. In the ways SICP's first three chapters exploit — functions as values, closures as objects, uniform structures you build abstractions over — Python gives a Lisp programmer nearly everything they reach for. That is *why* the translation works at all.

Where Python is *not* a Lisp is exactly where the book's later chapters live, and we will be honest about it throughout. Python has no macros in the Lisp sense and — the root fact beneath that — its code is not its own data. There is no homoiconicity to recover, and we will not pretend to recover it. What survives is most of what macros are *for*, reconstructed through syntax-tree manipulation, at a real cost in elegance. The seam between "Lisp-clothed" and "not actually Lisp" is not a defect in the translation. It is the most interesting boundary in the book, and it happens to coincide exactly with the boundary between the chapters that port for free and the chapters that require us to build scaffolding. The preface's aesthetic claim and the book's chapter structure are, it turns out, the same claim stated twice.

One promissory note, and then we begin. This book recovers the meta-theory of *computation*. It does not pursue, but repeatedly gestures toward, the natural sequel question — the meta-theory of *correctness*. SICP could not ask it; the intervening forty years produced the answer, and it is types: the discipline in which a type can be a proof and checking a program can mean checking an argument. Python has grown, unusually for a language of its temperament, a real gradual-typing surface, which is why the sequel is pursuable in the same language rather than a different one. We flag the trajectory — computation first, correctness after — because it is honest about where the project is going, and because it quietly explains choices this volume makes that would otherwise look like over-engineering. When we prefer a typed representation to an untyped one, we are, in part, laying track.

We are taking something from each side and leaving each slightly dissatisfied. To the Scheme tradition: your meta-theory was worth keeping, and we kept it. To the Python tradition: your language was worth teaching deeply, and it rewards the depth. Neither "kids these days abandoned the good book" nor "the old language lost, get over it" is a position we hold. The disagreement between the two tastes is not noise to be smoothed away. It is the subject.

---

## Introduction: How to Read This Translation

### This is a translation, and it says so out loud

This book follows *Structure and Interpretation of Computer Programs* section by section. It keeps the original's sequence of ideas and its arc, and it renders the code in idiomatic Python. "Faithful" here means faithful to structure and intent — not transliterated line by line, which is in places impossible (Python has no macros, no guaranteed tail calls, and a statement/expression split Scheme lacks) and everywhere undesirable, because the whole value of a translation is watching the ideas re-land in a different substrate.

Because it is a translation, the source language shows through, and we let it. You will read about cons cells, `car` and `cdr`, tail recursion, applicative versus normal order, and a certain amount of lambda calculus. This is by design. A translation that hid its original would be a worse translation, not a purer Python book. When the text pauses to explain what Scheme is doing, that pause is not a detour from the lesson — for long stretches it *is* the lesson, because understanding what the original leaned on is how you understand what your version has to rebuild.

### The one fact that organizes everything: what the atom is

Scheme is built on one logical data structure — the cons cell — from which lists, trees, and every richer structure are assembled, and on a very small set of built-in special forms. Its pedagogy is inseparable from that scarcity: the book teaches by *building* what the language lacks, out of one substrate and a handful of primitives. The construction is the curriculum.

Python's atom is different. Its core structure — the one everything else can be understood in terms of — is the namespace: the dictionary, the mapping from names to values. Its surface is not small; it is enormous. Many of the things SICP painstakingly constructs from cons cells are simply *present* in Python as language features. This inverts the pedagogical problem. Scheme teaches through scarcity that is native. Python arrives with abundance, so a faithful translation must sometimes *manufacture* scarcity — deliberately decline the surface — to recover a lesson that Python would otherwise hand over for free, pre-learned and therefore un-learned.

That single contrast is the spine of the whole book. It tells us, at every seam, what the choice actually is.

### The principle that resolves every choice: build from scarcity, or reveal the surface

At each point where Python offers a feature that SICP builds by hand, we make one of two moves, and we always tell you which:

- **Build from scarcity** when the construction *is* the lesson. The closure property of a data structure, the dispatch table that powers generic operations, the environment model of state, the evaluator itself — you learn these by building them, even when Python has a native equivalent, because the native equivalent is the answer with the reasoning deleted.
- **Reveal the surface** when the construction is mere plumbing — a thing worth showing *can* be built, once, and then set aside for the idiom a working Python programmer would actually use.

Disciplined taste, in other words, not a coin flip: the axis is whether building teaches something the finished feature conceals. We will name the move each time, because a reader who always knows whether they are building-to-learn or building-to-see-it-can-be-done is a reader who can predict our calls — and disagree with them from a position of understanding.

### Taste is real, and so is the line between taste and fact

This book sits on a fault line between two coherent aesthetics. Scheme's taste — small surface, functions all the way down, objects made of closures — is a genuine stance, and a beautiful one. Python's taste — large surface, one obvious way, classes and protocols — is equally coherent and mildly disapproving of the other. A translation feels the friction between them at every seam, and we say so up front so that friction reads as the subject rather than as the author wobbling.

When we choose a closure over a class, or a hand-built structure over a native one, that is often a taste call, made deliberately, and a reader steeped in the other tradition might rightly choose otherwise. That disagreement is not a flaw in the book; it is the most interesting thing in it.

But we promise one discipline that keeps "taste" from becoming an alibi: we will separate taste from fact. Some seams are genuinely aesthetic — closure versus class for a one-method object is a preference. Some only *look* aesthetic and are not. That a generator is not a memoized thunk is a structural fact about resumption protocols, not a style choice. That Python has no homoiconicity is a fact. That the *uses* of macros are mostly recoverable through syntax-tree manipulation, at a cost in elegance, is a fact. Learning to tell "I prefer this" from "this is correct" is most of what expertise in language design consists of, and drawing that line cleanly is one of the things this book is for.

### The representation climb: tuples → frozen dataclasses → real syntax trees

One decision propagates through the entire book: how a program is represented as data once we start writing interpreters. We settle it here, in the introduction, because it is expensive to reverse and easy to make by accident.

We climb it in three stages, and the climb is one lesson told three times at rising fidelity:

1. **Tuples.** *Programs are just structure.* Positional, tagged by convention, maximally Lisp-like — `('if', predicate, consequent, alternative)` is a tuple like any other. This preserves the "code is only data" character of the original and lets you feel, directly, the cost of an untyped positional representation as the structures grow.

2. **Frozen dataclasses.** *Programs are structure with names and types.* `If(predicate, consequent, alternative)`. Dispatch becomes pattern matching; the representation becomes legible and checkable. You earn this stage by having suffered the first, so the value of types is demonstrated rather than asserted.

3. **Real syntax trees.** *Programs are structure the host itself runs.* Here the climb resolves into working practice rather than a discarded toy. You do not rebuild Python's grammar to work with its syntax trees; you *extend* it — defining your own dataclass nodes for the few constructs you are adding, leaving every native node untouched, and *lowering* your custom nodes back into native ones when it is time to emit code. The frozen dataclasses of stage two do not get thrown away; they become the extension layer over the real thing. The authoring representation and the execution representation are different, and the compiler is the lowering pass between them.

Note what changes at each step. Tuples to dataclasses is a *re-typing* — same structure, richer type. Dataclasses to syntax trees is a *desugaring* — your construct erased into the host's constructs. The first climb adds types; the second climb adds a compiler. We build both in view.

This settles a genuine tradeoff rather than hiding it. Tuples keep the "code is data" epiphany of the original crisp, because code stays the same undifferentiated data as everything else. Dataclasses soften that epiphany — code becomes a distinct type from your other data, which is un-Lisp-like — in exchange for legibility, type-checking, and pattern-matchable structure. We take the trade knowingly, and we footnote the loss where it lands.

### What each chapter costs, and why that is predictable

Because the organizing fact is "what is the atom," we can tell you in advance which chapters port for free and which require work — and that prediction *is* the structure of the book:

- **Chapter 1** maps almost directly. Python has recursion, and its lack of tail-call optimization is a non-issue at the input sizes here. Where SICP relies on tail recursion to express an iterative process, we make the recursion-to-iteration transformation itself the visible lesson and write the loop by hand — because that transformation is precisely what the chapter's "shapes of processes" section teaches, and because it is how you will actually write the code.

- **Chapter 2** is where the "build or reveal" seam first bites, and it bites differently in different sections. Hierarchical data rewards building cons from scratch — the closure property is a real lesson Python's list obscures. Symbolic computation is where the representation climb begins in earnest. And the data-directed dispatch section contains the book's sharpest irony: SICP constructs, by hand and out of cons cells, a table keyed on operation and type — which is to say, it builds a dictionary, the exact mechanism Python itself is made of. We build it the hard way, then reveal what it became.

- **Chapter 3** is the hardest call in the book, and the difficulty is motivational, not representational. SICP introduces mutation *reluctantly*, shows what it costs — the loss of referential transparency, the substitution model breaking — and then offers two escapes: encapsulate state in objects, or banish it with streams. Python is mutation-first, so the reader never falls from grace and never feels the cost. We do not fake the reluctance. Instead we let mutation *explain bugs the Python reader already has* — aliasing, shared state, the closure-over-loop-variable trap — so the environment model earns its keep as an explanation rather than a new capability. Then objects, fast, as the surface. Then streams, slow and rich, where Python's generators are a near-perfect map and the referential-transparency lesson that mutation stole at the top of the chapter is finally repaid.

- **Chapter 4** is where the earlier investments converge. The metacircular evaluator is not a cold start; it is the symbolic representation from Chapter 2, evaluated through the dispatch table from Chapter 2, over the environment model from Chapter 3. Three chapters of manufactured scarcity pay off at once. This is also the chapter where Python's lack of homoiconicity stops mattering — because you are building your own representation and your own evaluator, the host language's inability to treat code as data is irrelevant. You define the substrate; inside it, code and data are whatever you make them.

- **Chapter 5** deliberately abandons the cons cell. The register machine is about the machine — registers, a stack, linear instructions, memory as a vector — and its honest atom is the mutable array, not the pair. The chapter's climax is that you *implement cons cells out of arrays*, which closes the book's largest loop: the substrate you began with in Chapter 2 is revealed to have been arrays with a story attached all along. Python, array- and dictionary-native, makes that reveal cleaner than Scheme does. And this is where tail-call optimization is finally *implemented* — so the loops you wrote by hand in Chapter 1 return as what the machine does mechanically. The two ends of the book are the same lesson.

### A note on what you will and will not be able to do afterward

You will finish this book able to build an interpreter for a small language, give that language proper tail calls that Python itself lacks, add syntactic abstractions to Python through syntax-tree transformation, and understand the register-level machine underneath all of it. You will not finish it with homoiconicity, because Python does not have it and cannot be given it — code is not data here, and no amount of tooling changes that root fact. You will finish with most of what macros are *for*, reconstructed honestly and, in places, unprettily.

That gap — powerful transformation, absent elegance, one root cause — is not a disappointment to be apologized for. It is one of the clearest lessons the translation has to offer, because seeing exactly what Python cannot recover is how you finally understand what Lisp actually was.

Begin at Section 1.1.
