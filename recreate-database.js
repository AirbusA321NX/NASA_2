const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

async function recreateDatabase() {
  // Connect to PostgreSQL default database
  const client = new Client({
    host: 'localhost',
    port: 5432,
    user: 'postgres',
    password: '1234',
    database: 'postgres' // Connect to default postgres database
  });

  try {
    await client.connect();
    console.log('Connected to PostgreSQL');

    // Drop database if exists
    try {
      await client.query('DROP DATABASE IF EXISTS nasa_biology');
      console.log('Dropped existing nasa_biology database');
    } catch (dropError) {
      console.log('Database drop failed (may not exist):', dropError.message);
    }

    // Create new database
    await client.query('CREATE DATABASE nasa_biology');
    console.log('Created nasa_biology database');

    await client.end();

    // Connect to the new database
    const newClient = new Client({
      host: 'localhost',
      port: 5432,
      user: 'postgres',
      password: '1234',
      database: 'nasa_biology'
    });

    await newClient.connect();
    console.log('Connected to nasa_biology database');

    // Read and execute schema
    const schemaPath = path.join(__dirname, '..', 'backend', 'src', 'database', 'schema_simple.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');
    
    // Split schema into individual statements and execute them
    const statements = schema.split(';').filter(stmt => stmt.trim().length > 0);
    
    for (const statement of statements) {
      if (statement.trim().length > 0) {
        try {
          await newClient.query(statement);
          console.log('Executed statement');
        } catch (error) {
          console.log('Statement execution warning:', error.message);
        }
      }
    }

    console.log('Database schema applied successfully');
    await newClient.end();

  } catch (error) {
    console.error('Error:', error.message);
  }
}

recreateDatabase();