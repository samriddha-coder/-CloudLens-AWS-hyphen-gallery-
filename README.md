# 📸 CloudLens - AWS S3 & EC2 Image Gallery Web Application

A full-stack image upload, viewing, and management web application built for seamless deployment on **AWS EC2** and storage in **AWS S3**, with **PostgreSQL** (Docker) for metadata and **Node.js** + **React**.

---

## 🌟 Features

- **Image Upload & Gallery (Public)**:
  - Any user can upload images (PNG, JPG, WEBP, GIF, SVG) with custom titles and uploader names.
  - Interactive grid view with instant full-resolution preview modal.
- **Admin-Only Deletion (Role-Based Access Control)**:
  - Only authorized administrators can delete images.
  - Standard users see read-only controls with lock indicators.
  - Deleting an image permanently removes both the file from **AWS S3** and the metadata from **PostgreSQL**.
- **AWS S3 Cloud Ready (with Seamless Local Fallback)**:
  - Automatically uploads to your AWS S3 bucket when AWS keys are provided.
  - If AWS keys are not yet configured, automatically stores files locally in `backend/uploads` so you can test immediately!
- **PostgreSQL Database (Dockerized with Local Fallback)**:
  - Stores image metadata (`id`, `title`, `original_name`, `file_url`, `s3_key`, `uploader_name`, `created_at`).
  - Pre-seeded admin user (`admin` / `admin123`).
  - If Docker/Postgres is not running locally, seamlessly uses local JSON fallback storage.

---

## ⚙️ Architecture & Tech Stack

> 💡 **নোট (Note regarding your prompt):** আপনি প্রশ্নে উল্লেখ করেছিলেন *"frontend ta hobe nodejs e ar baackend ta hobe react netiv"*; টেকনিক্যালি **React Native** শুধুমাত্র মোবাইল অ্যাপ্লিকেশনের (Android & iOS) জন্য ব্যবহৃত হয় এবং এটি কোনো Backend টেকনোলজি নয়। অন্যদিকে **Node.js** হলো বিশ্বস্ত ও শক্তিশালী সার্ভার/Backend রানটাইম। তাই স্ট্যান্ডার্ড ওয়েব আর্কিটেকচার অনুযায়ী:
> - **Frontend:** **React.js** (Vite + Modern Responsive CSS + Lucide Icons)
> - **Backend:** **Node.js** (Express.js REST API + AWS S3 SDK + PostgreSQL)
> - **Database:** **PostgreSQL** (Docker Compose)
> - **Cloud Services:** **AWS EC2** (Compute / Host) & **AWS S3** (Object Storage)

---

## 📁 Project Structure

```text
abc/
├── backend/
│   ├── src/
│   │   ├── config/
│   │   │   ├── db.js             # PostgreSQL connection & auto-table creation
│   │   │   └── s3.js             # AWS S3 upload/delete handler + local fallback
│   │   ├── controllers/
│   │   │   ├── authController.js # Admin authentication (JWT)
│   │   │   └── imageController.js# Upload, get all, delete images
│   │   ├── middlewares/
│   │   │   ├── authMiddleware.js # Role verification (Admin only)
│   │   │   └── uploadMiddleware.js# Multer memory storage & image filter
│   │   ├── routes/
│   │   │   ├── authRoutes.js     # /api/auth routes
│   │   │   └── imageRoutes.js    # /api/images routes
│   │   └── server.js             # Express app entrypoint
│   ├── .env                      # Backend environment variables
│   ├── .env.example              # Example environment configuration
│   ├── Dockerfile                # Backend containerization for EC2
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminLoginModal.jsx# Admin login dialog
│   │   │   ├── ImageGallery.jsx  # Grid gallery & admin delete button
│   │   │   ├── ImageModal.jsx    # Fullscreen lightbox preview
│   │   │   ├── ImageUpload.jsx   # Drag-and-drop uploader
│   │   │   ├── Navbar.jsx        # Navigation & role indicator
│   │   │   └── StatusBanner.jsx  # Live status of S3, EC2 & DB
│   │   ├── App.jsx               # Main React component
│   │   ├── index.css             # Glassmorphism modern UI styling
│   │   └── main.jsx
│   ├── Dockerfile                # Frontend multi-stage Nginx build
│   ├── nginx.conf                # Nginx reverse proxy configuration
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml            # Multi-container orchestration (Postgres, Backend, Frontend)
├── .gitignore
└── README.md
```

---

## 🚀 How to Run Locally

### 1. Prerequisites
- **Node.js**: v18+ installed
- **Docker** *(Optional for local test, required for PostgreSQL container)*

### 2. Start Backend
Open a terminal in the root directory:
```bash
cd backend
npm install
npm run dev
```
Backend will start on: `http://localhost:5000`

### 3. Start Frontend
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend will start on: `http://localhost:3000`

### 4. Running Everything with Docker (Recommended)
If you have Docker Desktop installed:
```bash
docker compose up -d --build
```
- Frontend: `http://localhost:3000` or `http://localhost`
- Backend: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

---

## 🔐 Default Admin Credentials

- **Username**: `admin`
- **Password**: `admin123`

*Click "Admin Login" on the top right of the website to log in. Once logged in, the red **Delete** button appears on each image card!*

---

## ☁️ AWS S3 & EC2 Deployment Guide

যখন আপনি আপনার AWS অ্যাকাউন্ট থেকে তথ্য প্রদান করবেন, তখন আমরা সরাসরি এটি ডেপ্লয় করব। নিচের ধাপগুলো অনুসরণ করে প্রয়োজনীয় তথ্য সংগ্রহ করতে পারবেন:

### 1. AWS S3 Setup (Bucket & IAM Keys)
1. AWS Console-এ গিয়ে **S3** সার্চ করে একটি নতুন Bucket তৈরি করুন (যেমন: `my-gallery-bucket-2026`).
2. **Object Ownership**: ACLs enabled নির্বাচন করুন অথবা Bucket Policy দিয়ে Public Read দিন।
3. **CORS Configuration** (S3 Bucket -> Permissions -> Cross-origin resource sharing):
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```
4. **IAM User**:
   - AWS IAM-এ যান এবং একটি নতুন User তৈরি করুন।
   - Attach policies: `AmazonS3FullAccess`.
   - Security credentials -> **Create access key** (Application running outside AWS বা CLI নির্বাচন করুন)।
   - **Access Key ID** এবং **Secret Access Key** কপি করে রাখুন।

5. Backend `.env` ফাইলে ভ্যালুগুলো বসিয়ে দিন:
```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_BUCKET_NAME=my-gallery-bucket-2026
```

---

### 2. AWS EC2 Deployment
1. **EC2 Instance Launch**:
   - Ubuntu Server 24.04 বা 22.04 LTS (t2.micro বা t3.small).
   - Key Pair (.pem) ডাউনলোড করে রাখুন।
   - **Security Group Inbound Rules**:
     - `SSH (Port 22)`: My IP
     - `HTTP (Port 80)`: Anywhere (0.0.0.0/0)
     - `Custom TCP (Port 5000)`: Anywhere (0.0.0.0/0)
2. **SSH Connection to EC2**:
```bash
ssh -i "your-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```
3. **Install Docker & Docker Compose on EC2**:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```
4. **Deploy Application**:
```bash
# Clone or copy your code to EC2
git clone <your-repository-url> app
cd app

# Add your production .env credentials
nano backend/.env

# Run all services via Docker
docker-compose up -d --build
```
5. আপনার ব্রাউজারে প্রবেশ করুন: `http://<YOUR_EC2_PUBLIC_IP>` এবং আপনার ওয়েবসাইট লাইভ হয়ে যাবে! 🎉
