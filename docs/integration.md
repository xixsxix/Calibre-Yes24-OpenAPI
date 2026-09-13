# Metadata Source와 Library Status 연동

YES24 프로젝트의 두 플러그인은 역할을 분리하면서 `identifier:yes24`를 통해 연결됩니다.

## 역할 분담

**YES24 Metadata Source**는 한 권의 책에 대한 서지정보를 찾고 Calibre 메타데이터에 저장합니다. 이 과정에서 선택된 YES24 상품의 숫자 `itemId`를 `identifier:yes24`로 함께 저장합니다.

**YES24 Library Status**는 해당 식별자를 이용해 YES24의 공개 베스트셀러·스테디셀러 목록 및 월별 이력과 로컬에서 대조한 뒤 사용자 정의 컬럼에 현재 상태와 순위 기록을 씁니다.

## 자동 연동 흐름

```text
사용자가 Metadata Source 실행
→ YES24 후보 검색
→ 원하는 판본 선택
→ 메타데이터 저장
→ identifier:yes24 저장
→ Calibre identifiers 변경 이벤트 발생
→ Library Status가 해당 책을 자동 큐에 추가
→ 메모리의 YES24 current snapshot과 로컬 대조
→ history.sqlite3의 완료 월 이력 병합
→ YES24 사용자 정의 컬럼 기록
```

Library Status는 자동 연동 시 YES24 itemId를 우선 사용하고 ISBN13을 보조 식별자로 사용합니다. 자동 worker가 실행되는 동안 식별자가 바뀌었는지도 종료 시 다시 확인합니다.

## 왜 두 플러그인을 한 저장소에서 관리하는가

두 ZIP은 Calibre에서는 별도 플러그인이지만 사용자 관점에서는 하나의 작업 흐름을 구성합니다. Metadata Source가 안정적인 YES24 식별자를 만들고 Library Status가 그 식별자를 후속 데이터 갱신에 사용하므로, 설치 문서·호환성·릴리스 노트를 한 저장소에서 함께 관리하는 편이 관계를 명확히 설명할 수 있습니다.

## 독립 사용

Metadata Source는 Library Status 없이도 정상적으로 사용할 수 있습니다.

Library Status도 YES24 itemId 또는 ISBN13이 이미 라이브러리에 존재하는 책에는 수동 갱신을 사용할 수 있습니다. 다만 Metadata Source와 함께 사용할 때 `identifier:yes24`가 자동으로 유지되므로 가장 안정적인 자동 연동 경로가 됩니다.

## 사용자 정의 컬럼

Library Status는 다음 lookup key를 사용합니다.

| lookup key | 의미 |
| --- | --- |
| `#yes24_status` | 현재 확인된 YES24 상태 |
| `#yes24_rank_detail` | 현재 목록별 순위 요약 |
| `#yes24_best_rank` | 현재 + 과거 이력의 최고 순위 |
| `#yes24_best_record` | 최고 기록의 종류·기간·순위 |
| `#yes24_years` | 기록이 존재하는 연도 |
| `#yes24_checked` | 자동 경로에서 사용한 current snapshot의 실제 획득 시각 |

## 갱신 시각의 의미

자동 갱신의 `#yes24_checked`는 컬럼을 쓴 시각이 아니라 **해당 판단에 사용한 YES24 current snapshot을 실제로 받은 시각**입니다. 따라서 캐시를 사용한 경우 현재 시각보다 몇 분 이전으로 보일 수 있으며 이는 의도된 데이터 신선도 표시입니다.

수동 `YES24 상태 갱신`은 캐시된 current snapshot이 아니라 live 조회 경로를 유지합니다.
