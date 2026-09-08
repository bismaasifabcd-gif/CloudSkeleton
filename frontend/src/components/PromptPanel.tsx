import { Loader2, Sparkles } from 'lucide-react';
import { samplePrompt } from '../lib/samplePrompt';

interface PromptPanelProps {
  description: string;
  title: string;
  tags: string;
  isLoading: boolean;
  onDescriptionChange: (value: string) => void;
  onTitleChange: (value: string) => void;
  onTagsChange: (value: string) => void;
  onGenerate: () => void;
}

export function PromptPanel({
  description,
  title,
  tags,
  isLoading,
  onDescriptionChange,
  onTitleChange,
  onTagsChange,
  onGenerate,
}: PromptPanelProps) {
  return (
    <section className="rounded-lg border border-ink-200 bg-white shadow-panel dark:border-ink-800 dark:bg-ink-900">
      <div className="border-b border-ink-200 p-4 dark:border-ink-800">
        <h2 className="text-sm font-semibold uppercase tracking-normal text-ink-500 dark:text-ink-400">
          Pipeline Description
        </h2>
      </div>
      <div className="space-y-4 p-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium">Design title</span>
          <input
            value={title}
            onChange={(event) => onTitleChange(event.target.value)}
            placeholder="FTP CSV to Athena"
            className="h-10 w-full rounded-lg border border-ink-200 bg-white px-3 text-sm outline-none focus:border-signal-600 focus:ring-2 focus:ring-signal-100 dark:border-ink-700 dark:bg-ink-950 dark:focus:ring-signal-700/30"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-sm font-medium">Natural language or structured prompt</span>
          <textarea
            value={description}
            onChange={(event) => onDescriptionChange(event.target.value)}
            rows={16}
            className="min-h-[360px] w-full resize-y rounded-lg border border-ink-200 bg-white p-3 text-sm leading-6 outline-none focus:border-signal-600 focus:ring-2 focus:ring-signal-100 dark:border-ink-700 dark:bg-ink-950 dark:focus:ring-signal-700/30"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-sm font-medium">Tags</span>
          <input
            value={tags}
            onChange={(event) => onTagsChange(event.target.value)}
            placeholder="ftp, csv, athena"
            className="h-10 w-full rounded-lg border border-ink-200 bg-white px-3 text-sm outline-none focus:border-signal-600 focus:ring-2 focus:ring-signal-100 dark:border-ink-700 dark:bg-ink-950 dark:focus:ring-signal-700/30"
          />
        </label>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => onDescriptionChange(samplePrompt)}
            className="h-10 rounded-lg border border-ink-200 px-3 text-sm font-medium text-ink-700 hover:bg-ink-100 dark:border-ink-700 dark:text-ink-200 dark:hover:bg-ink-800"
          >
            Load sample
          </button>
          <button
            type="button"
            onClick={onGenerate}
            disabled={isLoading || description.trim().length < 20}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-signal-600 px-3 text-sm font-semibold text-white hover:bg-signal-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? (
              <Loader2 size={17} className="animate-spin" />
            ) : (
              <Sparkles size={17} />
            )}
            Generate
          </button>
        </div>
      </div>
    </section>
  );
}
