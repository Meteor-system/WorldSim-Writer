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
  inactive: '沉寂',
  archived: '已归档',
  planted: '已埋下',
  advanced: '推进中',
  partially_resolved: '部分揭晓',
  fully_resolved: '已揭晓',
  resolved: '已揭晓',
  expired: '已放弃',
  abandoned: '已放弃',
  approved: '已写入正史',
  healthy: '健康',
  watch: '观察',
  at_risk: '高风险',
  high: '高',
  medium: '中',
  low: '低',
  stable: '稳定',
  urgent: '紧急',
  draft: '继续创作',
  repair: '修复风险',
  converge: '叙事收束',
  archive: '快照归档',
  protagonist: '主角',
  antagonist: '对手',
  supporting: '配角',
  minor: '次要角色',
  ally: '盟友',
  rival: '竞争者',
  mentor: '导师',
  mutual_suspicion: '相互猜疑',
  uneasy_alliance: '不稳定同盟',
  trusted_ally: '可信盟友',
  public: '公开',
  private: '私下',
  secret: '秘密',
  plot: '情节线索',
  character: '角色线索',
  world: '世界规则',
  theme: '主题线索',
  world_rule_clue: '世界规则线索',
  magic_clue: '魔法线索',
  expand: '扩张',
  organize: '整理',
  pressure: '加压',
  payoff: '兑现',
  endgame: '终局',
  flexible: '可扩展',
  limited: '有限扩张',
  locked: '停止新增',
  close: '收束',
  advance: '推进',
  merge: '合并',
  must_close: '必须收束',
  should_advance: '建议推进',
  can_delay: '可延后',
  can_leave_open: '可留白',
  foreshadow: '伏笔',
  character_goal: '角色目标',
  health_risk: '健康风险',
  updated: '更新',
  created: '创建',
  added: '新增',
  changed: '变化',
};

export const GENRE_LABELS: Record<string, string> = {
  fantasy: '奇幻',
  sci_fi: '科幻',
  modern: '现代都市',
  xianxia: '仙侠',
  weird_fantasy: '诡秘奇幻',
  dark_fantasy: '黑暗奇幻',
  political_fantasy: '政治奇幻',
  xianxia_intrigue: '仙侠 · 权谋/悬疑',
};

export const GENRE_TEMPLATE_OPTIONS = Object.entries(GENRE_LABELS).map(([value, label]) => ({ value, label }));

export function isKnownGenreTemplate(value: string): boolean {
  return value in GENRE_LABELS;
}

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
  return GENRE_LABELS[value] ?? value;
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

export function localizeBackendCopy(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/World Pulse/g, '世界近况')
    .replace(/Narrative Health/g, '叙事健康度')
    .replace(/Open Threads Board/g, '开放线索看板')
    .replace(/World Archive/g, '世界档案')
    .replace(/story arc/g, '故事弧线')
    .replace(/active goals/g, '当前目标')
    .replace(/active goal/g, '当前目标')
    .replace(/canon/g, '正史')
    .replace(/\bwatch\b/g, '观察')
    .replace(/\bdraft\b/g, '继续创作')
    .replace(/\badvance\b/g, '推进')
    .replace(/\bshould_advance\b/g, '建议推进')
    .replace(/\bcan_delay\b/g, '可延后')
    .replace(/\bmust_close\b/g, '必须收束')
    .replace(/\bforeshadow\b/g, '伏笔')
    .replace(/\bcharacter_goal\b/g, '角色目标')
    .replace(/\bhealth_risk\b/g, '健康风险');
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
  return value.replace(/_/g, ' ');
}
