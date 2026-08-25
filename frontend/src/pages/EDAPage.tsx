import React, { useEffect, useState } from 'react';
import { useData } from '../DataContext';
import { getEDAChart, getEDAReport } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, BarChart2, PieChart, Activity, AlertTriangle, Download } from 'lucide-react';
import Plot from 'react-plotly.js';

type Tab = 'numerical' | 'categorical' | 'correlation' | 'outliers' | 'report';

const EDAPage: React.FC = () => {
  const { dataset } = useData();
  const [activeTab, setActiveTab] = useState<Tab>('numerical');
  const [loading, setLoading] = useState(false);
  
  const [numData, setNumData] = useState<any>(null);
  const [catData, setCatData] = useState<any>(null);
  const [corrData, setCorrData] = useState<any>(null);
  const [outlierData, setOutlierData] = useState<any>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    if (!dataset) return;
    fetchAll();
  }, [dataset]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [num, cat, corr, outliers] = await Promise.all([
        getEDAChart('distributions', dataset!.filename).catch(() => null),
        getEDAChart('categorical', dataset!.filename).catch(() => null),
        getEDAChart('correlation', dataset!.filename).catch(() => null),
        getEDAChart('outliers', dataset!.filename).catch(() => null)
      ]);
      setNumData(num);
      setCatData(cat);
      setCorrData(corr);
      setOutlierData(outliers);
    } catch (e) {
      console.error("EDA Fetch Error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const rep = await getEDAReport(dataset!.filename);
      setReportData(rep);
    } catch (e) {
      console.error(e);
      alert("Failed to generate report.");
    } finally {
      setReportLoading(false);
    }
  };

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
        <p>Please upload a dataset first.</p>
      </div>
    );
  }

  return (
    <motion.div className="page-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <h1>Exploratory Data Analysis</h1>
        <p>Deep dive into your dataset's statistical properties and relationships.</p>
      </div>

      <div className="clean-layout" style={{ display: 'flex', gap: '2rem' }}>
        {/* Sidebar */}
        <div className="clean-sidebar" style={{ minWidth: '220px' }}>
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button className={`nav-tab ${activeTab === 'numerical' ? 'active' : ''}`} onClick={() => setActiveTab('numerical')}>
              <BarChart2 size={18} /> 📉 Distributions
            </button>
            <button className={`nav-tab ${activeTab === 'categorical' ? 'active' : ''}`} onClick={() => setActiveTab('categorical')}>
              <PieChart size={18} /> 📊 Categorical
            </button>
            <button className={`nav-tab ${activeTab === 'correlation' ? 'active' : ''}`} onClick={() => setActiveTab('correlation')}>
              <Activity size={18} /> 🌡️ Correlation
            </button>
            <button className={`nav-tab ${activeTab === 'outliers' ? 'active' : ''}`} onClick={() => setActiveTab('outliers')}>
              <AlertTriangle size={18} /> ⚠️ Outliers
            </button>
            <button className={`nav-tab ${activeTab === 'report' ? 'active' : ''}`} onClick={() => setActiveTab('report')}>
              <Download size={18} /> 📄 EDA Report
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="clean-content" style={{ flex: 1, minWidth: 0 }}>
          {loading ? (
             <div className="center-empty">
               <div className="spinner"></div>
               <p>Generating visualizations...</p>
             </div>
          ) : (
            <AnimatePresence mode="wait">
              {activeTab === 'numerical' && (
                <motion.div key="numerical" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                  <h2>📉 Numerical Distributions</h2>
                  {numData && numData.numeric_columns?.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginTop: '1rem' }}>
                      {numData.numeric_columns.map((col: string) => {
                        const chartObj = numData.charts[col];
                        if (!chartObj || !chartObj.histogram) return null;
                        return (
                          <div key={col} style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '12px' }}>
                            <h3 style={{ marginBottom: '1rem', color: '#a78bfa' }}>{col}</h3>
                            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                               <div style={{ flex: '1 1 400px' }}>
                                  <Plot 
                                    data={chartObj.histogram.data} 
                                    layout={{...chartObj.histogram.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '350px' }}
                                  />
                               </div>
                               <div style={{ flex: '1 1 400px' }}>
                                  <Plot 
                                    data={chartObj.boxplot.data} 
                                    layout={{...chartObj.boxplot.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                                    useResizeHandler={true}
                                    style={{ width: '100%', height: '350px' }}
                                  />
                               </div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                              {Object.entries(chartObj.stats || {}).map(([k, v]) => (
                                <div key={k} style={{ background: 'rgba(255,255,255,0.05)', padding: '0.5rem', borderRadius: '8px', textAlign: 'center' }}>
                                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'capitalize' }}>{k}</div>
                                  <div style={{ fontWeight: 'bold' }}>{typeof v === 'number' ? v.toFixed(2) : v as string}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p>No numeric columns found in this dataset.</p>
                  )}
                </motion.div>
              )}

              {activeTab === 'categorical' && (
                <motion.div key="categorical" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                  <h2>📊 Categorical Analysis</h2>
                  {catData && catData.categorical_columns?.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginTop: '1rem' }}>
                      {catData.categorical_columns.map((col: string) => {
                        const analysis = catData.analysis[col];
                        if (!analysis || !analysis.bar_chart) return null;
                        return (
                          <div key={col} style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '12px' }}>
                            <h3 style={{ marginBottom: '1rem', color: '#34d399' }}>{col} (Unique: {analysis.unique_count})</h3>
                            <Plot 
                              data={analysis.bar_chart.data} 
                              layout={{...analysis.bar_chart.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                              useResizeHandler={true}
                              style={{ width: '100%', height: '400px' }}
                            />
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p>No categorical columns found in this dataset.</p>
                  )}
                </motion.div>
              )}

              {activeTab === 'correlation' && (
                <motion.div key="correlation" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                  <h2>🌡️ Correlation Matrix</h2>
                  <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Pearson correlation across numeric features.</p>
                  {corrData && corrData.heatmap ? (
                    <div style={{ overflowX: 'auto' }}>
                      <Plot 
                        data={corrData.heatmap.data} 
                        layout={{...corrData.heatmap.layout, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: {color: '#fff'}, autosize: true}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '600px', minWidth: '600px' }}
                      />
                    </div>
                  ) : (
                    <p>{corrData?.error || "Insufficient numeric data for correlation."}</p>
                  )}
                </motion.div>
              )}

              {activeTab === 'outliers' && (
                <motion.div key="outliers" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                  <h2>⚠️ Outlier Detection</h2>
                  <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Tukey IQR fence method across numeric features.</p>
                  {outlierData && outlierData.summary ? (
                    <div style={{ overflowX: 'auto' }}>
                       <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                          <thead>
                            <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                               <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Column</th>
                               <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Outliers</th>
                               <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Outliers %</th>
                               <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Lower Fence</th>
                               <th style={{ padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Upper Fence</th>
                            </tr>
                          </thead>
                          <tbody>
                             {outlierData.summary.map((row: any) => (
                               <tr key={row.col} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                 <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{row.col}</td>
                                 <td style={{ padding: '0.75rem', color: row.outlier_count > 0 ? '#f87171' : '#34d399' }}>{row.outlier_count}</td>
                                 <td style={{ padding: '0.75rem' }}>{row.outlier_pct}%</td>
                                 <td style={{ padding: '0.75rem' }}>{row.lower.toFixed(2)}</td>
                                 <td style={{ padding: '0.75rem' }}>{row.upper.toFixed(2)}</td>
                               </tr>
                             ))}
                          </tbody>
                       </table>
                    </div>
                  ) : (
                    <p>Insufficient numeric data for outliers.</p>
                  )}
                </motion.div>
              )}

              {activeTab === 'report' && (
                <motion.div key="report" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                  <h2>📄 Automated EDA Report</h2>
                  <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Generate a comprehensive HTML analysis report via pandas-profiling.</p>
                  
                  {!reportData ? (
                    <button className="primary" onClick={handleGenerateReport} disabled={reportLoading}>
                       {reportLoading ? "Generating Report..." : "Generate EDA Report"}
                    </button>
                  ) : (
                    <div className="kpi-card" style={{ display: 'inline-block', padding: '2rem', border: '1px solid #34d399', background: 'rgba(52, 211, 153, 0.1)' }}>
                      <h3 style={{ color: '#34d399' }}>Report Generated</h3>
                      <p style={{ marginTop: '0.5rem' }}>Saved to: <code>{reportData.report_file}</code></p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default EDAPage;
