import { useEffect, useState } from 'react';
import { getChapterHistory, getChapterHistoryDetail, getNarrativeHealth, getOpenThreads, getWorldPulse } from '../api/client';
import type { ChapterHistoryDetailResponse, ChapterHistoryResponse, NarrativeHealthResponse, OpenThreadsResponse, WorldOverview, WorldPulseResponse } from '../api/types';
import { CharacterManager } from '../components/CharacterManager';
import { ForeshadowManager } from '../components/ForeshadowManager';
import { RelationManager } from '../components/RelationManager';
import { ChapterHistoryPanel } from '../world/ChapterHistoryPanel';
import { NarrativeHealthPanel } from '../world/NarrativeHealthPanel';
import { OpenThreadsPanel } from '../world/OpenThreadsPanel';
import { WorldPulsePanel } from '../world/WorldPulsePanel';

export type ManagerPanelKey = 'characters' | 'relations' | 'foreshadows' | 'history' | 'threads' | 'health' | 'pulse';

export const MANAGER_PANELS: { key: ManagerPanelKey; label: string }[] = [
  { key: 'characters', label: '角色' },
  { key: 'relations', label: '关系' },
  { key: 'foreshadows', label: '伏笔' },
  { key: 'history', label: '章节历史' },
  { key: 'threads', label: '开放线索' },
  { key: 'health', label: '叙事健康' },
  { key: 'pulse', label: '世界脉搏' },
];

const TITLES: Record<ManagerPanelKey, string> = Object.fromEntries(
  MANAGER_PANELS.map((item) => [item.key, item.label]),
) as Record<ManagerPanelKey, string>;

type Props = {
  world: WorldOverview;
  panel: ManagerPanelKey | null;
  onClose: () => void;
  onWorldChanged: () => void;
};

export function WorkbenchManagerDrawer({ world, panel, onClose, onWorldChanged }: Props) {
  const [history, setHistory] = useState<ChapterHistoryResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [historyDetail, setHistoryDetail] = useState<ChapterHistoryDetailResponse | null>(null);

  const [threads, setThreads] = useState<OpenThreadsResponse | null>(null);
  const [threadsLoading, setThreadsLoading] = useState(false);
  const [threadsError, setThreadsError] = useState('');

  const [health, setHealth] = useState<NarrativeHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState('');

  const [pulse, setPulse] = useState<WorldPulseResponse | null>(null);
  const [pulseLoading, setPulseLoading] = useState(false);
  const [pulseError, setPulseError] = useState('');

  useEffect(() => {
    setHistory(null);
    setHistoryError('');
    setHistoryDetail(null);
    setThreads(null);
    setThreadsError('');
    setHealth(null);
    setHealthError('');
    setPulse(null);
    setPulseError('');
    if (!panel) return;
    let cancelled = false;

    if (panel === 'history') {
      setHistoryLoading(true);
      getChapterHistory(world.id)
        .then((payload) => {
          if (!cancelled) setHistory(payload);
        })
        .catch((err) => {
          if (!cancelled) setHistoryError(err instanceof Error ? err.message : '章节历史加载失败');
        })
        .finally(() => {
          if (!cancelled) setHistoryLoading(false);
        });
    }
    if (panel === 'threads') {
      setThreadsLoading(true);
      getOpenThreads(world.id)
        .then((payload) => {
          if (!cancelled) setThreads(payload);
        })
        .catch((err) => {
          if (!cancelled) setThreadsError(err instanceof Error ? err.message : '开放线索加载失败');
        })
        .finally(() => {
          if (!cancelled) setThreadsLoading(false);
        });
    }
    if (panel === 'health') {
      setHealthLoading(true);
      getNarrativeHealth(world.id)
        .then((payload) => {
          if (!cancelled) setHealth(payload);
        })
        .catch((err) => {
          if (!cancelled) setHealthError(err instanceof Error ? err.message : '叙事健康加载失败');
        })
        .finally(() => {
          if (!cancelled) setHealthLoading(false);
        });
    }
    if (panel === 'pulse') {
      setPulseLoading(true);
      getWorldPulse(world.id)
        .then((payload) => {
          if (!cancelled) setPulse(payload);
        })
        .catch((err) => {
          if (!cancelled) setPulseError(err instanceof Error ? err.message : '世界脉搏加载失败');
        })
        .finally(() => {
          if (!cancelled) setPulseLoading(false);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [panel, world.id]);

  if (!panel) return null;

  return (
    <div
      className="workbench-manager-drawer"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      onKeyDown={(event) => {
        if (event.key === 'Escape') onClose();
      }}
    >
      <div className="workbench-manager-panel" role="dialog" aria-modal="true" aria-label={TITLES[panel]}>
        <div className="workbench-manager-drawer-header">
          <h2 className="text-xl font-black text-[#34210f]">{TITLES[panel]}</h2>
          <button type="button" className="ghost-button" onClick={onClose}>
            关闭 ✕
          </button>
        </div>
        <div className="workbench-manager-drawer-body">
          {panel === 'characters' && <CharacterManager worldId={world.id} onChanged={onWorldChanged} />}
          {panel === 'relations' && <RelationManager worldId={world.id} characters={world.characters} onChanged={onWorldChanged} />}
          {panel === 'foreshadows' && <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={onWorldChanged} />}
          {panel === 'history' && (
            <ChapterHistoryPanel
              history={history}
              loading={historyLoading}
              error={historyError}
              onLoadDetail={async (chapterId) => {
                const detail = await getChapterHistoryDetail(chapterId);
                setHistoryDetail(detail);
                return detail;
              }}
            />
          )}
          {panel === 'history' && historyDetail && (
            <article className="mt-4 rounded-2xl bg-white/45 p-4">
              <h3 className="font-black text-[#3b2511]">{historyDetail.title}</h3>
              <pre className="manuscript whitespace-pre-wrap text-sm">{historyDetail.approved_content}</pre>
            </article>
          )}
          {panel === 'threads' && <OpenThreadsPanel openThreads={threads} loading={threadsLoading} error={threadsError} />}
          {panel === 'health' && <NarrativeHealthPanel health={health} loading={healthLoading} error={healthError} />}
          {panel === 'pulse' && <WorldPulsePanel pulse={pulse} loading={pulseLoading} error={pulseError} />}
        </div>
      </div>
    </div>
  );
}
