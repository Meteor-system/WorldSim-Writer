import { useCallback, useRef, useState } from 'react';
import { SelectionToolbar, type SelectionAction } from './SelectionToolbar';

type SelectionState = {
  text: string;
  paragraphIndex: number;
  top: number;
  left: number;
};

type Props = {
  content: string;
  editable: boolean;
  busy: boolean;
  highlightedText?: string | null;
  onReviseSelection: (paragraphIndex: number, mode: 'rewrite' | 'polish', instruction: string | undefined, selectionText: string) => void;
};

export function splitParagraphs(content: string): string[] {
  return content.split('\n\n').map((paragraph) => paragraph.trim()).filter(Boolean);
}

function findParagraphIndex(container: HTMLElement, target: Node): number {
  const paragraphs = Array.from(container.querySelectorAll('[data-paragraph]'));
  for (let i = 0; i < paragraphs.length; i += 1) {
    if (paragraphs[i].contains(target)) return i;
  }
  return -1;
}

export function ManuscriptViewer({ content, editable, busy, highlightedText, onReviseSelection }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<SelectionState | null>(null);

  const handleSelection = useCallback(() => {
    if (!editable) {
      setSelection(null);
      return;
    }
    const container = containerRef.current;
    if (!container) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) {
      setSelection(null);
      return;
    }
    const range = sel.getRangeAt(0);
    const text = range.toString().trim();
    if (!text || text.length > 800) {
      setSelection(null);
      return;
    }
    const paragraphIndex = findParagraphIndex(container, range.startContainer);
    if (paragraphIndex < 0) {
      setSelection(null);
      return;
    }
    const rect = range.getBoundingClientRect();
    const toolbarLeft = Math.max(8, rect.left + rect.width / 2 - 140);
    const toolbarTop = Math.max(4, rect.top - 52);
    setSelection({ text, paragraphIndex, top: toolbarTop, left: toolbarLeft });
  }, [editable]);

  const handleAction = useCallback(
    (action: SelectionAction, instruction?: string) => {
      if (!selection) return;
      const mode = action === 'rewrite' ? 'rewrite' : 'polish';
      onReviseSelection(selection.paragraphIndex, mode, instruction, selection.text);
      setSelection(null);
      window.getSelection()?.removeAllRanges();
    },
    [selection, onReviseSelection],
  );

  const dismiss = useCallback(() => {
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  }, []);

  const paragraphs = splitParagraphs(content);

  return (
    <div className="manuscript-viewer relative">
      <div
        ref={containerRef}
        className={editable ? 'manuscript-selectable' : 'manuscript-readonly'}
        onMouseUp={handleSelection}
        onKeyUp={(event) => {
          if (event.key === 'Shift') handleSelection();
        }}
      >
        {paragraphs.length === 0 && <p className="manuscript text-lg">正文尚未生成。</p>}
        {paragraphs.map((paragraph, index) => {
          let body: React.ReactNode = paragraph;
          if (highlightedText && paragraph.includes(highlightedText)) {
            const pieces = paragraph.split(highlightedText);
            body = (
              <>
                {pieces[0]}
                <mark className="manuscript-highlight">{highlightedText}</mark>
                {pieces[1]}
              </>
            );
          }
          return (
            <p key={`${index}-${paragraph.slice(0, 24)}`} data-paragraph={index} className="manuscript whitespace-pre-wrap text-lg leading-loose">
              {body}
            </p>
          );
        })}
      </div>
      {selection && (
        <SelectionToolbar selection={selection} busy={busy} disabled={!editable} onAction={handleAction} onDismiss={dismiss} />
      )}
    </div>
  );
}
