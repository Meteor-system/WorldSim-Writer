import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Character, CharacterRelation } from '../api/types';
import { RelationManager } from './RelationManager';

vi.mock('../api/client', () => ({
  getRelations: vi.fn(async () => ([
    { id: 1, source_character_id: 1, target_character_id: 2, relation_type: 'uneasy_alliance', intensity: 2, visibility: 'public' },
  ] satisfies CharacterRelation[])),
  createRelation: vi.fn(),
  updateRelation: vi.fn(),
  deleteRelation: vi.fn(),
}));

const characters: Character[] = [
  { id: 1, name: '林砚', role_type: 'protagonist', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
  { id: 2, name: '沈微霜', role_type: 'ally', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
];

describe('RelationManager', () => {
  it('renders relationship cards with character names and edit reason affordance', async () => {
    render(<RelationManager worldId={7} characters={characters} />);

    expect(await screen.findByText('林砚 → 沈微霜')).toBeInTheDocument();
    expect(screen.getByText('关系：uneasy_alliance')).toBeInTheDocument();
    expect(screen.getByText('强度：2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();
  });
});
