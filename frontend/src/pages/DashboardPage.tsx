import React, { useEffect, useState } from 'react';
import { useData } from '../DataContext';
import { getDashboardOverview, getQualityScore, getDashboardChart } from '../api';
import { motion } from 'framer-motion';
import { AlertCircle, PieChart, Activity, Database, FileDigit } from 'lucide-react';
import Plot from 'react-plotly.js';

const DashboardPage: React.FC = () => {
  const { dataset } = useData();
  const [loading, setLoading] = useState(false);
  
  const [overview, setOverview] = useState<any>(null);
  const [quality, setQuality] = useState<any>(null);
  const [numerical, setNumerical] = useState<any>(null);
  const [categorical, setCategorical] = useState<any>(null);
  const [correlation, setCorrelation] = useState<any>(null);
  const [outliers, setOutliers] = useState<any>(null);

  useEffect(() => {
    if (!dataset) return;
    fetchDashboard();
  }, [dataset]);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const [ov, q, num, cat, corr, out] = await Promise.all([
        getDashboardOverview(dataset!.filename).catch(() => null),
        getQualityScore(dataset!.filename, dataset!.filename).catch(() => null), // Assuming same for now if no cleaned tracking
        getDashboardChart('numerical', dataset!.filename).catch(() => null),
        getDashboardChart('categorical', dataset!.filename).catch(() => null),
        getDashboardChart('correlation', dataset!.filename).catch(() => null),
        getDashboardChart('outlier_summary', dataset!.filename, dataset!.filename, dataset!.filename).catch(() => null),
      ]);
      setOverview(ov);
      setQuality(q);
      setNumerical(num);
      setCategorical(cat);
      setCorrelation(corr);
      setOutliers(out);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page-container center-empty">
        <div className="spinner"></div>
        <p>Crunching dashboard metrics...</p>
      </div>
    );
  }

  return (
    <motion.div className="page-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div className="page-header">
        <h1>ML Readiness Dashboard</h1>
        <p>Comprehensive visualizations for the cleaned dataset.</p>
      </div>

      {/* KPI Row */}
      {overview && (
        <div className="dashboard-grid">
          <div className="kpi-card glass-panel" style={{ borderTop: '3px solid #a78bfa' }}>
            <Activity className="kpi-icon primary" />
            <div className="kpi-info">
              <h3>{overview.rows?.toLocaleString()}</h3>
              <p>Total Records</p>
            </div>
          </div>
          <div className="kpi-card glass-panel" style={{ borderTop: '3px solid #60a5fa' }}>
            <FileDigit className="kpi-icon secondary" />
            <div className="kpi-info">
              <h3>{overview.columns?.toLocaleString()}</h3>
              <p>Total Features</p>
            </div>
          </div>
          <div className="kpi-card glass-panel" style={{ borderTop: '3px solid #f87171' }}>
            <AlertCircle className="kpi-icon warning" />
            <div className="kpi-info">
              <h3>{overview.missing_cells?.toLocaleString()}</h3>
              <p>Missing Cells</p>
            </div>
          </div>
          <div className="kpi-card glass-panel" style={{ borderTop: '3px solid #fbbf24' }}>
            <Database className="kpi-icon warning" />
            <div className="kpi-info">
              <h3>{overview.duplicate_rows?.toLocaleString()}</h3>
              <p>Duplicate Rows</p>
            </div>
          </div>
          <div className="kpi-card glass-panel" style={{ borderTop: '3px solid #34d399' }}>
            <PieChart className="kpi-icon success" />
            <div className="kpi-info">
              <h3>{overview.memory_kb?.toLocaleString()} KB</h3>
              <p>Memory Usage</p>
            </div>
          </div>
        </div>
      )}

      {/* Quality Score Row */}
      {quality && (
        <div className="full-width-card glass-panel">
          <h2>🎯 Data Quality Score</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
             <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase' }}>Before Cleaning</div>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#f87171' }}>{quality.raw_score?.toFixed(1)}%</div>
             </div>
             <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase' }}>Improvement</div>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: quality.improvement >= 0 ? '#34d399' : '#f87171' }}>
                  {quality.improvement >= 0 ? '↑' : '↓'} {Math.abs(quality.improvement).toFixed(1)}%
                </div>
             </div>
             <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase' }}>After Cleaning</div>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#34d399' }}>{quality.clean_score?.toFixed(1)}%</div>
             </div>
          </div>
        </div>
      )}

      {/* Numerical Analysis */}
      {numerical && numerical.charts?.length > 0 && (
        <div className="full-width-card glass-panel">
          <h2>📈 Numerical Analysis</h2>
          {numerical.charts.map((chartObj: any) => (
             <div key={chartObj.column} style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '2rem', marginBottom: '2rem' }}>
                <h3 style={{ color: '#a78bfa', marginBottom: '1rem' }}>{chartObj.column}</h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                   <div style={{ flex: '1 1 400px' }}>
                      {chartObj.histogram && (
                        <Plot 
                          data={chartObj.histogram.data} 
                          layout={{...chartObj.histogram.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                          useResizeHandler={true}
                          style={{ width: '100%', height: '350px' }}
                        />
                      )}
                   </div>
                   <div style={{ flex: '1 1 400px' }}>
                      {chartObj.boxplot && (
                        <Plot 
                          data={chartObj.boxplot.data} 
                          layout={{...chartObj.boxplot.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                          useResizeHandler={true}
                          style={{ width: '100%', height: '350px' }}
                        />
                      )}
                   </div>
                </div>
             </div>
          ))}
        </div>
      )}

      {/* Categorical Analysis */}
      {categorical && categorical.charts?.length > 0 && (
        <div className="full-width-card glass-panel">
          <h2>📊 Categorical Analysis</h2>
          {categorical.charts.map((chartObj: any) => (
             <div key={chartObj.column} style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '2rem', marginBottom: '2rem' }}>
                <h3 style={{ color: '#34d399', marginBottom: '1rem' }}>{chartObj.column}</h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                   <div style={{ flex: '1 1 400px' }}>
                      {chartObj.bar_chart && (
                        <Plot 
                          data={chartObj.bar_chart.data} 
                          layout={{...chartObj.bar_chart.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                          useResizeHandler={true}
                          style={{ width: '100%', height: '350px' }}
                        />
                      )}
                   </div>
                   <div style={{ flex: '1 1 400px' }}>
                      {chartObj.pie_chart && (
                        <Plot 
                          data={chartObj.pie_chart.data} 
                          layout={{...chartObj.pie_chart.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                          useResizeHandler={true}
                          style={{ width: '100%', height: '350px' }}
                        />
                      )}
                   </div>
                </div>
             </div>
          ))}
        </div>
      )}

      {/* Correlation Heatmap */}
      {correlation && correlation.chart && (
        <div className="full-width-card glass-panel">
          <h2>🌡️ Correlation Matrix</h2>
          <div style={{ overflowX: 'auto' }}>
            <Plot 
              data={correlation.chart.data} 
              layout={{...correlation.chart.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
              useResizeHandler={true}
              style={{ width: '100%', height: '600px', minWidth: '600px' }}
            />
          </div>
        </div>
      )}
      
      {/* Outliers */}
      {outliers && outliers.summary && (
        <div className="full-width-card glass-panel">
          <h2>⚠️ Outliers Summary</h2>
          <div style={{ overflowX: 'auto' }}>
             <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                     <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Column</th>
                     <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Raw Outliers</th>
                     <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Clean Outliers</th>
                     <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Change</th>
                  </tr>
                </thead>
                <tbody>
                   {outliers.summary.map((row: any) => {
                     const diff = row.clean_count - row.raw_count;
                     return (
                       <tr key={row.column} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                         <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{row.column}</td>
                         <td style={{ padding: '0.75rem' }}>{row.raw_count} ({row.raw_pct}%)</td>
                         <td style={{ padding: '0.75rem' }}>{row.clean_count} ({row.clean_pct}%)</td>
                         <td style={{ padding: '0.75rem', color: diff < 0 ? '#34d399' : (diff > 0 ? '#f87171' : '#94a3b8') }}>
                           {diff > 0 ? '+' : ''}{diff}
                         </td>
                       </tr>
                     );
                   })}
                </tbody>
             </table>
          </div>
        </div>
      )}

    </motion.div>
  );
};

export default DashboardPage;
