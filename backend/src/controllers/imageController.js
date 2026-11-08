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
