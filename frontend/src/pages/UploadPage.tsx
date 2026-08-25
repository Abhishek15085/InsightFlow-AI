import React, { useState } from 'react';
import { UploadCloud, CheckCircle } from 'lucide-react';
import { uploadCSV } from '../api';
import { useData } from '../DataContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import './UploadPage.css';

const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { setDataset } = useData();
  const navigate = useNavigate();

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelection = (selectedFile: File) => {
    if (selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
    } else {
      alert("Please upload a .csv file.");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadCSV(file);
      setDataset({
        filename: res.filename,
        rows: res.rows,
        columns: res.columns,
        column_names: res.column_names,
        dtypes: res.dtypes,
        memory_mb: res.memory_mb,
        duplicate_rows: res.duplicate_rows,
        preview: res.preview,
        summary: res.summary
      });
      // Navigate to preview tab after upload
      setTimeout(() => navigate('/preview'), 1000);
    } catch (error) {
      console.error("Upload failed", error);
      alert("Upload failed. Make sure backend is running.");
      setUploading(false);
    }
  };

  return (
    <motion.div 
      className="page-container upload-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="hero-section">
        <h1>Welcome to InsightFlow AI</h1>
        <p>The premium, AI-powered workbench for automated data exploration and cleaning.</p>
      </div>

      <div 
        className={`upload-zone glass-panel ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input 
          type="file" 
          id="file-upload" 
          accept=".csv" 
          onChange={(e) => e.target.files && handleFileSelection(e.target.files[0])}
          style={{ display: 'none' }} 
        />
        
        {uploading ? (
          <div className="upload-state uploading">
            <div className="spinner"></div>
            <h3>Uploading dataset...</h3>
            <p>Running initial analysis & schema detection.</p>
          </div>
        ) : file ? (
          <div className="upload-state success">
            <CheckCircle size={48} className="success-icon" />
            <h3>{file.name}</h3>
            <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            <div className="btn-group">
              <button className="secondary" onClick={() => setFile(null)}>Remove</button>
              <button className="primary" onClick={handleUpload}>Process Dataset</button>
            </div>
          </div>
        ) : (
          <label htmlFor="file-upload" className="upload-state empty">
            <UploadCloud size={64} className="upload-icon" />
            <h3>Drag & drop a CSV file here</h3>
            <p>or click to browse from your computer</p>
          </label>
        )}
      </div>
    </motion.div>
  );
};

export default UploadPage;
