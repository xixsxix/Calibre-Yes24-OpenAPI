# YES24 Library Status 0.3.7

릴리스 날짜: 2026-09-17

## 변경 사항

0.3.7은 기능 범위를 넓히는 릴리스가 아니라 배포 완성도와 공개 패키지 일치를 위한 패치 릴리스입니다.

- 전용 툴바 아이콘을 `library_status/images/icon.png`로 추가했습니다.
- `Yes24LibraryStatus.zip`에 `images/icon.png`를 포함합니다.
- Interface Action의 `genesis()`에서 Calibre `get_icons()`로 패키지 아이콘을 읽어 `qaction`에 설정합니다.
- 공개 `ui.py`는 내부에서 검증한 0.3.2~0.3.5 런타임 수정이 통합된 구현을 유지합니다.
- 0.3.6의 storefront steady-seller cache, startup snapshot prefetch, 자동 연동, 수동 live query, 월별 history 동작은 변경하지 않습니다.

## 검증

Windows Calibre 9.14.x 실환경에서 툴바 아이콘 표시를 확인했습니다. private 개발 기준 회귀 테스트는 `test_status_core.py`, `test_history_core.py`, `test_auto_contract.py`, `test_steady_cache.py`, `verify_release_036.py`가 통과했습니다.

공개 CI는 core/history/public-contract/steady-cache 테스트와 ZIP 빌드를 수행하며, ZIP에 `images/icon.png`가 실제 포함되는지와 런타임 버전 `(0, 3, 7)`을 추가로 검사합니다.

## 네트워크

네트워크 동작 변경은 없습니다. Library Status는 YES24 Open API 공개 랭킹 목록과 YES24 국내도서 스테디셀러 공개 storefront를 사용합니다. startup 요청에는 EPUB/PDF 파일이나 라이브러리 전체 메타데이터를 전송하지 않습니다.

## 설치 자산

`Yes24LibraryStatus.zip`
