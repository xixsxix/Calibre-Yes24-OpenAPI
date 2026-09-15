#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path


class FakeMetadata:
    def __init__(self, item_id, tags=None):
        self._identifiers = {"yes24": str(item_id)}
        self.tags = list(tags or [])
    def get_identifiers(self):
        return dict(self._identifiers)


class FakeResponse:
    def __init__(self, text): self._data = text.encode("utf-8")
    def read(self): return self._data


class FakeBrowser:
    def __init__(self, pages): self.pages = pages
    def open_novisit(self, url, timeout=30):
        item_id = url.rstrip("/").split("/")[-1]
        if item_id not in self.pages: raise RuntimeError("fixture page missing")
        return FakeResponse(self.pages[item_id])


class FakeYes24:
    version = (0, 5, 4)
    pages = {
        "100": """<html><body><h4>관련분류</h4><div>카테고리 분류</div><!--comment--><a href='/product/category/display/001001046'>소설/시/희곡</a><a href='/product/category/display/001001046013'>고전문학</a><a href='/product/category/display/001001046013003'>서양 고전문학</a><a href='/product/category/display/001001046002'>영미소설</a><h4>소개</h4></body></html>""",
        "200": """<html><body><h4><span>관련분류</span></h4><div>카테고리 분류</div><!--comment--><a href='/product/category/display/017001'>eBook</a><a href='/product/category/display/017001048'>인문</a><a href='/product/category/display/017001048006'>서양철학</a><h4>이 상품의 이벤트</h4></body></html>""",
        "300": """<html><body><h4>관련분류</h4><div>카테고리 분류</div><a href='/product/category/display/001001019'>인문</a><a href='/product/category/display/001001019001'>인문/교양</a><a href='/product/category/display/001001019001003'>교양으로 읽는 인문</a><a href='/product/category/display/001001026'>자기계발</a><a href='/product/category/display/001001026008'>처세술/삶의 자세</a><div>수상내역 및 미디어 추천 분류</div><a href='/product/category/display/001005011'>세종도서</a><a href='/product/category/display/001005044'>YES24 올해의 책</a></body></html>""",
    }
    @classmethod
    def _clean_text(cls, value): return " ".join(str(value or "").split())
    @staticmethod
    def _get_isbn(identifiers): return None
    def _prepare_browser(self, api=False, referer=None): return FakeBrowser(self.pages)
    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30):
        result_queue.put(FakeMetadata("100", ["소설/시/희곡"]))
        result_queue.put(FakeMetadata("200", ["전자책", "인문"]))
        result_queue.put(FakeMetadata("300", ["인문", "⭐스테디셀러"]))
        result_queue.put(FakeMetadata("999", ["예술"]))


class FakeLog:
    def __call__(self, message): pass
    def warning(self, message): pass
class FakeAbort:
    def is_set(self): return False
class CaptureQueue:
    def __init__(self): self.items = []
    def put(self, value): self.items.append(value)

root = Path(__file__).resolve().parent
patch = (root / "yes24_055_patch.py").read_text(encoding="utf-8")
exec(compile(patch, "yes24_055_patch.py", "exec"), {"Yes24": FakeYes24})

assert FakeYes24._get_isbn({"isbn": "978-89-329-6038-8 08890"}) == "9788932960388"
assert FakeYes24._get_isbn({"isbn": "978-89-329-6787-5 05170"}) == "9788932967875"
assert FakeYes24._get_isbn({"isbn": "978-89-329-6038-9 08890"}) is None
assert FakeYes24._extract_related_category_tags_055(FakeYes24.pages["100"]) == ["소설/시/희곡", "고전문학", "영미소설"]
assert FakeYes24._extract_related_category_tags_055(FakeYes24.pages["200"]) == ["인문", "서양철학"]
question = FakeYes24._extract_related_category_tags_055(FakeYes24.pages["300"])
assert question == ["인문", "인문/교양", "자기계발", "처세술/삶의 자세"], question
assert "세종도서" not in question and "YES24 올해의 책" not in question

queue = CaptureQueue()
FakeYes24().identify(FakeLog(), queue, FakeAbort(), title="모비딕", authors=["허먼 멜빌"])
assert queue.items[0].tags == ["소설/시/희곡", "고전문학", "영미소설"]
assert queue.items[1].tags == ["전자책", "인문", "서양철학"]
assert queue.items[2].tags == ["인문", "⭐스테디셀러", "인문/교양", "자기계발", "처세술/삶의 자세"]
assert queue.items[3].tags == ["예술"]
assert FakeYes24.version == (0, 5, 5)
print("YES24 Metadata Source 0.5.5 category/ISBN tests: OK")
