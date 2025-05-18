#!/usr/bin/env node

/**
 * PMAgent 스미더리 간단 등록 스크립트 - 초간단 버전
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

console.log(`스미더리 설치 시작 - 패키지: ${PACKAGE_NAME}, URL: ${SERVER_URL}`);

// 홈 디렉토리
const homedir = os.homedir();

// 스미더리 설정 디렉토리
const SMITHERY_DIR = path.join(homedir, '.smithery');
if (!fs.existsSync(SMITHERY_DIR)) {
  fs.mkdirSync(SMITHERY_DIR, { recursive: true });
}

// 연결 설정 파일 생성
const CONNECTION_FILE = path.join(SMITHERY_DIR, 'connections.json');
fs.writeFileSync(
  CONNECTION_FILE,
  JSON.stringify({
    [PACKAGE_NAME]: {
      "url": SERVER_URL,
      "apiKey": API_KEY
    }
  }, null, 2),
  'utf8'
);

console.log(`연결 설정 파일 생성됨: ${CONNECTION_FILE}`);

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
  console.log(`실행 명령: ${method.cmd}`);
  try {
    const output = execSync(method.cmd, { encoding: 'utf8' });
    console.log(output);
    success = true;
    console.log(`✅ ${method.name} 방식으로 설치 성공!`);
    break;
  } catch (error) {
    console.error(`설치 오류: ${error.message}`);
    if (error.stdout) console.log('오류 출력:', error.stdout);
  }
}

if (!success) {
  console.log('\n대체 설치 방법:');
  console.log('1. 새 터미널 창을 열고 다음 명령을 실행하세요:');
  console.log(`npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor`);
  
  // 수동 설치 명령어 파일 생성
  const manualCmds = installMethods.map(m => m.cmd).join('\n\n');
  fs.writeFileSync('smithery_manual_install_commands.txt', manualCmds, 'utf8');
  console.log('\n모든 설치 명령이 smithery_manual_install_commands.txt 파일에 저장되었습니다.');
  
  process.exit(1);
} 