from pathlib import Path


def test_mobile_layout_contract():
    css = Path("app/static/css/app.css").read_text()
    assert "font-size:16px" in css
    assert "overflow-x:hidden" in css
    assert "overscroll-behavior-inline:contain" in css
    assert "@media (max-width: 430px)" in css
    assert "@media (max-width: 768px)" in css
    assert ".table-wrap" in css and "overflow-x:auto" in css
    assert ".modal" in css and "overflow:auto" in css
