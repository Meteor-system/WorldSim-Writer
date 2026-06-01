import { useEffect, useState } from 'react';
import type { WorldMarkdownExportResponse, WorldSnapshotCompareResponse, WorldSnapshotListResponse, WorldSnapshotSummary } from '../api/types';

type Props = {
  onCreateSnapshot: () => Promise<WorldSnapshotSummary>;
  onExportMarkdown: () => Promise<WorldMarkdownExportResponse>;
  onListSnapshots: () => Promise<WorldSnapshotListResponse>;
  onCompareSnapshots: (baseSnapshotId: number, targetSnapshotId: number) => Promise<WorldSnapshotCompareResponse>;
};

function archiveUrlFromBase64(archiveBase64: string) {
  const binary = atob(archiveBase64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return URL.createObjectURL(new Blob([bytes], { type: 'application/zip' }));
}

export function WorldArchivePanel({ onCreateSnapshot, onExportMarkdown, onListSnapshots, onCompareSnapshots }: Props) {
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [snapshot, setSnapshot] = useState<WorldSnapshotSummary | null>(null);
  const [snapshotError, setSnapshotError] = useState('');
  const [exportLoading, setExportLoading] = useState(false);
  const [markdownExport, setMarkdownExport] = useState<WorldMarkdownExportResponse | null>(null);
  const [downloadUrl, setDownloadUrl] = useState('');
  const [selectedExportPath, setSelectedExportPath] = useState('');
  const [exportError, setExportError] = useState('');
  const [snapshotList, setSnapshotList] = useState<WorldSnapshotSummary[]>([]);
  const [snapshotListLoading, setSnapshotListLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');
  const [baseSnapshotId, setBaseSnapshotId] = useState('');
  const [targetSnapshotId, setTargetSnapshotId] = useState('');
  const [comparison, setComparison] = useState<WorldSnapshotCompareResponse | null>(null);

  useEffect(() => () => {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
  }, [downloadUrl]);

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
      const exported = await onExportMarkdown();
      const nextUrl = archiveUrlFromBase64(exported.archive_base64);
      setMarkdownExport(exported);
      setDownloadUrl(nextUrl);
      setSelectedExportPath(exported.files[0]?.path ?? '');
    } catch {
      setMarkdownExport(null);
      setDownloadUrl('');
      setSelectedExportPath('');
      setExportError('导出世界档案失败');
    } finally {
      setExportLoading(false);
    }
  }

  async function handleLoadSnapshots() {
    setSnapshotListLoading(true);
    setCompareError('');
    try {
      const response = await onListSnapshots();
      setSnapshotList(response.snapshots);
      setBaseSnapshotId(response.snapshots[0]?.id ? String(response.snapshots[0].id) : '');
      setTargetSnapshotId(response.snapshots[1]?.id ? String(response.snapshots[1].id) : '');
    } catch {
      setSnapshotList([]);
      setCompareError('加载快照列表失败');
    } finally {
      setSnapshotListLoading(false);
    }
  }

  async function handleCompareSnapshots() {
    if (!baseSnapshotId || !targetSnapshotId || baseSnapshotId === targetSnapshotId) return;
    setCompareLoading(true);
    setCompareError('');
    try {
      setComparison(await onCompareSnapshots(Number(baseSnapshotId), Number(targetSnapshotId)));
    } catch {
      setComparison(null);
      setCompareError('对比快照失败');
    } finally {
      setCompareLoading(false);
    }
  }

  const canCompare = Boolean(baseSnapshotId && targetSnapshotId && baseSnapshotId !== targetSnapshotId);
  const selectedExportFile = markdownExport?.files.find((file) => file.path === selectedExportPath) ?? markdownExport?.files[0] ?? null;

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
              <p className="font-black text-[#3b2511]">下载包已就绪</p>
              <p className="manuscript mt-1">导出成功：{markdownExport.files.length} 个 Markdown 文件已生成</p>
              <p className="mt-1 font-bold text-[#5e3b1c]">Archive：{markdownExport.archive_filename}</p>
              <p className="manuscript mt-1 text-sm">格式：{markdownExport.archive_format} · 编码：{markdownExport.archive_encoding} · 内联预览：{markdownExport.files_are_inline ? '是' : '否'}</p>
              <p className="manuscript mt-1 text-sm">世界版本：v{markdownExport.world_version} · 文件数：{markdownExport.files.length}</p>
              <p className="manuscript mt-1 text-sm">生成时间：{markdownExport.generated_at}</p>
              {downloadUrl && (
                <a className="secondary-button mt-3 inline-flex" href={downloadUrl} download={markdownExport.archive_filename}>
                  下载 Markdown ZIP
                </a>
              )}
              <ul className="mt-2 space-y-1 ink-muted">
                {markdownExport.files.map((file) => (
                  <li key={file.path}>{file.path}</li>
                ))}
              </ul>
              {markdownExport.files_are_inline && markdownExport.files.length > 0 && selectedExportFile && (
                <div className="mt-4 rounded-2xl bg-white/50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h4 className="font-black text-[#3b2511]">Markdown 预览</h4>
                    <label className="text-sm font-bold text-[#5e3b1c]">
                      选择预览文件
                      <select
                        className="paper-input mt-1"
                        aria-label="选择预览文件"
                        value={selectedExportFile.path}
                        onChange={(event) => setSelectedExportPath(event.target.value)}
                      >
                        {markdownExport.files.map((file) => (
                          <option key={file.path} value={file.path}>{file.path}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <pre className="manuscript mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-xl bg-amber-50/70 p-3 text-sm">{selectedExportFile.content}</pre>
                </div>
              )}
            </div>
          )}
          {!markdownExport && !exportError && <p className="ink-muted mt-2 text-sm">点击导出后会生成可下载 ZIP，并在下方显示内联 Markdown 预览；不会写入服务器文件系统。</p>}
        </div>
      </div>

      <div className="mt-4 rounded-2xl bg-white/35 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-[#5e3b1c]">快照对比</p>
            <p className="ink-muted mt-1 text-sm">选择两个只读快照，查看世界档案差异。</p>
          </div>
          <button className="secondary-button" disabled={snapshotListLoading} onClick={handleLoadSnapshots}>
            {snapshotListLoading ? '加载中...' : '加载快照列表'}
          </button>
        </div>
        {compareError && <p className="paper-error mt-3" role="alert">{compareError}</p>}
        <div className="mt-3 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          <label className="text-sm font-bold text-[#5e3b1c]">
            基准快照
            <select className="paper-input mt-1" value={baseSnapshotId} onChange={(event) => setBaseSnapshotId(event.target.value)}>
              <option value="">选择基准快照</option>
              {snapshotList.map((item) => (
                <option key={item.id} value={item.id}>#{item.id} · v{item.world_version} · {item.label ?? '未命名快照'}</option>
              ))}
            </select>
          </label>
          <label className="text-sm font-bold text-[#5e3b1c]">
            目标快照
            <select className="paper-input mt-1" value={targetSnapshotId} onChange={(event) => setTargetSnapshotId(event.target.value)}>
              <option value="">选择目标快照</option>
              {snapshotList.map((item) => (
                <option key={item.id} value={item.id}>#{item.id} · v{item.world_version} · {item.label ?? '未命名快照'}</option>
              ))}
            </select>
          </label>
          <button className="primary-button self-end" disabled={!canCompare || compareLoading} onClick={handleCompareSnapshots}>
            {compareLoading ? '对比中...' : '对比快照'}
          </button>
        </div>
        {comparison && (
          <div className="mt-4 space-y-3">
            <div className="rounded-2xl bg-amber-50/60 p-3">
              <p className="font-black text-[#3b2511]">v{comparison.base_snapshot.world_version} → v{comparison.target_snapshot.world_version}</p>
              <p className="manuscript mt-1 text-sm">总变更：{comparison.summary.total_changes}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(comparison.summary.object_type_counts).map(([objectType, count]) => (
                  <span key={objectType} className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-[#5e3b1c]">{objectType}：{count}</span>
                ))}
              </div>
            </div>
            {Object.entries(comparison.changes).flatMap(([group, changes]) => changes.map((change) => (
              <article key={`${group}-${change.object_type}-${change.object_id ?? change.title}`} className="rounded-2xl border border-amber-900/10 bg-white/50 p-3">
                <p className="text-sm font-black text-[#3b2511]">{change.title}</p>
                <p className="manuscript mt-1 text-sm">{change.object_type} · {change.change_type}</p>
                {change.fields_changed.length > 0 && <p className="manuscript mt-1 text-sm">字段：{change.fields_changed.join('、')}</p>}
              </article>
            )))}
          </div>
        )}
      </div>
    </article>
  );
}
