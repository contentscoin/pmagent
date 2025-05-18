#!/usr/bin/env node

/**
 * MCP 서버 RPC 엔드포인트 테스트 스크립트 - CommonJS 형식
 */

const fetch = require('node-fetch');

const SERVER_URL = "https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp";

async function testRpcDiscover() {
  console.log(`테스트 시작: ${SERVER_URL}`);
  
  const payload = {
    jsonrpc: "2.0",
    method: "rpc.discover",
    params: [],
    id: 1
  };
  
  try {
    const response = await fetch(SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    const data = await response.json();
    console.log("응답:", JSON.stringify(data, null, 2));
    
    // Smithery에 필요한 필드가 있는지 확인
    if (data.result && data.result.transport && data.result.transport.methods) {
      console.log("✅ rpc.discover 메서드가 정상 작동합니다!");
    } else {
      console.log("❌ rpc.discover 메서드가 올바른 정보를 반환하지 않습니다.");
    }
  } catch (error) {
    console.error("오류 발생:", error);
  }
}

// GET 요청으로 서버 상태 확인
async function testGetEndpoint() {
  try {
    const response = await fetch(SERVER_URL, {
      method: 'GET'
    });
    
    const data = await response.text();
    console.log("GET 요청 응답:", data);
  } catch (error) {
    console.error("GET 요청 오류:", error);
  }
}

// 메인 실행
async function main() {
  await testGetEndpoint();
  await testRpcDiscover();
}

main().catch(console.error); 