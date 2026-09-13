# YES24 Metadata Source for Calibre 0.5.3

0.5.3은 0.5.0 이후 실사용에서 발견된 식별자 연계와 검색 회귀를 정리한 안정화 릴리스입니다.

## 주요 변경

- 선택한 YES24 상품의 `itemId`를 Calibre의 `yes24` 식별자로 저장합니다. 별도의 YES24 Library Status 플러그인이 사용자가 선택한 정확한 판본을 식별할 수 있습니다.
- ASCII 문자와 숫자 사이 공백 차이를 보완하는 검색 fallback을 추가했습니다. 예: `TOP 99` → `TOP99`, `3 D` → `3D`. 한국어 일반 띄어쓰기나 `제 3권` 같은 표현은 임의로 합치지 않습니다.
- `TOP 99`와 `TOP99`가 기존 정규화 기준으로 같은 제목인데도 standalone 숫자를 권차로 오인해 후보를 제외하던 문제를 수정했습니다. 정규화 제목이 동일한 경우에만 sequence-conflict 판정을 건너뛰므로 실제 권차 충돌 검사는 그대로 유지됩니다.

## 실사용 회귀 확인

`부린이가 가장 궁금한 질문 TOP 99` / 레비앙 / ISBN `9791161253718` 사례에서 YES24의 실제 제목 `부린이가 가장 궁금한 질문 TOP99`를 찾고 정확한 판본을 반환하는 것을 Calibre에서 확인했습니다.

## 누적 호환성

0.5.0의 ranked candidate discovery, exact compatible ISBN 처리, 선택 후보별 표지 캐시, title/subtitle matching, contributor/translator 판본 검사, 보수적인 series/series_index 처리와 Comments 안전장치를 유지합니다.
