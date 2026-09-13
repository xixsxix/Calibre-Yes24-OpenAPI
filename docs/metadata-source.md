# YES24 Metadata Source

YES24 공식 Open API를 사용하는 Calibre Desktop Metadata Source 플러그인입니다.

현재 안정 버전: **0.5.3**

## 역할

한국 도서의 제목, 저자, ISBN, 출판사, 발행일, 책소개, 태그, 언어, 시리즈와 고해상도 표지를 Calibre로 가져옵니다. 선택한 YES24 상품의 숫자 `itemId`를 `identifier:yes24`로 저장하여 Library Status와의 안정적인 연동 기준으로 사용합니다.

## 주요 기능

- YES24 공식 Open API 기반 검색
- ISBN-13 직접 조회
- YES24 `itemId` → `identifier:yes24` 저장
- ISBN이 없거나 저장 ISBN이 맞지 않을 때 제목/저자 후보 검색
- 제목/부제 구조와 기여자를 고려한 후보 랭킹
- 번역자 및 보조 기여자를 이용한 판본 구분
- 종이책/eBook, 구판/신판, 시즌/권차 후보 비교
- YES24 `seriesName` 기반 Calibre 시리즈 저장
- 직접적인 근거가 있을 때만 `series_index` 저장
- API 책소개 우선, 제한적 donor/HTML fallback
- 목차형 텍스트를 Comments로 오인하지 않도록 검사
- YES24 고해상도 `/XL` 표지
- 사용자가 선택한 후보의 ISBN에 연결된 정확한 표지 사용

## 설치

GitHub Releases의 **`Yes24.zip`**을 설치하세요. GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일이 아닙니다.

```text
Preferences
→ Plugins
→ Load plugin from file
→ Yes24.zip 선택
```

소스에서 직접 빌드하려면 저장소 루트에서 실행합니다.

```powershell
python .\build_plugin.py
& "C:\Program Files\Calibre2\calibre-customize.exe" -a ".\Yes24.zip"
```

Calibre 설치 경로가 다르면 실행 파일 경로를 맞게 바꾸세요.

## YES24 API Key 설정

```text
Preferences
→ Plugins
→ Metadata source plugins
→ Yes24
→ Customize plugin
→ YES24 API key 입력
```

API Key는 공개 저장소나 버그 리포트에 포함하지 마세요.

## 검색 결과 선택

ISBN이 없는 검색에서는 플러그인이 관련 YES24 후보를 모아 서지 유사성 점수가 높은 순서대로 반환합니다. 후보 #1은 가장 높은 점수의 결과이며 이후 후보도 출간연도, 권차, 종이책/eBook, 개정판 차이를 보고 선택할 수 있습니다.

정확한 ISBN이 있고 제목/저자와 호환되면 이미 판본이 특정된 것으로 보고 한 건을 반환할 수 있습니다.

명백한 권차 충돌이나 확인된 기여자 충돌처럼 강한 오답 근거가 있는 후보는 제외할 수 있습니다.

Calibre 자체가 같은 메타데이터 소스에서 제목과 저자가 완전히 같은 결과를 병합할 수 있으므로 서로 다른 판본이 일부 합쳐져 보일 수 있습니다.

## 0.5.3 핵심 변경

0.5.3은 실사용에서 발견된 식별자 연계와 검색 회귀를 수정한 안정화 릴리스입니다.

```text
YES24 itemId → identifier:yes24 저장
TOP 99 → TOP99 검색 fallback
3 D → 3D 검색 fallback
정규화 제목이 동일한 경우 숫자 권차 충돌로 오인하지 않음
실제로 다른 권차의 sequence-conflict 검사는 유지
```

## 표지

YES24 표지는 다음 고해상도 경로를 우선 사용합니다.

```text
https://image.yes24.com/goods/{itemId}/XL
```

identify 단계에서 후보 ISBN과 정확한 YES24 표지 URL을 연결해 캐시합니다. 사용자가 후보를 선택하면 해당 ISBN에 연결된 표지를 우선 사용합니다.

## 시리즈

YES24 `seriesId`는 권 번호가 아니라 시리즈 자체의 식별자이므로 `series_index`로 직접 저장하지 않습니다.

권차는 제목, 공식 시리즈 정보, 정확한 상품 페이지처럼 직접적인 근거가 있을 때만 저장합니다. 근거가 없으면 시리즈명만 저장될 수 있으며 번호를 임의로 만들지 않습니다.

## 태그

태그는 YES24 상품 분류를 기반으로 만듭니다. `도서`, `국내도서`, `외국도서`, `eBook`처럼 지나치게 넓은 container label은 제거합니다. eBook 상품에는 `전자책` 태그가 추가될 수 있습니다.

## 저장 필드

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

상세 매칭·시리즈·표지 규칙은 [METADATA_DESIGN.md](../METADATA_DESIGN.md)를 참고하세요.

## Library Status와의 관계

Metadata Source가 저장한 `identifier:yes24`는 Library Status 자동 연동의 우선 식별자입니다. 자세한 흐름은 [두 플러그인의 연동](./integration.md)을 참고하세요.

## 버그 리포트

가능하면 제목, 저자, ISBN, 실제 Calibre 결과, 기대한 결과와 `--verbose` 로그를 함께 제공하세요.

```powershell
& "C:\Program Files\Calibre2\fetch-ebook-metadata.exe" `
  --allowed-plugin Yes24 `
  --title "책 제목" `
  --authors "저자명" `
  --isbn "ISBN" `
  --verbose
```

ISBN이 없는 사례는 `--isbn` 옵션을 빼면 됩니다.
