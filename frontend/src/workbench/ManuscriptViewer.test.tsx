import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ManuscriptViewer, splitParagraphs } from './ManuscriptViewer';

describe('ManuscriptViewer', () => {
  it('splits paragraphs on blank lines', () => {
    expect(splitParagraphs('第一段。\n\n第二段。\n\n')).toEqual(['第一段。', '第二段。']);
  });

  it('renders each paragraph with a data-paragraph index', () => {
    render(<ManuscriptViewer content={'第一段。\n\n第二段。'} editable busy={false} onReviseSelection={vi.fn()} />);
    expect(screen.getByText('第一段。')).toHaveAttribute('data-paragraph', '0');
    expect(screen.getByText('第二段。')).toHaveAttribute('data-paragraph', '1');
  });

  it('renders read-only mode without toolbar on selection', () => {
    render(<ManuscriptViewer content={'第一段。\n\n第二段。'} editable={false} busy={false} onReviseSelection={vi.fn()} />);
    expect(document.querySelector('.selection-toolbar')).toBeNull();
  });

  it('highlights the revised span', () => {
    render(
      <ManuscriptViewer
        content={'林砚停在雨巷口，玉佩发烫。'}
        editable
        busy={false}
        highlightedText="玉佩发烫"
        onReviseSelection={vi.fn()}
      />,
    );
    expect(screen.getByText('玉佩发烫')).toBeInTheDocument();
    expect(document.querySelector('mark.manuscript-highlight')).toBeInTheDocument();
  });
});
