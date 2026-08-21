import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import type { WorldOverview, WorldSummary } from '../api/types';
import { CreateWorldModal } from './CreateWorldModal';

type Props = {
  currentWorldId: number;
  currentWorldVersion: number;
  currentWorldStatus: string;
  onSwitchWorld: (world: WorldSummary) => void;
  onCreated: (world: WorldOverview) => void;
  onLogout: () => void;
  userEmail: string;
  onOpenWorld?: () => void;
};

export function WorkbenchTopBar({
  currentWorldId,
  currentWorldVersion,
  currentWorldStatus,
  onSwitchWorld,
  onCreated,
  onLogout,
  userEmail,
  onOpenWorld,
}: Props) {
  const [worlds, setWorlds] = useState<WorldSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateWorld, setShowCreateWorld] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiRequest<WorldSummary[]>('/worlds')
      .then((payload) => {
        if (!cancelled) setWorlds(Array.isArray(payload) ? payload : []);
      })
      .catch(() => {
        if (!cancelled) setWorlds([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [currentWorldId]);

  return (
    <>
    <header className="workbench-topbar" role="banner">
      <div className="workbench-topbar-start">
        <span className="font-bold text-[#4a321e]">WorldSim-Writer</span>
        <select
          className="paper-input workbench-world-switch"
          aria-label="切换世界"
          value={currentWorldId}
          disabled={loading}
          onChange={(event) => {
            const next = worlds.find((item) => item.id === Number(event.target.value));
            if (next) onSwitchWorld(next);
          }}
        >
          <option value={currentWorldId}>当前世界（加载中…）</option>
          {worlds.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title} · v{item.world_version} · {item.status === 'archived' ? '已归档' : '连载中'}
            </option>
          ))}
        </select>
        {onOpenWorld && (
          <button type="button" className="ghost-button" onClick={onOpenWorld}>
            世界
          </button>
        )}
      </div>
      <div className="workbench-topbar-end text-sm ink-muted">
        <span>v{currentWorldVersion}</span>
        <span>{currentWorldStatus === 'archived' ? '已归档' : '连载中'}</span>
        <button type="button" className="secondary-button" onClick={() => setShowCreateWorld(true)}>
          新建世界
        </button>
        <span className="workbench-email" title={userEmail}>{userEmail}</span>
        <button type="button" className="ghost-button" onClick={onLogout}>
          退出登录
        </button>
      </div>
    </header>
      <CreateWorldModal open={showCreateWorld} onClose={() => setShowCreateWorld(false)} onCreated={onCreated} />
    </>
  );
}
