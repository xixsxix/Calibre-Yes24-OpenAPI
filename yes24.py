#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre metadata source plugin for YES24."""

import html as html_lib
import json
import re
import time
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from calibre.ebooks.metadata.book.base import Metadata
from calibre.ebooks.metadata.sources.base import Option, Source


ITEM_LIST_URL = "https://apis.yes24.com/v1/goods/itemList"
ITEM_DETAIL_URL = "https://apis.yes24.com/v1/goods/itemDetail"
SERIES_PAGE_URL = "https://www.yes24.com/product/category/series/001001"

MAX_RESULTS = 6
SEARCH_PAGE_SIZE = 20
MIN_DESCRIPTION_LENGTH = 30
# eBook preference is relational, not a blanket score bonus. A global bonus can
# lift an unrelated translation/publisher edition above the bibliographic match.
EBOOK_TIE_BREAK_BONUS = 0.0
MAX_SERIES_PAGES = 12
SERIES_PAGE_TIME_BUDGET = 12.0

SUPPORTED_GOODS_TYPES = {"도서", "국내도서", "외국도서", "ebook"}
BROAD_CATEGORY_LABELS = {"도서", "국내도서", "외국도서", "ebook"}
SECONDARY_EDITION_ROLES = frozenset({"역", "옮김", "번역"})
# YES24 also exposes editorial/marketing collections through the series field.
# These labels are useful on the storefront but are not bibliographic series.
PROMOTIONAL_SERIES_RE = re.compile(r"(?:소개\s*도서|추천\s*도서)", re.I)

STRONG_SUBTITLE_SEPARATOR_RE = re.compile(r"\s+(?:[-‐‑‒–—―－]|[|｜])\s+")
COLON_SUBTITLE_SEPARATOR_RE = re.compile(r"\s*[:：]\s*")
TRAILING_PAREN_RE = re.compile(r"^(.*?)\s*[\(\[]([^\)\]]{2,})[\)\]]\s*$")
EDITION_SUFFIX_RE = re.compile(
    r"\s*[\(\[]\s*(?:"
    r"최신\s*개정판|최신개정판|개정\s*증보판|개정증보판|완전\s*개정판|완전개정판|"
    r"개정판|증보판|개정본|완역본|원전\s*완역본|라틴어\s*원전\s*완역본|완역판|"
    r"리커버(?:판)?|양장(?:본|판)?|특별판|합본판|초판본|"
    r"revised\s+edition|new\s+edition"
    r")\s*[\)\]]\s*$",
    re.I,
)
EDITION_DESCRIPTOR_RE = re.compile(
    r"^(?:"
    r"최신\s*개정판|최신개정판|개정\s*증보판|개정증보판|완전\s*개정판|완전개정판|"
    r"개정판|증보판|개정본|완역본|원전\s*완역본|라틴어\s*원전\s*완역본|완역판|"
    r"리커버(?:판)?|양장(?:본|판)?|특별판|합본판|초판본|"
    r"revised\s+edition|new\s+edition"
    r")$",
    re.I,
)
CONTRIBUTOR_ROLE_RE = re.compile(
    r"\s*(저|글|지음|원저|편저|저자|공저|엮음|편|역|옮김|번역|그림|사진|감수|해제|기획)\s*$"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)


class Yes24(Source):
    name = "Yes24"
    description = "Downloads metadata and high-resolution covers from YES24"
    author = "xixsxix"
    version = (0, 4, 13)
    minimum_calibre_version = (5, 0, 0)
    capabilities = frozenset({"identify", "cover"})
    touched_fields = frozenset({
        "title",
        "authors",
        "identifier:isbn",
        "publisher",
        "pubdate",
        "comments",
        "tags",
        "languages",
        "series",
        "series_index",
    })
    options = (
        Option(
            "api_key",
            "string",
            "",
            "YES24 API key",
            "developers.yes24.com에서 발급받은 YES24 Open API key",
        ),
    )
    config_help_message = (
        "YES24 Open API key가 필요합니다. "
        "developers.yes24.com에서 발급받은 키를 입력하세요."
    )
    supports_gzip_transfer_encoding = True
    cached_cover_url_is_reliable = True
    prefer_results_with_isbn = False

    # One Calibre worker can identify multiple books. Cache series-page scans
    # so a large collection such as 을유세계문학전집 is not fetched repeatedly.
    _series_page_cache = {}
    _series_page_attempted = set()

    @property
    def user_agent(self):
        return USER_AGENT

    def is_configured(self):
        return bool(self._api_key())

    def _api_key(self):
        return str(self.prefs.get("api_key") or "").strip()

    def _prepare_browser(self, api=False, referer=None):
        browser = self.browser.clone_browser()
        replace_headers = {
            "accept",
            "accept-language",
            "cache-control",
            "pragma",
            "referer",
            "x-api-key",
        }
        browser.addheaders = [
            (key, value)
            for key, value in browser.addheaders
            if key.lower() not in replace_headers
        ]
        browser.addheaders += [
            (
                "Accept",
                "application/json"
                if api
                else "text/html,application/xhtml+xml,*/*;q=0.8",
            ),
            ("Accept-Language", "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"),
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
        ]
        if api:
            browser.addheaders.append(("X-Api-Key", self._api_key()))
        if referer:
            browser.addheaders.append(("Referer", referer))
        return browser

    def identify(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
    ):
        if not self.is_configured():
            log.error("YES24 API key is not configured")
            return

        started = time.monotonic()
        title = self._clean_text(title)
        authors = self._clean_author_query(authors)
        requested_isbn = self._get_isbn(identifiers)

        results = []
        direct_match = False
        isbn_lookup_missed = False
        accepted_reason = None

        if requested_isbn and self._is_isbn13(requested_isbn):
            direct = self._detail_by_isbn(requested_isbn, timeout, log)
            if direct:
                if self._direct_candidate_is_safe(direct, title, authors):
                    log(f"YES24 ISBN direct match accepted: {requested_isbn}")
                    results = [direct]
                    direct_match = True
                else:
                    log(
                        "YES24 ISBN points to a bibliographically different item; "
                        "continuing with title/author search"
                    )
            else:
                isbn_lookup_missed = True
                log(
                    f"YES24 ISBN lookup missed: {requested_isbn}; "
                    "continuing with title/author search"
                )

        if not results and not abort.is_set():
            for query in self._search_queries(title, authors):
                if abort.is_set():
                    break

                log(f"YES24 search query: {query}")
                items = self._search_api(query, timeout, log)
                ranked = self._rank_and_filter(
                    items, title, authors, requested_isbn
                )
                if not ranked:
                    continue

                results = ranked
                accepted, reason = self._top_candidate_is_safe(
                    results, title, authors, requested_isbn
                )
                if accepted:
                    accepted_reason = reason
                    break

                log(f"YES24 query not decisive: {reason}")

        if not results:
            log(
                f"YES24 identify finished with no result in "
                f"{time.monotonic() - started:.3f}s"
            )
            return

        self._log_candidates(
            results[:MAX_RESULTS], title, authors, requested_isbn, log
        )

        # A syntactically valid ISBN that YES24 cannot resolve may still be a
        # real edition missing from the YES24 catalogue. In that situation a
        # title/author match to a different ISBN is not enough evidence to
        # replace the user's edition automatically. This is intentionally
        # different from the case where YES24 resolves the supplied ISBN to a
        # bibliographically different book: that is positive evidence that the
        # stored ISBN is wrong, so title/author fallback remains allowed.
        if isbn_lookup_missed and requested_isbn and not any(
            self._metrics_for(candidate, title, authors, requested_isbn)["isbn_exact"]
            for candidate in results
        ):
            log(
                "YES24 automatic match rejected: supplied ISBN was not found; "
                "refusing non-exact edition fallback"
            )
            return

        if not direct_match:
            if not accepted_reason:
                accepted, accepted_reason = self._top_candidate_is_safe(
                    results, title, authors, requested_isbn
                )
                if not accepted:
                    log(f"YES24 automatic match rejected: {accepted_reason}")
                    return
            log(f"YES24 automatic match accepted: {accepted_reason}")

        # Series data is sometimes present only on another edition. Fill only
        # from a strongly compatible edition and never use it for winner choice.
        self._ensure_series_metadata(
            results, title, authors, abort, timeout, log
        )

        item = results[0]
        self._enrich_series_index(item, title, abort, timeout, log)
        self._ensure_description_metadata(
            results, title, authors, abort, timeout, log
        )
        self._enrich_top_description(item, abort, timeout, log)
        if abort.is_set():
            return

        # The plugin has already made the safety decision. Returning only the
        # winner prevents Calibre's generic same-source sorter from undoing the
        # eBook preference.
        mi = self._metadata_from_item(item)
        if mi is None:
            log(
                f"YES24 identify finished with no usable metadata in "
                f"{time.monotonic() - started:.3f}s"
            )
            return

        mi.source_relevance = 0
        isbn = mi.get_identifiers().get("isbn")
        cover_url = self._xl_cover_url(item)
        if isbn and cover_url:
            self.cache_identifier_to_cover_url(isbn, cover_url)

        result_queue.put(mi)
        log(
            f"YES24 identify finished: 1 result(s), "
            f"{time.monotonic() - started:.3f}s"
        )

    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
        get_best_cover=False,
    ):
        if not self.is_configured():
            log.error("YES24 API key is not configured")
            return

        clean_title = self._clean_text(title)
        clean_authors = self._clean_author_query(authors)
        requested_isbn = self._get_isbn(identifiers)

        cached = self.get_cached_cover_url(identifiers)
        if not clean_title and cached:
            if self._download_cover_url(
                cached, result_queue, abort, timeout, log
            ):
                return

        item = None
        if requested_isbn and self._is_isbn13(requested_isbn):
            direct = self._detail_by_isbn(requested_isbn, timeout, log)
            if direct and self._direct_candidate_is_safe(
                direct, clean_title, clean_authors
            ):
                item = direct

        if item is None:
            for query in self._search_queries(clean_title, clean_authors):
                if abort.is_set():
                    return
                items = self._search_api(query, timeout, log)
                ranked = self._rank_and_filter(
                    items,
                    clean_title,
                    clean_authors,
                    requested_isbn,
                )
                if not ranked:
                    continue

                accepted, reason = self._top_candidate_is_safe(
                    ranked,
                    clean_title,
                    clean_authors,
                    requested_isbn,
                )
                if accepted:
                    item = ranked[0]
                    break
                log(f"YES24 cover query not decisive: {reason}")

        if not item:
            return

        cover_urls = []
        for url in (
            self._xl_cover_url(item),
            self._clean_text(item.get("cover")),
        ):
            if url and url not in cover_urls:
                cover_urls.append(url)

        for cover_url in cover_urls:
            if self._download_cover_url(
                cover_url,
                result_queue,
                abort,
                timeout,
                log,
                referer=self._clean_text(item.get("link")),
            ):
                isbn = self._clean_isbn13(item.get("isbn13"))
                if isbn:
                    self.cache_identifier_to_cover_url(isbn, cover_url)
                return

    def get_cached_cover_url(self, identifiers):
        isbn = self._get_isbn(identifiers)
        return self.cached_identifier_to_cover_url(isbn) if isbn else None

    def _download_cover_url(
        self,
        cover_url,
        result_queue,
        abort,
        timeout,
        log,
        referer=None,
    ):
        if abort.is_set() or not cover_url:
            return False

        try:
            browser = self._prepare_browser(api=False, referer=referer)
            data = browser.open_novisit(cover_url, timeout=timeout).read()
            if data and len(data) > 1024:
                result_queue.put((self, data))
                return True
        except Exception as err:
            log.warning(f"YES24 cover download failed for {cover_url}: {err}")

        return False

    def _api_get(self, endpoint, params, timeout, log, quiet_404=False):
        url = endpoint + "?" + urlencode(params)
        started = time.monotonic()

        try:
            browser = self._prepare_browser(api=True)
            raw = browser.open_novisit(url, timeout=timeout).read()
            if not raw:
                return None
            payload = json.loads(raw.decode("utf-8", "replace"))
        except Exception as err:
            if quiet_404 and getattr(err, "code", None) == 404:
                return None
            log.warning(f"YES24 API request failed: {err}")
            return None
        finally:
            log(f"YES24 API request: {time.monotonic() - started:.3f}s")

        if not isinstance(payload, dict) or not payload.get("success"):
            if not quiet_404 and isinstance(payload, dict):
                log.warning(
                    "YES24 API error: "
                    f"{payload.get('errorCode') or ''} "
                    f"{payload.get('message') or ''}"
                )
            return None

        return payload

    def _detail_by_isbn(self, isbn, timeout, log):
        payload = self._api_get(
            ITEM_DETAIL_URL,
            {
                "searchType": "ISBN13",
                "query": isbn,
                "detail": "Y",
            },
            timeout,
            log,
            quiet_404=True,
        )

        for item in self._payload_items(payload):
            if (
                self._clean_isbn13(item.get("isbn13")) == isbn
                and self._is_book_item(item)
            ):
                return item

        return None

    def _search_api(self, query, timeout, log):
        payload = self._api_get(
            ITEM_LIST_URL,
            {
                "query": query,
                "category": "ALL",
                "sort": "RELATION",
                "page": 1,
                "pageSize": SEARCH_PAGE_SIZE,
                "detail": "Y",
            },
            timeout,
            log,
            quiet_404=True,
        )
        return [
            item
            for item in self._payload_items(payload)
            if self._is_book_item(item)
        ]

    @staticmethod
    def _payload_items(payload):
        if not isinstance(payload, dict):
            return []
        data = payload.get("data")
        if not isinstance(data, dict):
            return []
        items = data.get("items")
        return items if isinstance(items, list) else []

    @classmethod
    def _is_book_item(cls, item):
        if not isinstance(item, dict):
            return False

        goods_type = cls._normalize_goods_type(item.get("goodsType"))
        goods_sort = cls._normalize_goods_type(item.get("goodsSortNm"))

        if goods_type in SUPPORTED_GOODS_TYPES:
            return True

        return any(
            goods_sort == value or goods_sort.startswith(value + "-")
            for value in SUPPORTED_GOODS_TYPES
        )

    @classmethod
    def _is_ebook_item(cls, item):
        if not isinstance(item, dict):
            return False

        goods_type = cls._normalize_goods_type(item.get("goodsType"))
        goods_sort = cls._normalize_goods_type(item.get("goodsSortNm"))
        return goods_type == "ebook" or goods_sort.startswith("ebook")

    @classmethod
    def _normalize_goods_type(cls, value):
        value = cls._clean_text(value)
        return value.lower() if value else ""

    @classmethod
    def _search_queries(cls, title, authors):
        queries = []

        def add(value):
            value = cls._clean_text(value)
            if value and value not in queries:
                queries.append(value)

        profile = cls._title_profile(title)
        if profile["structured"] and profile["primary"] != profile["full"]:
            add(profile["primary"])

        add(profile["full"])

        base = profile["primary"] or profile["full"]
        if base and authors:
            add(f"{base} {authors[0]}")

        add(cls._core_title(title))
        if not queries and authors:
            add(authors[0])

        return queries

    @classmethod
    def _rank_and_filter(cls, items, title, authors, requested_isbn):
        ranked = []
        seen = set()

        for source_order, item in enumerate(items or []):
            isbn = cls._clean_isbn13(item.get("isbn13")) or ""
            edition = "ebook" if cls._is_ebook_item(item) else "print"
            item_id = str(item.get("itemId") or "")

            # YES24 can expose purchase/rental products as separate itemIds
            # while they represent the same bibliographic edition.
            key = (
                ("isbn", isbn, edition)
                if isbn
                else ("item", item_id)
            )
            if key in seen:
                continue
            seen.add(key)

            if title and not cls._is_relevant_title(title, item):
                continue

            metrics = cls._candidate_metrics(
                item,
                title,
                authors,
                requested_isbn,
                source_order,
            )
            if metrics["sequence_conflict"]:
                continue
            if metrics["secondary_contributor_conflict"]:
                continue

            item["_match_metrics"] = metrics
            ranked.append((metrics["score"], source_order, item))

        ranked.sort(key=lambda row: (-row[0], row[1]))
        results = [item for _score, _order, item in ranked]

        if results and not any(
            cls._metrics_for(item, title, authors, requested_isbn)["isbn_exact"]
            for item in results
        ):
            results = cls._prefer_ebook_within_same_work(results)

        return results

    @classmethod
    def _prefer_ebook_within_same_work(cls, results):
        if not results or cls._is_ebook_item(results[0]):
            return results

        top = results[0]
        for index, candidate in enumerate(results[1:], 1):
            if cls._same_work_edition_pair(top, candidate):
                return [candidate] + results[:index] + results[index + 1:]

        return results

    @classmethod
    def _candidate_metrics(
        cls,
        item,
        title,
        authors,
        requested_isbn,
        source_order,
    ):
        found_isbn = cls._clean_isbn13(item.get("isbn13"))
        isbn_exact = bool(
            requested_isbn
            and found_isbn
            and found_isbn == requested_isbn
        )

        title_metrics = cls._title_match_metrics(title, item)
        work_title_exact = cls._work_title_exact(title, item)
        sequence_conflict = cls._title_sequence_conflict(title, item)

        result_authors = cls._split_authors(item.get("author"))
        author_similarity = (
            cls._author_similarity(authors, result_authors)
            if authors and result_authors
            else 0.0
        )
        secondary_similarity = cls._secondary_contributor_similarity(
            authors, item.get("author")
        )
        secondary_conflict = cls._secondary_contributor_conflict(
            authors, item.get("author")
        )
        author_exact = bool(
            authors
            and author_similarity >= 0.99
            and not secondary_conflict
        )
        is_ebook = cls._is_ebook_item(item)

        score = 0.0
        if isbn_exact:
            score += 10000.0

        if title:
            if title_metrics["full_exact"] or work_title_exact:
                score += 3000.0
            elif (
                title_metrics["primary_exact"]
                and title_metrics["structured"]
            ):
                score += 2900.0
            else:
                score += title_metrics["similarity"] * 2500.0

        if authors:
            if author_exact:
                score += 1800.0
            elif author_similarity >= 0.80:
                score += 1500.0
            elif author_similarity >= 0.60:
                score += 900.0
            else:
                score += author_similarity * 300.0

            if secondary_similarity >= 0.90:
                score += 1800.0
            elif secondary_similarity >= 0.75:
                score += 900.0

        if is_ebook and not isbn_exact:
            score += EBOOK_TIE_BREAK_BONUS

        score -= min(source_order, 100) * 0.5

        return {
            "score": score,
            "isbn_exact": isbn_exact,
            "title_exact": title_metrics["full_exact"],
            "title_similarity": title_metrics["similarity"],
            "primary_exact": title_metrics["primary_exact"],
            "primary_similarity": title_metrics["primary_similarity"],
            "combined_similarity": title_metrics["combined_similarity"],
            "subtitle_similarity": title_metrics["subtitle_similarity"],
            "subtitle_conflict": title_metrics["subtitle_conflict"],
            "structured": title_metrics["structured"],
            "work_title_exact": work_title_exact,
            "sequence_conflict": sequence_conflict,
            "author_exact": author_exact,
            "author_similarity": author_similarity,
            "secondary_contributor_similarity": secondary_similarity,
            "secondary_contributor_conflict": secondary_conflict,
            "is_ebook": is_ebook,
            "source_order": source_order,
        }

    @classmethod
    def _metrics_for(cls, item, title, authors, requested_isbn):
        metrics = item.get("_match_metrics")
        if isinstance(metrics, dict):
            return metrics

        return cls._candidate_metrics(
            item,
            title,
            authors,
            requested_isbn,
            0,
        )

    @classmethod
    def _direct_candidate_is_safe(cls, item, title, authors):
        if title:
            if cls._title_sequence_conflict(title, item):
                return False

            metrics = cls._title_match_metrics(title, item)
            if metrics["subtitle_conflict"]:
                return False

            if not (
                metrics["full_exact"]
                or cls._work_title_exact(title, item)
                or (
                    metrics["primary_exact"]
                    and metrics["structured"]
                )
                or metrics["similarity"] >= 0.80
            ):
                return False

        if authors:
            if cls._secondary_contributor_conflict(
                authors, item.get("author")
            ):
                return False

            result_authors = cls._split_authors(item.get("author"))
            if result_authors:
                author_similarity = cls._author_similarity(authors, result_authors)
                if author_similarity >= 0.55:
                    return True
                secondary_similarity = cls._secondary_contributor_similarity(
                    authors, item.get("author")
                )
                return (
                    secondary_similarity >= 0.90
                    and author_similarity >= 0.40
                )

        return True

    @classmethod
    def _top_candidate_is_safe(
        cls,
        results,
        title,
        authors,
        requested_isbn,
    ):
        if not results:
            return False, "no candidate"

        top = results[0]
        top_m = cls._metrics_for(top, title, authors, requested_isbn)
        second = results[1] if len(results) > 1 else None
        second_m = (
            cls._metrics_for(second, title, authors, requested_isbn)
            if second
            else None
        )
        margin = (
            top_m["score"] - second_m["score"]
            if second_m
            else float("inf")
        )

        if top_m["sequence_conflict"]:
            return False, "LOW: numbered volume conflicts with requested title"

        if top_m["secondary_contributor_conflict"]:
            return False, "LOW: translator/contributor conflicts with requested edition"

        if top_m["subtitle_conflict"] and not top_m["isbn_exact"]:
            return False, "LOW: subtitle conflicts with YES24 subtitle"

        if top_m["isbn_exact"]:
            if (
                top_m["title_similarity"] >= 0.80
                or top_m["work_title_exact"]
                or not title
            ):
                if not authors or top_m["author_similarity"] >= 0.55:
                    return True, "HIGH: exact ISBN with compatible title/author"

        if title and authors:
            if (
                (
                    top_m["title_exact"]
                    or top_m["work_title_exact"]
                    or (top_m["structured"] and top_m["primary_exact"])
                )
                and top_m["secondary_contributor_similarity"] >= 0.90
                and top_m["author_similarity"] >= 0.40
            ):
                if (
                    not second_m
                    or margin >= 80
                    or cls._same_edition_family(top, second)
                ):
                    return True, "HIGH: exact work title and matching translator"

            if (
                second
                and cls._same_work_edition_pair(top, second)
                and top_m["author_similarity"] >= 0.90
                and (
                    top_m["work_title_exact"]
                    or top_m["title_exact"]
                    or (
                        top_m["structured"]
                        and top_m["primary_exact"]
                    )
                )
            ):
                return True, "HIGH: same edition family; eBook tie-break"

            if (
                (top_m["title_exact"] or top_m["work_title_exact"])
                and top_m["author_similarity"] >= 0.90
            ):
                if (
                    not second_m
                    or margin >= 25
                    or cls._same_edition_family(top, second)
                ):
                    return True, "HIGH: exact work title and strong author match"

            if (
                top_m["structured"]
                and top_m["primary_exact"]
                and top_m["author_similarity"] >= 0.90
                and not top_m["subtitle_conflict"]
            ):
                if cls._same_work_edition_pair(top, second):
                    return True, "HIGH: main title/author exact; eBook tie-break"
                if not second_m or margin >= 25:
                    return True, "HIGH: structured main title and strong author match"

            if (
                top_m["title_similarity"] >= 0.92
                and top_m["author_similarity"] >= 0.90
                and (not second_m or margin >= 80)
            ):
                return True, "HIGH: very strong title and author match"

            if (
                top_m["title_similarity"] >= 0.82
                and top_m["author_similarity"] >= 0.97
                and (not second_m or margin >= 180)
            ):
                return True, "MEDIUM: strong title and exact author"

            if top_m["author_similarity"] < 0.55:
                return False, "LOW: author mismatch"

            if (
                second_m
                and margin < 80
                and not cls._same_edition_family(top, second)
            ):
                return False, f"LOW: ambiguous top candidates (margin {margin:.1f})"

            return False, "LOW: title/author agreement below automatic-update threshold"

        if title and not authors:
            if top_m["title_exact"] or top_m["work_title_exact"]:
                if cls._same_work_edition_pair(top, second):
                    return True, "MEDIUM: exact work title; same-edition eBook tie-break"
                if not second:
                    return True, "MEDIUM: unique exact-title candidate"
                if (
                    second_m
                    and not (
                        second_m["title_exact"]
                        or second_m["work_title_exact"]
                    )
                    and margin >= 250
                ):
                    return True, "MEDIUM: exact title with clear lead"

            if (
                top_m["structured"]
                and top_m["primary_exact"]
                and not top_m["subtitle_conflict"]
                and (not second_m or margin >= 250)
            ):
                return True, "MEDIUM: structured main title with clear lead"

            return False, "LOW: author missing and title is not uniquely decisive"

        if authors and not title:
            if top_m["author_similarity"] >= 0.99 and not second:
                return True, "MEDIUM: unique exact-author candidate"
            return False, "LOW: title missing"

        return False, "LOW: insufficient bibliographic input"

    @classmethod
    def _same_work(cls, first, second):
        if not isinstance(first, dict) or not isinstance(second, dict):
            return False

        first_key = cls._work_title_key(first.get("title"))
        second_key = cls._work_title_key(second.get("title"))
        if not first_key or first_key != second_key:
            return False

        first_authors = cls._split_authors(first.get("author"))
        second_authors = cls._split_authors(second.get("author"))
        if not first_authors or not second_authors:
            return False

        return cls._author_similarity(first_authors, second_authors) >= 0.99

    @classmethod
    def _same_edition_family(cls, first, second):
        if not cls._same_work(first, second):
            return False
        if not cls._publisher_compatible(
            first.get("publisher"), second.get("publisher")
        ):
            return False
        return cls._secondary_contributors_compatible(
            first.get("author"), second.get("author")
        )

    @classmethod
    def _same_work_edition_pair(cls, first, second):
        return bool(
            cls._same_edition_family(first, second)
            and cls._is_ebook_item(first) != cls._is_ebook_item(second)
        )

    @classmethod
    def _publisher_compatible(cls, first, second):
        left = cls._normalize_match_text(first)
        right = cls._normalize_match_text(second)
        if not left or not right:
            return False
        if left == right:
            return True
        if left in right or right in left:
            shorter = min(len(left), len(right))
            longer = max(len(left), len(right))
            return (shorter / longer) >= 0.65
        return SequenceMatcher(None, left, right).ratio() >= 0.85

    def _ensure_series_metadata(
        self,
        results,
        title,
        authors,
        abort,
        timeout,
        log,
    ):
        if not results:
            return

        top = results[0]
        if self._series_name(top):
            return

        self._inherit_series_from_same_work(results, log)
        if self._series_name(top) or abort.is_set() or not title:
            return

        for query in self._search_queries(title, authors)[:2]:
            if abort.is_set():
                return

            log(f"YES24 series donor query: {query}")
            items = self._search_api(query, timeout, log)
            ranked = self._rank_and_filter(items, title, authors, None)
            donors = [top] + [
                candidate
                for candidate in ranked
                if str(candidate.get("itemId") or "")
                != str(top.get("itemId") or "")
            ]
            self._inherit_series_from_same_work(donors, log)
            if self._series_name(top):
                return

    @classmethod
    def _inherit_series_from_same_work(cls, results, log):
        if not results:
            return

        top = results[0]
        if cls._series_name(top):
            return

        for donor in results[1:]:
            series_name = cls._series_name(donor)
            if not series_name:
                continue
            if not cls._same_work(top, donor):
                continue
            if not cls._publisher_compatible(
                top.get("publisher"), donor.get("publisher")
            ):
                continue
            if not cls._secondary_contributors_compatible(
                top.get("author"), donor.get("author")
            ):
                continue

            top["series"] = donor.get("series")
            donor_id = str(donor.get("itemId") or "").strip()
            if donor_id.isdigit():
                top["_series_donor_item_id"] = donor_id

            log(
                "YES24 series inherited from compatible same-work edition: "
                f"{series_name}"
            )
            return

    def _enrich_series_index(
        self,
        item,
        query_title,
        abort,
        timeout,
        log,
    ):
        series_name = self._series_name(item)
        if not series_name:
            return

        for candidate_title, source_label in (
            (item.get("title"), "YES24 title"),
            (query_title, "Calibre title"),
        ):
            series_index = self._series_index_from_title(
                candidate_title, series_name
            )
            if series_index is not None:
                item["_series_index"] = series_index
                log(
                    "YES24 series index resolved from "
                    f"{source_label}: {series_name} #{self._format_index(series_index)}"
                )
                return

        if abort.is_set():
            return

        series_id = self._series_id(item)
        if not series_id:
            log(
                f"YES24 series index unresolved: {series_name} "
                "(seriesId unavailable)"
            )
            return

        series_index = self._series_index_from_series_page(
            item,
            series_id,
            series_name,
            abort,
            timeout,
            log,
        )
        if series_index is not None:
            item["_series_index"] = series_index
            log(
                "YES24 series index resolved from series page: "
                f"{series_name} #{self._format_index(series_index)}"
            )
            return

        series_index = self._series_index_from_product_page(
            item,
            series_id,
            series_name,
            abort,
            timeout,
            log,
        )
        if series_index is not None:
            item["_series_index"] = series_index
            log(
                "YES24 series index resolved from product page: "
                f"{series_name} #{self._format_index(series_index)}"
            )
            return

        log(
            f"YES24 series index unresolved: {series_name} "
            f"(seriesId={series_id})"
        )

    def _series_index_from_product_page(
        self,
        item,
        series_id,
        series_name,
        abort,
        timeout,
        log,
    ):
        candidate_ids = []
        for raw_id in (
            item.get("_series_donor_item_id"),
            item.get("itemId"),
        ):
            value = str(raw_id or "").strip()
            if value.isdigit() and value not in candidate_ids:
                candidate_ids.append(value)

        for item_id in candidate_ids:
            if abort.is_set():
                return None

            url = f"https://www.yes24.com/Product/Goods/{item_id}"
            started = time.monotonic()
            try:
                browser = self._prepare_browser(
                    api=False,
                    referer="https://www.yes24.com/",
                )
                raw = browser.open_novisit(
                    url,
                    timeout=min(float(timeout), 6.0),
                ).read()
                html_text = raw.decode("utf-8", "replace")
            except Exception as err:
                log.warning(
                    f"YES24 product-page series lookup failed for {item_id}: {err}"
                )
                continue

            series_index = self._extract_series_index_from_product_html(
                html_text,
                series_name,
                str(series_id),
                item.get("title"),
            )
            log(
                "YES24 product-page series lookup: "
                f"item={item_id}, {time.monotonic() - started:.3f}s"
            )
            if series_index is not None:
                return series_index

        return None

    @classmethod
    def _extract_series_index_from_product_html(
        cls, html_text, series_name, series_id, product_title=None
    ):
        if not html_text or not series_name or not series_id:
            return None

        try:
            from lxml import html as lxml_html

            root = lxml_html.fromstring(html_text)
        except Exception:
            return None

        name_pattern = r"\s*".join(
            re.escape(part)
            for part in re.split(r"\s+", series_name)
            if part
        )
        if not name_pattern:
            return None

        label_re = re.compile(
            rf"^\s*{name_pattern}\s*[-–—―－:#：]\s*0*(\d{{1,4}})\s*$",
            re.I,
        )
        matches = []

        for anchor in root.xpath("//a[@href]"):
            href = html_lib.unescape(str(anchor.get("href") or "").strip())
            try:
                query = parse_qs(urlparse(href).query)
            except Exception:
                continue

            values = []
            for key, raw_values in query.items():
                if key.lower() == "seriesnumber":
                    values.extend(str(value) for value in raw_values)
            if str(series_id) not in values:
                continue

            anchor_text = cls._clean_text(" ".join(anchor.itertext()))
            match = label_re.match(anchor_text or "")
            if not match:
                continue

            index = cls._safe_series_index(match.group(1))
            if index is not None and index not in matches:
                matches.append(index)

        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None

        product_title = cls._clean_text(product_title)
        title_key = cls._normalize_match_text(product_title)
        if not title_key:
            return None

        headings = []
        for heading in root.xpath("//h1 | //h2 | //h3"):
            heading_text = cls._clean_text(" ".join(heading.itertext()))
            if cls._normalize_match_text(heading_text) == title_key:
                headings.append(heading)

        if not headings:
            return None

        nearby_re = re.compile(
            rf"(?:^|\s){name_pattern}\s*[-–—―－:#：]\s*0*(\d{{1,4}})(?=\s|$)",
            re.I,
        )
        nearby_matches = []

        for heading in headings[:2]:
            nodes = heading.xpath("preceding::*[position() <= 24]")
            for node in nodes:
                node_text = cls._clean_text(" ".join(node.itertext()))
                if not node_text or len(node_text) > len(series_name) + 32:
                    continue
                match = nearby_re.search(node_text)
                if not match:
                    continue
                index = cls._safe_series_index(match.group(1))
                if index is not None and index not in nearby_matches:
                    nearby_matches.append(index)

            for raw_text in heading.xpath("preceding::text()[position() <= 48]"):
                node_text = cls._clean_text(raw_text)
                if not node_text or len(node_text) > len(series_name) + 32:
                    continue
                match = nearby_re.search(node_text)
                if not match:
                    continue
                index = cls._safe_series_index(match.group(1))
                if index is not None and index not in nearby_matches:
                    nearby_matches.append(index)

        return nearby_matches[0] if len(nearby_matches) == 1 else None

    @classmethod
    def _is_promotional_series_name(cls, name):
        name = cls._clean_text(name)
        return bool(name and PROMOTIONAL_SERIES_RE.search(name))

    @classmethod
    def _series_entry(cls, item):
        value = item.get("series")
        if not value:
            return None

        if isinstance(value, dict):
            entries = [value]
        elif isinstance(value, list):
            entries = value
        else:
            entries = [value]

        fallback_name = None
        for entry in entries:
            if isinstance(entry, dict):
                name = (
                    entry.get("seriesName")
                    or entry.get("name")
                    or entry.get("title")
                )
                series_id = entry.get("seriesId") or entry.get("id")
            else:
                name = entry
                series_id = None

            name = cls._clean_text(name)
            if not name:
                continue
            if cls._is_promotional_series_name(name):
                continue

            if fallback_name is None:
                fallback_name = (name, None)

            series_id_text = str(series_id or "").strip()
            if series_id_text.isdigit():
                return name, series_id_text

        return fallback_name

    @classmethod
    def _series_name(cls, item):
        entry = cls._series_entry(item)
        return entry[0] if entry else None

    @classmethod
    def _series_id(cls, item):
        entry = cls._series_entry(item)
        return entry[1] if entry else None

    @classmethod
    def _series_index_from_title(cls, title, series_name):
        title = cls._clean_text(title)
        series_name = cls._clean_text(series_name)
        if not title or not series_name:
            return None

        series_pattern = r"\s*".join(
            re.escape(part)
            for part in re.split(r"\s+", series_name)
            if part
        )
        if not series_pattern:
            return None

        prefix = re.match(
            rf"^\s*{series_pattern}(?=$|[\s\-–—―－:：#])\s*(.*)$",
            title,
            re.I,
        )
        if not prefix:
            return cls._series_index_from_related_title_tail(title, series_name)

        remainder = prefix.group(1).strip()
        remainder = re.sub(r"^[\-–—―－:：#·ㆍ]\s*", "", remainder)

        patterns = (
            r"^(?:제\s*)?(\d{1,4}(?:\.\d+)?)\s*(?:권|편|부)?(?=$|[\s\-–—―－:：\(\[])",
            r"^(?:vol(?:ume)?|book)\.?\s*(\d{1,4}(?:\.\d+)?)(?=$|[\s\-–—―－:：\(\[])",
        )
        for pattern in patterns:
            match = re.match(pattern, remainder, re.I)
            if not match:
                continue
            return cls._safe_series_index(match.group(1))

        return None

    @classmethod
    def _series_index_from_related_title_tail(cls, title, series_name):
        """Infer a terminal volume only when title and series are closely related."""
        profile = cls._title_profile(title)
        primary = cls._clean_text(profile["primary"] or profile["full"])
        if not primary:
            return None

        match = re.search(
            r"(?:^|\s)(?:제\s*)?(\d{1,4})(\s*(?:권|편|부))?\s*$",
            primary,
            re.I,
        )
        if not match:
            return None

        number = cls._safe_series_index(match.group(1))
        if number is None:
            return None

        explicit_unit = bool(match.group(2))
        if not explicit_unit and 1900 <= number <= 2099:
            return None
        if not explicit_unit and number > 999:
            return None

        title_stem = cls._clean_text(primary[:match.start()])
        series_core = re.sub(
            r"\s*(?:시리즈|전집|총서|클래식)\s*$",
            "",
            series_name,
            flags=re.I,
        )
        series_core = cls._clean_text(series_core) or series_name
        if not title_stem:
            return None

        similarity = cls._title_similarity(title_stem, series_core)
        minimum = 0.60 if explicit_unit else 0.72
        if similarity < minimum:
            return None

        return number

    @staticmethod
    def _safe_series_index(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if number <= 0 or number > 9999:
            return None
        return number

    @staticmethod
    def _format_index(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:g}"

    def _series_index_from_series_page(
        self,
        item,
        series_id,
        series_name,
        abort,
        timeout,
        log,
    ):
        target_ids = []
        for raw_id in (item.get("itemId"), item.get("_series_donor_item_id")):
            value = str(raw_id or "").strip()
            if value.isdigit() and value not in target_ids:
                target_ids.append(value)

        if not target_ids:
            return None

        cache = self._series_page_cache.setdefault(str(series_id), {})
        for target_id in target_ids:
            if target_id in cache:
                return cache[target_id]

        if str(series_id) in self._series_page_attempted:
            return None

        self._series_page_attempted.add(str(series_id))
        started = time.monotonic()
        deadline = started + min(float(timeout), SERIES_PAGE_TIME_BUDGET)

        first_url = SERIES_PAGE_URL + "?" + urlencode({"SeriesNumber": series_id})
        queue = [first_url]
        visited = set()
        pages = 0

        while (
            queue
            and pages < MAX_SERIES_PAGES
            and not abort.is_set()
            and time.monotonic() < deadline
        ):
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            remaining = max(1.0, deadline - time.monotonic())
            try:
                browser = self._prepare_browser(
                    api=False,
                    referer="https://www.yes24.com/",
                )
                raw = browser.open_novisit(
                    url,
                    timeout=min(5.0, remaining),
                ).read()
                html_text = raw.decode("utf-8", "replace")
            except Exception as err:
                log.warning(f"YES24 series-page request failed: {err}")
                continue

            pages += 1
            mapping, page_urls = self._extract_series_page_data(
                html_text,
                series_name,
                str(series_id),
                url,
            )
            cache.update(mapping)

            for target_id in target_ids:
                if target_id in cache:
                    log(
                        "YES24 series page lookup: "
                        f"{pages} page(s), {time.monotonic() - started:.3f}s"
                    )
                    return cache[target_id]

            for page_url in page_urls:
                if page_url not in visited and page_url not in queue:
                    queue.append(page_url)

        log(
            "YES24 series page lookup: "
            f"{pages} page(s), {time.monotonic() - started:.3f}s"
        )
        return None

    @classmethod
    def _extract_series_page_data(
        cls,
        html_text,
        series_name,
        series_id,
        current_url,
    ):
        if not html_text or not series_name:
            return {}, []

        try:
            from lxml import html as lxml_html

            root = lxml_html.fromstring(html_text)
        except Exception:
            return {}, []

        mapping = {}
        name_pattern = r"\s*".join(
            re.escape(part)
            for part in re.split(r"\s+", series_name)
            if part
        )
        label_re = re.compile(
            rf"^\s*{name_pattern}\s*[-–—―－:#：]\s*"
            r"(\d{1,4}(?:\.\d+)?)\s*$",
            re.I,
        )

        for element in root.xpath("//*[not(self::script) and not(self::style)]"):
            text = cls._clean_text(" ".join(element.itertext()))
            if not text or len(text) > len(series_name) + 24:
                continue

            match = label_re.match(text)
            if not match:
                continue

            series_index = cls._safe_series_index(match.group(1))
            if series_index is None:
                continue

            ancestor = element
            for _depth in range(8):
                if ancestor is None:
                    break

                ids = []
                for href in ancestor.xpath(".//a[@href]/@href"):
                    goods_match = re.search(
                        r"/(?:product/)?goods/(\d+)",
                        str(href),
                        re.I,
                    )
                    if goods_match:
                        goods_id = goods_match.group(1)
                        if goods_id not in ids:
                            ids.append(goods_id)

                if 0 < len(ids) <= 8:
                    for goods_id in ids:
                        mapping.setdefault(goods_id, series_index)
                elif len(ids) > 8:
                    break

                ancestor = ancestor.getparent()

        page_urls = []
        candidate_urls = []

        for href in root.xpath("//a[@href]/@href"):
            href = html_lib.unescape(str(href or "").strip())
            if href:
                candidate_urls.append(urljoin(current_url, href))

        raw_url_re = re.compile(
            r'''["']([^"']*/product/category/series/001001\?[^"']*SeriesNumber=\d+[^"']*)["']''',
            re.I,
        )
        for match in raw_url_re.finditer(html_text):
            href = html_lib.unescape(match.group(1))
            candidate_urls.append(urljoin(current_url, href))

        for candidate_url in candidate_urls:
            try:
                parsed = urlparse(candidate_url)
                query = parse_qs(parsed.query)
            except Exception:
                continue

            values = (
                query.get("SeriesNumber")
                or query.get("seriesNumber")
                or query.get("seriesnumber")
                or []
            )
            if str(series_id) not in {str(value) for value in values}:
                continue

            if not any("page" in key.lower() for key in query):
                continue

            normalized = parsed._replace(fragment="").geturl()
            if normalized != current_url and normalized not in page_urls:
                page_urls.append(normalized)

        return mapping, page_urls

    @classmethod
    def _log_candidates(cls, results, title, authors, requested_isbn, log):
        for index, item in enumerate(results[:3], 1):
            metrics = cls._metrics_for(item, title, authors, requested_isbn)
            series_name = cls._series_name(item) or "-"
            log(
                "YES24 candidate "
                f"#{index}: score={metrics['score']:.1f}, "
                f"title_match={metrics['title_similarity']:.3f}, "
                f"main_match={metrics['primary_similarity']:.3f}, "
                f"combined_match={metrics['combined_similarity']:.3f}, "
                f"work_exact={'yes' if metrics['work_title_exact'] else 'no'}, "
                f"sequence_conflict={'yes' if metrics['sequence_conflict'] else 'no'}, "
                f"author_match={metrics['author_similarity']:.3f}, "
                f"secondary_match={metrics['secondary_contributor_similarity']:.3f}, "
                f"secondary_conflict={'yes' if metrics['secondary_contributor_conflict'] else 'no'}, "
                f"isbn_exact={'yes' if metrics['isbn_exact'] else 'no'}, "
                f"edition={'ebook' if metrics['is_ebook'] else 'print'}, "
                f"series={series_name}, "
                f"item={item.get('itemId')}"
            )

    @classmethod
    def _title_profile(cls, title):
        full = cls._clean_text(title) or ""
        profile = {
            "full": full,
            "primary": full,
            "subtitle": "",
            "structured": False,
            "separator": "",
        }
        if not full:
            return profile

        strong = STRONG_SUBTITLE_SEPARATOR_RE.search(full)
        if strong:
            left = cls._clean_text(full[:strong.start()]) or ""
            right = cls._clean_text(full[strong.end():]) or ""
            if (
                len(cls._normalize_match_text(left)) >= 2
                and len(cls._normalize_match_text(right)) >= 2
            ):
                profile.update(
                    primary=left,
                    subtitle=right,
                    structured=True,
                    separator="dash_or_pipe",
                )
                return profile

        colon = COLON_SUBTITLE_SEPARATOR_RE.search(full)
        if colon:
            left = cls._clean_text(full[:colon.start()]) or ""
            right = cls._clean_text(full[colon.end():]) or ""
            if (
                len(cls._normalize_match_text(left)) >= 2
                and len(cls._normalize_match_text(right)) >= 2
            ):
                profile.update(
                    primary=left,
                    subtitle=right,
                    structured=True,
                    separator="colon",
                )
                return profile

        paren = TRAILING_PAREN_RE.match(full)
        if paren:
            left = cls._clean_text(paren.group(1)) or ""
            right = cls._clean_text(paren.group(2)) or ""
            if len(cls._normalize_match_text(left)) >= 2:
                profile.update(
                    primary=left,
                    subtitle=right,
                    structured=True,
                    separator="trailing_parenthetical",
                )

        return profile

    @classmethod
    def _candidate_title_values(cls, item):
        main = cls._clean_text(item.get("title")) or ""
        subtitle = cls._clean_text(item.get("subTitle")) or ""
        values = []

        def add(value):
            value = cls._clean_text(value)
            if value and value not in values:
                values.append(value)

        add(main)
        if main and subtitle:
            add(f"{main} - {subtitle}")
            add(f"{main}: {subtitle}")
            add(f"{main} {subtitle}")

        return main, subtitle, values

    @classmethod
    def _title_match_metrics(cls, query_title, item):
        profile = cls._title_profile(query_title)
        main, candidate_subtitle, candidates = cls._candidate_title_values(item)
        candidate_profile = cls._title_profile(main)
        candidate_side_structure = bool(
            not profile["structured"] and candidate_profile["structured"]
        )
        candidate_primary = (
            candidate_profile["primary"]
            if candidate_side_structure
            else main
        )
        if not candidate_subtitle and candidate_side_structure:
            candidate_subtitle = candidate_profile["subtitle"]
        structured = bool(
            profile["structured"] or candidate_side_structure
        )

        if not profile["full"] or not main:
            return {
                "similarity": 0.0,
                "full_exact": False,
                "primary_exact": False,
                "primary_similarity": 0.0,
                "combined_similarity": 0.0,
                "subtitle_similarity": 0.0,
                "subtitle_conflict": False,
                "structured": structured,
            }

        full_norm = cls._normalize_match_text(profile["full"])
        primary_norm = cls._normalize_match_text(profile["primary"])
        candidate_primary_norm = cls._normalize_match_text(candidate_primary)
        candidate_norms = [cls._normalize_match_text(value) for value in candidates]

        full_exact = bool(full_norm and full_norm in candidate_norms)
        primary_exact = bool(
            primary_norm and primary_norm == candidate_primary_norm
        )

        combined_similarity = max(
            (cls._title_similarity(profile["full"], value) for value in candidates),
            default=0.0,
        )
        primary_similarity = cls._title_similarity(
            profile["primary"], candidate_primary
        )

        subtitle_similarity = 0.0
        subtitle_conflict = False
        if (
            profile["structured"]
            and profile["subtitle"]
            and candidate_subtitle
        ):
            subtitle_similarity = cls._title_similarity(
                profile["subtitle"], candidate_subtitle
            )
            subtitle_conflict = (
                len(cls._normalize_match_text(profile["subtitle"])) >= 4
                and len(cls._normalize_match_text(candidate_subtitle)) >= 4
                and subtitle_similarity < 0.35
            )

        similarity = combined_similarity
        if profile["structured"] and primary_similarity > similarity:
            boost = primary_similarity * (0.84 if subtitle_conflict else 0.96)
            similarity = max(similarity, boost)

        if full_exact:
            similarity = 1.0

        return {
            "similarity": similarity,
            "full_exact": full_exact,
            "primary_exact": primary_exact,
            "primary_similarity": primary_similarity,
            "combined_similarity": combined_similarity,
            "subtitle_similarity": subtitle_similarity,
            "subtitle_conflict": subtitle_conflict,
            "structured": structured,
        }

    @classmethod
    def _is_relevant_title(cls, query_title, item):
        if cls._title_sequence_conflict(query_title, item):
            return False

        metrics = cls._title_match_metrics(query_title, item)

        if (
            metrics["full_exact"]
            or metrics["primary_exact"]
            or cls._work_title_exact(query_title, item)
        ):
            return True

        if metrics["similarity"] >= 0.45:
            return True

        query_tokens = cls._title_tokens(query_title)
        candidate_text = " ".join(cls._candidate_title_values(item)[2])
        result_tokens = cls._title_tokens(candidate_text)

        if query_tokens and result_tokens:
            overlap = len(query_tokens & result_tokens) / min(
                len(query_tokens), len(result_tokens)
            )
            return overlap >= 0.50

        return False

    @classmethod
    def _work_title_exact(cls, query_title, item):
        query_key = cls._work_title_key(query_title)
        candidate_key = cls._work_title_key(item.get("title"))
        return bool(query_key and candidate_key and query_key == candidate_key)

    @classmethod
    def _work_title_key(cls, value):
        value = cls._clean_text(value)
        if not value:
            return ""

        profile = cls._title_profile(value)
        if (
            profile["structured"]
            and profile["subtitle"]
            and cls._is_edition_descriptor(profile["subtitle"])
        ):
            value = profile["primary"]

        previous = None
        while previous != value:
            previous = value
            value = EDITION_SUFFIX_RE.sub("", value).strip()

        return cls._normalize_match_text(value)

    @classmethod
    def _is_edition_descriptor(cls, value):
        value = cls._clean_text(value)
        return bool(value and EDITION_DESCRIPTOR_RE.fullmatch(value))

    @classmethod
    def _title_sequence_number(cls, value):
        value = cls._clean_text(value)
        if not value:
            return None

        profile = cls._title_profile(value)
        primary = profile["primary"] or profile["full"]
        patterns = (
            r"(?<![0-9A-Za-z가-힣])(\d{1,4})(?=$|[\s\-–—―－:：#\(\)\[\]])",
            r"(?<![0-9A-Za-z가-힣])(\d{1,4})\s*(?:권|편|부)(?=$|[\s\-–—―－:：#\(\)\[\]])",
        )
        for pattern in patterns:
            match = re.search(pattern, primary)
            if match:
                return match.group(1)
        return None

    @classmethod
    def _title_sequence_conflict(cls, query_title, item):
        query_number = cls._title_sequence_number(query_title)
        if query_number is None:
            return False

        candidate_number = cls._title_sequence_number(item.get("title"))
        return candidate_number != query_number

    @classmethod
    def _title_similarity(cls, left, right):
        left = cls._normalize_match_text(left)
        right = cls._normalize_match_text(right)

        if not left or not right:
            return 0.0
        if left == right:
            return 1.0

        if left in right or right in left:
            shorter = min(len(left), len(right))
            longer = max(len(left), len(right))
            return 0.82 + (0.18 * shorter / longer)

        return SequenceMatcher(None, left, right).ratio()

    @classmethod
    def _title_tokens(cls, value):
        value = cls._clean_text(value)
        if not value:
            return set()

        return {
            token.lower()
            for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", value)
        }

    @classmethod
    def _author_similarity(cls, query_authors, result_authors):
        query = [
            cls._normalize_match_text(author)
            for author in query_authors
            if author
        ]
        result = [
            cls._normalize_match_text(author)
            for author in result_authors
            if author
        ]
        query = [author for author in query if author]
        result = [author for author in result if author]

        if not query or not result:
            return 0.0

        best = 0.0
        for query_author in query:
            for result_author in result:
                if query_author == result_author:
                    return 1.0

                if query_author in result_author or result_author in query_author:
                    shorter = min(len(query_author), len(result_author))
                    longer = max(len(query_author), len(result_author))
                    best = max(best, 0.82 + (0.18 * shorter / longer))
                else:
                    best = max(
                        best,
                        SequenceMatcher(None, query_author, result_author).ratio(),
                    )

        return best

    @classmethod
    def _parse_contributors(cls, value):
        value = cls._clean_text(value)
        if not value:
            return []

        contributors = []
        for segment in re.split(r"\s*/\s*", value):
            segment = cls._clean_text(segment)
            if not segment:
                continue

            role_match = CONTRIBUTOR_ROLE_RE.search(segment)
            role = role_match.group(1) if role_match else ""
            name_part = segment[:role_match.start()].strip() if role_match else segment

            for name in re.split(r"\s*(?:,|;|ㆍ)\s*", name_part):
                name = cls._clean_text(name)
                if not name:
                    continue
                name = re.sub(r"\s+등$", "", name).strip()
                if not name:
                    continue
                row = (name, role)
                if row not in contributors:
                    contributors.append(row)

        return contributors

    @classmethod
    def _secondary_contributor_names(cls, value):
        return [
            name
            for name, role in cls._parse_contributors(value)
            if role in SECONDARY_EDITION_ROLES
        ]

    @classmethod
    def _unmatched_query_secondary_authors(cls, query_authors, raw_authors):
        if not query_authors or len(query_authors) < 2:
            return []

        candidate_primary = cls._split_authors(raw_authors)
        unmatched = []
        for author in query_authors[1:]:
            author = cls._clean_text(author)
            if not author:
                continue
            if (
                candidate_primary
                and cls._author_similarity([author], candidate_primary) >= 0.75
            ):
                continue
            unmatched.append(author)

        return unmatched

    @classmethod
    def _secondary_contributor_similarity(cls, query_authors, raw_authors):
        if not query_authors or len(query_authors) < 2:
            return 0.0

        candidate_secondary = cls._secondary_contributor_names(raw_authors)
        if not candidate_secondary:
            return 0.0

        query_secondary = cls._unmatched_query_secondary_authors(
            query_authors, raw_authors
        )
        if not query_secondary:
            return 0.0

        return cls._author_similarity(query_secondary, candidate_secondary)

    @classmethod
    def _secondary_contributor_conflict(cls, query_authors, raw_authors):
        if not query_authors or len(query_authors) < 2:
            return False

        candidate_secondary = cls._secondary_contributor_names(raw_authors)
        if not candidate_secondary:
            return False

        query_secondary = cls._unmatched_query_secondary_authors(
            query_authors, raw_authors
        )
        if not query_secondary:
            return False

        return cls._author_similarity(query_secondary, candidate_secondary) < 0.55

    @classmethod
    def _secondary_contributors_compatible(cls, first, second):
        first_names = cls._secondary_contributor_names(first)
        second_names = cls._secondary_contributor_names(second)
        if not first_names or not second_names:
            return True
        return cls._author_similarity(first_names, second_names) >= 0.75

    @classmethod
    def _api_description(cls, item):
        if not isinstance(item, dict):
            return None
        content_detail = item.get("contentDetail")
        if not isinstance(content_detail, dict):
            return None
        description = cls._clean_description(content_detail.get("bookIntroduction"))
        if (
            not description
            or len(description) < MIN_DESCRIPTION_LENGTH
            or cls._looks_like_toc_text(description)
        ):
            return None
        return description

    def _ensure_description_metadata(
        self,
        results,
        title,
        authors,
        abort,
        timeout,
        log,
    ):
        if not results:
            return

        top = results[0]
        if self._api_description(top):
            return

        if self._inherit_description_from_same_work(results, log):
            return

        if abort.is_set() or not title:
            return

        for query in self._search_queries(title, authors)[:2]:
            if abort.is_set():
                return

            log(f"YES24 description donor query: {query}")
            items = self._search_api(query, timeout, log)
            ranked = self._rank_and_filter(items, title, authors, None)
            donors = [top] + [
                candidate
                for candidate in ranked
                if str(candidate.get("itemId") or "")
                != str(top.get("itemId") or "")
            ]
            if self._inherit_description_from_same_work(donors, log):
                return

    @classmethod
    def _inherit_description_from_same_work(cls, results, log):
        if not results:
            return False

        top = results[0]
        if cls._api_description(top):
            return True

        for donor in results[1:]:
            if not cls._same_edition_family(top, donor):
                continue

            description = cls._api_description(donor)
            if not description:
                continue

            top["_donor_description"] = description
            log(
                "YES24 description inherited from compatible same-work edition: "
                f"item={donor.get('itemId')}"
            )
            return True

        return False

    def _enrich_top_description(self, item, abort, timeout, log):
        if abort.is_set() or not self._needs_page_description(item):
            log("YES24 HTML fallback: skipped")
            return

        url = self._clean_text(item.get("link"))
        if not url:
            return

        started = time.monotonic()
        try:
            browser = self._prepare_browser(
                api=False,
                referer="https://www.yes24.com/",
            )
            raw = browser.open_novisit(url, timeout=min(timeout, 10)).read()
            description = self._extract_description_from_html(
                raw.decode("utf-8", "replace")
            )
            if description:
                item["_page_description"] = description
        except Exception as err:
            log.warning(f"YES24 book-introduction fallback failed: {err}")
        finally:
            log(f"YES24 HTML fallback: {time.monotonic() - started:.3f}s")

    @classmethod
    def _needs_page_description(cls, item):
        if cls._api_description(item):
            return False
        donor_description = cls._clean_description(item.get("_donor_description"))
        if (
            donor_description
            and len(donor_description) >= MIN_DESCRIPTION_LENGTH
            and not cls._looks_like_toc_text(donor_description)
        ):
            return False
        return True

    @classmethod
    def _api_tags(cls, item):
        tags = []

        def add(value):
            value = cls._clean_text(value)
            if not value or value.lower() in BROAD_CATEGORY_LABELS:
                return
            if value not in tags:
                tags.append(value)

        if cls._is_ebook_item(item):
            add("전자책")

        goods_sort = cls._clean_text(item.get("goodsSortNm"))
        if not goods_sort:
            return tags

        parts = re.split(r"\s*-\s*", goods_sort)
        if parts and parts[0].lower() in BROAD_CATEGORY_LABELS:
            parts = parts[1:]

        for part in parts:
            for label in re.split(r"\s*[/>]\s*", part):
                add(label)

        return tags

    @classmethod
    def _looks_like_toc_text(cls, text):
        text = cls._clean_description(text)
        if not text:
            return False

        chapter_hits = re.findall(
            r"(?<![0-9A-Za-z가-힣])(?:제\s*)?\d{1,3}\s*(?:장|절|권|편|부)(?=$|[\s:：.、,;])",
            text,
            re.I,
        )
        if len(chapter_hits) >= 4:
            return True

        numbered_lines = re.findall(r"(?:^|\n)\s*\d{1,3}[.)]\s+", text, re.I)
        return len(numbered_lines) >= 6

    @classmethod
    def _extract_description_from_html(cls, html_text):
        if not html_text:
            return None

        try:
            from lxml import html as lxml_html

            root = lxml_html.fromstring(html_text)

            for section_id in (
                "infoset_introduce",
                "infoset_toc",
                "infoset_pubReivew",
            ):
                nodes = root.xpath(
                    f'//*[@id="{section_id}"]//*['
                    'contains(concat(" ", normalize-space(@class), " "), '
                    '" infoWrap_txt ")] | '
                    f'//*[@id="{section_id}"]//textarea'
                )
                seen = set()
                for node in nodes:
                    candidate = cls._clean_description("\n".join(node.itertext()))
                    if (
                        not candidate
                        or len(candidate) < MIN_DESCRIPTION_LENGTH
                        or candidate in seen
                    ):
                        continue
                    seen.add(candidate)
                    if cls._looks_like_toc_text(candidate):
                        continue
                    return candidate
        except Exception:
            pass

        match = re.search(
            r'id=["\']infoset_introduce["\'][^>]*>'
            r'(.*?)(?:id=["\']infoset_|</section>|<h[234][^>]*>)',
            html_text,
            re.I | re.S,
        )
        if not match:
            return None

        candidate = cls._clean_description(match.group(1))
        return (
            candidate
            if candidate
            and len(candidate) >= MIN_DESCRIPTION_LENGTH
            and not cls._looks_like_toc_text(candidate)
            else None
        )

    @classmethod
    def _metadata_from_item(cls, item):
        title = cls._clean_text(item.get("title"))
        if not title:
            return None

        authors = cls._split_authors(item.get("author"))
        mi = Metadata(title, authors)

        isbn = cls._clean_isbn13(item.get("isbn13"))
        if isbn:
            mi.set_identifier("isbn", isbn)

        publisher = cls._clean_text(item.get("publisher"))
        if publisher:
            mi.publisher = publisher

        published = cls._parse_date(item.get("publishDate"))
        if published:
            mi.pubdate = published

        description = cls._api_description(item)
        if not description:
            donor_description = cls._clean_description(item.get("_donor_description"))
            if (
                donor_description
                and len(donor_description) >= MIN_DESCRIPTION_LENGTH
                and not cls._looks_like_toc_text(donor_description)
            ):
                description = donor_description

        if not description:
            page_description = cls._clean_description(item.get("_page_description"))
            if (
                page_description
                and len(page_description) >= MIN_DESCRIPTION_LENGTH
                and not cls._looks_like_toc_text(page_description)
            ):
                description = page_description

        if description:
            mi.comments = description

        categories = cls._api_tags(item)
        if categories:
            mi.tags = categories

        series_name = cls._series_name(item)
        if series_name:
            mi.series = series_name
            series_index = cls._safe_series_index(item.get("_series_index"))
            if series_index is not None:
                mi.series_index = series_index
            else:
                mi.series_index = None

        language = cls._infer_language(item)
        if language:
            mi.language = language

        return mi

    @classmethod
    def _split_authors(cls, value):
        value = cls._clean_text(value)
        if not value:
            return []

        authors = []
        for segment in re.split(r"\s*/\s*", value):
            segment = cls._clean_text(segment)
            if not segment:
                continue

            if re.search(
                r"\s*(?:역|옮김|번역|그림|사진|감수|해제)\s*$",
                segment,
            ):
                continue

            segment = re.sub(
                r"\s*(?:저|글|지음|원저|편저|저자|공저|엮음|편)\s*$",
                "",
                segment,
            ).strip()

            for name in re.split(r"\s*(?:,|;|ㆍ)\s*", segment):
                name = cls._clean_text(name)
                if name and name not in authors:
                    authors.append(name)

        return authors

    @classmethod
    def _infer_language(cls, item):
        goods_type = cls._normalize_goods_type(item.get("goodsType"))
        goods_sort = cls._normalize_goods_type(item.get("goodsSortNm"))
        title = cls._clean_text(item.get("title"))
        author = cls._clean_text(item.get("author"))
        publisher = cls._clean_text(item.get("publisher"))

        if goods_type == "국내도서" or goods_sort.startswith("국내도서"):
            return "kor"
        if goods_type == "외국도서" or goods_sort.startswith("외국도서"):
            return None

        if goods_type == "도서" or cls._is_ebook_item(item):
            if any(
                cls._contains_hangul(value)
                for value in (title, author, publisher)
            ):
                return "kor"

        return None

    @classmethod
    def _xl_cover_url(cls, item):
        item_id = str(item.get("itemId") or "").strip()
        if item_id.isdigit():
            return f"https://image.yes24.com/goods/{item_id}/XL"

        cover = cls._clean_text(item.get("cover"))
        if cover:
            return re.sub(r"/(?:S|M|L|XL)(?:\?.*)?$", "/XL", cover)

        return None

    @staticmethod
    def _parse_date(value):
        value = Yes24._clean_text(value)
        if not value:
            return None

        compact = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", value)
        if compact:
            try:
                return datetime(
                    int(compact.group(1)),
                    int(compact.group(2)),
                    int(compact.group(3)),
                )
            except ValueError:
                return None

        match = re.search(
            r"(\d{4})[-./년\s]+"
            r"(\d{1,2})[-./월\s]+"
            r"(\d{1,2})",
            value,
        )
        if not match:
            return None

        try:
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
        except ValueError:
            return None

    @classmethod
    def _clean_description(cls, value):
        if value is None:
            return None

        value = str(value)
        value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
        value = re.sub(r"</p\s*>", "\n", value, flags=re.I)
        value = re.sub(r"<[^>]+>", " ", value)
        value = html_lib.unescape(value)
        value = re.sub(r"[ \t\r\f\v]+", " ", value)
        value = re.sub(r"\s*\n\s*", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        value = value.strip()
        return value or None

    @staticmethod
    def _get_isbn(identifiers):
        if not identifiers:
            return None

        value = identifiers.get("isbn")
        if isinstance(value, (list, tuple)):
            value = value[0] if value else None
        if not value:
            return None

        return re.sub(r"[^0-9Xx]", "", str(value)) or None

    @staticmethod
    def _is_isbn13(value):
        return bool(value and re.fullmatch(r"97[89]\d{10}", str(value)))

    @staticmethod
    def _clean_isbn13(value):
        if not value:
            return None

        value = re.sub(r"[^0-9]", "", str(value))
        return value if re.fullmatch(r"97[89]\d{10}", value) else None

    @staticmethod
    def _clean_author_query(authors):
        if not authors:
            return []

        if isinstance(authors, str):
            authors = [authors]

        result = []
        for author in authors:
            author = Yes24._clean_text(author)
            if author and author not in result:
                result.append(author)

        return result

    @classmethod
    def _core_title(cls, title):
        title = cls._clean_text(title)
        if not title:
            return None

        profile = cls._title_profile(title)
        if profile["structured"] and profile["primary"]:
            return profile["primary"]

        core = re.split(r"\s*[\(\[].*$", title, maxsplit=1)[0]
        core = cls._clean_text(core)
        return core if core and len(core) >= 2 else title

    @staticmethod
    def _normalize_match_text(value):
        value = Yes24._clean_text(value)
        if not value:
            return ""

        return re.sub(r"[\W_]+", "", value.lower(), flags=re.UNICODE)

    @staticmethod
    def _clean_text(value):
        if value is None:
            return None

        value = re.sub(r"\s+", " ", str(value)).strip()
        return value or None

    @staticmethod
    def _contains_hangul(value):
        return bool(value and re.search(r"[가-힣]", str(value)))


if __name__ == "__main__":
    print(
        "This file is a Calibre metadata source plugin "
        "and must be installed in Calibre."
    )
