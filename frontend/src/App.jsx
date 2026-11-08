import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import StatusBanner from './components/StatusBanner';
import ImageUpload from './components/ImageUpload';
import ImageGallery from './components/ImageGallery';
import ImageModal from './components/ImageModal';
import AdminLoginModal from './components/AdminLoginModal';
import { Sparkles, RefreshCw } from 'lucide-react';

export default function App() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('cloudlens_token') || '');
  const [adminUser, setAdminUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('cloudlens_user') || 'null');
    } catch (e) {
      return null;
    }
  });
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);

  const isAdmin = !!(token && adminUser && adminUser.role === 'admin');

  // Fetch images from backend
  const fetchImages = async () => {
    try {
      const res = await fetch('/api/images');
      const data = await res.json();
      if (data.success) {
        setImages(data.images || []);
      }
    } catch (err) {
      console.error('Failed to load images:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch backend status / health
  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error('Failed to check health:', err);
    }
  };

  useEffect(() => {
    fetchImages();
    fetchHealth();
  }, []);

  const handleLoginSuccess = (newToken, user) => {
    setToken(newToken);
    setAdminUser(user);
    localStorage.setItem('cloudlens_token', newToken);
    localStorage.setItem('cloudlens_user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setToken('');
    setAdminUser(null);
    localStorage.removeItem('cloudlens_token');
    localStorage.removeItem('cloudlens_user');
  };

  const handleUploadSuccess = (newImage) => {
    setImages((prev) => [newImage, ...prev]);
  };

  const handleDeleteSuccess = (deletedId) => {
    setImages((prev) => prev.filter((img) => img.id !== deletedId));
  };

  return (
    <div>
      <Navbar
        isAdmin={isAdmin}
        adminUser={adminUser}
        onOpenLogin={() => setIsLoginModalOpen(true)}
        onLogout={handleLogout}
      />

      <main className="container">
        {/* Hero Section */}
        <header className="hero">
          <div className="hero-tag">
            <Sparkles size={14} />
            <span>AWS Cloud Ready Gallery</span>
          </div>
          <h1 className="hero-title">
            Store & View Images with <span>AWS S3 & EC2</span>
          </h1>
          <p className="hero-desc">
            Upload and view images seamlessly. Role-based security ensures only administrators can delete photos.
          </p>

          <StatusBanner health={health} />
        </header>

        {/* Upload Form */}
        <ImageUpload onUploadSuccess={handleUploadSuccess} />

        {/* Gallery */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#64748b' }}>
            <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px' }} />
            <p>Loading image gallery...</p>
          </div>
        ) : (
          <ImageGallery
            images={images}
            isAdmin={isAdmin}
            token={token}
            onDeleteSuccess={handleDeleteSuccess}
            onSelectImage={(img) => setSelectedImage(img)}
          />
        )}
      </main>

      {/* Lightbox Modal */}
      <ImageModal
        image={selectedImage}
        onClose={() => setSelectedImage(null)}
      />

      {/* Admin Login Modal */}
      <AdminLoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
}
