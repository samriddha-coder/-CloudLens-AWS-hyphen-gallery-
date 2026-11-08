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
