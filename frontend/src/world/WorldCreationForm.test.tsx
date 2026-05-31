import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WorldCreationForm } from './WorldCreationForm';

afterEach(() => cleanup());

describe('WorldCreationForm', () => {
  it('submits a custom world payload with starter assets', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={onCreateSample} />);

    await user.clear(screen.getByLabelText('世界标题'));
    await user.type(screen.getByLabelText('世界标题'), '自定义群星边境');
    await user.click(screen.getByRole('button', { name: '添加关系' }));
    await user.click(screen.getByRole('button', { name: '添加伏笔' }));
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(onCreate).toHaveBeenCalledOnce();
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({
      title: '自定义群星边境',
      starter_assets: expect.objectContaining({
        characters: expect.arrayContaining([expect.objectContaining({ name: expect.any(String), role_type: expect.any(String) })]),
        relations: expect.arrayContaining([expect.objectContaining({ source_index: 0, target_index: 1 })]),
        foreshadows: expect.arrayContaining([expect.objectContaining({ status: 'planted', urgency_level: expect.any(Number) })]),
      }),
    }));
  });

  it('calls the sample world shortcut without submitting the custom form', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onCreateSample = vi.fn().mockResolvedValue(undefined);
    render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={onCreateSample} />);

    await user.click(screen.getByRole('button', { name: '创建内置示例世界' }));

    expect(onCreateSample).toHaveBeenCalledOnce();
    expect(onCreate).not.toHaveBeenCalled();
  });
});
