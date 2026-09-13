# YES24 Library Status source

이 디렉터리는 **YES24 Library Status** Calibre Interface Action 플러그인의 공개 소스입니다.

현재 버전: **0.3.5**

루트의 YES24 Metadata Source와는 별도 ZIP으로 설치되지만, Metadata Source가 저장한 `identifier:yes24`와 같은 API Key 설정을 사용해 자동 연동합니다.

## 공개 소스 구조

```text
library_status/
├─ __init__.py
├─ ui.py
├─ client.py
├─ columns.py
├─ history.py
├─ build_plugin.py
├─ test_status_core.py
├─ test_history_core.py
└─ test_public_contract.py
```

내부 개발 과정에서 사용한 버전별 runtime overlay는 공개 패키지에 포함하지 않습니다. 0.3.5에서 실사용 검증된 startup-safe listener, `server_library_id` 처리, 식별자 안정성 검증, startup prefetch와 memory snapshot cache 동작을 `ui.py` 하나로 통합했습니다.

## 빌드

```powershell
cd .\library_status
python .\test_status_core.py
python .\test_history_core.py
python .\test_public_contract.py
python .\build_plugin.py
```

생성 파일:

```text
Yes24LibraryStatus.zip
```

Calibre 설치:

```powershell
& "D:\Program Files\Calibre2\calibre-customize.exe" -a ".\Yes24LibraryStatus.zip"
```

## ZIP 구성

```text
__init__.py
ui.py
client.py
columns.py
history.py
plugin-import-name-yes24_library_status.txt
```

테스트 파일과 빌드 스크립트는 설치 ZIP에 포함하지 않습니다.

## 네트워크 동작

API Key가 설정되어 있으면 Calibre GUI 초기화 완료 후 약 5초 뒤 YES24 공개 랭킹 목록을 자동으로 prefetch합니다. startup prefetch에는 사용자 EPUB 파일, 책 제목, ISBN, `identifier:yes24` 또는 라이브러리 전체 메타데이터를 요청 파라미터로 보내지 않습니다.

자세한 사용자 문서는 [`../docs/library-status.md`](../docs/library-status.md), 네트워크·캐시 설명은 [`../docs/network-and-data.md`](../docs/network-and-data.md)를 참고하세요.
