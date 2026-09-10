# YES24 Metadata Source for Calibre 0.4.11

## Summary

0.4.11 is the first public release candidate of this independent Calibre Desktop metadata source built around the **official YES24 Open API introduced in 2026**.

The release focuses on conservative automatic matching: when the evidence for a book or edition is weak, the plugin prefers returning no result over applying plausible-but-wrong metadata.

## Highlights

- official YES24 Open API for search and ISBN detail lookup
- title/subtitle-aware matching
- author and translator compatibility checks
- conservative handling of supplied ISBNs
- print/eBook edition awareness
- same-work donor logic for missing series or description metadata
- conservative `series_index` recovery from title, series page, or exact product page evidence
- filtering of marketing/recommendation collections such as `소개도서` and `추천도서`
- TOC-like Comments rejection
- high-resolution YES24 `/XL` cover download

## ISBN safety policy

0.4.10 introduced a critical safety distinction retained in 0.4.11:

```text
YES24 resolves the supplied ISBN to the expected book
→ exact-ISBN path

YES24 resolves the supplied ISBN to a bibliographically different book
→ positive evidence that the stored ISBN may be wrong
→ title/author recovery may proceed

YES24 cannot resolve the supplied ISBN at all
→ a different-ISBN edition is NOT automatically applied
```

This prevents a valid edition that happens to be missing from the current YES24 catalogue from being silently replaced by another print/eBook edition.

A real regression case involved `페스트`: an existing eBook ISBN could not be resolved by YES24 while a newer print edition was found by title. The plugin now rejects that non-exact fallback instead of replacing the user's ISBN.

## Series safety

YES24 can expose editorial or marketing collections through its series-shaped data. In the 0.4.10 100-book audit, examples included recommendation groups that looked like Calibre series and could even produce misleading sequence numbers.

0.4.11 excludes names containing `소개도서` or `추천도서` from bibliographic series candidates while preserving real publication series.

Targeted regression examples:

```text
지리의 힘
- removed: tvN 요즘책방 소개도서 #29

오늘부터의 세계
- removed: 문재인 대통령 2020년 독서의 달 추천도서

코스모스
- preserved/recovered: 사이언스 클래식 #4

오만과 편견
- preserved: 열린책들 세계문학 #143
```

## Comments safety

Some YES24 eBook data can contain introduction/TOC inconsistencies. The plugin uses conservative description selection:

```text
valid API introduction
→ use directly

missing or TOC-like introduction
→ try a strongly compatible same-work edition as a metadata donor

still unavailable
→ narrow HTML fallback

TOC-like candidate
→ reject rather than store as Comments
```

## Validation

### Normal ISBN audit — 100 books

```text
accepted             : 97
rejected             : 3
accepted/library ISBN: 97
accepted/other ISBN  : 0
```

Release-gate findings:

- accepted with a different ISBN: 0
- ISBN miss accepted as another edition: 0
- TOC-like Comments: 0
- marketing/recommendation series: 0
- release-blocking wrong-work matches: 0

The three rejections were conservative safety outcomes rather than crashes or empty searches.

### No-ISBN stress audit — 100 books

```text
accepted : 94
rejected : 6
error    : 0
```

The six rejections were ambiguous or bibliographically weak matches. Review of accepted results found no release-blocking wrong-work, wrong-translation, bogus-series, or TOC-Comments case.

### Wrong-ISBN stress audit — 20 books

- 19 conflict cases: recovered through title/author fallback
- 1 miss case: rejected because the supplied ISBN could not be resolved

This confirms that `conflict` and `miss` are intentionally different safety states.

## Final installation smoke test

The built ZIP was installed into Calibre and tested through `fetch-ebook-metadata.exe`.

Positive path:

```text
십팔사략
ISBN   : 9791195329373
Series : 현대지성 클래식 #3
Result : accepted
```

Safety path:

```text
페스트
ISBN supplied : 9788932963655
YES24 lookup   : miss
Result         : 0 results
Reason         : refusing non-exact edition fallback
```

## Known non-blocking issues

A small number of YES24 author strings can still expose representation differences such as name spelling variants or role suffixes. These are intentionally deferred rather than expanding the author parser immediately before the first public release.

## Upgrade note

0.4.11 contains no broad ranking rewrite over the release candidate immediately preceding it; the functional change is intentionally narrow around promotional/recommendation series filtering. Broad audits showed no unrelated field changes in the validated normal-ISBN corpus.

## License

GNU General Public License v3.0 only.