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
