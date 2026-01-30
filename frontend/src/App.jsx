import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import SummarySection from './components/SummarySection';
import { getFileMetadata } from './services/api';
import './App.css';

function App() {
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = async (fileId) => {
    setSelectedFileId(fileId);
    if (fileId) {
      try {
        const response = await getFileMetadata(fileId);
        setSelectedFile(response.data);
      } catch (error) {
        console.error('Error loading file metadata:', error);
        setSelectedFile(null);
      }
    } else {
      setSelectedFile(null);
    }
  };

  return (
    <div className="app">
      <Sidebar onFileSelect={handleFileSelect} selectedFileId={selectedFileId} />
      <ChatArea selectedFileId={selectedFileId} />
      <SummarySection selectedFileId={selectedFileId} selectedFile={selectedFile} />
    </div>
  );
}

export default App;
