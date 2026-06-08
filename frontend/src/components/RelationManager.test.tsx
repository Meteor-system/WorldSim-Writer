import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRelation, deleteRelation, getRelations, updateRelation } from '../api/client';
import type { Character, CharacterRelation } from '../api/types';
import { RelationManager } from './RelationManager';

vi.mock('../api/client', () => ({
  getRelations: vi.fn(),
  createRelation: vi.fn(),
  updateRelation: vi.fn(),
  deleteRelation: vi.fn(),
}));

const characters: Character[] = [
  { id: 1, name: '林砚', role_type: 'protagonist', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
  { id: 2, name: '沈微霜', role_type: 'ally', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
];

const relations: CharacterRelation[] = [
  { id: 1, source_character_id: 1, target_character_id: 2, relation_type: 'uneasy_alliance', intensity: 2, visibility: 'public' },
];

beforeEach(() => {
  vi.mocked(getRelations).mockReset().mockResolvedValue(relations);
  vi.mocked(createRelation).mockReset().mockResolvedValue(relations[0]);
  vi.mocked(updateRelation).mockReset().mockResolvedValue(relations[0]);
  vi.mocked(deleteRelation).mockReset().mockResolvedValue(undefined);
});

afterEach(() => cleanup());

describe('RelationManager', () => {
  it('renders relationship cards with character names and world version governance warning', async () => {
    render(<RelationManager worldId={7} characters={characters} />);

    expect(await screen.findByText('林砚 → 沈微霜')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.getByText('关系：uneasy_alliance')).toBeInTheDocument();
    expect(screen.getByText('强度：2')).toBeInTheDocument();
    expect(screen.getByText('可见性：公开')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('可见性：public');
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();
  });

  it('deletes a relation and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<RelationManager worldId={7} characters={characters} onChanged={onChanged} />);

    expect(await screen.findByText('林砚 → 沈微霜')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '删除' }));
    await user.type(screen.getByPlaceholderText('删除原因（可选）'), '关系线废弃');
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    await waitFor(() => expect(deleteRelation).toHaveBeenCalledWith(1, '关系线废弃'));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('creates a relation and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<RelationManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.type(screen.getByLabelText('关系类型 *'), 'mentor');
    await user.type(screen.getByLabelText('备注 / 修改原因（可选）'), '补充师承关系');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(createRelation).toHaveBeenCalledWith(7, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'mentor',
      intensity: 1,
      visibility: 'public',
      edit_reason: '补充师承关系',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('edits a relation and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<RelationManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    const relationType = screen.getByLabelText('关系类型 *');
    await user.clear(relationType);
    await user.type(relationType, 'trusted_ally');
    await user.type(screen.getByLabelText('备注 / 修改原因（可选）'), '关系升温');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateRelation).toHaveBeenCalledWith(1, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'trusted_ally',
      intensity: 2,
      visibility: 'public',
      edit_reason: '关系升温',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('shows saving state while saving a relation', async () => {
    const user = userEvent.setup();
    let resolveCreate: (value: CharacterRelation) => void = () => undefined;
    vi.mocked(createRelation).mockReturnValueOnce(new Promise((resolve) => { resolveCreate = resolve; }));
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.type(screen.getByLabelText('关系类型 *'), 'mentor');
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(screen.getByRole('button', { name: '保存中…' })).toBeDisabled();
    resolveCreate(relations[0]);
  });

  it('shows save errors without closing the form', async () => {
    const user = userEvent.setup();
    vi.mocked(updateRelation).mockRejectedValueOnce(new Error('保存关系失败'));
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('保存关系失败');
    expect(screen.getByText('编辑关系')).toBeInTheDocument();
  });

  it('prevents saving a relation with the same source and target character', async () => {
    const user = userEvent.setup();
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.selectOptions(screen.getByLabelText('目标角色'), '1');

    expect(screen.getByText('起点角色和目标角色不能相同。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
  });
});
