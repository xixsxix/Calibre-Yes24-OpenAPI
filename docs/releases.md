# 릴리스 문서

이 저장소에는 두 개의 플러그인이 함께 있으므로 버전 번호만 쓰지 않고 항상 플러그인 이름과 버전을 함께 표기합니다.

## 현재 안정 기준

| 플러그인 | 버전 | 상태 | 설치 파일 |
| --- | ---: | --- | --- |
| YES24 Metadata Source | 0.5.3 | 공개 안정 릴리스 | `Yes24.zip` |
| YES24 Library Status | 0.3.5 | 공개 안정 릴리스 | `Yes24LibraryStatus.zip` |

## 릴리스 노트 규칙

앞으로 새 릴리스 문서는 `docs/releases/` 아래에서 플러그인 이름이 드러나는 파일명으로 관리합니다.

```text
docs/releases/
├─ metadata-source-0.5.3.md
└─ library-status-0.3.5.md
```

기존 Metadata Source의 루트 `RELEASE_NOTES_*.md` 파일은 기존 링크 호환성을 위해 유지합니다. 새로운 문서 구조로 옮기는 과정에서 역사적인 릴리스 노트를 삭제하거나 URL을 깨뜨리지 않습니다.

## Metadata Source

현재 공개 안정 릴리스는 **0.5.3**입니다.

기존 릴리스 노트:

- [0.5.3](../RELEASE_NOTES_0.5.3.md)
- [0.5.0](../RELEASE_NOTES_0.5.0.md)
- [0.4.13](../RELEASE_NOTES_0.4.13.md)
- [0.4.12](../RELEASE_NOTES_0.4.12.md)
- [0.4.11](../RELEASE_NOTES_0.4.11.md)

## Library Status

- [0.3.5 검증 및 릴리스 기준](./releases/library-status-0.3.5.md)
- [0.3.5 공개 패키지 최종 검증](./releases/library-status-0.3.5-package-validation.md)

Library Status는 Metadata Source와 버전 번호를 공유하지 않습니다. 예를 들어 Metadata Source 0.5.3과 Library Status 0.3.5는 서로 다른 플러그인의 독립적인 버전입니다.

## GitHub Release 자산

같은 저장소의 GitHub Releases에서 두 설치 파일을 명확한 이름으로 구분합니다.

```text
Yes24.zip               # Metadata Source
Yes24LibraryStatus.zip  # Library Status
```

GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일로 안내하지 않습니다.
