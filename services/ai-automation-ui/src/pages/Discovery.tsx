/**
 * Discovery Page
 * 
 * Helps users discover what they can automate with existing devices
 * and provides data-driven device purchase recommendations.
 * 
 * Epic AI-4, Story AI4.3
 */
import React, { useState, useEffect } from 'react';
import { DeviceExplorer } from '../components/discovery/DeviceExplorer';
import { SmartShopping } from '../components/discovery/SmartShopping';

interface DiscoveryPageProps {}

export const DiscoveryPage: React.FC<DiscoveryPageProps> = () => {
  const [userDevices, setUserDevices] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch user's devices from ai-automation-service
    const fetchDevices = async () => {
      try {
        const response = await fetch('http://localhost:8018/api/data/devices');
        if (!response.ok) {
          throw new Error('Failed to fetch devices');
        }
        
        const data = await response.json();
        const deviceTypes = data.devices?.map((d: any) => d.device_type || d.domain) || [];
        
        setUserDevices(deviceTypes);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching devices:', err);
        setError('Failed to load devices. Using demo mode.');
        setUserDevices(['light', 'switch', 'sensor']);  // Demo devices
        setLoading(false);
      }
    };

    fetchDevices();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading discovery features...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Automation Discovery</h1>
        <p className="text-gray-600">
          Discover what you can automate and get smart device recommendations
        </p>
      </div>

      {error && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6">
          <p className="font-bold">Note</p>
          <p>{error}</p>
        </div>
      )}

      <div className="space-y-8">
        {/* Device Explorer Section */}
        <section className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4">Device Explorer</h2>
          <p className="text-gray-600 mb-6">
            See what you can automate with your existing devices
          </p>
          <DeviceExplorer devices={userDevices} />
        </section>

        {/* Smart Shopping Section */}
        <section className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4">Smart Shopping Recommendations</h2>
          <p className="text-gray-600 mb-6">
            Data-driven device suggestions to unlock new automations
          </p>
          <SmartShopping userDevices={userDevices} />
        </section>
      </div>
    </div>
  );
};

export default DiscoveryPage;

