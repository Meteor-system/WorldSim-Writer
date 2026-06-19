import { FormEvent, useState } from 'react';
import { apiRequest } from '../api/client';
import type { AuthResponse } from '../api/types';

type Props = { onAuth: (userEmail: string) => void };

type FieldErrors = { email?: string; password?: string };

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AuthPage({ onAuth }: Props) {
  const [email, setEmail] = useState('writer@example.com');
  const [password, setPassword] = useState('strongpass123');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  function validate(mode: 'login' | 'register'): FieldErrors {
    const errors: FieldErrors = {};
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      errors.email = '请输入邮箱';
    } else if (!EMAIL_PATTERN.test(trimmedEmail)) {
      errors.email = '邮箱格式不正确';
    }
    if (!password) {
      errors.password = '请输入密码';
    } else if (mode === 'register' && password.length < 8) {
      errors.password = '注册密码至少 8 位';
    }
    return errors;
  }

  async function submit(event: FormEvent, mode: 'login' | 'register') {
    event.preventDefault();
    if (submitting) return;
    setError('');
    const errors = validate(mode);
    setFieldErrors(errors);
    if (errors.email || errors.password) return;
    setSubmitting(true);
    try {
      const response = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), password }),
      });
      localStorage.setItem('worldsim_token', response.access_token);
      onAuth(response.user.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : '认证失败');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="book-app flex items-center justify-center">
      <section className="paper-panel surface-layer motion-page-enter w-full max-w-4xl overflow-hidden p-8 md:grid md:grid-cols-[1.05fr_0.95fr] md:p-0" data-testid="auth-entry-panel">
        <div className="border-b border-amber-900/15 p-8 md:border-b-0 md:border-r md:p-12">
          <p className="chapter-kicker">故事世界入口</p>
          <h1 className="mt-4 text-5xl font-black tracking-tight text-[#34210f]">故事世界运营台</h1>
          <p className="manuscript mt-6 text-lg">登录后创建世界胚胎、推进章节草稿，并把通过审核的章节写入正史。</p>
          <div className="mt-10 rounded-2xl border border-amber-900/15 bg-white/30 p-5 text-sm ink-muted">
            <p>审批通过后，系统会更新世界进度、角色目标、悬念/伏笔和世界历史记录。</p>
          </div>
        </div>
        <form className="space-y-5 p-8 md:p-12" noValidate onSubmit={(event) => submit(event, 'login')}>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="email">邮箱</label>
            <input id="email" className="paper-input" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
            {fieldErrors.email && <p className="mt-1 text-sm text-red-700" role="alert">{fieldErrors.email}</p>}
          </div>
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="password">密码</label>
            <input id="password" className="paper-input" type="password" required value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
            {fieldErrors.password && <p className="mt-1 text-sm text-red-700" role="alert">{fieldErrors.password}</p>}
          </div>
          {error && <p className="paper-error" role="alert">{error}</p>}
          <div className="flex flex-wrap gap-3 pt-2" data-testid="auth-actions">
            <button type="submit" className="primary-button motion-soft-lift" disabled={submitting}>{submitting ? '登录中…' : '登录'}</button>
            <button type="button" className="secondary-button motion-soft-lift" disabled={submitting} onClick={(event) => submit(event, 'register')}>{submitting ? '注册中…' : '注册'}</button>
          </div>
        </form>
      </section>
    </main>
  );
}
