# Beta Testing Playbook Design

## Brainstorming outcome

The highest-value small Beta readiness improvement is a root-level `BETA_TESTING.md` playbook. The README already lists setup and smoke commands, but beta testers need a single checklist that says what to run, what to verify, how to clean up, and what evidence to report. This targets smoke/main-flow QA without changing product behavior.

## Scope

- Add `BETA_TESTING.md` at the repository root.
- Cover local setup assumptions, backend/frontend verification gates, mock smoke E2E, optional real-LLM smoke, manual main-flow QA, archive/read-only spot checks, cleanup, and bug report evidence.
- Keep commands aligned with current README/project instructions.
- Add a docs regression test that requires the playbook and key checklist terms.

## Non-goals

- Do not change backend or frontend behavior.
- Do not require live backend smoke during unit tests.
- Do not add new external tooling.

## Testing

- Add a failing docs test that requires `BETA_TESTING.md` and key sections.
- Create the playbook.
- Run the docs test and full backend pytest.
- Run frontend build because this is a release-readiness doc change and the user requested relevant tests/build.
