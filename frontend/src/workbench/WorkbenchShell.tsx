import type { ReactNode } from 'react';

type Props = {
  topBar?: ReactNode;
  nav?: ReactNode;
  main: ReactNode;
  inspector?: ReactNode;
  overlay?: ReactNode;
  navLabel?: string;
  mainLabel?: string;
  inspectorLabel?: string;
  className?: string;
};

export function WorkbenchShell({
  topBar,
  nav,
  main,
  inspector,
  overlay,
  navLabel,
  mainLabel,
  inspectorLabel,
  className = '',
}: Props) {
  return (
    <section className={['workbench-shell', className].filter(Boolean).join(' ')}>
      {topBar}
      <div
        className={[
          'workbench-body',
          nav ? 'has-nav' : 'no-nav',
          inspector ? 'has-inspector' : 'no-inspector',
        ].join(' ')}
      >
        {nav ? (
          <aside className="workbench-nav studio-rail studio-navigation" role="region" aria-label={navLabel}>
            {nav}
          </aside>
        ) : null}
        <div className="workbench-main studio-main" role="region" aria-label={mainLabel}>
          {main}
        </div>
        {inspector ? (
          <aside className="workbench-inspector studio-rail studio-inspector" role="region" aria-label={inspectorLabel}>
            {inspector}
          </aside>
        ) : null}
      </div>
      {overlay}
    </section>
  );
}
