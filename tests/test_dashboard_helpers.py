from risklens.dashboard.helpers import language_suffix


def test_language_suffix_handles_chinese_label():
    assert language_suffix("中文") == "zh"
    assert language_suffix("English") == "en"
