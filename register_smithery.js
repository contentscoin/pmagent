#!/usr/bin/env node

/**
 * PMAgent를 스미더리에 등록하는 스크립트
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

// ES 모듈에서 __dirname 구현
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 스미더리 JSON 파일 위치
const smitheryJsonPath = path.join(__dirname, 'smithery-simple.json');

// 기존 JSON 파일 읽기
let smitheryJson = JSON.parse(fs.readFileSync(smitheryJsonPath, 'utf8'));

// baseUrl 업데이트
smitheryJson.baseUrl = "https://pmagent-k5dwxsuwl-jakes-projects-0ab50f91.vercel.app";

// 업데이트된 JSON 파일 저장
fs.writeFileSync(smitheryJsonPath, JSON.stringify(smitheryJson, null, 2), 'utf8');

console.log('스미더리 JSON 파일 업데이트 완료!');
console.log('새 baseUrl:', smitheryJson.baseUrl);

console.log(`PMAgent 스미더리 등록 시작`);
console.log(`서버 URL: ${smitheryJson.baseUrl}`);
console.log(`JSON-RPC 엔드포인트: ${smitheryJson.transport.jsonrpc.endpoint}`);

try {
  // 스미더리 CLI 사용하여 등록
  const command = `npx @smithery/cli register --name ${smitheryJson.qualifiedName} --url ${smitheryJson.baseUrl} --version ${smitheryJson.version} --client cursor`;
  
  console.log(`실행 명령: ${command}`);
  const output = execSync(command, { encoding: 'utf8' });
  
  console.log('등록 성공:');
  console.log(output);
  
  // 등록 확인
  console.log('등록된 서버 목록:');
  const listOutput = execSync('npx @smithery/cli list --client cursor', { encoding: 'utf8' });
  console.log(listOutput);
  
} catch (error) {
  console.error('오류 발생:', error.message);
  if (error.stdout) console.error('출력:', error.stdout);
  if (error.stderr) console.error('오류 출력:', error.stderr);
} 