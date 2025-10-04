import React from 'react';
import { useLayout } from '../contexts/LayoutContext';
import { LayoutConfig } from '../types';

export const LayoutSwitcher: React.FC = () => {
  const { layoutState, setCurrentLayout, getCurrentLayoutConfig } = useLayout();
  const currentConfig = getCurrentLayoutConfig();

  const handleLayoutChange = (layoutId: string) => {
    if (layoutId !== layoutState.currentLayout) {
      setCurrentLayout(layoutId);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <label htmlFor="layout-select" className="text-sm font-medium text-gray-700">
        Layout:
      </label>
      <select
        id="layout-select"
        value={layoutState.currentLayout}
        onChange={(e) => handleLayoutChange(e.target.value)}
        className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        disabled={layoutState.isTransitioning}
      >
        {layoutState.availableLayouts.map((layout: LayoutConfig) => (
          <option key={layout.id} value={layout.id}>
            {layout.name}
          </option>
        ))}
      </select>
      {layoutState.isTransitioning && (
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-gray-500">Switching...</span>
        </div>
      )}
    </div>
  );
};
