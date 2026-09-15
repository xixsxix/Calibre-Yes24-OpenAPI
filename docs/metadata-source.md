# YES24 Metadata Source

YES24 공식 Open API를 중심으로 사용하는 Calibre Desktop Metadata Source 플러그인입니다.

현재 안정 버전: **0.5.5**

## 역할

한국 도서의 제목, 저자, ISBN, 출판사, 발행일, 책소개, 태그, 언어, 시리즈와 고해상도 표지를 Calibre로 가져옵니다. 선택한 YES24 상품의 숫자 `itemId`를 `identifier:yes24`로 저장하여 Library Status와의 연동 기준으로 사용합니다.

## 0.5.5 주요 기능

- ISBN-13 직접 조회 및 제목/저자 fallback 검색
- ISBN 뒤에 5자리 부가번호가 붙은 EPUB identifier에서 유효 ISBN 추출
- YES24 `itemId` → `identifier:yes24` 저장
- 최대 10개 후보를 자체 서지 랭킹 순서로 표시
- YES24 상품 페이지 `관련분류 > 카테고리 분류`에서 광역 루트 아래 2단계까지 태그 보강
- 여러 공식 관련분류 경로 병합 및 정확한 중복 제거
- 수상/미디어 추천 분류와 `이 상품의 태그` 제외
- Library Status 0.3.6 공유 캐시 기반 `⭐스테디셀러` 태그
- YES24 시리즈, 책소개, 고해상도 `/XL` 표지 보강

## ISBN 처리

Calibre에 저장된 원본 ISBN identifier는 검색을 위해 직접 수정하지 않습니다. 검색 시 문자열에서 체크디지트가 유효한 ISBN을 추출합니다.

```text
978-89-329-6038-8 08890 → 9788932960388
978-89-329-6787-5 05170 → 9788932967875
```

YES24 Open API가 해당 ISBN을 검색 인덱스에서 반환하지 않으면 제목/저자가 있는 경우 기존 후보 검색 fallback으로 넘어갑니다. 이 경우 같은 작품의 다른 판본이 후보로 나올 수 있으므로 사용자가 판본을 확인해야 합니다.

## 태그

0.5.5는 YES24 상품 페이지의 공식 `카테고리 분류` 경로마다 광역 루트 아래 첫 두 단계만 사용합니다. `/`가 포함된 공식 이름은 하나의 태그로 유지합니다.

```text
국내도서 > 소설/시/희곡 > 고전문학 > 서양 고전문학
국내도서 > 소설/시/희곡 > 영미소설 > 영미 장편소설
→ 소설/시/희곡, 고전문학, 영미소설
```

`수상내역 및 미디어 추천 분류`와 `이 상품의 태그`는 이 카테고리 보강에 섞지 않습니다. 상품 페이지 요청/파싱이 실패하면 기존 Open API 태그만 사용합니다.

## 설치

GitHub Releases의 `Yes24.zip`을 설치하세요. GitHub가 자동 생성하는 Source code ZIP은 Calibre 플러그인 설치 파일이 아닙니다.

```text
Preferences → Plugins → Load plugin from file → Yes24.zip
```

## API Key

YES24 Metadata Source 설정에서 YES24 Open API Key를 입력합니다. API Key는 공개 저장소나 버그 리포트에 포함하지 마세요.

## 저장 필드

`title`, `authors`, `identifier:isbn`, `identifier:yes24`, `publisher`, `pubdate`, `comments`, `tags`, `languages`, `series`, `series_index`, `Cover`

상세 네트워크 동작은 [네트워크와 데이터 처리](./network-and-data.md), 릴리스 변경점은 [Metadata Source 0.5.5](./releases/metadata-source-0.5.5.md)를 참고하세요.
