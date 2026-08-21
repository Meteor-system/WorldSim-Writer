import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, AUTH_EXPIRED_EVENT, AUTH_TOKEN_KEY } from './api/client';
import type { StudioLaunchContext, WorldOverview, WorldSummary } from './api/types';
import { AuthPage } from './auth/AuthPage';
import { StudioPage } from './studio/StudioPage';
import { WorkbenchBookshelf } from './workbench/WorkbenchBookshelf';
import { WorkbenchTopBar } from './workbench/WorkbenchTopBar';

type WorldRefreshKey = {
  worldId: number;
  token: number;
};

export function App() {
  const [userEmail, setUserEmail] = useState(localStorage.getItem(AUTH_TOKEN_KEY) ? '已登录用户' : '');
  const [studioWorld, setStudioWorld] = useState<WorldOverview | null>(null);
  const [studioLaunchContext, setStudioLaunchContext] = useState<StudioLaunchContext>({});
  const [createOpen, setCreateOpen] = useState(false);
  const [approvedWorld, setApprovedWorld] = useState<WorldOverview | null>(null);
  const [worldRefreshKey, setWorldRefreshKey] = useState<WorldRefreshKey | null>(null);
  const successRef = useRef<HTMLDivElement>(null);

  const handleLogout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setUserEmail('');
    setStudioWorld(null);
    setStudioLaunchContext({});
    setCreateOpen(false);
    setApprovedWorld(null);
    setWorldRefreshKey(null);
  }, []);

  useEffect(() => {
    const handleSessionExpired = () => handleLogout();
    window.addEventListener(AUTH_EXPIRED_EVENT, handleSessionExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleSessionExpired);
  }, [handleLogout]);

  useEffect(() => {
    if (approvedWorld) successRef.current?.focus();
  }, [approvedWorld]);

  function enterStudio(world: WorldOverview, context: StudioLaunchContext = {}) {
    setStudioWorld(world);
    setStudioLaunchContext(context);
    setApprovedWorld(null);
  }

  function refreshWorld(worldId: number) {
    setWorldRefreshKey((current) => ({ worldId, token: (current?.token ?? 0) + 1 }));
  }

  async function openWorldSummary(summary: WorldSummary) {
    try {
      const overview = await apiRequest<WorldOverview>(`/worlds/${summary.id}/overview`);
      enterStudio(overview);
    } catch {
      // 静默失败：书架打开路径已有显式错误处理。
    }
  }

  if (!userEmail) return <AuthPage onAuth={setUserEmail} />;

  return (
    <main className="workbench-app">
      <WorkbenchTopBar
        currentWorldId={studioWorld?.id ?? null}
        currentWorldVersion={studioWorld?.world_version}
        currentWorldStatus={studioWorld?.status}
        userEmail={userEmail}
        onLogout={handleLogout}
        onSwitchWorld={(summary) => void openWorldSummary(summary)}
        onCreated={(overview) => {
          enterStudio(overview);
          refreshWorld(overview.id);
        }}
        createOpen={createOpen}
        onCreateOpenChange={setCreateOpen}
        onOpenWorld={() => setStudioWorld(null)}
      />
      {approvedWorld && (
        <div ref={successRef} tabIndex={-1} className="paper-success px-6 py-3" role="status" aria-live="polite">
          章节已通过，世界版本更新为 {approvedWorld.world_version}
        </div>
      )}
      <div className="workbench-app-body">
        {studioWorld ? (
          <StudioPage
            world={studioWorld}
            launchContext={studioLaunchContext}
            hideTopBar
            userEmail={userEmail}
            onLogout={handleLogout}
            onBack={() => {
              refreshWorld(studioWorld.id);
              setStudioWorld(null);
              setStudioLaunchContext({});
            }}
            onApproved={(world) => {
              setApprovedWorld(world);
              refreshWorld(world.id);
              setStudioWorld(null);
              setStudioLaunchContext({});
            }}
            onAbandoned={(worldId) => {
              setApprovedWorld(null);
              refreshWorld(worldId);
              setStudioWorld(null);
              setStudioLaunchContext({});
            }}
          />
        ) : (
          <div className="workbench-main" role="region" aria-label="作品书架">
            <WorkbenchBookshelf
              refreshKey={worldRefreshKey}
              onCreateWorld={() => setCreateOpen(true)}
              onOpenWorld={(world) => enterStudio(world)}
            />
          </div>
        )}
      </div>
    </main>
  );
}
