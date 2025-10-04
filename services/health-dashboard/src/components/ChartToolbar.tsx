import React from 'react';

interface ChartToolbarProps {
  title: string;
  isZoomed: boolean;
  onZoomReset: () => void;
  onExport: (format: 'csv' | 'json' | 'pdf') => void;
  realTime?: boolean;
  enableZoom?: boolean;
  enablePan?: boolean;
  enableDrillDown?: boolean;
}

export const ChartToolbar: React.FC<ChartToolbarProps> = ({
  title,
  isZoomed,
  onZoomReset,
  onExport,
  realTime = false,
  enableZoom = true,
  enablePan = true,
  enableDrillDown = true,
}) => {
  return (
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 space-y-2 sm:space-y-0">
      {/* Title and Status */}
      <div className="flex items-center space-x-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {realTime && (
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-600 font-medium">Live</span>
          </div>
        )}
      </div>

      {/* Toolbar Actions */}
      <div className="flex items-center space-x-2">
        {/* Zoom Controls */}
        {enableZoom && (
          <div className="flex items-center space-x-1">
            {isZoomed && (
              <button
                onClick={onZoomReset}
                className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                title="Reset zoom"
              >
                Reset Zoom
              </button>
            )}
            <div className="text-xs text-gray-500">
              {enablePan ? 'Zoom & Pan' : 'Zoom only'}
            </div>
          </div>
        )}

        {/* Export Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => onExport('csv')}
            className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            title="Export as CSV"
          >
            CSV
          </button>
          <button
            onClick={() => onExport('json')}
            className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            title="Export as JSON"
          >
            JSON
          </button>
          <button
            onClick={() => onExport('pdf')}
            className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            title="Export as PDF"
          >
            PDF
          </button>
        </div>

        {/* Interaction Info */}
        <div className="text-xs text-gray-500">
          {enableDrillDown && (
            <span className="inline-flex items-center">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              Click to drill down
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
