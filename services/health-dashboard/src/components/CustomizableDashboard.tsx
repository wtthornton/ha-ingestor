/**
 * CustomizableDashboard Component
 * 
 * Drag-and-drop customizable dashboard with persistent layouts
 * Epic 15.3: Dashboard Customization & Layout
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { HealthWidget, MetricsWidget, ServicesWidget, AlertsWidget, EventsWidget, ChartWidget } from './widgets';
import { DEFAULT_LAYOUTS, LayoutPreset, DashboardLayout } from '../types/dashboard';
import 'react-grid-layout/css/styles.css';
import '../styles/dashboard-grid.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface CustomizableDashboardProps {
  health: any;
  darkMode: boolean;
}

export const CustomizableDashboard: React.FC<CustomizableDashboardProps> = ({ health, darkMode }) => {
  const [currentPreset, setCurrentPreset] = useState<LayoutPreset>('default');
  const [layouts, setLayouts] = useState<any>(DEFAULT_LAYOUTS.default.layout);
  const [widgets, setWidgets] = useState(DEFAULT_LAYOUTS.default.widgets);
  const [isEditMode, setIsEditMode] = useState(false);

  // Load saved layout from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('dashboard-layout');
    if (saved) {
      try {
        const { preset, customLayouts, customWidgets } = JSON.parse(saved);
        setCurrentPreset(preset);
        if (customLayouts) setLayouts(customLayouts);
        if (customWidgets) setWidgets(customWidgets);
      } catch (e) {
        console.error('Failed to load saved layout:', e);
      }
    }
  }, []);

  // Save layout to localStorage
  const saveLayout = (newLayouts: any, newWidgets?: any) => {
    const toSave = {
      preset: currentPreset,
      customLayouts: newLayouts,
      customWidgets: newWidgets || widgets,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('dashboard-layout', JSON.stringify(toSave));
  };

  // Handle layout change
  const handleLayoutChange = (layout: Layout[], allLayouts: any) => {
    if (isEditMode) {
      setLayouts(allLayouts);
      saveLayout(allLayouts);
    }
  };

  // Switch preset
  const switchPreset = (preset: LayoutPreset) => {
    const presetConfig = DEFAULT_LAYOUTS[preset];
    setCurrentPreset(preset);
    setLayouts(presetConfig.layout);
    setWidgets(presetConfig.widgets);
    saveLayout(presetConfig.layout, presetConfig.widgets);
  };

  // Reset to default
  const resetToDefault = () => {
    switchPreset('default');
  };

  // Export layout
  const exportLayout = () => {
    const data = {
      preset: currentPreset,
      layouts,
      widgets,
      exported: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-layout-${currentPreset}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Render widget based on type
  const renderWidget = (widgetId: string) => {
    const widget = widgets.find(w => w.id === widgetId);
    if (!widget) return null;

    const widgetContent = (() => {
      switch (widget.type) {
        case 'health':
          return <HealthWidget health={health} darkMode={darkMode} />;
        case 'metrics':
          return <MetricsWidget health={health} darkMode={darkMode} />;
        case 'services':
          return <ServicesWidget darkMode={darkMode} />;
        case 'alerts':
          return <AlertsWidget darkMode={darkMode} />;
        case 'events':
          return <EventsWidget darkMode={darkMode} />;
        case 'chart':
          return <ChartWidget title={widget.title} darkMode={darkMode} />;
        default:
          return <div>Unknown widget type</div>;
      }
    })();

    return (
      <div className={`h-full card-base p-4 overflow-hidden ${isEditMode ? 'ring-2 ring-blue-500/50' : ''}`}>
        {widgetContent}
      </div>
    );
  };

  const ResponsiveGrid = useMemo(() => ResponsiveGridLayout, []);

  return (
    <div className="space-y-4">
      {/* Dashboard Controls */}
      <div className={`card-base p-4`}>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className={`text-h2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              📊 Customizable Dashboard
            </h2>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {isEditMode ? '✏️ Edit mode: Drag and resize widgets' : 'View mode'}
            </p>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {/* Edit Mode Toggle */}
            <button
              onClick={() => setIsEditMode(!isEditMode)}
              className={`btn-${isEditMode ? 'success' : 'primary'} text-sm min-h-[44px]`}
            >
              {isEditMode ? '✅ Done Editing' : '✏️ Edit Layout'}
            </button>
            
            {/* Preset Selector */}
            <select
              value={currentPreset}
              onChange={(e) => switchPreset(e.target.value as LayoutPreset)}
              className="input-base min-h-[44px] text-sm"
              disabled={isEditMode}
            >
              <option value="default">📊 Default</option>
              <option value="operations">🔧 Operations</option>
              <option value="development">💻 Development</option>
              <option value="executive">👔 Executive</option>
            </select>
            
            {/* Reset */}
            <button
              onClick={resetToDefault}
              className="btn-secondary text-sm min-h-[44px]"
              disabled={isEditMode}
            >
              🔄 Reset
            </button>
            
            {/* Export */}
            <button
              onClick={exportLayout}
              className="btn-secondary text-sm min-h-[44px]"
            >
              📥 Export
            </button>
          </div>
        </div>
        
        {/* Preset Description */}
        <div className={`mt-3 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          {DEFAULT_LAYOUTS[currentPreset].description}
        </div>
      </div>

      {/* Grid Layout */}
      <ResponsiveGrid
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4 }}
        rowHeight={100}
        isDraggable={isEditMode}
        isResizable={isEditMode}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".drag-handle"
        margin={[16, 16]}
        containerPadding={[0, 0]}
        useCSSTransforms={true}
      >
        {widgets.map((widget) => (
          <div key={widget.id} className="relative">
            {isEditMode && (
              <div className={`drag-handle absolute top-2 left-2 p-2 rounded cursor-move ${
                darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'
              }`}>
                ⣿
              </div>
            )}
            {renderWidget(widget.id)}
          </div>
        ))}
      </ResponsiveGrid>
    </div>
  );
};

