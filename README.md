# hackathon-kit

**과제와 무관한 범용 작업 도구**다. AI 코딩 에이전트(Codex)와 함께 데이터·코드 과제를 풀 때, 사람이 결정하고 AI가 실행·검증하도록 진행 순서를 고정해 둔 지침·스킬·스크립트·템플릿 모음이다. 특정 과제의 데이터, 정답, 도메인 규칙 코드는 들어 있지 않다.

## 무엇이 들어 있나

| 경로 | 무엇 | 누가 언제 읽나 |
| --- | --- | --- |
| `AGENTS.md` | 작업 규칙 12줄 | Codex, 세션 시작 때 자동 |
| `skills/kit-*` | 단계별 스킬 9개 (`$kit-start` … `$kit-final`) | Codex, 부를 때만 |
| `skills/kit-tools/scripts/` | 표준 라이브러리 스크립트 5개 | 스킬이나 내가 실행 |
| `templates/` | PLAN·DECISIONS·REPORT·HANDOFF·ESSAY_CARDS 빈 양식 | Codex와 나 |
| `PROMPTS.md` | 시간표, 담당자 질문, 스킬이 안 보일 때 쓸 긴 프롬프트 | 나 |
| `install.py` | 스킬·AGENTS.md·템플릿 배치 | 시작 직후 한 번 |
| `docs/QUICKSTART.md` | 시험·리허설에서 쓰는 순서 | 나 |
| `tests/`, `fixtures/` | 스크립트 자체 시험과 가짜 데이터 | `python -m unittest` |

## 빠른 사용

```bash
git clone https://github.com/<아이디>/hackathon-kit.git ~/hackathon-kit
python ~/hackathon-kit/install.py --workspace <과제 폴더>     # codex 실행 전에
cd <과제 폴더> && codex                                       # /skills 로 kit-* 확인
```

자세한 순서는 [docs/QUICKSTART.md](docs/QUICKSTART.md).

## 단계와 사람이 개입하는 지점

| 단계 | 스킬 | AI가 하는 일 | **사람이 하는 일** |
| --- | --- | --- | --- |
| 파악 | `$kit-start` → `$kit-trapmap` | 과제 정리, 데이터 프로파일, 함정 지도, 2차 질문 초안 | 담당자 질문 전송·답 기록, 기본 해석 승인 |
| 뼈대 | `$kit-plan` | PLAN, 끝까지 도는 최소 구현, 커밋 | 체크포인트 1: "왜" 질문에 답 |
| 규칙 | `$kit-rule` (반복) | 기대값 테스트 먼저 → 구현 → 전후·대안 숫자 | 체크포인트 2: 1건 따라가기 검산, "왜" 답 |
| 검증 | `$kit-verify` | 독립 재계산, 자가 홀드아웃, 재스캔 | 체크포인트 3: 튀는 그룹 담당자 질문 |
| 정리 | `$kit-docsync` | 문서 정합, 최종 커밋 | 기능 동결 결정 |
| 대비 | `$kit-essay` | 근거 위치 제시·채점만 | **답은 직접 쓴다** |
| 제출 | `$kit-final` | 재실행·점검 숫자 보고 | 94% 시점에 제출 |

원칙: 규칙은 문서대로 / 전체를 멈추지 않는다 / 먼저 끝까지 돌고 그다음 정확하게 / 내 코드 말고 다른 길로 정답 확인 / 결정은 숫자 두 개로 남긴다.

## 스크립트 자체 시험

```bash
python -m unittest -v
```

## 출처와 라이선스

MIT. 참고하거나 고쳐 쓴 오픈소스는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)와 `licenses/`에 있다.
