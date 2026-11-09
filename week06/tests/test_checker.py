"""No-key tests for the checker: the code that compares a critique with the requirements (spec behaviors 14-22).

    .venv/bin/python -m pytest week06/tests -v     # from the repo root; no key, well under a second
"""
from critique import check, disagreements, extract_json, text_matches

REQS = ["The Sun is shown", "Exactly eight planets are shown", "Saturn is drawn with rings"]


def critique_with(*met):
    return {"checks": [{"requirement": r, "met": m, "evidence": "x"} for r, m in zip(REQS, met)]}


def test_all_met_is_ok():
    assert check(REQS, critique_with(True, True, True)) == {"ok": True, "problems": [], "unmet": [], "missing": [], "extra": []}


def test_unmet_requirement_is_reported_by_name():
    result = check(REQS, critique_with(True, False, True))
    assert not result["ok"]
    assert result["unmet"] == ["Exactly eight planets are shown"]


def test_met_must_be_true_not_a_truthy_string():
    c = critique_with(True, True, True)
    c["checks"][2]["met"] = "yes"
    assert check(REQS, c)["unmet"] == ["Saturn is drawn with rings"]


def test_missing_requirement_is_a_problem_even_if_the_rest_pass():
    partial = {"checks": [{"requirement": REQS[0], "met": True}, {"requirement": REQS[1], "met": True}]}
    result = check(REQS, partial)
    assert not result["ok"]
    assert result["missing"] == [REQS[2]]


def test_invented_requirement_is_flagged():
    c = critique_with(True, True, True)
    c["checks"].append({"requirement": "Pluto is shown", "met": False})
    result = check(REQS, c)
    assert result["extra"] == ["Pluto is shown"]
    assert not result["ok"]


def test_requirement_text_is_matched_ignoring_case_and_punctuation():
    c = {"checks": [{"requirement": "the sun is shown.", "met": True},
                    {"requirement": "EXACTLY eight planets are shown", "met": True},
                    {"requirement": "Saturn is drawn with rings!", "met": True}]}
    assert check(REQS, c)["ok"]


def test_non_json_reply_is_a_failed_critique_not_a_crash():
    for reply in ["Sorry, I can't see any image.", "", None, '{"checks": "all good"}', "[1, 2]"]:
        result = check(REQS, extract_json(reply) if reply != '{"checks": "all good"}' else {"checks": "all good"})
        assert not result["ok"]
        assert result["missing"] == REQS


def test_json_inside_prose_and_fences_is_extracted():
    text = 'Here you go:\n```json\n{"checks": [{"requirement": "a", "met": true}]}\n```\nHope that helps.'
    assert extract_json(text) == {"checks": [{"requirement": "a", "met": True}]}


def test_title_is_compared_in_code():
    assert text_matches("Volcano Cross-Section", "  volcano cross section ")
    assert not text_matches("Volcano Cross-Section", "Volcano Cross-Sectoin")
    assert not text_matches("Phases of the Moon", "Phases of the Moon Moon")
    assert not text_matches("The Rock Cycle", None)


def test_disagreements_between_two_critics():
    a = [{"name": "solar-system", "critique": critique_with(True, True, True), "text_read": "The Solar System"}]
    b = [{"name": "solar-system", "critique": critique_with(True, False, True), "text_read": "The Solar Sytem"}]
    d = disagreements(a, b)
    assert len(d) == 1
    assert {x["requirement"] for x in d[0]["diffs"]} == {REQS[1], "<text read>"}
    assert disagreements(a, a) == []
