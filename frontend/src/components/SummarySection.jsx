import React, { useState, useEffect } from 'react';
import {
  summarizeFile,
  getTranscription,
  extractTimestamps,
  processPDF,
  transcribeFile,
} from '../services/api';
import MediaPlayer from './MediaPlayer';
import './SummarySection.css';

const SummarySection = ({ selectedFileId, selectedFile }) => {
  const [summary, setSummary] = useState(null);
  const [transcription, setTranscription] = useState(null);
  const [timestamps, setTimestamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [localJumpToTimestamp, setLocalJumpToTimestamp] = useState(null);

  useEffect(() => {
    if (selectedFileId) {
      loadSummary();
      // Only load transcription for audio/video files
      if (selectedFile?.file_type === 'audio' || selectedFile?.file_type === 'video') {
        loadTranscription();
      } else {
        setTranscription(null);
      }
    } else {
      setSummary(null);
      setTranscription(null);
      setTimestamps([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFileId, selectedFile]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const response = await summarizeFile(selectedFileId);
      setSummary(response.data);
    } catch (err) {
      console.error('Error loading summary:', err);
      const errorMessage = err.response?.data?.detail || err.message;
      
      // If file needs processing, try to process/transcribe it first
      if (err.response?.status === 400 && errorMessage?.includes('process the file first')) {
        if (selectedFile?.file_type === 'pdf') {
          try {
            // Automatically process the PDF
            await processPDF(selectedFileId);
            // Retry summarization after processing
            const response = await summarizeFile(selectedFileId);
            setSummary(response.data);
            return;
          } catch (processErr) {
            console.error('Error processing PDF:', processErr);
            alert('Please process the PDF first. Processing failed: ' + (processErr.response?.data?.detail || processErr.message));
            setSummary(null);
            return;
          }
        } else if (selectedFile?.file_type === 'audio' || selectedFile?.file_type === 'video') {
          try {
            // Show transcription in progress
            setSummary({ summary: 'Transcribing audio file... This may take a few minutes.' });
            
            // Automatically transcribe the audio/video file
            // This can take a long time, especially on first use (model download)
            await transcribeFile(selectedFileId);
            
            // Wait a bit for the transcription to be fully saved
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Reload transcription to verify it's complete
            await loadTranscription();
            
            // Poll for transcription completion if needed
            let attempts = 0;
            let transcriptionComplete = false;
            while (attempts < 10 && !transcriptionComplete) {
              try {
                const transResponse = await getTranscription(selectedFileId);
                if (transResponse.data?.status === 'completed' && transResponse.data?.full_text) {
                  transcriptionComplete = true;
                  setTranscription(transResponse.data);
                  break;
                }
                // Wait before next attempt
                await new Promise(resolve => setTimeout(resolve, 2000));
                attempts++;
              } catch (pollErr) {
                if (pollErr.response?.status === 404) {
                  // Still processing, wait and retry
                  await new Promise(resolve => setTimeout(resolve, 2000));
                  attempts++;
                } else {
                  throw pollErr;
                }
              }
            }
            
            if (!transcriptionComplete) {
              throw new Error('Transcription is taking longer than expected. Please try again in a moment.');
            }
            
            // Retry summarization after transcription
            const response = await summarizeFile(selectedFileId);
            setSummary(response.data);
            return;
          } catch (transcribeErr) {
            console.error('Error transcribing file:', transcribeErr);
            const errorMsg = transcribeErr.response?.data?.detail || transcribeErr.message;
            alert('Transcription failed: ' + errorMsg + '\n\nNote: First-time transcription may take several minutes to download the Whisper model.');
            setSummary(null);
            return;
          }
        }
      }
      
      // Show error for other cases
      if (err.response?.status !== 400) {
        alert('Error loading summary: ' + errorMessage);
      }
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const loadTranscription = async () => {
    // Only load transcription for audio/video files
    if (selectedFile?.file_type !== 'audio' && selectedFile?.file_type !== 'video') {
      setTranscription(null);
      return;
    }
    
    try {
      const response = await getTranscription(selectedFileId);
      setTranscription(response.data);
    } catch (err) {
      // Transcription might not exist - silently handle 404
      if (err.response?.status !== 404) {
        console.error('Error loading transcription:', err);
      }
      setTranscription(null);
    }
  };

  const handlePlayTimestamp = async (startTime) => {
    try {
      setLocalJumpToTimestamp(startTime);
      // Reset after a moment to allow re-triggering
      setTimeout(() => setLocalJumpToTimestamp(null), 100);
    } catch (error) {
      console.error('Error getting playback info:', error);
    }
  };

  // This useEffect is for external jumpToTimestamp prop (if needed in future)
  // Currently using localJumpToTimestamp state instead

  const handleExtractTimestamps = async (text) => {
    if (!text.trim()) return;
    try {
      const response = await extractTimestamps(selectedFileId, text);
      setTimestamps(response.data.timestamps || []);
      setActiveTab('timestamps');
    } catch (error) {
      console.error('Error extracting timestamps:', error);
      alert('Error extracting timestamps: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (!selectedFileId) {
    return (
      <div className="summary-section">
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <p>Select a file to see summaries and timestamps</p>
        </div>
      </div>
    );
  }

  return (
    <div className="summary-section">
      {(selectedFile?.file_type === 'audio' || selectedFile?.file_type === 'video') && (
        <MediaPlayer
          fileId={selectedFileId}
          fileType={selectedFile?.file_type}
          fileName={selectedFile?.original_filename}
          onTimestampJump={localJumpToTimestamp}
        />
      )}
      <div className="summary-header">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          {(selectedFile?.file_type === 'audio' || selectedFile?.file_type === 'video') && (
            <>
              <button
                className={`tab ${activeTab === 'transcription' ? 'active' : ''}`}
                onClick={() => setActiveTab('transcription')}
              >
                Transcription
              </button>
              <button
                className={`tab ${activeTab === 'timestamps' ? 'active' : ''}`}
                onClick={() => setActiveTab('timestamps')}
              >
                Timestamps
              </button>
            </>
          )}
        </div>
        {activeTab === 'summary' && (
          <button className="refresh-button" onClick={loadSummary} disabled={loading}>
            {loading ? 'Loading...' : '🔄'}
          </button>
        )}
      </div>

      <div className="summary-content">
        {activeTab === 'summary' && (
          <div className="summary-tab">
            {loading ? (
              <div className="loading">Generating summary...</div>
            ) : summary ? (
              <div className="summary-text">
                <div className="summary-meta">
                  <span>Model: {summary.model}</span>
                  <span>{summary.summary_length} chars</span>
                </div>
                <div className="summary-body">{summary.summary}</div>
              </div>
            ) : (
              <div className="empty-state">
                <p>No summary available. Process the file first.</p>
                <button onClick={loadSummary} className="generate-button">
                  Generate Summary
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'transcription' && (
          <div className="transcription-tab">
            {transcription ? (
              <div className="transcription-content">
                <div className="transcription-meta">
                  <span>Language: {transcription.language || 'Unknown'}</span>
                  {transcription.duration && (
                    <span>Duration: {Math.round(transcription.duration)}s</span>
                  )}
                </div>
                <div className="transcription-text">{transcription.full_text}</div>
                {transcription.segments && transcription.segments.length > 0 && (
                  <div className="transcription-segments">
                    <h4>Segments:</h4>
                    {transcription.segments.slice(0, 10).map((segment, idx) => (
                      <div key={idx} className="segment">
                        <span className="segment-time">
                          {segment.start?.toFixed(1)}s - {segment.end?.toFixed(1)}s
                        </span>
                        <span className="segment-text">{segment.text}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <p>No transcription available. Transcribe the file first.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'timestamps' && (
          <div className="timestamps-tab">
            <div className="timestamp-search">
              <input
                type="text"
                placeholder="Enter text to find timestamps..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleExtractTimestamps(e.target.value);
                  }
                }}
                className="timestamp-input"
              />
              <button
                onClick={(e) => {
                  const input = e.target.previousElementSibling;
                  handleExtractTimestamps(input.value);
                }}
                className="search-button"
              >
                Search
              </button>
            </div>
            {timestamps.length > 0 ? (
              <div className="timestamps-list">
                {timestamps.map((ts, idx) => (
                  <div key={idx} className="timestamp-item">
                    <div className="timestamp-header">
                      <span className="timestamp-time">
                        {ts.formatted_start} - {ts.formatted_end}
                      </span>
                      <button
                        className="play-button"
                        onClick={() => handlePlayTimestamp(ts.start)}
                        title="Play from this timestamp"
                      >
                        ▶️
                      </button>
                    </div>
                    <div className="timestamp-text">{ts.text}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>Search for text to find timestamps</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SummarySection;

