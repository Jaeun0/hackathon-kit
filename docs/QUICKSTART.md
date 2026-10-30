# QUICKSTART

시험이나 리허설에서 이 키트를 쓰는 순서. 자세한 표와 질문 목록은 `cat ~/kit/PROMPTS.md`.

## 0. 시작 직후 (0–7%)

1. README를 열고, 환경 점검 명령(check_setup 등)이 있으면 먼저 실행한다.
2. 터미널 1에서 두 줄 (아직 codex를 켜지 않는다):
   ```bash
   git clone https://github.com/Jaeun0/hackathon-kit ~/kit
   python3 ~/kit/install.py --workspace .
   ```
   - `python3`가 없으면 `python`.
   - **Windows cmd**에서는 `~`가 홈으로 해석되지 않는다. `"%USERPROFILE%\kit"`를 쓴다.
3. 설치가 끝나면 ★ 질문 3개가 화면에 나온다. 담당자에게 하나씩 보낸다.
4. 터미널 1에서 `codex` → `/status`(fast 켜짐 확인) → `/model` → `$kit`까지만 쳐서 자동완성 확인 → `$kit-start`.
   - 자동완성에 없으면: codex 종료 → `python3 ~/kit/install.py --workspace . --skills-dir .agents/skills` → 다시 codex.
   - 그래도 없으면 고치지 말고 PROMPTS.md 긴 프롬프트.

## 1. 진행 (터미널 1)

`$kit-start` → `$kit-trapmap` → `$kit-plan` → `$kit-rule T○` 반복 → `$kit-verify` → `$kit-docsync` (동결) → `$kit-essay` → `$kit-final` → 제출

## 2. 선생님 (터미널 2, `$kit-trapmap` 보고 직후부터)

1. 터미널 `+`로 새 탭 → 과제 폴더인지 확인 → `codex` → `$kit-quiz`
2. 처음에는 `수업`(과제 한 장 → 함정 → 처리 흐름 순서로 가르침). 모르면 `쉽게`, 더 알고 싶으면 `왜`.
3. `$kit-rule` 커밋이 생길 때마다 `새로`(방금 바뀐 것 수업), 시간이 남으면 `다음`·`묶음`(예상 문제+모범 답).
4. 동결 뒤 `정리`(최신 코드에 다시 맞춘 한 장 요약) → `시험` 2~3문제.
5. 터미널 2는 읽기 전용이다. 고칠 게 보이면 터미널 1에 지시한다.

## 3. 웹 과제면 (터미널 3)

터미널 1의 `$kit-plan` 보고에 나온 서버 명령을 터미널 3에서 실행하고 닫지 않는다. 왼쪽 Browser 도구 PORT·URL로 확인. 코드를 고친 뒤에는 `Ctrl+C` → 다시 실행 → 원형 화살표.

## 4. 시간 관문

| 관문 | 180분 | 120분 |
| --- | --- | --- |
| 뼈대 커밋 | 40 | 26 |
| 규칙 끝 | 115 | 77 |
| 검증 끝 | 140 | 94 |
| **기능 동결** | **150** | **100** |
| **제출 시작** | **170** | **113** |

## 비상 경로

| 문제 | 할 일 |
| --- | --- |
| clone 실패 | 키트 없이 진행 (외운 순서대로) |
| 스킬이 안 보임 | PROMPTS.md 긴 프롬프트 |
| 스크립트 오류 | AI에게 같은 일을 짧은 코드로 하게 하고 넘어감 |
| 같은 문제 10분 | 기본 해석으로 확정, 다음 항목 |
| 관문에 늦음 | PROMPTS.md "늦었을 때 한 줄 지시" |
