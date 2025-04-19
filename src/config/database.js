import mongoose from 'mongoose';
import dotenv from 'dotenv';

dotenv.config();

// MongoDB 연결 URI (환경 변수에서 가져오거나 기본값 사용)
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/pmagent-db';

// 데이터베이스 연결 함수
export async function connectDatabase() {
  try {
    await mongoose.connect(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log('🔌 MongoDB 데이터베이스에 성공적으로 연결되었습니다.');
    return mongoose.connection;
  } catch (error) {
    console.error('❌ MongoDB 연결 오류:', error.message);
    process.exit(1);
  }
}

// 연결 종료 함수
export async function disconnectDatabase() {
  try {
    await mongoose.disconnect();
    console.log('📴 MongoDB 데이터베이스 연결이 종료되었습니다.');
  } catch (error) {
    console.error('❌ MongoDB 연결 종료 오류:', error.message);
  }
}

export default {
  connectDatabase,
  disconnectDatabase,
}; 