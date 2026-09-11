# Calibre YES24 Metadata Plugin

**YES24 공식 Open API를 사용하는 독립적인 Calibre Desktop 메타데이터 소스 플러그인**

An independent Calibre Desktop metadata source plugin using the official YES24 Open API.

한국 도서의 제목, 저자, ISBN, 출판사, 발행일, 책소개, 태그, 언어, 시리즈와 고해상도 표지를 Calibre로 가져옵니다. 이 프로젝트는 YES24 또는 Calibre의 공식 플러그인이 아니며, 두 프로젝트와 제휴·승인 관계를 주장하지 않습니다.

현재 릴리스 후보 / Current release candidate: **0.5.0**

## 0.5.0의 핵심 / What's new

0.5.0부터 ISBN이 없는 **낱권 검색**에서는 플러그인이 하나의 판본을 임의로 확정하지 않습니다. 관련 YES24 후보를 모아 서지 유사성 점수가 높은 순서대로 최대 10개를 Calibre에 반환하고, 사용자가 원하는 판본을 선택합니다.

```text
제목/저자 검색
→ 관련 YES24 후보 수집
→ 구매/대여 중복 제거
→ 제목·저자·ISBN·기여자 근거로 점수 계산
→ 높은 점수부터 후보 표시
→ 사용자가 최종 판본 선택
```

정확한 ISBN이 있고 제목/저자와 호환되면 이미 판본이 특정되므로 해당 도서를 한 건으로 반환합니다.

## 주요 기능 / Features

- YES24 공식 Open API 기반 검색
- ISBN-13 직접 조회
- ISBN이 없거나 저장 ISBN이 맞지 않을 때 제목/저자 후보 검색
- 제목/부제 구조를 고려한 검색과 유사도 랭킹
- 번역자 및 보조 기여자를 이용한 판본 구분
- 종이책/eBook, 구판/신판, 시즌/권차 후보 비교
- YES24 `seriesName` 기반 Calibre 시리즈 저장
- 확실한 근거가 있을 때만 `series_index` 저장
- `소개도서`/`추천도서` 같은 마케팅성 series 제외
- API 책소개 우선, 호환 판본 donor와 제한적 HTML fallback
- 목차 형태의 텍스트를 Comments로 잘못 저장하지 않도록 검사
- YES24 고해상도 `/XL` 표지
- 사용자가 선택한 후보의 ISBN에 연결된 정확한 표지 사용

## 요구 사항 / Requirements

- Calibre 5.0 or later
- YES24 Open API key from `developers.yes24.com`
- YES24 Open API 및 필요한 YES24 상품 페이지에 대한 네트워크 접근

## 설치 / Installation

일반 사용자는 GitHub **Releases의 `Yes24.zip`**을 설치하세요. GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 설치 파일이 아닙니다.

```text
Preferences
→ Plugins
→ Load plugin from file
→ Yes24.zip 선택
```

소스에서 직접 빌드하려면:

```powershell
python .\build_plugin.py
calibre-customize.exe -a .\Yes24.zip
```

## YES24 API key 설정 / Configure API key

```text
Preferences
→ Plugins
→ Metadata source plugins
→ Yes24
→ Customize plugin
→ YES24 API key 입력
```

API key는 공개 저장소, 로그, 버그 리포트에 포함하지 마세요.

## 검색 결과 선택 / Choosing a result

ISBN이 없는 검색에서는 후보 #1이 가장 높은 서지 유사성 점수를 가진 결과입니다. #2, #3 이후도 관련 후보이며, 출간연도·권차·종이책/eBook·개정판 차이를 보고 사용자가 선택할 수 있습니다.

명백한 권차 충돌이나 확인된 번역자 충돌처럼 강한 오답 근거가 있는 후보는 목록에서 제외할 수 있습니다.

Calibre 자체가 같은 메타데이터 소스에서 **제목과 저자가 완전히 같은 결과를 병합**할 수 있으므로, 제목·저자가 완전히 동일한 서로 다른 판본은 일부 합쳐져 보일 수 있습니다.

## 표지 / Covers

YES24 표지는 다음 고해상도 경로를 우선 사용합니다.

```text
https://image.yes24.com/goods/{itemId}/XL
```

identify 단계에서 각 후보의 ISBN과 정확한 YES24 표지 URL을 연결해 캐시합니다. 사용자가 후보를 선택하면 Calibre가 그 후보의 ISBN을 표지 단계로 전달하고, 플러그인은 해당 ISBN의 캐시된 표지를 먼저 사용합니다. 따라서 여러 후보 중 어느 책을 골라도 선택한 판본의 표지가 따라옵니다.

캐시에 표지가 없는 경우에만 ISBN 상세조회와 제목/저자 검색을 fallback으로 사용합니다.

## 시리즈 / Series

YES24 `seriesId`는 권 번호가 아니라 시리즈 자체의 식별자입니다. 따라서 `seriesId` 값을 `series_index`로 직접 저장하지 않습니다.

권차는 제목, 공식 시리즈 페이지, 정확한 상품 페이지의 공식 시리즈 라벨처럼 직접적인 근거가 있을 때만 저장합니다. YES24 데이터에 특정 권차가 없으면 시리즈명만 저장될 수 있으며, 플러그인이 번호를 임의로 만들어내지 않습니다.

## 태그 / Tags

태그는 YES24 상품 분류를 기반으로 만듭니다. `도서`, `국내도서`, `외국도서`, `eBook`처럼 지나치게 넓은 container label은 제거합니다. eBook 상품에는 현재 `전자책` 태그가 추가될 수 있습니다.

## 저장 필드 / Fields

```text
title
authors
identifier:isbn
publisher
pubdate
comments
tags
languages
series
series_index
Cover
```

자세한 매칭·시리즈·표지 보완 규칙은 [METADATA_DESIGN.md](./METADATA_DESIGN.md)를 참고하세요.

## 버그 리포트 / Bug reports

가능하면 다음 정보를 함께 보내주세요.

```text
제목 / title
저자 / author
ISBN (있는 경우)
실제 Calibre 결과
잘못되었다고 생각하는 부분
--verbose 로그
```

재현 예:

```powershell
& "C:\Program Files\Calibre2\fetch-ebook-metadata.exe" `
  --allowed-plugin Yes24 `
  --title "책 제목" `
  --authors "저자명" `
  --isbn "ISBN" `
  --verbose
```

ISBN이 없는 사례는 `--isbn` 옵션을 빼면 됩니다.

## 데이터 및 보안 / Data & security

이 공개 저장소에는 캡처한 YES24 API 원문 응답 fixture를 배포하지 않으며 YES24 API key도 저장하지 않습니다. API 데이터의 사용 조건은 YES24 개발자 정책을 확인하세요.

See [SECURITY.md](./SECURITY.md) for credential and reporting guidance.

## Related projects

YES24를 사용하는 기존 Calibre 프로젝트들이 있으며, 일부는 HTML scraping 기반이거나 표지 다운로드에 초점을 둡니다. 이 저장소는 2026 YES24 공식 Open API를 중심으로 독립 구현되었습니다.

## License

GNU General Public License v3.0 only. See [LICENSE](./LICENSE).
