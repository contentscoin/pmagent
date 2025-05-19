#!/usr/bin/env node

/**
 * Smithery 서버 직접 등록 스크립트
 * - API 키와 URL을 환경 변수로 직접 전달
 */

const { execSync } = require('child_process');

// 설정 값
const PACKAGE_NAME = "@contentscoin/pmagent";
const SERVER_URL = "https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp";
const API_KEY = "8220ee20-fe17-464b-b658-35113b05be41";
const CLIENT = "cursor";

console.log(`
========================================
Smithery 서버 직접 등록 시도
패키지: ${PACKAGE_NAME}
서버 URL: ${SERVER_URL}
클라이언트: ${CLIENT}
========================================
`);

// 다양한 설치 방법 시도
const installMethods = [
  { 
    name: "verbose 사용", 
    cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --url "${SERVER_URL}" --apiKey "${API_KEY}" --client ${CLIENT} --verbose`
  },
  { 
    name: "패키지명만 사용", 
    cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --client ${CLIENT}`
  },
  { 
    name: "환경 변수 사용",
    env: { SMITHERY_API_KEY: API_KEY, SMITHERY_URL: SERVER_URL },
    cmd: `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --client ${CLIENT}`
  }
];

// 각 방법을 순차적으로 시도
let success = false;
for (const method of installMethods) {
  console.log(`\n설치 시도 (${method.name})...`);
  console.log(`실행 명령: ${method.cmd}`);
  
  try {
    const options = { 
      encoding: 'utf8',
      stdio: 'inherit'
    };
    
    // 환경 변수가 있으면 추가
    if (method.env) {
      options.env = { ...process.env, ...method.env };
      console.log(`환경 변수: ${JSON.stringify(method.env)}`);
    }
    
    execSync(method.cmd, options);
    success = true;
    console.log(`✅ ${method.name} 방식으로 설치 성공!`);
    break;
  } catch (error) {
    console.error(`❌ ${method.name} 방식 설치 실패:`);
    console.log('다음 방식 시도...');
  }
}

if (success) {
  console.log(`
========================================
Smithery 서버 등록 성공!
========================================
`);
} else {
  console.error(`
========================================
모든 설치 방법이 실패했습니다.

다음 단계로 시도해보세요:
1. Smithery CLI 문서 확인: https://docs.smithery.ai/
2. Smithery GitHub 이슈 확인: https://github.com/smithery-io/cli/issues
3. 관리자 권한으로 터미널을 실행하여 다시 시도
========================================
`);
} 