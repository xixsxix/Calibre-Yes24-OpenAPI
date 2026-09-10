# YES24 Metadata Matching Design

This document describes the safety model used by the Calibre YES24 Metadata Plugin.

Current implementation: **0.4.11**

## Design principle

The plugin is optimized for automatic metadata updates in real Calibre libraries. The priority order is:

```text
wrong automatic update prevention
> edition accuracy
> series/index accuracy
> collection rate
> speed
```

In other words:

> **A missing result is preferable to a confidently wrong result.**

## Data sources

The normal lookup path uses the official YES24 Open API:

```text
GET /v1/goods/itemDetail
GET /v1/goods/itemList
```

HTML is used only for narrow enrichment paths that the Open API does not always expose consistently, such as selected series-index evidence or a final description fallback.

High-resolution covers use the YES24 goods image URL for the selected item.

## Query inputs

Calibre's metadata-source `identify()` supplies bibliographic inputs such as:

```text
title
authors
identifiers (including ISBN)
```

It does not reliably provide the local EPUB/PDF format as an edition-selection signal, so this plugin does not claim to infer an edition from the local file format.

## Title and subtitle handling

Calibre libraries often store a title and subtitle in a single string while YES24 can expose them separately.

Example:

```text
Calibre
AI 최강의 수업 - KAIST 김진형 교수에게 듣는

YES24
title    = AI 최강의 수업
subTitle = KAIST 김진형 교수에게 듣는
```

The plugin therefore separates **search normalization** from **automatic-application validation**.

```text
normalize likely main title
→ search broadly
→ compare original full title against YES24 title + subtitle
→ combine title evidence with author/contributor evidence
```

Common subtitle separators include spaced dashes, pipes, colons, and trailing parenthetical descriptors. Hyphens inside normal words such as `K-콘텐츠` are not treated as subtitle separators.

## Edition descriptors

Clear edition suffixes such as `개정판`, `최신개정판`, `완역본`, or similar parenthetical markers may be removed for **work identity comparison**.

They are not removed from the final YES24 title written to Calibre.

## Candidate ranking

Each candidate is scored using evidence such as:

```text
exact ISBN
title similarity
structured main-title agreement
work-title identity
author similarity
translator/secondary-contributor similarity
sequence conflict
subtitle conflict
print/eBook relationship
YES24 result order
```

Exact ISBN is intentionally dominant, but it still requires basic bibliographic compatibility so a corrupt or mismapped ISBN response is not blindly trusted.

## ISBN states

The most important safety distinction is between **conflict** and **miss**.

### Exact/direct

The supplied ISBN resolves to a compatible YES24 item.

```text
exact ISBN + compatible title/author
→ accept
```

### Conflict

YES24 resolves the supplied ISBN, but the returned item is bibliographically different from the requested book.

This is positive evidence that the stored ISBN may be wrong.

```text
ISBN resolves to another book
→ title/author search may recover the requested work
→ replacement ISBN is allowed only after normal safety checks
```

### Miss

YES24 cannot resolve the supplied ISBN at all.

The ISBN may still be a real edition that is missing from the current YES24 catalogue. A title match to another edition is therefore not enough evidence to overwrite it.

```text
ISBN lookup miss
→ title/author search may run diagnostically
→ if only a different-ISBN candidate is found, reject automatic application
```

This rule prevents silent print/eBook edition replacement when YES24 coverage is incomplete.

### None

No ISBN was supplied.

The plugin falls back to conservative title/author matching. In this mode, selecting another valid edition ISBN is not itself an error because no ISBN anchor existed.

## Author and translator handling

YES24 contributor strings can contain authors, translators, illustrators, editors, and other roles.

Primary author agreement is used for work identity. Translation roles such as:

```text
역
옮김
번역
```

are used as strong **edition evidence**.

For a translated work, a translator mismatch can outweigh an otherwise strong title match.

The plugin does not intentionally write translators into Calibre's `authors` field. Some upstream author-string representation edge cases remain known non-blocking cleanup work.

## print / eBook selection

The plugin identifies eBook items from YES24 goods-type/category fields.

There is no blanket global eBook score bonus. A global bonus could cause an unrelated translation or publisher edition to outrank the bibliographically correct print edition.

Instead, eBook preference is relational:

```text
same work
+ compatible publisher
+ compatible secondary contributors
+ one candidate print and one candidate eBook
→ eBook may win the tie
```

## Duplicate products

YES24 may expose purchase and rental products as different item IDs while they represent the same bibliographic edition.

Candidates with the same valid ISBN and media type are deduplicated before final ranking.

## Final-result policy

The plugin returns only the single winner that has already passed the safety decision.

```text
search
→ rank
→ validate
→ enrich the fixed winner
→ return one result
```

This prevents Calibre's generic same-source sorter from changing the intended final edition order.

## Series policy

YES24 `seriesId` identifies a series; it is **not** a volume number and must never be written directly as `series_index`.

The plugin can use `seriesName` as Calibre `series`, subject to filtering and compatibility checks.

### Promotional/curation filtering

YES24 can expose marketing/editorial collections through series-shaped data. Examples found in real data include labels containing `소개도서` or `추천도서`.

Those are not bibliographic publication series and are excluded in 0.4.11.

Real series such as publication classics, world-literature lines, poetry series, etc. continue through the normal series logic.

## Series donor logic

An accepted item may have no series data even when another edition of the same work does.

Series data may be inherited only when the donor is strongly compatible:

```text
same normalized work title
+ compatible primary author
+ compatible publisher
+ no known translator/secondary-contributor conflict
```

The donor never changes the already selected winner.

## series_index evidence

The index is written only when there is positive evidence. Resolution order is roughly:

```text
1. explicit sequence in the selected YES24 title
2. explicit sequence in the original Calibre title
3. conservative terminal-number inference when title and series are strongly related
4. official YES24 series page mapping
5. exact current/donor product-page series badge
6. otherwise leave the index unset
```

Plain numbers that look like years or implausibly large unmarked values are rejected from heuristic inference.

If the evidence is ambiguous, the plugin stores the series name without inventing an index.

## Description / Comments policy

YES24 API data for some eBook entries has shown introduction/TOC inconsistencies. The plugin therefore validates description candidates before writing Calibre Comments.

```text
normal API introduction
→ use it

missing/short/TOC-like introduction
→ try compatible same-work description donor

still unavailable
→ narrow HTML fallback

TOC-like text
→ reject
```

TOC detection is conservative and requires repeated structural markers rather than a single occurrence of words such as chapter/section.

## Tags and language

Tags are derived primarily from YES24 goods/category labels, excluding broad container labels such as simply `도서`, `국내도서`, `외국도서`, or `eBook`.

An eBook marker may be added for eBook items.

Korean language is inferred conservatively from domestic-book/eBook classification and Hangul-bearing bibliographic fields. Foreign-book classification is not blindly forced to Korean.

## Cover policy

For a selected YES24 item, the plugin prefers:

```text
https://image.yes24.com/goods/{itemId}/XL
```

The cover path follows the same bibliographic selection logic as metadata lookup rather than independently selecting an arbitrary search result.

## Logging

Verbose logs expose the evidence needed to audit a decision, including candidate score components and important branch outcomes such as:

```text
YES24 ISBN direct match accepted
YES24 ISBN points to a bibliographically different item
YES24 ISBN lookup missed
YES24 automatic match accepted
YES24 automatic match rejected
YES24 series inherited from compatible same-work edition
YES24 description inherited from compatible same-work edition
```

No API key should be written to logs.

## Release-gate examples

The following are release blockers:

```text
a different work is automatically applied
an unresolved ISBN is silently replaced with another edition
a known translator mismatch is automatically accepted
marketing/recommendation collections become bibliographic series/index values
obvious table-of-contents text is written as Comments
media classification changes selection incorrectly
```

The following are usually non-blocking unless they systematically change identity:

```text
minor name spelling variants
role suffix representation differences
missing optional metadata when safe evidence is unavailable
```

## 0.4.11 validation status

0.4.11 passed:

- 100-book normal-ISBN audit
- 100-book no-ISBN stress audit
- 20-book wrong-ISBN stress audit
- targeted series regressions
- targeted ISBN-miss regression
- final installed-ZIP smoke tests

No release-blocking wrong automatic application remained in the validated corpus.

The functional logic is therefore frozen for the initial public release. New changes should be driven by reproducible real-world cases.