const express = require('express');
const axios = require('axios');
const { query, validationResult } = require('express-validator');
const logger = require('../utils/logger');

const router = express.Router();

// Data pipeline API URL
const DATA_PIPELINE_URL = process.env.DATA_PIPELINE_URL || 'http://localhost:8002';

/**
 * @route   GET /api/knowledge-graph
 * @desc    Get knowledge graph data
 * @access  Public
 */
router.get('/', [
  query('limit').optional().isInt({ min: 10, max: 500 }).withMessage('Limit must be between 10 and 500'),
  query('depth').optional().isInt({ min: 1, max: 3 }).withMessage('Depth must be between 1 and 3'),
], async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }

    const { limit = 100, depth = 2 } = req.query;

    // Get publications data
    const publicationsResponse = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit }
    });

    const publications = publicationsResponse.data.publications || [];

    // Get OSDR files data
    let osdrFiles = [];
    try {
      const filesResponse = await axios.get(`${DATA_PIPELINE_URL}/osdr-files`);
      osdrFiles = filesResponse.data || [];
    } catch (error) {
      logger.warn(`Failed to fetch OSDR files data: ${error.message}`);
    }

    // Build knowledge graph with both publications and OSDR files
    const knowledgeGraph = buildKnowledgeGraph(publications, osdrFiles, depth);

    res.json({
      success: true,
      data: {
        graph: knowledgeGraph,
        metadata: {
          total_nodes: knowledgeGraph.nodes.length,
          total_edges: knowledgeGraph.edges.length,
          node_types: getNodeTypeCounts(knowledgeGraph.nodes),
          edge_types: getEdgeTypeCounts(knowledgeGraph.edges),
          depth,
          generated_at: new Date().toISOString()
        }
      }
    });

  } catch (error) {
    logger.error(`Error building knowledge graph: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/knowledge-graph/nodes/:id
 * @desc    Get detailed information about a specific node
 * @access  Public
 */
router.get('/nodes/:id', async (req, res, next) => {
  try {
    const { id } = req.params;

    // Get all publications to find the node
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 500 }
    });

    const publications = response.data.publications || [];
    const nodeInfo = findNodeInformation(id, publications);

    if (!nodeInfo) {
      return res.status(404).json({
        success: false,
        error: 'Node not found'
      });
    }

    res.json({
      success: true,
      data: nodeInfo
    });

  } catch (error) {
    logger.error(`Error fetching node information: ${error.message}`);
    next(error);
  }
});

/**
 * @route   POST /api/knowledge-graph/search
 * @desc    Search knowledge graph for specific patterns
 * @access  Public
 */
router.post('/search', async (req, res, next) => {
  try {
    const { query, node_types, max_results = 50 } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: 'Query is required'
      });
    }

    // Get publications data
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 300 }
    });

    const publications = response.data.publications || [];
    const graph = buildKnowledgeGraph(publications, 2);

    // Search nodes
    const matchingNodes = searchGraphNodes(graph.nodes, query, node_types);
    const subgraph = extractSubgraph(graph, matchingNodes.slice(0, max_results));

    res.json({
      success: true,
      data: {
        query,
        matching_nodes: matchingNodes.length,
        subgraph,
        search_metadata: {
          node_types_searched: node_types || 'all',
          max_results,
          timestamp: new Date().toISOString()
        }
      }
    });

  } catch (error) {
    logger.error(`Error searching knowledge graph: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/knowledge-graph/paths
 * @desc    Find paths between two nodes
 * @access  Public
 */
router.get('/paths', [
  query('from').notEmpty().withMessage('From node is required'),
  query('to').notEmpty().withMessage('To node is required'),
  query('max_length').optional().isInt({ min: 1, max: 6 }).withMessage('Max length must be between 1 and 6'),
], async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }

    const { from, to, max_length = 4 } = req.query;

    // Get publications data and build graph
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 300 }
    });

    const publications = response.data.publications || [];
    const graph = buildKnowledgeGraph(publications, 2);

    // Find paths
    const paths = findShortestPaths(graph, from, to, max_length);

    res.json({
      success: true,
      data: {
        from,
        to,
        paths: paths.slice(0, 10), // Limit to top 10 paths
        path_count: paths.length,
        shortest_path_length: paths.length > 0 ? paths[0].length : null
      }
    });

  } catch (error) {
    logger.error(`Error finding graph paths: ${error.message}`);
    next(error);
  }
});

/**
 * @route   GET /api/knowledge-graph/clusters
 * @desc    Get clustered view of the knowledge graph
 * @access  Public
 */
router.get('/clusters', async (req, res, next) => {
  try {
    // Get publications data
    const response = await axios.get(`${DATA_PIPELINE_URL}/publications`, {
      params: { limit: 200 }
    });

    const publications = response.data.publications || [];
    const graph = buildKnowledgeGraph(publications, 2);

    // Perform clustering
    const clusters = performGraphClustering(graph);

    res.json({
      success: true,
      data: {
        clusters,
        cluster_count: clusters.length,
        clustering_metadata: {
          algorithm: 'community_detection',
          modularity: calculateModularity(clusters, graph),
          generated_at: new Date().toISOString()
        }
      }
    });

  } catch (error) {
    logger.error(`Error clustering knowledge graph: ${error.message}`);
    next(error);
  }
});

// Helper functions for knowledge graph construction
function buildKnowledgeGraph(publications, osdrFiles, depth) {
  const nodes = new Map();
  const edges = [];

  // Add root NASA OSDR node
  const rootNodeId = 'nasa_osdr_root';
  nodes.set(rootNodeId, {
    id: rootNodeId,
    type: 'database',
    label: 'NASA OSDR',
    level: 0,
    properties: {
      description: 'NASA Open Science Data Repository',
      url: 'https://osdr.nasa.gov'
    }
  });

  // Add publication nodes
  publications.forEach(pub => {
    const pubId = `pub_${pub.osdr_id}`;
    nodes.set(pubId, {
      id: pubId,
      type: 'publication',
      label: pub.title.length > 50 ? pub.title.substring(0, 50) + '...' : pub.title,
      level: 1,
      properties: {
        osdr_id: pub.osdr_id,
        title: pub.title,
        research_area: pub.research_area,
        publication_date: pub.publication_date,
        authors: pub.authors,
        abstract: pub.abstract
      }
    });

    // Connect publication to root
    edges.push({
      id: `${rootNodeId}_${pubId}`,
      source: rootNodeId,
      target: pubId,
      type: 'contains',
      weight: 1
    });

    // Add research area nodes
    const areaId = `area_${pub.research_area.replace(/\s+/g, '_')}`;
    if (!nodes.has(areaId)) {
      nodes.set(areaId, {
        id: areaId,
        type: 'research_area',
        label: pub.research_area,
        level: 1,
        properties: {
          area: pub.research_area
        }
      });

      // Connect research area to root
      edges.push({
        id: `${rootNodeId}_${areaId}`,
        source: rootNodeId,
        target: areaId,
        type: 'contains',
        weight: 1
      });
    }

    // Connect publication to research area
    edges.push({
      id: `${pubId}_${areaId}`,
      source: pubId,
      target: areaId,
      type: 'belongs_to',
      weight: 1
    });

    // Add organism nodes
    (pub.organisms || []).forEach(organism => {
      const orgId = `org_${organism.replace(/\s+/g, '_')}`;
      if (!nodes.has(orgId)) {
        nodes.set(orgId, {
          id: orgId,
          type: 'organism',
          label: organism,
          level: 2,
          properties: {
            scientific_name: organism
          }
        });
      }

      // Connect publication to organism
      edges.push({
        id: `${pubId}_${orgId}`,
        source: pubId,
        target: orgId,
        type: 'studies',
        weight: 1
      });
    });

    // Add author nodes
    (pub.authors || []).forEach(author => {
      const authorId = `author_${author.replace(/\s+/g, '_')}`;
      if (!nodes.has(authorId)) {
        nodes.set(authorId, {
          id: authorId,
          type: 'author',
          label: author,
          level: 2,
          properties: {
            name: author
          }
        });
      }

      // Connect author to publication
      edges.push({
        id: `${authorId}_${pubId}`,
        source: authorId,
        target: pubId,
        type: 'authored',
        weight: 1
      });
    });

    // Add keyword nodes
    (pub.keywords || []).forEach(keyword => {
      if (keyword && keyword.length > 2) {
        const keywordId = `keyword_${keyword.replace(/\s+/g, '_')}`;
        if (!nodes.has(keywordId)) {
          nodes.set(keywordId, {
            id: keywordId,
            type: 'keyword',
            label: keyword,
            level: 2,
            properties: {
              keyword
            }
          });
        }

        // Connect publication to keyword
        edges.push({
          id: `${pubId}_${keywordId}`,
          source: pubId,
          target: keywordId,
          type: 'tagged_with',
          weight: 0.5
        });
      }
    });
  });

  // Add OSDR study nodes and their file contents
  const studyFilesMap = {};
  
  // Group files by study ID
  osdrFiles.forEach(file => {
    const studyId = file.study_id;
    if (!studyFilesMap[studyId]) {
      studyFilesMap[studyId] = [];
    }
    studyFilesMap[studyId].push(file);
  });

  // Create study nodes and file sub-nodes
  Object.entries(studyFilesMap).forEach(([studyId, files]) => {
    // Add study node
    const studyNodeId = `study_${studyId}`;
    nodes.set(studyNodeId, {
      id: studyNodeId,
      type: 'study',
      label: studyId,
      level: 1,
      properties: {
        study_id: studyId,
        file_count: files.length,
        species: files[0]?.species || 'Unknown',
        mission: files[0]?.mission || 'Unknown'
      }
    });

    // Connect study to root
    edges.push({
      id: `${rootNodeId}_${studyNodeId}`,
      source: rootNodeId,
      target: studyNodeId,
      type: 'contains',
      weight: 1
    });

    // Add file nodes for each study with hierarchical structure
    files.forEach((file, index) => {
      const fileNodeId = `file_${studyId}_${index}`;
      const fileType = file.type || 'Unknown';
      const fileName = file.name || `File ${index + 1}`;
      
      nodes.set(fileNodeId, {
        id: fileNodeId,
        type: 'file',
        label: fileName.length > 30 ? fileName.substring(0, 30) + '...' : fileName,
        level: 2,
        properties: {
          file_id: file.id,
          name: fileName,
          type: fileType,
          experiment_type: file.experiment_type || 'Unknown',
          date: file.date || 'Unknown',
          size: file.size || 'Unknown',
          url: file.url || '',
          species: file.species || 'Unknown',
          mission: file.mission || 'Unknown'
        }
      });

      // Connect file to study
      edges.push({
        id: `${studyNodeId}_${fileNodeId}`,
        source: studyNodeId,
        target: fileNodeId,
        type: 'contains',
        weight: 0.5
      });
    });
  });

  // Add co-occurrence edges (publications in same research area)
  if (depth >= 2) {
    addCooccurrenceEdges(nodes, edges, publications);
  }

  // Add references between publications and studies if they share the same OSDR ID
  if (depth >= 2) {
    addPublicationStudyReferences(nodes, edges, publications, studyFilesMap);
  }

  return {
    nodes: Array.from(nodes.values()),
    edges
  };
}

function addCooccurrenceEdges(nodes, edges, publications) {
  // Group publications by research area
  const areaGroups = {};
  publications.forEach(pub => {
    const area = pub.research_area;
    if (!areaGroups[area]) areaGroups[area] = [];
    areaGroups[area].push(pub);
  });

  // Add similarity edges between publications in the same area
  Object.values(areaGroups).forEach(group => {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const pub1 = group[i];
        const pub2 = group[j];
        const similarity = calculatePublicationSimilarity(pub1, pub2);
        
        if (similarity > 0.3) {
          edges.push({
            id: `sim_${pub1.osdr_id}_${pub2.osdr_id}`,
            source: `pub_${pub1.osdr_id}`,
            target: `pub_${pub2.osdr_id}`,
            type: 'similar_to',
            weight: similarity
          });
        }
      }
    }
  });
}

function calculatePublicationSimilarity(pub1, pub2) {
  let similarity = 0;
  
  // Same research area
  if (pub1.research_area === pub2.research_area) {
    similarity += 0.3;
  }
  
  // Common keywords
  const keywords1 = new Set(pub1.keywords || []);
  const keywords2 = new Set(pub2.keywords || []);
  const commonKeywords = new Set([...keywords1].filter(k => keywords2.has(k)));
  const totalKeywords = new Set([...keywords1, ...keywords2]);
  
  if (totalKeywords.size > 0) {
    similarity += (commonKeywords.size / totalKeywords.size) * 0.4;
  }
  
  // Common organisms
  const organisms1 = new Set(pub1.organisms || []);
  const organisms2 = new Set(pub2.organisms || []);
  const commonOrganisms = new Set([...organisms1].filter(o => organisms2.has(o)));
  const totalOrganisms = new Set([...organisms1, ...organisms2]);
  
  if (totalOrganisms.size > 0) {
    similarity += (commonOrganisms.size / totalOrganisms.size) * 0.3;
  }
  
  return similarity;
}

function getNodeTypeCounts(nodes) {
  const counts = {};
  nodes.forEach(node => {
    counts[node.type] = (counts[node.type] || 0) + 1;
  });
  return counts;
}

function getEdgeTypeCounts(edges) {
  const counts = {};
  edges.forEach(edge => {
    counts[edge.type] = (counts[edge.type] || 0) + 1;
  });
  return counts;
}

function findNodeInformation(nodeId, publications) {
  // Extract node type from ID
  const [type, ...idParts] = nodeId.split('_');
  const actualId = idParts.join('_');
  
  switch (type) {
    case 'pub':
      const publication = publications.find(pub => pub.osdr_id === actualId);
      return publication ? {
        id: nodeId,
        type: 'publication',
        data: publication,
        connections: findNodeConnections(nodeId, publications)
      } : null;
      
    case 'area':
      const areaName = actualId.replace(/_/g, ' ');
      const areaPubs = publications.filter(pub => pub.research_area === areaName);
      return {
        id: nodeId,
        type: 'research_area',
        data: {
          name: areaName,
          publication_count: areaPubs.length,
          publications: areaPubs.slice(0, 10) // Limit for performance
        }
      };
      
    default:
      return null;
  }
}

function findNodeConnections(nodeId, publications) {
  // This would normally query the graph database
  // For now, return a simple analysis
  return {
    direct_connections: 0,
    connection_types: [],
    strongest_connections: []
  };
}

function searchGraphNodes(nodes, query, nodeTypes) {
  const queryLower = query.toLowerCase();
  
  return nodes.filter(node => {
    // Filter by node type if specified
    if (nodeTypes && nodeTypes.length > 0 && !nodeTypes.includes(node.type)) {
      return false;
    }
    
    // Search in label
    if (node.label.toLowerCase().includes(queryLower)) {
      return true;
    }
    
    // Search in properties
    if (node.properties) {
      return Object.values(node.properties).some(value => 
        typeof value === 'string' && value.toLowerCase().includes(queryLower)
      );
    }
    
    return false;
  });
}

function extractSubgraph(graph, nodes) {
  const nodeIds = new Set(nodes.map(n => n.id));
  const subgraphEdges = graph.edges.filter(edge => 
    nodeIds.has(edge.source) || nodeIds.has(edge.target)
  );
  
  return {
    nodes,
    edges: subgraphEdges
  };
}

function findShortestPaths(graph, fromId, toId, maxLength) {
  // Simple BFS implementation for finding paths
  const adjacencyList = {};
  
  // Build adjacency list
  graph.edges.forEach(edge => {
    if (!adjacencyList[edge.source]) adjacencyList[edge.source] = [];
    if (!adjacencyList[edge.target]) adjacencyList[edge.target] = [];
    adjacencyList[edge.source].push(edge.target);
    adjacencyList[edge.target].push(edge.source);
  });
  
  const paths = [];
  const visited = new Set();
  
  function dfs(current, target, path, depth) {
    if (depth > maxLength) return;
    if (current === target) {
      paths.push([...path]);
      return;
    }
    
    visited.add(current);
    
    (adjacencyList[current] || []).forEach(neighbor => {
      if (!visited.has(neighbor)) {
        path.push(neighbor);
        dfs(neighbor, target, path, depth + 1);
        path.pop();
      }
    });
    
    visited.delete(current);
  }
  
  dfs(fromId, toId, [fromId], 0);
  
  // Sort by length
  return paths.sort((a, b) => a.length - b.length);
}

function performGraphClustering(graph) {
  // Simple clustering based on node types and connections
  const clusters = [];
  const clusteredNodes = new Set();
  
  // Cluster by research areas
  const researchAreas = graph.nodes.filter(n => n.type === 'research_area');
  
  researchAreas.forEach(areaNode => {
    const cluster = {
      id: `cluster_${areaNode.id}`,
      type: 'research_area_cluster',
      center: areaNode,
      nodes: [areaNode],
      size: 1
    };
    
    // Find connected publications
    const connectedPubs = graph.edges
      .filter(e => e.target === areaNode.id && e.type === 'belongs_to')
      .map(e => graph.nodes.find(n => n.id === e.source))
      .filter(n => n);
    
    cluster.nodes.push(...connectedPubs);
    cluster.size = cluster.nodes.length;
    
    connectedPubs.forEach(pub => clusteredNodes.add(pub.id));
    clusteredNodes.add(areaNode.id);
    
    clusters.push(cluster);
  });
  
  return clusters;
}

function calculateModularity(clusters, graph) {
  // Simplified modularity calculation
  const totalEdges = graph.edges.length;
  if (totalEdges === 0) return 0;
  
  let modularity = 0;
  
  clusters.forEach(cluster => {
    const nodeIds = new Set(cluster.nodes.map(n => n.id));
    const internalEdges = graph.edges.filter(e => 
      nodeIds.has(e.source) && nodeIds.has(e.target)
    ).length;
    
    const expectedEdges = (cluster.size * (cluster.size - 1)) / (2 * totalEdges);
    modularity += (internalEdges - expectedEdges) / totalEdges;
  });
  
  return Math.round(modularity * 1000) / 1000;
}

function addPublicationStudyReferences(nodes, edges, publications, studyFilesMap) {
  // Connect publications to studies if they have the same OSDR ID
  publications.forEach(pub => {
    const pubId = `pub_${pub.osdr_id}`;
    const studyId = pub.osdr_id;
    
    // Check if there's a study with the same ID
    if (studyFilesMap[studyId]) {
      const studyNodeId = `study_${studyId}`;
      
      // Only add edge if both nodes exist
      if (nodes.has(pubId) && nodes.has(studyNodeId)) {
        edges.push({
          id: `${pubId}_${studyNodeId}_ref`,
          source: pubId,
          target: studyNodeId,
          type: 'references',
          weight: 1
        });
      }
    }
  });
}

module.exports = router;
