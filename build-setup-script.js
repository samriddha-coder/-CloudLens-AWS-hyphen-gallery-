const fs = require('fs');
const path = require('path');

const files = [
  'docker-compose.yml',
  'backend/package.json',
  'backend/Dockerfile',
  'backend/src/server.js',
  'backend/src/config/db.js',
  'backend/src/config/s3.js',
  'backend/src/controllers/authController.js',
  'backend/src/controllers/imageController.js',
  'backend/src/middlewares/authMiddleware.js',
  'backend/src/middlewares/uploadMiddleware.js',
  'backend/src/routes/authRoutes.js',
  'backend/src/routes/imageRoutes.js',
  'frontend/package.json',
  'frontend/vite.config.js',
  'frontend/Dockerfile',
  'frontend/nginx.conf',
  'frontend/index.html',
  'frontend/src/index.css',
  'frontend/src/main.jsx',
  'frontend/src/App.jsx',
  'frontend/src/components/Navbar.jsx',
  'frontend/src/components/StatusBanner.jsx',
  'frontend/src/components/ImageUpload.jsx',
  'frontend/src/components/ImageGallery.jsx',
  'frontend/src/components/ImageModal.jsx',
  'frontend/src/components/AdminLoginModal.jsx'
];

let script = `#!/bin/bash
set -e

echo "🚀 Installing Docker & Docker Compose on EC2..."
sudo apt update -y
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

echo "📁 Creating application directories..."
mkdir -p app/backend/src/config app/backend/src/controllers app/backend/src/middlewares app/backend/src/routes app/backend/uploads app/frontend/src/components
cd app

`;

for (const f of files) {
  const content = fs.readFileSync(path.join(__dirname, f), 'utf8');
  script += `cat << 'EOF' > ${f}\n${content}\nEOF\n\n`;
}

script += `echo "⚙️ Creating backend .env file..."
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
`;

fs.writeFileSync(path.join(__dirname, 'setup-ec2.sh'), script);
console.log('setup-ec2.sh generated successfully! File size: ' + (script.length / 1024).toFixed(2) + ' KB');
