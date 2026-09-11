# YES24 Metadata Source for Calibre 0.4.13

0.4.13은 **보조 저자 역할 판별**을 좁게 수정한 버전입니다.

0.4.13 fixes a narrow secondary-contributor role-matching issue while preserving the existing conservative edition-safety policy.

## 핵심 수정 / Key fix

실사용 사례 `너의 색` / `사노 아키라 & 『너의 색』제작위원회` / ISBN `9791194293316`에서 YES24 exact-ISBN 상품이 존재하는데도 0.4.12가 해당 상품을 `bibliographically different item`으로 오판했습니다.

YES24 저자 문자열은 `사노 아키라 저 / 『너의 색』 제작위원회 원저 / 부윤아 역` 형태입니다. 0.4.12는 Calibre 입력의 두 번째 이후 저자를 번역자 비교 대상으로 사용해 `원저` 제작위원회를 실제 번역자와 비교했습니다.

0.4.13은 추가 입력 저자가 YES24의 비번역 저자 목록과 이미 호환되면 번역자 비교 대상에서 제외합니다. 일반 저자와 일치하지 않는 추가 저자만 `역` / `옮김` / `번역` contributor와 비교합니다.

When an additional Calibre author already matches a YES24 non-translator contributor such as an original-work contributor or co-author, 0.4.13 no longer treats that name as a translator candidate. Translator checks remain active for unmatched additional names.

## 표적 회귀 / Targeted regression

- `너의 색` + `사노 아키라 & 『너의 색』제작위원회` + ISBN `9791194293316` → exact ISBN direct ACCEPT
- `페스트` + `알베르 카뮈 & 최윤주` + ISBN `9788932925936` → translator match ACCEPT
- `페스트` + `알베르 카뮈 & 다른 번역자` + same ISBN → REJECT

## 회귀 감사 / Regression audits

### normal ISBN 100권

```text
accepted             : 97
rejected             : 3
error                : 0
accepted/library ISBN: 97
accepted/other ISBN  : 0
```

### no-ISBN 100권

```text
accepted             : 94
rejected             : 6
error                : 0
accepted/library ISBN: 39
accepted/other ISBN  : 53
```

### wrong-ISBN 20권

```text
accepted             : 19
rejected             : 1
error                : 0
accepted/library ISBN: 9
accepted/other ISBN  : 9
```

0.4.12와 비교해 실행시간을 제외한 검사 결과 필드는 세 감사 세트 모두 동일했습니다. wrong-ISBN 20권의 19건은 conflict→fallback으로 복구되고 1건의 miss는 계속 거절됩니다.

Across the three regression sets, all checked non-timing fields stayed unchanged from 0.4.12. Nineteen wrong-ISBN conflicts were recovered through title/author fallback; the one ISBN miss remained safely rejected.

## 안전성 원칙 / Safety principle

> 잘못된 메타데이터를 확신해서 적용하는 것보다 결과를 비워 두는 편이 낫습니다.
>
> A missing result is better than confidently applying the wrong book or edition.

0.4.13은 임계값을 낮추지 않습니다. 이번 수정은 contributor 역할 분류만 더 정확하게 합니다.
