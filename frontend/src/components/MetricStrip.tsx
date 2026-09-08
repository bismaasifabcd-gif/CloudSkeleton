import { Boxes, GitBranch, ShieldCheck, WalletCards } from 'lucide-react';
import type { PipelineRecord } from '../types/pipeline';

interface MetricStripProps {
  record?: PipelineRecord;
}

export function MetricStrip({ record }: MetricStripProps) {
  const metrics = [
    {
      label: 'Services',
      value: record?.spec.aws_services.length ?? 0,
      icon: Boxes,
    },
    {
      label: 'Workflow steps',
      value: record?.spec.workflow.length ?? 0,
      icon: GitBranch,
    },
    {
      label: 'Security controls',
      value: record?.spec.security_best_practices.length ?? 0,
      icon: ShieldCheck,
    },
    {
      label: 'Cost levers',
      value: record?.spec.cost_optimization.length ?? 0,
      icon: WalletCards,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.label}
            className="rounded-lg border border-ink-200 bg-white p-3 dark:border-ink-800 dark:bg-ink-900"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-medium uppercase tracking-normal text-ink-500 dark:text-ink-400">
                {metric.label}
              </span>
              <Icon size={17} className="text-signal-600" />
            </div>
            <p className="mt-2 text-2xl font-semibold">{metric.value}</p>
          </div>
        );
      })}
    </div>
  );
}
