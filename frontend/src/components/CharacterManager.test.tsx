import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createCharacter, deleteCharacter, getCharacters, updateCharacter } from '../api/client';
import type { Character } from '../api/types';
import { CharacterManager } from './CharacterManager';

vi.mock('../api/client', () => ({
  createCharacter: vi.fn(),
  deleteCharacter: vi.fn(),
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
  vi.mocked(createCharacter).mockReset().mockResolvedValue(characters[0]);
  vi.mocked(deleteCharacter).mockReset().mockResolvedValue(undefined);
  vi.mocked(updateCharacter).mockReset().mockResolvedValue(characters[0]);
  vi.mocked(getCharacters).mockReset().mockResolvedValue(characters);
});

afterEach(() => cleanup());

describe('CharacterManager', () => {
  it('renders existing characters with world version governance warning', async () => {
    render(<CharacterManager worldId={7} />);

    expect(await screen.findByText('林砚')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.getByText('目标：')).toBeInTheDocument();
    expect(screen.getByText('调查灵脉衰退')).toBeInTheDocument();
  });

  it('creates a character and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<CharacterManager worldId={7} onChanged={onChanged} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '+ 新增角色' }));
    await user.type(screen.getByLabelText('名字 *'), '沈微霜');
    await user.selectOptions(screen.getByLabelText('类型'), 'supporting');
    await user.type(screen.getByLabelText('当前目标'), '保住城主府档案、查清密信来源');
    await user.type(screen.getByLabelText('修改原因（可选）'), '补充新角色');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(createCharacter).toHaveBeenCalledWith(7, {
      name: '沈微霜',
      role_type: 'supporting',
      status: 'active',
      destiny_flag: undefined,
      current_goals: ['保住城主府档案', '查清密信来源'],
      edit_reason: '补充新角色',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('edits a character and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<CharacterManager worldId={7} onChanged={onChanged} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    const status = screen.getByLabelText('状态');
    await user.selectOptions(status, 'inactive');
    const reason = screen.getByLabelText('修改原因（可选）');
    await user.type(reason, '同步章节结果');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateCharacter).toHaveBeenCalledWith(1, expect.objectContaining({
      name: '林砚',
      role_type: 'protagonist',
      status: 'inactive',
      current_goals: ['调查灵脉衰退'],
      edit_reason: '同步章节结果',
    })));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('deletes a character with an optional reason and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<CharacterManager worldId={7} onChanged={onChanged} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '删除' }));
    await user.type(screen.getByPlaceholderText('删除原因（可选）'), '误建角色');
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    await waitFor(() => expect(deleteCharacter).toHaveBeenCalledWith(1, '误建角色'));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });
});
