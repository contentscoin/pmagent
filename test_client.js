// MCP 서버 테스트 클라이언트
import fetch from 'node-fetch';

// MCP 서버 URL
const MCP_SERVER_URL = 'https://pmagent-jakes-projects-0ab50f91.vercel.app/api/jsonrpc';

// JSON-RPC 요청 함수
async function jsonRpcRequest(method, params = {}) {
  const response = await fetch(MCP_SERVER_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params,
    }),
  });

  const data = await response.json();
  return data;
}

// MCP 서버 정보 가져오기
async function getServerInfo() {
  console.log('서버 정보 요청 중...');
  const response = await jsonRpcRequest('initialize');
  console.log('서버 정보:', response);
  return response;
}

// 도구 목록 가져오기
async function getToolsList() {
  console.log('도구 목록 요청 중...');
  const response = await jsonRpcRequest('tools/list');
  console.log('도구 목록:', response);
  return response;
}

// 특정 도구 호출하기
async function callTool(toolName, parameters) {
  console.log(`'${toolName}' 도구 호출 중...`);
  const response = await jsonRpcRequest('tools/call', {
    tool: toolName,
    parameters,
  });
  console.log(`'${toolName}' 응답:`, response);
  return response;
}

// 테스트 실행
async function runTests() {
  try {
    // 1. 서버 정보 확인
    await getServerInfo();
    
    // 2. 도구 목록 확인
    await getToolsList();
    
    // 3. create_project 도구 테스트
    await callTool('create_project', {
      name: '테스트 프로젝트',
      description: 'MCP 클라이언트 테스트를 위한 프로젝트',
    });
    
    // 4. get_project_status 도구 테스트
    await callTool('get_project_status', {
      projectId: 'proj-test',
    });
    
    // 5. assign_task 도구 테스트
    await callTool('assign_task', {
      taskId: 'task-1',
      agentType: 'designer',
    });
    
    console.log('테스트 완료!');
  } catch (error) {
    console.error('테스트 실패:', error);
  }
}

// 테스트 실행
runTests(); 