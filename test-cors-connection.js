// Test CORS connection from browser context
const testCORS = async () => {
  try {
    console.log('Testing CORS connection to backend...');
    const response = await fetch('http://localhost:4004/api/analytics');
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Success:', data);
  } catch (error) {
    console.error('CORS Error:', error);
  }
};

testCORS();