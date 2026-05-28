import { useEffect, useRef, useState } from 'react';
import type { WorldOverview } from './api/types';
import { AuthPage } from './auth/AuthPage';
import { StudioPage } from './studio/StudioPage';
import { WorldPage } from './world/WorldPage';

export function App() {
  const [userEmail, setUserEmail] = useState(localStorage.getItem('worldsim_token') ? '已登录用户' : '');
  const [studioWorld, setStudioWorld] = useState<WorldOverview | null>(null);
  const [approvedWorld, setApprovedWorld] = useState<WorldOverview | null>(null);
  const successRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (approvedWorld) successRef.current?.focus();
  }, [approvedWorld]);

  if (!userEmail) return <AuthPage onAuth={setUserEmail} />;

  if (studioWorld) {
    return (
      <main className="book-app">
        <StudioPage
          world={studioWorld}
          onBack={() => setStudioWorld(null)}
          onApproved={(world) => {
            setApprovedWorld(world);
            setStudioWorld(null);
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
          <span>{userEmail}</span>
        </header>
        {approvedWorld && <div ref={successRef} tabIndex={-1} className="paper-success px-6 py-3" role="status" aria-live="polite">章节已通过，世界版本更新为 {approvedWorld.world_version}</div>}
        <WorldPage onEnterStudio={setStudioWorld} autoFocusTitle={!approvedWorld} />
      </div>
    </main>
  );
}
