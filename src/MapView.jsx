import { useMemo, useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  Popup,
  LayersControl,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

// ── Leaflet div-icon factory ──────────────────────────────────────
function assetIcon(type, status) {
  const color = { normal: '#22c55e', warning: '#eab308', alarm: '#ef4444' }[status] || '#999';
  const shape = type === 'sensor' ? 'circle' : 'diamond';
  const inner = type === 'sensor' ? 'S' : 'V';

  const html = shape === 'circle'
    ? `<div style="
        width:28px;height:28px;border-radius:50%;background:${color};
        border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);
        display:flex;align-items:center;justify-content:center;
        color:#fff;font-weight:700;font-size:12px;">${inner}</div>`
    : `<div style="
        width:28px;height:28px;transform:rotate(45deg);background:${color};
        border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);
        display:flex;align-items:center;justify-content:center;">
        <span style="transform:rotate(-45deg);color:#fff;font-weight:700;font-size:11px;">${inner}</span></div>`;

  return L.divIcon({
    className: '',
    html,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

// ── GeoJSON style ─────────────────────────────────────────────────
const PIPELINE_COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
];
function pipelineStyle(feature, index) {
  return {
    color: PIPELINE_COLORS[(index || 0) % PIPELINE_COLORS.length],
    weight: 3,
    opacity: 0.6,
  };
}
function onEachFeature(feature, layer) {
  const { name, objectid } = feature.properties;
  layer.bindPopup(`<strong>${name || 'Pipeline'}</strong><br/>ID: ${objectid}`);
}

// ── Fly-to-selected helper ────────────────────────────────────────
function FlyTo({ asset }) {
  const map = useMap();
  const prevId = useRef(null);

  useEffect(() => {
    if (asset && asset.id !== prevId.current) {
      map.flyTo([asset.latitude, asset.longitude], 12, { duration: 0.8 });
      prevId.current = asset.id;
    }
  }, [asset, map]);

  return null;
}

// ── Main component ────────────────────────────────────────────────
export default function MapView({ assets, geoData, selectedAsset, onSelectAsset, lastUpdate }) {
  // Map pipeline name → index of its first feature occurrence (for stable legend colour)
  const pipelineNameIndex = useMemo(() => {
    if (!geoData?.features) return new Map();
    const seen = new Map();
    geoData.features.forEach((f, i) => {
      const name = f.properties?.name;
      if (name && !seen.has(name)) seen.set(name, i);
    });
    return seen;
  }, [geoData]);

  const statusCounts = useMemo(() => {
    const counts = { normal: 0, warning: 0, alarm: 0 };
    assets.forEach((a) => { counts[a.status] = (counts[a.status] || 0) + 1; });
    return counts;
  }, [assets]);

  const selectedData = assets.find((a) => a.id === selectedAsset?.id);

  return (
    <div className="map-wrapper">
      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <div className="sidebar">
        <h2>Pipeline & Asset Monitor</h2>

        <div className="sidebar-stats">
          <p><strong>Assets:</strong> {assets.length}</p>
          <p>
            <span className="stat-dot" style={{ background: '#22c55e' }} /> {statusCounts.normal} normal
            {'  '}
            <span className="stat-dot" style={{ background: '#eab308' }} /> {statusCounts.warning} warning
            {'  '}
            <span className="stat-dot" style={{ background: '#ef4444' }} /> {statusCounts.alarm} alarm
          </p>
          {lastUpdate && (
            <p className="last-update">Updated: {lastUpdate.toLocaleTimeString()}</p>
          )}
        </div>

        {/* ── Asset list ─────────────────────────────────────── */}
        <h3>Assets</h3>
        <ul className="asset-list">
          {assets.map((a) => (
            <li
              key={a.id}
              className={`asset-item ${selectedAsset?.id === a.id ? 'selected' : ''}`}
              onClick={() => onSelectAsset(selectedAsset?.id === a.id ? null : a)}
            >
              <span className={`status-dot status-${a.status}`} title={a.status} />
              <span className="asset-type-badge">{a.type === 'sensor' ? 'S' : 'V'}</span>
              <div className="asset-item-info">
                <span className="asset-item-name">{a.name}</span>
                {a.latestReading && (
                  <span className="asset-item-reading">
                    {a.latestReading.temperature.toFixed(0)}°C / {a.latestReading.pressure.toFixed(0)} PSI
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>

        {/* ── Pipeline legend ─────────────────────────────────── */}
        <h3>Pipelines</h3>
        <ul className="pipeline-list">
          {[...pipelineNameIndex].map(([name, idx]) => (
            <li key={name}>
              <span className="color-swatch" style={{ background: PIPELINE_COLORS[idx % PIPELINE_COLORS.length] }} />
              {name}
            </li>
          ))}
        </ul>
      </div>

      {/* ── Map ──────────────────────────────────────────────────── */}
      <div className="map-container">
        <MapContainer
          center={[45.8, -65.8]}
          zoom={7}
          style={{ height: '100%', width: '100%' }}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
            <LayersControl.BaseLayer name="Satellite">
              <TileLayer
                attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />
            </LayersControl.BaseLayer>
          </LayersControl>

          {/* Pipeline lines */}
          {geoData && (
            <GeoJSON
              data={geoData}
              style={(feature) => {
                const idx = geoData.features.indexOf(feature);
                return pipelineStyle(feature, idx);
              }}
              onEachFeature={onEachFeature}
            />
          )}

          {/* Asset markers */}
          {assets.map((asset) => (
            <Marker
              key={asset.id}
              position={[asset.latitude, asset.longitude]}
              icon={assetIcon(asset.type, asset.status)}
              eventHandlers={{
                click: () => onSelectAsset(asset),
              }}
            >
              <Popup>
                <div className="popup-content">
                  <strong>{asset.name}</strong>
                  <div className={`popup-status status-${asset.status}`}>
                    {asset.status.toUpperCase()}
                  </div>
                  <table className="popup-table">
                    <tbody>
                      <tr><td>Type:</td><td>{asset.type}</td></tr>
                      {asset.latestReading && (
                        <>
                          <tr><td>Temp:</td><td>{asset.latestReading.temperature.toFixed(1)}°C</td></tr>
                          <tr><td>Pressure:</td><td>{asset.latestReading.pressure.toFixed(1)} PSI</td></tr>
                          <tr><td>Time:</td><td>{new Date(asset.latestReading.timestamp).toLocaleTimeString()}</td></tr>
                        </>
                      )}
                    </tbody>
                  </table>
                </div>
              </Popup>
            </Marker>
          ))}

          <FlyTo asset={selectedAsset} />
        </MapContainer>
      </div>

      {/* ── Detail panel ────────────────────────────────────────── */}
      {selectedData && (
        <div className="detail-panel">
          <button className="detail-close" onClick={() => onSelectAsset(null)}>&times;</button>
          <h3>{selectedData.name}</h3>
          <div className={`detail-status status-${selectedData.status}`}>
            {selectedData.status.toUpperCase()}
          </div>
          <table>
            <tbody>
              <tr><td>Type</td><td>{selectedData.type}</td></tr>
              <tr><td>Coordinates</td><td>{selectedData.latitude.toFixed(4)}, {selectedData.longitude.toFixed(4)}</td></tr>
              <tr><td>Updated</td><td>{new Date(selectedData.updatedAt).toLocaleString()}</td></tr>
              {selectedData.latestReading && (
                <>
                  <tr><td>Temperature</td><td className="val-temp">{selectedData.latestReading.temperature.toFixed(1)}°C</td></tr>
                  <tr><td>Pressure</td><td className="val-pres">{selectedData.latestReading.pressure.toFixed(1)} PSI</td></tr>
                </>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
