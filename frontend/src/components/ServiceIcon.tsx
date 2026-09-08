import {
  Activity,
  Braces,
  CloudCog,
  Database,
  FileInput,
  GitBranch,
  KeyRound,
  LockKeyhole,
  Network,
  Table2,
  Workflow,
} from 'lucide-react';

interface ServiceIconProps {
  service?: string | null;
  category?: string;
}

export function ServiceIcon({ service, category }: ServiceIconProps) {
  const name = (service ?? category ?? '').toLowerCase();
  const Icon = name.includes('transfer')
    ? FileInput
    : name.includes('s3')
      ? Database
      : name.includes('glue')
        ? Workflow
        : name.includes('dbt')
          ? Braces
          : name.includes('dagster')
            ? GitBranch
            : name.includes('athena')
              ? Table2
              : name.includes('cloudwatch')
                ? Activity
                : name.includes('kms')
                  ? KeyRound
                  : name.includes('iam')
                    ? LockKeyhole
                    : name.includes('api')
                      ? Network
                      : CloudCog;

  return (
    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-aws-deep text-aws-orange shadow-sm">
      <Icon size={18} />
    </div>
  );
}
