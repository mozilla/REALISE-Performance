'use client';

import * as React from 'react';
import {
  ComposedChart,
  Scatter,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

// Original display of the mocked example:
// https://treeherder.mozilla.org/perfherder/graphs?highlightAlerts=1&highlightChangelogData=0&highlightCommonAlerts=0&highlightInitialDataPoints=0&replicates=0&series=autoland,5304496,1,1

// ---------------------------------------------------------------------------
// API endpoints
// Timeseries is proxied via Vite (/api → https://123.org).
// Alerts are fetched directly — the sql.telemetry.mozilla.org endpoint
// returns JSON even though the browser downloads it as a file; fetch() has
// no such restriction.
// ---------------------------------------------------------------------------
const TIMESERIES_API_URL = '/api';
const ALERTS_API_URL     = 'https://sql.telemetry.mozilla.org/api/queries/117898/results.json?api_key=uxgQwqWKeymE0K4EF62Dp3WjfpfZttZxGp0oZh9c';

// ---------------------------------------------------------------------------
// Time range options
// ---------------------------------------------------------------------------
const TIME_RANGES = [
  { label: 'Last day',     days: 1   },
  { label: 'Last 2 days',  days: 2   },
  { label: 'Last 7 days',  days: 7   },
  { label: 'Last 14 days', days: 14  },
  { label: 'Last 30 days', days: 30  },
  { label: 'Last 60 days', days: 60  },
  { label: 'Last 90 days', days: 90  },
  { label: 'Last year',    days: 365 },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatAxisDate(ts) {
  const d = new Date(ts);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatFullDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    year: 'numeric', hour: '2-digit', minute: '2-digit',
    timeZoneName: 'short',
  });
}

function shortRevision(rev) {
  return rev ? rev.slice(0, 12) : '—';
}

// ---------------------------------------------------------------------------
// Detection method parser
// Handles: "priority_voting_3_min_method_agreement_1_tolerance_replicates_not_enabled"
// Falls back gracefully for plain values like "student".
// ---------------------------------------------------------------------------
function parseDetectionMethod(raw) {
  if (!raw) return null;
  const m = raw.match(
    /^(\w+)_voting_(\d+)_min_method_agreement_(\d+)_tolerance_replicates_(not_enabled|enabled)$/
  );
  if (m) {
    return [
      { label: 'Voting',           value: m[1] },
      { label: 'Min. votes',       value: m[2] },
      { label: 'Min. method agr.', value: m[3] },
      { label: 'Replicates',       value: m[4] === 'not_enabled' ? 'disabled' : 'enabled' },
    ];
  }
  return [{ label: 'Detection', value: raw }];
}

// ---------------------------------------------------------------------------
// Alert row parser
// Confirmed shape from https://sql.telemetry.mozilla.org/api/queries/117898/…
// The response is: { query_result: { data: { rows: [...] } } }
// Each row has: id, push_id, created, new_value, prev_value, amount_abs,
//               amount_pct, status (int), detection_method, confidences
// ---------------------------------------------------------------------------
function parseAlertRow(r) {
  return {
    id:               r.id,
    push_id:          r.push_id,
    revision:         null,
    push_timestamp:   null,
    submit_time:      r.created,
    new_value:        r.new_value,
    prev_value:       r.prev_value,
    amount_abs:       r.amount_abs,
    amount_pct:       r.amount_pct,
    status:           r.status === 0 ? 'untriaged' : 'triaged',
    infra_affected:   false,
    platform:         'linux2404-64-shippable',
    repository:       'autoland',
    detection_method: r.detection_method ?? null,
    confidences:      r.confidences ?? null,
  };
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const CARD_WIDTH        = 340;
const POINTER_SIZE      = 8;
const CHART_LEFT_MARGIN = 70;

// ---------------------------------------------------------------------------
// Alert tooltip card
// ---------------------------------------------------------------------------
function AlertTooltipCard({ alert, onClose, onMouseEnter, onMouseLeave, side }) {
  if (!alert) return null;

  const deltaSign  = alert.amount_abs >= 0 ? '+' : '';
  const deltaColor = alert.amount_abs < 0 ? '#4fc3a1' : '#e57373';
  const detection  = parseDetectionMethod(alert.detection_method);

  const confidenceRows = alert.confidences
    ? Object.entries(alert.confidences)
        .map(([method, data]) => ({
          method,
          confidence:      data.confidence,
          change_detected: data.change_detected,
        }))
        .sort((a, b) => {
          if (a.change_detected !== b.change_detected) return b.change_detected - a.change_detected;
          return (a.confidence ?? 1) - (b.confidence ?? 1);
        })
    : [];

  const pointerStyle = side === 'right'
    ? {
        position: 'absolute', top: -POINTER_SIZE, left: POINTER_SIZE,
        width: 0, height: 0,
        borderBottom: `${POINTER_SIZE}px solid rgba(20, 20, 20, 0.82)`,
        borderLeft:   `${POINTER_SIZE}px solid transparent`,
        borderRight:  `${POINTER_SIZE}px solid transparent`,
      }
    : {
        position: 'absolute', top: -POINTER_SIZE, right: POINTER_SIZE,
        width: 0, height: 0,
        borderBottom: `${POINTER_SIZE}px solid rgba(20, 20, 20, 0.82)`,
        borderLeft:   `${POINTER_SIZE}px solid transparent`,
        borderRight:  `${POINTER_SIZE}px solid transparent`,
      };

  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{ position: 'relative', width: CARD_WIDTH, pointerEvents: 'auto' }}
    >
      <div style={pointerStyle} />

      <div style={{
        background:           'rgba(20, 20, 20, 0.82)',
        backdropFilter:       'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        color:                '#e8e8e8',
        borderRadius:         10,
        padding:              '14px 16px',
        boxShadow:            '0 6px 28px rgba(0,0,0,0.4)',
        border:               '1px solid rgba(255,255,255,0.08)',
        fontFamily:           'inherit',
      }}>

        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 10, right: 10,
            background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 6,
            color: '#ccc', cursor: 'pointer', width: 22, height: 22,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13,
          }}
          aria-label="Close"
        >×</button>

        {/* Repository + platform */}
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: '#fff' }}>
            ({alert.repository})
          </span>
          <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{alert.platform}</div>
        </div>

        {/* Value */}
        <div style={{ marginBottom: 3 }}>
          <span style={{ fontSize: 19, fontWeight: 700, color: '#fff' }}>
            {alert.new_value != null ? alert.new_value.toFixed(2) : '—'} ms
          </span>{' '}
          <span style={{ fontSize: 11, color: '#7ecfb3' }}>(lower is better)</span>
        </div>

        {/* Delta */}
        <div style={{ fontSize: 12, color: deltaColor, marginBottom: 6 }}>
          Δ {deltaSign}{alert.amount_abs != null ? alert.amount_abs.toFixed(2) : '—'}{' '}
          ({deltaSign}{alert.amount_pct != null ? alert.amount_pct.toFixed(1) : '—'}%)
        </div>

        {/* Infra warning */}
        {alert.infra_affected && (
          <div style={{ fontSize: 11, color: '#f4a93a', marginBottom: 6 }}>
            Could be affected by infra changes.
          </div>
        )}

        {/* Detection method */}
        {detection && (
          <div style={{
            background: 'rgba(255,255,255,0.06)',
            borderRadius: 5,
            padding: '5px 8px',
            marginBottom: 10,
            display: 'flex',
            flexWrap: 'wrap',
            gap: '3px 12px',
          }}>
            {detection.map(({ label, value }) => (
              <span key={label} style={{ fontSize: 11 }}>
                <span style={{ color: '#777' }}>{label}: </span>
                <span style={{ color: '#fff', fontWeight: 500 }}>{value}</span>
              </span>
            ))}
          </div>
        )}

        {/* Confidences table */}
        {confidenceRows.length > 0 && (
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 11, color: '#888', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Detection methods
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left',   color: '#666', fontWeight: 400, paddingBottom: 4, paddingRight: 8 }}>Method</th>
                  <th style={{ textAlign: 'right',  color: '#666', fontWeight: 400, paddingBottom: 4, paddingRight: 8 }}>Confidence</th>
                  <th style={{ textAlign: 'center', color: '#666', fontWeight: 400, paddingBottom: 4 }}>Detected</th>
                </tr>
              </thead>
              <tbody>
                {confidenceRows.map(({ method, confidence, change_detected }) => {
                  const detected = change_detected === true;
                  const rowBg    = detected ? 'rgba(79,195,161,0.08)' : 'rgba(229,115,115,0.08)';
                  const dotColor = detected ? '#4fc3a1' : '#e57373';
                  const confStr  = confidence != null ? confidence.toFixed(4) : '—';
                  return (
                    <tr key={method} style={{ background: rowBg }}>
                      <td style={{
                        padding: '3px 8px 3px 4px', color: '#ddd',
                        fontFamily: 'monospace', borderLeft: `3px solid ${dotColor}`,
                      }}>
                        {method}
                      </td>
                      <td style={{ textAlign: 'right', padding: '3px 8px', color: '#ccc', fontFamily: 'monospace' }}>
                        {confStr}
                      </td>
                      <td style={{ textAlign: 'center', padding: '3px 4px' }}>
                        <span style={{
                          display: 'inline-block', width: 8, height: 8,
                          borderRadius: '50%', background: dotColor,
                        }} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Revision */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
          <span style={{ color: '#5eb8ff', fontSize: 11, fontFamily: 'monospace' }}>
            {shortRevision(alert.revision)}
          </span>
          {alert.revision && (
            <button
              onClick={() => navigator.clipboard?.writeText(alert.revision)}
              style={{ background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 3, cursor: 'pointer', padding: '1px 5px', color: '#ccc', fontSize: 10 }}
              title="Copy revision"
            >⧉</button>
          )}
        </div>

        {/* Alert # */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <span style={{ fontSize: 12, color: '#f4a93a' }}>⚠</span>
          <span style={{ color: '#5eb8ff', fontSize: 12, fontWeight: 500 }}>Alert # {alert.id}</span>
          <span style={{ color: '#aaa', fontSize: 12 }}>- {alert.status}</span>
          <button
            onClick={() => navigator.clipboard?.writeText(String(alert.id))}
            style={{ background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: 3, cursor: 'pointer', padding: '1px 5px', color: '#ccc', fontSize: 10 }}
            title="Copy alert id"
          >⧉</button>
        </div>

        {/* Timestamps */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 8, fontSize: 11, color: '#aaa', lineHeight: 1.8 }}>
          <div>Push time: {formatFullDate(alert.push_timestamp)}</div>
          <div>Trigger date: {formatFullDate(alert.submit_time)}</div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom dot
// ---------------------------------------------------------------------------
function CustomDot(props) {
  const { cx, cy, payload, alertPushIds, onAlertEnter, onAlertLeave } = props;
  if (cx == null || cy == null) return null;

  const isAlert = alertPushIds.has(payload.push_id);

  if (isAlert) {
    return (
      <circle
        cx={cx} cy={cy} r={7}
        fill="#5eb8ff" stroke="#fff" strokeWidth={2}
        style={{ cursor: 'pointer' }}
        onMouseEnter={() => onAlertEnter(payload, cx, cy)}
        onMouseLeave={onAlertLeave}
      />
    );
  }

  return <circle cx={cx} cy={cy} r={4} fill="#3a3f8f" fillOpacity={0.85} />;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function PerfTimeseriesChart() {
  const [rangeDays, setRangeDays]       = React.useState(14);
  const [rawData, setRawData]           = React.useState([]);
  const [alerts, setAlerts]             = React.useState([]);
  const [loading, setLoading]           = React.useState(false);
  const [alertsLoading, setAlertsLoading] = React.useState(false);
  const [error, setError]               = React.useState(null);
  const [alertsError, setAlertsError]   = React.useState(null);
  const [activeAlert, setActiveAlert]   = React.useState(null);

  const hideTimer       = React.useRef(null);
  const chartWrapperRef = React.useRef(null);

  // ---------------------------------------------------------------------------
  // Fetch timeseries — proxied via Vite to https://123.org
  // ---------------------------------------------------------------------------
  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(TIMESERIES_API_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json) => {
        if (cancelled) return;
        const series = Array.isArray(json) ? json[0] : json;
        setRawData(series?.data ?? []);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  // ---------------------------------------------------------------------------
  // Fetch alerts — direct fetch to sql.telemetry.mozilla.org.
  // The server sends Content-Disposition: attachment which causes the browser
  // to download when navigating, but fetch() ignores that header entirely.
  // Response shape: { query_result: { data: { rows: [...] } } }
  // ---------------------------------------------------------------------------
  React.useEffect(() => {
    let cancelled = false;
    setAlertsLoading(true);
    setAlertsError(null);

    fetch(ALERTS_API_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`Alerts API HTTP ${r.status}`);
        return r.json();
      })
      .then((json) => {
        if (cancelled) return;
        const rows = json?.query_result?.data?.rows;
        if (!rows) throw new Error('Unexpected alerts response shape');
        setAlerts(rows.map(parseAlertRow));
        setAlertsLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setAlertsError(err.message);
        setAlertsLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  // ---------------------------------------------------------------------------
  // Derived data
  // ---------------------------------------------------------------------------
  const alertPushIds = React.useMemo(
    () => new Set(alerts.map((a) => a.push_id)),
    [alerts]
  );

  const alertByPushId = React.useMemo(
    () => Object.fromEntries(alerts.map((a) => [a.push_id, a])),
    [alerts]
  );

  const chartData = React.useMemo(() => {
    const cutoff = Date.now() - rangeDays * 86400 * 1000;
    return rawData
      .filter((d) => new Date(d.push_timestamp).getTime() >= cutoff)
      .map((d) => ({ ...d, ts: new Date(d.push_timestamp).getTime() }))
      .sort((a, b) => a.ts - b.ts);
  }, [rawData, rangeDays]);

  const { yMin, yMax } = React.useMemo(() => {
    if (!chartData.length) return { yMin: 0, yMax: 1000 };
    const vals = chartData.map((d) => d.value);
    const min  = Math.min(...vals);
    const max  = Math.max(...vals);
    const pad  = (max - min) * 0.1 || max * 0.1;
    return { yMin: Math.max(0, min - pad), yMax: max + pad };
  }, [chartData]);

  const alertLines = React.useMemo(() => {
    const seen = new Set();
    return alerts
      .map((a) => {
        const pt = chartData.find((d) => d.push_id === a.push_id);
        if (!pt || seen.has(a.push_id)) return null;
        seen.add(a.push_id);
        return { ts: pt.ts, alert: a };
      })
      .filter(Boolean);
  }, [chartData, alerts]);

  // ---------------------------------------------------------------------------
  // Hover handlers
  // ---------------------------------------------------------------------------
  function scheduleHide() {
    hideTimer.current = setTimeout(() => setActiveAlert(null), 300);
  }

  function cancelHide() {
    clearTimeout(hideTimer.current);
  }

  function handleAlertEnter(payload, cx, cy) {
    cancelHide();
    const alert = alertByPushId[payload.push_id];
    if (!alert) return;

    const containerWidth = chartWrapperRef.current?.offsetWidth ?? 900;
    const dotX = cx + CHART_LEFT_MARGIN;
    const side = (dotX + CARD_WIDTH + 16 <= containerWidth) ? 'right' : 'left';

    setActiveAlert({
      alert: {
        ...alert,
        revision:       payload.revision,
        push_timestamp: payload.push_timestamp,
      },
      dotX,
      dotY: cy,
      side,
    });
  }

  function renderDot(props) {
    return (
      <CustomDot
        {...props}
        alertPushIds={alertPushIds}
        onAlertEnter={handleAlertEnter}
        onAlertLeave={scheduleHide}
      />
    );
  }

  const cardLeft = activeAlert
    ? activeAlert.side === 'right'
      ? activeAlert.dotX + 12
      : activeAlert.dotX - CARD_WIDTH - 12
    : 0;

  const cardTop = activeAlert ? activeAlert.dotY - POINTER_SIZE : 0;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: '20px 24px' }}>

      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <select
          value={rangeDays}
          onChange={(e) => { setRangeDays(Number(e.target.value)); setActiveAlert(null); }}
          style={{
            padding: '6px 12px', borderRadius: 6, border: '1px solid #ccc',
            fontSize: 14, cursor: 'pointer', background: '#fff', color: '#222',
          }}
        >
          {TIME_RANGES.map((r) => (
            <option key={r.days} value={r.days}>{r.label}</option>
          ))}
        </select>

        <span style={{ fontSize: 13, color: '#888' }}>
          {loading ? 'Loading timeseries…' : `${chartData.length} data points`}
        </span>

        <span style={{ fontSize: 13, color: '#888' }}>
          {alertsLoading
            ? '· loading alerts…'
            : alertsError
              ? `· ⚠ alerts error: ${alertsError}`
              : `· ${alerts.length} alert${alerts.length !== 1 ? 's' : ''} loaded`
          }
        </span>

        {error && (
          <span style={{ fontSize: 13, color: '#c0392b' }}>⚠ {error}</span>
        )}
      </div>

      {/* Chart wrapper */}
      <div ref={chartWrapperRef} style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={280} minWidth={900}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 24, bottom: 10, left: CHART_LEFT_MARGIN }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />

            <XAxis
              dataKey="ts"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              tickFormatter={formatAxisDate}
              tickCount={8}
              tick={{ fontSize: 12, fill: '#666' }}
              axisLine={{ stroke: '#ccc' }}
              tickLine={false}
            />

            <YAxis
              domain={[yMin, yMax]}
              tickFormatter={(v) => `${Math.round(v).toLocaleString()}`}
              tick={{ fontSize: 12, fill: '#666' }}
              axisLine={false}
              tickLine={false}
              label={{
                value: 'ms', angle: -90, position: 'insideLeft',
                offset: -10, style: { fontSize: 12, fill: '#999' },
              }}
            />

            {alertLines.map(({ ts, alert }) => (
              <ReferenceLine
                key={alert.id}
                x={ts}
                stroke="#5eb8ff"
                strokeWidth={1.5}
                strokeDasharray="4 3"
              />
            ))}

            <Line
              type="monotone"
              dataKey="value"
              stroke="#3a3f8f"
              strokeWidth={1.5}
              dot={false}
              activeDot={false}
              connectNulls
            />

            <Scatter dataKey="value" shape={renderDot} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Tooltip overlay */}
        {activeAlert && (
          <div style={{
            position:      'absolute',
            left:          cardLeft,
            top:           cardTop,
            zIndex:        100,
            pointerEvents: 'none',
          }}>
            <AlertTooltipCard
              alert={activeAlert.alert}
              side={activeAlert.side}
              onClose={() => { cancelHide(); setActiveAlert(null); }}
              onMouseEnter={cancelHide}
              onMouseLeave={scheduleHide}
            />
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 20, marginTop: 16, fontSize: 12, color: '#666' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3a3f8f', display: 'inline-block' }} />
          Measurement
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#5eb8ff', border: '2px solid #fff', outline: '1.5px solid #5eb8ff', display: 'inline-block' }} />
          Alert (hover to inspect)
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 18, height: 2, background: '#5eb8ff', opacity: 0.7, display: 'inline-block' }} />
          Alert boundary
        </span>
      </div>
    </div>
  );
}
