import React, { useState, useRef } from 'react';
import { uploadFile, getFiles, deleteFile } from '../services/api';
import './Sidebar.css';

const Sidebar = ({ onFileSelect, selectedFileId }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const response = await getFiles();
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      const response = await uploadFile(file);
      await loadFiles();
      if (onFileSelect) {
        onFileSelect(response.data.id);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteFile = async (fileId, event) => {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      await deleteFile(fileId);
      await loadFiles();
      if (selectedFileId === fileId) {
        onFileSelect(null);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('Error deleting file: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getFileIcon = (fileType) => {
    switch (fileType?.toLowerCase()) {
      case 'pdf':
        return '📄';
      case 'audio':
        return '🎵';
      case 'video':
        return '🎬';
      case 'image':
        return '🖼️';
      default:
        return '📎';
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Files</h2>
        <button
          className="upload-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : '+ Upload'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          onChange={handleFileUpload}
          accept=".pdf,.mp3,.mp4,.wav,.avi,.mov"
        />
      </div>

      <div className="files-list">
        {loading ? (
          <div className="loading">Loading files...</div>
        ) : files.length === 0 ? (
          <div className="empty-state">No files uploaded yet</div>
        ) : (
          files.map((file) => (
            <div
              key={file.id}
              className={`file-item ${selectedFileId === file.id ? 'selected' : ''}`}
              onClick={() => onFileSelect(file.id)}
            >
              <div className="file-icon">{getFileIcon(file.file_type)}</div>
              <div className="file-info">
                <div className="file-name" title={file.original_filename}>
                  {file.original_filename}
                </div>
                <div className="file-meta">
                  {file.file_size_mb.toFixed(2)} MB • {file.file_type}
                </div>
              </div>
              <button
                className="delete-button"
                onClick={(e) => handleDeleteFile(file.id, e)}
                title="Delete file"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Sidebar;

