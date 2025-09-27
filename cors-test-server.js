const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3002;

// Enable CORS for all origins
app.use(cors());

app.get('/test-connection', (req, res) => {
  res.json({ 
    success: true, 
    message: 'CORS test successful',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`CORS test server running on port ${PORT}`);
});