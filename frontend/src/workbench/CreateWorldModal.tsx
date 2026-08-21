import { useEffect, useState } from 'react';
import { apiRequest, createSampleWorld, createWorld, createWorldFromSeed, getWorldSeed, listWorldSeeds } from '../api/client';
import type { WorldCreateRequest, WorldOverview, WorldSeedDetail, WorldSeedSummary } from '../api/types';
import { WorldCreationForm } from '../world/WorldCreationForm';

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: (world: WorldOverview) => void;
};

export function CreateWorldModal({ open, onClose, onCreated }: Props) {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [seeds, setSeeds] = useState<WorldSeedSummary[]>([]);
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedError, setSeedError] = useState('');

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setSeedLoading(true);
    setSeedError('');
    listWorldSeeds()
      .then((payload) => {
        if (!cancelled) setSeeds(payload.seeds ?? []);
      })
      .catch((err) => {
        if (!cancelled) setSeedError(err instanceof Error ? err.message : '灵感模板加载失败');
      })
      .finally(() => {
        if (!cancelled) setSeedLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  if (!open) return null;

  async function loadOverview(createdId: number, firstChapterGoal = '') {
    const overview = await apiRequest<WorldOverview>(`/worlds/${createdId}/overview`);
    onCreated(overview);
    if (firstChapterGoal) {
      // Keep the first chapter goal available via the launch context.
      window.dispatchEvent(new CustomEvent('worldsim:created-goal', { detail: firstChapterGoal }));
    }
  }

  async function submitWorld(payload: WorldCreateRequest, context?: { firstChapterGoal?: string }) {
    setCreating(true);
    setError('');
    try {
      const created = await createWorld(payload);
      await loadOverview(created.id, context?.firstChapterGoal ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function submitSampleWorld() {
    setCreating(true);
    setError('');
    try {
      const created = await createSampleWorld();
      await loadOverview(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function loadSeed(seedKey: string): Promise<WorldSeedDetail> {
    return getWorldSeed(seedKey);
  }

  async function submitSeedWorld(seedKey: string) {
    const firstChapterGoal = seeds.find((seed) => seed.key === seedKey)?.starter_guidance.first_chapter_goal ?? '';
    setCreating(true);
    setError('');
    try {
      const created = await createWorldFromSeed(seedKey);
      await loadOverview(created.id, firstChapterGoal);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建灵感模板失败');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div
      className="workbench-manager-drawer"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="workbench-manager-panel" role="dialog" aria-modal="true" aria-label="新建世界">
        <div className="workbench-manager-drawer-header">
          <h2 className="text-xl font-black text-[#34210f]">新建世界</h2>
          <button type="button" className="ghost-button" onClick={onClose}>
            关闭 ✕
          </button>
        </div>
        <div className="workbench-manager-drawer-body">
          {error && <p className="paper-error" role="alert">{error}</p>}
          <WorldCreationForm
            creating={creating}
            onCreate={submitWorld}
            onCreateSample={submitSampleWorld}
            seeds={seeds}
            seedLoading={seedLoading}
            seedError={seedError}
            onLoadSeed={loadSeed}
            onCreateSeed={submitSeedWorld}
          />
        </div>
      </div>
    </div>
  );
}
