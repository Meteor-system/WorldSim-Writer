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
};

export type ParagraphReviseRequest = {
  paragraph_index: number;
  mode: 'rewrite' | 'polish';
  instruction?: string;
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
  before: Record<string, unknown>;
  after: Record<string, unknown>;
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
  character_changes: Array<ApprovalPreviewChange & { character_id: number; name: string }>;
  foreshadow_changes: Array<ApprovalPreviewChange & { foreshadow_id: number; title: string }>;
};
