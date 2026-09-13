# 릴리스 문서

이 저장소에는 두 개의 플러그인이 함께 있으므로 버전 번호만 쓰지 않고 항상 플러그인 이름과 버전을 함께 표기합니다.

## 현재 안정 기준

| 플러그인 | 버전 | 상태 | 설치 파일 |
| --- | ---: | --- | --- |
| YES24 Metadata Source | 0.5.4 | 공개 안정 릴리스 | `Yes24.zip` |
| YES24 Library Status | 0.3.6 | 공개 안정 릴리스 | `Yes24LibraryStatus.zip` |

## 2026-09-14 릴리스

### YES24 Metadata Source 0.5.4

- Library Status 0.3.6이 만든 로컬 storefront steady-seller cache를 읽어 선택된 YES24 `itemId`가 포함되면 `⭐스테디셀러` 태그를 추가합니다.
- 별 태그 판정을 위해 Metadata Source가 storefront HTML 요청을 추가하지 않습니다.
- 캐시가 없거나 손상되어도 일반 메타데이터 검색은 그대로 동작합니다.
- 공개 태그: `v0.5.4`
- 설치 자산: `Yes24.zip`

### YES24 Library Status 0.3.6

- Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회합니다.
- 고유 product `itemId` 집합을 `<Calibre config>/yes24_library_status/steady_seller.json`에 원자적으로 저장합니다.
- 갱신 실패 시 이전 정상 캐시를 유지하고 한 차례 지연 재시도합니다.
- 공개 태그: `library-status-v0.3.6`
- 설치 자산: `Yes24LibraryStatus.zip`

실환경 검증은 Calibre 9.14 / Windows 11 / 3,776권 라이브러리에서 수행했고, storefront cache 26페이지 / 1,028 unique product IDs 수집과 양성·음성·다권 재검색을 확인했습니다.

상세 릴리스 메모: [0.5.4 / 0.3.6](../RELEASE_NOTES_0.5.4_AND_LIBRARY_STATUS_0.3.6.md)

## 이전 안정 릴리스

### Metadata Source 0.5.3

- [0.5.3](../RELEASE_NOTES_0.5.3.md)
- [0.5.0](../RELEASE_NOTES_0.5.0.md)
- [0.4.13](../RELEASE_NOTES_0.4.13.md)
- [0.4.12](../RELEASE_NOTES_0.4.12.md)
- [0.4.11](../RELEASE_NOTES_0.4.11.md)

### Library Status 0.3.5

- [0.3.5 검증 및 릴리스 기준](./releases/library-status-0.3.5.md)
- [0.3.5 공개 패키지 최종 검증](./releases/library-status-0.3.5-package-validation.md)

Library Status는 Metadata Source와 버전 번호를 공유하지 않습니다.

## GitHub Release 자산

같은 저장소의 GitHub Releases에서 두 설치 파일을 명확한 이름으로 구분합니다.

```text
Yes24.zip               # Metadata Source
Yes24LibraryStatus.zip  # Library Status
```

GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일로 안내하지 않습니다.
