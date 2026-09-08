import { useMemo } from 'react';
import dagre from 'dagre';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  type Edge,
  type Node,
} from 'reactflow';
import type { DiagramSpec } from '../../types/pipeline';
import { PipelineNode } from './PipelineNode';

const nodeTypes = {
  pipelineNode: PipelineNode,
};

const nodeWidth = 220;
const nodeHeight = 124;

interface ArchitectureDiagramProps {
  diagram?: DiagramSpec;
}

function getLayoutedElements(nodes: Node[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: direction, ranksep: 140, nodesep: 70, marginx: 30, marginy: 30 });

  nodes.forEach((node) => {
    graph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    graph.setEdge(edge.source, edge.target);
  });

  dagre.layout(graph);

  return {
    nodes: nodes.map((node) => {
      const layoutedNode = graph.node(node.id);
      return {
        ...node,
        position: {
          x: layoutedNode.x - nodeWidth / 2,
          y: layoutedNode.y - nodeHeight / 2,
        },
      };
    }),
    edges,
  };
}

export function ArchitectureDiagram({ diagram }: ArchitectureDiagramProps) {
  const { nodes, edges } = useMemo(() => {
    if (!diagram) {
      return { nodes: [], edges: [] };
    }

    const flowNodes: Node[] = diagram.nodes.map((node) => ({
      id: node.id,
      type: 'pipelineNode',
      position: { x: node.x, y: node.y },
      data: {
        label: node.label,
        category: node.category,
        service: node.service,
        description: node.description,
      },
    }));

    const flowEdges: Edge[] = diagram.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label ?? undefined,
      animated: true,
      markerEnd: {
        type: MarkerType.ArrowClosed,
      },
      style: {
        strokeWidth: 2,
      },
    }));

    return getLayoutedElements(flowNodes, flowEdges, 'LR');
  }, [diagram]);

  return (
    <section className="h-[520px] min-h-[420px] overflow-hidden rounded-lg border border-ink-200 bg-white dark:border-ink-800 dark:bg-[#0b1120]">
      <div className="flex items-center justify-between border-b border-ink-200 px-4 py-3 dark:border-ink-800">
        <h2 className="text-sm font-semibold uppercase tracking-normal text-ink-500 dark:text-ink-400">
          Architecture Diagram
        </h2>
        <span className="text-xs text-ink-500 dark:text-ink-400">
          Interactive React Flow
        </span>
      </div>
      <div className="h-[calc(100%-49px)]">
        {nodes.length === 0 ? (
          <div className="grid h-full place-items-center text-sm text-ink-500">
            Generate a pipeline to view the architecture.
          </div>
        ) : (
          <ReactFlow
            className="bg-white dark:bg-[#0b1120]"
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.08, minZoom: 0.72, maxZoom: 1.05 }}
            minZoom={0.55}
            maxZoom={1.5}
          >
            <Background color="#64748b" gap={16} size={1} />
            <MiniMap
              className="pipeline-minimap"
              nodeBorderRadius={8}
              nodeColor={() => '#3b82f6'}
              maskColor="rgba(15, 23, 42, 0.55)"
              pannable
              zoomable
            />
            <Controls className="pipeline-controls" showInteractive={false} />
          </ReactFlow>
        )}
      </div>
    </section>
  );
}
