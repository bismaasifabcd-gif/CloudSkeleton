export type LayerCategory =
  | 'source'
  | 'ingestion'
  | 'storage'
  | 'transformation'
  | 'orchestration'
  | 'serving'
  | 'analytics'
  | 'monitoring'
  | 'security'
  | string;

export interface GeneratePipelineRequest {
  description: string;
  user_id: string;
  title?: string;
  tags: string[];
}

export interface WorkflowStep {
  order: number;
  name: string;
  description: string;
  inputs: string[];
  outputs: string[];
  owner?: string | null;
}

export interface ServiceRecommendation {
  name: string;
  category: LayerCategory;
  purpose: string;
  why_selected: string;
  alternatives: string[];
}

export interface LayerRecommendation {
  name: string;
  services: string[];
  rationale: string;
}

export interface DiagramNodeSpec {
  id: string;
  label: string;
  category: LayerCategory;
  service?: string | null;
  description?: string | null;
  icon?: string | null;
  x: number;
  y: number;
}

export interface DiagramEdgeSpec {
  id: string;
  source: string;
  target: string;
  label?: string | null;
}

export interface DiagramSpec {
  nodes: DiagramNodeSpec[];
  edges: DiagramEdgeSpec[];
}

export interface PipelineSpec {
  title: string;
  summary: string;
  architecture: string;
  workflow: WorkflowStep[];
  aws_services: ServiceRecommendation[];
  ingestion_strategy: LayerRecommendation;
  storage_layer: LayerRecommendation;
  transformation_layer: LayerRecommendation;
  orchestration_strategy: LayerRecommendation;
  monitoring_strategy: LayerRecommendation;
  security_best_practices: string[];
  cost_optimization: string[];
  folder_structure: string;
  deployment_recommendations: string[];
  diagram: DiagramSpec;
  assumptions: string[];
  risks: string[];
  generated_by: string;
  generation_warnings: string[];
}

export interface PipelineRecord {
  id: string;
  user_id: string;
  title: string;
  description: string;
  tags: string[];
  spec: PipelineSpec;
  created_at: string;
  updated_at: string;
}

export interface HistoryListResponse {
  items: PipelineRecord[];
}

export interface ExportResponse {
  filename: string;
  content_type: string;
  content: string | PipelineRecord;
  s3_key?: string | null;
}
