import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Dot } from 'recharts';

const API_URL = 'http://localhost:8000';

const SENSOR_CONFIG = {
  temperature: { color: '#ff7300', unit: '°C', threshold: 80 },
  pressure: { color: '#387908', unit: 'PSI', threshold: 150 },
  vibration: { color: '#8884d8', unit: 'Hz', threshold: 10 },
  acoustic: { color: '#0088fe', unit: 'dB', threshold: 90 }
};

const CustomizedDot = (props) => {
  const { cx, cy, payload, threshold } = props;

  if (payload.value > threshold) {
    return (
      <circle cx={cx} cy={cy} r={5} fill="red" stroke="none" />
    );
  }

  return null;
};

const SensorChart = ({ type, data }) => {
  const config = SENSOR_CONFIG[type];
  const sensorData = data.filter(d => d.sensor_type === type);

  return (
    <div style={{ flex: '1 1 45%', minWidth: '300px', height: '250px', background: '#f9f9f9', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
      <h3 style={{ margin: '0 0 10px 0', textTransform: 'capitalize' }}>
        {type} ({config.unit}) 
        <span style={{ fontSize: '0.7em', color: '#666', marginLeft: '10px' }}>Threshold: {config.threshold}</span>
      </h3>
      <ResponsiveContainer width="100%" height="80%">
        <LineChart data={sensorData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleTimeString()} />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip labelFormatter={(t) => new Date(t).toLocaleString()} />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={config.color} 
            name={type} 
            strokeWidth={2}
            dot={<CustomizedDot threshold={config.threshold} />}
            activeDot={{ r: 8 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

function App() {
  const [data, setData] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [intervalSec, setIntervalSec] = useState(5);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${API_URL}/simulator/status`);
        setIsPaused(!res.data.active);
        setIntervalSec(res.data.interval);
      } catch (err) {
        console.error("Error fetching status:", err);
      }
    };
    fetchStatus();

    const fetchData = async () => {
      try {
        const [dataRes, notifyRes] = await Promise.all([
          axios.get(`${API_URL}/data?limit=100`),
          axios.get(`${API_URL}/notifications?limit=10`)
        ]);
        const sortedData = dataRes.data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        setData(sortedData);
        setNotifications(notifyRes.data);
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [isPaused]);

  const handleIntervalChange = async (e) => {
    let val = parseInt(e.target.value);
    if (isNaN(val)) return;
    setIntervalSec(val);
    if (val >= 5 && val <= 30) {
        try {
            await axios.post(`${API_URL}/simulator/interval?seconds=${val}`);
        } catch (err) {
            console.error("Error setting interval:", err);
        }
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', backgroundColor: 'white', padding: '15px 25px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h1 style={{ margin: 0, color: '#1a1a1a' }}>Data Pipeline Monitor</h1>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <label htmlFor="interval" style={{ fontWeight: 'bold' }}>Frequency (5-30s):</label>
            <input 
              id="interval"
              type="number" 
              min="5" 
              max="30" 
              value={intervalSec} 
              onChange={handleIntervalChange}
              style={{ padding: '8px', width: '60px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>

          <button 
            onClick={async () => {
              await axios.post(`${API_URL}/simulator/${isPaused ? 'resume' : 'pause'}`);
              setIsPaused(!isPaused);
            }}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: 'bold',
              backgroundColor: isPaused ? '#4CAF50' : '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'background-color 0.3s'
            }}
          >
            {isPaused ? '▶ Start Simulator' : '⏸ Pause Simulator'}
          </button>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: '25px', flexWrap: 'wrap' }}>
        <div style={{ flex: '3 1 600px', display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
          {Object.keys(SENSOR_CONFIG).map(type => (
            <SensorChart key={type} type={type} data={data} />
          ))}
        </div>

        <div style={{ flex: '1 1 300px', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', borderTop: '5px solid #d32f2f', maxHeight: '550px', overflowY: 'auto' }}>
          <h3 style={{ color: '#d32f2f', marginTop: 0 }}>Active Alerts</h3>
          <div>
            {notifications.map(n => (
              <div key={n.id} style={{ borderBottom: '1px solid #f0f0f0', padding: '12px 0' }}>
                <span style={{ fontWeight: 'bold', color: SENSOR_CONFIG[n.sensor_type]?.color }}>{n.sensor_type.toUpperCase()}</span>
                <div style={{ fontWeight: '500', margin: '4px 0' }}>{n.message}</div>
                <div style={{ fontSize: '0.8em', color: '#888' }}>
                  {new Date(n.timestamp).toLocaleString()} | Val: {n.value.toFixed(2)}
                </div>
              </div>
            ))}
            {notifications.length === 0 && <p style={{ color: '#999', fontStyle: 'italic' }}>No alerts detected.</p>}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '30px', background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3 style={{ marginTop: 0 }}>Recent Data Logs</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '2px solid #eee' }}>
              <th style={{ padding: '12px' }}>Sensor</th>
              <th style={{ padding: '12px' }}>Value</th>
              <th style={{ padding: '12px' }}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {[...data].reverse().slice(0, 10).map(d => (
              <tr key={d.id} style={{ borderBottom: '1px solid #f9f9f9' }}>
                <td style={{ padding: '12px', fontWeight: 'bold', color: SENSOR_CONFIG[d.sensor_type]?.color }}>{d.sensor_type}</td>
                <td style={{ padding: '12px' }}>{d.value.toFixed(2)}</td>
                <td style={{ padding: '12px', color: '#666' }}>{new Date(d.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
