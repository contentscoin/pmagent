#!/usr/bin/env node

/**
 * PMAgent를 스미더리에 등록하는 통합 스크립트
 * register_smithery.sh, reinstall_smithery.sh, register_smithery.js를 통합한 버전
 */

import fs from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

// ES 모듈에서 __dirname 구현
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 설정 파일 위치
const configJsonPath = path.join(__dirname, 'config.json');
const smitheryJsonPath = path.join(__dirname, 'smithery-simple.json');

// 설정 파일 읽기
const config = JSON.parse(fs.readFileSync(configJsonPath, 'utf8'));
const smitheryJson = JSON.parse(fs.readFileSync(smitheryJsonPath, 'utf8'));

// 기본 설정값
const PACKAGE_NAME = smitheryJson.qualifiedName;
const SERVER_URL = config.mcpUrl || smitheryJson.baseUrl + smitheryJson.endpoints.production;
const API_KEY = config.apiKey || smitheryJson.apiKey;

// 명령행 인자 처리
const args = process.argv.slice(2);
const isReinstall = args.includes('--reinstall');
const isLocal = args.includes('--local');
const isHelp = args.includes('--help') || args.includes('-h');
const skipCursor = args.includes('--skip-cursor');

// 도움말 출력
if (isHelp) {
  console.log(`
PMAgent Smithery 등록 스크립트 사용법:
  node register_smithery.js [options]

옵션:
  --reinstall        기존 설치를 제거하고 다시 설치합니다.
  --local            로컬 서버를 사용합니다.
  --skip-cursor      Cursor 설정 파일 생성을 건너뜁니다.
  --help, -h         이 도움말을 표시합니다.
  `);
  process.exit(0);
}

// 로컬 모드 설정
if (isLocal) {
  console.log('로컬 서버 모드로 설정합니다...');
  smitheryJson.baseUrl = config.localUrl || "http://localhost:4000/api/mcp";
  fs.writeFileSync(smitheryJsonPath, JSON.stringify(smitheryJson, null, 2), 'utf8');
}

// 설정 표시
console.log('스미더리 설정:');
console.log(`- 패키지 이름: ${PACKAGE_NAME}`);
console.log(`- 서버 URL: ${SERVER_URL}`);
console.log(`- API 키: ${API_KEY.substring(0, 8)}...`);

// 재설치 모드
if (isReinstall) {
  console.log('기존 PMAgent 서버 제거 중...');
  try {
    execSync(`npx -y @smithery/cli@latest uninstall ${PACKAGE_NAME} --client cursor`, { stdio: 'inherit' });
    console.log('기존 설치가 제거되었습니다.');
  } catch (error) {
    console.warn('제거 중 오류가 발생했지만 계속 진행합니다:', error.message);
  }
}

// Cursor 설정 파일 생성
if (!skipCursor) {
  // Cursor 설정 디렉토리 확인
  const homedir = os.homedir();
  const CURSOR_DIR = path.join(homedir, 'Library/Application Support/Cursor');
  const CURSOR_SMITHERY_DIR = path.join(CURSOR_DIR, 'smithery');

  console.log('1. Cursor 설정 디렉토리 확인...');
  if (fs.existsSync(CURSOR_DIR)) {
    console.log(`   Cursor 디렉토리 존재: ${CURSOR_DIR}`);
    
    if (!fs.existsSync(CURSOR_SMITHERY_DIR)) {
      fs.mkdirSync(CURSOR_SMITHERY_DIR, { recursive: true });
    }
    console.log(`   Smithery 디렉토리 생성: ${CURSOR_SMITHERY_DIR}`);
    
    // Cursor Smithery 설정 파일 생성
    const serversContent = {
      servers: {
        [PACKAGE_NAME]: {
          url: SERVER_URL,
          apiKey: API_KEY
        }
      }
    };
    
    fs.writeFileSync(
      path.join(CURSOR_SMITHERY_DIR, 'servers.json'), 
      JSON.stringify(serversContent, null, 2), 
      'utf8'
    );
    console.log('   설정 파일 생성됨:', path.join(CURSOR_SMITHERY_DIR, 'servers.json'));
    
    // Cursor의 확장 설정 확인
    const EXTENSIONS_FILE = path.join(CURSOR_DIR, 'extensions.json');
    if (fs.existsSync(EXTENSIONS_FILE)) {
      console.log('   확장 설정 파일 존재:', EXTENSIONS_FILE);
      // 백업 생성
      fs.copyFileSync(EXTENSIONS_FILE, `${EXTENSIONS_FILE}.bak`);
      console.log('   백업 생성됨:', `${EXTENSIONS_FILE}.bak`);
      
      console.log('   확장 설정 수정은 수동으로 진행해야 합니다.');
      console.log(`   ${EXTENSIONS_FILE} 파일에 다음 정보를 추가하세요:`);
      console.log(`   {
      "smitheryServers": {
        "${PACKAGE_NAME}": {
          "url": "${SERVER_URL}",
          "apiKey": "${API_KEY}"
        }
      }
    }`);
    } else {
      console.log('   확장 설정 파일이 존재하지 않습니다.');
    }
  } else {
    console.log('   Cursor 디렉토리가 존재하지 않습니다. 다른 방법을 시도합니다.');
  }

  // Smithery CLI 설정 생성
  console.log('2. Smithery CLI 설정 생성...');
  const SMITHERY_DIR = path.join(homedir, '.smithery');
  
  if (!fs.existsSync(SMITHERY_DIR)) {
    fs.mkdirSync(SMITHERY_DIR, { recursive: true });
  }
  
  // 다양한 형식의 설정 파일 생성
  // 형식 1: cursor.json
  fs.writeFileSync(
    path.join(SMITHERY_DIR, 'cursor.json'),
    JSON.stringify({
      connections: {
        [PACKAGE_NAME]: {
          url: SERVER_URL,
          apiKey: API_KEY
        }
      }
    }, null, 2),
    'utf8'
  );
  
  // 형식 2: clients/cursor.json
  const clientsDir = path.join(SMITHERY_DIR, 'clients');
  if (!fs.existsSync(clientsDir)) {
    fs.mkdirSync(clientsDir, { recursive: true });
  }
  
  fs.writeFileSync(
    path.join(clientsDir, 'cursor.json'),
    JSON.stringify({
      servers: {
        [PACKAGE_NAME]: {
          url: SERVER_URL,
          apiKey: API_KEY
        }
      }
    }, null, 2),
    'utf8'
  );
  
  // 형식 3: config.json
  fs.writeFileSync(
    path.join(SMITHERY_DIR, 'config.json'),
    JSON.stringify({
      cursor: {
        servers: {
          [PACKAGE_NAME]: {
            url: SERVER_URL,
            apiKey: API_KEY
          }
        }
      }
    }, null, 2),
    'utf8'
  );
  
  console.log('   설정 파일들이 생성되었습니다:');
  console.log(`   - ${path.join(SMITHERY_DIR, 'cursor.json')}`);
  console.log(`   - ${path.join(clientsDir, 'cursor.json')}`);
  console.log(`   - ${path.join(SMITHERY_DIR, 'config.json')}`);
}

// API 엔드포인트 테스트
try {
  console.log('3. API 엔드포인트 테스트...');
  const curlCmd = `curl -s -X POST "${smitheryJson.baseUrl}${smitheryJson.transport.jsonrpc.endpoint || ''}" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"rpc.discover","params":[],"id":1}'`;
  console.log(`   테스트 명령: ${curlCmd}`);
  const curlOutput = execSync(curlCmd, { encoding: 'utf8' });
  console.log('   API 응답:', curlOutput.substring(0, 100) + '...');
} catch (error) {
  console.error('   API 테스트 오류:', error.message);
  console.log('   API 테스트가 실패했지만 등록을 계속 진행합니다.');
}

// Smithery CLI로 등록
try {
  console.log('4. Smithery 서버 등록 중...');
  const command = `npx -y @smithery/cli@latest install ${PACKAGE_NAME} --client cursor`;
  
  console.log(`   실행 명령: ${command}`);
  const output = execSync(command, { encoding: 'utf8' });
  
  console.log('   등록 성공:');
  console.log('   ' + output.replace(/\n/g, '\n   '));
  
  // 등록 확인
  console.log('5. 등록된 서버 목록 확인:');
  const listOutput = execSync('npx -y @smithery/cli@latest list servers --client cursor', { encoding: 'utf8' });
  console.log('   ' + listOutput.replace(/\n/g, '\n   '));
  
  console.log('\n모든 과정이 완료되었습니다. Cursor를 재시작하여 설정을 적용하세요.');
} catch (error) {
  console.error('오류 발생:', error.message);
  if (error.stdout) console.error('출력:', error.stdout);
  if (error.stderr) console.error('오류 출력:', error.stderr);
  
  console.error('등록에 실패했습니다. 다음 사항을 확인하세요:');
  console.error('1. 인터넷 연결 상태');
  console.error('2. API 서버 작동 여부');
  console.error('3. Node.js 및 npm 설치 상태');
  
  process.exit(1);
}
