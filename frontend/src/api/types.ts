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

export type Foreshadow = {
  id: number;
  title: string;
  description: string;
  foreshadow_type: string;
  status: string;
  urgency_level: number;
  related_character_ids: number[];
  expected_resolution_window: string | null;
};

export type EventLog = {
  id: number;
  event_type: string;
  source_type: string;
  commit_id: string;
  payload: Record<string, unknown>;
  world_version_before: number;
  world_version_after: number;
  created_at: string;
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
  characters: Character[];
  relations: Array<Record<string, unknown>>;
  foreshadows: Foreshadow[];
  recent_events: EventLog[];
};

export type DraftResponse = {
  chapter_id: number;
  draft_id: number;
  title: string;
  content: string;
  context_summary: string;
  review_hints: string[];
  proposed_changes: Record<string, unknown>;
  source_world_version: number;
};
