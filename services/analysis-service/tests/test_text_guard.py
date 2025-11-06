from .text_guard import TextGuard


def build_guard() -> TextGuard:
    return TextGuard.from_file()


def test_forbidden_terms_redacted() -> None:
    guard = build_guard()
    result = guard.guard("이 결과는 반드시 성공합니다.", [])
    assert "반드시" not in result


def test_append_note_for_sensitive_topics() -> None:
    guard = build_guard()
    result = guard.guard("건강 관련 조언입니다.", ["건강"])
    assert "전문가 상담" in result
