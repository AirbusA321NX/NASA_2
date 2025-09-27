// Test frontend API connection
async function testAPIConnection() {
  try {
    console.log('Testing API connection...');
    
    // Test analytics endpoint
    const analyticsResponse = await fetch('http://localhost:4004/api/analytics?period=all_time');
    console.log('Analytics response status:', analyticsResponse.status);
    const analyticsData = await analyticsResponse.json();
    console.log('Analytics data:', JSON.stringify(analyticsData, null, 2));
    
    // Test publications endpoint
    const pubsResponse = await fetch('http://localhost:4004/api/publications?limit=5');
    console.log('Publications response status:', pubsResponse.status);
    const pubsData = await pubsResponse.json();
    console.log('Publications data:', JSON.stringify(pubsData, null, 2));
    
  } catch (error) {
    console.error('API connection test failed:', error);
  }
}

testAPIConnection();