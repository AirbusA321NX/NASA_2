const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
require('dotenv').config();

const logger = require('./utils/logger');
const errorHandler = require('./middleware/errorHandler');
const publicationRoutes = require('./routes/publications');
const searchRoutes = require('./routes/search');
const analyticsRoutes = require('./routes/analytics');
const knowledgeGraphRoutes = require('./routes/knowledgeGraph');
const osdrFilesRoutes = require('./routes/osdrFiles');

const app = express();
const PORT = process.env.PORT || 4000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://osdr.nasa.gov"],
    },
  },
}));

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// Body parsing middleware
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging middleware
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// API routes
app.use('/api/publications', publicationRoutes);
app.use('/api/search', searchRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/knowledge-graph', knowledgeGraphRoutes);
app.use('/api/osdr', osdrFilesRoutes);

// Root endpoint with API information
app.get('/', (req, res) => {
  res.json({
    name: 'NASA Space Biology Knowledge Engine API',
    version: '1.0.0',
    description: 'Backend API for the NASA Space Biology Knowledge Engine',
    documentation: `${req.protocol}://${req.get('host')}/api/docs`,
    endpoints: {
      health: '/health',
      publications: '/api/publications',
      search: '/api/search',
      analytics: '/api/analytics',
      knowledgeGraph: '/api/knowledge-graph',
      osdrFiles: '/api/osdr/files'
    },
    timestamp: new Date().toISOString()
  });
});

// API documentation endpoint
app.get('/api/docs', (req, res) => {
  res.json({
    openapi: '3.0.0',
    info: {
      title: 'NASA Space Biology Knowledge Engine API',
      version: '1.0.0',
      description: 'API for accessing and analyzing NASA bioscience publications'
    },
    servers: [
      {
        url: `${req.protocol}://${req.get('host')}`,
        description: 'Development server'
      }
    ],
    paths: {
      '/api/publications': {
        get: {
          summary: 'Get publications',
          parameters: [
            { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
            { name: 'offset', in: 'query', schema: { type: 'integer', default: 0 } }
          ]
        }
      },
      '/api/search': {
        post: {
          summary: 'Search publications',
          requestBody: {
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    query: { type: 'string' },
                    filters: { type: 'object' }
                  }
                }
              }
            }
          }
        }
      },
      '/api/analytics': {
        get: {
          summary: 'Get analytics data'
        }
      },
      '/api/knowledge-graph': {
        get: {
          summary: 'Get knowledge graph data'
        }
      },
      '/api/osdr/files': {
        get: {
          summary: 'Get OSDR files',
          description: 'Retrieve metadata for all files in the NASA OSDR repository'
        }
      }
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: `The requested endpoint ${req.originalUrl} does not exist`,
    availableEndpoints: [
      '/health',
      '/api/publications',
      '/api/search',
      '/api/analytics',
      '/api/knowledge-graph',
      '/api/osdr/files'
    ]
  });
});

// Error handling middleware
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 NASA Space Biology Knowledge Engine API running on port ${PORT}`);
  logger.info(`📚 API Documentation: http://localhost:${PORT}/api/docs`);
  logger.info(`🏥 Health Check: http://localhost:${PORT}/health`);
  
  // Log environment info
  logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
  logger.info(`CORS Origins: ${process.env.CORS_ORIGIN || 'http://localhost:3000'}`);
});

module.exports = app;