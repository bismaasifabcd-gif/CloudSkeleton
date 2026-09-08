import type { NodeProps } from 'reactflow';
import { Handle, Position } from 'reactflow';
import { ServiceIcon } from '../ServiceIcon';

interface PipelineNodeData {
  label: string;
  category: string;
  service?: string | null;
  description?: string | null;
}

export function PipelineNode({ data }: NodeProps<PipelineNodeData>) {
  return (
    <div className="w-[220px] rounded-lg border border-ink-200 bg-white p-3 shadow-panel dark:border-ink-700 dark:bg-ink-900">
      <Handle type="target" position={Position.Left} className="!bg-signal-600" />
      <div className="flex items-start gap-3">
        <ServiceIcon service={data.service} category={data.category} />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink-950 dark:text-ink-50">
            {data.label}
          </p>
          <p className="mt-1 break-words text-xs font-medium text-signal-700 dark:text-signal-100">
            {data.service || data.category}
          </p>
        </div>
      </div>
      {data.description ? (
        <p className="mt-2 line-clamp-2 text-xs leading-5 text-ink-500 dark:text-ink-400">
          {data.description}
        </p>
      ) : null}
      <Handle type="source" position={Position.Right} className="!bg-signal-600" />
    </div>
  );
}
