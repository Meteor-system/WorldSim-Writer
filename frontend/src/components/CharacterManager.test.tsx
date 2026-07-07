import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getCharacters, updateCharacter } from '../api/client';
import type { Character } from '../api/types';
import { CharacterManager } from './CharacterManager';

vi.mock('../api/client', () => ({
  getCharacters: vi.fn(),
  updateCharacter: vi.fn(),
}));

const characters: Character[] = [
  {
    id: 1,
    name: '林砚',
    role_type: 'protagonist',
    status: 'active',
    public_profile: {},
    hidden_traits: {},
    destiny_flag: '灵脉异动见证者',
    current_goals: ['调查灵脉衰退'],
  },
];

beforeEach(() => {
  vi.mocked(updateCharacter).mockReset().mockResolvedValue({
    ...characters[0],
    status: 'inactive',
    current_goals: ['验证沈微霜是否可信', '追查湿信来源'],
  });
  vi.mocked(getCharacters).mockReset().mockResolvedValue(characters);
});

afterEach(() => cleanup());

describe('CharacterManager', () => {
  it('renders existing characters with world version governance warning', async () => {
    render(<CharacterManager worldId={7} />);

    expect(await screen.findByText('林砚')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并提升世界版本。')).toBeInTheDocument();
    expect(screen.getByText('目标：')).toBeInTheDocument();
    expect(screen.getByText('调查灵脉衰退')).toBeInTheDocument();
  });

  it('hides character create and delete controls for MVP9 scope', async () => {
    render(<CharacterManager worldId={7} />);

    expect(await screen.findByText('林砚')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增角色' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '删除' })).not.toBeInTheDocument();
  });

  it('edits only character status and current goals then refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<CharacterManager worldId={7} onChanged={onChanged} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    expect(screen.getByText('林砚 · 主角')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('状态'), 'inactive');
    const goals = screen.getByLabelText('当前目标');
    await user.clear(goals);
    await user.type(goals, '验证沈微霜是否可信、追查湿信来源');
    await user.type(screen.getByLabelText('修改原因（可选）'), '同步章节结果');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateCharacter).toHaveBeenCalledWith(1, {
      status: 'inactive',
      current_goals: ['验证沈微霜是否可信', '追查湿信来源'],
      edit_reason: '同步章节结果',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('shows saving state while updating a character', async () => {
    const user = userEvent.setup();
    let resolveUpdate: (value: Character) => void = () => undefined;
    vi.mocked(updateCharacter).mockReturnValueOnce(new Promise((resolve) => { resolveUpdate = resolve; }));
    render(<CharacterManager worldId={7} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(screen.getByRole('button', { name: '保存中…' })).toBeDisabled();
    resolveUpdate(characters[0]);
  });

  it('shows save errors without closing the edit form', async () => {
    const user = userEvent.setup();
    vi.mocked(updateCharacter).mockRejectedValueOnce(new Error('保存角色失败'));
    render(<CharacterManager worldId={7} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('保存角色失败');
    expect(screen.getByText('林砚 · 主角')).toBeInTheDocument();
  });
});
