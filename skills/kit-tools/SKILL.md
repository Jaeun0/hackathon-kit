---
name: kit-tools
description: 다른 kit-* 스킬이 부르는 공용 스크립트 모음이다. 데이터 요약, 지정 명령 종단 실행, 자가 홀드아웃 생성, 범주별 분할, 제출 점검이 필요할 때 쓴다. 과제 코드를 대신 짜는 데는 쓰지 않는다.
---

# kit-tools: 공용 스크립트

이 SKILL.md가 있는 폴더의 `scripts/`에 있다. 모두 파이썬 표준 라이브러리만 쓴다.
**본문을 읽지 말고 `--help`부터 실행해 사용법만 확인한다.** (컨텍스트 절약)

| 스크립트 | 언제 | 예 |
| --- | --- | --- |
| profile.py | 과제 시작 직후 data/ 요약 | `python scripts/profile.py data` |
| run_e2e.py | 뼈대·검증·최종 점검에서 지정 명령으로 끝까지 실행 | `python scripts/run_e2e.py cli --cmd "..." --out out/x.csv` · `python scripts/run_e2e.py server --cmd "..." --path "/api/x?date={key}" --keys-url /api/dates` |
| make_holdout.py | 날짜를 옮기고 함정 변형을 넣은 자가 홀드아웃 | `python scripts/make_holdout.py data ../holdout/data --config holdout.json` |
| slice_report.py | 결과를 범주·기간별로 나눠 튀는 그룹 찾기 | `python scripts/slice_report.py out/x.csv --by line --by date --metric yield --weight wafers` |
| check_submit.py | 제출 직전: 미커밋·data 변경·문서 TODO·예외 기대 테스트 | `python scripts/check_submit.py --require REPORT.md DECISIONS.md` |

## 규칙
- 스크립트가 실패하면 고치려 하지 말고, 같은 일을 직접 짧은 코드로 한 뒤 "kit 스크립트 실패: 이유"를 보고한다.
- 자가 홀드아웃은 과제 폴더 밖이나 git에 넣지 않는 폴더에 만든다. 원본 data/는 건드리지 않는다.
- 스크립트 출력은 그대로 붙이지 말고 숫자만 요약해 보고한다.
