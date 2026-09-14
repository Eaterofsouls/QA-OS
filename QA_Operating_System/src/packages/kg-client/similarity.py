"""Retrieval-based-memory support: TF-IDF cosine similarity over stored
Requirement text.

This is deliberately NOT a vector-embedding search. There is no embedding
model, no external service, and no new dependency here -- just stdlib
tokenization, term-frequency / inverse-document-frequency weighting, and
cosine similarity over the resulting sparse vectors. That was an explicit
constraint on this feature (see README.md §6/§7): "token-overlap or TF-IDF
cosine similarity over requirement text is sufficient -- do NOT silently
introduce a vector embedding dependency."

If someone later wants real semantic (embedding-based) similarity, that is
a deliberate, separately-approved upgrade, not something to sneak in here.

Used by KGClientStub.find_similar_requirements() (stub.py) to find past
Requirement nodes worth surfacing as few-shot context before a new
assessment. Kept as a standalone module (no KGClientStub-specific state) so
it can be unit-tested and reasoned about on its own.
"""
import math
import re
from collections import Counter

# Empirically chosen, not tuned against a real dataset (none exists yet --
# see README.md §9 "no real LLM call has ever been made through this
# pipeline"). At the scale of short, single-sentence requirement text,
# cosine similarity over TF-IDF vectors reliably separates requirements
# that genuinely share subject matter (~0.3-0.6+ for near-duplicates or
# close paraphrases) from coincidental overlap on a couple of common words
# (~0.05-0.15). 0.2 sits below the former and above the latter, and errs
# toward precision: injecting a WRONG "similar past requirement" into the
# prompt as grounding is worse than injecting none, so a borderline match
# is skipped rather than included. Revisit once real usage data exists.
DEFAULT_SIMILARITY_THRESHOLD = 0.2

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# A short, generic stopword list -- just enough that shared articles/
# prepositions/modal verbs in short requirement sentences ("must", "in",
# "via", "the") don't dominate the similarity score. Not exhaustive or
# linguistically rigorous; this is intentionally simple (see module
# docstring), not a NLP pipeline.
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on",
    "for", "with", "is", "are", "be", "must", "should", "will", "shall",
    "this", "that", "it", "as", "by", "at", "from", "via", "into", "when",
})


def tokenize(text: str) -> list[str]:
    """Lowercase, alphanumeric-only tokenization with stopwords removed."""
    return [tok for tok in _TOKEN_RE.findall(text.lower()) if tok not in _STOPWORDS]


def tfidf_vectors(documents: list[str]) -> list[dict[str, float]]:
    """Compute one TF-IDF weight vector (term -> weight) per document.

    Document frequency (and therefore IDF) is computed over the full input
    list, so the query text (conventionally documents[0], see
    find_similar_requirements below) contributes to the vocabulary/IDF
    calculation too -- with the very small corpora this system will have
    early on, excluding it would make IDF close to meaningless.

    Returns a list in the same order as `documents`. Uses smoothed IDF
    (`ln((1 + N) / (1 + df)) + 1`) so a term's weight is never zero or
    undefined, including for a corpus of size 1.
    """
    tokenized_docs = [tokenize(doc) for doc in documents]
    n_docs = len(tokenized_docs)

    document_frequency: Counter = Counter()
    for tokens in tokenized_docs:
        for term in set(tokens):
            document_frequency[term] += 1

    vectors: list[dict[str, float]] = []
    for tokens in tokenized_docs:
        term_frequency = Counter(tokens)
        vector: dict[str, float] = {}
        for term, count in term_frequency.items():
            idf = math.log((1 + n_docs) / (1 + document_frequency[term])) + 1
            vector[term] = count * idf
        vectors.append(vector)
    return vectors


def cosine_similarity(vector_a: dict[str, float], vector_b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors. Returns 0.0 for
    an empty vector on either side (e.g. text that tokenized to nothing
    after stopword removal) rather than raising a division error.
    """
    if not vector_a or not vector_b:
        return 0.0
    shared_terms = set(vector_a) & set(vector_b)
    dot_product = sum(vector_a[term] * vector_b[term] for term in shared_terms)
    norm_a = math.sqrt(sum(weight * weight for weight in vector_a.values()))
    norm_b = math.sqrt(sum(weight * weight for weight in vector_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)
