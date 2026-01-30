import React, { useState, useRef, useCallback } from 'react';
import { getFiles, deleteFile } from '../services/api';
import './Sidebar.css';

const Sidebar = ({ onFileSelect, selectedFileId }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [isDragging, setIsDragging] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [dragCounter, setDragCounter] = useState(0);
  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

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

  const validateFile = (file) => {
    const allowedTypes = [
      'application/pdf',
      'audio/mpeg',
      'audio/mp3',
      'audio/wav',
      'audio/x-wav',
      'video/mp4',
      'video/avi',
      'video/quicktime',
      'video/x-msvideo',
    ];
    const allowedExtensions = ['.pdf', '.mp3', '.mp4', '.wav', '.avi', '.mov'];
    const fileName = file.name.toLowerCase();
    
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    const hasValidType = allowedTypes.includes(file.type) || file.type === '';
    
    return hasValidExtension || hasValidType;
  };

  const uploadFileWithProgress = async (file, fileId) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    
    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        setUploadProgress((prev) => ({
          ...prev,
          [fileId]: {
            loaded: e.loaded,
            total: e.total,
            percent: percentComplete,
          },
        }));
      }
    });

    return new Promise((resolve, reject) => {
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      };

      xhr.onerror = () => reject(new Error('Upload failed'));
      
      xhr.open('POST', `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/files/upload`);
      xhr.send(formData);
    });
  };

  const handleFiles = async (fileList) => {
    const filesArray = Array.from(fileList);
    const validFiles = filesArray.filter(validateFile);
    
    if (validFiles.length === 0) {
      alert('No valid files selected. Supported formats: PDF, MP3, MP4, WAV, AVI, MOV');
      return;
    }

    if (validFiles.length < filesArray.length) {
      alert(`${filesArray.length - validFiles.length} file(s) were skipped due to invalid format.`);
    }

    setUploading(true);
    const uploadPromises = [];

    for (const file of validFiles) {
      const fileId = `${Date.now()}-${Math.random()}`;
      
      // Initialize progress
      setUploadProgress((prev) => ({
        ...prev,
        [fileId]: {
          loaded: 0,
          total: file.size,
          percent: 0,
          fileName: file.name,
        },
      }));

      uploadPromises.push(
        uploadFileWithProgress(file, fileId)
          .then(async (response) => {
            await loadFiles();
            if (onFileSelect && uploadPromises.length === 1) {
              onFileSelect(response.id);
            }
            // Remove progress after a delay
            setTimeout(() => {
              setUploadProgress((prev) => {
                const newProgress = { ...prev };
                delete newProgress[fileId];
                return newProgress;
              });
            }, 1000);
            return response;
          })
          .catch((error) => {
            console.error(`Error uploading ${file.name}:`, error);
            alert(`Error uploading ${file.name}: ${error.message}`);
            // Remove progress on error
            setUploadProgress((prev) => {
              const newProgress = { ...prev };
              delete newProgress[fileId];
              return newProgress;
            });
          })
      );
    }

    try {
      await Promise.all(uploadPromises);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileUpload = async (event) => {
    const fileList = event.target.files;
    if (fileList.length > 0) {
      await handleFiles(fileList);
    }
  };

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((prev) => prev + 1);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((prev) => {
      const newCounter = prev - 1;
      if (newCounter === 0) {
        setIsDragging(false);
      }
      return newCounter;
    });
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    async (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      setDragCounter(0);

      const fileList = e.dataTransfer.files;
      if (fileList.length > 0) {
        await handleFiles(fileList);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
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
          multiple
        />
      </div>

      <div
        ref={dropZoneRef}
        className={`drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div className="drop-zone-overlay">
            <div className="drop-zone-content">
              <div className="drop-icon">📤</div>
              <div className="drop-text">Drop files here to upload</div>
              <div className="drop-hint">PDF, Audio, or Video files</div>
            </div>
          </div>
        )}

        {Object.keys(uploadProgress).length > 0 && (
          <div className="upload-progress-list">
            {Object.entries(uploadProgress).map(([fileId, progress]) => (
              <div key={fileId} className="upload-progress-item">
                <div className="progress-header">
                  <span className="progress-filename">{progress.fileName}</span>
                  <span className="progress-percent">{Math.round(progress.percent)}%</span>
                </div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar"
                    style={{ width: `${progress.percent}%` }}
                  />
                </div>
                <div className="progress-size">
                  {formatFileSize(progress.loaded)} / {formatFileSize(progress.total)}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="files-list">
          {loading ? (
            <div className="loading">Loading files...</div>
          ) : files.length === 0 && Object.keys(uploadProgress).length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <p>No files uploaded yet</p>
              <p className="empty-hint">Drag and drop files here or click Upload</p>
            </div>
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
    </div>
  );
};

export default Sidebar;
