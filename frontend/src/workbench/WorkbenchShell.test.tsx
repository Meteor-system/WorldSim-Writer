import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { WorkbenchShell } from './WorkbenchShell';

describe('WorkbenchShell', () => {
  it('renders the three-pane workbench landmarks', () => {
    render(
      <WorkbenchShell
        navLabel="世界与章节导航"
        mainLabel="大纲与正文编辑"
        inspectorLabel="质量与 Canon 审批"
        nav={<p>导航</p>}
        main={<p>正文</p>}
        inspector={<button type="button">写入正史并更新世界</button>}
      />,
    );

    expect(screen.getByRole('region', { name: '世界与章节导航' })).toHaveTextContent('导航');
    expect(screen.getByRole('region', { name: '大纲与正文编辑' })).toHaveTextContent('正文');
    const inspector = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(inspector).toContainElement(screen.getByRole('button', { name: '写入正史并更新世界' }));
  });

  it('drops the inspector column when no inspector is provided', () => {
    const { container } = render(
      <WorkbenchShell
        navLabel="世界模块"
        mainLabel="世界内容"
        nav={<button type="button">世界概览</button>}
        main={<p>档案</p>}
      />,
    );

    expect(container.querySelector('.workbench-body')).toHaveClass('no-inspector');
    expect(container.querySelector('.workbench-inspector')).toBeNull();
    expect(screen.getByRole('button', { name: '世界概览' })).toBeInTheDocument();
  });
});
