import { MapContainer, TileLayer, GeoJSON, LayersControl } from 'react-leaflet';

const PIPELINE_COLORS = [
  '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
  '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
  '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
];

function getColor(index) {
  return PIPELINE_COLORS[index % PIPELINE_COLORS.length];
}

function pipelineStyle(feature, index) {
  return {
    color: getColor(index),
    weight: 3,
    opacity: 0.8,
  };
}

function onEachFeature(feature, layer) {
  const { name, objectid, shape_leng } = feature.properties;
  const lengthKm = shape_leng ? (parseFloat(shape_leng) / 1000).toFixed(1) : 'N/A';
  layer.bindPopup(`
    <strong>${name || 'Unnamed Pipeline'}</strong><br/>
    ID: ${objectid}<br/>
    Length: ${lengthKm} km
  `);
}

export default function MapView({ data }) {
  const featureCount = data.features?.length ?? 0;
  const pipelineNames = [...new Set(
    (data.features || []).map((f) => f.properties?.name).filter(Boolean)
  )];

  return (
    <div className="map-wrapper">
      <div className="sidebar">
        <h2>Pipeline & Asset Monitor</h2>
        <div className="sidebar-stats">
          <p><strong>Total Segments:</strong> {featureCount}</p>
          <p><strong>Pipelines:</strong> {pipelineNames.length}</p>
        </div>
        <div className="pipeline-list">
          <h3>Pipelines</h3>
          <ul>
            {pipelineNames.map((name, i) => (
              <li key={name}>
                <span className="color-swatch" style={{ background: getColor(i) }} />
                {name}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="map-container">
        <MapContainer
          center={[49.5, -110.0]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
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

          <GeoJSON
            key={featureCount}
            data={data}
            style={(feature) => {
              const idx = data.features.indexOf(feature);
              return pipelineStyle(feature, idx);
            }}
            onEachFeature={onEachFeature}
          />
        </MapContainer>
      </div>
    </div>
  );
}
