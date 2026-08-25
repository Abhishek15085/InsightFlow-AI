import React, { useState } from 'react';
import { useData } from '../DataContext';
import { imputeMissing, encodeCategorical, scaleNumeric, featureSelection, dropDuplicates, runFullPipeline } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Wand2, Eraser, Scissors, Repeat, Box, BarChart, Rocket } from 'lucide-react';

type Tab = 'missing' | 'encoding' | 'scaling' | 'features' | 'duplicates' | 'pipeline';

const CleanPage: React.FC = () => {
  const { dataset, setDataset } = useData();
  const [activeTab, setActiveTab] = useState<Tab>('missing');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // States for forms
  const [missingStrategy, setMissingStrategy] = useState('mean');
  const [encodeMethod, setEncodeMethod] = useState('label');
  const [scaleMethod, setScaleMethod] = useState('standard');
  const [dropConstant, setDropConstant] = useState(true);
  const [dropHighMissing, setDropHighMissing] = useState(50);
  const [dropDuplicateCols, setDropDuplicateCols] = useState(true);

  if (!dataset) {
    return (
      <div className="page-container center-empty">
        <AlertCircle size={48} className="empty-icon warning" />
        <h2>No Dataset Uploaded</h2>
      </div>
    );
  }

  const updateDatasetContext = (cleanedFilename: string, newRows: number, newCols: number) => {
    // In a real app we'd fetch the full fresh stats, but for now we just update filename/shape.
    setDataset({
      ...dataset,
      filename: cleanedFilename,
      rows: newRows,
      columns: newCols,
    });
  };

  const handleAction = async (actionFn: () => Promise<any>, successMsg: (res: any) => string) => {
    setLoading(true);
    setMessage('');
    try {
      const res = await actionFn();
      setMessage(successMsg(res));
      if (res.cleaned_filename) {
        updateDatasetContext(res.cleaned_filename, res.cleaned_shape?.rows ?? dataset.rows, res.cleaned_shape?.columns ?? dataset.columns);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div className="page-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <h1>Data Cleaning Studio</h1>
        <p>Apply transformations and fix data quality issues instantly.</p>
      </div>

      <div className="clean-layout" style={{ display: 'flex', gap: '2rem' }}>
        {/* Sub-navigation Sidebar */}
        <div className="clean-sidebar" style={{ minWidth: '220px' }}>
          <div className="glass-panel" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button className={`nav-tab ${activeTab === 'missing' ? 'active' : ''}`} onClick={() => setActiveTab('missing')}>
              <Eraser size={18} /> Missing Values
            </button>
            <button className={`nav-tab ${activeTab === 'encoding' ? 'active' : ''}`} onClick={() => setActiveTab('encoding')}>
              <Box size={18} /> Encoding
            </button>
            <button className={`nav-tab ${activeTab === 'scaling' ? 'active' : ''}`} onClick={() => setActiveTab('scaling')}>
              <BarChart size={18} /> Scaling
            </button>
            <button className={`nav-tab ${activeTab === 'features' ? 'active' : ''}`} onClick={() => setActiveTab('features')}>
              <Scissors size={18} /> Feature Selection
            </button>
            <button className={`nav-tab ${activeTab === 'duplicates' ? 'active' : ''}`} onClick={() => setActiveTab('duplicates')}>
              <Repeat size={18} /> Duplicates
            </button>
            <button className={`nav-tab ${activeTab === 'pipeline' ? 'active' : ''}`} onClick={() => setActiveTab('pipeline')}>
              <Rocket size={18} /> Full Pipeline
            </button>
          </div>

          {message && (
            <div className="glass-panel" style={{ marginTop: '1rem', padding: '1rem', borderLeft: '4px solid #34d399' }}>
              <p style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>{message}</p>
            </div>
          )}
        </div>

        {/* Action Panel */}
        <div className="clean-content" style={{ flex: 1 }}>
          <AnimatePresence mode="wait">
            {activeTab === 'missing' && (
              <motion.div key="missing" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>🕳️ Handle Missing Values</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Fill or drop missing values across the dataset.</p>
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label>Strategy</label>
                  <select value={missingStrategy} onChange={(e) => setMissingStrategy(e.target.value)} style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '8px' }}>
                    <option value="mean">Mean (Numeric only)</option>
                    <option value="median">Median (Numeric only)</option>
                    <option value="mode">Mode (All columns)</option>
                    <option value="drop">Drop Rows</option>
                  </select>
                </div>
                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => imputeMissing(dataset.filename, missingStrategy, null),
                  (res) => `Success! Applied ${res.strategy} strategy.`
                )}>
                  <Wand2 size={18} /> {loading ? 'Processing...' : 'Apply Missing Values Fix'}
                </button>
              </motion.div>
            )}

            {activeTab === 'encoding' && (
              <motion.div key="encoding" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>🔢 Encode Categorical Data</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Convert text categories into machine-readable numeric formats.</p>
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label>Encoding Method</label>
                  <select value={encodeMethod} onChange={(e) => setEncodeMethod(e.target.value)} style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '8px' }}>
                    <option value="label">Label Encoding</option>
                    <option value="onehot">One-Hot Encoding</option>
                  </select>
                </div>
                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => encodeCategorical(dataset.filename, encodeMethod, null),
                  (res) => `Success! Encoded categorical columns using ${res.method}.`
                )}>
                  <Wand2 size={18} /> {loading ? 'Processing...' : 'Apply Encoding'}
                </button>
              </motion.div>
            )}

            {activeTab === 'scaling' && (
              <motion.div key="scaling" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>⚖️ Scale Numeric Features</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Normalize or standardize numerical values.</p>
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label>Scaling Method</label>
                  <select value={scaleMethod} onChange={(e) => setScaleMethod(e.target.value)} style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '8px' }}>
                    <option value="standard">Standard Scaler (Z-Score)</option>
                    <option value="minmax">MinMax Scaler (0 to 1)</option>
                  </select>
                </div>
                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => scaleNumeric(dataset.filename, scaleMethod, null),
                  (res) => `Success! Scaled numeric columns using ${res.method}.`
                )}>
                  <Wand2 size={18} /> {loading ? 'Processing...' : 'Apply Scaling'}
                </button>
              </motion.div>
            )}

            {activeTab === 'features' && (
              <motion.div key="features" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>✂️ Feature Selection</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Automatically drop useless or redunant columns.</p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input type="checkbox" checked={dropConstant} onChange={(e) => setDropConstant(e.target.checked)} />
                    Drop Constant Columns
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input type="checkbox" checked={dropDuplicateCols} onChange={(e) => setDropDuplicateCols(e.target.checked)} />
                    Drop Duplicate Columns
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <span>Drop columns with missing % &gt;= {dropHighMissing}%</span>
                    <input type="range" min="0" max="100" value={dropHighMissing} onChange={(e) => setDropHighMissing(Number(e.target.value))} />
                  </label>
                </div>

                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => featureSelection(dataset.filename, dropConstant, dropHighMissing, dropDuplicateCols),
                  (res) => `Success! Removed ${res.columns_removed} columns.`
                )}>
                  <Wand2 size={18} /> {loading ? 'Processing...' : 'Apply Feature Selection'}
                </button>
              </motion.div>
            )}

            {activeTab === 'duplicates' && (
              <motion.div key="duplicates" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>🔁 Remove Duplicate Rows</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Delete exact row copies from the dataset.</p>
                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => dropDuplicates(dataset.filename, 'first'),
                  (res) => `Success! Removed ${res.duplicates_removed} duplicate rows.`
                )}>
                  <Wand2 size={18} /> {loading ? 'Processing...' : 'Drop Duplicates'}
                </button>
              </motion.div>
            )}

            {activeTab === 'pipeline' && (
              <motion.div key="pipeline" className="full-width-card glass-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2>🚀 Full Cleaning Pipeline</h2>
                <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Run all cleaning steps in one shot with default strategies.</p>
                <button className="primary" disabled={loading} onClick={() => handleAction(
                  () => runFullPipeline(dataset.filename, {}),
                  (res) => `Success! Pipeline executed. Data shape changed from ${dataset.rows}x${dataset.columns} to ${res.cleaned_shape?.rows}x${res.cleaned_shape?.columns}.`
                )}>
                  <Rocket size={18} /> {loading ? 'Processing...' : 'Execute Full Pipeline'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default CleanPage;
