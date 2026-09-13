# YES24 Library Status 0.3.5

0.3.5는 Metadata Source 저장 직후 자동 Status 기록이 현재 YES24 랭킹 목록 전체 조회를 기다리느라 수십 초 지연되는 문제를 줄이기 위한 성능 개선 릴리스입니다.

## 핵심 변경

- Calibre GUI 초기화 완료 후 약 5초 뒤 current YES24 snapshot을 백그라운드에서 미리 준비
- current snapshot은 Calibre 프로세스 메모리에만 보관
- fresh TTL 10분
- 자동 연동에서는 최대 30분 이내 stale snapshot을 즉시 사용 가능
- stale snapshot 사용 시 background refresh
- cache가 전혀 없으면 live snapshot fallback
- 수동 `YES24 상태 갱신`은 기존 live-query 경로 유지
- 자동 경로의 `#yes24_checked`에는 worker 실행 시각이 아니라 실제 snapshot 획득 시각 기록
- Calibre 종료 시 prefetch timer/worker 중지 및 메모리 snapshot 폐기

## 네트워크 동작 고지

YES24 Metadata Source API Key가 설정되어 있으면 Calibre 시작 후 자동으로 YES24 Open API에 접속하여 베스트셀러·스테디셀러 등 공개 랭킹 목록을 미리 가져옵니다.

startup prefetch 자체에는 사용자의 EPUB 파일, 책 제목, ISBN, `identifier:yes24` 또는 라이브러리 전체 메타데이터를 요청 파라미터로 보내지 않습니다. 받아온 공개 랭킹 목록과 사용자의 식별자 비교는 로컬에서 수행합니다.

## 캐시 정책

```text
Calibre 시작
→ GUI 초기화 완료
→ 약 5초 후 current snapshot prefetch
→ 메모리 캐시 저장
→ 10분 주기 background refresh

Metadata Source 저장
→ identifier:yes24 이벤트
→ fresh/stale 메모리 snapshot 사용
→ 로컬 itemId/ISBN 대조
→ history.sqlite3 월별 이력 병합
→ Status 컬럼 기록
```

현재 snapshot은 영구 파일로 저장하지 않습니다. `history.sqlite3`는 완료된 월의 월별 이력 캐시 용도로만 사용합니다.

## 실사용 성능 검증

Calibre 9.14 환경에서 startup prefetch 및 Metadata Source 자동 연동을 확인했습니다.

```text
Calibre startup: 1.87s
startup prefetch dispatch: +5s
snapshot observations: 10340
snapshot prefetch elapsed: 12.796s
```

캐시 준비 후 automatic worker 측정:

```text
book 26: cache age 72.6s, worker elapsed 0.276s
book 29: cache age 92.3s, worker elapsed 0.253s
book 32: cache age 432.7s, worker elapsed 0.268s
history: downloaded=0, reused=32
```

book 26/29는 current/history 매칭이 없는 책으로 `status=''`, `best_rank=None`, `matched_books=0`이 정상적으로 처리되었습니다.

book 32는 실제 랭킹 기록이 있는 책으로 다음 값이 계산·기록되었습니다.

```text
itemId: 126181478
ISBN13: 9788962632729
history matched_books: 1
status: 종합베스트|스테디셀러|일간베스트|월간베스트
best_rank: 6
years: 2024|2025|2026
automatic refresh complete: current=1 history=1
```

따라서 `identifier:yes24` 이벤트 수신 → 자동 큐 → 메모리 snapshot 매칭 → 월별 history 병합 → 6개 사용자 정의 컬럼 기록까지 실환경에서 정상 동작했습니다.

## 10분 TTL background refresh 검증

```text
14:11:10 snapshot prefetch skipped: cache fresh age=565.3s
14:21:10 snapshot prefetch dispatch
14:21:10 snapshot prefetch worker started
14:21:25 snapshot prefetch worker finished observations=10340 elapsed=15.096s
14:21:25 snapshot cache stored observations=10340 elapsed=15.097s
```

fresh cache에서는 불필요한 중복 요청을 건너뛰고, 이후 주기에는 새 snapshot을 백그라운드에서 받아 메모리 캐시를 정상 교체했습니다.

## 연속 실사용 검증

실제 Metadata Source 작업을 약 30권 연속으로 수행하면서 자동 Status 갱신이 안정적으로 진행되는 것을 확인했습니다.

## 검증 상태

| 항목 | 결과 |
| --- | --- |
| startup prefetch | PASS |
| memory snapshot cache hit | PASS |
| cache worker 성능 | PASS |
| identifier 안정성 검증 | PASS |
| 사용자 정의 컬럼 자동 기록 | PASS |
| 랭킹 있는 책의 상태/순위 계산 | PASS |
| current + 월별 history 병합 | PASS |
| 10분 TTL background refresh | PASS |
| 약 30권 연속 자동 연동 | PASS |

0.3.5를 Library Status의 안정 기준 버전으로 확정합니다.
