const express = require('express');
const axios = require('axios');
const logger = require('../utils/logger');

const router = express.Router();

// Data pipeline API URL
const DATA_PIPELINE_URL = process.env.DATA_PIPELINE_URL || 'http://localhost:8002';

/**
 * @route   GET /api/osdr/files
 * @desc    Get all OSDR files with metadata from NASA S3 repository
 * @access  Public
 */
router.get('/files', async (req, res, next) => {
  try {
    logger.info('Fetching OSDR files from data pipeline...');
    
    // Forward request to data pipeline
    const response = await axios.get(`${DATA_PIPELINE_URL}/osdr-files`, {
      timeout: 30000 // 30 second timeout for data fetching
    });
    
    // Validate response data
    if (!response.data || !Array.isArray(response.data)) {
      logger.warn('Invalid data received from data pipeline for OSDR files');
      return res.json({
        success: true,
        data: [],
        message: 'No OSDR files data available'
      });
    }
    
    res.json({
      success: true,
      data: response.data,
      count: response.data.length
    });

  } catch (error) {
    logger.error(`Error fetching OSDR files: ${error.message}`);
    
    if (error.response) {
      // Data pipeline returned an error
      logger.error(`Data pipeline error response: ${JSON.stringify(error.response.data)}`);
      return res.status(error.response.status).json({
        success: false,
        error: error.response.data,
        message: 'Failed to fetch OSDR files from data pipeline'
      });
    }
    
    if (error.code === 'ECONNREFUSED') {
      logger.error('Data pipeline is not running or not accessible');
      return res.status(503).json({
        success: false,
        error: 'Service Unavailable',
        message: 'Data pipeline service is not running. Please start the data pipeline server.',
        service: 'NASA OSDR Data Pipeline',
        endpoint: `${DATA_PIPELINE_URL}/osdr-files`
      });
    }
    
    // Return empty data instead of error to maintain frontend functionality
    res.json({
      success: true,
      data: [],
      message: 'No OSDR files data available at this time'
    });
  }
});

/**
 * @route   GET /api/osdr/files/:studyId
 * @desc    Get files for a specific OSDR study from NASA S3 repository
 * @access  Public
 */
router.get('/files/:studyId', async (req, res, next) => {
  try {
    const { studyId } = req.params;
    logger.info(`Fetching files for OSDR study: ${studyId}`);
    
    // Validate studyId format (should be GLDS-XXXX)
    const studyIdRegex = /^GLDS-\d+$/;
    if (!studyIdRegex.test(studyId)) {
      logger.warn(`Invalid study ID format: ${studyId}`);
      return res.status(400).json({
        success: false,
        error: 'Invalid Study ID',
        message: 'Study ID must be in the format GLDS-XXXX'
      });
    }
    
    // Forward request to data pipeline
    const response = await axios.get(`${DATA_PIPELINE_URL}/osdr-files/${studyId}`, {
      timeout: 30000 // 30 second timeout for data fetching
    });
    
    // Validate response data
    if (!response.data || !Array.isArray(response.data)) {
      logger.warn(`Invalid data received from data pipeline for study ${studyId}`);
      return res.json({
        success: true,
        data: [],
        message: `No files found for study ${studyId}`
      });
    }
    
    res.json({
      success: true,
      data: response.data,
      count: response.data.length,
      studyId: studyId
    });

  } catch (error) {
    logger.error(`Error fetching files for study ${req.params.studyId}: ${error.message}`);
    
    if (error.response) {
      // Data pipeline returned an error
      logger.error(`Data pipeline error response for study ${req.params.studyId}: ${JSON.stringify(error.response.data)}`);
      return res.status(error.response.status).json({
        success: false,
        error: error.response.data,
        message: `Failed to fetch files for study ${req.params.studyId} from data pipeline`
      });
    }
    
    if (error.code === 'ECONNREFUSED') {
      logger.error('Data pipeline is not running or not accessible');
      return res.status(503).json({
        success: false,
        error: 'Service Unavailable',
        message: 'Data pipeline service is not running. Please start the data pipeline server.',
        service: 'NASA OSDR Data Pipeline',
        endpoint: `${DATA_PIPELINE_URL}/osdr-files/${req.params.studyId}`
      });
    }
    
    // Return empty data instead of error
    res.json({
      success: true,
      data: [],
      message: `No files found for study ${req.params.studyId} at this time`
    });
  }
});

module.exports = router;