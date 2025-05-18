#!/usr/bin/env node

/**
 * PMAgent MCP 서버 테스트 클라이언트 (HTTP API)
 * 
 * 이 스크립트는 스미더리 없이 직접 PMAgent MCP 서버의 HTTP API를 호출합니다.
 * JavaScript 환경에서 MCP 서버 접근 및 테스트를 위한 표준 도구입니다.
 */

import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES 모듈에서 __dirname 구현
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 설정 파일 로드
const configPath = path.join(__dirname, 'config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// 서버 URL (통합된 config.json에서 가져옴)
const SERVER_URL = process.argv.includes('--local') 
  ? config.localUrl 
  : (config.client?.server?.url || "https://pmagent.vercel.app/api");

// 로그 파일 설정
const LOG_FILE = 'mcp_test.log';

// 로그 기록 함수
function log(message) {
  const logMessage = `[${new Date().toISOString()}] ${message}`;
  console.log(logMessage);
  fs.appendFileSync(LOG_FILE, logMessage + '\n');
}

async function main() {
  try {
    log("PMAgent MCP 서버 HTTP API 테스트 클라이언트 시작");
    log(`서버 URL: ${SERVER_URL}`);
    
    // 1. 서버 정보 확인
    log("\n서버 정보 확인 중...");
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
    
    // 5. 테스트용 태스크 생성 (프로젝트가 성공적으로 생성된 경우)
    if (createResult && createResult.project && createResult.project.id) {
      log("\n프로젝트에 테스트 태스크 생성 중...");
      const projectId = createResult.project.id;
      
      const createTaskData = {
        name: "create_task",
        parameters: {
          project_id: projectId,
          name: `테스트 태스크 ${new Date().toISOString()}`,
          description: "MCP 클라이언트에서 생성된 테스트 태스크",
          status: "TODO",
          assignee: "테스터"
        }
      };
      
      const taskResponse = await fetch(`${SERVER_URL}/invoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createTaskData),
      });
      
      if (taskResponse.ok) {
        const taskResult = await taskResponse.json();
        log(`태스크 생성 결과: ${JSON.stringify(taskResult, null, 2)}`);
      } else {
        log(`태스크 생성 실패: ${taskResponse.status}`);
      }
    }
    
    log("\n테스트 완료!");
  } catch (error) {
    log(`오류 발생: ${error.message}`);
    if (error.stack) {
      log(`스택: ${error.stack}`);
    }
  }
}

// 스크립트가 직접 실행되었을 때만 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

// 다른 모듈에서 사용할 수 있도록 함수 내보내기
export { main as testMcpServer }; 