#!/usr/bin/env node

/**
 * PMAgent MCP 서버 직접 테스트 클라이언트 (HTTP API)
 * 
 * 이 스크립트는 스미더리 없이 직접 PMAgent MCP 서버의 HTTP API를 호출합니다.
 */

import fetch from 'node-fetch';
import fs from 'fs';

// 서버 URL (Vercel 배포 URL)
const SERVER_URL = "https://pmagent.vercel.app";

// 로그 기록 함수
function log(message) {
  const logMessage = `[${new Date().toISOString()}] ${message}`;
  console.log(logMessage);
  fs.appendFileSync('mcp_test.log', logMessage + '\n');
}

async function main() {
  try {
    log("PMAgent MCP 서버 HTTP API 테스트 클라이언트 시작");
    
    // 1. 서버 정보 확인
    log("서버 정보 확인 중...");
    const infoResponse = await fetch(SERVER_URL);
    const serverInfo = await infoResponse.json();
    log(`서버 정보: ${JSON.stringify(serverInfo)}`);
    
    // 2. 도구 목록 가져오기
    log("\n도구 목록 가져오는 중...");
    const toolsResponse = await fetch(`${SERVER_URL}/tools`);
    if (!toolsResponse.ok) {
      throw new Error(`도구 목록 가져오기 실패: ${toolsResponse.status}`);
    }
    
    const toolsData = await toolsResponse.json();
    const tools = toolsData.tools || [];
    log(`${tools.length}개의 도구를 찾았습니다:`);
    tools.forEach(tool => {
      log(`  - ${tool.name}: ${tool.description || '설명 없음'}`);
    });
    
    // 3. 프로젝트 목록 가져오기
    log("\n프로젝트 목록 가져오는 중...");
    const invokeData = {
      name: "list_projects",
      parameters: {}
    };
    
    const projectsResponse = await fetch(`${SERVER_URL}/invoke`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(invokeData),
    });
    
    if (!projectsResponse.ok) {
      throw new Error(`프로젝트 목록 가져오기 실패: ${projectsResponse.status}`);
    }
    
    const projectsData = await projectsResponse.json();
    log(`프로젝트 목록: ${JSON.stringify(projectsData, null, 2)}`);
    
    // 4. 테스트용 프로젝트 생성
    log("\n테스트 프로젝트 생성 중...");
    const createProjectData = {
      name: "create_project",
      parameters: {
        name: `테스트 프로젝트 ${new Date().toISOString()}`,
        description: "HTTP API 테스트에서 생성된 프로젝트"
      }
    };
    
    const createResponse = await fetch(`${SERVER_URL}/invoke`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(createProjectData),
    });
    
    if (!createResponse.ok) {
      throw new Error(`프로젝트 생성 실패: ${createResponse.status}`);
    }
    
    const createResult = await createResponse.json();
    log(`프로젝트 생성 결과: ${JSON.stringify(createResult, null, 2)}`);
    
    log("\n테스트 완료!");
  } catch (error) {
    log(`오류 발생: ${error.message}`);
    log(`스택: ${error.stack}`);
  }
}

// 스크립트 실행
main(); 