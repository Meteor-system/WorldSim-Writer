import { useCallback, useLayoutEffect, useRef, useState } from 'react';

export type SelectionAction = 'polish' | 'rewrite' | 'expand' | 'condense' | 'custom';

type Props = {
  selection: { text: string; top: number; left: number };
  busy: boolean;
  disabled: boolean;
  onAction: (action: SelectionAction, instruction?: string) => void;
  onDismiss: () => void;
};

const ACTIONS: { key: SelectionAction; label: string }[] = [
  { key: 'polish', label: '润色' },
  { key: 'rewrite', label: '重写' },
  { key: 'expand', label: '扩写' },
  { key: 'condense', label: '缩写' },
  { key: 'custom', label: '自定义…' },
];

export function SelectionToolbar({ selection, busy, disabled, onAction, onDismiss }: Props) {
  const [customOpen, setCustomOpen] = useState(false);
  const [instruction, setInstruction] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useLayoutEffect(() => {
    setCustomOpen(false);
    setInstruction('');
  }, [selection.text]);

  useLayoutEffect(() => {
    if (customOpen) inputRef.current?.focus();
  }, [customOpen]);

  const handleCustom = useCallback(() => {
    const value = instruction.trim();
    if (!value) return;
    onAction('custom', value);
  }, [instruction, onAction]);

  return (
    <div
      className="selection-toolbar"
      style={{ top: selection.top, left: selection.left }}
      role="toolbar"
      aria-label="选中文本操作"
      onMouseDown={(event) => event.preventDefault()}
    >
      {customOpen ? (
        <div className="selection-toolbar-custom">
          <input
            ref={inputRef}
            value={instruction}
            onChange={(event) => setInstruction(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') handleCustom();
              if (event.key === 'Escape') onDismiss();
            }}
            placeholder="输入修改指令，回车确认"
            aria-label="自定义修改指令"
          />
          <button type="button" className="secondary-button" disabled={busy || disabled || !instruction.trim()} onClick={handleCustom}>
            确认
          </button>
          <button type="button" className="ghost-button" disabled={busy} onClick={onDismiss}>
            取消
          </button>
        </div>
      ) : (
        <div className="selection-toolbar-actions">
          {ACTIONS.map((action) => (
            <button
              key={action.key}
              type="button"
              className="selection-toolbar-button"
              disabled={busy || disabled}
              onClick={() => onAction(action.key)}
            >
              {busy ? '…' : action.label}
            </button>
          ))}
          <button type="button" className="selection-toolbar-button selection-toolbar-dismiss" disabled={busy} onClick={onDismiss} aria-label="关闭">
            ×
          </button>
        </div>
      )}
    </div>
  );
}
