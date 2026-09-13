# Documentation

이 저장소는 서로 연동되는 두 개의 Calibre 플러그인을 함께 관리합니다.

| 문서 | 설명 |
| --- | --- |
| [Metadata Source](./metadata-source.md) | YES24 서지정보·표지·`identifier:yes24`를 가져오는 Metadata Source 플러그인 |
| [Library Status](./library-status.md) | YES24 베스트셀러·스테디셀러·순위 이력을 사용자 정의 컬럼에 기록하는 Interface Action 플러그인 |
| [두 플러그인의 연동](./integration.md) | Metadata Source → `identifier:yes24` → Library Status 자동 갱신 흐름 |
| [네트워크와 데이터 처리](./network-and-data.md) | API 요청, startup prefetch, 로컬 캐시, 전송하지 않는 데이터 |
| [릴리스 문서](./releases.md) | 두 플러그인의 버전 체계와 릴리스 노트 안내 |

## 권장 설치 순서

```text
1. YES24 Metadata Source 설치
2. YES24 API Key 설정
3. YES24 Library Status 설치
4. Metadata Source로 메타데이터를 저장
5. Library Status가 identifier:yes24 변경을 감지해 상태/순위를 자동 기록
```

두 플러그인은 각각 별도의 Calibre 플러그인 ZIP으로 설치되며 독립적으로 동작할 수 있습니다. 다만 Library Status의 자동 연동은 Metadata Source가 저장하는 `identifier:yes24`를 우선 사용하므로 함께 설치하는 것을 권장합니다.

## 문서 원칙

- 루트 `README.md`는 프로젝트 전체와 설치 입구만 설명합니다.
- 기능별 상세 사용법은 `docs/` 아래에서 플러그인별로 분리합니다.
- 구현 세부 규칙은 설계 문서에 둡니다. Metadata Source의 세부 매칭 규칙은 기존 [METADATA_DESIGN.md](../METADATA_DESIGN.md)를 유지합니다.
- 릴리스 노트는 플러그인 이름과 버전을 함께 표기하여 같은 저장소 안에서도 어느 플러그인의 변경인지 명확히 구분합니다.
- 설치 전에 알아야 하는 자동 네트워크 동작은 루트 README와 Library Status 문서 양쪽에 모두 고지합니다.
