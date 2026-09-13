# YES24 Library Status

Calibre 라이브러리의 도서를 YES24 공개 랭킹 목록과 대조하여 현재 상태와 과거 순위 이력을 사용자 정의 컬럼에 기록하는 Interface Action 플러그인입니다.

현재 검증 완료 버전: **0.3.5**

## 역할

Metadata Source가 저장한 `identifier:yes24`를 우선 사용하고 ISBN13을 보조 식별자로 사용하여 YES24 베스트셀러·스테디셀러 목록 및 월별 이력과 책을 대조합니다.

자동 연동과 수동 갱신을 모두 지원합니다.

## 설치

공식 릴리스 이후에는 GitHub Releases의 `Yes24LibraryStatus.zip`을 설치합니다. GitHub가 자동 생성하는 `Source code (zip)`은 Calibre 플러그인 설치 파일이 아닙니다.

```text
Preferences
→ Plugins
→ Load plugin from file
→ Yes24LibraryStatus.zip 선택
```

Library Status 0.3.5의 최소 Calibre 버전은 **9.0.0**입니다.

Metadata Source와 함께 사용할 때는 다음 순서를 권장합니다.

```text
1. YES24 Metadata Source 설치
2. Metadata Source에서 YES24 API Key 설정
3. YES24 Library Status 설치
4. Library Status의 `YES24 상태 갱신`을 한 번 수동 실행
5. 필요한 사용자 정의 컬럼이 생성되면 Calibre 재시작
6. 이후 Metadata Source 저장 시 자동 Status 연동 사용
```

첫 수동 실행에서 필요한 컬럼이 없으면 플러그인이 컬럼을 생성하고 Calibre 재시작을 안내합니다.

## 자동 연동

```text
Calibre 시작
→ GUI 초기화 완료 약 5초 후 YES24 current snapshot prefetch
→ 메모리 캐시 준비

Metadata Source로 메타데이터 저장
→ identifier:yes24 변경 이벤트 감지
→ 해당 책을 자동 갱신 큐에 추가
→ 메모리 snapshot에서 itemId/ISBN 로컬 대조
→ history.sqlite3의 완료 월 이력 병합
→ 사용자 정의 컬럼 기록
```

캐시가 준비된 상태의 실사용 테스트에서는 automatic worker가 약 0.25~0.28초에 완료되었습니다. 약 30권 연속 Metadata Source 작업에서도 자동 연동이 안정적으로 동작하는 것을 확인했습니다.

## 수동 갱신

사용자가 직접 `YES24 상태 갱신`을 실행하면 current snapshot 캐시를 사용하지 않고 기존 live 조회 경로로 현재 YES24 상태를 다시 확인합니다.

수동 실행은 선택한 책에 `identifier:yes24` 또는 ISBN13이 있어야 합니다. 두 식별자가 모두 없으면 조회를 건너뜁니다.

## 사용자 정의 컬럼

| lookup key | 권장 표시 이름 | 타입 | 의미 |
| --- | --- | --- | --- |
| `#yes24_status` | YES24 상태 | text | 현재 확인된 상태 |
| `#yes24_rank_detail` | YES24 순위 | text | 현재 목록별 순위 요약 |
| `#yes24_best_rank` | YES24 최고순위 | int | 현재 + 과거 월별 이력 통합 최고 순위 |
| `#yes24_best_record` | YES24 최고기록 | text | 최고 기록의 종류·기간·순위 |
| `#yes24_years` | YES24 기록연도 | text | 기록이 존재하는 연도 |
| `#yes24_checked` | YES24 확인일 | datetime | 사용한 current snapshot을 실제로 받은 시각 |

`#yes24_status`와 `#yes24_years`는 다중값 컬럼이 아니라 `|`가 포함된 하나의 문자열로 저장합니다.

기존에 같은 lookup key의 컬럼이 있지만 datatype 또는 multi-value 설정이 다르면 자동으로 덮어쓰지 않고 충돌로 처리합니다.

## 확인하는 현재 상태

current snapshot은 YES24 Category API의 다음 목록을 조회합니다.

- 실시간 베스트셀러
- 종합 베스트셀러
- 특가 베스트셀러
- 스테디셀러
- 일별 베스트셀러
- 월별 베스트셀러

일별·월별 current 상태는 한국 시간 기준 전일을 명시적으로 조회합니다.

## 과거 월별 이력

과거 이력은 완료된 월의 월별 베스트셀러를 로컬 SQLite 캐시에 저장해 재사용합니다.

```text
<Calibre config>/yes24_library_status/history.sqlite3
```

실제 API 점검 기준으로 첫 구현의 수집 하한은 2024-01입니다. 확인된 예시는 다음과 같습니다.

```text
2026-08-01: data available
2025-01-01: data available
2024-01-01: data available
2023-01-01: no data at checked point
```

이는 YES24에 2023년 데이터가 어떤 날짜에도 절대 존재하지 않는다는 의미가 아니라, 실제 점검한 API 체크포인트를 기준으로 둔 보수적인 하한입니다.

캐시에는 원본 YES24 JSON 전체를 저장하지 않고 기간, 카테고리, 순위, itemId, ISBN13 등 매칭에 필요한 최소 필드만 저장합니다.

## startup prefetch와 캐시

0.3.5는 Metadata Source 저장 직후 Status 기록이 current 랭킹 전체 조회를 기다리느라 수십 초 지연되던 문제를 줄이기 위해 current snapshot을 미리 준비합니다.

```text
GUI 초기화 완료
→ 5초 후 background prefetch
→ process-local memory cache
→ fresh TTL 10분
→ 최대 30분 stale snapshot 사용 가능
→ stale 사용 시 background refresh
→ cache 없음: live snapshot fallback
```

current snapshot은 디스크에 영구 저장하지 않으며 Calibre 종료 시 폐기합니다.

실사용에서는 fresh cache일 때 refresh를 건너뛰고, 이후 주기에 새 snapshot을 백그라운드에서 다시 받아 교체하는 동작까지 확인했습니다.

## `#yes24_checked`의 의미

자동 갱신에서 `#yes24_checked`는 컬럼을 쓴 시각이 아니라 해당 상태 판단에 사용한 current snapshot을 실제로 받은 시각입니다.

예를 들어 snapshot을 14:21에 받고 14:28에 책을 저장했다면 `#yes24_checked`는 14:21 부근이 될 수 있습니다. 이는 오류가 아니라 데이터의 실제 신선도를 나타내기 위한 동작입니다.

## 식별자 안정성

자동 worker가 시작할 때의 `(YES24 itemId, ISBN13)`와 종료 시점 DB의 식별자를 다시 비교합니다. 작업 중 식별자가 변경되면 첫 결과를 그대로 최종값으로 간주하지 않고 해당 책을 다시 자동 큐에 넣습니다.

Calibre DB listener의 library id는 `server_library_id` 기준으로 비교하여 현재 열린 라이브러리의 이벤트만 처리합니다.

## API Key

Library Status는 별도 API Key 입력란을 두지 않고 YES24 Metadata Source 설정의 API Key를 사용합니다.

```text
metadata_sources/Yes24.json
```

따라서 두 플러그인을 함께 사용할 때 API Key는 Metadata Source에서 한 번만 설정하면 됩니다.

## 네트워크 동작

API Key가 설정되어 있으면 Calibre 시작 후 Library Status가 YES24 Open API에 자동 접속하여 공개 랭킹 목록을 백그라운드에서 미리 가져옵니다.

startup prefetch 요청에는 사용자의 EPUB 파일, 개별 책 제목, ISBN, `identifier:yes24` 또는 라이브러리 전체 메타데이터를 요청 파라미터로 보내지 않습니다. 공개 랭킹 목록을 받은 뒤 식별자 대조는 로컬에서 수행합니다.

자세한 내용은 [네트워크와 데이터 처리](./network-and-data.md)를 참고하세요.

## 진단 로그

```text
<Calibre config>/yes24_library_status/auto_debug.log
```

같은 내용은 `calibre-debug -g` 콘솔에서도 확인할 수 있습니다. API Key와 YES24 원본 응답 전체는 로그에 기록하지 않습니다.

주요 성능 로그 예시는 다음과 같습니다.

```text
snapshot prefetch worker started
snapshot prefetch worker finished observations=... elapsed=...s
snapshot cache stored observations=... elapsed=...s
snapshot cache hit age=...s observations=...
cached worker finished source='memory' age=...s elapsed=...s history=...
```

## 공개 소스와 빌드

공개 소스는 저장소의 `library_status/` 디렉터리에 있습니다. 내부 개발 과정에서 사용한 버전별 overlay 파일은 공개 패키지에 넣지 않고, 0.3.5에서 검증한 동작을 하나의 `ui.py`로 통합합니다.

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

소스 테스트와 빌드:

```powershell
cd .\library_status
python .\test_status_core.py
python .\test_history_core.py
python .\test_public_contract.py
python .\build_plugin.py
```

설치:

```powershell
& "D:\Program Files\Calibre2\calibre-customize.exe" -a ".\Yes24LibraryStatus.zip"
```

공개 ZIP에는 실행에 필요한 `__init__.py`, `ui.py`, `client.py`, `columns.py`, `history.py`와 Calibre 플러그인 import marker만 포함합니다.

## 0.3.5 검증 결과

Calibre 9.14.0 실환경에서 다음 항목을 확인했습니다.

- startup prefetch 정상 동작
- memory snapshot cache hit
- cache worker 약 0.25~0.28초
- `identifier:yes24` 이벤트 자동 큐 진입
- 식별자 안정성 검증
- 랭킹 없는 책 정상 처리
- 랭킹 있는 책의 current + history 병합
- 6개 사용자 정의 컬럼 기록
- 10분 TTL background refresh
- 약 30권 연속 Metadata Source 자동 연동

위 실사용 검증은 private 개발 빌드 0.3.5에 대한 결과입니다. 공개 소스는 같은 동작을 읽기 쉬운 단일 `ui.py` 구조로 정리했으므로, 공식 Release 자산을 게시하기 전에 공개 빌드 ZIP을 Calibre 9.14.x에서 한 번 더 설치·회귀 확인합니다.

0.3.5의 실사용 기준선과 측정값은 [릴리스 문서](./releases/library-status-0.3.5.md)에 기록합니다.
