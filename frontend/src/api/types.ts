export type User = { id: number; email: string };
export type AuthResponse = { access_token: string; token_type: string; user: User };

export type Character = {
  id: number;
  name: string;
  role_type: string;
  status: string;
  public_profile: Record<string, unknown>;
  hidden_traits: Record<string, unknown>;
  destiny_flag: string | null;
  current_goals: string[];
};

export type CharacterCreate = {
  name: string;
  role_type: string;
  status?: string;
  public_profile?: Record<string, unknown>;
  hidden_traits?: Record<string, unknown>;
  destiny_flag?: string;
  current_goals?: string[];
  edit_reason?: string;
};

export type CharacterUpdate = {
  name?: string;
  role_type?: string;
  status?: string;
  public_profile?: Record<string, unknown>;
  hidden_traits?: Record<string, unknown>;
  destiny_flag?: string;
  current_goals?: string[];
  edit_reason?: string;
};

export type CharacterRelation = {
  id: number;
  source_character_id: number;
  target_character_id: number;
  relation_type: string;
  intensity: number;
  visibility: string;
};

export type CharacterRelationCreate = {
  source_character_id: number;
  target_character_id: number;
  relation_type: string;
  intensity?: number;
  visibility?: string;
  edit_reason?: string;
};

export type CharacterRelationUpdate = {
  source_character_id?: number;
  target_character_id?: number;
  relation_type?: string;
  intensity?: number;
  visibility?: string;
  edit_reason?: string;
};

export type ForeshadowStatus = 'planted' | 'advanced' | 'resolved' | 'expired';

export type Foreshadow = {
  id: number;
  source_chapter_id: number | null;
  title: string;
  description: string;
  foreshadow_type: string;
  status: ForeshadowStatus;
  urgency_level: number;
  related_character_ids: number[];
  expected_resolution_window: string | null;
};

export type ForeshadowCreate = {
  source_chapter_id?: number;
  title: string;
  description: string;
  foreshadow_type: string;
  status?: ForeshadowStatus;
  urgency_level?: number;
  related_character_ids?: number[];
  expected_resolution_window?: string;
  edit_reason?: string;
};

export type ForeshadowUpdate = {
  source_chapter_id?: number;
  title?: string;
  description?: string;
  foreshadow_type?: string;
  status?: ForeshadowStatus;
  urgency_level?: number;
  related_character_ids?: number[];
  expected_resolution_window?: string;
  edit_reason?: string;
};

export type ForeshadowEvent = {
  event_type: ForeshadowStatus;
  chapter_id: number | null;
  chapter_title: string | null;
  note: string | null;
  created_at: string;
};

export type RelatedCharacterBrief = {
  id: number;
  name: string;
  role_type: string;
};

export type ForeshadowPressureLevel = 'medium' | 'high' | 'critical' | 'resolved' | 'expired';

export type ForeshadowLedgerSummary = {
  total: number;
  open_count: number;
  planted_count: number;
  advanced_count: number;
  resolved_count: number;
  expired_count: number;
  high_urgency_count: number;
  stale_count: number;
  overdue_count: number;
};

export type ForeshadowLedgerEntry = {
  foreshadow: Foreshadow;
  status_group: ForeshadowStatus;
  is_open: boolean;
  is_high_urgency: boolean;
  is_stale: boolean;
  is_overdue: boolean;
  chapters_since_planted: number;
  pressure_level: ForeshadowPressureLevel;
  pressure_reasons: string[];
  related_characters: RelatedCharacterBrief[];
  recent_events: ForeshadowEvent[];
};

export type ForeshadowLedgerResponse = {
  world_id: number;
  world_version: number;
  summary: ForeshadowLedgerSummary;
  groups: Record<ForeshadowStatus, ForeshadowLedgerEntry[]>;
  high_pressure: ForeshadowLedgerEntry[];
};

export type StaleForeshadow = {
  foreshadow: Foreshadow;
  chapters_since_planted: number;
  alert_level: 'warning' | 'critical';
};

export type StarterCharacterCreate = {
  name: string;
  role_type: string;
  status?: string;
  public_profile?: Record<string, unknown>;
  hidden_traits?: Record<string, unknown>;
  destiny_flag?: string;
  current_goals?: string[];
};

export type StarterRelationCreate = {
  source_index: number;
  target_index: number;
  relation_type: string;
  intensity?: number;
  visibility?: string;
};

export type StarterForeshadowCreate = {
  title: string;
  description: string;
  foreshadow_type: string;
  status?: string;
  urgency_level?: number;
  related_character_indexes?: number[];
  expected_resolution_window?: string;
};

export type StarterAssetsCreate = {
  characters: StarterCharacterCreate[];
  relations?: StarterRelationCreate[];
  foreshadows?: StarterForeshadowCreate[];
};

export type WorldCreateRequest = {
  title: string;
  genre_template: string;
  truth_canon: string;
  tone_profile?: Record<string, unknown>;
  starter_assets: StarterAssetsCreate;
};

export type WorldSeedSummary = {
  key: string;
  label: string;
  genre_template: string;
  hook: string;
  tension_profile: string[];
  starter_summary: Record<string, unknown>;
};

export type WorldSeedDetail = WorldSeedSummary & {
  payload: WorldCreateRequest;
};

export type WorldSeedListResponse = {
  seeds: WorldSeedSummary[];
};

export type EventLog = {
  id: number;
  world_id: number;
  chapter_id: number | null;
  event_type: string;
  source_type: string;
  commit_id: string;
  payload: Record<string, unknown>;
  world_version_before: number;
  world_version_after: number;
  created_at: string;
};

export type EventLogSummary = {
  total: number;
  event_type_counts: Record<string, number>;
  latest_world_version: number;
};

export type EventLogListResponse = {
  items: EventLog[];
  total: number;
  limit: number;
  offset: number;
  summary: EventLogSummary;
};

export type WorldSearchResult = {
  object_type: string;
  object_id: number | null;
  title: string;
  subtitle: string;
  snippet: string;
  metadata: Record<string, unknown>;
};

export type WorldSearchResponse = {
  world_id: number;
  query: string;
  object_type_counts: Record<string, number>;
  results: WorldSearchResult[];
};

export type TagResponse = {
  id: number;
  world_id: number;
  name: string;
  slug: string;
  color: string | null;
  created_at: string;
};

export type TagUpdateRequest = {
  name?: string;
  color?: string | null;
};

export type TagMergeRequest = {
  target_tag_id: number;
};

export type TagMergeResponse = {
  world_id: number;
  source_tag_id: number;
  target_tag_id: number;
  moved_count: number;
  already_assigned_count: number;
  deleted_source_tag: boolean;
};

export type TagSummaryResponse = TagResponse & {
  assignment_count: number;
  object_type_counts: Record<string, number>;
};

export type TaggedObjectSummary = {
  object_type: string;
  object_id: number;
  title: string;
  subtitle: string;
  snippet: string;
  metadata: Record<string, unknown>;
};

export type ObjectTagResponse = {
  id: number;
  world_id: number;
  tag_id: number;
  object_type: string;
  object_id: number;
  created_at: string;
};

export type ObjectTagBulkAssignResponse = {
  world_id: number;
  tag_id: number;
  object_type: string;
  requested_count: number;
  assigned_count: number;
  already_assigned_count: number;
  assigned_object_ids: number[];
  already_assigned_object_ids: number[];
};

export type TagListResponse = {
  world_id: number;
  tags: TagSummaryResponse[];
};

export type TagDetailResponse = {
  tag: TagSummaryResponse;
  objects: TaggedObjectSummary[];
};

export type StoryArcChapter = {
  chapter_number: number;
  title: string;
  summary: string;
  core_conflict: string;
  pov_suggestion: string;
  foreshadow_hints: string[];
};

export type StoryArcResponse = {
  world_id: number;
  story_arc: StoryArcChapter[];
};

export type WorldOverview = {
  id: number;
  title: string;
  genre_template: string;
  truth_canon: string;
  truth_canon_version: number;
  world_version: number;
  status: string;
  tone_profile: Record<string, unknown>;
  current_characters: Character[];
  current_foreshadows: Foreshadow[];
  current_relations: CharacterRelation[];
  characters: Character[];
  relations: CharacterRelation[];
  foreshadows: Foreshadow[];
  recent_events: EventLog[];
  story_arc: StoryArcChapter[];
  approved_chapter_count: number;
};

export type BeatCard = {
  beat_id: string;
  summary: string;
  pov_character: string | null;
  location: string | null;
  emotional_arc: string;
  key_dialogue_hints: string[];
};

export type ChapterExecutionContext = {
  source: 'next_chapter_prep' | 'manual';
  source_world_version: number;
  next_chapter_number: number | null;
  goal: string;
  recommended_pov: { character_id: number | null; name: string | null };
  source_signals: string[];
  priority_characters: NextChapterPrepCharacter[];
  priority_foreshadows: NextChapterPrepForeshadow[];
  progression_hints: ChapterProgressionHint[];
  continuity_warnings: NextChapterPrepWarning[];
  recent_events: Array<Omit<NextChapterPrepEvent, 'payload'>>;
};

export type StudioLaunchContext = {
  initialChapterGoal?: string;
  executionContext?: ChapterExecutionContext;
};

export type ChapterPipelineResponse = {
  id: number;
  world_id: number;
  title: string;
  status: string;
  draft_version: number;
  approved_version: number | null;
  base_world_version: number;
  approved_content: string | null;
  chapter_goal: string | null;
  outline_beats: BeatCard[];
  outline_context: Record<string, unknown>;
  critique_report: Record<string, unknown>;
  execution_context: ChapterExecutionContext | null;
};

export type OutlineResponse = {
  chapter_id: number;
  outline_beats: BeatCard[];
  outline_context: Record<string, unknown>;
  status: string;
};

export type CritiqueIssue = {
  category: string;
  severity: string;
  message: string;
};

export type CritiqueReport = {
  score: number;
  issues: CritiqueIssue[];
  suggestions: string[];
  consistency_check: Record<string, unknown>;
};

export type CriticIssue = {
  severity: 'low' | 'medium' | 'high';
  dimension: string;
  message: string;
  paragraph_index: number | null;
  suggested_action: string | null;
};

export type CriticDimension = {
  score: number;
  summary: string;
  issues: CriticIssue[];
  suggestions: string[];
};

export type CriticReportResponse = {
  chapter_id: number;
  draft_version: number;
  current_draft_version: number;
  is_stale: boolean;
  overall_score: number;
  summary: string;
  dimensions: Record<string, CriticDimension>;
  issues: CriticIssue[];
  suggestions: string[];
  created_at: string;
};

export type CharacterPresenceLevel = 'absent' | 'mentioned' | 'supporting' | 'major';
export type CharacterArcStage = 'setup' | 'pressure' | 'choice' | 'consequence' | 'growth' | 'regression' | 'resolution' | 'unknown';
export type ContinuityRisk = 'none' | 'low' | 'medium' | 'high';
export type ProgressionHintType = 'character' | 'relationship' | 'foreshadow' | 'plot';
export type ProgressionPriority = 'low' | 'medium' | 'high';

export type CharacterArcEntry = {
  character_id: number;
  name: string;
  role_type: string | null;
  current_status: string | null;
  current_goals: string[];
  presence_level: CharacterPresenceLevel;
  arc_stage: CharacterArcStage;
  chapter_function: string;
  observed_shift: string;
  proposed_state_change: Record<string, unknown> | null;
  continuity_risk: ContinuityRisk;
  risk_reason: string | null;
  suggested_revision: string | null;
  next_chapter_setup: string | null;
};

export type RelationshipProgressionNote = {
  source_character_id: number;
  target_character_id: number;
  source_name: string;
  target_name: string;
  relation_type: string;
  current_intensity: number | null;
  visibility: string | null;
  chapter_shift: string;
  progression_hint: string;
  risk_level: ContinuityRisk;
  risk_reason: string | null;
};

export type ChapterProgressionHint = {
  hint_type: ProgressionHintType;
  priority: ProgressionPriority;
  title: string;
  rationale: string;
  suggested_next_beat: string;
  related_character_ids: number[];
  related_foreshadow_ids: number[];
  can_seed_next_chapter_goal: boolean;
};

export type CharacterArcReportResponse = {
  chapter_id: number;
  draft_version: number;
  current_draft_version: number;
  is_stale: boolean;
  summary: string;
  character_arcs: CharacterArcEntry[];
  relationship_notes: RelationshipProgressionNote[];
  progression_hints: ChapterProgressionHint[];
  created_at: string;
};

export type ChapterHistoryItem = {
  id: number;
  title: string;
  status: string;
  approved_version: number;
  base_world_version: number;
  world_version_after: number;
  approved_excerpt: string;
  event_count: number;
  character_change_count: number;
  foreshadow_change_count: number;
};

export type ChapterHistoryResponse = {
  world_id: number;
  chapters: ChapterHistoryItem[];
};

export type ChapterHistoryEvent = {
  id: number;
  event_type: string;
  source_type: string;
  world_version_before: number;
  world_version_after: number;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ChapterHistoryChange = {
  event_type: string;
  object_type: string | null;
  object_id: number | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  payload: Record<string, unknown>;
};

export type ChapterHistoryDetailResponse = {
  id: number;
  world_id: number;
  title: string;
  status: string;
  approved_version: number;
  base_world_version: number;
  approved_content: string;
  world_version_before: number;
  world_version_after: number;
  events: ChapterHistoryEvent[];
  character_changes: ChapterHistoryChange[];
  foreshadow_changes: ChapterHistoryChange[];
  critic_summary: string | null;
  character_arc_summary: string | null;
  execution_context: ChapterExecutionContext | null;
};

export type ApprovedChapterHistoryResponse = ChapterHistoryResponse;
export type ApprovedChapterHistoryDetailResponse = ChapterHistoryDetailResponse;

export type NextChapterPrepCharacter = {
  character_id: number;
  name: string;
  role_type: string;
  status: string;
  reason: string;
};

export type NextChapterPrepForeshadow = {
  foreshadow_id: number;
  title: string;
  status: string;
  urgency_level: number;
  reason: string;
};

export type NextChapterPrepWarning = {
  severity: string;
  category: string;
  message: string;
  related_character_ids: number[];
  related_foreshadow_ids: number[];
};

export type NextChapterPrepEvent = {
  id: number;
  event_type: string;
  world_version_before: number;
  world_version_after: number;
  payload: Record<string, unknown>;
  created_at: string;
};

export type NextChapterPrepResponse = {
  world_id: number;
  world_version: number;
  next_chapter_number: number;
  suggested_goal: string;
  recommended_pov_character_id: number | null;
  recommended_pov_character_name: string | null;
  source_signals: string[];
  priority_characters: NextChapterPrepCharacter[];
  priority_foreshadows: NextChapterPrepForeshadow[];
  progression_hints: ChapterProgressionHint[];
  continuity_warnings: NextChapterPrepWarning[];
  recent_events: NextChapterPrepEvent[];
};

export type NarrativeHealthMetric = {
  key: string;
  label: string;
  value: number;
  status: string;
  detail: string;
};

export type NarrativeHealthRisk = {
  severity: string;
  source: string;
  message: string;
  object_type: string | null;
  object_id: number | null;
  object_title: string | null;
  suggested_action: string;
};

export type NarrativeHealthAction = {
  action_key: string;
  label: string;
  detail: string;
};

export type NarrativeHealthResponse = {
  world_id: number;
  world_version: number;
  health_score: number;
  status: 'healthy' | 'watch' | 'at_risk';
  summary: Record<string, unknown>;
  metrics: NarrativeHealthMetric[];
  risks: NarrativeHealthRisk[];
  suggested_actions: NarrativeHealthAction[];
};

export type OpenThreadItem = {
  thread_id: string;
  thread_type: string;
  priority: 'must_close' | 'should_advance' | 'can_delay' | 'can_leave_open';
  pressure_level: string;
  title: string;
  summary: string;
  related_object_type: string | null;
  related_object_id: number | null;
  related_character_ids: number[];
  related_foreshadow_ids: number[];
  suggested_action: string;
  can_seed_next_chapter_goal: boolean;
};

export type OpenThreadsSummary = {
  total_open_threads: number;
  must_close_count: number;
  should_advance_count: number;
  can_delay_count: number;
  can_leave_open_count: number;
  convergence_ratio: number;
  narrative_entropy_level: 'low' | 'medium' | 'high';
  recent_event_count: number;
};

export type OpenThreadsResponse = {
  world_id: number;
  world_version: number;
  summary: OpenThreadsSummary;
  threads: OpenThreadItem[];
  suggested_next_actions: Array<Record<string, unknown>>;
};

export type WorldPulseIndicator = {
  key: string;
  label: string;
  value: string;
  status: string;
  detail: string;
};

export type WorldPulseFocus = {
  focus_key: string;
  priority: string;
  title: string;
  detail: string;
  suggested_action: string;
  related_thread_id: string | null;
};

export type WorldPulseAction = {
  action_key: string;
  label: string;
  detail: string;
  target: string | null;
};

export type WorldPulseResponse = {
  world_id: number;
  world_version: number;
  pulse_status: 'stable' | 'watch' | 'urgent';
  primary_mode: 'draft' | 'repair' | 'converge' | 'archive';
  headline: string;
  indicators: WorldPulseIndicator[];
  focus: WorldPulseFocus[];
  next_actions: WorldPulseAction[];
  source_summary: Record<string, unknown>;
};

export type ArcPlanClosureItem = {
  item_key: string;
  thread_id: string | null;
  treatment: 'close' | 'advance' | 'merge' | 'defer' | 'leave_open';
  priority: string;
  title: string;
  rationale: string;
  suggested_next_step: string;
  related_character_ids: number[];
  related_foreshadow_ids: number[];
};

export type ArcPlanGuidance = {
  guidance_key: string;
  label: string;
  detail: string;
};

export type ArcPlanResponse = {
  world_id: number;
  world_version: number;
  arc_mode: 'expand' | 'organize' | 'pressure' | 'converge' | 'payoff' | 'endgame';
  mode_reason: string;
  expansion_budget: 'open' | 'limited' | 'locked';
  next_chapter_number: number;
  recommended_goal: string;
  closure_items: ArcPlanClosureItem[];
  guidance: ArcPlanGuidance[];
  source_summary: Record<string, unknown>;
};

export type WorldSnapshotSummary = {
  id: number;
  world_id: number;
  world_version: number;
  label: string | null;
  note: string | null;
  created_at: string;
};

export type WorldSnapshotListResponse = {
  world_id: number;
  snapshots: WorldSnapshotSummary[];
};

export type WorldSnapshotPayload = {
  world: Record<string, unknown>;
  characters: unknown[];
  relations: unknown[];
  foreshadows: unknown[];
  approved_chapters: unknown[];
  events: unknown[];
};

export type WorldSnapshotDetailResponse = WorldSnapshotSummary & {
  payload: WorldSnapshotPayload;
};

export type WorldSnapshotCompareChange = {
  object_type: string;
  object_id: number | null;
  change_type: 'added' | 'removed' | 'changed';
  title: string;
  fields_changed: string[];
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
};

export type WorldSnapshotCompareSummary = {
  total_changes: number;
  object_type_counts: Record<string, number>;
};

export type WorldSnapshotCompareResponse = {
  world_id: number;
  base_snapshot: WorldSnapshotSummary;
  target_snapshot: WorldSnapshotSummary;
  summary: WorldSnapshotCompareSummary;
  changes: Record<string, WorldSnapshotCompareChange[]>;
};

export type MarkdownExportFile = {
  path: string;
  content: string;
};

export type WorldMarkdownExportResponse = {
  world_id: number;
  world_version: number;
  generated_at: string;
  archive_filename: string;
  archive_format: string;
  archive_encoding: string;
  archive_base64: string;
  files_are_inline: boolean;
  files: MarkdownExportFile[];
};

export type CritiqueResponse = {
  chapter_id: number;
  critique_report: CritiqueReport;
  status: string;
};

export type DraftResponse = {
  chapter_id: number;
  draft_id: number;
  draft_version: number;
  title: string;
  content: string;
  context_summary: string;
  review_hints: string[];
  proposed_changes: Record<string, unknown>;
  source_world_version: number;
  change_type: string;
  change_summary: string | null;
  parent_draft_version: number | null;
  status?: string;
  approved_content?: string | null;
  rejection_feedback?: string;
  outline_beats?: BeatCard[];
  outline_context?: Record<string, unknown>;
  critique_report?: CritiqueReport;
  execution_context?: ChapterExecutionContext | null;
};

export type ParagraphReviseRequest = {
  paragraph_index: number;
  mode: 'rewrite' | 'polish';
  instruction?: string;
};

export type ReviseDraftRequest = {
  instruction: string;
};

export type DraftDiffLine = {
  type: 'added' | 'removed' | 'unchanged';
  text: string;
};

export type DraftDiffResponse = {
  chapter_id: number;
  from_version: number;
  to_version: number;
  from_content: string;
  to_content: string;
  diff_lines: DraftDiffLine[];
};

export type ApprovalPreviewChange = {
  change_index: number;
  selected_by_default: boolean;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
};

export type ApproveRequest = {
  draft_version?: number;
  selected_character_change_indexes?: number[];
  selected_foreshadow_change_indexes?: number[];
};

export type ConsistencySeverity = 'info' | 'warning' | 'blocking';
export type ConsistencyStatus = 'clear' | 'needs_review' | 'blocked';

export type ConsistencyWarning = {
  severity: ConsistencySeverity;
  category: string;
  message: string;
  object_type: 'character' | 'foreshadow' | 'chapter';
  object_id: number | null;
  change_index: number | null;
  details: Record<string, unknown>;
};

export type ConsistencySummary = {
  status: ConsistencyStatus;
  total: number;
  info_count: number;
  warning_count: number;
  blocking_count: number;
};

export type ApprovalConsistencyResponse = {
  chapter_id: number;
  draft_version: number;
  selected_change_indexes: { characters: number[]; foreshadows: number[] };
  consistency_summary: ConsistencySummary;
  consistency_warnings: ConsistencyWarning[];
};

export type ApprovalPreviewResponse = {
  chapter_id: number;
  draft_version: number;
  source_world_version: number;
  current_world_version: number;
  will_increment_world_version: boolean;
  world_version_before: number;
  world_version_after: number;
  version_conflict: boolean;
  warnings: string[];
  consistency_summary: ConsistencySummary;
  consistency_warnings: ConsistencyWarning[];
  character_changes: Array<ApprovalPreviewChange & { character_id: number; name: string }>;
  foreshadow_changes: Array<ApprovalPreviewChange & { foreshadow_id: number; title: string }>;
};

export type ApprovalReadinessStatus = 'ready' | 'needs_review' | 'blocked';
export type ApprovalReadinessCheckStatus = 'pass' | 'warning' | 'fail';

export type ApprovalReadinessCheck = {
  key: string;
  label: string;
  status: ApprovalReadinessCheckStatus;
  message: string;
  details: Record<string, unknown> | unknown[] | null;
};

export type ApprovalReadinessResponse = {
  chapter_id: number;
  draft_version: number;
  status: ApprovalReadinessStatus;
  summary: string;
  world_version: {
    source_world_version: number;
    current_world_version: number;
    matches: boolean;
  };
  checks: ApprovalReadinessCheck[];
  high_risk_items: Array<{
    source: string;
    severity: string;
    message: string;
    details: Record<string, unknown>;
  }>;
};
