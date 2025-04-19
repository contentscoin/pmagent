/**
 * 에이전트 클라이언트 테스트 파일
 */

const AgentClient = require('./agent_client');

// 환경 변수 설정 (실제 사용 시 .env 파일이나 환경 설정에서 관리)
process.env.OPENAI_API_KEY = 'your_openai_api_key_here';

// 클라이언트 인스턴스 생성
const agentClient = new AgentClient({
  // 가상 환경 경로 설정 (필요한 경우)
  // pythonPath: '/path/to/venv/bin/python',
  
  // 추가 환경 변수 설정
  env: {
    // API 키 등 환경 변수 추가 가능
  }
});

// 에이전트 테스트 함수
async function testAgents() {
  try {
    // 백엔드 에이전트 테스트
    console.log('=== 백엔드 에이전트 테스트 ===');
    const backendResult = await agentClient.runBackendAgent('Create a RESTful API endpoint for user registration');
    console.log('백엔드 결과:', backendResult);
    console.log();
    
    // AI 엔지니어 에이전트 테스트 (API 키 필요)
    console.log('=== AI 엔지니어 에이전트 테스트 ===');
    try {
      const aiResult = await agentClient.runAIEngineerAgent('Implement a sentiment analysis service');
      console.log('AI 엔지니어 결과:', aiResult);
    } catch (aiError) {
      console.log('AI 엔지니어 에러:', aiError.message);
      console.log('(참고: 유효한 OpenAI API 키가 필요합니다)');
    }
    console.log();
    
    // 프론트엔드 에이전트 테스트
    console.log('=== 프론트엔드 에이전트 테스트 ===');
    const frontendResult = await agentClient.runFrontendAgent('Create a React component for user profile page');
    console.log('프론트엔드 결과:', frontendResult);
    
  } catch (error) {
    console.error('테스트 중 오류 발생:', error);
  }
}

// 테스트 실행
testAgents().catch(err => console.error('실행 오류:', err)); 