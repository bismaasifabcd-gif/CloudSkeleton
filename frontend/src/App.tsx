import { useEffect, useMemo, useState } from 'react';
import { ArchitectureDiagram } from './components/diagram/ArchitectureDiagram';
import { HistoryPanel } from './components/HistoryPanel';
import { MetricStrip } from './components/MetricStrip';
import { PromptPanel } from './components/PromptPanel';
import { Shell } from './components/layout/Shell';
import { SpecPanel } from './components/SpecPanel';
import { StatusBanner } from './components/StatusBanner';
import { useTheme } from './hooks/useTheme';
import { api, downloadText } from './lib/api';
import { samplePrompt } from './lib/samplePrompt';
import type { PipelineRecord } from './types/pipeline';

const defaultUserId = import.meta.env.VITE_DEFAULT_USER_ID ?? 'anonymous';

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [description, setDescription] = useState(samplePrompt);
  const [title, setTitle] = useState('FTP CSV to Athena');
  const [tags, setTags] = useState('ftp, csv, athena');
  const [activeRecord, setActiveRecord] = useState<PipelineRecord | undefined>();
  const [history, setHistory] = useState<PipelineRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<{ tone: 'error' | 'success' | 'warning'; message: string }>();

  const parsedTags = useMemo(
    () =>
      tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean)
        .slice(0, 12),
    [tags],
  );

  useEffect(() => {
    void refreshHistory();
  }, []);

  async function refreshHistory() {
    try {
      const response = await api.listHistory(defaultUserId);
      setHistory(response.items);
    } catch (error) {
      setStatus({ tone: 'warning', message: error instanceof Error ? error.message : 'History could not be loaded.' });
    }
  }

  async function handleGenerate() {
    setIsLoading(true);
    setStatus(undefined);
    try {
      const record = await api.generatePipeline({
        description,
        title: title.trim() || undefined,
        user_id: defaultUserId,
        tags: parsedTags,
      });
      setActiveRecord(record);
      setHistory((current) => [record, ...current.filter((item) => item.id !== record.id)]);
      setStatus({ tone: 'success', message: 'Pipeline design generated and saved to history.' });
    } catch (error) {
      setStatus({
        tone: 'error',
        message: error instanceof Error ? error.message : 'Pipeline generation failed.',
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOpen(id: string) {
    setStatus(undefined);
    try {
      const record = await api.getPipeline(id);
      setActiveRecord(record);
      setDescription(record.description);
      setTitle(record.title);
      setTags(record.tags.join(', '));
    } catch (error) {
      setStatus({ tone: 'error', message: error instanceof Error ? error.message : 'Could not open design.' });
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deletePipeline(id);
      setHistory((current) => current.filter((item) => item.id !== id));
      if (activeRecord?.id === id) {
        setActiveRecord(undefined);
      }
      setStatus({ tone: 'success', message: 'Design removed from history.' });
    } catch (error) {
      setStatus({ tone: 'error', message: error instanceof Error ? error.message : 'Could not delete design.' });
    }
  }

  async function handleExportMarkdown() {
    if (!activeRecord) {
      return;
    }
    try {
      const response = await api.exportMarkdown(activeRecord.id);
      downloadText(response.filename, String(response.content), response.content_type);
      setStatus({ tone: 'success', message: 'Markdown export downloaded.' });
    } catch (error) {
      setStatus({ tone: 'error', message: error instanceof Error ? error.message : 'Markdown export failed.' });
    }
  }

  async function handleExportJson() {
    if (!activeRecord) {
      return;
    }
    try {
      const response = await api.exportJson(activeRecord.id);
      downloadText(
        response.filename,
        JSON.stringify(response.content, null, 2),
        response.content_type,
      );
      setStatus({ tone: 'success', message: 'JSON export downloaded.' });
    } catch (error) {
      setStatus({ tone: 'error', message: error instanceof Error ? error.message : 'JSON export failed.' });
    }
  }

  return (
    <Shell isDark={theme === 'dark'} onToggleTheme={toggleTheme}>
      <div className="grid gap-4 xl:grid-cols-[430px_minmax(0,1fr)]">
        <div className="space-y-4">
          <PromptPanel
            description={description}
            title={title}
            tags={tags}
            isLoading={isLoading}
            onDescriptionChange={setDescription}
            onTitleChange={setTitle}
            onTagsChange={setTags}
            onGenerate={handleGenerate}
          />
          <HistoryPanel
            items={history}
            activeId={activeRecord?.id}
            onOpen={handleOpen}
            onDelete={handleDelete}
          />
        </div>

        <div className="space-y-4">
          <StatusBanner message={status?.message} tone={status?.tone ?? 'success'} />
          <MetricStrip record={activeRecord} />
          <ArchitectureDiagram diagram={activeRecord?.spec.diagram} />
          <SpecPanel
            record={activeRecord}
            onExportMarkdown={handleExportMarkdown}
            onExportJson={handleExportJson}
          />
        </div>
      </div>
    </Shell>
  );
}
