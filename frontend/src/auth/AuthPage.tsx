import { FormEvent, useState } from 'react';
import { login, register } from '../api/client';

type Props = { onAuth: (userEmail: string) => void };

export function AuthPage({ onAuth }: Props) {
  const [email, setEmail] = useState('writer@example.com');
  const [password, setPassword] = useState('strongpass123');
  const [error, setError] = useState('');

  async function submit(event: FormEvent, mode: 'login' | 'register') {
    event.preventDefault();
    setError('');
    try {
      const response = mode === 'login'
        ? await login({ email, password })
        : await register({ email, password });
      localStorage.setItem('worldsim_token', response.access_token);
      onAuth(response.user.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : '认证失败');
    }
  }

  return (
    <main className="workbench-auth">
      <section className="paper-panel workbench-auth-card">
        <p className="chapter-kicker">WorldSim Archive</p>
        <h1 className="mt-3 text-4xl font-black tracking-tight text-[#34210f]">WorldSim-Writer</h1>
        <p className="manuscript mt-4">翻开世界手稿，创建样本世界，并让第一章草稿落到纸面。</p>
        <form className="mt-8 space-y-5" onSubmit={(event) => submit(event, 'login')}>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="email">邮箱</label>
            <input id="email" className="paper-input" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
          </div>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="password">密码</label>
            <input id="password" className="paper-input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </div>
          {error && <p className="paper-error" role="alert">{error}</p>}
          <div className="workbench-auth-actions pt-1">
            <button type="submit" className="primary-button">登录</button>
            <button type="button" className="secondary-button" onClick={(event) => submit(event, 'register')}>注册</button>
          </div>
        </form>
      </section>
    </main>
  );
}
