require('dotenv').config();
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const { connectDB, isFallback } = require('./config/db');
const { isS3Configured, uploadsDir } = require('./config/s3');
const imageRoutes = require('./routes/imageRoutes');
const authRoutes = require('./routes/authRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

// Middlewares
app.use(cors({
  origin: '*', // Allow frontend connection
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-admin-key'],
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// Static serving for local uploads fallback
app.use('/uploads', express.static(uploadsDir));

// API Routes
app.use('/api/images', imageRoutes);
app.use('/api/auth', authRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    storage: isS3Configured() ? 'AWS S3' : 'Local Disk (/uploads)',
    database: isFallback() ? 'Fallback (Local JSON)' : 'PostgreSQL',
    timestamp: new Date().toISOString(),
  });
});

// Root welcome route
app.get('/', (req, res) => {
  res.json({
    message: 'Image Gallery API is running',
    docs: {
      images: '/api/images',
      upload: 'POST /api/images/upload',
      delete: 'DELETE /api/images/:id (Admin only)',
      health: '/api/health',
    },
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled Server Error:', err);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Internal Server Error',
  });
});

// Start server after DB initialization
const startServer = async () => {
  await connectDB();
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Backend server is running on http://localhost:${PORT}`);
    console.log(`📦 Storage Mode: ${isS3Configured() ? 'AWS S3 ☁️' : 'Local Disk 📁'}`);
    console.log(`🗄️  Database Mode: ${isFallback() ? 'Local Storage (Docker/Postgres not running)' : 'PostgreSQL 🐘'}`);
  });
};

startServer();
