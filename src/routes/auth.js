// 사용자 인증 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

const router = express.Router();

// 인-메모리 데이터베이스
const users = new Map();
const tokens = new Map();

// JWT 시크릿 키 (실제 프로덕션에서는 환경 변수에서 가져와야 함)
const JWT_SECRET = process.env.JWT_SECRET || 'pmagent-secret-key';
const TOKEN_EXPIRES_IN = '24h';

// 회원가입 요청 검증 스키마
const registerSchema = z.object({
  username: z.string().min(4, { message: "사용자명은 최소 4자 이상이어야 합니다." }),
  email: z.string().email({ message: "유효한 이메일 형식이 필요합니다." }),
  password: z.string().min(8, { message: "비밀번호는 최소 8자 이상이어야 합니다." }),
  name: z.string().optional(),
  role: z.enum(['admin', 'manager', 'member']).default('member'),
});

// 로그인 요청 검증 스키마
const loginSchema = z.object({
  email: z.string().email({ message: "유효한 이메일 형식이 필요합니다." }),
  password: z.string().min(1, { message: "비밀번호는 필수입니다." }),
});

// 토큰 검증 미들웨어
const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      status: 'error',
      message: '인증 토큰이 필요합니다.',
    });
  }
  
  const token = authHeader.split(' ')[1];
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // 토큰이 유효한지 확인
    if (!tokens.has(decoded.userId)) {
      return res.status(401).json({
        status: 'error',
        message: '유효하지 않은 토큰입니다.',
      });
    }
    
    // 사용자가 존재하는지 확인
    if (!users.has(decoded.userId)) {
      return res.status(401).json({
        status: 'error',
        message: '사용자를 찾을 수 없습니다.',
      });
    }
    
    req.user = users.get(decoded.userId);
    next();
  } catch (error) {
    console.error('토큰 검증 오류:', error);
    res.status(401).json({
      status: 'error',
      message: '인증에 실패했습니다.',
    });
  }
};

// 역할 기반 접근 제어 미들웨어
const roleCheck = (roles) => (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({
      status: 'error',
      message: '인증이 필요합니다.',
    });
  }
  
  if (!roles.includes(req.user.role)) {
    return res.status(403).json({
      status: 'error',
      message: '접근 권한이 없습니다.',
    });
  }
  
  next();
};

// 미들웨어: 요청 본문 검증
const validateRequest = (schema) => (req, res, next) => {
  try {
    req.validatedBody = schema.parse(req.body);
    next();
  } catch (error) {
    res.status(400).json({
      status: 'error',
      message: '요청 데이터 검증 실패',
      details: error.errors,
    });
  }
};

// 회원가입 API
router.post('/register', validateRequest(registerSchema), async (req, res) => {
  try {
    const { username, email, password, name, role } = req.validatedBody;
    
    // 이메일 중복 확인
    const existingUser = Array.from(users.values()).find(user => user.email === email);
    if (existingUser) {
      return res.status(409).json({
        status: 'error',
        message: '이미 등록된 이메일입니다.',
      });
    }
    
    // 사용자명 중복 확인
    const existingUsername = Array.from(users.values()).find(user => user.username === username);
    if (existingUsername) {
      return res.status(409).json({
        status: 'error',
        message: '이미 사용 중인 사용자명입니다.',
      });
    }
    
    // 비밀번호 해싱
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    const userId = uuidv4();
    
    const user = {
      id: userId,
      username,
      email,
      password: hashedPassword,
      name: name || username,
      role,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    users.set(userId, user);
    
    // 응답에서 비밀번호 제외
    const { password: _, ...userWithoutPassword } = user;
    
    res.status(201).json({
      status: 'success',
      message: '회원가입이 성공적으로 완료되었습니다.',
      data: userWithoutPassword,
    });
  } catch (error) {
    console.error('회원가입 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '회원가입 중 오류가 발생했습니다.',
    });
  }
});

// 로그인 API
router.post('/login', validateRequest(loginSchema), async (req, res) => {
  try {
    const { email, password } = req.validatedBody;
    
    // 사용자 찾기
    const user = Array.from(users.values()).find(user => user.email === email);
    if (!user) {
      return res.status(401).json({
        status: 'error',
        message: '이메일 또는 비밀번호가 일치하지 않습니다.',
      });
    }
    
    // 비밀번호 확인
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({
        status: 'error',
        message: '이메일 또는 비밀번호가 일치하지 않습니다.',
      });
    }
    
    // JWT 토큰 생성
    const token = jwt.sign(
      { userId: user.id, email: user.email, role: user.role },
      JWT_SECRET,
      { expiresIn: TOKEN_EXPIRES_IN }
    );
    
    // 토큰 저장
    tokens.set(user.id, {
      token,
      createdAt: new Date().toISOString(),
    });
    
    // 응답에서 비밀번호 제외
    const { password: _, ...userWithoutPassword } = user;
    
    res.status(200).json({
      status: 'success',
      message: '로그인이 성공적으로 완료되었습니다.',
      data: {
        user: userWithoutPassword,
        token,
        expiresIn: TOKEN_EXPIRES_IN,
      },
    });
  } catch (error) {
    console.error('로그인 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '로그인 중 오류가 발생했습니다.',
    });
  }
});

// 로그아웃 API
router.post('/logout', authMiddleware, (req, res) => {
  try {
    tokens.delete(req.user.id);
    
    res.status(200).json({
      status: 'success',
      message: '로그아웃이 성공적으로 완료되었습니다.',
    });
  } catch (error) {
    console.error('로그아웃 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '로그아웃 중 오류가 발생했습니다.',
    });
  }
});

// 사용자 정보 조회 API
router.get('/profile', authMiddleware, (req, res) => {
  try {
    // 응답에서 비밀번호 제외
    const { password, ...userWithoutPassword } = req.user;
    
    res.status(200).json({
      status: 'success',
      data: userWithoutPassword,
    });
  } catch (error) {
    console.error('사용자 정보 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '사용자 정보 조회 중 오류가 발생했습니다.',
    });
  }
});

// 사용자 정보 업데이트 API
router.patch('/profile', authMiddleware, (req, res) => {
  try {
    const { name, username } = req.body;
    
    // 사용자 정보 가져오기
    const user = users.get(req.user.id);
    
    // 사용자명 변경 시 중복 확인
    if (username && username !== user.username) {
      const existingUsername = Array.from(users.values()).find(u => u.username === username);
      if (existingUsername) {
        return res.status(409).json({
          status: 'error',
          message: '이미 사용 중인 사용자명입니다.',
        });
      }
      
      user.username = username;
    }
    
    // 이름 업데이트
    if (name) {
      user.name = name;
    }
    
    user.updatedAt = new Date().toISOString();
    users.set(user.id, user);
    
    // 응답에서 비밀번호 제외
    const { password, ...userWithoutPassword } = user;
    
    res.status(200).json({
      status: 'success',
      message: '사용자 정보가 성공적으로 업데이트되었습니다.',
      data: userWithoutPassword,
    });
  } catch (error) {
    console.error('사용자 정보 업데이트 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '사용자 정보 업데이트 중 오류가 발생했습니다.',
    });
  }
});

// 비밀번호 변경 API
router.post('/change-password', authMiddleware, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    
    if (!currentPassword || !newPassword) {
      return res.status(400).json({
        status: 'error',
        message: '현재 비밀번호와 새 비밀번호가 필요합니다.',
      });
    }
    
    if (newPassword.length < 8) {
      return res.status(400).json({
        status: 'error',
        message: '새 비밀번호는 최소 8자 이상이어야 합니다.',
      });
    }
    
    // 사용자 정보 가져오기
    const user = users.get(req.user.id);
    
    // 현재 비밀번호 확인
    const isPasswordValid = await bcrypt.compare(currentPassword, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({
        status: 'error',
        message: '현재 비밀번호가 일치하지 않습니다.',
      });
    }
    
    // 비밀번호 해싱
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(newPassword, salt);
    
    // 비밀번호 업데이트
    user.password = hashedPassword;
    user.updatedAt = new Date().toISOString();
    users.set(user.id, user);
    
    // 모든 디바이스에서 로그아웃 (토큰 삭제)
    tokens.delete(user.id);
    
    res.status(200).json({
      status: 'success',
      message: '비밀번호가 성공적으로 변경되었습니다. 다시 로그인해주세요.',
    });
  } catch (error) {
    console.error('비밀번호 변경 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '비밀번호 변경 중 오류가 발생했습니다.',
    });
  }
});

// 관리자용: 모든 사용자 목록 조회 API
router.get('/users', authMiddleware, roleCheck(['admin']), (req, res) => {
  try {
    const userList = Array.from(users.values()).map(user => {
      const { password, ...userWithoutPassword } = user;
      return userWithoutPassword;
    });
    
    res.status(200).json({
      status: 'success',
      data: userList,
    });
  } catch (error) {
    console.error('사용자 목록 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '사용자 목록 조회 중 오류가 발생했습니다.',
    });
  }
});

// 내보내기
export { authMiddleware, roleCheck };
export default router; 