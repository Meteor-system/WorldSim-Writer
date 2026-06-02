import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(process.cwd(), 'src/styles.css'), 'utf8');

describe('frontend motion utilities', () => {
  it('defines reusable motion and layered surface utilities', () => {
    expect(css).toContain('.motion-page-enter');
    expect(css).toContain('.motion-soft-lift');
    expect(css).toContain('.surface-layer');
    expect(css).toContain('.workspace-shell');
    expect(css).toContain('@keyframes page-rise');
  });

  it('disables animation, transition, and transform for reduced motion users', () => {
    const reducedMotionBlock = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce)'));

    expect(reducedMotionBlock).toContain('.motion-page-enter');
    expect(reducedMotionBlock).toContain('animation: none');
    expect(reducedMotionBlock).toContain('transition: none');
    expect(reducedMotionBlock).toContain('transform: none');
  });
});
