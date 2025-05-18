#!/usr/bin/env node

/**
 * PMAgent 스미더리 간단 등록 스크립트
 * 최소한의 필수 기능만 구현한 버전
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

// 필수 설정값
const PACKAGE_NAME = "@contentscoin/pmagent";
const SERVER_URL = "https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp";
const API_KEY = "0c8f6386-e443-4b8b-95ba-22a40d5f5e38";

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

// 스미더리 설치 실행
try {
  // 명시적 API 키와 URL 사용
  const command = `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor`;
  console.log(`실행 명령: ${command}`);
  
  // 명령 실행
  console.log('스미더리 서버 등록 중...');
  const output = execSync(command, { encoding: 'utf8' });
  console.log('등록 결과:', output);
  
  // 성공 메시지
  console.log('설치 완료! Cursor를 재시작하여 변경사항을 적용하세요.');
} catch (error) {
  console.error('설치 오류:', error.message);
  
  if (error.stdout) console.log('명령 출력:', error.stdout);
  if (error.stderr) console.log('오류 출력:', error.stderr);
  
  console.log('\n대체 설치 명령을 시도합니다...');
  try {
    // api-key 형식으로 시도
    const altCommand = `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --api-key "${API_KEY}" --client cursor`;
    console.log(`실행 명령: ${altCommand}`);
    
    const altOutput = execSync(altCommand, { encoding: 'utf8' });
    console.log('등록 결과:', altOutput);
    console.log('설치 완료! Cursor를 재시작하여 변경사항을 적용하세요.');
  } catch (altError) {
    console.error('대체 설치도 실패했습니다. 수동 설치가 필요합니다.');
    console.log('\n수동 설치 방법:');
    console.log('1. 새 터미널 창을 열고 다음 명령을 실행하세요:');
    console.log(`npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client cursor`);
    process.exit(1);
  }
} 