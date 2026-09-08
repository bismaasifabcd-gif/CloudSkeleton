import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface StatusBannerProps {
  message?: string;
  tone: 'error' | 'success' | 'warning';
}

export function StatusBanner({ message, tone }: StatusBannerProps) {
  if (!message) {
    return null;
  }

  const styles =
    tone === 'error'
      ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200'
      : tone === 'warning'
        ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200'
        : 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200';

  return (
    <div className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${styles}`}>
      {tone === 'success' ? (
        <CheckCircle2 size={17} className="mt-0.5 shrink-0" />
      ) : (
        <AlertTriangle size={17} className="mt-0.5 shrink-0" />
      )}
      <span>{message}</span>
    </div>
  );
}
