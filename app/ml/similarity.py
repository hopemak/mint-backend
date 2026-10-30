import re
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

_TOKEN = re.compile(r"[a-z0-9]+")


def _norm(t):
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def token_list(text):
    return [_norm(t) for t in _TOKEN.findall((text or "").lower())
            if len(t) > 2 and t not in ENGLISH_STOP_WORDS]


def tokens(text):
    return set(token_list(text))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare_ideas(new_text, candidates, cos_min=0.45, jac_min=0.25, top_k=5):
    """candidates: list of {"id": ..., "title": ..., "text": ...}"""
    cands = [c for c in candidates if (c.get("text") or "").strip()]
    if not (new_text or "").strip() or not cands:
        return []
    texts = [new_text] + [c["text"] for c in cands]
    try:
        m = TfidfVectorizer(analyzer=token_list,
                            sublinear_tf=True).fit_transform(texts)
    except ValueError:  # empty vocabulary
        return []
    cos = cosine_similarity(m[0:1], m[1:]).ravel()
    new_tokens = tokens(new_text)
    out = []
    for c, cs in zip(cands, cos):
        js = jaccard(new_tokens, tokens(c["text"]))
        out.append({
            "id": c.get("id"),
            "title": c.get("title"),
            "cosine": round(float(cs), 3),
            "jaccard": round(js, 3),
            "score": round(0.6 * float(cs) + 0.4 * js, 3),
            "possible_duplicate": bool(cs >= cos_min and js >= jac_min),
        })
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:top_k]
