import { FormEvent, useState } from 'react';
import { apiRequest } from '../api/client';
import type { AuthResponse } from '../api/types';

type Props = { onAuth: (userEmail: string) => void };

export function AuthPage({ onAuth }: Props) {
  const [email, setEmail] = useState('writer@example.com');
  const [password, setPassword] = useState('strongpass123');
  const [error, setError] = useState('');

  async function submit(event: FormEvent, mode: 'login' | 'register') {
    event.preventDefault();
    setError('');
    try {
      const response = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('worldsim_token', response.access_token);
      onAuth(response.user.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : '认证失败');
    }
  }

  return (
    <main className="book-app flex items-center justify-center">
      <section className="paper-panel surface-layer motion-page-enter w-full max-w-4xl overflow-hidden p-8 md:grid md:grid-cols-[1.05fr_0.95fr] md:p-0" data-testid="auth-entry-panel">
        <div className="border-b border-amber-900/15 p-8 md:border-b-0 md:border-r md:p-12">
          <p className="chapter-kicker">故事世界入口</p>
          <h1 className="mt-4 text-5xl font-black tracking-tight text-[#34210f]">进入故事世界运营台</h1>
          <p className="manuscript mt-6 text-lg">登录后创建世界胚胎、推进章节草稿，并把通过审核的章节写入正史。</p>
          <div className="mt-10 rounded-2xl border border-amber-900/15 bg-white/30 p-5 text-sm ink-muted">
            <p>审批通过后，系统会更新世界进度、角色目标、悬念/伏笔和世界历史记录。</p>
          </div>
        </div>
        <form className="space-y-5 p-8 md:p-12" onSubmit={(event) => submit(event, 'login')}>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="email">邮箱</label>
            <input id="email" className="paper-input" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="password">密码</label>
            <input id="password" className="paper-input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </div>
          {error && <p className="paper-error" role="alert">{error}</p>}
          <div className="flex flex-wrap gap-3 pt-2" data-testid="auth-actions">
            <button type="submit" className="primary-button motion-soft-lift">登录</button>
            <button type="button" className="secondary-button motion-soft-lift" onClick={(event) => submit(event, 'register')}>注册</button>
          </div>
        </form>
      </section>
    </main>
  );
}
