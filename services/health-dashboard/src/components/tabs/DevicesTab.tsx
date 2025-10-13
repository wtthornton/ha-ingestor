import React, { useState, useMemo } from 'react';
import { useDevices, Device, Entity } from '../../hooks/useDevices';
import type { TabProps } from './types';

export const DevicesTab: React.FC<TabProps> = ({ darkMode }) => {
  const { devices, entities, integrations, loading, error, refresh } = useDevices();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedArea, setSelectedArea] = useState('');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  // Get unique manufacturers and areas for filters
  const manufacturers = useMemo(() => {
    const unique = Array.from(new Set(devices.map(d => d.manufacturer).filter(Boolean)));
    return unique.sort();
  }, [devices]);

  const areas = useMemo(() => {
    const unique = Array.from(new Set(devices.map(d => d.area_id).filter(Boolean)));
    return unique.sort();
  }, [devices]);

  // Filter devices
  const filteredDevices = useMemo(() => {
    return devices.filter(device => {
      const matchesSearch = !searchTerm || 
        device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.manufacturer?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.model?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesManufacturer = !selectedManufacturer || 
        device.manufacturer === selectedManufacturer;
      
      const matchesArea = !selectedArea || 
        device.area_id === selectedArea;
      
      return matchesSearch && matchesManufacturer && matchesArea;
    });
  }, [devices, searchTerm, selectedManufacturer, selectedArea]);

  // Get device icon
  const getDeviceIcon = (device: Device): string => {
    const name = device.name.toLowerCase();
    const manufacturer = device.manufacturer?.toLowerCase() || '';
    const model = device.model?.toLowerCase() || '';
    
    if (name.includes('light') || name.includes('bulb') || name.includes('lamp') || manufacturer.includes('hue') || manufacturer.includes('lifx')) return '💡';
    if (name.includes('thermostat') || name.includes('climate') || manufacturer.includes('nest') || manufacturer.includes('ecobee')) return '🌡️';
    if (name.includes('camera') || name.includes('cam') || manufacturer.includes('ring') || manufacturer.includes('arlo')) return '📷';
    if (name.includes('switch') || name.includes('outlet') || name.includes('plug')) return '🔌';
    if (name.includes('lock') || name.includes('door lock')) return '🔒';
    if (name.includes('cover') || name.includes('blind') || name.includes('shade') || name.includes('garage')) return '🚪';
    if (name.includes('sensor')) return '📱';
    if (name.includes('media') || name.includes('sonos') || name.includes('chromecast')) return '🎵';
    if (name.includes('vacuum') || name.includes('roomba')) return '🤖';
    if (name.includes('hub') || name.includes('bridge') || model.includes('bridge')) return '🔧';
    
    return '📦'; // Default
  };

  // Get entities for selected device
  const deviceEntities = useMemo(() => {
    if (!selectedDevice) return [];
    return entities.filter(e => e.device_id === selectedDevice.device_id);
  }, [selectedDevice, entities]);

  // Loading state
  if (loading && devices.length === 0) {
    return (
      <div className={`p-8 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <span className="ml-4">Loading devices...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`p-8 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        <div className={`p-6 rounded-lg ${darkMode ? 'bg-red-900/20 border-red-800' : 'bg-red-50 border-red-200'} border`}>
          <p className="text-red-600 dark:text-red-400 font-medium">⚠️ Error loading devices</p>
          <p className="text-sm mt-2">{error}</p>
          <button
            onClick={refresh}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 sm:p-6 ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Devices</p>
              <p className="text-3xl font-bold mt-1">{devices.length}</p>
            </div>
            <div className="text-4xl">📱</div>
          </div>
        </div>

        <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Entities</p>
              <p className="text-3xl font-bold mt-1">{entities.length}</p>
            </div>
            <div className="text-4xl">🔌</div>
          </div>
        </div>

        <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Integrations</p>
              <p className="text-3xl font-bold mt-1">{integrations.length}</p>
            </div>
            <div className="text-4xl">🔧</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border mb-6`}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="🔍 Search devices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={`px-4 py-2 rounded-lg border ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' 
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          />

          {/* Manufacturer Filter */}
          <select
            value={selectedManufacturer}
            onChange={(e) => setSelectedManufacturer(e.target.value)}
            className={`px-4 py-2 rounded-lg border ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-gray-100' 
                : 'bg-white border-gray-300 text-gray-900'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            <option value="">All Manufacturers</option>
            {manufacturers.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          {/* Area Filter */}
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className={`px-4 py-2 rounded-lg border ${
              darkMode 
                ? 'bg-gray-700 border-gray-600 text-gray-100' 
                : 'bg-white border-gray-300 text-gray-900'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            <option value="">All Areas</option>
            {areas.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>

        {/* Results count */}
        <div className="mt-3 text-sm text-gray-500">
          Showing {filteredDevices.length} of {devices.length} devices
        </div>
      </div>

      {/* Device Grid */}
      {filteredDevices.length === 0 ? (
        <div className={`p-8 text-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          <div className="text-6xl mb-4">📦</div>
          <p className="text-lg">No devices found</p>
          <p className="text-sm mt-2">
            {searchTerm || selectedManufacturer || selectedArea 
              ? 'Try adjusting your filters' 
              : 'Waiting for device discovery...'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredDevices.map(device => (
            <button
              key={device.device_id}
              onClick={() => setSelectedDevice(device)}
              className={`p-4 rounded-lg border text-left transition-all duration-200 ${
                darkMode 
                  ? 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-blue-600' 
                  : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-blue-400'
              } hover:shadow-lg hover:scale-105`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="text-4xl">{getDeviceIcon(device)}</div>
                <div className={`text-xs px-2 py-1 rounded ${
                  darkMode ? 'bg-gray-700' : 'bg-gray-100'
                }`}>
                  {device.entity_count} {device.entity_count === 1 ? 'entity' : 'entities'}
                </div>
              </div>

              <h3 className={`font-semibold mb-1 ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                {device.name}
              </h3>

              <div className={`text-xs space-y-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                <div>🏭 {device.manufacturer || 'Unknown'}</div>
                <div>📦 {device.model || 'Unknown'}</div>
                {device.sw_version && <div>💾 {device.sw_version}</div>}
                {device.area_id && <div>📍 {device.area_id}</div>}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Entity Browser Modal */}
      {selectedDevice && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedDevice(null)}
        >
          <div 
            className={`max-w-4xl w-full max-h-[90vh] overflow-auto rounded-lg ${
              darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            } border shadow-2xl`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className={`sticky top-0 p-6 border-b ${
              darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-4xl">{getDeviceIcon(selectedDevice)}</span>
                    <h2 className="text-2xl font-bold">{selectedDevice.name}</h2>
                  </div>
                  <div className={`text-sm space-y-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    <div>🏭 {selectedDevice.manufacturer}</div>
                    <div>📦 {selectedDevice.model}</div>
                    {selectedDevice.sw_version && <div>💾 {selectedDevice.sw_version}</div>}
                    {selectedDevice.area_id && <div>📍 {selectedDevice.area_id}</div>}
                  </div>
                </div>
                <button
                  onClick={() => setSelectedDevice(null)}
                  className={`text-2xl ${darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'}`}
                >
                  ×
                </button>
              </div>
            </div>

            {/* Entities */}
            <div className="p-6">
              <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                Entities ({deviceEntities.length})
              </h3>

              {deviceEntities.length === 0 ? (
                <div className={`text-center py-8 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                  <div className="text-4xl mb-2">🔌</div>
                  <p>No entities found for this device</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(groupByDomain(deviceEntities)).map(([domain, domainEntities]) => (
                    <div key={domain}>
                      <div className={`text-sm font-medium mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        {getDomainIcon(domain)} {domain} ({domainEntities.length})
                      </div>
                      <div className="space-y-1 ml-6">
                        {domainEntities.map((entity: Entity) => (
                          <div
                            key={entity.entity_id}
                            className={`p-3 rounded ${
                              darkMode ? 'bg-gray-750 border-gray-600' : 'bg-gray-50 border-gray-200'
                            } border`}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <code className={`text-sm font-mono ${
                                  entity.disabled 
                                    ? (darkMode ? 'text-gray-600' : 'text-gray-400')
                                    : (darkMode ? 'text-blue-400' : 'text-blue-600')
                                }`}>
                                  {entity.entity_id}
                                </code>
                                <div className={`text-xs mt-1 ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                  Platform: {entity.platform}
                                </div>
                              </div>
                              {entity.disabled && (
                                <span className={`text-xs px-2 py-1 rounded ${
                                  darkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
                                }`}>
                                  Disabled
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions
function groupByDomain(entities: Entity[]): Record<string, Entity[]> {
  return entities.reduce((acc, entity) => {
    const domain = entity.domain || 'unknown';
    if (!acc[domain]) acc[domain] = [];
    acc[domain].push(entity);
    return acc;
  }, {} as Record<string, Entity[]>);
}

function getDomainIcon(domain: string): string {
  const icons: Record<string, string> = {
    light: '💡',
    sensor: '📊',
    switch: '🔌',
    climate: '🌡️',
    camera: '📷',
    lock: '🔒',
    cover: '🚪',
    binary_sensor: '🔘',
    media_player: '🎵',
    vacuum: '🤖',
    fan: '🌀',
    automation: '⚙️',
    script: '📝',
    scene: '🎭',
    person: '👤',
    device_tracker: '📍',
    sun: '☀️',
    weather: '🌤️',
  };
  
  return icons[domain] || '🔌';
}

