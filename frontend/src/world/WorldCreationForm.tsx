import type { FormEvent } from 'react';
import { useRef, useState } from 'react';
import type {
  StarterCharacterCreate,
  StarterForeshadowCreate,
  StarterRelationCreate,
  WorldBriefExpandResponse,
  WorldCreateRequest,
  WorldSeedDetail,
  WorldSeedSummary,
} from '../api/types';
import { clonePreset, GENRE_PRESETS } from './genrePresets';
import { SeedLibraryPanel } from './SeedLibraryPanel';

type Props = {
  creating: boolean;
  onCreate: (payload: WorldCreateRequest) => Promise<void>;
  onCreateSample: () => Promise<void>;
  seeds?: WorldSeedSummary[];
  selectedSeedKey?: string | null;
  seedLoading?: boolean;
  seedError?: string;
  onLoadSeed?: (seedKey: string) => Promise<WorldSeedDetail>;
  onCreateSeed?: (seedKey: string) => Promise<void> | void;
  onExpandBrief?: (data: { brief: string }) => Promise<WorldBriefExpandResponse>;
};

function goalsToText(goals: string[] | undefined): string {
  return goals?.join('、') ?? '';
}

function textToGoals(value: string): string[] {
  return value
    .split(/[、,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function profileText(character: StarterCharacterCreate, key: string): string {
  const value = character.public_profile?.[key];
  return typeof value === 'string' ? value : '';
}

function hiddenText(character: StarterCharacterCreate, key: string): string {
  const value = character.hidden_traits?.[key];
  return typeof value === 'string' ? value : '';
}

function toneText(form: WorldCreateRequest, key: string): string {
  const value = form.tone_profile?.[key];
  return typeof value === 'string' ? value : '';
}

function mapIndexAfterRemoval(index: number, removedIndex: number): number | null {
  if (index === removedIndex) return null;
  if (index > removedIndex) return index - 1;
  return index;
}

export function WorldCreationForm({
  creating,
  onCreate,
  onCreateSample,
  seeds = [],
  selectedSeedKey = null,
  seedLoading = false,
  seedError = '',
  onLoadSeed,
  onCreateSeed,
  onExpandBrief,
}: Props) {
  const [selectedPresetKey, setSelectedPresetKey] = useState(GENRE_PRESETS[0].key);
  const [activeSeedKey, setActiveSeedKey] = useState<string | null>(selectedSeedKey);
  const [form, setForm] = useState<WorldCreateRequest>(() => clonePreset(GENRE_PRESETS[0]));
  const [brief, setBrief] = useState('');
  const [briefLoading, setBriefLoading] = useState(false);
  const [briefError, setBriefError] = useState('');
  const [briefSuccess, setBriefSuccess] = useState('');
  const [briefNotes, setBriefNotes] = useState<Pick<WorldBriefExpandResponse, 'rationale' | 'assumptions' | 'safety_notes'>>({});
  const briefRequestIdRef = useRef(0);

  function selectPreset(key: string) {
    const preset = GENRE_PRESETS.find((item) => item.key === key) ?? GENRE_PRESETS[0];
    setSelectedPresetKey(preset.key);
    setActiveSeedKey(null);
    setForm(clonePreset(preset));
  }

  async function applySeed(seedKey: string) {
    if (!onLoadSeed) return;
    const seed = await onLoadSeed(seedKey);
    setSelectedPresetKey('');
    setActiveSeedKey(seedKey);
    setForm(JSON.parse(JSON.stringify(seed.payload)) as WorldCreateRequest);
  }

  function updateToneField(key: string, value: string) {
    setForm((current) => ({
      ...current,
      tone_profile: { ...(current.tone_profile ?? {}), [key]: value },
    }));
  }

  function updateCharacter(index: number, patch: Partial<StarterCharacterCreate>) {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        characters: current.starter_assets.characters.map((character, characterIndex) =>
          characterIndex === index ? { ...character, ...patch } : character,
        ),
      },
    }));
  }

  function updateCharacterProfile(index: number, key: string, value: string) {
    const character = form.starter_assets.characters[index];
    updateCharacter(index, { public_profile: { ...(character.public_profile ?? {}), [key]: value } });
  }

  function updateCharacterHidden(index: number, key: string, value: string) {
    const character = form.starter_assets.characters[index];
    updateCharacter(index, { hidden_traits: { ...(character.hidden_traits ?? {}), [key]: value } });
  }

  function addCharacter() {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        characters: [
          ...current.starter_assets.characters,
          {
            name: '新角色',
            role_type: 'supporting',
            status: 'active',
            public_profile: { identity: '待设定', skill: '待设定' },
            hidden_traits: { secret: '待揭示秘密' },
            current_goals: ['待设定目标'],
          },
        ],
      },
    }));
  }

  function removeCharacter(index: number) {
    setForm((current) => {
      if (current.starter_assets.characters.length <= 1) return current;
      const relations = (current.starter_assets.relations ?? [])
        .map((relation) => {
          const sourceIndex = mapIndexAfterRemoval(relation.source_index, index);
          const targetIndex = mapIndexAfterRemoval(relation.target_index, index);
          if (sourceIndex === null || targetIndex === null) return null;
          return { ...relation, source_index: sourceIndex, target_index: targetIndex };
        })
        .filter((relation): relation is StarterRelationCreate => relation !== null);
      const foreshadows = (current.starter_assets.foreshadows ?? []).map((foreshadow) => ({
        ...foreshadow,
        related_character_indexes: (foreshadow.related_character_indexes ?? [])
          .map((relatedIndex) => mapIndexAfterRemoval(relatedIndex, index))
          .filter((relatedIndex): relatedIndex is number => relatedIndex !== null),
      }));
      return {
        ...current,
        starter_assets: {
          ...current.starter_assets,
          characters: current.starter_assets.characters.filter((_, characterIndex) => characterIndex !== index),
          relations,
          foreshadows,
        },
      };
    });
  }

  function updateRelation(index: number, patch: Partial<StarterRelationCreate>) {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        relations: (current.starter_assets.relations ?? []).map((relation, relationIndex) =>
          relationIndex === index ? { ...relation, ...patch } : relation,
        ),
      },
    }));
  }

  function addRelation() {
    if (form.starter_assets.characters.length < 2) return;
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        relations: [
          ...(current.starter_assets.relations ?? []),
          { source_index: 0, target_index: 1, relation_type: 'alliance', intensity: 2, visibility: 'public' },
        ],
      },
    }));
  }

  function removeRelation(index: number) {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        relations: (current.starter_assets.relations ?? []).filter((_, relationIndex) => relationIndex !== index),
      },
    }));
  }

  function updateForeshadow(index: number, patch: Partial<StarterForeshadowCreate>) {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        foreshadows: (current.starter_assets.foreshadows ?? []).map((foreshadow, foreshadowIndex) =>
          foreshadowIndex === index ? { ...foreshadow, ...patch } : foreshadow,
        ),
      },
    }));
  }

  function addForeshadow() {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        foreshadows: [
          ...(current.starter_assets.foreshadows ?? []),
          {
            title: '新伏笔',
            description: '描述这个伏笔会如何影响后续章节。',
            foreshadow_type: 'plot_clue',
            status: 'planted',
            urgency_level: 2,
            related_character_indexes: [0],
            expected_resolution_window: '第2-4章',
          },
        ],
      },
    }));
  }

  function removeForeshadow(index: number) {
    setForm((current) => ({
      ...current,
      starter_assets: {
        ...current.starter_assets,
        foreshadows: (current.starter_assets.foreshadows ?? []).filter((_, foreshadowIndex) => foreshadowIndex !== index),
      },
    }));
  }

  function toggleForeshadowCharacter(foreshadowIndex: number, characterIndex: number) {
    const foreshadow = form.starter_assets.foreshadows?.[foreshadowIndex];
    if (!foreshadow) return;
    const current = foreshadow.related_character_indexes ?? [];
    updateForeshadow(foreshadowIndex, {
      related_character_indexes: current.includes(characterIndex)
        ? current.filter((index) => index !== characterIndex)
        : [...current, characterIndex],
    });
  }

  function friendlyBriefError(error: unknown): string {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes('PROTECTED_REFERENCE_TERMS')) return '草稿里可能包含受保护作品的专有名称或设定，请换成更原创的一句话后重试。';
    if (message.includes('brief') || message.includes('too short') || message.includes('String should have at least')) return '请写得再具体一点，比如一句包含主角、世界规则或核心冲突的话。';
    return '草稿生成失败，请稍后重试，或先用模板手动创建。';
  }

  async function submitBriefDraft() {
    if (!onExpandBrief || briefLoading) return;
    const trimmed = brief.trim();
    if (trimmed.length < 6) {
      setBriefError('请写得再具体一点，比如一句包含主角、世界规则或核心冲突的话。');
      setBriefSuccess('');
      setBriefNotes({});
      return;
    }
    const requestId = briefRequestIdRef.current + 1;
    briefRequestIdRef.current = requestId;
    setBriefLoading(true);
    setBriefError('');
    setBriefSuccess('');
    setBriefNotes({});
    try {
      const response = await onExpandBrief({ brief: trimmed });
      if (briefRequestIdRef.current !== requestId) return;
      setSelectedPresetKey('');
      setActiveSeedKey(null);
      setForm(JSON.parse(JSON.stringify(response.payload)) as WorldCreateRequest);
      setBriefNotes({ rationale: response.rationale, assumptions: response.assumptions, safety_notes: response.safety_notes });
      setBriefSuccess('草稿已填入下方表单。请检查标题、设定、角色和伏笔，确认后再创建世界。');
    } catch (error) {
      if (briefRequestIdRef.current !== requestId) return;
      setBriefError(friendlyBriefError(error));
    } finally {
      if (briefRequestIdRef.current === requestId) setBriefLoading(false);
    }
  }

  function cancelBriefDraft() {
    briefRequestIdRef.current += 1;
    setBriefLoading(false);
    setBriefError('');
    setBriefSuccess('已取消生成，可以修改一句话后重新尝试。');
    setBriefNotes({});
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onCreate(form);
  }

  return (
    <form onSubmit={submit} className="motion-page-enter mx-auto max-w-5xl px-6 py-10 text-left" data-testid="world-creation-form">
      <section className="surface-layer rounded-[28px] border border-amber-900/15 bg-amber-100/60 p-5 shadow-sm" data-testid="newcomer-loop-panel">
        <p className="chapter-kicker">3-Minute World Loop</p>
        <h1 className="mt-2 text-3xl font-black text-[#34210f]">3 分钟开始运营你的故事世界</h1>
        <p className="manuscript mt-3 text-sm text-[#5e3b1c]">
          不需要先填完后台表单：先选一个高张力世界胚胎，生成第一章，写入正史，再查看角色、悬念/伏笔和世界进度如何变化。
        </p>
        <ol className="mt-4 grid gap-3 text-sm md:grid-cols-4">
          {['选世界胚胎', '生成第一章', '写入正史', '查看世界变化'].map((step, index) => (
            <li key={step} className="rounded-2xl bg-white/60 p-3 font-black text-[#3b2511]">
              <span className="mr-2 rounded-full bg-amber-900 px-2 py-0.5 text-xs text-amber-50">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </section>

      <div className="mt-8 text-center">
        <p className="chapter-kicker">World Genesis</p>
        <h1 className="mt-3 text-4xl font-black text-[#34210f]">创建世界工坊</h1>
        <p className="manuscript mx-auto mt-4 max-w-2xl">
          从官方题材模板开始，编辑真理库、角色关系与伏笔，然后冻结为你的初始世界状态。
        </p>
        <button className="secondary-button mt-5" disabled={creating} type="button" onClick={onCreateSample}>
          创建内置示例世界
        </button>
      </div>

      <section className="book-card mt-8 p-5" data-testid="brief-world-entry-panel">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="chapter-kicker">一句话创建故事世界</p>
            <h2 className="mt-2 text-2xl font-black text-[#34210f]">一句话开书</h2>
            <p className="manuscript mt-2 text-sm text-[#5e3b1c]">写下一个故事点子，系统会生成可编辑的创建草稿。</p>
            <p className="manuscript mt-1 text-sm font-bold text-[#5e3b1c]">生成草稿只会填入下方表单，不会创建世界，也不会写入正史。</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
          <label className="block">
            <span className="text-sm font-semibold text-[#4a321e]">一句话故事想法</span>
            <textarea
              className="mt-1 min-h-24 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3"
              value={brief}
              onChange={(event) => setBrief(event.target.value)}
              placeholder="例如：一个所有人出生时都会被分配未来死因的王国"
              disabled={briefLoading}
            />
          </label>
          <div className="flex items-end gap-2">
            <button className="primary-button" type="button" disabled={briefLoading || !onExpandBrief} onClick={() => void submitBriefDraft()}>
              {briefLoading ? '正在生成可编辑草稿…' : '生成创建草稿'}
            </button>
            {briefLoading && <button className="secondary-button" type="button" onClick={cancelBriefDraft}>取消生成</button>}
          </div>
        </div>
        {briefError && <p className="paper-error mt-4 text-left" role="alert">{briefError}</p>}
        {briefSuccess && (
          <section className="mt-4 rounded-2xl bg-amber-50/70 p-4" aria-live="polite">
            <p className="font-black text-[#3b2511]">{briefSuccess}</p>
            <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">现在还没有创建世界，也没有写入正史。只有点击“创建自定义世界”后才会创建。</p>
            {briefNotes.rationale && <p className="manuscript mt-3 text-sm">{briefNotes.rationale}</p>}
            {(briefNotes.assumptions?.length ?? 0) > 0 && (
              <div className="mt-3">
                <p className="text-sm font-bold text-[#5e3b1c]">草稿补全时采用的假设</p>
                <ul className="manuscript mt-1 list-disc space-y-1 pl-5 text-sm">{briefNotes.assumptions?.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            )}
            {(briefNotes.safety_notes?.length ?? 0) > 0 && (
              <div className="mt-3">
                <p className="text-sm font-bold text-[#5e3b1c]">安全提示</p>
                <ul className="manuscript mt-1 list-disc space-y-1 pl-5 text-sm">{briefNotes.safety_notes?.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            )}
          </section>
        )}
      </section>

      {seeds.length > 0 || seedLoading || seedError ? (
        <section className="mt-8">
          <SeedLibraryPanel
            seeds={seeds}
            selectedSeedKey={activeSeedKey}
            loading={seedLoading}
            error={seedError}
            onApplySeed={applySeed}
            onCreateSeed={(seedKey) => void onCreateSeed?.(seedKey)}
          />
        </section>
      ) : null}

      <section className="mt-8 grid gap-4 md:grid-cols-3" data-testid="genre-preset-grid">
        {GENRE_PRESETS.map((preset) => (
          <button
            key={preset.key}
            type="button"
            onClick={() => selectPreset(preset.key)}
            className={`book-card motion-soft-lift p-4 text-left transition ${
              selectedPresetKey === preset.key ? 'border-amber-900 bg-amber-100/70' : 'hover:bg-amber-50'
            }`}
          >
            <span className="text-lg font-black text-[#3b2511]">{preset.label}</span>
            <p className="mt-2 text-sm ink-muted">{preset.description}</p>
          </button>
        ))}
      </section>

      <section className="book-card mt-8 grid gap-4 p-5 md:grid-cols-2">
        <label className="block">
          <span className="text-sm font-semibold text-[#4a321e]">世界标题</span>
          <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-[#4a321e]">题材标识</span>
          <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={form.genre_template} onChange={(event) => setForm({ ...form, genre_template: event.target.value })} required />
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-[#4a321e]">叙事风格</span>
          <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={toneText(form, 'style')} onChange={(event) => updateToneField('style', event.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-[#4a321e]">节奏提示</span>
          <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={toneText(form, 'pacing')} onChange={(event) => updateToneField('pacing', event.target.value)} />
        </label>
        <label className="block md:col-span-2">
          <span className="text-sm font-semibold text-[#4a321e]">真理库 / 世界底层设定</span>
          <textarea className="mt-1 min-h-32 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={form.truth_canon} onChange={(event) => setForm({ ...form, truth_canon: event.target.value })} required />
        </label>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black text-[#34210f]">预置角色</h2>
          <button type="button" className="secondary-button" onClick={addCharacter}>添加角色</button>
        </div>
        <div className="mt-4 space-y-4">
          {form.starter_assets.characters.map((character, index) => (
            <article key={index} className="book-card grid gap-3 p-5 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">姓名</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={character.name} onChange={(event) => updateCharacter(index, { name: event.target.value })} required />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">角色类型</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={character.role_type} onChange={(event) => updateCharacter(index, { role_type: event.target.value })} required />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">公开身份</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={profileText(character, 'identity')} onChange={(event) => updateCharacterProfile(index, 'identity', event.target.value)} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">能力/标签</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={profileText(character, 'skill')} onChange={(event) => updateCharacterProfile(index, 'skill', event.target.value)} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">隐藏秘密</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={hiddenText(character, 'secret')} onChange={(event) => updateCharacterHidden(index, 'secret', event.target.value)} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">命运标记</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={character.destiny_flag ?? ''} onChange={(event) => updateCharacter(index, { destiny_flag: event.target.value })} />
              </label>
              <label className="block md:col-span-2">
                <span className="text-sm font-semibold text-[#4a321e]">当前目标（用顿号、逗号或换行分隔）</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={goalsToText(character.current_goals)} onChange={(event) => updateCharacter(index, { current_goals: textToGoals(event.target.value) })} />
              </label>
              <div className="md:col-span-2">
                <button type="button" className="text-sm font-bold text-red-700" onClick={() => removeCharacter(index)} disabled={form.starter_assets.characters.length <= 1}>删除角色</button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black text-[#34210f]">初始关系</h2>
          <button type="button" className="secondary-button" onClick={addRelation} disabled={form.starter_assets.characters.length < 2}>添加关系</button>
        </div>
        <div className="mt-4 space-y-3">
          {(form.starter_assets.relations ?? []).map((relation, index) => (
            <article key={index} className="book-card grid gap-3 p-4 md:grid-cols-5">
              <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={relation.source_index} onChange={(event) => updateRelation(index, { source_index: Number(event.target.value) })}>
                {form.starter_assets.characters.map((character, characterIndex) => <option key={characterIndex} value={characterIndex}>{character.name}</option>)}
              </select>
              <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={relation.target_index} onChange={(event) => updateRelation(index, { target_index: Number(event.target.value) })}>
                {form.starter_assets.characters.map((character, characterIndex) => <option key={characterIndex} value={characterIndex}>{character.name}</option>)}
              </select>
              <select className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" value={relation.relation_type} onChange={(event) => updateRelation(index, { relation_type: event.target.value })} required>
                <option value="" disabled>选择关系类型</option>
                <option value="mutual_suspicion">相互猜疑</option>
                <option value="ally">盟友</option>
                <option value="rival">对手/竞争</option>
                <option value="mentor">师徒</option>
                <option value="enemy">敌对</option>
                <option value="friend">朋友</option>
                <option value="family">亲属</option>
                <option value="romantic">恋人</option>
                <option value="stranger">陌生人</option>
                <option value="alliance">同盟</option>
                <option value="strained_alliance">貌合神离</option>
                <option value="public_opponents">公开对立</option>
              </select>
              <input className="rounded-2xl border border-amber-900/20 bg-white/70 px-3 py-2" type="number" min={1} max={5} value={relation.intensity ?? 1} onChange={(event) => updateRelation(index, { intensity: Number(event.target.value) })} />
              <button type="button" className="text-sm font-bold text-red-700" onClick={() => removeRelation(index)}>删除</button>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black text-[#34210f]">初始伏笔</h2>
          <button type="button" className="secondary-button" onClick={addForeshadow}>添加伏笔</button>
        </div>
        <div className="mt-4 space-y-4">
          {(form.starter_assets.foreshadows ?? []).map((foreshadow, index) => (
            <article key={index} className="book-card grid gap-3 p-5 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">标题</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={foreshadow.title} onChange={(event) => updateForeshadow(index, { title: event.target.value })} required />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">类型</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={foreshadow.foreshadow_type} onChange={(event) => updateForeshadow(index, { foreshadow_type: event.target.value })} required />
              </label>
              <label className="block md:col-span-2">
                <span className="text-sm font-semibold text-[#4a321e]">描述</span>
                <textarea className="mt-1 min-h-24 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={foreshadow.description} onChange={(event) => updateForeshadow(index, { description: event.target.value })} required />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">紧迫度</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" type="number" min={1} max={5} value={foreshadow.urgency_level ?? 1} onChange={(event) => updateForeshadow(index, { urgency_level: Number(event.target.value) })} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">预计回收窗口</span>
                <input className="mt-1 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3" value={foreshadow.expected_resolution_window ?? ''} onChange={(event) => updateForeshadow(index, { expected_resolution_window: event.target.value })} />
              </label>
              <div className="md:col-span-2">
                <span className="text-sm font-semibold text-[#4a321e]">关联角色</span>
                <div className="mt-2 flex flex-wrap gap-3">
                  {form.starter_assets.characters.map((character, characterIndex) => (
                    <label key={characterIndex} className="rounded-full border border-amber-900/20 bg-amber-50/60 px-3 py-2 text-sm text-[#4a321e]">
                      <input className="mr-2" type="checkbox" checked={(foreshadow.related_character_indexes ?? []).includes(characterIndex)} onChange={() => toggleForeshadowCharacter(index, characterIndex)} />
                      {character.name}
                    </label>
                  ))}
                </div>
              </div>
              <div className="md:col-span-2">
                <button type="button" className="text-sm font-bold text-red-700" onClick={() => removeForeshadow(index)}>删除伏笔</button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="mt-8 text-center">
        <button className="primary-button" disabled={creating} type="submit">
          {creating ? '正在冻结初始真理库...' : '创建自定义世界'}
        </button>
      </div>
    </form>
  );
}
