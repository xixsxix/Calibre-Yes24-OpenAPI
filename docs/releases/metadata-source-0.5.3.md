# YES24 Metadata Source 0.5.3

YES24 Metadata Source 0.5.3은 현재 공개 안정 릴리스입니다.

이 문서는 두 플러그인의 릴리스 문서 구조를 통일하기 위한 인덱스 페이지입니다. 기존 공개 릴리스 노트의 URL 호환성을 유지하기 위해 상세 변경 기록은 루트의 [RELEASE_NOTES_0.5.3.md](../../RELEASE_NOTES_0.5.3.md)에 계속 보존합니다.

## 핵심 변경

- 선택한 YES24 상품의 숫자 `itemId`를 Calibre `identifier:yes24`로 저장
- `TOP 99` → `TOP99`, `3 D` → `3D` 같은 ASCII 문자/숫자 공백 차이에 대한 검색 fallback
- 정규화 제목이 동일한 경우 숫자 권차 충돌로 잘못 판정하던 문제 수정
- 실제로 다른 권차의 기존 sequence-conflict 검사는 유지

## Library Status와의 연결

0.5.3에서 저장하는 `identifier:yes24`는 YES24 Library Status 자동 연동의 우선 식별자입니다.

```text
Metadata Source 0.5.3
→ identifier:yes24 저장
→ Library Status identifiers 이벤트 감지
→ YES24 상태/순위 자동 갱신
```

두 플러그인의 전체 연동은 [integration.md](../integration.md)를 참고하세요.

## 공개 릴리스

설치 자산 이름:

```text
Yes24.zip
```

GitHub의 자동 생성 `Source code (zip)`이 아니라 Release에 첨부된 `Yes24.zip`을 Calibre에 설치해야 합니다.
