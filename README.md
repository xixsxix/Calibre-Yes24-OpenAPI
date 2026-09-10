# Calibre YES24 Metadata Plugin

**Official YES24 Open API Metadata Source for Calibre**

`Calibre-Yes24-OpenAPI` is an independent Calibre Desktop metadata source plugin that retrieves Korean book metadata and high-resolution covers from the official YES24 Open API.

Current release candidate: **0.4.11**

> This project is a new implementation built for the 2026 YES24 Open API. It is not a fork of the older YES24 Calibre plugins.

## What it does

The plugin provides both metadata lookup and cover download for Calibre.

- title / subtitle-aware search
- author-aware candidate ranking
- ISBN-13 direct lookup
- conservative fallback when an ISBN is missing or wrong
- print / eBook edition awareness
- translator and secondary-contributor checks for translated works
- publisher-aware same-work donor logic
- series and conservative `series_index` recovery
- filtering of YES24 marketing/curation groups such as `소개도서` / `추천도서`
- Comments fallback with TOC-like text rejection
- high-resolution `/XL` cover download

The design goal is deliberately conservative:

> **A missing result is better than confidently applying the wrong book or edition.**

## Requirements

- Calibre 5.0 or later
- a YES24 Open API key from `developers.yes24.com`
- network access to the YES24 Open API and YES24 product pages used by narrow fallbacks

## Installation

### From a GitHub Release

Download `Yes24.zip` from the Releases page, then install it in Calibre:

```text
Preferences
→ Plugins
→ Load plugin from file
→ select Yes24.zip
```

Restart Calibre after installation.

### Build from source

```powershell
python .\build_plugin.py
```

This creates:

```text
Yes24.zip
```

You can also install the generated ZIP from the command line:

```powershell
calibre-customize.exe -a .\Yes24.zip
```

## Configure the YES24 API key

In Calibre:

```text
Preferences
→ Plugins
→ Metadata source plugins
→ Yes24
→ Customize plugin
→ enter your YES24 API key
```

The plugin stores the key through Calibre's plugin preferences. Do not commit API keys to Git or include them in bug reports.

## Matching safety

The plugin treats ISBN states differently:

```text
exact ISBN found
→ use that edition when title/author are compatible

supplied ISBN resolves to a different book
→ positive evidence that the stored ISBN may be wrong
→ title/author fallback may recover the correct work

supplied ISBN is not found at all
→ title/author search may run diagnostically
→ a different-ISBN edition is NOT applied automatically

no ISBN supplied
→ title/author matching is used conservatively
```

Translated works use translator agreement as strong edition evidence. Series metadata can be inherited only from a strongly compatible same-work edition and never changes the already selected winner.

See [METADATA_DESIGN.md](./METADATA_DESIGN.md) for the full decision rules.

## 0.4.11 validation

Before the first public release, 0.4.11 passed broad real-data validation:

```text
normal ISBN audit, 100 books
- accepted: 97
- rejected: 3
- accepted with library ISBN: 97
- accepted with a different ISBN: 0
- miss → accepted: 0
- TOC-like Comments: 0
- marketing/recommendation series: 0

no-ISBN stress audit, 100 books
- accepted: 94
- rejected: 6
- release-blocking wrong-work / wrong-translation / wrong-series cases: 0

wrong-ISBN stress audit, 20 books
- conflict: 19 → safely recovered through title/author fallback
- miss: 1 → safely rejected
```

Final installation smoke tests also reconfirmed both a positive path (`십팔사략`, eBook ISBN `9791195329373`, `현대지성 클래식 #3`) and the critical safety path where an unresolved eBook ISBN for `페스트` was not silently replaced with a different print edition.

See [RELEASE_NOTES_0.4.11.md](./RELEASE_NOTES_0.4.11.md) for release details.

## Development tools

The repository includes several optional development/audit helpers:

```text
build_plugin.py          build Yes24.zip
test_yes24.py            direct YES24 Open API probe / fixture collector
bulk_audit.py            read-only audit against a Calibre library
bulk_stress_audit.py     no-ISBN / wrong-ISBN stress audit
```

Audit output such as CSV reports is intentionally ignored by Git and should not be committed.

## Security

Never publish your YES24 API key. If a bug report needs logs, remove credentials and unrelated personal paths first.

See [SECURITY.md](./SECURITY.md).

## Related projects / prior art

YES24 integrations for Calibre existed before this project, including older Calibre Desktop metadata plugins and newer cover-only or Calibre-Web integrations. Those projects largely rely on YES24 HTML scraping or predate the 2026 official Open API.

This repository is an **independent implementation** designed around the official YES24 Open API, conservative edition matching, and current Calibre Desktop metadata-source behavior.

## License

GNU General Public License v3.0 only. See [LICENSE](./LICENSE).

## Status

**0.4.11 is functionally frozen and release-ready.**

The next stage is real-world Calibre usage. New changes should be driven by reproducible user cases rather than feature expansion.