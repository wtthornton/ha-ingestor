/**
 * Animated Dependency Graph with Real-Time Data Flow
 * 
 * Enhanced Dependencies tab showing animated data flow in real-time.
 * Uses SVG animations and CSS for smooth, performant visualizations.
 * 
 * Research from Context7 KB:
 * - React Flow (/websites/reactflow_dev) - Animated edges and nodes
 * - Framer Motion (/grx7/framer-motion) - Smooth animations
 */

import React, { useState, useRef } from 'react';
import type { ServiceStatus } from '../types';

interface AnimatedDependencyGraphProps {
  services: ServiceStatus[];
  darkMode: boolean;
  realTimeData?: RealTimeMetrics;
}

interface RealTimeMetrics {
  eventsPerSecond: number;
  apiCallsActive: number;
  dataSourcesActive: string[];
  lastUpdate: Date;
}

interface DataFlowPath {
  id: string;
  from: string;
  to: string;
  type: 'websocket' | 'api' | 'storage' | 'query';
  active: boolean;
  throughput?: number; // events/sec or calls/sec
  color: string;
}

interface ServiceNode {
  id: string;
  name: string;
  icon: string;
  type: 'source' | 'processor' | 'storage' | 'ui' | 'external';
  position: { x: number; y: number };
  layer: number;
  status?: 'running' | 'error' | 'degraded' | 'unknown';
  metrics?: {
    throughput?: number;
    latency?: number;
    errorRate?: number;
  };
  description?: string;
}

export const AnimatedDependencyGraph: React.FC<AnimatedDependencyGraphProps> = ({
  services,
  darkMode,
  realTimeData,
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Define service nodes with accurate architecture (Epic 13 + Epic 22)
  const nodes: ServiceNode[] = [
    // Layer 1: External Sources
    { id: 'home-assistant', name: 'Home Assistant', icon: '🏠', type: 'source', position: { x: 400, y: 50 }, layer: 1, description: 'External event source' },
    { id: 'espn-api', name: 'ESPN API', icon: '🏈🏒', type: 'external', position: { x: 150, y: 50 }, layer: 1, description: 'NFL/NHL game data' },
    { id: 'openweather', name: 'OpenWeather', icon: '☁️', type: 'external', position: { x: 550, y: 50 }, layer: 1, description: 'Weather enrichment' },
    { id: 'external-apis', name: 'External APIs', icon: '🌐', type: 'external', position: { x: 700, y: 50 }, layer: 1, description: 'Air quality, carbon, pricing' },
    
    // Layer 2: Ingestion
    { id: 'websocket-ingestion', name: 'WebSocket Ingestion', icon: '📡', type: 'processor', position: { x: 400, y: 150 }, layer: 2, description: 'Event capture + inline weather' },
    { id: 'sports-data', name: 'Sports Data', icon: '⚡', type: 'processor', position: { x: 150, y: 150 }, layer: 2, description: 'ESPN cache + persistence' },
    { id: 'external-services', name: 'External Services', icon: '🔌', type: 'processor', position: { x: 650, y: 150 }, layer: 2, description: 'Periodic external data fetch' },
    
    // Layer 3: Processing (Optional Enhancement Path)
    { id: 'enrichment-pipeline', name: 'Enrichment Pipeline', icon: '🔄', type: 'processor', position: { x: 400, y: 250 }, layer: 3, description: 'Optional normalization' },
    
    // Layer 4: Storage (Hybrid Architecture - Epic 22!)
    { id: 'influxdb', name: 'InfluxDB', icon: '🗄️', type: 'storage', position: { x: 350, y: 370 }, layer: 4, description: 'Time-series events' },
    { id: 'sqlite', name: 'SQLite', icon: '💾', type: 'storage', position: { x: 450, y: 370 }, layer: 4, description: 'Metadata (Epic 22)' },
    
    // Layer 5: API Gateway (Epic 13 Split!)
    { id: 'data-api', name: 'Data API', icon: '🔌', type: 'processor', position: { x: 350, y: 470 }, layer: 5, description: 'Feature data hub' },
    { id: 'admin-api', name: 'Admin API', icon: '⚙️', type: 'processor', position: { x: 500, y: 470 }, layer: 5, description: 'System monitoring' },
    
    // Layer 6: UI
    { id: 'health-dashboard', name: 'Dashboard', icon: '📊', type: 'ui', position: { x: 425, y: 570 }, layer: 6, description: 'You are here!' },
  ];

  // Define data flow paths based on actual call trees
  const dataFlows: DataFlowPath[] = [
    // Primary HA Event Flow (Path A - Always Active)
    { id: 'ha-ws', from: 'home-assistant', to: 'websocket-ingestion', type: 'websocket', active: true, throughput: realTimeData?.eventsPerSecond || 0, color: '#3B82F6' },
    { id: 'ws-direct-influx', from: 'websocket-ingestion', to: 'influxdb', type: 'storage', active: true, color: '#10B981' }, // Primary path!
    
    // Enhancement Path (Path B - Optional)
    { id: 'ws-enrich', from: 'websocket-ingestion', to: 'enrichment-pipeline', type: 'api', active: true, color: '#F59E0B' },
    { id: 'enrich-db', from: 'enrichment-pipeline', to: 'influxdb', type: 'storage', active: true, color: '#F59E0B' },
    
    // Inline Weather Enrichment (within websocket-ingestion)
    { id: 'weather-inline', from: 'openweather', to: 'websocket-ingestion', type: 'api', active: true, color: '#06B6D4' },
    
    // Sports Data Flow (Epic 12 - Hybrid Pattern A+B)
    { id: 'espn-sports', from: 'espn-api', to: 'sports-data', type: 'api', active: realTimeData?.dataSourcesActive?.includes('sports') || false, throughput: 0.5, color: '#8B5CF6' },
    { id: 'sports-influx', from: 'sports-data', to: 'influxdb', type: 'storage', active: true, color: '#8B5CF6' }, // Epic 12: InfluxDB persistence
    { id: 'sports-sqlite', from: 'sports-data', to: 'sqlite', type: 'storage', active: true, color: '#8B5CF6' }, // Epic 22: SQLite webhooks
    
    // External API Services (Pattern A - Continuous Push)
    { id: 'external-fetch', from: 'external-apis', to: 'external-services', type: 'api', active: true, color: '#6B7280' },
    { id: 'external-influx', from: 'external-services', to: 'influxdb', type: 'storage', active: true, color: '#6B7280' },
    
    // Epic 22: Hybrid Database Queries
    { id: 'influx-data', from: 'influxdb', to: 'data-api', type: 'query', active: true, color: '#3B82F6' },
    { id: 'sqlite-data', from: 'sqlite', to: 'data-api', type: 'query', active: true, color: '#10B981' },
    
    // Epic 13: API Gateway Layer
    { id: 'data-dash', from: 'data-api', to: 'health-dashboard', type: 'api', active: true, color: '#3B82F6' },
    { id: 'admin-dash', from: 'admin-api', to: 'health-dashboard', type: 'api', active: true, color: '#F59E0B' },
  ];

  // Note: Pulse and active flows managed through CSS animations and real-time data

  const getServiceStatus = (nodeId: string): ServiceStatus | undefined => {
    return services.find(s => 
      s.service === nodeId || 
      s.service.toLowerCase().includes(nodeId.toLowerCase()) ||
      nodeId.toLowerCase().includes(s.service.toLowerCase())
    );
  };

  const getNodeColor = (node: ServiceNode): string => {
    const service = getServiceStatus(node.id);
    
    if (!service) {
      return darkMode ? '#374151' : '#E5E7EB'; // gray
    }
    
    switch (service.status) {
      case 'running':
        return darkMode ? '#10B981' : '#34D399'; // green
      case 'error':
        return darkMode ? '#EF4444' : '#F87171'; // red
      case 'degraded':
        return darkMode ? '#F59E0B' : '#FBBF24'; // yellow
      default:
        return darkMode ? '#374151' : '#E5E7EB'; // gray
    }
  };


  // Calculate path between two nodes
  const calculatePath = (fromId: string, toId: string): string => {
    const from = nodes.find(n => n.id === fromId);
    const to = nodes.find(n => n.id === toId);
    
    if (!from || !to) return '';
    
    const startX = from.position.x;
    const startY = from.position.y + 30; // Offset from node center
    const endX = to.position.x;
    const endY = to.position.y - 30; // Offset from node center
    
    // Create smooth curve
    const midY = (startY + endY) / 2;
    
    return `M ${startX} ${startY} 
            C ${startX} ${midY}, 
              ${endX} ${midY}, 
              ${endX} ${endY}`;
  };

  const renderDataFlow = (flow: DataFlowPath) => {
    const path = calculatePath(flow.from, flow.to);
    const isHighlighted = selectedNode === flow.from || selectedNode === flow.to;
    const opacity = !selectedNode || isHighlighted ? 1 : 0.2;

    return (
      <g key={flow.id} opacity={opacity}>
        {/* Base path */}
        <path
          d={path}
          fill="none"
          stroke={darkMode ? '#374151' : '#E5E7EB'}
          strokeWidth="2"
          strokeDasharray={flow.active ? undefined : '5,5'}
        />
        
        {/* Animated path overlay */}
        {flow.active && (
          <>
            <path
              d={path}
              fill="none"
              stroke={flow.color}
              strokeWidth="3"
              strokeLinecap="round"
              opacity="0.6"
              filter={`url(#glow-${flow.type})`}
            >
              <animate
                attributeName="stroke-dasharray"
                values="10,5;20,15"
                dur="1s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="stroke-dashoffset"
                from="0"
                to="30"
                dur="1.5s"
                repeatCount="indefinite"
              />
            </path>
            
            {/* Data particles */}
            <circle r="4" fill={flow.color} filter={`url(#glow-${flow.type})`}>
              <animateMotion
                dur={`${2 + Math.random() * 2}s`}
                repeatCount="indefinite"
                path={path}
              />
              <animate
                attributeName="r"
                values="3;5;3"
                dur="1s"
                repeatCount="indefinite"
              />
            </circle>
            
            {/* Additional particles for high throughput */}
            {flow.throughput && flow.throughput > 10 && (
              <circle r="3" fill={flow.color} opacity="0.7">
                <animateMotion
                  dur="3s"
                  repeatCount="indefinite"
                  path={path}
                  begin="1s"
                />
              </circle>
            )}
          </>
        )}
        
        {/* Throughput label */}
        {flow.throughput && flow.throughput > 0 && isHighlighted && (
          <text
            x={(nodes.find(n => n.id === flow.from)!.position.x + nodes.find(n => n.id === flow.to)!.position.x) / 2}
            y={(nodes.find(n => n.id === flow.from)!.position.y + nodes.find(n => n.id === flow.to)!.position.y) / 2}
            fill={darkMode ? '#fff' : '#000'}
            fontSize="12"
            textAnchor="middle"
            style={{ 
              pointerEvents: 'none',
              fontWeight: 600,
              textShadow: darkMode ? '0 0 4px rgba(0,0,0,0.8)' : '0 0 4px rgba(255,255,255,0.8)'
            }}
          >
            {flow.throughput.toFixed(1)}/s
          </text>
        )}
      </g>
    );
  };

  const renderNode = (node: ServiceNode) => {
    const isSelected = selectedNode === node.id;
    const isHovered = hoveredNode === node.id;
    const isHighlighted = !selectedNode || isSelected || 
      dataFlows.some(f => (f.from === selectedNode && f.to === node.id) || (f.to === selectedNode && f.from === node.id));
    
    const nodeColor = getNodeColor(node);
    const scale = isSelected ? 1.15 : isHovered ? 1.08 : 1;
    const opacity = !selectedNode || isHighlighted ? 1 : 0.3;

    return (
      <g
        key={node.id}
        transform={`translate(${node.position.x}, ${node.position.y}) scale(${scale})`}
        opacity={opacity}
        style={{ 
          cursor: 'pointer',
          transition: 'all 0.3s ease',
        }}
        onClick={() => setSelectedNode(isSelected ? null : node.id)}
        onMouseEnter={() => setHoveredNode(node.id)}
        onMouseLeave={() => setHoveredNode(null)}
      >
        {/* Node glow effect */}
        <circle
          r="35"
          fill={nodeColor}
          opacity="0.2"
          filter="url(#node-glow)"
        >
          <animate
            attributeName="r"
            values="35;40;35"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
        
        {/* Node background */}
        <circle
          r="30"
          fill={darkMode ? '#1F2937' : '#FFFFFF'}
          stroke={nodeColor}
          strokeWidth="3"
          filter={isSelected ? 'url(#selected-glow)' : undefined}
        />
        
        {/* Node icon */}
        <text
          textAnchor="middle"
          dy=".3em"
          fontSize="24"
          style={{ pointerEvents: 'none' }}
        >
          {node.icon}
        </text>
        
        {/* Node label */}
        <text
          y="45"
          textAnchor="middle"
          fill={darkMode ? '#E5E7EB' : '#1F2937'}
          fontSize="12"
          fontWeight="600"
          style={{ pointerEvents: 'none' }}
        >
          {node.name}
        </text>
        
        {/* Status indicator */}
        {getServiceStatus(node.id) && (
          <circle
            cx="20"
            cy="-20"
            r="6"
            fill={nodeColor}
            stroke={darkMode ? '#1F2937' : '#FFFFFF'}
            strokeWidth="2"
          >
            <animate
              attributeName="r"
              values="6;8;6"
              dur="1.5s"
              repeatCount="indefinite"
            />
          </circle>
        )}
      </g>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`p-6 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} flex items-center gap-3`}>
              <span className="animate-pulse">🌊</span>
              Complete Architecture Flow
            </h2>
            <p className={`mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Hybrid database (Epic 22) • API split (Epic 13) • Sports persistence (Epic 12) • Click nodes for details
            </p>
          </div>
          
          {/* Live Metrics */}
          {realTimeData && (
            <div className={`px-6 py-3 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                    {realTimeData.eventsPerSecond.toFixed(1)}
                  </div>
                  <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    events/sec
                  </div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                    {realTimeData.apiCallsActive}
                  </div>
                  <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    active APIs
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>WebSocket/Query</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-green-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Primary Path</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-orange-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Enhancement Path</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-purple-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Sports (Epic 12)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-cyan-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Weather (Inline)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-gray-500"></div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>External APIs</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🗄️💾</span>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Hybrid DB (Epic 22)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="animate-pulse">●</div>
            <span className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Active Flow</span>
          </div>
        </div>
      </div>

      {/* SVG Diagram */}
      <div className={`p-8 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg overflow-x-auto`}>
        <svg
          ref={svgRef}
          width="800"
          height="600"
          viewBox="0 0 800 600"
          className="w-full"
          style={{ minWidth: '800px' }}
        >
          {/* Definitions for filters and effects */}
          <defs>
            {/* Glow filters for different flow types */}
            <filter id="glow-websocket">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="glow-api">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="glow-storage">
              <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <filter id="glow-query">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            {/* Node glow */}
            <filter id="node-glow">
              <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            {/* Selected node glow */}
            <filter id="selected-glow">
              <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Render all data flows first (so they appear behind nodes) */}
          {dataFlows.map(renderDataFlow)}

          {/* Render all nodes */}
          {nodes.map(renderNode)}
        </svg>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className={`p-6 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2 flex items-center gap-2`}>
                <span className="text-2xl">{nodes.find(n => n.id === selectedNode)?.icon}</span>
                {nodes.find(n => n.id === selectedNode)?.name}
              </h3>
              <div className="space-y-2">
                <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} italic`}>
                  {nodes.find(n => n.id === selectedNode)?.description}
                </p>
                <div className="grid grid-cols-3 gap-4 mt-3">
                  <div>
                    <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Type</p>
                    <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {nodes.find(n => n.id === selectedNode)?.type}
                    </p>
                  </div>
                  <div>
                    <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Layer</p>
                    <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {nodes.find(n => n.id === selectedNode)?.layer}
                    </p>
                  </div>
                  <div>
                    <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Connections</p>
                    <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {dataFlows.filter(f => f.from === selectedNode || f.to === selectedNode).length} active
                    </p>
                  </div>
                </div>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mt-2`}>
                  <span className="font-semibold">Status:</span>{' '}
                  <span className={getServiceStatus(selectedNode)?.status === 'running' ? 'text-green-500' : 'text-gray-500'}>
                    {getServiceStatus(selectedNode)?.status || 'unknown'}
                  </span>
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className={`ml-4 px-4 py-2 rounded-lg transition-colors ${
                darkMode
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              Clear Selection
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnimatedDependencyGraph;

