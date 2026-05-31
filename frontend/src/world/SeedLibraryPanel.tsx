import type { WorldSeedSummary } from '../api/types';

type Props = {
  seeds: WorldSeedSummary[];
  selectedSeedKey: string | null;
  loading?: boolean;
  error?: string;
  onApplySeed: (seedKey: string) => void;
  onCreateSeed: (seedKey: string) => void;
};

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function countText(seed: WorldSeedSummary): string {
  const summary = seed.starter_summary;
  return `角色 ${summary.character_count ?? 0} · 关系 ${summary.relation_count ?? 0} · 伏笔 ${summary.foreshadow_count ?? 0}`;
}

export function SeedLibraryPanel({ seeds, selectedSeedKey, loading, error, onApplySeed, onCreateSeed }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在读取世界胚胎库...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="book-card p-5">
        <p className="paper-error" role="alert">{error}</p>
      </section>
    );
  }

  if (seeds.length === 0) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">暂无可用世界胚胎。</p>
      </section>
    );
  }

  return (
    <section className="book-card p-5">
      <div>
        <p className="chapter-kicker">World Embryos</p>
        <h2 className="text-2xl font-black text-[#34210f]">Sandbox Seed Library</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">从高张力官方世界胚胎开始，也可以套用后继续编辑。</p>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {seeds.map((seed) => {
          const characterNames = stringList(seed.starter_summary.character_names);
          const foreshadowTitles = stringList(seed.starter_summary.foreshadow_titles);
          return (
            <article key={seed.key} className={`rounded-2xl border p-4 ${selectedSeedKey === seed.key ? 'border-amber-900 bg-amber-100/70' : 'border-amber-900/15 bg-white/45'}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-xl font-black text-[#3b2511]">{seed.label}</h3>
                  <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-[#8a5a2b]">{seed.genre_template}</p>
                </div>
                {selectedSeedKey === seed.key && <span className="rounded-full bg-amber-900 px-3 py-1 text-xs font-black text-amber-50">当前套用中</span>}
              </div>
              <p className="manuscript mt-3 text-sm">{seed.hook}</p>
              <p className="mt-3 text-sm font-bold text-[#5e3b1c]">{countText(seed)}</p>
              {characterNames.length > 0 && <p className="manuscript mt-2 text-xs">角色：{characterNames.join('、')}</p>}
              {foreshadowTitles.length > 0 && <p className="manuscript mt-1 text-xs">伏笔：{foreshadowTitles.join('、')}</p>}
              <div className="mt-3 flex flex-wrap gap-2">
                {seed.tension_profile.map((tag) => (
                  <span key={tag} className="rounded-full border border-amber-900/15 bg-amber-50/70 px-3 py-1 text-xs font-bold text-[#5e3b1c]">{tag}</span>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" className="secondary-button" onClick={() => onApplySeed(seed.key)}>套用到表单</button>
                <button type="button" className="primary-button" onClick={() => onCreateSeed(seed.key)}>直接创建此胚胎</button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
