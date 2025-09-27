// Test frontend CORS connection
fetch('http://localhost:4004/api/analytics')
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));