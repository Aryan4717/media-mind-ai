import React, { useState, useEffect } from 'react';
import {
  summarizeFile,
  getTranscription,
  getPlaybackInfo,
  extractTimestamps,
} from '../services/api';
import './SummarySection.css';

const SummarySection = ({ selectedFileId, selectedFile }) => {
  const [summary, setSummary] = useState(null);
  const [transcription, setTranscription] = useState(null);
  const [timestamps, setTimestamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    if (selectedFileId) {
      loadSummary();
      loadTranscription();
    } else {
      setSummary(null);
      setTranscription(null);
      setTimestamps([]);
    }
  }, [selectedFileId]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const response = await summarizeFile(selectedFileId);
      setSummary(response.data);
    } catch (error) {
      console.error('Error loading summary:', error);
      if (error.response?.status !== 400) {
        // Don't show error if file just needs processing
        setSummary(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTranscription = async () => {
    try {
      const response = await getTranscription(selectedFileId);
      setTranscription(response.data);
    } catch (error) {
      // Transcription might not exist
      setTranscription(null);
    }
  };

  const handlePlayTimestamp = async (startTime) => {
    try {
      const response = await getPlaybackInfo(selectedFileId, startTime);
      // In a real app, you'd use this to control a media player
      console.log('Playback info:', response.data);
      alert(`Playback URL: ${response.data.file_url}\nStart time: ${response.data.formatted_timestamp}`);
    } catch (error) {
      console.error('Error getting playback info:', error);
    }
  };

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

