# One-Sentence World Entry Autofill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a frontend one-sentence story/world entry that calls `POST /worlds/brief/expand`, fills the existing world creation form with the returned draft, and keeps world creation behind the existing explicit create action.

**Architecture:** Extend the existing frontend API types/client with a small typed helper, pass that helper from `WorldPage` into `WorldCreationForm`, and add an inline Chinese “一句话开书” panel above the existing editable form fields. The panel manages only local draft-generation UI state; the existing `onCreate(form)` submit remains the only path that creates a world.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify: `frontend/src/api/types.ts`
  - Add `WorldBriefExpandRequest` and `WorldBriefExpandResponse` next to `WorldCreateRequest`.
- Modify: `frontend/src/api/client.ts`
  - Import the new types and add `expandWorldBrief(data)` using `/worlds/brief/expand`.
- Modify: `frontend/src/world/WorldCreationForm.tsx`
  - Add optional `onExpandBrief` prop.
  - Add local brief, loading, error, success, rationale/notes, and cancel-token state.
  - Fill `form` from `response.payload` on success.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Import `expandWorldBrief` and pass it to `WorldCreationForm`.
- Modify: `frontend/src/api/client.test.ts`
  - Test the new API helper path and payload.
- Modify: `frontend/src/world/WorldCreationForm.test.tsx`
  - Add RED tests for rendering, autofill, error copy, cancel state, and no world creation before confirm.

---

### Task 1: Add RED API helper test

**Files:**
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing test**

Add `expandWorldBrief` to the import list and add this test under `describe('world creation API helpers', ...)`:

```ts
it('calls the one-sentence world draft endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
    payload: {
      title: '死因王国',
      genre_template: 'political_fantasy',
      truth_canon: '每个人出生时都会被分配未来死因。',
      starter_assets: { characters: [{ name: '莉塔', role_type: 'protagonist' }], relations: [], foreshadows: [] },
    },
    rationale: '从一句话补全世界草稿。',
    assumptions: ['主角需要接触制度。'],
    safety_notes: ['不会自动创建世界。'],
  }));
  vi.stubGlobal('fetch', fetchMock);

  const response = await expandWorldBrief({ brief: '一个所有人出生时都会被分配未来死因的王国' });

  expect(fetchMock).toHaveBeenCalledWith(
    'http://localhost:8000/worlds/brief/expand',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ brief: '一个所有人出生时都会被分配未来死因的王国' }),
    }),
  );
  expect(response.payload.title).toBe('死因王国');
  expect(response.safety_notes).toEqual(['不会自动创建世界。']);
});
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts --run
```

Expected: FAIL because `expandWorldBrief` is not exported/imported yet.

---

### Task 2: Add RED WorldCreationForm tests

**Files:**
- Modify: `frontend/src/world/WorldCreationForm.test.tsx`

- [ ] **Step 1: Add draft fixture**

Add a `briefDraftPayload` fixture after `seedPayload`:

```ts
const briefDraftPayload: WorldCreateRequest = {
  title: '死因王国',
  genre_template: 'political_fantasy',
  truth_canon: '赫洛王国会在每个孩子出生时分配未来死因，命簿最近出现空白页。',
  tone_profile: { style: '政治奇幻', pacing: '制度压力与个人选择交替推进' },
  starter_assets: {
    characters: [
      { name: '莉塔', role_type: 'protagonist', status: '命簿抄录员', public_profile: { identity: '命簿抄录员', skill: '解读死因文书' }, hidden_traits: { secret: '她的死因栏是空白' }, destiny_flag: '空白死因持有者', current_goals: ['查清空白死因'] },
      { name: '维克托公爵', role_type: 'rival', status: '荣耀死因贵族', public_profile: { identity: '王国公爵', skill: '操控命簿审判' }, hidden_traits: { secret: '他的荣耀死因被篡改过' }, current_goals: ['夺回空白命簿页'] },
    ],
    relations: [{ source_index: 0, target_index: 1, relation_type: 'rival', intensity: 4, visibility: 'public' }],
    foreshadows: [{ title: '空白命簿页', description: '命簿中出现没有名字也没有死因的空白页。', foreshadow_type: 'fate_clue', status: 'planted', urgency_level: 4, related_character_indexes: [0, 1], expected_resolution_window: '第2-5章' }],
  },
};
```

- [ ] **Step 2: Add failing render/autofill/error/cancel tests**

Add tests inside `describe('WorldCreationForm', ...)`:

```ts
it('renders a one-sentence story entry with canon safety copy', () => {
  render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={vi.fn()} />);

  expect(screen.getByRole('heading', { name: '一句话开书' })).toBeInTheDocument();
  expect(screen.getByLabelText('一句话故事想法')).toBeInTheDocument();
  expect(screen.getByText('生成草稿只会填入下方表单，不会创建世界，也不会写入正史。')).toBeInTheDocument();
});

it('fills the editable form from a one-sentence draft without creating a world', async () => {
  const user = userEvent.setup();
  const onCreate = vi.fn().mockResolvedValue(undefined);
  const onExpandBrief = vi.fn().mockResolvedValue({
    payload: briefDraftPayload,
    rationale: '从死因制度补全政治奇幻世界。',
    assumptions: ['主角需要能接触命簿制度。'],
    safety_notes: ['这是原创世界创建草稿，不会自动创建世界或写入正史。'],
  });
  render(<WorldCreationForm creating={false} onCreate={onCreate} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

  await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配未来死因的王国');
  await user.click(screen.getByRole('button', { name: '生成创建草稿' }));

  expect(onExpandBrief).toHaveBeenCalledWith({ brief: '一个所有人出生时都会被分配未来死因的王国' });
  expect(screen.getByLabelText('世界标题')).toHaveValue('死因王国');
  expect(screen.getByLabelText('叙事风格')).toHaveValue('政治奇幻');
  expect(screen.getByLabelText('真理库 / 世界底层设定')).toHaveValue(expect.stringContaining('命簿最近出现空白页'));
  expect(screen.getByDisplayValue('莉塔')).toBeInTheDocument();
  expect(screen.getByText('草稿已填入下方表单。请检查标题、设定、角色和伏笔，确认后再创建世界。')).toBeInTheDocument();
  expect(screen.getByText('现在还没有创建世界，也没有写入正史。只有点击“创建自定义世界”后才会创建。')).toBeInTheDocument();
  expect(screen.getByText('从死因制度补全政治奇幻世界。')).toBeInTheDocument();
  expect(screen.getByText('主角需要能接触命簿制度。')).toBeInTheDocument();
  expect(screen.getByText('这是原创世界创建草稿，不会自动创建世界或写入正史。')).toBeInTheDocument();
  expect(onCreate).not.toHaveBeenCalled();
});

it('shows a friendly retry message when brief expansion fails and keeps current form data', async () => {
  const user = userEvent.setup();
  const onExpandBrief = vi.fn().mockRejectedValue(new Error('PROTECTED_REFERENCE_TERMS'));
  render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

  await user.clear(screen.getByLabelText('世界标题'));
  await user.type(screen.getByLabelText('世界标题'), '手动保留标题');
  await user.type(screen.getByLabelText('一句话故事想法'), '一个魔法学校里的少年冒险故事');
  await user.click(screen.getByRole('button', { name: '生成创建草稿' }));

  expect(screen.getByRole('alert')).toHaveTextContent('草稿里可能包含受保护作品的专有名称或设定，请换成更原创的一句话后重试。');
  expect(screen.getByLabelText('世界标题')).toHaveValue('手动保留标题');
});

it('can cancel a pending one-sentence draft request', async () => {
  const user = userEvent.setup();
  let resolveDraft: (value: { payload: WorldCreateRequest }) => void = () => undefined;
  const onExpandBrief = vi.fn().mockReturnValue(new Promise((resolve) => { resolveDraft = resolve; }));
  render(<WorldCreationForm creating={false} onCreate={vi.fn()} onCreateSample={vi.fn()} onExpandBrief={onExpandBrief} />);

  await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配未来死因的王国');
  await user.click(screen.getByRole('button', { name: '生成创建草稿' }));
  expect(screen.getByRole('button', { name: '取消生成' })).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '取消生成' }));
  resolveDraft({ payload: briefDraftPayload });

  expect(await screen.findByLabelText('世界标题')).not.toHaveValue('死因王国');
  expect(screen.getByText('已取消生成，可以修改一句话后重新尝试。')).toBeInTheDocument();
});
```

- [ ] **Step 3: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: FAIL because `onExpandBrief` prop and the brief panel do not exist.

---

### Task 3: Implement typed API helper

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add types in `types.ts`**

Insert after `WorldCreateRequest`:

```ts
export type WorldBriefExpandRequest = {
  brief: string;
};

export type WorldBriefExpandResponse = {
  payload: WorldCreateRequest;
  rationale?: string;
  assumptions?: string[];
  safety_notes?: string[];
};
```

- [ ] **Step 2: Add client import and helper**

In `client.ts`, import `WorldBriefExpandRequest` and `WorldBriefExpandResponse`. Add after `createSampleWorld()`:

```ts
export function expandWorldBrief(data: WorldBriefExpandRequest) {
  return apiRequest<WorldBriefExpandResponse>('/worlds/brief/expand', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 3: Run API helper test**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts --run
```

Expected: PASS for the API helper file.

---

### Task 4: Implement WorldCreationForm brief panel

**Files:**
- Modify: `frontend/src/world/WorldCreationForm.tsx`

- [ ] **Step 1: Extend props**

Import `useRef` and `WorldBriefExpandResponse`, add prop:

```ts
onExpandBrief?: (data: { brief: string }) => Promise<WorldBriefExpandResponse>;
```

- [ ] **Step 2: Add local state**

Inside the component add:

```ts
const [brief, setBrief] = useState('');
const [briefLoading, setBriefLoading] = useState(false);
const [briefError, setBriefError] = useState('');
const [briefSuccess, setBriefSuccess] = useState('');
const [briefNotes, setBriefNotes] = useState<Pick<WorldBriefExpandResponse, 'rationale' | 'assumptions' | 'safety_notes'>>({});
const briefRequestIdRef = useRef(0);
```

- [ ] **Step 3: Add helper functions**

Add:

```ts
function friendlyBriefError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (message.includes('PROTECTED_REFERENCE_TERMS')) return '草稿里可能包含受保护作品的专有名称或设定，请换成更原创的一句话后重试。';
  if (message.includes('brief') || message.includes('too short') || message.includes('String should have at least')) return '请写得再具体一点，比如一句包含主角、世界规则或核心冲突的话。';
  return '草稿生成失败，请稍后重试，或先用模板手动创建。';
}

async function submitBriefDraft() {
  if (!onExpandBrief || briefLoading) return;
  const trimmed = brief.trim();
  if (trimmed.length < 6) {
    setBriefError('请写得再具体一点，比如一句包含主角、世界规则或核心冲突的话。');
    setBriefSuccess('');
    setBriefNotes({});
    return;
  }
  const requestId = briefRequestIdRef.current + 1;
  briefRequestIdRef.current = requestId;
  setBriefLoading(true);
  setBriefError('');
  setBriefSuccess('');
  setBriefNotes({});
  try {
    const response = await onExpandBrief({ brief: trimmed });
    if (briefRequestIdRef.current !== requestId) return;
    setSelectedPresetKey('');
    setActiveSeedKey(null);
    setForm(JSON.parse(JSON.stringify(response.payload)) as WorldCreateRequest);
    setBriefNotes({ rationale: response.rationale, assumptions: response.assumptions, safety_notes: response.safety_notes });
    setBriefSuccess('草稿已填入下方表单。请检查标题、设定、角色和伏笔，确认后再创建世界。');
  } catch (error) {
    if (briefRequestIdRef.current !== requestId) return;
    setBriefError(friendlyBriefError(error));
  } finally {
    if (briefRequestIdRef.current === requestId) setBriefLoading(false);
  }
}

function cancelBriefDraft() {
  briefRequestIdRef.current += 1;
  setBriefLoading(false);
  setBriefError('');
  setBriefSuccess('已取消生成，可以修改一句话后重新尝试。');
  setBriefNotes({});
}
```

- [ ] **Step 4: Render panel above seed library**

Add a section after the “创建世界工坊” heading block and before seed library:

```tsx
<section className="book-card mt-8 p-5" data-testid="brief-world-entry-panel">
  <div className="flex flex-wrap items-start justify-between gap-3">
    <div>
      <p className="chapter-kicker">一句话创建故事世界</p>
      <h2 className="mt-2 text-2xl font-black text-[#34210f]">一句话开书</h2>
      <p className="manuscript mt-2 text-sm text-[#5e3b1c]">写下一个故事点子，系统会生成可编辑的创建草稿。</p>
      <p className="manuscript mt-1 text-sm font-bold text-[#5e3b1c]">生成草稿只会填入下方表单，不会创建世界，也不会写入正史。</p>
    </div>
  </div>
  <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
    <label className="block">
      <span className="text-sm font-semibold text-[#4a321e]">一句话故事想法</span>
      <textarea
        className="mt-1 min-h-24 w-full rounded-2xl border border-amber-900/20 bg-white/70 px-4 py-3"
        value={brief}
        onChange={(event) => setBrief(event.target.value)}
        placeholder="例如：一个所有人出生时都会被分配未来死因的王国"
        disabled={briefLoading}
      />
    </label>
    <div className="flex items-end gap-2">
      <button className="primary-button" type="button" disabled={briefLoading || !onExpandBrief} onClick={() => void submitBriefDraft()}>
        {briefLoading ? '正在生成可编辑草稿…' : '生成创建草稿'}
      </button>
      {briefLoading && <button className="secondary-button" type="button" onClick={cancelBriefDraft}>取消生成</button>}
    </div>
  </div>
  {briefError && <p className="paper-error mt-4 text-left" role="alert">{briefError}</p>}
  {briefSuccess && (
    <section className="mt-4 rounded-2xl bg-amber-50/70 p-4" aria-live="polite">
      <p className="font-black text-[#3b2511]">{briefSuccess}</p>
      <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">现在还没有创建世界，也没有写入正史。只有点击“创建自定义世界”后才会创建。</p>
      {briefNotes.rationale && <p className="manuscript mt-3 text-sm">{briefNotes.rationale}</p>}
      {(briefNotes.assumptions?.length ?? 0) > 0 && (
        <div className="mt-3">
          <p className="text-sm font-bold text-[#5e3b1c]">草稿补全时采用的假设</p>
          <ul className="manuscript mt-1 list-disc space-y-1 pl-5 text-sm">{briefNotes.assumptions?.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      )}
      {(briefNotes.safety_notes?.length ?? 0) > 0 && (
        <div className="mt-3">
          <p className="text-sm font-bold text-[#5e3b1c]">安全提示</p>
          <ul className="manuscript mt-1 list-disc space-y-1 pl-5 text-sm">{briefNotes.safety_notes?.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      )}
    </section>
  )}
</section>
```

- [ ] **Step 5: Run form test**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: PASS for the form file.

---

### Task 5: Wire WorldPage

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Import and pass helper**

Add `expandWorldBrief` to the API import block and pass it to `WorldCreationForm`:

```tsx
<WorldCreationForm
  creating={creating}
  onCreate={submitWorld}
  onCreateSample={submitSampleWorld}
  onExpandBrief={expandWorldBrief}
  seeds={seedLibrary}
  seedLoading={seedLibraryLoading}
  seedError={seedLibraryError}
  onLoadSeed={getWorldSeed}
  onCreateSeed={submitSeedWorld}
/>
```

- [ ] **Step 2: Run targeted frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx --run
```

Expected: PASS.

---

### Task 6: Final verification and commit

**Files:**
- All modified frontend files and this plan file.

- [ ] **Step 1: Full frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
```

Expected: PASS.

- [ ] **Step 2: Frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 3: Diff check**

Run:

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 4: Inspect diff/status**

Run:

```bash
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer diff -- frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldCreationForm.tsx frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldPage.tsx docs/superpowers/plans/2026-06-07-one-sentence-world-entry-autofill.md
```

Expected: only MVP Next-2 scoped changes.

- [ ] **Step 5: Staged diff check and commit**

Run:

```bash
git -C /opt/WorldSim-Writer add frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldCreationForm.tsx frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldPage.tsx docs/superpowers/plans/2026-06-07-one-sentence-world-entry-autofill.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: add one-sentence world creation autofill"
```

Expected: commit succeeds. Do not push. Do not merge.

---

## Plan Self-Review

- Spec coverage: Covers frontend type/client support, Chinese UI entry, endpoint call, form autofill, rationale/assumption/safety display, loading/error/cancel/retry states, canon boundary copy, no auto-create, tests, build, diff check, commit.
- Placeholder scan: No placeholders remain.
- Type consistency: `WorldBriefExpandRequest`, `WorldBriefExpandResponse`, `expandWorldBrief`, and `onExpandBrief` names are consistent across tasks.
- Scope: Frontend only. Backend contracts are consumed but not changed, so backend tests are not required unless implementation touches backend files.
