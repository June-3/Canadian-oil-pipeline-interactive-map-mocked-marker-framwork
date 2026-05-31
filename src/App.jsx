import { useState, useEffect, useCallback } from 'react';
import MapView from './MapView';

export default function App() {
  const [assets, setAssets] = useState([]);
  const [geoData, setGeoData] = useState(null);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchAssets = useCallback(async () => {
    try {
      const res = await fetch('/api/assets');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAssets(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load GeoJSON (pipeline lines) once
  useEffect(() => {
    fetch('/Pipelines.geojson')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setGeoData(data))
      .catch(() => {}); // GeoJSON is optional — map still works without it
  }, []);

  // Poll for asset data
  useEffect(() => {
    fetchAssets();
    const interval = setInterval(fetchAssets, 10_000); // every 10s
    return () => clearInterval(interval);
  }, [fetchAssets]);

  if (loading && assets.length === 0) {
    return <div className="loading-container">Loading assets...</div>;
  }

  return (
    <div className="app-root">
      {error && (
        <div className="api-banner">
          API unavailable: {error} — retrying every 10s...
        </div>
      )}
      <MapView
        assets={assets}
        geoData={geoData}
        selectedAsset={selectedAsset}
        onSelectAsset={setSelectedAsset}
        lastUpdate={lastUpdate}
      />
    </div>
  );
}
