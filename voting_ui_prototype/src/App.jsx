import PerfTimeseriesChart from './PerfTimeseriesChart'

export default function App() {
  return (
    <div style={{ padding: '40px 32px' }}>
      <h2 style={{ fontFamily: 'system-ui', marginBottom: 24 }}>
        Performance Dashboard Prototype
      </h2>
      <PerfTimeseriesChart />
    </div>
  )
}