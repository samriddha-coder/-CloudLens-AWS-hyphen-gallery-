import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, X, Check, Loader2 } from 'lucide-react';

export default function ImageUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [title, setTitle] = useState('');
  const [uploaderName, setUploaderName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please select a valid image file (JPG, PNG, WEBP, GIF, SVG).');
      return;
    }
    setError('');
    setFile(selectedFile);
    setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
    setPreview(URL.createObjectURL(selectedFile));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const clearSelection = () => {
    setFile(null);
    setPreview(null);
    setTitle('');
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please choose an image to upload.');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('title', title.trim() || file.name);
      formData.append('uploader_name', uploaderName.trim() || 'Anonymous User');

      const res = await fetch('/api/images/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Image upload failed.');
      }

      clearSelection();
      if (onUploadSuccess) {
        onUploadSuccess(data.image);
      }
    } catch (err) {
      setError(err.message || 'Something went wrong during upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-card">
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '14px' }}>
        📤 Upload Image to Cloud Gallery
      </h3>

      {error && (
        <div style={{
          background: '#fee2e2',
          color: '#b91c1c',
          padding: '10px 14px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '0.88rem'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => handleFileChange(e.target.files[0])}
          />
          <UploadCloud className="dropzone-icon" />
          <p style={{ fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
            Click to browse or drag & drop an image here
          </p>
          <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
            Supports PNG, JPG, WEBP, GIF, SVG (Stored directly on AWS S3)
          </p>
        </div>

        {file && (
          <div className="preview-container">
            <img src={preview} alt="Preview" className="preview-thumb" />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {file.name}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </div>
            </div>
            <button
              type="button"
              onClick={clearSelection}
              style={{ padding: '6px', color: '#64748b' }}
              title="Remove selection"
            >
              <X size={18} />
            </button>
          </div>
        )}

        <div className="upload-form-grid">
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
              Image Title
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Sunset in Cox's Bazar"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
              Your Name (Optional)
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Samriddha"
              value={uploaderName}
              onChange={(e) => setUploaderName(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          {file && (
            <button type="button" onClick={clearSelection} className="btn-outline">
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="btn-primary"
            disabled={!file || uploading}
            style={{ opacity: !file || uploading ? 0.6 : 1 }}
          >
            {uploading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Uploading to S3...</span>
              </>
            ) : (
              <>
                <UploadCloud size={16} />
                <span>Upload Image</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
