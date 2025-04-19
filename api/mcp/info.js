// MCP 정보 제공 서버리스 함수
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

  // MCP 서버 정보
  const serverInfo = {
    qualifiedName: 'pmagent-mcp-server',
    displayName: 'PM 에이전트 MCP 서버',
    description: 'PM 에이전트 시스템을 위한 MCP 서버입니다.',
    version: '1.0.0',
  };

  return res.status(200).json(serverInfo);
} 