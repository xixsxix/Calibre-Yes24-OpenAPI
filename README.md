# Calibre YES24 Metadata Plugin

**YES24 공식 Open API를 사용하는 독립적인 Calibre Desktop 메타데이터 소스 플러그인**

An independent Calibre Desktop metadata source plugin using the official YES24 Open API.

한국 도서 메타데이터와 고해상도 표지를 Calibre로 가져옵니다. 이 프로젝트는 YES24 또는 Calibre의 공식 플러그인이 아니며, 2026 YES24 Open API를 기반으로 독립 구현되었습니다.

Retrieves Korean book metadata and high-resolution covers for Calibre. This is an independent community project, not an official YES24 or Calibre plugin.

현재 공개 릴리스 / Current public release: **0.4.13**

## 주요 기능 / What it does

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

설계 원칙은 보수적입니다.

> **잘못된 책이나 판본을 확신해서 적용하는 것보다 결과를 비워 두는 편이 낫습니다.**  
> **A missing result is better than confidently applying the wrong book or edition.**

## 요구 사항 / Requirements

- Calibre 5.0 or later
- YES24 Open API key from `developers.yes24.com`
- network access to the YES24 Open API and YES24 product pages used by narrow fallbacks

## 설치 / Installation

### GitHub Release에서 설치 / From a GitHub Release

일반 사용자는 **Releases에서 `Yes24.zip`을 다운로드**해 설치하세요. GitHub가 자동 생성하는 **`Source code (zip)`은 Calibre 설치 파일이 아닙니다.**

For normal installation, download **`Yes24.zip` from Releases**. The GitHub-generated **`Source code (zip)` archive is not the Calibre plugin ZIP.**

```text
Preferences
→ Plugins
→ Load plugin from file
→ select Yes24.zip
```

설치 후 Calibre를 다시 시작하세요. / Restart Calibre after installation.

### 소스에서 빌드 / Build from source

```powershell
python .\build_plugin.py
```

This creates `Yes24.zip`. You can install it from the command line with:

```powershell
calibre-customize.exe -a .\Yes24.zip
```

## YES24 API key 설정 / Configure the API key

Calibre에서:

```text
Preferences
→ Plugins
→ Metadata source plugins
→ Yes24
→ Customize plugin
→ enter your YES24 API key
```

API key는 Calibre 플러그인 설정에 저장됩니다. Git에 커밋하거나 버그 리포트에 포함하지 마세요.

The key is stored through Calibre's plugin preferences. Do not commit API keys to Git or include them in bug reports.

## 매칭 안전 정책 / Matching safety

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

번역서는 번역자 일치를 강한 판본 증거로 사용합니다. 시리즈 정보는 강하게 호환되는 동일 작품 판본에서만 상속할 수 있으며 이미 선택된 winner를 바꾸지 않습니다.

Translated works use translator agreement as strong edition evidence. Series metadata can be inherited only from a strongly compatible same-work edition and never changes the already selected winner.

See [METADATA_DESIGN.md](./METADATA_DESIGN.md) for the full decision rules.

## 0.4.13 검증 / Validation

0.4.13은 Calibre 입력의 두 번째 이후 저자가 YES24의 `원저`/공저 계열과 이미 일치하는 경우 이를 번역자로 오판하지 않도록 역할 판별을 좁게 수정합니다. 기존 번역자 판본 검증과 자동 매칭 임계값은 유지합니다.

0.4.13 narrows secondary-contributor role handling so co-authors or original-work contributors are not misclassified as translators. Existing translator edition checks and global match thresholds remain unchanged.

```text
normal ISBN audit, 100 books
- accepted: 97
- rejected: 3
- accepted with library ISBN: 97
- accepted with a different ISBN: 0

no-ISBN stress audit, 100 books
- accepted: 94
- rejected: 6
- accepted with library ISBN: 39
- accepted with another ISBN: 53

wrong-ISBN stress audit, 20 books
- conflict: 19 → safely recovered through title/author fallback
- miss: 1 → safely rejected
```

Compared with 0.4.12, all checked non-timing audit fields remained unchanged across normal-100, refined no-ISBN-100, and wrong-ISBN-20. The targeted `너의 색` exact-ISBN case is newly recovered, while a deliberately wrong translator remains rejected.

See [RELEASE_NOTES_0.4.13.md](./RELEASE_NOTES_0.4.13.md) for details.

## 0.4.12 검증 / Validation

0.4.12는 0.4.11의 안전 정책을 유지하면서, 사용자가 짧은 본제목만 입력했을 때 YES24 후보 제목 자체에 부제가 포함되어 있어 매칭을 놓치는 경우를 좁게 수정합니다.

The 0.4.12 candidate keeps the 0.4.11 safety policy and adds a narrow candidate-side subtitle fix.

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
- accepted with library ISBN: 39
- accepted with another ISBN: 53
- TOC-like Comments: 0
- marketing/recommendation series: 0

wrong-ISBN stress audit, 20 books
- conflict: 19 → safely recovered through title/author fallback
- miss: 1 → safely rejected
```

표적 회귀에서는 `질투라는 감옥` / `야마모토 케이`가 ISBN 없이 정상 검색되며, 의도적으로 잘못 넣은 부제는 계속 거절됩니다. 첫 수정안에서 생겼던 `화폐전쟁 1~4` 회귀도 refined patch에서 복구했습니다.

See [RELEASE_NOTES_0.4.12.md](./RELEASE_NOTES_0.4.12.md) for details. The released 0.4.11 history remains in [RELEASE_NOTES_0.4.11.md](./RELEASE_NOTES_0.4.11.md).

## 저장소 범위 / Repository scope

이 공개 저장소는 의도적으로 작게 유지합니다.

```text
yes24.py                 Calibre Metadata Source plugin
build_plugin.py           builds the installable Yes24.zip
README.md                 installation and user-facing overview
METADATA_DESIGN.md        matching and safety design
RELEASE_NOTES_0.4.11.md   0.4.11 release notes
RELEASE_NOTES_0.4.12.md   0.4.12 release notes
RELEASE_NOTES_0.4.13.md   0.4.13 release notes
SECURITY.md               credential and reporting guidance
LICENSE                   GPL-3.0-only license
```

Bulk-audit scripts, captured API responses, local Calibre databases, and generated CSV reports are private development-lab material and are intentionally not published here. Captured YES24 API response fixtures are not redistributed.

## 보안 / Security

YES24 API key를 공개하지 마세요. 로그를 첨부할 때는 인증정보와 불필요한 개인 경로를 제거하세요.

Never publish your YES24 API key. If a bug report needs logs, remove credentials and unrelated personal paths first.

See [SECURITY.md](./SECURITY.md).

## 관련 프로젝트 / Related projects

YES24 integrations for Calibre existed before this project, including older Calibre Desktop metadata plugins and newer cover-only or Calibre-Web integrations. Those projects largely rely on YES24 HTML scraping or predate the 2026 official Open API.

This repository is an **independent implementation** designed around the official YES24 Open API, conservative edition matching, and current Calibre Desktop metadata-source behavior.

## License

GNU General Public License v3.0 only. See [LICENSE](./LICENSE).

## Status

**0.4.13 is the current public release.**

새 변경은 기능 확장보다 실제 Calibre 사용에서 재현 가능한 사례를 우선합니다.  
New changes should be driven by reproducible real-world Calibre cases rather than feature expansion.
