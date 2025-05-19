#!/usr/bin/env node

/**
 * Smithery 연결 설정 파일 생성 스크립트
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// 설정 값 지정
const PACKAGE_NAME = "@contentscoin/pmagent";
const SERVER_URL = "https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp";
const API_KEY = "8220ee20-fe17-464b-b658-35113b05be41";

// Smithery 디렉토리
const homedir = os.homedir();
const SMITHERY_DIR = path.join(homedir, '.smithery');

// 디렉토리 생성 (없는 경우)
if (!fs.existsSync(SMITHERY_DIR)) {
  fs.mkdirSync(SMITHERY_DIR, { recursive: true });
  console.log(`Smithery 디렉토리 생성됨: ${SMITHERY_DIR}`);
} else {
  console.log(`Smithery 디렉토리 이미 존재함: ${SMITHERY_DIR}`);
}

// 연결 설정 파일 경로
const CONNECTION_FILE = path.join(SMITHERY_DIR, 'connections.json');

// 연결 설정
const connection = {
  [PACKAGE_NAME]: {
    url: SERVER_URL,
    apiKey: API_KEY
  }
};

// 기존 파일이 있으면 병합
let finalConnection = connection;
if (fs.existsSync(CONNECTION_FILE)) {
  try {
    const existingContent = fs.readFileSync(CONNECTION_FILE, 'utf8');
    const existingConnections = JSON.parse(existingContent);
    finalConnection = { ...existingConnections, ...connection };
    console.log('기존 연결 설정에 새 설정 병합');
  } catch (e) {
    console.log('기존 연결 파일 읽기 실패, 새로 생성합니다:', e.message);
  }
}

// 파일 쓰기
fs.writeFileSync(
  CONNECTION_FILE,
  JSON.stringify(finalConnection, null, 2),
  'utf8'
);

console.log(`
========================================
Smithery 연결 설정 파일 생성 완료!
파일 경로: ${CONNECTION_FILE}

내용:
${JSON.stringify(finalConnection, null, 2)}
========================================
`);

// 파일 권한 확인
try {
  const stats = fs.statSync(CONNECTION_FILE);
  console.log(`파일 권한: ${stats.mode.toString(8)}`);
  console.log(`소유자: ${stats.uid}, 그룹: ${stats.gid}`);
} catch (e) {
  console.error('파일 정보 확인 실패:', e.message);
}

// 설치 명령어 안내
console.log(`
다음 명령어로 Smithery에 서버 등록을 시도하세요:

npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor
`); 