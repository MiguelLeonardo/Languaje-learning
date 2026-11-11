from app.services.evaluation import WordStatus, evaluate, similarity
from app.services.feedback import build_feedback
from app.services.text import normalize_words


def test_normalize_handles_contractions_and_punctuation():
    assert normalize_words("I'm fine, thanks!") == ["i", "am", "fine", "thanks"]
    assert normalize_words("It\u2019s OK") == ["it", "is", "ok"]


def test_perfect_answer_passes():
    ev = evaluate("Can I have a coffee, please?", "can i have a coffee please", 0.75)
    assert ev.passed and ev.score == 1.0 and ev.accuracy == 1.0


def test_missing_and_substituted_words_detected():
    ev = evaluate("Can I have a coffee, please?", "can I half a coffee", 0.75)
    statuses = {w.expected: w.status for w in ev.words if w.expected}
    assert statuses["have"] == WordStatus.MISPRONOUNCED
    assert statuses["please"] == WordStatus.MISSING
    assert not ev.passed
    assert set(ev.problem_words) == {"have", "please"}


def test_extra_words_reduce_fluency():
    ev = evaluate("Thank you", "uh thank you um", 0.7)
    assert ev.fluency < 1.0
    assert any(w.status == WordStatus.EXTRA for w in ev.words)


def test_empty_transcript_scores_zero():
    ev = evaluate("Thank you", "", 0.7)
    assert ev.score == 0 and not ev.passed


def test_confidence_blends_into_score():
    ev = evaluate("Thank you", "thank you", 0.7, confidence=0.5)
    assert ev.score == 0.9


def test_insert_only_replace_branch():
    ev = evaluate("a b", "x y z", 0.5)
    assert any(w.status == WordStatus.EXTRA for w in ev.words)


def test_similarity():
    assert similarity("How much is it?", "how much is it") == 1.0
    assert similarity("", "hi") == 0.0


def test_feedback_levels_and_tips(tmp_path):
    from app.content.schema import GlossaryEntry, Phrase

    phrase = Phrase(id="p", text="Can I have a coffee, please?", translation="x",
                    glossary=[GlossaryEntry(word="have", meaning="tener", ipa="hæv"),
                              GlossaryEntry(word="please", meaning="por favor")])
    fb = build_feedback(evaluate(phrase.text, "um can I half a coffee", 0.75), phrase)
    assert fb.level == "retry"
    issues = {t.issue for t in fb.tips}
    assert issues == {"mispronounced", "missing", "extra"}
    assert any("/hæv/" in t.advice for t in fb.tips)
    assert any("por favor" in t.advice for t in fb.tips)
    assert build_feedback(evaluate("Thank you", "thank you", 0.7)).level == "excellent"
    assert build_feedback(evaluate("a b c d e f g h i j", "a b c d e f g h i", 0.7)).level == "good"
