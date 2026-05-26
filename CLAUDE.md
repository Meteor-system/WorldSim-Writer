# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current repository state

This repository is currently in the requirements and architecture design phase. The only project artifact is [WorldSim-Writer.md](WorldSim-Writer.md), a detailed Chinese product and technical specification for the WorldSim-Writer platform.

There is not yet any runnable application code, package manifest, database schema, tests, deployment config, or executable prototype in this repository. Treat described capabilities as design targets, not implemented behavior.

## Commands

No build, lint, test, or run commands exist yet because the repository does not contain source code or project manifests.

When implementation begins, add the actual commands here after the relevant tooling is committed. The architecture spec currently recommends:

- Backend: Python FastAPI monolith
- Database: PostgreSQL
- Frontend: React + TailwindCSS
- MVP integration: local Obsidian export

Do not invent commands before the corresponding files exist.

## Source of truth

Use [WorldSim-Writer.md](WorldSim-Writer.md) as the authoritative product and architecture specification. It defines:

- Current project status and MVP boundaries
- Product goals and target users
- Domain modules and state machines
- Recommended technical architecture
- API contract drafts
- Data model drafts
- Security, testing, and acceptance criteria
- Risk register and follow-up recommendations

## Product architecture overview

WorldSim-Writer is intended to be a long-form narrative operating system, not a one-shot text generator. Its core loop is:

1. Create or select a world and freeze its Truth Canon.
2. Manage characters, factions, map state, foreshadowing, and history.
3. Generate chapter drafts through a Showrunner -> Director -> Critics pipeline.
4. Let the user revise, approve, or reject the draft.
5. Only after user approval, commit the chapter and structured world-state events.
6. Continue simulation and generation from the updated world state.

The design principle is state-driven generation: world state, character state, event history, and the Truth Canon constrain chapter output.

## MVP scope

The MVP should focus on the stable long-form writing loop:

- Genre template creation and Truth Canon freeze
- Basic character and relationship management
- Three-stage chapter generation: Showrunner, Director, Critics
- Review workflow where approved chapters update state
- Foreshadow ledger
- Basic Obsidian export
- Single-app consistency around world state, event logs, and projections

The MVP explicitly should not include:

- 3D planet map or advanced map rendering
- Voice control
- Multi-user collaborative review
- Template marketplace or plugin ecosystem
- Complex branch-world management beyond basic snapshot design reservations
- Premature microservice, graph database, or vector database architecture

## Recommended implementation architecture

The spec recommends starting with a simple monolith:

- FastAPI as the only backend application
- PostgreSQL as the primary database
- Lightweight in-process or simple background tasks for MVP simulations
- React + TailwindCSS frontend
- Static or 2D map UI for MVP
- Code-level domain separation without independent service deployment

The backend should preserve these domain boundaries in code even inside a monolith:

- `world`: world setup, genre templates, Truth Canon, lifecycle status
- `character`: characters, relationships, factions, destiny markers
- `simulation`: map tiles, resources, damage, monthly simulation
- `narrative`: chapter planning, drafting, review, approval workflows
- `memory`: short/mid/long-term summaries, retrieval context, compression
- `integration`: Obsidian export, sync logs, external assets

Only introduce Redis, Neo4j, standalone vector stores, service splits, or complex monitoring after a real bottleneck exists.

## State and consistency model

The system’s formal source of truth should be:

- Event Log: append-only structured records of accepted world changes
- Current State Projection: query-optimized state derived from event logs
- Draft Cache: temporary review-state chapters and candidate events that do not modify the formal world

Important rules from the spec:

- Chapter draft generation must not write formal world state.
- Rewrites and polishing only update draft/cache data.
- Chapter approval must be a single atomic transaction.
- Approval must write the final chapter, structured events, projections, memory/index markers, and version changes together.
- Every formal write needs version checks, idempotency via commit IDs, audit metadata, and rollback via new events rather than history deletion.
- If a draft’s `base_world_version` no longer matches the current world version, force a realignment flow instead of overwriting current state.

## Key domain objects

The spec’s first implementation should stabilize these objects before expanding feature depth:

- World
- Truth Canon
- Character
- Faction
- Tile
- Chapter
- Chapter Draft
- Foreshadow
- Event Log
- Snapshot
- Sync Log
- Tags and object tag mappings

Prefer consistent English identifiers in code and APIs, such as `world_id`, `chapter_id`, `event_id`, `world_version`, `source_world_version`, and `base_world_version`.

## API design direction

The spec drafts REST-style endpoints around world-scoped resources. Core endpoint groups include:

- World management: create world, fetch world overview, update config, freeze canon
- Character and faction management
- Chapter draft, rewrite, polish, approve, and reject workflows
- Foreshadow ledger and event history
- Snapshots and branch creation
- Monthly simulation
- Obsidian export and sync logs
- Global search, bulk actions, and repair tools

Response shape should follow the documented `success`, `data`, `meta`, `error_code`, `message`, `details`, and `retryable` conventions.

## Frontend product surfaces

The intended MVP UI should prioritize workflow screens over visual effects:

- Onboarding page: genre selection, rhythm selection, sample world entry, first chapter generation
- World home: progress, recent events, risks, pending foreshadows
- Studio / creation desk: chapter task input, context summary, drafts, diffs, review hints, approve/reject
- Character library: profiles, relationships, destiny flags, history
- Basic map page: map overview, tile detail, risk areas, filters
- Foreshadow ledger: status, urgency, source chapters, related characters
- History library: chapter timeline, snapshots, branch records
- Tools workspace: search, batch edits, repair, export, sync logs

## Security and safety constraints

Implement security from the first runnable version rather than deferring it:

- No anonymous formal writes.
- Use at least `owner`, `editor`, and `viewer` roles for MVP.
- Store model keys, sync tokens, and database credentials outside business tables and outside the repo.
- Frontend must never receive high-privilege model API keys.
- External model output must be validated before any state write.
- Obsidian export must be limited to explicitly configured allowed directories and safe file types.
- Sync conflicts must never auto-overwrite either side.
- Audit login, permission changes, chapter approvals, manual corrections, rollback, delete, sync config changes, and exports.

## Testing and acceptance direction

Once code exists, tests should cover the critical stateful writing loop rather than only isolated helpers:

- Unit tests for rule validation, state transitions, foreshadow updates, snapshots, and pure domain logic
- Integration tests for chapter generation -> review -> approval -> event log -> projection updates
- Regression/evaluation samples for prompt, memory retrieval, event rules, consistency, OOC risk, and foreshadow recovery
- Acceptance gates tied to the spec: consistency pass rate, foreshadow traceability, character-state traceability, chapter usability after light editing, and model cost visibility

## Working guidance for future Claude instances

- Read [WorldSim-Writer.md](WorldSim-Writer.md) before making product or architecture decisions.
- Keep recommendations scoped to the MVP unless the user explicitly asks about P1/P2 or final-state capabilities.
- Prefer tightening specs, schemas, contracts, state machines, and acceptance criteria before adding new feature ideas.
- Do not describe the system as implemented until source code and verification exist.
- When adding the first real code, update this file with the actual commands and source layout.