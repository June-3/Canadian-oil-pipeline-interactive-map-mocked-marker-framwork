import { useState, useEffect } from 'react';
import MapView from './MapView';

export default function App() {
  const [geoData, setGeoData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/Pipelines.geojson')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setGeoData(data))
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="error-container">
        <p>Failed to load GeoJSON: {error}</p>
      </div>
    );
  }

  if (!geoData) {
    return <div className="loading-container">Loading map data...</div>;
  }

  return <MapView data={geoData} />;
}
