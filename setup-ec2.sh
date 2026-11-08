#!/bin/bash
set -e

echo "🚀 Installing Docker & Docker Compose on EC2..."
sudo apt update -y
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

echo "📁 Creating application directories..."
mkdir -p app/backend/src/config app/backend/src/controllers app/backend/src/middlewares app/backend/src/routes app/backend/uploads app/frontend/src/components
cd app

cat << 'EOF' > docker-compose.yml
version: '3.8'

services:
  # 1. PostgreSQL Database Service
  postgres:
    image: postgres:16-alpine
    container_name: gallery_postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-image_gallery}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-image_gallery}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 2. Node.js Backend Service
  backend:
    build: ./backend
    container_name: gallery_backend
    restart: always
    environment:
      PORT: 5000
      BASE_URL: ${BASE_URL:-http://localhost:5000}
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: ${DB_USER:-postgres}
      DB_PASSWORD: ${DB_PASSWORD:-postgres}
      DB_NAME: ${DB_NAME:-image_gallery}
      JWT_SECRET: ${JWT_SECRET:-super_secret_jwt_key_gallery_2026}
      ADMIN_USERNAME: ${ADMIN_USERNAME:-admin}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin123}
      ADMIN_SECRET_KEY: ${ADMIN_SECRET_KEY:-admin_super_secret_key}
      # AWS S3 Settings (set these when ready)
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:-}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:-}
      AWS_REGION: ${AWS_REGION:-us-east-1}
      AWS_BUCKET_NAME: ${AWS_BUCKET_NAME:-}
    ports:
      - "5000:5000"
    volumes:
      - ./backend/uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy

  # 3. React Frontend Service
  frontend:
    build: ./frontend
    container_name: gallery_frontend
    restart: always
    ports:
      - "80:80"
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
    driver: local

EOF

cat << 'EOF' > backend/package.json
{
  "name": "image-gallery-backend",
  "version": "1.0.0",
  "description": "Image Upload and View Backend with AWS S3, EC2, PostgreSQL & Node.js",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "node --watch src/server.js"
  },
  "dependencies": {
    "@aws-sdk/client-s3": "^3.750.0",
    "bcryptjs": "^3.0.2",
    "cors": "^2.8.5",
    "dotenv": "^16.4.7",
    "express": "^4.21.2",
    "jsonwebtoken": "^9.0.2",
    "morgan": "^1.10.0",
    "multer": "^1.4.5-lts.1",
    "pg": "^8.13.3"
  }
}

EOF

cat << 'EOF' > backend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application source
COPY . .

# Expose backend port
EXPOSE 5000

# Start server
CMD ["node", "src/server.js"]

EOF

cat << 'EOF' > backend/src/server.js
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

EOF

cat << 'EOF' > backend/src/config/db.js
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');

let pool = null;
let useFallback = false;

// Fallback JSON DB path for when PostgreSQL server is not currently reachable
const fallbackDbPath = path.join(__dirname, '..', '..', 'data_fallback.json');

const initFallbackDb = () => {
  if (!fs.existsSync(fallbackDbPath)) {
    const defaultData = {
      images: [],
      users: []
    };
    fs.writeFileSync(fallbackDbPath, JSON.stringify(defaultData, null, 2));
  }
};

const getFallbackData = () => {
  initFallbackDb();
  try {
    return JSON.parse(fs.readFileSync(fallbackDbPath, 'utf8'));
  } catch (e) {
    return { images: [], users: [] };
  }
};

const saveFallbackData = (data) => {
  fs.writeFileSync(fallbackDbPath, JSON.stringify(data, null, 2));
};

const connectDB = async () => {
  const connectionString = process.env.DATABASE_URL || 
    `postgresql://${process.env.DB_USER || 'postgres'}:${process.env.DB_PASSWORD || 'postgres'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'image_gallery'}`;

  pool = new Pool({
    connectionString,
    connectionTimeoutMillis: 3000,
  });

  try {
    const client = await pool.connect();
    console.log('✅ Connected to PostgreSQL database successfully.');
    
    // Create tables if not exist
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS images (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        original_name VARCHAR(255) NOT NULL,
        file_url TEXT NOT NULL,
        s3_key VARCHAR(255),
        uploader_name VARCHAR(100) DEFAULT 'Anonymous',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Ensure default admin user exists
    const adminUser = process.env.ADMIN_USERNAME || 'admin';
    const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
    const res = await client.query('SELECT * FROM users WHERE username = $1', [adminUser]);
    if (res.rows.length === 0) {
      const hashed = await bcrypt.hash(adminPass, 10);
      await client.query('INSERT INTO users (username, password, role) VALUES ($1, $2, $3)', [adminUser, hashed, 'admin']);
      console.log(`🔐 Default admin created: Username "${adminUser}", Password "${adminPass}"`);
    }

    client.release();
    useFallback = false;
  } catch (err) {
    console.warn('⚠️  Could not connect to PostgreSQL (Ensure Docker or PostgreSQL is running).');
    console.warn(`⚠️  Database Error: ${err.message}`);
    console.log('🔄 Switching to local fallback storage (data_fallback.json) for smooth local testing...');
    useFallback = true;
    initFallbackDb();

    // Ensure default admin in fallback
    const data = getFallbackData();
    const adminUser = process.env.ADMIN_USERNAME || 'admin';
    const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
    const exists = data.users.find(u => u.username === adminUser);
    if (!exists) {
      const hashed = await bcrypt.hash(adminPass, 10);
      data.users.push({
        id: 1,
        username: adminUser,
        password: hashed,
        role: 'admin',
        created_at: new Date().toISOString()
      });
      saveFallbackData(data);
      console.log(`🔐 Default admin initialized in fallback: "${adminUser}"`);
    }
  }
};

const query = async (text, params) => {
  if (!useFallback && pool) {
    try {
      return await pool.query(text, params);
    } catch (e) {
      console.error('PostgreSQL query error:', e.message);
      throw e;
    }
  }

  // Fallback handler for queries
  const data = getFallbackData();
  const lower = text.toLowerCase().trim();

  // Handle users query
  if (lower.startsWith('select * from users where username = $1')) {
    const user = data.users.find(u => u.username === params[0]);
    return { rows: user ? [user] : [] };
  }

  // Handle images SELECT
  if (lower.startsWith('select * from images order by created_at desc')) {
    const sorted = [...data.images].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    return { rows: sorted };
  }

  // Handle images INSERT
  if (lower.startsWith('insert into images')) {
    const newImage = {
      id: Date.now(),
      title: params[0],
      original_name: params[1],
      file_url: params[2],
      s3_key: params[3],
      uploader_name: params[4],
      created_at: new Date().toISOString()
    };
    data.images.unshift(newImage);
    saveFallbackData(data);
    return { rows: [newImage] };
  }

  // Handle images SELECT by id
  if (lower.startsWith('select * from images where id = $1')) {
    const img = data.images.find(i => String(i.id) === String(params[0]));
    return { rows: img ? [img] : [] };
  }

  // Handle images DELETE
  if (lower.startsWith('delete from images where id = $1')) {
    const idx = data.images.findIndex(i => String(i.id) === String(params[0]));
    if (idx !== -1) {
      const deleted = data.images.splice(idx, 1);
      saveFallbackData(data);
      return { rowCount: 1, rows: deleted };
    }
    return { rowCount: 0, rows: [] };
  }

  return { rows: [] };
};

module.exports = {
  connectDB,
  query,
  isFallback: () => useFallback
};

EOF

cat << 'EOF' > backend/src/config/s3.js
const { S3Client, PutObjectCommand, DeleteObjectCommand } = require('@aws-sdk/client-s3');
const fs = require('fs');
const path = require('path');

const isS3Configured = () => {
  return !!(
    process.env.AWS_ACCESS_KEY_ID &&
    process.env.AWS_SECRET_ACCESS_KEY &&
    process.env.AWS_BUCKET_NAME &&
    process.env.AWS_REGION
  );
};

let s3Client = null;

if (isS3Configured()) {
  s3Client = new S3Client({
    region: process.env.AWS_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },
  });
  console.log(`☁️  AWS S3 Client initialized. Target Bucket: ${process.env.AWS_BUCKET_NAME} (${process.env.AWS_REGION})`);
} else {
  console.log('📁 AWS S3 credentials not set. Uploads will be stored locally in /uploads directory.');
}

// Local uploads directory fallback
const uploadsDir = path.join(__dirname, '..', '..', 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

/**
 * Upload a file to S3 or local storage
 * @param {Object} file - Multer file object
 * @returns {Promise<{file_url: string, s3_key: string|null}>}
 */
const uploadFile = async (file) => {
  const timestamp = Date.now();
  const sanitizedName = file.originalname.replace(/[^a-zA-Z0-9.-]/g, '_');
  const filename = `${timestamp}-${sanitizedName}`;

  if (isS3Configured() && s3Client) {
    const s3Key = `images/${filename}`;
    const command = new PutObjectCommand({
      Bucket: process.env.AWS_BUCKET_NAME,
      Key: s3Key,
      Body: file.buffer,
      ContentType: file.mimetype,
    });

    await s3Client.send(command);
    
    // Construct S3 public URL
    const file_url = `https://${process.env.AWS_BUCKET_NAME}.s3.${process.env.AWS_REGION}.amazonaws.com/${s3Key}`;
    return { file_url, s3_key: s3Key };
  }

  // Local fallback: write buffer to uploads folder
  const filePath = path.join(uploadsDir, filename);
  fs.writeFileSync(filePath, file.buffer);
  
  // Return relative or full URL for local serving
  const baseUrl = process.env.BASE_URL || `http://localhost:${process.env.PORT || 5000}`;
  const file_url = `${baseUrl}/uploads/${filename}`;
  return { file_url, s3_key: null, local_path: filePath };
};

/**
 * Delete a file from S3 or local storage
 * @param {string} file_url
 * @param {string|null} s3_key
 */
const deleteFile = async (file_url, s3_key) => {
  if (s3_key && isS3Configured() && s3Client) {
    const command = new DeleteObjectCommand({
      Bucket: process.env.AWS_BUCKET_NAME,
      Key: s3_key,
    });
    await s3Client.send(command);
    console.log(`🗑️  Deleted object from S3: ${s3_key}`);
    return;
  }

  // Local fallback delete
  try {
    const filename = path.basename(file_url);
    const localFilePath = path.join(uploadsDir, filename);
    if (fs.existsSync(localFilePath)) {
      fs.unlinkSync(localFilePath);
      console.log(`🗑️  Deleted local file: ${filename}`);
    }
  } catch (err) {
    console.warn(`Warning: Could not delete local file: ${err.message}`);
  }
};

module.exports = {
  isS3Configured,
  uploadFile,
  deleteFile,
  uploadsDir,
};

EOF

cat << 'EOF' > backend/src/controllers/authController.js
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../config/db');
const { JWT_SECRET } = require('../middlewares/authMiddleware');

const login = async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ success: false, message: 'Username and password are required.' });
    }

    const result = await db.query('SELECT * FROM users WHERE username = $1', [username]);
    if (result.rows.length === 0) {
      return res.status(401).json({ success: false, message: 'Invalid credentials.' });
    }

    const user = result.rows[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ success: false, message: 'Invalid credentials.' });
    }

    const token = jwt.sign(
      { id: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      message: 'Logged in successfully.',
      token,
      user: {
        id: user.id,
        username: user.username,
        role: user.role,
      },
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ success: false, message: 'Server error during login.' });
  }
};

const getMe = async (req, res) => {
  res.json({ success: true, user: req.user });
};

module.exports = {
  login,
  getMe,
};

EOF

cat << 'EOF' > backend/src/controllers/imageController.js
const db = require('../config/db');
const { uploadFile, deleteFile } = require('../config/s3');

// Upload an image
const uploadImage = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No image file uploaded.' });
    }

    const title = req.body.title || req.file.originalname;
    const uploader_name = req.body.uploader_name || 'Anonymous User';

    // Upload to S3 or local storage
    const uploadResult = await uploadFile(req.file);

    // Insert record into PostgreSQL
    const insertQuery = `
      INSERT INTO images (title, original_name, file_url, s3_key, uploader_name)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING *;
    `;
    const values = [
      title,
      req.file.originalname,
      uploadResult.file_url,
      uploadResult.s3_key,
      uploader_name,
    ];

    const result = await db.query(insertQuery, values);
    const newImage = result.rows[0];

    res.status(201).json({
      success: true,
      message: 'Image uploaded successfully!',
      image: newImage,
    });
  } catch (err) {
    console.error('Image upload error:', err);
    res.status(500).json({ success: false, message: 'Failed to upload image.', error: err.message });
  }
};

// Get all uploaded images
const getAllImages = async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM images ORDER BY created_at DESC');
    res.json({
      success: true,
      count: result.rows.length,
      images: result.rows,
    });
  } catch (err) {
    console.error('Fetch images error:', err);
    res.status(500).json({ success: false, message: 'Failed to fetch images.' });
  }
};

// Delete an image (Admin only)
const deleteImage = async (req, res) => {
  try {
    const { id } = req.params;

    // Find image in database
    const findResult = await db.query('SELECT * FROM images WHERE id = $1', [id]);
    if (findResult.rows.length === 0) {
      return res.status(404).json({ success: false, message: 'Image not found.' });
    }

    const image = findResult.rows[0];

    // Delete from AWS S3 or local filesystem
    await deleteFile(image.file_url, image.s3_key);

    // Delete from PostgreSQL
    await db.query('DELETE FROM images WHERE id = $1', [id]);

    res.json({
      success: true,
      message: `Image "${image.title || image.original_name}" deleted successfully.`,
    });
  } catch (err) {
    console.error('Delete image error:', err);
    res.status(500).json({ success: false, message: 'Failed to delete image.' });
  }
};

module.exports = {
  uploadImage,
  getAllImages,
  deleteImage,
};

EOF

cat << 'EOF' > backend/src/middlewares/authMiddleware.js
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'secret-jwt-key-image-gallery-2026';
const ADMIN_SECRET_KEY = process.env.ADMIN_SECRET_KEY || 'admin_super_secret_key';

const verifyAdmin = (req, res, next) => {
  // Option 1: Admin Secret Header
  const directKey = req.headers['x-admin-key'];
  if (directKey && directKey === ADMIN_SECRET_KEY) {
    req.user = { role: 'admin', username: 'admin' };
    return next();
  }

  // Option 2: Bearer JWT Token
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(403).json({
      success: false,
      message: 'Access denied. Admin authentication required to perform this action.'
    });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    if (decoded.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Forbidden. Only administrators can delete images.'
      });
    }
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({
      success: false,
      message: 'Invalid or expired token.'
    });
  }
};

module.exports = {
  verifyAdmin,
  JWT_SECRET,
};

EOF

cat << 'EOF' > backend/src/middlewares/uploadMiddleware.js
const multer = require('multer');

// Store file in memory buffer so it can be streamed to AWS S3 or saved locally
const storage = multer.memoryStorage();

const fileFilter = (req, file, cb) => {
  const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/svg+xml'];
  if (allowedMimeTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type! Only JPG, PNG, WEBP, GIF, and SVG images are allowed.'), false);
  }
};

const upload = multer({
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter,
});

module.exports = upload;

EOF

cat << 'EOF' > backend/src/routes/authRoutes.js
const express = require('express');
const router = express.Router();
const { login, getMe } = require('../controllers/authController');
const { verifyAdmin } = require('../middlewares/authMiddleware');

router.post('/login', login);
router.get('/me', verifyAdmin, getMe);

module.exports = router;

EOF

cat << 'EOF' > backend/src/routes/imageRoutes.js
const express = require('express');
const router = express.Router();
const upload = require('../middlewares/uploadMiddleware');
const { verifyAdmin } = require('../middlewares/authMiddleware');
const {
  uploadImage,
  getAllImages,
  deleteImage,
} = require('../controllers/imageController');

// Public routes: Anyone can upload and view
router.post('/upload', upload.single('image'), uploadImage);
router.get('/', getAllImages);

// Admin-only route: Only admin can delete
router.delete('/:id', verifyAdmin, deleteImage);

module.exports = router;

EOF

cat << 'EOF' > frontend/package.json
{
  "name": "image-gallery-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "lucide-react": "^1.16.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.2.0"
  }
}

EOF

cat << 'EOF' > frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
});

EOF

cat << 'EOF' > frontend/Dockerfile
# Stage 1: Build Vite React App
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx conf to handle React SPA routing & reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

EOF

cat << 'EOF' > frontend/nginx.conf
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy local uploads fallback
    location /uploads/ {
        proxy_pass http://backend:5000/uploads/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

EOF

cat << 'EOF' > frontend/index.html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236366f1'><path d='M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z'/></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CloudLens - AWS S3 & EC2 Image Gallery</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>

EOF

cat << 'EOF' > frontend/src/index.css
:root {
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --primary-light: #eef2ff;
  --secondary: #06b6d4;
  --accent: #f59e0b;
  --danger: #ef4444;
  --danger-hover: #dc2626;
  --danger-light: #fee2e2;
  --success: #10b981;
  --success-light: #d1fae5;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --bg-main: #f8fafc;
  --card-bg: #ffffff;
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --radius: 14px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-main);
  color: var(--text-main);
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  background: none;
  transition: all 0.2s ease;
}

input, textarea {
  font-family: inherit;
}

/* Container */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Navbar */
.navbar {
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid var(--border-color);
  padding: 16px 0;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 1.25rem;
  color: var(--primary);
  text-decoration: none;
}

.logo-badge {
  font-size: 0.7rem;
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  color: white;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 0.82rem;
  font-weight: 600;
}

.status-badge.admin {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.status-badge.user {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid var(--border-color);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--primary);
  color: white;
  padding: 9px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
}

.btn-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: white;
  color: var(--text-main);
  padding: 9px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid var(--border-color);
}

.btn-outline:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--danger-light);
  color: var(--danger);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.btn-danger:hover {
  background: var(--danger);
  color: white;
}

/* Hero Section */
.hero {
  text-align: center;
  padding: 40px 0 24px;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary-light);
  color: var(--primary);
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 700;
  margin-bottom: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
  margin-bottom: 12px;
  color: #1e1b4b;
}

.hero-title span {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  max-width: 600px;
  margin: 0 auto;
  color: var(--text-muted);
  font-size: 1.05rem;
}

/* Service Info Bar */
.service-info-bar {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.service-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid var(--border-color);
  padding: 6px 14px;
  border-radius: 30px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-main);
  box-shadow: var(--shadow-sm);
}

.service-chip .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
}

/* Upload Card */
.upload-card {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow-md);
  margin-bottom: 40px;
}

.dropzone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 36px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #f8fafc;
}

.dropzone:hover, .dropzone.active {
  border-color: var(--primary);
  background: #f5f7ff;
}

.dropzone-icon {
  width: 48px;
  height: 48px;
  color: var(--primary);
  margin-bottom: 12px;
}

.upload-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.input-field {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.input-field:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.preview-container {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
}

.preview-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
}

/* Gallery Section */
.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.gallery-title {
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 60px;
}

.image-card {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.image-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.image-thumb-wrapper {
  position: relative;
  width: 100%;
  height: 220px;
  overflow: hidden;
  background: #f1f5f9;
  cursor: pointer;
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.image-card:hover .image-thumb {
  transform: scale(1.05);
}

.image-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(4px);
  color: white;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.image-details {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.image-title {
  font-weight: 700;
  font-size: 1.05rem;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  padding: 28px;
  box-shadow: var(--shadow-xl);
  position: relative;
}

.image-modal-content {
  max-width: 900px;
  padding: 16px;
  background: #0f172a;
  color: white;
  text-align: center;
}

.image-modal-img {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: 8px;
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #f1f5f9;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.modal-close:hover {
  background: #e2e8f0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius);
  grid-column: 1 / -1;
}

.empty-icon {
  width: 56px;
  height: 56px;
  color: #94a3b8;
  margin-bottom: 12px;
}

/* Responsive */
@media (max-width: 640px) {
  .hero-title {
    font-size: 1.8rem;
  }
  .upload-form-grid {
    grid-template-columns: 1fr;
  }
}

EOF

cat << 'EOF' > frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

EOF

cat << 'EOF' > frontend/src/App.jsx
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

EOF

cat << 'EOF' > frontend/src/components/Navbar.jsx
import React from 'react';
import { Cloud, Shield, ShieldCheck, LogOut, LogIn, HardDrive } from 'lucide-react';

export default function Navbar({ isAdmin, adminUser, onOpenLogin, onLogout }) {
  return (
    <nav className="navbar">
      <div className="container nav-container">
        <div className="logo">
          <Cloud className="w-7 h-7 text-indigo-600" />
          <span>CloudLens</span>
          <span className="logo-badge">AWS S3 & EC2</span>
        </div>

        <div className="nav-actions">
          {isAdmin ? (
            <>
              <div className="status-badge admin">
                <ShieldCheck size={16} />
                <span>Admin ({adminUser?.username || 'admin'})</span>
              </div>
              <button onClick={onLogout} className="btn-outline" title="Log out from admin mode">
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <div className="status-badge user">
                <Shield size={14} />
                <span>User Mode (Upload & View)</span>
              </div>
              <button onClick={onOpenLogin} className="btn-primary" title="Login as Admin to Delete images">
                <LogIn size={16} />
                <span>Admin Login</span>
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

EOF

cat << 'EOF' > frontend/src/components/StatusBanner.jsx
import React from 'react';
import { Database, Cloud, Server, CheckCircle2 } from 'lucide-react';

export default function StatusBanner({ health }) {
  return (
    <div className="service-info-bar">
      <div className="service-chip">
        <Server size={14} color="#4f46e5" />
        <span>Compute: <strong>AWS EC2 Ready</strong></span>
        <span className="dot"></span>
      </div>

      <div className="service-chip">
        <Cloud size={14} color="#0284c7" />
        <span>Storage: <strong>{health?.storage || 'AWS S3 (or Local Fallback)'}</strong></span>
        <span className="dot"></span>
      </div>

      <div className="service-chip">
        <Database size={14} color="#059669" />
        <span>Database: <strong>{health?.database || 'PostgreSQL (Docker)'}</strong></span>
        <span className="dot"></span>
      </div>
    </div>
  );
}

EOF

cat << 'EOF' > frontend/src/components/ImageUpload.jsx
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

EOF

cat << 'EOF' > frontend/src/components/ImageGallery.jsx
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

EOF

cat << 'EOF' > frontend/src/components/ImageModal.jsx
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

EOF

cat << 'EOF' > frontend/src/components/AdminLoginModal.jsx
import React, { useState } from 'react';
import { X, Lock, ShieldCheck, Loader2 } from 'lucide-react';

export default function AdminLoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Login failed. Please check credentials.');
      }

      onLoginSuccess(data.token, data.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} title="Close">
          <X size={18} />
        </button>

        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: '#eef2ff',
            color: '#4f46e5',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '10px'
          }}>
            <Lock size={22} />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Admin Login</h3>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            Only administrator users are authorized to delete images.
          </p>
        </div>

        {error && (
          <div style={{
            background: '#fee2e2',
            color: '#b91c1c',
            padding: '8px 12px',
            borderRadius: '8px',
            marginBottom: '16px',
            fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
              Username
            </label>
            <input
              type="text"
              className="input-field"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            padding: '10px 12px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            color: '#64748b',
            marginBottom: '20px'
          }}>
            💡 <strong>Default Admin Credentials:</strong><br />
            Username: <code>admin</code> | Password: <code>admin123</code>
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <ShieldCheck size={16} />
                <span>Login as Admin</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

EOF

echo "⚙️ Creating backend .env file..."
cat << 'EOF' > backend/.env
PORT=5000
BASE_URL=http://localhost:5000
JWT_SECRET=super_secret_jwt_key_gallery_2026
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_SECRET_KEY=admin_super_secret_key

DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=image_gallery

# AWS S3 Settings
AWS_ACCESS_KEY_ID=__REPLACE_AWS_ACCESS_KEY__
AWS_SECRET_ACCESS_KEY=__REPLACE_AWS_SECRET_KEY__
AWS_REGION=__REPLACE_AWS_REGION__
AWS_BUCKET_NAME=samriddhabaket1718
EOF

echo "🐳 Building and starting all Docker containers..."
sudo docker-compose up -d --build

echo "✅ Deployment complete! Website is live on port 80 and 3000!"
sudo docker ps
