import React from 'react';
import { X, ExternalLink, Calendar, User, Cloud } from 'lucide-react';

export default function ImageModal({ image, onClose }) {
  if (!image) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content image-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} title="Close">
          <X size={18} />
        </button>

        <img
          src={image.file_url}
          alt={image.title || image.original_name}
          className="image-modal-img"
        />

        <div style={{ marginTop: '16px', textAlign: 'left', padding: '0 8px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '6px' }}>
            {image.title || image.original_name}
          </h3>

          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '16px',
            fontSize: '0.85rem',
            color: '#cbd5e1',
            marginBottom: '14px'
          }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <User size={14} /> {image.uploader_name || 'Anonymous'}
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={14} /> {new Date(image.created_at).toLocaleString()}
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Cloud size={14} /> {image.s3_key ? `AWS S3: ${image.s3_key}` : 'Local Server Storage'}
            </span>
          </div>

          <a
            href={image.file_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: '#818cf8',
              fontSize: '0.9rem',
              textDecoration: 'none',
              fontWeight: 600
            }}
          >
            <span>Open Original Image URL</span>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>
    </div>
  );
}
