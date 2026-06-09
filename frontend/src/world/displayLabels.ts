const OBJECT_TYPE_LABELS: Record<string, string> = {
  character: '角色',
  foreshadow: '悬念/伏笔',
  chapter: '章节',
  event: '事件',
  world: '世界',
};

const STATUS_LABELS: Record<string, string> = {
  active: '进行中',
  running: '进行中',
  archived: '已归档',
  planted: '已埋下',
  advanced: '推进中',
  partially_resolved: '部分揭晓',
  fully_resolved: '已揭晓',
  resolved: '已揭晓',
  abandoned: '已放弃',
  approved: '已写入正史',
  protagonist: '主角',
  antagonist: '对手',
  supporting: '配角',
  updated: '更新',
  created: '创建',
  changed: '变化',
};

const CHANGE_TYPE_LABELS: Record<string, string> = {
  added: '新增资料',
  removed: '移除资料',
  changed: '资料已更新',
  created: '新增资料',
  updated: '资料已更新',
};

const FIELD_LABELS: Record<string, string> = {
  status: '状态',
  title: '标题',
  name: '名称',
  current_goals: '当前目标',
  public_profile: '公开资料',
  hidden_traits: '隐藏设定',
  description: '描述',
  urgency_level: '紧迫度',
  world_version: '世界进度',
  truth_canon: '正史文本',
  truth_canon_version: '正史修订',
};

const GENRE_LABELS: Record<string, string> = {
  xianxia: '仙侠',
  xianxia_intrigue: '仙侠 · 权谋/悬疑',
  sci_fi: '科幻',
  weird_fantasy: '诡秘奇幻',
};

const TAG_PART_LABELS: Record<string, string> = {
  xianxia: '仙侠',
  intrigue: '权谋/悬疑',
  suspense: '悬疑',
  mystery: '悬疑',
  sci: '科幻',
  fi: '科幻',
  fantasy: '奇幻',
  weird: '诡秘',
};

export function labelObjectType(value: string): string {
  return OBJECT_TYPE_LABELS[value] ?? readableToken(value);
}

export function labelStatus(value: string): string {
  return STATUS_LABELS[value] ?? readableToken(value);
}

export function labelGenre(value: string): string {
  return GENRE_LABELS[value] ?? readableToken(value);
}

export function labelTagName(value: string): string {
  if (GENRE_LABELS[value]) return GENRE_LABELS[value];
  if (!value.includes('_')) return value;
  const labels = value.split('_').filter(Boolean).map((part) => TAG_PART_LABELS[part] ?? readableToken(part));
  return Array.from(new Set(labels)).join(' · ');
}

export function labelEventType(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized === 'world_created') return '世界已创建';
  if (normalized === 'chapter_approved') return '章节写入正史';
  if (normalized === 'character_change') return '角色变化';
  if (normalized === 'foreshadow_change') return '悬念/伏笔变化';
  if (normalized === 'world_version_increment') return '世界进度更新';
  return readableToken(value);
}

export function labelWorldVersion(version: number | string | null | undefined): string {
  return `第 ${version ?? '?'} 版`;
}

export function labelChangeType(value: string): string {
  return CHANGE_TYPE_LABELS[value] ?? readableToken(value);
}

export function labelFieldName(value: string): string {
  return FIELD_LABELS[value] ?? readableToken(value);
}

export function labelSnapshotOption(id: number, version: number, label?: string | null): string {
  void id;
  return `${label?.trim() || '未命名保存点'} · ${labelWorldVersion(version)}`;
}

export function localizeSubtitle(subtitle: string): string {
  return subtitle
    .split(' · ')
    .map((part) => localizeSubtitlePart(part.trim()))
    .filter(Boolean)
    .join(' · ');
}

function localizeSubtitlePart(part: string): string {
  if (/^urgency\s+\d+$/i.test(part)) return `紧迫度 ${part.match(/\d+/)?.[0]}`;
  if (/^world\s+v\d+$/i.test(part)) return `世界${labelWorldVersion(part.match(/\d+/)?.[0])}`;
  if (OBJECT_TYPE_LABELS[part.toLowerCase()]) return labelObjectType(part.toLowerCase());
  if (STATUS_LABELS[part.toLowerCase()]) return labelStatus(part.toLowerCase());
  if (GENRE_LABELS[part]) return labelGenre(part);
  if (part.includes('_')) return readableToken(part);
  return part;
}

function readableToken(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
