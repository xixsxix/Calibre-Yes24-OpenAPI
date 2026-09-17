# YES24 Library Status

YES24 공개 랭킹 목록을 Calibre 사용자 정의 컬럼에 기록하는 Interface Action 플러그인입니다. 현재 릴리스 후보는 **0.3.7**입니다.

## Metadata Source 연동

YES24 Metadata Source가 저장한 `identifier:yes24`를 우선 사용하고 ISBN13을 보조 식별자로 사용합니다. Metadata Source 저장 직후 identifiers 변경 이벤트를 감지해 해당 도서의 YES24 상태를 자동 갱신할 수 있습니다.

Calibre 시작 후 YES24 국내도서 스테디셀러 storefront를 백그라운드에서 순회해 `<Calibre config>/yes24_library_status/steady_seller.json` 공유 캐시를 생성합니다. Metadata Source 0.5.5는 이 캐시를 로컬 대조해 `⭐스테디셀러` 태그를 추가합니다.

## 현재 상태와 이력

현재 snapshot은 YES24 Open API의 실시간/종합/특가/스테디/일간/월간 베스트 목록을 사용합니다. 월별 과거 이력은 로컬 SQLite 캐시에 동기화합니다. 수동 `YES24 상태 갱신`은 live query를 유지하고 자동 갱신은 startup snapshot cache를 우선 사용합니다.

## 0.3.7 툴바 아이콘

0.3.7은 설치 ZIP에 `images/icon.png`를 포함하고 Interface Action 시작 시 이 리소스를 툴바 아이콘으로 설정합니다. Windows Calibre 9.14.x 실환경에서 아이콘 표시를 확인했습니다. 상태/이력/자동 연동/스테디셀러 캐시 동작은 0.3.6 기준선을 유지합니다.

## 네트워크 동작

API Key가 설정되어 있으면 Calibre 시작 후 YES24 Open API 공개 랭킹 목록을 prefetch합니다. 또한 YES24 국내도서 스테디셀러 공개 storefront를 조회합니다. startup 요청에는 사용자의 EPUB/PDF 파일, 책 제목, ISBN, `identifier:yes24`, 라이브러리 전체 메타데이터를 전송하지 않습니다.

## 빌드

```powershell
cd library_status
python .\test_status_core.py
python .\test_history_core.py
python .\test_public_contract.py
python .\test_steady_cache.py
python .\build_plugin.py
```

생성 파일은 `Yes24LibraryStatus.zip`이며 패키지 안에 `images/icon.png`가 포함되어야 합니다.
