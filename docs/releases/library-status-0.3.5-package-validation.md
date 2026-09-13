# YES24 Library Status 0.3.5 — Public package validation

2026-09-13에 공개 저장소의 `library-status-0.3.5-public` 브랜치에서 빌드한 통합 공개판을 Calibre 9.14.0에서 재검증했습니다.

## 결과

공개 패키지의 startup prefetch, Metadata Source 연동, 메모리 snapshot cache, 식별자 안정성 확인, 사용자 정의 컬럼 기록까지 정상 동작했습니다.

대표 로그:

```text
Calibre startup: 1.91s
snapshot prefetch delay: 5s
snapshot observations: 10340
snapshot prefetch elapsed: 14.224s

book id: 82
identifier:yes24: 67116558
ISBN13: 9788932034942
snapshot cache age: 53.3s
cached automatic worker: 0.280s
history downloaded: 0
history reused: 32
identifier before/after worker: stable
automatic refresh complete: current=0 history=0
```

`current=0`, `history=0`은 이 테스트 도서가 현재/과거 YES24 랭킹 목록에서 매칭되지 않은 결과이며 오류가 아닙니다. 중요한 패키징 검증 항목인 `identifier:yes24` 이벤트 수신, 자동 큐 진입, cache hit, history 재사용, 식별자 재검증, 6개 사용자 정의 컬럼 write 경로가 모두 정상 완료되었습니다.

## CI

PR #1의 최종 CI run #92에서 두 job이 모두 성공했습니다.

```text
Metadata Source: compile / behavior contract / build / ZIP verification PASS
Library Status: compile / core tests / history tests / public contract / build / ZIP verification PASS
```

## 결론

공개 저장소용으로 통합한 YES24 Library Status 0.3.5 소스와 빌드 ZIP은 실환경 package validation을 통과했습니다. PR #1은 이 검증 후 `main`에 병합했습니다.
