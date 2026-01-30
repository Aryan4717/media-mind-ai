import React, { useRef, useEffect, useState } from 'react';
import { getPlaybackInfo } from '../services/api';
import './MediaPlayer.css';

const MediaPlayer = ({ fileId, fileType, fileName, onTimestampJump }) => {
  const mediaRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [mediaUrl, setMediaUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (fileId && (fileType === 'audio' || fileType === 'video')) {
      loadMediaUrl();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId, fileType]);

  useEffect(() => {
    if (onTimestampJump !== undefined && onTimestampJump !== null) {
      jumpToTimestamp(onTimestampJump);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onTimestampJump]);

  const loadMediaUrl = async () => {
    try {
      setLoading(true);
      const response = await getPlaybackInfo(fileId);
      // Construct full URL
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      const fullUrl = response.data.file_url.startsWith('http')
        ? response.data.file_url
        : `${baseUrl}${response.data.file_url}`;
      setMediaUrl(fullUrl);
    } catch (error) {
      console.error('Error loading media URL:', error);
    } finally {
      setLoading(false);
    }
  };

  const jumpToTimestamp = (timestamp) => {
    if (mediaRef.current && timestamp !== null && timestamp !== undefined) {
      mediaRef.current.currentTime = timestamp;
      if (!isPlaying) {
        mediaRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const handlePlayPause = () => {
    if (mediaRef.current) {
      if (isPlaying) {
        mediaRef.current.pause();
      } else {
        mediaRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (mediaRef.current) {
      setDuration(mediaRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    if (mediaRef.current) {
      const rect = e.currentTarget.getBoundingClientRect();
      const percent = (e.clientX - rect.left) / rect.width;
      const newTime = percent * duration;
      mediaRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (mediaRef.current) {
      mediaRef.current.volume = newVolume;
    }
  };

  const handleMute = () => {
    if (mediaRef.current) {
      mediaRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate);
    if (mediaRef.current) {
      mediaRef.current.playbackRate = rate;
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!fileId || (fileType !== 'audio' && fileType !== 'video')) {
    return (
      <div className="media-player-placeholder">
        <div className="placeholder-icon">🎵</div>
        <p>Select an audio or video file to play</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="media-player-placeholder">
        <div className="loading-spinner"></div>
        <p>Loading media...</p>
      </div>
    );
  }

  return (
    <div className="media-player">
      <div className="media-player-header">
        <h3>{fileName || 'Media Player'}</h3>
        <div className="media-info">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      {fileType === 'video' && mediaUrl && (
        <div className="video-container">
          <video
            ref={mediaRef}
            src={mediaUrl}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            className="video-element"
            controls={false}
          />
        </div>
      )}

      {fileType === 'audio' && mediaUrl && (
        <div className="audio-container">
          <div className="audio-visualizer">
            <div className="audio-wave">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="wave-bar"
                  style={{
                    animationDelay: `${i * 0.05}s`,
                    height: isPlaying ? `${Math.random() * 60 + 20}%` : '20%',
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="media-controls">
        <div className="controls-row">
          <button
            className="control-button play-pause"
            onClick={handlePlayPause}
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>

          <div className="progress-container" onClick={handleSeek}>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(currentTime / duration) * 100}%` }}
              />
              <div
                className="progress-handle"
                style={{ left: `${(currentTime / duration) * 100}%` }}
              />
            </div>
          </div>

          <div className="time-display">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        <div className="controls-row">
          <div className="volume-controls">
            <button
              className="control-button"
              onClick={handleMute}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? '🔇' : volume > 0.5 ? '🔊' : '🔉'}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="volume-slider"
            />
          </div>

          <div className="playback-rate-controls">
            <span className="rate-label">Speed:</span>
            {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
              <button
                key={rate}
                className={`rate-button ${playbackRate === rate ? 'active' : ''}`}
                onClick={() => handlePlaybackRateChange(rate)}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MediaPlayer;

