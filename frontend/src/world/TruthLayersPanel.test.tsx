import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { updateWorldTruthLayers } from '../api/client';
import type { WorldOverview } from '../api/types';
import { TruthLayersPanel } from './TruthLayersPanel';

vi.mock('../api/client', () => ({
  updateWorldTruthLayers: vi.fn(),
}));

const world = {
  id: 7,
  title: '青岚城',
  genre_template: 'mystery',
  truth_canon: '公开正史',
  truth_layers: [
    { id: 'layer-1', title: '表层', content: '城主府公开记录', reveal_at_chapter: 0, frozen: false },
    { id: 'layer-2', title: '深层', content: '湿信来自旧朝', reveal_at_chapter: 4, frozen: true },
  ],
  truth_canon_version: 1,
  world_version: 1,
  status: 'active',
  tone_profile: {},
  current_characters: [],
  current_foreshadows: [],
  current_relations: [],
  characters: [],
  relations: [],
  foreshadows: [],
  recent_events: [],
  story_arc: [],
  approved_chapter_count: 0,
} as WorldOverview;

afterEach(() => cleanup());

beforeEach(() => {
  vi.mocked(updateWorldTruthLayers).mockReset().mockResolvedValue(world);
});

describe('TruthLayersPanel', () => {
  it('keeps frozen layers read-only and saves unfrozen edits', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<TruthLayersPanel world={world} onChanged={onChanged} />);

    expect(screen.getByDisplayValue('湿信来自旧朝')).toBeDisabled();
    const surface = screen.getByDisplayValue('城主府公开记录');
    expect(surface).toBeEnabled();
    await user.clear(surface);
    await user.type(surface, '城主府只公开雨巷异动');
    await user.click(screen.getByRole('button', { name: '保存真相层' }));

    await waitFor(() => expect(updateWorldTruthLayers).toHaveBeenCalled());
    const payload = vi.mocked(updateWorldTruthLayers).mock.calls[0][1];
    expect(payload.truth_layers[0].content).toContain('城主府只公开雨巷异动');
    expect(payload.truth_layers[1].content).toBe('湿信来自旧朝');
    expect(onChanged).toHaveBeenCalledTimes(1);
  });
});
