import type { ChapterMemoryCard } from '../api/types';

type Props = { card: ChapterMemoryCard | null | undefined };

export function MemoryCardPanel({ card }: Props) {
  if (!card) return null;
  const facts = card.facts ?? [];
  const links = card.causal_links ?? [];
  return (
    <section className="space-y-2 rounded-2xl border border-amber-900/15 bg-white/40 p-4" aria-label="本章记忆卡">
      <h3 className="font-black text-[#3b2511]">本章记忆卡</h3>
      {card.emotional_arc && <p className="manuscript text-sm">情绪弧：{card.emotional_arc}</p>}
      {facts.length > 0 && (
        <ul className="list-disc pl-5 text-sm">
          {facts.map((fact) => <li key={fact} className="manuscript">{fact}</li>)}
        </ul>
      )}
      {links.length > 0 && (
        <p className="manuscript text-sm">因果：{links.join('；')}</p>
      )}
    </section>
  );
}
