import React, { useState } from 'react';
import { Eye, Trash2, Calendar, User, Images, AlertCircle, Loader2 } from 'lucide-react';

export default function ImageGallery({ images, isAdmin, token, onDeleteSuccess, onSelectImage }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (image) => {
    if (!isAdmin) {
      alert('Only admin users are allowed to delete images. Please log in as Admin.');
      return;
    }

    const confirm = window.confirm(`Are you sure you want to delete "${image.title || image.original_name}"? This will permanently delete it from AWS S3 and the database.`);
    if (!confirm) return;

    setDeletingId(image.id);

    try {
      const res = await fetch(`/api/images/${image.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Failed to delete image');
      }

      if (onDeleteSuccess) {
        onDeleteSuccess(image.id);
      }
    } catch (err) {
      alert(`Error deleting image: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (e) {
      return isoString;
    }
  };

  return (
    <section>
      <div className="gallery-header">
        <h2 className="gallery-title">
          <Images className="text-indigo-600" size={24} />
          <span>Uploaded Images ({images.length})</span>
        </h2>
      </div>

      <div className="gallery-grid">
        {images.length === 0 ? (
          <div className="empty-state">
            <Images className="empty-icon" />
            <h4 style={{ fontWeight: 700, fontSize: '1.2rem', marginBottom: '6px' }}>No Images Yet</h4>
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Upload your first image above to store it in AWS S3 and database.
            </p>
          </div>
        ) : (
          images.map((img) => (
            <div key={img.id} className="image-card">
              <div
                className="image-thumb-wrapper"
                onClick={() => onSelectImage(img)}
                title="Click to view full image"
              >
                <img
                  src={img.file_url}
                  alt={img.title || img.original_name}
                  className="image-thumb"
                  loading="lazy"
                  onError={(e) => {
                    // Fallback placeholder if image link cannot load
                    e.target.onerror = null;
                    e.target.src = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=60';
                  }}
                />
                <span className="image-badge">
                  {img.s3_key ? 'AWS S3' : 'Local'}
                </span>
              </div>

              <div className="image-details">
                <h4 className="image-title" title={img.title || img.original_name}>
                  {img.title || img.original_name}
                </h4>

                <div className="image-meta">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <User size={13} />
                    <span>Uploaded by: <strong>{img.uploader_name || 'Anonymous'}</strong></span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Calendar size={13} />
                    <span>{formatDate(img.created_at)}</span>
                  </div>
                </div>

                <div className="card-footer">
                  <button
                    onClick={() => onSelectImage(img)}
                    className="btn-outline"
                    style={{ padding: '6px 12px', fontSize: '0.82rem' }}
                  >
                    <Eye size={14} />
                    <span>View</span>
                  </button>

                  {isAdmin ? (
                    <button
                      onClick={() => handleDelete(img)}
                      className="btn-danger"
                      disabled={deletingId === img.id}
                      title="Admin: Delete this image"
                    >
                      {deletingId === img.id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Trash2 size={14} />
                      )}
                      <span>Delete</span>
                    </button>
                  ) : (
                    <span
                      style={{
                        fontSize: '0.78rem',
                        color: '#94a3b8',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                      title="Only Administrator can delete images"
                    >
                      <span>🔒 Admin only</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
