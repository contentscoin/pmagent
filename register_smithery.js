#!/usr/bin/env node

/**
 * PMAgent MCP 서버 스미더리 레지스트리 등록 스크립트
 * 
 * 이 스크립트는 PMAgent MCP 서버를 스미더리 레지스트리에 등록합니다.
 * 
 * 사용법:
 * 1. npm install -g smithery-cli
 * 2. node register_smithery.js
 */

import fs from 'fs';
import { exec } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

// __dirname 대응값 생성 (ES 모듈에서는 __dirname이 없음)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// smithery.json 파일 경로
const smitheryJsonPath = path.join(__dirname, 'smithery.json');

// smithery.json 파일 읽기
function readSmitheryJson() {
  try {
    const data = fs.readFileSync(smitheryJsonPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('smithery.json 파일을 읽을 수 없습니다:', error);
    process.exit(1);
  }
}

// 스미더리 레지스트리에 등록
function registerToSmithery() {
  const serverInfo = readSmitheryJson();
  
  console.log('스미더리 레지스트리에 등록 중...');
  console.log(`- 서버 이름: ${serverInfo.displayName}`);
  console.log(`- 서버 버전: ${serverInfo.version}`);
  console.log(`- 서버 URL: ${serverInfo.baseUrl}`);
  
  // Smithery CLI 명령 실행
  const command = `smithery register --file "${smitheryJsonPath}"`;
  
  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`스미더리 등록 오류: ${error.message}`);
      return;
    }
    
    if (stderr) {
      console.error(`스미더리 등록 오류: ${stderr}`);
      return;
    }
    
    console.log('스미더리 레지스트리 등록 결과:');
    console.log(stdout);
    
    console.log('등록 완료! 이제 다음 명령어로 스미더리에 MCP 서버를 추가할 수 있습니다:');
    console.log(`mcp_toolbox_add_server qualifiedName="${serverInfo.qualifiedName}"`);
  });
}

// 메인 함수
function main() {
  console.log('PMAgent MCP 서버 스미더리 레지스트리 등록 시작');
  registerToSmithery();
}

// 스크립트 실행
main(); 