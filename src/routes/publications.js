const express = require('express');
const axios = require('axios');
const { body, query, validationResult } = require('express-validator');
const logger = require('../utils/logger');

const router = express.Router();

// Data pipeline API URL
const DATA_PIPELINE_URL = process.env.DATA_PIPELINE_URL || 'http://localhost:8002';

/**
 * @route   GET /api/publications
 * @desc    Get all publications with pagination
 * @access  Public
 */
router.get('/', [
  query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
  query('offset').optional().isInt({ min: 0 }).withMessage('Offset must be non-negative'),
], async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }

    const { limit = 50, offset = 0 } = req.query;

    // Forward request to data pipeline
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit, offset }
    });

    res.json({
      success: true,
      data: response.data
    });

  } catch (error) {
    logger.error(`Error fetching publications: ${error.message}`);
    
    if (error.response) {
      // Data pipeline returned an error
      return res.status(error.response.status).json({
        success: false,
        error: error.response.data
      });
    }
    
    next(error);
  }
});

/**
 * @route   GET /api/publications/:id
 * @desc    Get single publication by OSDR ID
 * @access  Public
 */
router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;

    // Search for publication by OSDR ID
    const response = await axios.post(`${DATA_PIPELINE_URL}/search`, {
      query: id,
      limit: 1
    });

    const publications = response.data.results;
    
    if (!publications || publications.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Publication not found'
      });
    }

    // Find exact match by OSDR ID
    const publication = publications.find(pub => pub.osdr_id === id);
    
    if (!publication) {
      return res.status(404).json({
        success: false,
        error: 'Publication not found'
      });
    }

    res.json({
      success: true,
      data: publication
    });

  } catch (error) {
    logger.error(`Error fetching publication ${req.params.id}: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/publications/research-areas
 * @desc    Get all research areas
 * @access  Public
 */
router.get('/meta/research-areas', async (req, res, next) => {
  try {
    // Get statistics which includes research areas
    const response = await axios.get(`${DATA_PIPELINE_URL}/statistics`);
    
    const researchAreas = Object.keys(response.data.top_research_areas || {});
    
    res.json({
      success: true,
      data: researchAreas
    });

  } catch (error) {
    logger.error(`Error fetching research areas: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/publications/organisms
 * @desc    Get all organisms
 * @access  Public
 */
router.get('/meta/organisms', async (req, res, next) => {
  try {
    // Get statistics which includes organisms
    const response = await axios.get(`${DATA_PIPELINE_URL}/statistics`);
    
    const organisms = response.data.top_organisms || [];
    
    res.json({
      success: true,
      data: organisms
    });

  } catch (error) {
    logger.error(`Error fetching organisms: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/publications/authors
 * @desc    Get all authors
 * @access  Public
 */
router.get('/meta/authors', async (req, res, next) => {
  try {
    // Get all publications and extract unique authors
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 1000 } // Get more to extract authors
    });

    const publications = response.data.publications || [];
    const authorsSet = new Set();
    
    publications.forEach(pub => {
      if (pub.authors && Array.isArray(pub.authors)) {
        pub.authors.forEach(author => authorsSet.add(author));
      }
    });

    const authors = Array.from(authorsSet).sort();

    res.json({
      success: true,
      data: authors
    });

  } catch (error) {
    logger.error(`Error fetching authors: ${error.message}`);
    next(error);
  }
});

/**
 * @route   POST /api/publications/bulk
 * @desc    Create or update multiple publications
 * @access  Private (Admin only - would need auth middleware)
 */
router.post('/bulk', [
  body('publications').isArray().withMessage('Publications must be an array'),
  body('publications.*.title').notEmpty().withMessage('Title is required'),
  body('publications.*.osdr_id').notEmpty().withMessage('OSDR ID is required'),
], async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }

    // This would typically involve database operations
    // For now, we'll return a placeholder response
    res.json({
      success: true,
      message: 'Bulk publication update not implemented yet',
      data: {
        processed: req.body.publications.length,
        created: 0,
        updated: 0,
        errors: []
      }
    });

  } catch (error) {
    logger.error(`Error in bulk publication update: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/publications/trending
 * @desc    Get trending publications (most accessed/relevant)
 * @access  Public
 */
router.get('/meta/trending', async (req, res, next) => {
  try {
    // Get recent publications (simulating trending)
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 10, offset: 0 }
    });

    // Sort by publication date (newest first) as a proxy for trending
    const publications = response.data.publications || [];
    const trending = publications
      .sort((a, b) => new Date(b.publication_date) - new Date(a.publication_date))
      .slice(0, 5);

    res.json({
      success: true,
      data: trending
    });

  } catch (error) {
    logger.error(`Error fetching trending publications: ${error.message}`);
    next(error);
  }
});

module.exports = router;