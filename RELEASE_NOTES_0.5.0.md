# YES24 Metadata Source for Calibre 0.5.0

0.5.0은 **낱권 메타데이터 검색에서 점수순 후보 목록 + 사용자 선택**을 중심으로 동작하는 릴리스입니다.

## 주요 변경

- ISBN이 없는 제목/저자 검색에서 관련 후보를 하나로 합쳐 서지 유사성 점수순으로 최대 10개 반환합니다.
- 1·2위 점수 차가 작다는 이유만으로 검색 전체를 0건 처리하지 않습니다.
- 정확 ISBN이 제목/저자와 호환되면 해당 판본은 한 건으로 직접 반환합니다.
- 저장 ISBN이 다른 책을 가리키거나 YES24에서 찾히지 않는 경우에도 관련 제목/저자 후보를 사용자가 비교할 수 있습니다.
- YES24 storefront의 원래 결과 순서는 서지 점수에 섞지 않고, 점수가 같을 때만 안정적인 tie-break로 사용합니다.
- 특정 종이책/eBook을 점수와 무관하게 앞으로 이동시키는 identify 후처리를 제거했습니다.
- Calibre의 same-source 정렬이 YES24의 점수순 후보를 뒤집지 않도록 `identify_results_keygen()`과 `source_relevance`를 사용합니다.

## 선택한 후보의 표지

identify 단계에서 각 후보 ISBN과 다음 YES24 고해상도 표지 URL을 연결합니다.

```text
https://image.yes24.com/goods/{itemId}/XL
```

사용자가 후보를 선택한 뒤 표지 단계로 이동하면 선택된 후보의 ISBN 캐시를 최우선으로 사용합니다. 따라서 같은 제목 검색에서 여러 권·시즌·판본이 나와도 선택한 책에 맞는 YES24 XL 표지가 따라옵니다.

## 확인 사례

`비밀의 숲 / 이수연`을 ISBN 없이 검색했을 때 다음과 같은 관련 후보들이 Calibre 선택 목록에 노출되는 것을 확인했습니다.

- `비밀의 숲 1`
- `비밀의 숲 2`
- `비밀의 숲 시즌 1 (1)` / `(2)`
- `비밀의 숲 시즌 2 (상)` / `(하)`
- 시즌 세트 후보

서로 다른 후보를 선택했을 때 YES24 플러그인과 별도의 YES24 Cover 플러그인이 동일한 해당 판본 표지를 노출하는 것도 확인했습니다.

## 기존 기능 유지

- title/subtitle-aware matching
- translator/secondary-contributor edition checks
- `원저`/공저 계열을 번역자로 오인하지 않는 역할 처리
- compatible same-work series/description donor
- promotional `소개도서`/`추천도서` series filtering
- conservative `series_index` evidence
- TOC-like Comments rejection
- YES24 high-resolution `/XL` cover

## 알려진 Calibre 동작

Calibre는 같은 메타데이터 소스에서 제목과 저자가 완전히 같은 결과를 병합할 수 있습니다. 따라서 서로 다른 ISBN이나 발행연도를 가진 판본이라도 제목·저자가 완전히 동일하면 일부가 하나로 합쳐져 보일 수 있습니다.

## English summary

0.5.0 changes single-book discovery from a single automatic winner to a ranked list of relevant YES24 candidates. Exact compatible ISBN lookups remain edition-specific. Candidate cover URLs are cached by the selected ISBN so the cover screen follows the edition chosen by the user.
