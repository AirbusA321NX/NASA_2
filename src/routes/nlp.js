const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;

/**
 * Natural Language Processing Routes for NASA OSDR
 * 
 * Provides endpoints for advanced NLP analysis including:
 * - Experiment metadata analysis
 * - Literature summarization
 * - Cross-reference detection
 * - Research hypothesis generation
 * - Complex result interpretation
 */

class NLPService {
  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.nlpScriptPath = path.join(__dirname, '../../../data-pipeline/nlp_analyzer.py');
    this.isAvailable = false;
    this.checkAvailability();
  }

  async checkAvailability() {
    try {
      // Check if Python NLP script exists
      await fs.access(this.nlpScriptPath);
      this.isAvailable = true;
      logger.info('NLP service is available');
    } catch (error) {
      logger.warn('NLP service is not available - Python script not found');
      this.isAvailable = false;
    }
  }

  async runPythonAnalysis(documents, analysisType = 'complete', options = {}) {
    if (!this.isAvailable) {
      throw new Error('NLP service is not available');
    }

    return new Promise((resolve, reject) => {
      const tempInputFile = path.join(__dirname, '../../../data/temp_nlp_input.json');
      const tempOutputFile = path.join(__dirname, '../../../data/temp_nlp_output.json');

      // Prepare input data
      const inputData = {
        documents: documents.slice(0, 20), // Limit for performance
        analysis_type: analysisType,
        options: {
          mistral_api_key: process.env.MISTRAL_API_KEY,
          ...options
        }
      };

      // Write input data to temporary file
      fs.writeFile(tempInputFile, JSON.stringify(inputData, null, 2))
        .then(() => {
          // Spawn Python process
          const pythonProcess = spawn(this.pythonPath, [
            this.nlpScriptPath,
            '--input', tempInputFile,
            '--output', tempOutputFile,
            '--analysis-type', analysisType
          ], {
            stdio: ['pipe', 'pipe', 'pipe']
          });

          let stdout = '';
          let stderr = '';

          pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
          });

          pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
          });

          pythonProcess.on('close', async (code) => {
            try {
              // Clean up input file
              await fs.unlink(tempInputFile).catch(() => {});

              if (code !== 0) {
                logger.error(`Python NLP process failed with code ${code}: ${stderr}`);
                reject(new Error(`NLP analysis failed: ${stderr}`));
                return;
              }

              // Read output file
              const outputData = await fs.readFile(tempOutputFile, 'utf8');
              const results = JSON.parse(outputData);

              // Clean up output file
              await fs.unlink(tempOutputFile).catch(() => {});

              resolve(results);
            } catch (error) {
              logger.error(`Error processing NLP results: ${error.message}`);
              reject(error);
            }
          });

          // Set timeout for long-running processes
          setTimeout(() => {
            pythonProcess.kill('SIGTERM');
            reject(new Error('NLP analysis timeout'));
          }, 300000); // 5 minutes timeout

        })
        .catch(reject);
    });
  }
}

const nlpService = new NLPService();

/**
 * @route POST /api/nlp/analyze
 * @desc Run complete NLP analysis on documents
 * @access Public
 */
router.post('/analyze', async (req, res) => {
  try {
    const { documents, options = {} } = req.body;

    if (!documents || !Array.isArray(documents) || documents.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Documents array is required'
      });
    }

    logger.info(`Starting NLP analysis for ${documents.length} documents`);

    const results = await nlpService.runPythonAnalysis(documents, 'complete', options);

    res.json({
      success: true,
      data: results,
      metadata: {
        documents_analyzed: documents.length,
        analysis_type: 'complete',
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    logger.error(`NLP analysis error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/nlp/metadata
 * @desc Analyze experiment metadata
 * @access Public
 */
router.post('/metadata', async (req, res) => {
  try {
    const { documents, options = {} } = req.body;

    if (!documents || !Array.isArray(documents)) {
      return res.status(400).json({
        success: false,
        error: 'Documents array is required'
      });
    }

    const results = await nlpService.runPythonAnalysis(documents, 'metadata', options);

    res.json({
      success: true,
      data: results.experiment_metadata || [],
      metadata: {
        documents_processed: documents.length,
        analysis_type: 'metadata'
      }
    });

  } catch (error) {
    logger.error(`Metadata analysis error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/nlp/literature
 * @desc Analyze literature content
 * @access Public
 */
router.post('/literature', async (req, res) => {
  try {
    const { documents, options = {} } = req.body;

    if (!documents || !Array.isArray(documents)) {
      return res.status(400).json({
        success: false,
        error: 'Documents array is required'
      });
    }

    const results = await nlpService.runPythonAnalysis(documents, 'literature', options);

    res.json({
      success: true,
      data: results.literature_analyses || [],
      metadata: {
        documents_processed: documents.length,
        analysis_type: 'literature'
      }
    });

  } catch (error) {
    logger.error(`Literature analysis error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/nlp/cross-reference
 * @desc Find cross-references between studies
 * @access Public
 */
router.post('/cross-reference', async (req, res) => {
  try {
    const { documents, similarity_threshold = 0.3, options = {} } = req.body;

    if (!documents || !Array.isArray(documents) || documents.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'At least 2 documents are required for cross-reference analysis'
      });
    }

    const analysisOptions = {
      ...options,
      similarity_threshold
    };

    const results = await nlpService.runPythonAnalysis(documents, 'cross_reference', analysisOptions);

    res.json({
      success: true,
      data: results.cross_references || [],
      metadata: {
        documents_processed: documents.length,
        similarity_threshold,
        cross_references_found: results.cross_references?.length || 0
      }
    });

  } catch (error) {
    logger.error(`Cross-reference analysis error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/nlp/hypotheses
 * @desc Generate research hypotheses
 * @access Public
 */
router.post('/hypotheses', async (req, res) => {
  try {
    const { documents, research_area, options = {} } = req.body;

    if (!documents || !Array.isArray(documents)) {
      return res.status(400).json({
        success: false,
        error: 'Documents array is required'
      });
    }

    const analysisOptions = {
      ...options,
      research_area
    };

    const results = await nlpService.runPythonAnalysis(documents, 'hypotheses', analysisOptions);

    res.json({
      success: true,
      data: results.research_hypotheses || {},
      metadata: {
        documents_processed: documents.length,
        research_area: research_area || 'general',
        hypotheses_generated: results.research_hypotheses?.hypotheses?.length || 0
      }
    });

  } catch (error) {
    logger.error(`Hypothesis generation error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/nlp/interpret
 * @desc Interpret complex research results
 * @access Public
 */
router.post('/interpret', async (req, res) => {
  try {
    const { results_data, audience = ['scientific', 'general'], options = {} } = req.body;

    if (!results_data || typeof results_data !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Results data object is required'
      });
    }

    const analysisOptions = {
      ...options,
      audience: Array.isArray(audience) ? audience : [audience]
    };

    const interpretations = await nlpService.runPythonAnalysis([results_data], 'interpret', analysisOptions);

    res.json({
      success: true,
      data: interpretations,
      metadata: {
        audience_types: analysisOptions.audience,
        interpretation_count: Object.keys(interpretations).length
      }
    });

  } catch (error) {
    logger.error(`Result interpretation error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route GET /api/nlp/status
 * @desc Get NLP service status
 * @access Public
 */
router.get('/status', async (req, res) => {
  try {
    await nlpService.checkAvailability();

    res.json({
      success: true,
      data: {
        available: nlpService.isAvailable,
        python_path: nlpService.pythonPath,
        script_path: nlpService.nlpScriptPath,
        mistral_configured: !!process.env.MISTRAL_API_KEY,
        capabilities: [
          'experiment_metadata_analysis',
          'literature_analysis',
          'cross_reference_detection',
          'research_hypothesis_generation',
          'complex_result_interpretation'
        ]
      }
    });

  } catch (error) {
    logger.error(`NLP status check error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route GET /api/nlp/capabilities
 * @desc Get detailed information about NLP capabilities
 * @access Public
 */
router.get('/capabilities', (req, res) => {
  res.json({
    success: true,
    data: {
      experiment_metadata_analysis: {
        description: "Extract and structure experiment metadata from unstructured text",
        features: [
          "Protocol type identification",
          "Organism extraction",
          "Methodology detection", 
          "Objective extraction",
          "Safety consideration identification"
        ],
        input: "NASA OSDR experiment documents",
        output: "Structured metadata objects"
      },
      literature_analysis: {
        description: "Comprehensive analysis of scientific literature using AI",
        features: [
          "AI-powered summarization",
          "Key findings extraction",
          "Methodology identification",
          "Research gap analysis",
          "Future directions identification"
        ],
        input: "Scientific papers and abstracts",
        output: "Structured literature analysis"
      },
      cross_reference_detection: {
        description: "Automatic detection of related studies using semantic similarity",
        features: [
          "Semantic similarity calculation",
          "Common theme extraction", 
          "Relationship type classification",
          "AI-powered relevance explanation"
        ],
        input: "Collection of research documents",
        output: "Cross-reference relationships with explanations"
      },
      research_hypothesis_generation: {
        description: "Generate novel research hypotheses based on existing literature",
        features: [
          "Context-aware hypothesis generation",
          "Research area specialization",
          "Novelty and feasibility scoring",
          "Space-mission relevance assessment"
        ],
        input: "Research context and existing findings",
        output: "Ranked research hypotheses with explanations"
      },
      complex_result_interpretation: {
        description: "Interpret complex research results for different audiences",
        features: [
          "Multi-audience interpretation",
          "Scientific to plain language translation",
          "Mission planning implications",
          "Clinical relevance assessment"
        ],
        input: "Complex research results and data",
        output: "Audience-specific interpretations"
      }
    }
  });
});

module.exports = router;