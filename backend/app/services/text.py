"""Text normalisation helpers shared by evaluation and roleplay matching."""

import re

CONTRACTIONS = {
    "i'm": "i am", "you're": "you are", "we're": "we are", "they're": "they are", "it's": "it is",
    "that's": "that is", "what's": "what is", "there's": "there is", "he's": "he is", "she's": "she is",
    "i'd": "i would", "i'll": "i will", "you'll": "you will", "we'll": "we will", "can't": "cannot",
    "won't": "will not", "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not", "i've": "i have", "let's": "let us",
    "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
}
_PUNCT = re.compile(r"[^\w\s']")


def normalize_words(text: str) -> list[str]:
    text = text.lower().replace("\u2019", "'")
    text = _PUNCT.sub(" ", text)
    words: list[str] = []
    for w in text.split():
        w = w.strip("'")
        if not w:
            continue
        words.extend(CONTRACTIONS.get(w, w).split())
    return words
