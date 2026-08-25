import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DatasetInfo {
  filename: string;
  rows: number;
  columns: number;
  column_names: string[];
  dtypes: Record<string, string>;
  memory_mb: string;
  duplicate_rows: number;
  preview?: any[];
  summary: {
    memory_usage: Record<string, string>;
    numeric_stats: Record<string, any>;
  };
}

interface DataContextType {
  dataset: DatasetInfo | null;
  setDataset: (ds: DatasetInfo | null) => void;
  chatHistory: any[];
  setChatHistory: React.Dispatch<React.SetStateAction<any[]>>;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [chatHistory, setChatHistory] = useState<any[]>([]);

  return (
    <DataContext.Provider value={{ dataset, setDataset, chatHistory, setChatHistory }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) throw new Error('useData must be used within a DataProvider');
  return context;
};
