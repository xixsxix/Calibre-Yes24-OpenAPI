# Calibre YES24 Plugins

YES24 공식 Open API를 사용하는 **두 개의 Calibre Desktop 플러그인**을 한 저장소에서 관리합니다.

이 프로젝트는 YES24 또는 Calibre의 공식 플러그인이 아니며, 두 프로젝트와 제휴·승인 관계를 주장하지 않습니다.

## 플러그인 구성

| 플러그인 | 역할 | 현재 버전 | 설치 파일 |
| --- | --- | ---: | --- |
| **YES24 Metadata Source** | 서지정보·표지·`identifier:yes24` 저장 | **0.5.3** | `Yes24.zip` |
| **YES24 Library Status** | 베스트셀러·스테디셀러·순위 이력 기록 | **0.3.5** | `Yes24LibraryStatus.zip` |

두 플러그인은 Calibre에서는 별도로 설치되지만 하나의 작업 흐름으로 연동됩니다.

```text
YES24 Metadata Source
→ 사용자가 원하는 판본 선택
→ identifier:yes24 저장
→ Library Status가 identifiers 변경 감지
→ YES24 공개 랭킹 snapshot과 로컬 대조
→ 현재 상태 + 과거 순위 이력을 사용자 정의 컬럼에 기록
```

Metadata Source만 독립적으로 사용할 수도 있습니다. Library Status의 자동 연동까지 사용할 경우 **Metadata Source → Library Status 순서로 설치**하는 것을 권장합니다.

## 빠른 설치

GitHub **Releases**에서 필요한 Calibre 플러그인 ZIP을 받아 설치합니다.

```text
Preferences
→ Plugins
→ Load plugin from file
```

설치 파일:

```text
Yes24.zip               # Metadata Source
Yes24LibraryStatus.zip  # Library Status
```

GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일이 아닙니다.

> Metadata Source 0.5.3과 Library Status 0.3.5는 공개 안정 릴리스입니다. GitHub Releases에서 `Yes24.zip`과 `Yes24LibraryStatus.zip`을 각각 설치할 수 있습니다.

## YES24 API Key

YES24 Open API Key가 필요합니다. Metadata Source에서 한 번 설정하면 Library Status도 같은 설정을 사용합니다.

```text
Preferences
→ Plugins
→ Metadata source plugins
→ Yes24
→ Customize plugin
→ YES24 API key 입력
```

API Key는 공개 저장소, 로그, 스크린샷, 버그 리포트에 포함하지 마세요.

## 두 플러그인의 역할

### YES24 Metadata Source

한 권의 책을 찾고 Calibre 메타데이터를 채우는 플러그인입니다.

주요 저장 항목:

```text
title
authors
identifier:isbn
identifier:yes24
publisher
pubdate
comments
tags
languages
series
series_index
Cover
```

ISBN 직접 조회, 제목/저자 후보 검색, 판본 구분, 시리즈 처리, 고해상도 표지와 `identifier:yes24` 저장을 담당합니다.

상세 사용법: [docs/metadata-source.md](./docs/metadata-source.md)

### YES24 Library Status

라이브러리의 책을 YES24 공개 랭킹 목록과 대조하여 상태와 순위 이력을 기록하는 Interface Action 플러그인입니다.

사용자 정의 컬럼:

```text
#yes24_status
#yes24_rank_detail
#yes24_best_rank
#yes24_best_record
#yes24_years
#yes24_checked
```

Metadata Source가 저장한 `identifier:yes24`를 우선 사용하고 ISBN13을 보조 식별자로 사용합니다.

상세 사용법: [docs/library-status.md](./docs/library-status.md)

## 자동 네트워크 동작 고지

**Library Status 0.3.5부터**, YES24 Metadata Source API Key가 설정되어 있으면 Calibre GUI 초기화 완료 후 YES24 공개 베스트셀러·스테디셀러 목록을 백그라운드에서 미리 가져옵니다.

이 startup prefetch 요청 자체에는 사용자의 EPUB 파일, 개별 책 제목, ISBN, `identifier:yes24` 또는 라이브러리 전체 메타데이터를 요청 파라미터로 보내지 않습니다. 공개 랭킹 목록을 받은 뒤 사용자 책과의 대조는 로컬에서 수행합니다.

current snapshot은 Calibre 프로세스 메모리에만 보관하고 종료 시 폐기합니다. 과거 완료 월의 최소 순위 정보만 별도 SQLite 캐시에 저장합니다.

자세한 설명: [docs/network-and-data.md](./docs/network-and-data.md)

## Library Status 0.3.5 성능 개선

0.3.5는 Metadata Source 저장 후 Status 기록이 current 랭킹 전체 조회를 기다리느라 수십 초 지연되던 문제를 줄이기 위해 startup prefetch + memory snapshot cache를 사용합니다.

실사용 검증에서는 캐시 준비 후 automatic worker가 약 **0.25~0.28초**에 완료되었고, 랭킹이 있는 책의 current/history 병합, 10분 TTL background refresh, 약 30권 연속 자동 연동까지 확인했습니다.

검증 기록: [docs/releases/library-status-0.3.5.md](./docs/releases/library-status-0.3.5.md)

## Metadata Source 0.5.3

0.5.3은 식별자 연계와 검색 회귀를 수정한 안정화 릴리스입니다.

- 선택한 YES24 상품의 `itemId`를 `identifier:yes24`로 저장
- `TOP 99` → `TOP99`, `3 D` → `3D` 같은 ASCII 문자/숫자 공백 차이 fallback
- 정규화 제목이 동일한 경우 숫자 권차 충돌로 오인하던 문제 수정
- 실제 다른 권차의 sequence-conflict 검사는 유지

릴리스 노트: [RELEASE_NOTES_0.5.3.md](./RELEASE_NOTES_0.5.3.md)

## 저장소 구조

기존 Metadata Source 공개 경로는 호환성을 위해 루트에 유지하고, Library Status는 별도 디렉터리에 둡니다.

```text
Calibre-Yes24-OpenAPI/
├─ yes24.py
├─ build_plugin.py
├─ library_status/
│  ├─ __init__.py
│  ├─ ui.py
│  ├─ client.py
│  ├─ columns.py
│  ├─ history.py
│  ├─ build_plugin.py
│  └─ tests...
└─ docs/
```

Library Status의 내부 개발용 버전별 overlay 파일은 공개 소스에 포함하지 않고, 실사용 검증된 동작을 `library_status/ui.py`에 통합합니다.

## 문서

문서 전체 목차는 [docs/README.md](./docs/README.md)에서 확인할 수 있습니다.

```text
docs/
├─ README.md
├─ metadata-source.md
├─ library-status.md
├─ integration.md
├─ network-and-data.md
├─ releases.md
└─ releases/
   ├─ metadata-source-0.5.3.md
   └─ library-status-0.3.5.md
```

기존 Metadata Source의 역사적인 `RELEASE_NOTES_*.md`와 `METADATA_DESIGN.md`는 기존 링크 호환성을 위해 루트에 유지합니다.

## 요구 사항

- **Metadata Source:** Calibre 5.0 이상
- **Library Status:** Calibre 9.0 이상
- YES24 Open API Key
- YES24 Open API 및 필요한 YES24 페이지에 대한 네트워크 접근

Library Status 자동 연동은 Metadata Source와 함께 사용하는 것을 권장합니다.

## 소스 빌드

Metadata Source:

```powershell
python .\build_plugin.py
& "D:\Program Files\Calibre2\calibre-customize.exe" -a ".\Yes24.zip"
```

Library Status:

```powershell
cd .\library_status
python .\test_status_core.py
python .\test_history_core.py
python .\test_public_contract.py
python .\build_plugin.py
& "D:\Program Files\Calibre2\calibre-customize.exe" -a ".\Yes24LibraryStatus.zip"
```

공개 소스 구조에 대한 개발자 설명은 [library_status/README.md](./library_status/README.md)를 참고하세요.

## 버그 리포트

Metadata Source 문제에는 가능하면 제목, 저자, ISBN, 실제 Calibre 결과, 기대 결과와 `--verbose` 로그를 포함해 주세요.

Library Status 문제에는 대상 book id, `identifier:yes24`/ISBN 상태, 기대한 컬럼 값과 다음 로그의 관련 구간이 도움이 됩니다.

```text
<Calibre config>/yes24_library_status/auto_debug.log
```

API Key와 YES24 원본 응답 전체는 공유하지 마세요.

## 데이터 및 보안

이 공개 저장소에는 캡처한 YES24 API 원문 응답 fixture나 API Key를 배포하지 않습니다. API 데이터의 사용 조건은 YES24 개발자 정책을 확인하세요.

자세한 보안 안내는 [SECURITY.md](./SECURITY.md), 네트워크·캐시 설명은 [docs/network-and-data.md](./docs/network-and-data.md)를 참고하세요.

## License

GNU General Public License v3.0 only. See [LICENSE](./LICENSE).
