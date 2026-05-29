import type { FormEvent } from 'react';
import { useState } from 'react';
import type {
  StarterCharacterCreate,
  StarterForeshadowCreate,
  StarterRelationCreate,
  WorldCreateRequest,
} from '../api/types';
import { clonePreset, GENRE_PRESETS } from './genrePresets';

type Props = {
  creating: boolean;
  onCreate: (payload: WorldCreateRequest) => Promise<void>;
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

export function WorldCreationForm({ creating, onCreate }: Props) {
  const [selectedPresetKey, setSelectedPresetKey] = useState(GENRE_PRESETS[0].key);
  const [form, setForm] = useState<WorldCreateRequest>(() => clonePreset(GENRE_PRESETS[0]));

  function selectPreset(key: string) {
    const preset = GENRE_PRESETS.find((item) => item.key === key) ?? GENRE_PRESETS[0];
    setSelectedPresetKey(preset.key);
    setForm(clonePreset(preset));
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

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onCreate(form);
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-5xl px-6 py-10 text-left">
      <div className="text-center">
        <p className="chapter-kicker">World Genesis</p>
        <h1 className="mt-3 text-4xl font-black text-[#34210f]">创建世界工坊</h1>
        <p className="manuscript mx-auto mt-4 max-w-2xl">
          从官方题材模板开始，编辑真理库、角色关系与伏笔，然后冻结为你的初始世界状态。
        </p>
      </div>

      <section className="mt-8 grid gap-3 md:grid-cols-3">
        {GENRE_PRESETS.map((preset) => (
          <button
            key={preset.key}
            type="button"
            onClick={() => selectPreset(preset.key)}
            className={`book-card p-4 text-left transition ${
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
