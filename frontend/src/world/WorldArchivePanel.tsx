import { useState } from 'react';
import type { WorldMarkdownExportResponse, WorldSnapshotSummary } from '../api/types';

type Props = {
  onCreateSnapshot: () => Promise<WorldSnapshotSummary>;
  onExportMarkdown: () => Promise<WorldMarkdownExportResponse>;
};

export function WorldArchivePanel({ onCreateSnapshot, onExportMarkdown }: Props) {
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [snapshot, setSnapshot] = useState<WorldSnapshotSummary | null>(null);
  const [snapshotError, setSnapshotError] = useState('');
  const [exportLoading, setExportLoading] = useState(false);
  const [markdownExport, setMarkdownExport] = useState<WorldMarkdownExportResponse | null>(null);
  const [exportError, setExportError] = useState('');

  async function handleCreateSnapshot() {
    setSnapshotLoading(true);
    setSnapshotError('');
    try {
      setSnapshot(await onCreateSnapshot());
    } catch {
      setSnapshot(null);
      setSnapshotError('创建快照失败');
    } finally {
      setSnapshotLoading(false);
    }
  }

  async function handleExportMarkdown() {
    setExportLoading(true);
    setExportError('');
    try {
      setMarkdownExport(await onExportMarkdown());
    } catch {
      setMarkdownExport(null);
      setExportError('导出世界档案失败');
    } finally {
      setExportLoading(false);
    }
  }

  return (
    <article className="book-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">Archive</p>
          <h3 className="mt-2 text-2xl font-black text-[#34210f]">World Archive</h3>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">创建当前世界版本的只读快照，或生成 Obsidian 风格 Markdown 档案。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="secondary-button" disabled={snapshotLoading} onClick={handleCreateSnapshot}>
            {snapshotLoading ? '创建中...' : '创建世界快照'}
          </button>
          <button className="primary-button" disabled={exportLoading} onClick={handleExportMarkdown}>
            {exportLoading ? '导出中...' : '导出世界档案'}
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">世界快照</p>
          {snapshotError && <p className="paper-error mt-2" role="alert">{snapshotError}</p>}
          {snapshot && (
            <div className="manuscript mt-2 text-sm">
              <p>快照已创建：版本 {snapshot.world_version}</p>
              <p>Snapshot #{snapshot.id}</p>
              <p className="ink-muted">{snapshot.created_at}</p>
            </div>
          )}
          {!snapshot && !snapshotError && <p className="ink-muted mt-2 text-sm">尚未创建本次快照。</p>}
        </div>

        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">Markdown 导出</p>
          {exportError && <p className="paper-error mt-2" role="alert">{exportError}</p>}
          {markdownExport && (
            <div className="mt-2 text-sm">
              <p className="manuscript">导出成功：{markdownExport.files.length} 个 Markdown 文件已生成</p>
              <ul className="mt-2 space-y-1 ink-muted">
                {markdownExport.files.map((file) => (
                  <li key={file.path}>{file.path}</li>
                ))}
              </ul>
            </div>
          )}
          {!markdownExport && !exportError && <p className="ink-muted mt-2 text-sm">导出只返回文本，不写入服务器文件系统。</p>}
        </div>
      </div>
    </article>
  );
}
