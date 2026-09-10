# YES24 Metadata Source for Calibre 0.4.12

0.4.12는 실제 사용 중 발견된 **부제 포함 YES24 제목 매칭 누락**을 보수적으로 수정한 버전입니다.

0.4.12 fixes a real-world matching gap where a short Calibre title could fail against a YES24 title that already contains a subtitle.

## 핵심 수정 / Key fix

`질투라는 감옥` / `야마모토 케이`를 ISBN 없이 검색하면 YES24는 정확한 eBook/종이책 후보를 반환했지만, 0.4.11은 후보의 `title` 필드 자체가 `본제목 : 부제` 형태인 경우 본제목을 구조적으로 분리하지 않아 자동 매칭을 거절했습니다.

0.4.12는 **사용자 입력 제목이 비구조화된 경우에만** YES24 후보 제목의 본제목/부제를 보조적으로 분리합니다. 자동 매칭 임계값을 낮추지 않으며, 이미 구조화된 사용자 제목에는 기존 보수적 비교 경로를 유지합니다.

When the user supplies a simple title, 0.4.12 can recognize the primary title inside a YES24 candidate title such as `Primary title : Subtitle`. Existing structured user titles continue to use the conservative 0.4.11 path, and global match thresholds are unchanged.

## 회귀 검증 / Regression validation

### 표적 회귀 / Targeted cases

- `질투라는 감옥` + `야마모토 케이`, no ISBN → 정상 ACCEPT, eBook ISBN `9791193937303`
- 가짜 부제 `질투라는 감옥 : 완전히 다른 부제` → REJECT
- 첫 수정안에서 회귀했던 `화폐전쟁 1~4` → refined patch에서 정상 복구
- `페스트` ISBN miss → 다른 판본 자동 적용 없이 REJECT 유지

### no-ISBN 100권

```text
accepted             : 94
rejected             : 6
error                : 0
accepted/library ISBN: 39
accepted/other ISBN  : 53
```

- TOC-like Comments: 0
- empty Comments: 0
- marketing/recommendation series: 0

### normal ISBN 100권

```text
accepted             : 97
rejected             : 3
error                : 0
accepted/library ISBN: 97
accepted/other ISBN  : 0
```

- miss → accepted: 0
- TOC-like Comments: 0
- marketing/recommendation series: 0

### wrong-ISBN 20권

```text
conflict → accepted  : 19
miss → rejected      : 1
error                : 0
```

19건의 ISBN conflict는 제목/저자 fallback으로 복구했고, YES24가 공급 ISBN 자체를 찾지 못한 1건은 non-exact edition fallback을 거부했습니다.

19 ISBN-conflict cases were safely recovered through title/author fallback. The one ISBN-miss case remained rejected, preserving the conservative edition-safety rule.

## 안전성 원칙 / Safety principle

> 잘못된 메타데이터를 확신해서 적용하는 것보다 결과를 비워 두는 편이 낫습니다.
>
> A missing result is better than confidently applying the wrong book or edition.

0.4.12는 이 원칙을 바꾸지 않습니다. 이번 수정은 후보 제목 구조 인식 범위만 좁게 보강합니다.
