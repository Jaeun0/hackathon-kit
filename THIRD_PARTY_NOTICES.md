# 사용한 오픈소스

이 저장소의 문장과 코드는 대부분 새로 썼다. 아래 오픈소스에서 생각을 빌리거나 코드를 고쳐 썼고, 라이선스 원문은 `licenses/`에 있다.

| 출처 | 라이선스 | 이 저장소의 어디 | 방식 |
| --- | --- | --- | --- |
| [anthropics/skills](https://github.com/anthropics/skills) `webapp-testing/scripts/with_server.py` | Apache-2.0 | `skills/kit-tools/scripts/run_e2e.py`의 서버 기동·포트 대기·정리 부분 | 코드를 고쳐 씀 (파일 머리에 출처 표기) |
| [obra/superpowers](https://github.com/obra/superpowers) `verification-before-completion` | MIT | AGENTS.md 4번, kit-verify, kit-final | 원칙 발췌·한국어로 새로 씀 |
| obra/superpowers `test-driven-development`, `systematic-debugging` | MIT | kit-rule | 원칙 발췌·한국어로 새로 씀 |
| obra/superpowers `writing-plans` (Review Focus) | MIT | kit-trapmap "명세가 말하지 않는 입력 5개" | 원칙 발췌·한국어로 새로 씀 |
| [github/spec-kit](https://github.com/github/spec-kit) `clarify`, `analyze`, bug 확장 | MIT | kit-trapmap 2차 질문 규칙, kit-docsync 대조 항목, kit-rule 진단→수정→재확인 | 원칙 발췌·한국어로 새로 씀 |
| [openai/skills](https://github.com/openai/skills) `define-goal`, `skill-creator` | Apache-2.0 | kit-plan 완료 조건, 스킬 작성 방식 | 원칙 참고 |
| [Agent Skills 표준](https://agentskills.io/specification) | — | 모든 SKILL.md의 형식 | 형식 준수 |

- obra/superpowers: Copyright (c) 2025 Jesse Vincent
- github/spec-kit: Copyright GitHub, Inc.
- anthropics/skills, openai/skills: 각 저장소의 Apache License 2.0
