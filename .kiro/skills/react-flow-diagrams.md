# React Flow Diagram Generation Skill

## Purpose
Specialized knowledge for creating interactive, auto-layout diagrams using React Flow, specifically for AWS architecture visualization and data pipeline representation.

## Core Concepts

### React Flow Setup
- Install @reactflow/core and dagre for automatic layout
- Configure proper node and edge types for architecture diagrams
- Implement custom node components for AWS services
- Use hooks for diagram state management and interactions

### Node and Edge Configuration
```typescript
interface PipelineNode extends Node {
  id: string;
  type: 'service' | 'data' | 'process';
  data: {
    label: string;
    service: string;
    description?: string;
    icon?: string;
  };
  position: { x: number; y: number };
}

interface PipelineEdge extends Edge {
  id: string;
  source: string;
  target: string;
  type: 'default' | 'smoothstep' | 'straight';
  animated?: boolean;
  label?: string;
}
```

### Automatic Layout with Dagre
```typescript
import dagre from 'dagre';
import type { Node, Edge } from '@reactflow/core';

interface LayoutResult {
  nodes: Node[];
  edges: Edge[];
}

const getLayoutedElements = (
  nodes: Node[], 
  edges: Edge[], 
  direction: 'TB' | 'LR' = 'TB'
): LayoutResult => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ 
    rankdir: direction,
    ranksep: 100,
    nodesep: 80,
    marginx: 20,
    marginy: 20
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 100,
        y: nodeWithPosition.y - 50,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};
```

## Custom Node Components

### Service Node Implementation
```typescript
interface ServiceNodeData {
  label: string;
  service: string;
  description?: string;
  status?: 'active' | 'inactive' | 'pending';
}

interface ServiceNodeProps extends NodeProps<ServiceNodeData> {
  data: ServiceNodeData;
  selected: boolean;
}

const ServiceNode: React.FC<ServiceNodeProps> = ({ 
  data, 
  selected 
}) => {
  const { service, label, description, status } = data;
  
  return (
    <div className={`
      bg-white dark:bg-gray-800 
      border-2 rounded-lg p-4 min-w-[200px]
      ${selected ? 'border-blue-500' : 'border-gray-300 dark:border-gray-600'}
      ${status === 'active' ? 'shadow-lg' : 'shadow-md'}
      transition-all duration-200 hover:shadow-xl
    `}>
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500"
      />
      
      <div className="flex items-center gap-3">
        <ServiceIcon service={service} className="w-8 h-8" />
        <div className="flex-1">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
            {label}
          </h3>
          {description && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-blue-500"
      />
    </div>
  );
};

ServiceNode.displayName = 'ServiceNode';
```

### Edge Styling and Animation
```typescript
interface CustomEdgeStyle {
  style: React.CSSProperties;
  labelBgStyle?: React.CSSProperties;
  labelStyle?: React.CSSProperties;
  animated?: boolean;
}

const customEdgeTypes: Record<string, CustomEdgeStyle> = {
  default: {
    style: {
      strokeWidth: 2,
      stroke: '#6366f1',
    },
    labelBgStyle: {
      fill: '#ffffff',
      fillOpacity: 0.8,
    },
    labelStyle: {
      fontSize: '12px',
      fontWeight: 600,
    },
  },
  animated: {
    style: {
      strokeWidth: 2,
      stroke: '#10b981',
    },
    animated: true,
  },
};
```

## State Management Patterns

### Diagram State Hook
```typescript
interface UseDiagramStateResult {
  nodes: Node[];
  edges: Edge[];
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  fitView: () => void;
  resetDiagram: () => void;
}

const useDiagramState = (initialData?: PipelineSpec): UseDiagramStateResult => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { fitView } = useReactFlow();

  const onConnect = useCallback((connection: Connection) => {
    if (!connection.source || !connection.target) {
      console.warn('Invalid connection: missing source or target');
      return;
    }

    const newEdge: Edge = {
      id: `${connection.source}-${connection.target}`,
      source: connection.source,
      target: connection.target,
      type: 'default',
    };
    setEdges((prev) => addEdge(newEdge, prev));
  }, [setEdges]);

  const resetDiagram = useCallback(() => {
    setNodes([]);
    setEdges([]);
  }, [setNodes, setEdges]);

  return {
    nodes,
    edges,
    setNodes,
    setEdges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    fitView,
    resetDiagram,
  };
};
```

### Data Transformation
```typescript
interface PipelineService {
  id: string;
  name: string;
  type: string;
  description?: string;
}

interface PipelineConnection {
  from: string;
  to: string;
  type?: string;
}

interface PipelineSpec {
  services: PipelineService[];
  connections: PipelineConnection[];
}

const transformPipelineToFlow = (pipeline: PipelineSpec): LayoutResult => {
  try {
    const nodes: Node[] = pipeline.services.map((service, index) => ({
      id: service.id,
      type: 'service',
      data: {
        label: service.name,
        service: service.type,
        description: service.description,
      },
      position: { x: 0, y: index * 150 }, // Temporary positions
    }));

    const edges: Edge[] = pipeline.connections.map((connection) => ({
      id: `${connection.from}-${connection.to}`,
      source: connection.from,
      target: connection.to,
      type: 'default',
      label: connection.type,
    }));

    return getLayoutedElements(nodes, edges);
  } catch (error) {
    console.error('Failed to transform pipeline to flow:', error);
    return { nodes: [], edges: [] };
  }
};
```

## Performance Optimization

### Memoization Strategy
```typescript
interface ArchitectureDiagramProps {
  pipeline: PipelineSpec;
  className?: string;
}

const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({ 
  pipeline,
  className = ''
}) => {
  const diagramData = useMemo(
    () => transformPipelineToFlow(pipeline),
    [pipeline]
  );

  const nodeTypes = useMemo(
    () => ({
      service: ServiceNode,
      data: DataNode,
      process: ProcessNode,
    }),
    []
  );

  const edgeTypes = useMemo(() => customEdgeTypes, []);

  return (
    <div className={className}>
      <ReactFlow
        nodes={diagramData.nodes}
        edges={diagramData.edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
      />
    </div>
  );
};

ArchitectureDiagram.displayName = 'ArchitectureDiagram';
```

### Viewport Management
```typescript
interface ViewportControls {
  resetView: () => void;
  centerOnNode: (nodeId: string) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  zoomTo: (zoom: number) => void;
}

const useViewportControl = (): ViewportControls => {
  const { fitView, zoomIn, zoomOut, zoomTo, getNodes, setCenter } = useReactFlow();

  const resetView = useCallback(() => {
    fitView({ duration: 800, padding: 0.1 });
  }, [fitView]);

  const centerOnNode = useCallback((nodeId: string) => {
    try {
      const node = getNodes().find(n => n.id === nodeId);
      if (node) {
        setCenter(node.position.x, node.position.y, { zoom: 1.5 });
      } else {
        console.warn(`Node with id ${nodeId} not found`);
      }
    } catch (error) {
      console.error('Failed to center on node:', error);
    }
  }, [getNodes, setCenter]);

  return { resetView, centerOnNode, zoomIn, zoomOut, zoomTo };
};
```

## Integration Patterns

### Theme Support
```typescript
interface DiagramThemeProps {
  children: React.ReactNode;
}

const DiagramTheme: React.FC<DiagramThemeProps> = ({ children }) => {
  const { theme } = useTheme();
  
  return (
    <div 
      className={`react-flow__renderer ${theme === 'dark' ? 'dark' : ''}`}
      style={{
        '--react-flow-background': theme === 'dark' ? '#1f2937' : '#f9fafb',
        '--react-flow-node-border': theme === 'dark' ? '#374151' : '#e5e7eb',
      } as React.CSSProperties}
    >
      {children}
    </div>
  );
};

DiagramTheme.displayName = 'DiagramTheme';
```

### Export Functionality
```typescript
interface ExportControls {
  exportAsPNG: () => Promise<void>;
  exportAsJSON: () => void;
}

const useExportDiagram = (): ExportControls => {
  const { getNodes, getEdges, getViewport } = useReactFlow();

  const exportAsPNG = useCallback(async (): Promise<void> => {
    try {
      const imageWidth = 1200;
      const imageHeight = 800;
      
      const element = document.querySelector('.react-flow') as HTMLElement;
      if (!element) {
        throw new Error('React Flow element not found');
      }
      
      // Use html2canvas or similar library
      const { default: html2canvas } = await import('html2canvas');
      const canvas = await html2canvas(element, {
        width: imageWidth,
        height: imageHeight,
      });
      
      const link = document.createElement('a');
      link.download = 'pipeline-diagram.png';
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Failed to export diagram as PNG:', error);
    }
  }, []);

  const exportAsJSON = useCallback((): void => {
    try {
      const data = {
        nodes: getNodes(),
        edges: getEdges(),
        viewport: getViewport(),
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      
      const link = document.createElement('a');
      link.download = 'pipeline-diagram.json';
      link.href = URL.createObjectURL(blob);
      link.click();
    } catch (error) {
      console.error('Failed to export diagram as JSON:', error);
    }
  }, [getNodes, getEdges, getViewport]);

  return { exportAsPNG, exportAsJSON };
};
```

## Accessibility and UX

### Keyboard Navigation
```typescript
const useKeyboardNavigation = (): void => {
  const { getNodes, setNodes } = useReactFlow();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Tab') {
        event.preventDefault();
        
        try {
          const nodes = getNodes();
          const selectedNode = nodes.find(n => n.selected);
          
          if (selectedNode) {
            const currentIndex = nodes.indexOf(selectedNode);
            const nextIndex = (currentIndex + 1) % nodes.length;
            
            setNodes(prev => prev.map((node, index) => ({
              ...node,
              selected: index === nextIndex,
            })));
          }
        } catch (error) {
          console.error('Keyboard navigation error:', error);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [getNodes, setNodes]);
};
```

### ARIA Labels and Screen Reader Support
```typescript
interface AccessibleNodeProps extends NodeProps {
  data: {
    service: string;
    label: string;
  };
  selected: boolean;
}

const AccessibleNode: React.FC<AccessibleNodeProps> = ({ 
  data, 
  selected 
}) => (
  <div
    role="button"
    tabIndex={0}
    aria-label={`${data.service} service: ${data.label}`}
    aria-selected={selected}
    className="service-node"
  >
    {/* Node content */}
  </div>
);

AccessibleNode.displayName = 'AccessibleNode';
```

#[[file:frontend/src/components/diagram/ArchitectureDiagram.tsx]]
#[[file:frontend/src/components/diagram/PipelineNode.tsx]]