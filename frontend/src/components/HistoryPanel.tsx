import { Clock3, Trash2 } from 'lucide-react';
import type { PipelineRecord } from '../types/pipeline';

interface HistoryPanelProps {
  items: PipelineRecord[];
  activeId?: string;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}

export function HistoryPanel({ items, activeId, onOpen, onDelete }: HistoryPanelProps) {
  return (
    <section className="rounded-lg border border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900">
      <div className="flex items-center gap-2 border-b border-ink-200 p-4 dark:border-ink-800">
        <Clock3 size={17} className="text-ink-500" />
        <h2 className="text-sm font-semibold uppercase tracking-normal text-ink-500 dark:text-ink-400">
          History
        </h2>
      </div>
      <div className="max-h-[380px] overflow-auto p-2">
        {items.length === 0 ? (
          <p className="p-3 text-sm text-ink-500 dark:text-ink-400">
            Previous generations will appear here.
          </p>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className={`rounded-lg border p-3 ${
                  item.id === activeId
                    ? 'border-signal-500 bg-signal-50 text-ink-950 dark:border-signal-400 dark:bg-ink-800 dark:text-ink-50'
                    : 'border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-950'
                }`}
              >
                <button
                  type="button"
                  onClick={() => onOpen(item.id)}
                  className="block w-full min-w-0 text-left"
                >
                  <h4 className="max-w-full truncate text-sm font-semibold">{item.title}</h4>
                  <span
                    className={`mt-1 block text-xs ${
                      item.id === activeId
                        ? 'text-ink-600 dark:text-ink-300'
                        : 'text-ink-500 dark:text-ink-400'
                    }`}
                  >
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </button>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <div className="flex min-w-0 flex-wrap gap-1">
                    {historyTags(item).map((tag, index) => (
                      <span
                        key={`${tag}-${index}`}
                        className={`rounded-md px-2 py-0.5 text-[11px] ${
                          item.id === activeId
                            ? 'bg-white/80 text-ink-700 dark:bg-ink-700 dark:text-ink-100'
                            : 'bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-300'
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => onDelete(item.id)}
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                    aria-label={`Delete ${item.title}`}
                    title="Delete design"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function historyTags(item: PipelineRecord) {
  const explicitTags = item.tags.filter(Boolean);
  if (explicitTags.length > 0) {
    return explicitTags.slice(0, 3);
  }

  const generatedTags = item.spec.aws_services
    .flatMap((service) => [service.name, service.category])
    .map(toTag)
    .filter(Boolean);

  const tags = unique(generatedTags).slice(0, 3);
  return tags.length > 0 ? tags : ['aws', 'pipeline'];
}

function toTag(value: string) {
  return value
    .toLowerCase()
    .replace(/^amazon\s+/, '')
    .replace(/^aws\s+/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

function unique(values: string[]) {
  return values.filter((value, index) => values.indexOf(value) === index);
}
