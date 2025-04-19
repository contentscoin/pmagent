// MCP 도구 목록 제공 서버리스 함수
export default function handler(req, res) {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // OPTIONS 요청 처리
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // GET 메서드만 허용
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // 도구 목록
  const tools = [
    // PM 에이전트 도구
    {
      name: 'create_project',
      description: '새로운 프로젝트를 생성합니다.',
      category: 'pm'
    },
    {
      name: 'assign_task',
      description: '특정 에이전트에게 작업을 할당합니다.',
      category: 'pm'
    },
    {
      name: 'get_project_status',
      description: '현재 프로젝트 상태를 가져옵니다.',
      category: 'pm'
    },
    
    // 디자이너 에이전트 도구
    {
      name: 'create_design',
      description: '새로운 디자인을 생성합니다.',
      category: 'designer'
    },
    {
      name: 'get_design_system',
      description: '디자인 시스템 정보를 가져옵니다.',
      category: 'designer'
    },
    
    // 프론트엔드 에이전트 도구
    {
      name: 'create_component',
      description: '새로운 UI 컴포넌트를 생성합니다.',
      category: 'frontend'
    },
    {
      name: 'implement_screen',
      description: '화면 구현을 수행합니다.',
      category: 'frontend'
    }
  ];

  return res.status(200).json({ tools });
} 