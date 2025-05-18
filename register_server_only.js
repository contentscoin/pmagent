#!/usr/bin/env node

/**
 * Smithery에 PMAgent 서버만 등록하는 스크립트 (Cursor 통합 없음)
 */

const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');
const os = require('os');

// 설정 파일에서 값 읽기
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const PACKAGE_NAME = config.smithery.packageName;
const SERVER_URL = config.smithery.serverUrl;
const API_KEY = config.smithery.apiKey;

console.log(`
========================================
Smithery 서버 등록 시작 (Cursor 통합 없음)
패키지: ${PACKAGE_NAME}
서버 URL: ${SERVER_URL}
========================================
`);

// Smithery 설정 디렉토리
const homedir = os.homedir();
const SMITHERY_DIR = path.join(homedir, '.smithery');
if (!fs.existsSync(SMITHERY_DIR)) {
  fs.mkdirSync(SMITHERY_DIR, { recursive: true });
}

// 연결 설정 파일 생성
const CONNECTION_FILE = path.join(SMITHERY_DIR, 'connections.json');
let connections = {};

// 기존 설정 파일이 있으면 읽기
if (fs.existsSync(CONNECTION_FILE)) {
  try {
    connections = JSON.parse(fs.readFileSync(CONNECTION_FILE, 'utf8'));
    console.log('기존 연결 설정 파일을 읽었습니다.');
  } catch (e) {
    console.log('기존 연결 설정 파일을 읽을 수 없습니다. 새로 생성합니다.');
  }
}

// 새 서버 설정 추가
connections[PACKAGE_NAME] = {
  "url": SERVER_URL,
  "apiKey": API_KEY
};

// 설정 파일 저장
fs.writeFileSync(
  CONNECTION_FILE,
  JSON.stringify(connections, null, 2),
  'utf8'
);

console.log(`연결 설정 파일 생성/업데이트됨: ${CONNECTION_FILE}`);

// 다양한 설치 방법 시도
const installMethods = [
  { name: "apiKey", cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor` },
  { name: "api-key", cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --api-key "${API_KEY}" --client cursor` },
  { name: "key", cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --key "${API_KEY}" --client cursor` },
  { name: "URL만", cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --client cursor` }
];

// 각 방법을 순차적으로 시도
let success = false;
for (const method of installMethods) {
  console.log(`\n설치 시도 (${method.name})...`);
  console.log(`실행 명령: ${method.cmd}`);
  
  try {
    const output = execSync(method.cmd, { encoding: 'utf8' });
    console.log(output);
    success = true;
    console.log(`✅ ${method.name} 방식으로 설치 성공!`);
    break;
  } catch (error) {
    console.error(`❌ ${method.name} 방식 설치 실패:`);
    if (error.stdout) console.log(error.stdout);
    console.log('다음 방식 시도...');
  }
}

if (success) {
  console.log(`
========================================
Smithery 서버 등록 성공!
Smithery에서 다음 서버를 사용할 수 있습니다:
  패키지: ${PACKAGE_NAME}
  URL: ${SERVER_URL}
========================================
`);

  // 서버 목록 확인
  try {
    console.log('\n등록된 서버 목록:');
    const listOutput = execSync('npx -y @smithery/cli@latest list servers', { encoding: 'utf8' });
    console.log(listOutput);
  } catch (error) {
    console.error('서버 목록 조회 실패:', error.message);
  }
} else {
  console.error('\n❌ 모든 설치 방법이 실패했습니다.');
  console.log('\n수동 설치 방법:');
  console.log('1. 새 터미널 창을 열고 다음 명령을 직접 실행하세요:');
  console.log(`npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor`);
  
  process.exit(1);
} 