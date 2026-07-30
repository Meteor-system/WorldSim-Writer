import { useCallback, useEffect, useRef, useState } from 'react';
import { AUTH_EXPIRED_EVENT, AUTH_TOKEN_KEY } from './api/client';
import type { StudioLaunchContext, WorldOverview } from './api/types';
import { AuthPage } from './auth/AuthPage';
import { StudioPage } from './studio/StudioPage';
import { WorldPage } from './world/WorldPage';

type WorldRefreshKey = {
  worldId: number;
  token: number;
};

export function App() {
  const [userEmail, setUserEmail] = useState(localStorage.getItem(AUTH_TOKEN_KEY) ? '已登录用户' : '');
  const [studioWorld, setStudioWorld] = useState<WorldOverview | null>(null);
  const [studioLaunchContext, setStudioLaunchContext] = useState<StudioLaunchContext>({});
  const [approvedWorld, setApprovedWorld] = useState<WorldOverview | null>(null);
  const [worldRefreshKey, setWorldRefreshKey] = useState<WorldRefreshKey | null>(null);
  const successRef = useRef<HTMLDivElement>(null);

  const handleLogout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setUserEmail('');
    setStudioWorld(null);
    setStudioLaunchContext({});
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
  }

  function refreshWorld(worldId: number) {
    setWorldRefreshKey((current) => ({ worldId, token: (current?.token ?? 0) + 1 }));
  }

  if (!userEmail) return <AuthPage onAuth={setUserEmail} />;

  if (studioWorld) {
    return (
      <main className="book-app">
        <StudioPage
          world={studioWorld}
          launchContext={studioLaunchContext}
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
      </main>
    );
  }

  return (
    <main className="book-app">
      <div className="mx-auto max-w-6xl overflow-hidden rounded-[28px] border border-amber-900/20 bg-[#fff8e8]/70 shadow-xl shadow-amber-950/10">
        <header className="flex items-center justify-between border-b border-amber-900/15 px-6 py-4 text-sm ink-muted">
          <span className="font-bold text-[#4a321e]">WorldSim-Writer</span>
          <div className="flex items-center gap-3">
            <span>{userEmail}</span>
            <button type="button" className="secondary-button" onClick={handleLogout}>退出登录</button>
          </div>
        </header>
        {approvedWorld && <div ref={successRef} tabIndex={-1} className="paper-success px-6 py-3" role="status" aria-live="polite">章节已通过，世界版本更新为 {approvedWorld.world_version}</div>}
        <WorldPage onEnterStudio={enterStudio} autoFocusTitle={!approvedWorld} refreshKey={worldRefreshKey} />
      </div>
    </main>
  );
}
