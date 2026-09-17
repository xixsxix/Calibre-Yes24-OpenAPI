# 릴리스 문서

이 저장소에는 두 개의 플러그인이 함께 있으므로 버전 번호만 쓰지 않고 항상 플러그인 이름과 버전을 함께 표기합니다.

## 현재 안정 기준

| 플러그인 | 버전 | 상태 | 설치 파일 |
| --- | ---: | --- | --- |
| YES24 Metadata Source | 0.5.5 | 공개 안정 릴리스 | `Yes24.zip` |
| YES24 Library Status | 0.3.7 | 공개 안정 릴리스 | `Yes24LibraryStatus.zip` |

## 2026-09-17 릴리스

### YES24 Library Status 0.3.7

- 전용 툴바 아이콘 `images/icon.png`를 설치 ZIP에 포함합니다.
- 실제 Interface Action 시작 시 패키지 아이콘을 로드합니다.
- 0.3.6의 startup snapshot, 자동 상태 연동, 월별 이력, storefront steady-seller cache 동작을 유지합니다.
- Windows Calibre 9.14.x에서 아이콘 표시와 기존 회귀 테스트를 확인했습니다.
- 공개 태그: `library-status-v0.3.7`
- 설치 자산: `Yes24LibraryStatus.zip`

상세 릴리스 메모: [Library Status 0.3.7](./releases/library-status-0.3.7.md)

## 2026-09-16 릴리스

### YES24 Metadata Source 0.5.5

- YES24 상품 페이지 공식 관련분류 2단계 태그 보강
- ISBN 뒤 부가번호가 붙은 identifier에서 유효 ISBN 추출
- 공개 태그: `v0.5.5`
- 설치 자산: `Yes24.zip`

상세 릴리스 메모: [Metadata Source 0.5.5](./releases/metadata-source-0.5.5.md)

## 2026-09-14 릴리스

### YES24 Library Status 0.3.6

- Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회합니다.
- 고유 product `itemId` 집합을 `<Calibre config>/yes24_library_status/steady_seller.json`에 저장합니다.
- 공개 태그: `library-status-v0.3.6`

## GitHub Release 자산

```text
Yes24.zip
Yes24LibraryStatus.zip
```

GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일이 아닙니다.
