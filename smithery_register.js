#!/usr/bin/env node

/**
 * PMAgent MCP 서버 스미더리 레지스트리 등록 스크립트 (API 키 버전)
 * 
 * 이 스크립트는 PMAgent MCP 서버를 스미더리 레지스트리에 등록합니다.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import https from 'https';

// API 키
const SMITHERY_API_KEY = '1af77da5-658a-404b-bf92-bd2fea377d24';

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

// 스미더리 레지스트리에 API로 직접 등록
function registerToSmithery() {
  const serverInfo = readSmitheryJson();
  
  console.log('스미더리 레지스트리에 등록 중...');
  console.log(`- 서버 이름: ${serverInfo.name}`);
  console.log(`- 서버 버전: ${serverInfo.version}`);
  console.log(`- 서버 URL: ${serverInfo.base_url}`);
  
  // JSON 데이터 준비
  const data = JSON.stringify(serverInfo);
  
  // HTTPS 요청 옵션
  const options = {
    hostname: 'api.smithery.ai',
    port: 443,
    path: '/api/register',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${SMITHERY_API_KEY}`,
      'Content-Length': data.length
    }
  };
  
  // HTTPS 요청
  const req = https.request(options, (res) => {
    console.log(`상태 코드: ${res.statusCode}`);
    
    let responseData = '';
    
    res.on('data', (chunk) => {
      responseData += chunk;
    });
    
    res.on('end', () => {
      if (res.statusCode === 200 || res.statusCode === 201) {
        console.log('스미더리 레지스트리 등록 성공!');
        try {
          const result = JSON.parse(responseData);
          console.log('등록 결과:', result);
          console.log('이제 다음 명령어로 스미더리에 MCP 서버를 추가할 수 있습니다:');
          console.log(`mcp_toolbox_add_server qualifiedName="${serverInfo.name}"`);
        } catch (e) {
          console.log('응답:', responseData);
        }
      } else {
        console.error('스미더리 등록 오류:');
        console.error(responseData);
      }
    });
  });
  
  req.on('error', (e) => {
    console.error(`스미더리 등록 중 문제 발생: ${e.message}`);
  });
  
  // 요청 데이터 전송
  req.write(data);
  req.end();
}

// 메인 함수
function main() {
  console.log('PMAgent MCP 서버 스미더리 레지스트리 등록 시작 (API 키 버전)');
  registerToSmithery();
}

// 스크립트 실행
main(); 