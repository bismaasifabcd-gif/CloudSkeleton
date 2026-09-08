import { DatabaseZap, Moon, Sun } from 'lucide-react';

interface ShellProps {
  children: React.ReactNode;
  isDark: boolean;
  onToggleTheme: () => void;
}

export function Shell({ children, isDark, onToggleTheme }: ShellProps) {
  return (
    <div className="min-h-screen bg-ink-50 text-ink-950 transition-colors dark:bg-ink-950 dark:text-ink-50">
      <header className="sticky top-0 z-30 border-b border-ink-200/80 bg-white/90 backdrop-blur dark:border-ink-800 dark:bg-ink-950/95">
        <div className="mx-auto flex max-w-[1800px] items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-aws-deep text-aws-orange">
              <DatabaseZap size={21} aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold tracking-normal sm:text-lg">
                AI Data Pipeline Generator
              </h1>
              <p className="truncate text-xs text-ink-500 dark:text-ink-400">
                AWS architecture design workspace
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onToggleTheme}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-ink-200 bg-white text-ink-700 hover:bg-ink-100 dark:border-ink-700 dark:bg-ink-900 dark:text-ink-100 dark:hover:bg-ink-800"
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-[1800px] px-4 py-4 sm:px-6 sm:py-6">
        {children}
      </main>
    </div>
  );
}
