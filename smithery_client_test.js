#!/usr/bin/env node

/**
 * PMAgent MCP 서버 테스트 클라이언트
 * 
 * 이 스크립트는 스미더리를 통해 PMAgent MCP 서버에 연결하고 사용 가능한 도구를 확인합니다.
 */

import { createTransport } from "@smithery/sdk/transport.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import WebSocket from 'ws';

// Node.js 환경에서 WebSocket 전역 객체 설정
global.WebSocket = WebSocket;

// 스미더리 API 키
const SMITHERY_API_KEY = "1af77da5-658a-404b-bf92-bd2fea377d24";

async function main() {
  try {
    console.log("PMAgent MCP 서버 테스트 클라이언트 시작");
    
    // 스미더리 트랜스포트 생성
    console.log("스미더리 트랜스포트 생성 중...");
    const transport = createTransport(
      "https://server.smithery.ai/@contentscoin/pmagent/ws", 
      SMITHERY_API_KEY
    );
    
    // MCP 클라이언트 생성
    console.log("MCP 클라이언트 생성 중...");
    const client = new Client({
      name: "PMAgent Test Client",
      version: "1.0.0"
    });
    
    // 서버에 연결
    console.log("서버에 연결 중...");
    await client.connect(transport);
    console.log("서버에 연결됨!");
    
    // 사용 가능한 도구 목록 가져오기
    console.log("사용 가능한 도구 목록 가져오는 중...");
    const tools = await client.listTools();
    console.log(`사용 가능한 도구: ${tools.map(t => t.name).join(", ")}`);
    
    // 프로젝트 목록 가져오기 예제
    console.log("\n프로젝트 목록 가져오기 테스트:");
    const projectsResult = await client.callTool("list_projects", {});
    console.log("프로젝트 목록:", projectsResult);
    
    // 연결 종료
    console.log("\n연결 종료 중...");
    await client.disconnect();
    console.log("연결 종료됨!");
    
  } catch (error) {
    console.error("오류 발생:", error);
  }
}

// 스크립트 실행
main(); 