"""Lesson content for the AI Engineering subject.

Module count per competency tracks real topic complexity — see
app.seeds.lessons.types.LessonModule. These competencies are more
conceptual than code-heavy, so modules lean on concrete mechanisms and
worked examples rather than large code samples.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "llm-fundamentals": [
        LessonModule(
            title="Tokens, embeddings, and context windows",
            content=r"""
## Tokenization: the model doesn't see characters or words

An LLM never reads raw text. Before anything reaches the model, a
tokenizer splits text into a sequence of **subword tokens** from a fixed
vocabulary (commonly 30k-100k+ entries), and every downstream computation
operates on the resulting integer IDs, not on letters.

Modern tokenizers (BPE — Byte Pair Encoding, or variants like
SentencePiece/tiktoken) are built by starting from individual characters
and iteratively merging the most frequent adjacent pairs until the
vocabulary reaches its target size. The result is a vocabulary of common
whole words (`"the"`, `"function"`), common word-pieces (`"ing"`,
`"tion"`, `"pre"`), and, as a fallback, individual bytes/characters for
anything rare enough not to have earned a merged token.

Concretely, `"strawberry"` might tokenize as something like `["straw",
"berry"]` or `["str", "aw", "berry"]` depending on the tokenizer — never
as `["s", "t", "r", "a", "w", ...]` under normal circumstances, because
merging into larger chunks is exactly what BPE optimizes for. This is
*why* "how many r's are in strawberry" famously trips up LLMs: the model
never receives the individual letters as distinct units to count. It
receives one or two opaque token IDs whose internal spelling it has to
have memorized from training data, not compute on demand. Asking an LLM
to count letters is asking it to do a task its input representation
actively works against — it's answering from statistical association
("strawberry... has appeared near 'three r's' in training text"), not
from character-level inspection. This generalizes: any task that requires
reasoning below the token boundary (character counts, exact substring
manipulation, some arithmetic) is a structurally hard task for a
token-based model, independent of how "smart" the model otherwise is.

Tokenization also explains other odd behavior: leading spaces are often
part of the token (`" the"` and `"the"` can be different token IDs),
which is why some models are sensitive to whitespace in prompts; numbers
are frequently tokenized in inconsistent chunks (`"1234"` might become
`["123", "4"]` in one context and `["12", "34"]` in another), which
degrades arithmetic; and uncommon languages or code with unusual
identifiers get tokenized less efficiently (more tokens per unit of
meaning), which is part of why non-English and niche-language prompts
cost more and perform worse.

## Embeddings: meaning as geometry

Once text is tokenized, each token ID is looked up in an embedding table
and converted into a dense vector — typically hundreds to thousands of
real numbers. That vector is the model's *learned* representation of what
the token means, refined by training so that vectors end up positioned in
a high-dimensional space where **geometric proximity approximates
semantic similarity**. Tokens/phrases used in similar contexts across the
training data end up with vectors that point in similar directions.

This is not a metaphor — it's directly measurable. Take an embedding
model (a model whose entire job is producing one vector per input text,
as opposed to generating more text), embed `"queen"`, `"king"`,
`"woman"`, and `"man"`, and the classic result is
`vector("king") - vector("man") + vector("woman") ≈ vector("queen")`:
linear arithmetic on the vectors tracks a semantic relationship. In
practice, this is what makes embeddings useful for search: embed a query
and embed a corpus of documents, then rank documents by vector similarity
(cosine similarity or dot product) to the query vector — semantically
related text ends up "nearby" even when it shares no exact words with the
query. This is the mechanism underneath semantic search and RAG
retrieval (see the rag-architecture competency).

Two embeddings worth distinguishing: **token embeddings** (the input
lookup table, one fixed vector per vocabulary entry, context-independent)
versus **contextual embeddings** (the vector for a token *after* it has
passed through the model's attention layers, which changes depending on
surrounding text — the word "bank" gets a different contextual embedding
next to "river" than next to "loan"). When people talk about "embeddings"
for RAG/search, they almost always mean a pooled contextual
representation of a whole chunk of text, produced by a dedicated
embedding model, not the raw input-lookup vectors.

## Context window: a hard ceiling on working memory

The context window is the maximum number of tokens (input + output
combined, for most APIs) the model can attend to in a single call —
commonly ranging from 8k to over 1M tokens depending on the model. It is
not a soft guideline; text beyond the limit is either rejected outright
or silently truncated by the client library, depending on how the API is
called.

What the context window actually constrains is **attention**, not just
storage. The model's self-attention mechanism lets every token attend to
every other token in the window, and that's the computational
mechanism that lets a model "notice" a fact stated on page 1 while
generating page 40. Nothing outside the window exists for the model at
all in that call — there is no memory beyond it unless the application
explicitly re-feeds relevant information on the next call (which is the
entire premise behind conversation history, RAG, and agent memory
systems). A bigger context window doesn't mean the model *uses* all of
it equally well — see the context-engineering competency for why more
tokens in context isn't free even when they technically fit.

## Key takeaways

- Tokenization splits text into subword units via merge rules (BPE-style),
  not characters or words — this is mechanically why LLMs are bad at
  character-level tasks like counting letters.
- An embedding is a dense vector positioned so that geometric distance
  approximates semantic similarity; this is the computational basis for
  semantic search and RAG retrieval.
- Token embeddings (fixed, per-vocabulary-entry) and contextual embeddings
  (computed per use, context-dependent) are different things — RAG/search
  systems use the latter, produced by a dedicated embedding model.
- The context window is a hard limit on how many tokens the model's
  attention mechanism can relate to each other in one call; nothing
  outside it is visible unless explicitly re-supplied.
""",
        ),
        LessonModule(
            title="Sampling and generation",
            content=r"""
## The model outputs a probability distribution, not an answer

At each generation step, the model doesn't produce "the next word" — it
produces a probability distribution over its entire vocabulary (every
possible next token gets a probability). A **decoding strategy** then
picks one token from that distribution, appends it to the sequence, and
repeats. Everything about how "creative," "deterministic," or "random" a
model feels is a property of the decoding strategy layered on top of the
model, not an intrinsic property of the model's knowledge.

## Greedy decoding: deterministic, and worse than it sounds

Greedy decoding always picks the single highest-probability token at
every step. It's fully deterministic — same prompt, same output, every
time — which sounds desirable, but it produces noticeably worse text in
practice: it can't course-correct, tends to produce repetitive/generic
phrasing, and a locally-optimal token choice can lead to a globally worse
continuation (choosing the most likely word right now can back the model
into a corner three words later). Greedy decoding is used when
determinism matters more than quality — e.g., some evaluation harnesses,
or generation where reproducibility is a hard requirement.

## Temperature: reshaping the distribution before sampling

Temperature is a scalar applied to the logits (the model's raw,
pre-probability scores) before they're converted to probabilities via
softmax, mechanically:

```
probability(token) = softmax(logit(token) / temperature)
```

- **Temperature → 0**: sharpens the distribution toward a spike on the
  single highest-logit token — converges to greedy decoding.
- **Temperature = 1**: uses the model's raw learned distribution
  unmodified.
- **Temperature > 1**: flattens the distribution, making low-probability
  tokens relatively more likely to be picked — more "random," more
  prone to incoherence at high values (temperature 2+ often produces
  garbage).

This is *why* the same prompt gives different outputs across calls at
temperature > 0: the model computes the same distribution each time, but
sampling from a distribution is a random draw, not a lookup. Two calls
with identical input can legitimately draw different tokens at step one,
which then changes the context for step two, compounding into visibly
different completions — this is inherent to sampling, not a sign of
inconsistency or a bug.

## Top-p (nucleus) and top-k: restricting the candidate pool

Sampling directly from the full vocabulary's distribution at moderate
temperature occasionally draws a wildly implausible token from the long
tail (low probability, but vocabulary sizes are large enough that the
tail has non-trivial cumulative mass). Two common mitigations:

- **Top-k sampling**: only consider the k highest-probability tokens,
  renormalize, then sample from that restricted set. Simple, but a fixed
  k is wrong for different distributions — sometimes the model is very
  confident (only 2-3 tokens are plausible) and k=40 needlessly includes
  garbage; sometimes it's genuinely uncertain across dozens of tokens and
  k=40 is too restrictive.
- **Top-p / nucleus sampling**: instead of a fixed count, take the
  smallest set of highest-probability tokens whose cumulative probability
  exceeds p (e.g., p=0.9 → keep adding tokens, highest probability first,
  until their probabilities sum past 90%), renormalize, then sample. This
  adapts to the shape of the distribution automatically — a confident
  distribution needs few tokens to reach 90% mass, an uncertain one needs
  many. Top-p is the more common default in production APIs, frequently
  combined with a temperature setting.

Both are typically combined with temperature: temperature reshapes the
distribution, top-p/top-k then truncates the candidate pool before the
random draw happens.

## Practical implication for engineering with these knobs

- Low temperature (0-0.3) + no/high top-p: near-deterministic, good for
  extraction, classification, structured output, code generation where
  you want the "obvious" answer.
- Higher temperature (0.7-1.0) with top-p ~0.9: more varied phrasing,
  used for brainstorming, creative writing, varied conversational tone.
- Temperature 0 does not guarantee bit-identical outputs across calls in
  most production APIs, because of floating-point non-determinism in
  batched GPU inference (different batch composition changes numerical
  rounding) — "deterministic" from decoding strategy and "reproducible in
  practice" are not quite the same guarantee.

## Key takeaways

- The model produces a probability distribution over the vocabulary at
  each step; a decoding strategy (greedy or sampling-based) turns that
  into an actual chosen token.
- Temperature rescales the distribution's sharpness before sampling —
  near 0 approaches greedy/deterministic, higher values flatten it toward
  more randomness.
- Top-p (nucleus) truncates the candidate pool to the smallest
  high-probability set before sampling, adapting to how confident the
  distribution is at each step — this is why it's generally preferred
  over a fixed top-k.
- Non-determinism at temperature > 0 is inherent to sampling from a
  distribution, not a symptom of the model being unreliable.
""",
        ),
        LessonModule(
            title="Why LLMs hallucinate, and what actually mitigates it",
            content=r"""
## The training objective has no "I don't know" outcome

An LLM is trained (at the pretraining stage) on one core objective: given
the preceding tokens, predict the next token, over and over across a huge
corpus. There is no training signal that says "abstain here" or "flag
uncertainty here" — the model is scored purely on how well its predicted
distribution matches what token actually came next in the training data.
When the model is later prompted with a factual question, it is doing the
exact same mechanical operation: producing the most probable
continuation of the prompt, token by token. If the training data
contained the fact, the most probable continuation likely *is* the fact.
If it didn't, or the model didn't generalize it correctly, the most
probable continuation is still *some* fluent, confident-sounding
continuation — because fluency and confidence are what the training
objective rewards, not calibrated uncertainty. This is the root
mechanism of hallucination: the model has no built-in circuit that
distinguishes "I recall this" from "I am pattern-matching my way to
something plausible."

Instruction tuning and RLHF (reinforcement learning from human feedback)
add a layer on top that can partially teach a model to say "I'm not
sure" in some cases, because human raters can reward that behavior — but
this is a learned, imperfect override on top of a next-token predictor,
not a structural fix. It's why hallucination rates differ across models
and improve with better post-training, but the underlying mechanism (no
built-in ground-truth check) never fully goes away.

## Knowledge gap vs. confident wrong answer — different failure modes

It's worth distinguishing two distinct situations that both get called
"hallucination":

1. **Knowledge gap**: the model was never trained on the relevant fact
   (an event after its training cutoff, a fact from a private/internal
   document, a rarely-discussed detail). The model doesn't "know that it
   doesn't know" — it just produces its best statistical guess, often
   confidently, because nothing in its representation flags this
   particular guess as lower-quality than a well-supported one.
2. **Retrieval/reasoning failure with the right facts in context**: even
   when the correct information is right there in the prompt (e.g., in a
   RAG-retrieved document), the model can still misattribute, conflate,
   or misread it — this is a different mechanism (attention/composition
   failure) from a pure knowledge gap, and is exactly why grounding alone
   doesn't take hallucination to zero (see below).

Both present identically to the end user: a fluent, plausible, wrong
answer, stated with the same confident tone as a correct one. There is no
tone or phrasing signal from the model that reliably distinguishes a
memorized fact from a confabulation — this is *the* core reason
hallucination is dangerous rather than merely annoying: the failure mode
is not obviously a failure.

## Grounding via retrieval: constrains, doesn't eliminate

Retrieval-Augmented Generation (RAG — full mechanics in the
rag-architecture competency) mitigates the *knowledge gap* failure mode
by injecting relevant source text directly into the context window before
generation, so the model's most-probable continuation is now conditioned
on real, current, verifiable text rather than solely on its parametric
memory (whatever got baked into its weights during training). This
measurably reduces hallucination rates in practice and is the standard
production mitigation for factual grounding.

It does not eliminate hallucination, for two structural reasons: (1) the
retrieval step itself can fail — retrieving irrelevant or wrong documents
means the model is now grounded in the *wrong* thing, confidently; and
(2) even with correct context supplied, the model can still misread,
conflate multiple retrieved passages, or add unsupported embellishment on
top of a real fact, because generation is still fundamentally next-token
prediction, now conditioned on more (but not infallible) input.

## Other mitigations, and their limits

- **Bigger/better-trained models hallucinate less on average** — more
  training data and better post-training generally improve factual
  recall and calibration — but this is a continuous improvement, not a
  threshold that reaches zero. Scale reduces the *frequency*, not the
  *existence*, of the failure mode, because the underlying mechanism
  (no ground-truth check) is architectural, not a training-data problem
  alone.
- **Lower temperature** reduces variance and can reduce some hallucination
  (less likely to sample an implausible tail token), but a model can
  hallucinate at temperature 0 too — greedy decoding just deterministically
  picks the most probable wrong answer instead of a randomly sampled one.
- **Citations/attribution** (asking the model to cite which retrieved
  passage supports each claim) makes hallucination *detectable* by a
  human or a downstream check, which is valuable operationally, but
  doesn't by itself prevent the model from generating an unsupported
  claim in the first place — it's a mitigation for the consequence, not
  the cause.
- **Structured/constrained output and tool use** (forcing the model to
  call a calculator, a database query, or a verified API instead of
  generating a number or fact freehand) sidesteps hallucination for the
  specific sub-task handed to the tool — but only for what's actually
  delegated to the tool.

## The engineering takeaway

Treat "does this answer sound confident" as zero evidence of correctness
— confidence is a stylistic property of fluent text generation, not a
calibrated signal. For anything where being wrong has real cost, the
system needs an external check: grounding in retrieved/verified sources,
a deterministic tool call for anything computable, human review, or an
evaluation pipeline that measures groundedness (see ai-evaluation) rather
than trusting the model's own tone.

## Key takeaways

- Hallucination is a structural consequence of next-token prediction
  having no built-in "I don't know" — not a bug that gets patched away.
- Knowledge gaps (never learned the fact) and reasoning/attribution
  failures (misread facts that were right there in context) are
  different mechanisms that produce the same visible symptom.
- RAG/grounding reduces hallucination by conditioning generation on real
  retrieved text, but doesn't eliminate it — retrieval can fail, and the
  model can still misread or embellish correct context.
- Bigger/better-trained models hallucinate less on average but never
  reach zero, because the architectural gap (no ground-truth check) isn't
  a function of scale alone.
- A confident tone is not evidence of correctness — build external
  verification (grounding, tool calls, evaluation) for anything where
  being wrong is costly.
""",
        ),
    ],
    "context-engineering": [
        LessonModule(
            title="What context engineering actually is",
            content=r"""
## From "prompt engineering" to "context engineering"

Early LLM application work focused on **prompt engineering**: wording a
single instruction well — phrasing, few-shot examples, output format
hints — to get better behavior from a fixed, usually short input. That
remains useful, but it addresses a shrinking fraction of what determines
output quality in a real application. The harder, now-dominant problem is
**context engineering**: deciding what the model *sees* at all, across
everything that can occupy the context window — because in most
production systems the prompt template is a small, mostly-fixed piece,
while the bulk of the tokens the model actually processes come from
elsewhere.

Concretely, the full context assembled for a single LLM call in a real
system is a composite of several distinct sources:

- The **system instructions** (persona, constraints, output format).
- The **user's actual message** (often the smallest piece).
- **Retrieved documents** (RAG chunks — see rag-architecture).
- **Tool/function call results** from earlier in the same turn (a
  database query result, a search API response, file contents).
- **Conversation history** (prior turns, potentially many).
- **Long-running memory** (facts persisted across sessions, if the
  system has that).

Context engineering is the discipline of deciding, for each of these
sources, what goes in, what gets left out, what gets compressed, and in
what order — for every single call, because the answer changes as the
task, conversation, and available information change. It's a strictly
harder problem than prompt engineering because prompt engineering
optimizes a mostly-static template, while context engineering is a
per-request selection and prioritization problem over a large and
growing pool of candidate information.

## The core tension: more context is not free

The naive instinct once context windows grew large (100k-1M+ tokens) was
"just put everything in — let the model figure out what's relevant."
This fails for three separate reasons, and conflating them is a common
mistake:

1. **Cost.** Most LLM APIs charge per input token. A call with 200k
   tokens of context costs meaningfully more than one with 5k, every
   single time it's made — and this compounds fast in an agent loop that
   makes many calls per task, or a chat product with thousands of users.
2. **Latency.** Time-to-first-token and total generation time both scale
   with input length (attention is at least quadratic in sequence length
   for the un-optimized case, and even with optimizations like KV-caching
   and flash attention, more input tokens still means more processing
   before the first output token). A context-bloated call is a slower
   call, and users notice.
3. **Attention dilution — "lost in the middle."** This is the least
   intuitive and most important effect for engineering purposes:
   empirically, model accuracy on information placed in the *middle* of a
   long context is measurably worse than the same information placed
   near the *beginning* or *end* of the context, even though the
   information is technically "in the window" and the model could in
   principle attend to it. The mechanism is that attention is a learned,
   imperfect prioritization over the input, not a perfect uniform
   lookup — training data skews toward relevant information appearing
   near prompt boundaries, and very long contexts push some content into
   a region the model attends to less reliably. The practical consequence
   is directly counter to the naive intuition: adding *more* correct,
   relevant information to context can make the model's actual answer
   *worse* if it pushes the truly critical fact into a low-attention
   region, or if it simply adds enough competing signal that the
   important fact gets diluted relative to everything else.

The combination of these three effects is why "context engineering" is a
real discipline rather than a solved problem that scaled away once
context windows got bigger: a bigger window raises the ceiling of what
*can* be included, but it does not make indiscriminate inclusion a good
strategy. The job is still to decide, deliberately, what belongs in
context for this specific call — a large window gives you more room to
be sloppy before something visibly breaks, not permission to stop
choosing.

## Key takeaways

- Context engineering supersedes prompt engineering as the harder
  problem because most tokens an LLM call processes come from retrieved
  docs, tool outputs, and history — not the hand-written prompt template.
- "Context" is a composite: system instructions + user message + RAG
  results + tool outputs + conversation history + persisted memory — each
  source needs its own inclusion/exclusion/compression decision.
- More context is never free: it costs more tokens (money), adds latency,
  and — critically — can degrade output quality via "lost in the middle"
  attention dilution, even when every included fact is technically
  correct and relevant.
- A larger context window raises the ceiling of what fits; it does not
  remove the need to deliberately choose what belongs in context for a
  given call.
""",
        ),
        LessonModule(
            title="Practical context engineering techniques",
            content=r"""
## Context budgeting: treat the window like a scarce resource

For any non-trivial application — a coding agent working across a large
codebase, a chat product with a long-running conversation — the context
window should be treated as a budget to allocate deliberately across
competing needs, not a bucket to fill until it errors. A practical
budgeting approach reserves rough token allotments per source ahead of
time: e.g., system instructions (small, fixed), a hard cap on retrieved
document tokens (even if more relevant chunks exist), a cap on how much
conversation history is replayed verbatim, and a reserved allotment for
the model's own output. When one source would exceed its budget (more
retrieved chunks look relevant than the RAG budget allows, or the
conversation has grown past the history budget), the system needs an
explicit policy for what to drop or compress — not an implicit "let it
overflow and let the API truncate for you," which truncates from
whichever end the API defaults to, not necessarily the least important
content.

For a long-running coding agent specifically, this shows up as: does the
agent keep the full text of every file it has read this session in
context, or does it summarize/discard files after use and re-read them
on demand if needed later? Keeping everything is simpler to implement and
gets expensive and dilutive fast; discarding and re-fetching costs an
extra tool call when something is needed again but keeps the working
context lean — this is a real tradeoff, not a solved default, and the
right answer depends on how often old file contents actually get reused
later in the session.

## Summarization and compression

When history or retrieved content exceeds budget, compressing it (rather
than truncating it blindly) preserves more useful signal per token.
Common strategies:

- **Rolling summarization**: periodically (e.g., every N turns) replace
  older conversation turns with an LLM-generated summary of "what
  happened and what matters going forward," keeping only recent turns
  verbatim. This trades exact wording for compactness — fine for most
  conversational context, risky if an exact prior instruction or number
  needs to be preserved precisely (summarization can silently drop or
  distort details).
- **Extractive compression**: instead of a generative summary, pull out
  only the specific spans that are relevant to the current task (e.g.,
  from a long retrieved document, keep only the paragraphs that mention
  the query's key terms) rather than the whole document. Cheaper and more
  faithful than generative summarization, but requires a relevance signal
  to decide what to extract.
- **Structured state instead of transcript replay**: for agentic systems,
  maintaining an explicit structured state object (e.g., "current plan,"
  "files modified so far," "open questions") that gets updated and
  re-serialized into context each turn, instead of replaying the entire
  raw conversation transcript, can be dramatically more token-efficient
  and also more reliable — the model reads a clean current-state summary
  instead of having to reconstruct it by re-reading a long history.

## Prioritization: what must be in context vs. what can be fetched on demand

Not everything potentially relevant needs to be pre-loaded into context.
A key architectural decision is what's pushed into context proactively
versus what's left retrievable via a tool call the model can issue only
if it decides it's needed:

- **Must be in context**: the current task/instruction, anything the
  model cannot function without on this specific call (e.g., the schema
  of the table it's about to query), and anything expensive to
  reconstruct if missed.
- **Fetch on demand via tool call**: large reference material (full API
  docs, a large codebase, a knowledge base) that's cheap to query
  precisely but expensive to include wholesale "just in case." This is
  the actual mechanism behind giving an agent a `search_codebase(query)`
  or `read_file(path)` tool instead of pasting the entire repository into
  the system prompt — it shifts the burden of relevance-filtering from
  "pre-load everything and hope attention sorts it out" to "let the model
  ask for exactly what it decides it needs, when it needs it," which is
  both cheaper and, per the lost-in-the-middle effect, often more
  accurate.

The general principle: context that's *reliably* needed on every call
belongs in the prompt; context that's *conditionally* needed belongs
behind a tool call the model invokes selectively.

## Context pollution: irrelevant content degrades output even when it fits

A distinct failure mode from budget overflow: content that technically
fits within the window and costs relatively little can still measurably
degrade output quality just by being present and irrelevant — competing
for attention, or in the worst case, being misinterpreted as relevant
instruction. Examples: including a large volume of loosely-related
retrieved chunks (rather than a smaller set of highly relevant ones)
can make the model's answer worse, not just slower, because it now has
more plausible-looking but wrong material to draw from; including stale
tool output from three turns ago that no longer reflects current state
can cause the model to act on outdated information even though newer,
correct information is also present, because both are given equal
positional weight; including boilerplate or verbose formatting in every
retrieved chunk (headers, metadata, repeated disclaimers) burns attention
budget without adding signal.

The engineering discipline here is closer to *editing* than *including*:
the question for each candidate piece of context is not "does this fit"
or "is this technically relevant," but "does including this make the
model's actual answer better" — which is a higher bar, and sometimes
means deliberately leaving out marginally-relevant material that would
otherwise dilute the genuinely important content.

## Key takeaways

- Context budgeting means allocating explicit token limits per source
  (system prompt, retrieval, history, output) and having a deliberate
  policy for what to drop or compress when a source exceeds its budget —
  not relying on implicit API truncation.
- Compression ranges from generative summarization (compact, lossy) to
  extractive pulls (faithful, needs a relevance signal) to maintaining
  structured state instead of replaying raw transcripts.
- Not everything relevant needs to be pre-loaded: content reliably needed
  every call belongs in the prompt; conditionally-needed reference
  material belongs behind an on-demand tool call.
- Context pollution — irrelevant or stale content that technically fits —
  degrades output quality even without exceeding any budget; the design
  question is "does this make the answer better," not "does this fit."
""",
        ),
    ],
    "rag-architecture": [
        LessonModule(
            title="The RAG pipeline end to end: ingestion, chunking, embedding",
            content=r"""
## Why RAG exists

Retrieval-Augmented Generation grounds an LLM's output in external,
current, verifiable text by retrieving relevant documents and inserting
them into the context window before generation — rather than relying
solely on facts baked into the model's weights during training (see
llm-fundamentals for why that parametric memory alone is unreliable and
can't reflect anything private or post-training-cutoff). The pipeline has
three stages that happen at different times: **ingestion** (offline, once
per document, or whenever content changes), **retrieval** (online, per
query), and **generation** (online, using what retrieval returned). This
module covers ingestion and chunking; the next covers retrieval and
reranking.

## Ingestion: turning source documents into searchable units

Raw source material — PDFs, wiki pages, code files, support tickets — is
rarely usable as a single retrieval unit: documents are too long to embed
usefully as one vector (a single embedding for a 50-page document
averages away most of its specific content) and too long to dump wholly
into context for every query that touches them. Ingestion splits
documents into smaller **chunks**, each of which gets its own embedding
and becomes an independently retrievable unit.

## Chunking strategy: the central tradeoff

**Chunk size vs. recall/precision tradeoff.** This is the single most
consequential decision in a RAG pipeline, and it's a genuine tradeoff, not
a solved default:

- **Smaller chunks** (e.g., 100-200 tokens) produce more precise,
  focused embeddings — a chunk containing exactly one idea embeds closer
  to queries about that specific idea, improving retrieval **precision**
  (less irrelevant material comes back with each retrieved chunk).
  Downside: small chunks lose surrounding context — a chunk might contain
  a pronoun ("it improved performance by 40%") without the sentence that
  established what "it" refers to, so even a correctly-retrieved chunk
  can be unusable or misleading in isolation. Small chunks also mean more
  total chunks, raising storage and retrieval-time cost.
- **Larger chunks** (e.g., 1000+ tokens) preserve more surrounding
  context per chunk, improving usability of what's retrieved, and improve
  **recall** for questions whose answer spans more text. Downside: the
  embedding for a large chunk is an average over more content, so it
  becomes less precisely matched to any single specific query — a large
  chunk touching five topics embeds as a blurry compromise between all
  five, and can fail to rank highly for a query about any one of them,
  even though the relevant sentence is in there somewhere. Larger chunks
  retrieved into context also cost more tokens (see context-engineering)
  and increase the chance of including irrelevant material alongside the
  relevant sentence.

There's no universally correct chunk size — it's tuned per corpus and
query pattern, typically by measuring retrieval quality (see the
evaluation module) at a few candidate sizes.

**Fixed-size vs. semantic chunking.**

- **Fixed-size chunking** splits text every N tokens (often with a
  sliding window), regardless of sentence or paragraph boundaries. Cheap,
  simple, and predictable in size — but can slice a sentence, a code
  function, or a table row in half, destroying the coherence of both
  resulting chunks.
- **Semantic/structural chunking** splits at natural boundaries —
  paragraph breaks, markdown headers, function/class boundaries in code,
  sentence boundaries — so each chunk is a coherent unit of meaning
  rather than an arbitrary token-count slice. This generally produces
  better-embedded, more usable chunks, at the cost of variable chunk
  sizes (harder to budget context precisely) and more implementation
  complexity (needs a document-structure-aware splitter, not just a
  token counter).

Most production systems use a hybrid: split on structural boundaries
first (headers, paragraphs), then further split any resulting section
that still exceeds the target token size, giving mostly-coherent chunks
with a bounded maximum size.

**Overlap.** Adjacent chunks commonly overlap by some fraction (e.g., a
200-token chunk with a 50-token overlap with its neighbor) so that
content near a chunk boundary — which would otherwise be split awkwardly
between two chunks, weakening both — appears fully within at least one
chunk. Overlap trades some storage/embedding redundancy for reduced risk
of losing meaning at boundaries.

## Embedding and storing

Each chunk is passed through an embedding model (a model trained
specifically to produce a single dense vector representing a text's
meaning — distinct from a generative LLM, though some providers offer
both from the same underlying architecture family) and the resulting
vector is stored in a **vector store** (a database optimized for
nearest-neighbor search over high-dimensional vectors — e.g., pgvector as
a Postgres extension, or a dedicated vector database), typically indexed
alongside the chunk's original text and metadata (source document,
section, date, permissions) for later retrieval and filtering.

It's worth being precise that the vector store holds the *embedding
vectors*, not the LLM's understanding — retrieval at query time is a
nearest-neighbor search over these precomputed vectors, entirely separate
from and prior to any generative LLM call.

## Key takeaways

- RAG has three stages: offline ingestion/chunking/embedding, then
  per-query retrieval, then generation using retrieved context.
- Chunk size is a precision/recall tradeoff: smaller chunks embed more
  precisely but lose context; larger chunks preserve context but embed
  as a blurrier, less-targeted match.
- Semantic/structural chunking (splitting at paragraph/header/function
  boundaries) generally beats naive fixed-size splitting because it keeps
  each chunk coherent, at the cost of implementation complexity.
- Overlap between adjacent chunks protects meaning that would otherwise
  be awkwardly split at a chunk boundary.
- The vector store holds precomputed embedding vectors for nearest-
  neighbor search — a separate, prior step from the generative LLM call
  that eventually uses the retrieved text.
""",
        ),
        LessonModule(
            title="Retrieval and reranking",
            content=r"""
## Dense retrieval: semantic similarity search

Dense retrieval embeds the incoming query with the same (or a compatible)
embedding model used during ingestion, then finds the nearest chunk
vectors by similarity metric (cosine similarity or dot product are the
common choices) — "nearest" in the embedding space, which per the
llm-fundamentals module approximates semantic relatedness. This is what
lets a query like "how do I cancel my subscription" retrieve a document
chunk that says "to end your plan, go to Settings" even though it shares
almost no exact words with the query — the strength of dense retrieval is
exactly this ability to match on meaning rather than surface form.

Dense retrieval's weakness is the mirror image of its strength: it can
underperform on queries where exact lexical/token match matters more than
semantic similarity — an error code (`ERR_504`), a specific product SKU,
an exact API method name, a person's name. Two texts can be embedded as
"similar" in a general semantic sense while differing on the one specific
token that actually matters for the query, and a dense retriever has no
special mechanism to weight that.

## Sparse retrieval: BM25 and exact term matching

Sparse retrieval (the modern standard is BM25, a refinement of TF-IDF)
scores documents by term-frequency statistics over the literal words in
the query — it's the mechanism traditional search engines and full-text
search (e.g., Postgres's built-in text search) are built on. It has no
notion of semantic similarity at all — `"cancel subscription"` and
`"terminate plan"` share no terms and score as unrelated under pure
BM25 — but it excels precisely where dense retrieval is weak: exact
matches on rare, specific terms (codes, identifiers, names, exact
phrases) score very highly, because BM25 explicitly rewards rare-term
matches.

## Hybrid retrieval: combining both

Because dense and sparse retrieval fail in complementary ways, production
RAG systems commonly run both in parallel and combine their results —
**hybrid retrieval**. A common combination method is reciprocal rank
fusion (merging two ranked lists by each document's rank position rather
than trying to normalize two different score scales directly, since a
BM25 score and a cosine similarity score aren't on a comparable numeric
scale). Hybrid retrieval generally outperforms either method alone on
real-world query mixes, because real user queries are a mix of
semantic-intent queries and exact-term queries, often within the same
query ("what's the error code for a timeout" needs both semantic
understanding of "timeout" and exact matching on whatever code format the
docs use).

## Metadata filtering

Retrieval is frequently narrowed by structured metadata before or
alongside the similarity search — e.g., restrict to chunks from documents
tagged with a specific product version, a date range, or a permission
level the requesting user has access to. This is a straightforward but
important production concern: without it, a vector search alone has no
way to enforce that a user only retrieves content they're authorized to
see, or that a query about "the current pricing" doesn't surface a
chunk from a two-years-stale pricing document that happens to embed
similarly.

## Why reranking improves precision after initial retrieval

Initial retrieval (dense, sparse, or hybrid) is optimized to be fast over
a large corpus — it typically returns a broad candidate set (e.g., top 50
or top 100 chunks) using a relatively cheap similarity computation.
**Reranking** adds a second, more expensive but more accurate step: a
cross-encoder model that takes the query and *each* candidate chunk
together as a single input (rather than embedding them separately and
comparing vectors) and directly scores how relevant that specific
chunk is to that specific query.

The mechanistic reason this improves precision: a bi-encoder (the
embed-query-and-chunk-separately-then-compare-vectors approach used in
initial retrieval) has to compress all of a chunk's meaning into one
fixed vector *before* it ever sees the query — it can't adjust what it
attends to based on what the query actually asks. A cross-encoder sees
query and chunk together and can attend directly to whether *this
specific chunk* answers *this specific query*, producing a more accurate
relevance judgment. The tradeoff is cost: a cross-encoder call is far
more expensive per (query, document) pair than a vector similarity
lookup, which is why it's only run on a modest, already-narrowed
candidate set (rerank the top 50 down to the top 5-10 that actually go
into context) rather than the whole corpus — running a cross-encoder over
every document in a large corpus for every query would be far too slow.

The typical production shape is therefore: cheap broad retrieval (dense/
sparse/hybrid) narrows a large corpus to a manageable candidate set, then
an expensive precise reranker narrows that candidate set to the final,
small set of chunks that actually get inserted into the LLM's context —
directly serving the context-engineering goal of putting only the most
relevant material into a token-constrained, attention-limited window.

## Key takeaways

- Dense retrieval matches on semantic similarity via embeddings; sparse
  retrieval (BM25) matches on exact term frequency — they fail in
  complementary ways, which is why hybrid retrieval generally beats
  either alone on real query mixes.
- Metadata filtering (permissions, date, version) is a necessary
  production concern that pure similarity search doesn't handle on its
  own.
- Reranking uses a cross-encoder that scores query+chunk jointly (more
  accurate but far more expensive) to re-sort an already-narrowed
  candidate set from initial retrieval — improving precision on the small
  final set that actually reaches the LLM's context.
- The standard production shape is cheap-broad-retrieval followed by
  expensive-narrow-reranking, not one or the other alone.
""",
        ),
        LessonModule(
            title="Evaluating RAG quality: groundedness and failure modes",
            content=r"""
## The RAG-specific failure mode: confidently wrong from bad retrieval

RAG is often pitched as a hallucination fix (see llm-fundamentals), and
it does help — but it introduces its own distinct failure mode: **a RAG
system that retrieves irrelevant or wrong chunks and then generates a
fluent, confident answer grounded in the wrong material.** This is often
worse than a plain LLM hallucination in practice, because the presence of
"sources" and "citations" creates an appearance of rigor that a bare
ungrounded answer doesn't — a wrong answer with a footnote reads as more
trustworthy than a wrong answer without one, even though the underlying
correctness is not actually improved by a bad citation. Retrieval failure
is silent by default: the system doesn't know it retrieved the wrong
chunk, and the generation step will produce a fluent answer from whatever
it was given, correct or not.

This means evaluating a RAG system requires checking two separate things
that are easy to conflate: did retrieval find the right material, and did
generation faithfully use what was retrieved. A system can fail at either
stage independently, and the fixes are different (better chunking/
retrieval/reranking vs. better prompting/generation).

## Groundedness: does the answer actually come from the retrieved context?

**Groundedness** (also called faithfulness) measures whether each claim
in the generated answer is actually supported by the retrieved context
that was provided — as opposed to being drawn from the model's
parametric memory (which might be right, might be outdated, might be
subtly different from what the authoritative retrieved source says) or
fabricated outright. A generated answer can be *factually correct* by
coincidence while being *ungrounded* (the model happened to know the
right answer from training, ignoring or not needing the retrieved
context at all) — this matters operationally because an ungrounded
correct answer today gives no guarantee of a correct answer tomorrow when
the underlying source document changes and the model's stale parametric
memory doesn't.

Groundedness is typically checked by an evaluation step (often
LLM-as-judge — see ai-evaluation) that takes the generated answer and the
retrieved context and asks: is every claim in this answer traceable to
something in this context? This is a different check from "is the answer
correct" — a well-designed RAG eval checks both, because a system that's
accidentally-correct-but-ungrounded is a latent reliability problem, not
a working system.

## Citation as both a UX feature and a verification mechanism

Having the model cite which retrieved chunk supports each claim (e.g.,
inline references to source documents) serves two purposes: it lets a
human user verify the answer against the original source directly, and it
gives an automated evaluation pipeline something concrete to check
(does the cited chunk actually contain the claim attributed to it,
mechanically checkable without needing a full LLM-judge call for the
simple case). Citation doesn't prevent ungrounded generation on its own —
a model can still fabricate a citation that doesn't actually support the
claim next to it — but it substantially improves *detectability* of
ungrounded answers, which is often the more achievable engineering goal
than eliminating the failure mode entirely.

## What a full RAG evaluation checks

A thorough RAG evaluation separates retrieval quality from generation
quality rather than only scoring the end-to-end answer:

- **Retrieval quality**: for a query with a known correct source
  document/chunk, did retrieval actually return it in the top-k results
  (recall@k), and how highly ranked was it (precision/ranking quality)?
  This can be measured with a golden dataset of (query, correct source)
  pairs, independent of anything the LLM generates afterward.
- **Groundedness**: given the retrieved context that was actually
  returned, is the generated answer's content supported by it?
- **Answer correctness**: is the final answer actually right (which
  requires the golden dataset to know the correct answer, not just the
  correct source)?

Separating these matters because the fix for a low-retrieval-quality
failure (better chunking, a reranker, better embeddings, hybrid
retrieval) is completely different from the fix for a
low-groundedness-with-good-retrieval failure (the right chunk was
retrieved, but the model still ignored or misread it — a generation/
prompting problem). Scoring only the end-to-end answer conflates these
and makes it much harder to know what to actually change.

## Key takeaways

- The characteristic RAG failure mode is confident generation from
  irrelevant or wrong retrieved chunks — arguably worse than a bare
  hallucination because citations create unearned trust.
- Groundedness (is the answer traceable to the retrieved context) is a
  distinct property from correctness — an answer can be accidentally
  correct while ungrounded, which is a latent reliability risk.
- Citations improve detectability of ungrounded answers for both human
  reviewers and automated checks, even though they don't prevent
  fabrication outright.
- A rigorous RAG evaluation separates retrieval quality (did we fetch the
  right chunk) from groundedness (did generation use it faithfully) from
  answer correctness — conflating them into one end-to-end score hides
  which stage actually needs fixing.
""",
        ),
    ],
    "ai-agents-tool-use": [
        LessonModule(
            title="The agent loop and tool calling mechanics",
            content=r"""
## What "tool calling" mechanically is

An LLM, by itself, only produces text. Tool calling (also called function
calling) is an API-level convention that lets the model produce
**structured, machine-parseable output requesting an action**, instead of
just prose — and lets the application feed the result of that action back
in. The model itself never executes anything; it only ever outputs text
(or now, structured data) that your application code interprets and
acts on.

The mechanics, concretely, for a single tool-calling turn:

1. Your application sends the model a prompt *and* a list of available
   tools, each described by a name, a natural-language description of
   what it does, and a schema for its parameters (commonly JSON Schema):

```json
{
  "name": "search_flights",
  "description": "Search available flights between two airports on a given date.",
  "parameters": {
    "type": "object",
    "properties": {
      "origin": {"type": "string", "description": "IATA airport code"},
      "destination": {"type": "string", "description": "IATA airport code"},
      "date": {"type": "string", "description": "YYYY-MM-DD"}
    },
    "required": ["origin", "destination", "date"]
  }
}
```

2. If the model decides (based purely on next-token prediction over its
   training, now conditioned on the tool descriptions in context) that
   calling a tool is the best continuation, it outputs a structured call
   instead of a prose answer:

```json
{"tool": "search_flights", "arguments": {"origin": "JFK", "destination": "LAX", "date": "2026-09-01"}}
```

3. Your application code — not the model — parses this, validates it
   against the schema, and actually executes the corresponding function
   (calls a real flights API, hits a database, runs a calculation).
4. The **result** of that execution is serialized back into the
   conversation as a new message (a "tool result" or "function result"
   role, depending on the API), and the whole updated conversation —
   original prompt, the model's tool call, and the tool's result — is
   sent back to the model for another generation step.
5. The model now generates its next output conditioned on that real
   result: it might produce a final prose answer, or decide to call
   another tool, and the loop continues.

This is the entire mechanism — there is no hidden execution capability in
the model. "The model calls a tool" is a convenient shorthand for "the
model outputs structured intent, and the application executes it and
reports back." Getting this wrong (e.g., assuming the model can directly
affect the world) is a common source of confused agent-system design.

## The agent loop

An "agent," in the concrete engineering sense used here, is this
tool-call-then-feed-result-back cycle run repeatedly, with the model
deciding at each step whether to call another tool or produce a final
answer, until it decides the task is done (or a step/iteration limit is
hit). Pseudocode for the loop:

```python
messages = [system_prompt, user_task]
while True:
    response = llm.generate(messages, tools=available_tools)
    if response.is_tool_call:
        result = execute_tool(response.tool_call)          # your code runs this
        messages.append(response.tool_call)
        messages.append(tool_result_message(result))
        continue                                             # loop again
    else:
        return response.text                                 # model decided it's done
```

Every iteration re-sends the growing message history to the model — which
is exactly why context engineering (see that competency) matters
intensely for agents: a long-running agent loop accumulates tool calls
and results in context turn after turn, and without active management
(summarization, discarding stale results, structured state) that context
grows, gets diluted, and gets expensive fast.

## What "planning" means concretely, and ReAct

"Planning" is not a separate module bolted onto the model — it's the same
next-token-prediction mechanism, applied to producing text that
*describes* a plan before or interleaved with taking actions, because
models trained/prompted to do this empirically perform better on
multi-step tasks. The most common concrete pattern is **ReAct**
(Reason + Act): the model is prompted to interleave explicit reasoning
text with tool calls — e.g., produce a short "Thought: I need to find the
user's current subscription tier before I can check upgrade eligibility"
before issuing the corresponding tool call, rather than jumping straight
to actions with no visible reasoning trace.

This matters for two concrete engineering reasons: (1) the reasoning
text becomes part of the context for the *next* generation step, so it
functions as the model "showing its work" in a way that measurably
improves its own subsequent decisions (this is closely related to why
chain-of-thought prompting improves accuracy generally — reasoning
tokens give the model more computation, spread across more forward
passes, before committing to an action); and (2) it gives a human
debugging the agent's behavior a visible trace of *why* the model took
each action, rather than an opaque sequence of tool calls with no stated
rationale — which is often the difference between a debuggable agent
system and one where failures are inscrutable.

## Key takeaways

- Tool calling is the model outputting structured intent (name +
  arguments matching a schema); your application code, not the model,
  actually executes the action and reports the result back into context.
- The agent loop is: generate → (if tool call) execute and append result
  → generate again → ... → final answer. Nothing more mystical than that
  cycle, repeated.
- Every loop iteration re-sends the accumulated history, which is why
  context engineering (budgeting, compression, discarding stale results)
  is not optional for any non-trivial agent — it directly determines
  cost, latency, and accuracy as the loop runs longer.
- "Planning" is the model generating explicit reasoning text (ReAct-style
  "Thought: ..." steps) interleaved with actions — it improves both the
  model's own subsequent decisions (more computation before committing to
  an action) and human debuggability of the agent's behavior.
""",
        ),
        LessonModule(
            title="Workflow vs. single agent vs. multi-agent",
            content=r"""
## Three architectures, and why the choice isn't cosmetic

"Agent" has become a marketing word applied to almost any LLM-powered
system, which erases a genuinely important engineering distinction.
There are at least three meaningfully different architectures for
building an LLM-powered system that takes multiple steps, and picking the
wrong one has real cost — in reliability, debuggability, and often
literal dollar cost from unnecessary LLM calls.

- **Workflow**: a fixed, predetermined sequence of steps, where the
  *code* — not the model — decides what happens next and in what order.
  LLM calls may appear at individual steps (e.g., "step 3: summarize this
  document with an LLM call"), but the control flow itself is ordinary
  deterministic code: `if`/`else`, a fixed pipeline, a state machine with
  explicit transitions defined in advance.
- **Single agent**: the LLM itself decides, at each step, what to do
  next — which tool to call, whether the task is done, whether to try a
  different approach after a failure. Control flow lives in the model's
  own generated decisions (the agent loop from the previous module), not
  in code written in advance to handle every case.
- **Multi-agent**: multiple independent agent loops (each potentially
  with its own context, tools, and even a different underlying model)
  collaborating on a task — e.g., an orchestrator agent that delegates
  independent subtasks to specialized worker agents and combines their
  results.

## The actual decision criteria

The distinguishing question is not "how impressive should this look" —
it's **how predictable is the process, and does any step genuinely need
dynamic judgment**:

- If the sequence of steps is knowable in advance and doesn't need to
  change based on intermediate results in ways you can't enumerate ahead
  of time — use a **workflow**. Example: "extract structured fields from
  an invoice, validate them against business rules, write to the
  database" is a fixed pipeline; even though step 1 uses an LLM, nothing
  about the *order* or *branching* of these steps needs the model to
  decide it dynamically. Workflows are more reliable (deterministic
  control flow is easier to test exhaustively), cheaper (no wasted
  reasoning/planning tokens spent re-deriving a process that's the same
  every time), and far easier to debug (a failure is in a known step, not
  somewhere in an opaque decision the model made).
- If the number of steps, their order, or which tools are needed
  genuinely can't be known in advance and depends on what earlier steps
  discover — use a **single agent**. Example: "investigate why this
  production error is happening" requires the system to decide, based on
  what it finds at each step, what to look at next — that's a case where
  hardcoding the sequence in advance isn't possible because the
  investigation path is exactly what's unknown going in.
- If the task decomposes into genuinely **independent** subtasks that
  don't need to share evolving context with each other as they run — use
  **multi-agent**. Example: "research five unrelated competitors and
  summarize each" parallelizes cleanly because researching competitor A
  doesn't need to know anything discovered while researching competitor
  B. Multi-agent buys you parallelism (wall-clock speedup) and isolation
  (each subagent's context doesn't get polluted by the others' work — see
  context-engineering) for tasks that are actually decomposable this way.

## Why "more agents" is usually worse, not better

The intuitive appeal of multi-agent systems — "have specialized agents
handle different aspects and combine their work" — runs into two
compounding costs that make it a worse default than it sounds:

1. **Coordination overhead.** Subtasks that are not actually independent
   (they depend on shared, evolving context — a design decision made by
   one worker that the others need to know about) require the
   orchestrator to explicitly pass that context between agents, which
   means re-serializing and re-transmitting state across agent
   boundaries — extra LLM calls, extra tokens, extra places for
   information to get lost or garbled in translation between agents. A
   single agent working through the same task sequentially has that
   context sitting right there in its own running conversation; splitting
   the work doesn't remove the need for that information to flow, it
   just adds a communication step for it.
2. **Compounding error rates.** If each individual agent call has some
   independent probability of a mistake (misunderstanding a subtask,
   a subtly wrong tool call, a hallucinated detail), then a pipeline of N
   agents each with reliability r has combined reliability that
   multiplies down (roughly r^N for a strictly sequential dependency
   chain) — more agents in a chain is *structurally* more failure-prone,
   not less, unless each additional agent is doing genuinely independent
   parallel work rather than being one more link in a sequential chain
   that the task now depends on end to end.

The practical rule of thumb: start with the simplest architecture that
could work — a workflow if the process is knowable, a single agent if it
needs dynamic judgment — and only reach for multi-agent when a task
demonstrably decomposes into independent parallel work, not merely
because splitting responsibilities *sounds* like better engineering
practice by analogy to microservices. The analogy is misleading:
microservices trade complexity for independent scaling/deployment of
reliable deterministic code; multi-agent systems add coordination
overhead on top of components (LLM calls) that are individually less
reliable than deterministic code to begin with, so the tradeoff math is
different and less favorable than it looks by analogy.

## Key takeaways

- Workflow (code decides control flow), single agent (model decides
  control flow), and multi-agent (multiple independent agent loops
  collaborating) are distinct architectures, not points on a hype
  spectrum — the choice should be driven by the task's actual structure.
- Use a workflow when the process is predictable in advance; use a single
  agent when steps genuinely require dynamic judgment that can't be
  hardcoded; use multi-agent when subtasks are genuinely independent and
  benefit from parallelism/isolation.
- Multi-agent systems add real coordination overhead (context has to be
  explicitly passed between agents) and compounding error rates
  (reliability multiplies down across a sequential chain of imperfect
  agents) — "more agents" is a cost to justify, not a default upgrade.
- Default to the simplest architecture that fits the task's actual
  structure; reach for multi-agent only when the task demonstrably
  decomposes into independent parallel work.
""",
        ),
    ],
    "ai-evaluation": [
        LessonModule(
            title="Golden datasets and the evaluation loop",
            content=r"""
## The wrong question and the right one

"Does the AI work?" is not answerable — it has no fixed truth value
because LLM output is non-deterministic (see llm-fundamentals on
sampling) and "works" is underspecified (works on what inputs, by what
standard, how often). The question that's actually answerable, and the
one that lets you improve a system over time instead of guessing, is
"**how do I know it works, and how often does it fail, and on what**" —
which requires an explicit, repeatable measurement, not a vibe formed
from trying a few prompts by hand. Trying prompts manually and eyeballing
the output is a legitimate first pass during initial development, but it
does not scale to catching regressions, does not give you a number to
compare before/after a change, and is exactly the practice that lets a
"fix" for one case silently break three others without anyone noticing
until a user hits it in production.

## What a golden dataset is

A golden dataset is a fixed, curated set of (input, expected-output-or-
pass-criterion) pairs that the system gets evaluated against, repeatedly,
as the system changes. It plays the same role a test suite plays for
conventional software — a concrete, reproducible check that you didn't
break something — adapted to the reality that LLM outputs aren't exact-
match deterministic the way a function's return value is.

**What makes a golden dataset good, concretely:**

- **Representative of real usage.** Pulled from (or closely modeled on)
  actual production queries/tasks, not just cases that were easy to think
  up — a dataset built entirely from the engineer's own imagined
  scenarios systematically misses the actual distribution of real inputs,
  which is usually messier and weirder than what you'd invent.
- **Includes edge cases deliberately, not incidentally.** Ambiguous
  inputs, adversarial inputs, empty/malformed inputs, inputs where the
  correct behavior is to refuse or say "I don't know" rather than answer
  — these need to be *deliberately* included, because they're exactly the
  cases most likely to be absent from a dataset built only from "typical"
  examples, and they're disproportionately where real failures cluster.
- **Has a clear, checkable pass/fail criterion per example.** Not
  necessarily an exact-string match (LLM output is rarely exactly
  reproducible), but something concrete enough that two different people
  — or an automated check — would agree on whether a given output passed:
  "the correct tool was called with the correct arguments," "the answer
  contains these key facts and doesn't contradict them," "the output
  matches this schema," rather than a vague "the answer should be good."
- **Sized and maintained deliberately.** A golden dataset that never
  grows misses new failure modes discovered in production; one that grows
  without curation accumulates redundant or low-signal examples that slow
  down the eval loop without adding new coverage. Production failures
  worth generalizing from should be added as new golden examples — this
  is the direct link between "a real user hit a bug" and "the eval suite
  now guards against that bug specifically."

## The build → evaluate → observe-failure → change → re-evaluate loop

This is the operating loop that a golden dataset enables, and it's the
actual mechanism by which an LLM-powered system improves reliably over
time, as opposed to improving by luck:

1. **Build** — implement or change the system (a new prompt, a different
   retrieval strategy, a new model version, a tweaked tool description).
2. **Evaluate** — run the full golden dataset against the current system
   and get a score (pass rate, or a breakdown by category/failure type).
3. **Observe failure** — look at exactly which examples failed and *why*
   — not just the aggregate score. The aggregate number tells you
   *whether* something regressed; only looking at individual failures
   tells you *what* actually went wrong and what to change.
4. **Change** — make a targeted fix aimed at the specific observed
   failure mode (better retrieval for a groundedness failure, a clearer
   tool description for a wrong-tool-call failure, a prompt clarification
   for a formatting failure).
5. **Re-evaluate** — run the *entire* dataset again, not just the
   examples that were failing before. This step is the one most often
   skipped under time pressure, and it's the one that catches the
   specific failure mode this whole module is about: a change that fixes
   the observed failure while silently breaking a previously-passing case
   elsewhere (see the next module's discussion of regression suites).

The loop only works if evaluation is cheap and fast enough to run after
every meaningful change — a golden dataset that takes hours to run or
requires manual grading of every example gets skipped under deadline
pressure, which defeats its purpose. This is part of why automated
scoring mechanisms (deterministic checks, LLM-as-judge — covered in the
next module) matter operationally, not just as a nice-to-have: they're
what keeps the loop's step 2 cheap enough to actually run every time.

## Key takeaways

- "Does it work" isn't measurable; "what's the pass rate on a fixed,
  representative dataset, and what specifically fails" is — that
  reframing is what makes systematic improvement possible.
- A good golden dataset is representative of real usage, deliberately
  includes edge cases (not just typical inputs), and has a concrete,
  checkable pass/fail criterion per example rather than a vague quality
  judgment.
- The build-evaluate-observe-change-re-evaluate loop is the actual
  mechanism for reliable improvement; skipping the full re-evaluation
  step is what lets a fix for one case silently regress another.
- The loop only sustains itself if evaluation is cheap and fast enough to
  run after every change — which is why automated scoring methods matter
  operationally, not just as nice-to-have tooling.
""",
        ),
        LessonModule(
            title="Evaluation techniques: deterministic checks, LLM-as-judge, and regression suites",
            content=r"""
## Deterministic checks: cheap, precise, limited in scope

Wherever a golden example's pass criterion can be checked by ordinary
code — not by asking another model to judge — do that first, because
it's cheap, perfectly reproducible, and has zero risk of the evaluator
itself being wrong in a way that's hard to notice. Concrete cases where
deterministic checks apply directly:

- **Exact match / structured output validation**: if the task is
  extraction or classification with a well-defined correct answer, check
  the output against it directly (string equality, schema validation, or
  a numeric tolerance for a computed value).
- **Tool-call correctness**: for an agentic system (see
  ai-agents-tool-use), a large and important class of failures is
  entirely checkable without any judgment call — did the system call the
  *correct tool* (right name), with the *correct arguments* (matching
  expected values, or satisfying constraints like "date is in the
  future"), *in the correct order* if order matters for the task. This is
  ordinary code comparing the actual tool-call trace against an expected
  one from the golden example — no LLM judge needed, no ambiguity, fully
  reproducible. This matters because tool-call correctness is often the
  single highest-value thing to check in an agent system: a wrong tool
  call is a concrete, mechanical failure, not a matter of interpretation.
- **Format/schema conformance**: does the output parse as valid JSON
  matching the expected schema, is a required field present, is a numeric
  value within a valid range — all directly checkable with code.

The limitation is scope: deterministic checks only work when correctness
is well-defined enough to encode as a rule. They can't judge whether a
free-text explanation is *good*, whether a summary captures the
*important* points, or whether an answer is *faithful* to retrieved
context (groundedness — see rag-architecture) — these require judging
open-ended text against a more holistic standard.

## LLM-as-judge: when it's appropriate, and its own failure modes

For exactly the cases deterministic checks can't cover — open-ended
text quality, groundedness, whether an explanation is helpful — a common
approach is **LLM-as-judge**: use a (typically stronger or
differently-prompted) LLM to evaluate the system's output against a
rubric, given the golden example's context and expected criteria. This
scales far better than pure human evaluation while still being able to
make the kind of holistic judgment a rule-based check can't.

LLM-as-judge is appropriate when the judgment is genuinely about
open-ended quality that resists hard-coded rules, and when the judge is
given a specific, narrow rubric to apply — "does this answer correctly
state the customer's refund eligibility as described in this policy
document" is a well-scoped judging task; "is this answer good" is not,
because it gives the judge nothing concrete to anchor on, which produces
noisy and inconsistent scores.

Its own failure modes are worth naming explicitly, because trusting an
LLM judge uncritically defeats the purpose of evaluation in the first
place:

- **Judge bias**: LLM judges have been shown to systematically favor
  longer answers, answers stylistically similar to their own typical
  output, and answers that merely *sound* confident and well-structured —
  independent of actual correctness. A judge model can reward the same
  surface-level fluency that causes hallucination to go undetected by a
  human in the first place (see llm-fundamentals).
  Judge prompts that explicitly ask for a rubric-based score against
  stated criteria, rather than an open-ended "rate this answer,"
  meaningfully reduce (not eliminate) this effect.
- **Inconsistency**: the same (input, output) pair judged twice by an
  LLM judge can get different scores, for the same sampling-non-
  determinism reasons covered in llm-fundamentals — mitigated by using
  low/zero temperature for judge calls specifically (quality of the
  *generation* being judged benefits from variety; the *judging* step
  benefits from consistency) and, for high-stakes evaluation, averaging
  over multiple judge calls or having multiple judge prompts cross-check.
- **The judge can share the same blind spots as the system being judged**,
  especially if judge and system are the same underlying model — a judge
  built on the same model family may fail to catch a factual error the
  base model itself would also generate, because both share the same gaps
  in training data. Using a different, ideally stronger, model as judge
  than the one being evaluated mitigates this, though doesn't eliminate
  it entirely.

The practical stance: LLM-as-judge is a real, useful, necessary tool for
evaluating open-ended output at scale — but its scores are themselves
noisy measurements with known systematic biases, not ground truth. Spot-
check judge scores against human judgment periodically, especially when
first setting up a judge rubric, rather than trusting the automated score
blindly forever.

## Human evaluation

Still the gold standard for the hardest-to-specify quality judgments —
particularly early in building an eval rubric (to establish what "good"
even means for this task before trying to automate judging it), and for
periodic spot-checking of both the system's outputs and the LLM judge's
scores against actual human standards. Human eval doesn't scale to
running after every change, which is exactly why it's typically used to
calibrate and validate the cheaper automated methods (deterministic
checks, LLM-as-judge) rather than replacing them for everyday iteration.

## Building a regression suite

A regression suite is the accumulation, over time, of the golden dataset
plus specifically every case that has previously failed in production or
during development — each converted into a permanent golden example once
it's fixed. The purpose is direct: a "fix" for one case is only
confirmed *safe* once you've verified it doesn't silently break any
previously-passing case, and the only way to verify that mechanically
(rather than by hoping) is to re-run the entire accumulated suite, not
just the example that was just fixed, after every change.

This is precisely why step 5 of the evaluation loop from the previous
module ("re-evaluate the *entire* dataset, not just what was failing")
matters as a discipline: a regression suite is only doing its job if it's
actually run in full, every time — a suite that exists but only gets
partially checked provides false confidence, which is arguably worse than
having no suite and knowing you're flying blind.

## Key takeaways

- Deterministic checks (exact match, tool-call correctness, schema
  validation) should be used wherever correctness is rule-encodable —
  they're cheap, exact, and have no evaluator-reliability risk of their
  own.
- LLM-as-judge fills the gap for open-ended quality judgments
  deterministic checks can't cover, but carries real failure modes —
  length/style bias, inconsistency, and shared blind spots with the
  system it's judging — that need active mitigation (rubric-based
  prompts, low temperature, a different/stronger judge model, periodic
  human spot-checks).
- Human evaluation doesn't scale to every iteration but is essential for
  calibrating what "good" means before automating a judge, and for
  periodically validating that automated scores still track real quality.
- A regression suite is the golden dataset plus every previously-fixed
  production failure, and it only provides real protection if the *full*
  suite is re-run after every change — partial re-checking creates false
  confidence.
""",
        ),
    ],
}
