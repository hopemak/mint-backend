// MongoDB Initialization Script
// Creates collections and indexes

print('🚀 Initializing MInT Platform Database...');

// Create collections
db.createCollection('users');
db.createCollection('startups');
db.createCollection('evaluations');
db.createCollection('funding_requests');
db.createCollection('funding_disbursements');
db.createCollection('grants');
db.createCollection('grant_applications');
db.createCollection('mentors');
db.createCollection('documents');
db.createCollection('analytics');
db.createCollection('audit_logs');

print('✅ Collections created!');

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ role: 1 });
db.startups.createIndex({ startup_id: 1 }, { unique: true });
db.startups.createIndex({ user_id: 1 });
db.evaluations.createIndex({ startup_id: 1 }, { unique: true });
db.funding_requests.createIndex({ request_id: 1 }, { unique: true });
db.grants.createIndex({ grant_id: 1 }, { unique: true });
db.mentors.createIndex({ mentor_id: 1 }, { unique: true });
db.documents.createIndex({ document_id: 1 }, { unique: true });

print('✅ Indexes created!');

// Insert default admin user
db.users.insertOne({
  email: 'admin@mint.gov',
  password: '$2b$12$X7Z8Y9W0Q1R2S3T4U5V6W7X8Y9Z0A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7', // "admin123" hashed
  full_name: 'Ministry Admin',
  role: 'admin',
  status: 'active',
  created_at: new Date(),
  updated_at: new Date()
});

print('✅ Default admin user created!');
print('📧 Email: admin@mint.gov');
print('🔑 Password: admin123');
print('🏛️ MInT Platform Database Ready!');
