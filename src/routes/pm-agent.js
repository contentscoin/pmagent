// PM 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const projects = new Map();

// 프로젝트 생성 요청 검증 스키마
const createProjectSchema = z.object({
  name: z.string().min(1, { message: "프로젝트 이름은 필수입니다." }),
  description: z.string(),
  timeline: z.string().optional(),
  requirements: z.array(z.string()).optional(),
});

// 작업 할당 요청 검증 스키마
const assignTaskSchema = z.object({
  projectId: z.string().uuid({ message: "유효한 프로젝트 ID가 필요합니다." }),
  agentType: z.enum(['designer', 'frontend', 'backend', 'ai_engineer'], {
    errorMap: () => ({ message: "유효한 에이전트 유형이 필요합니다." }),
  }),
  taskDescription: z.string().min(1, { message: "작업 설명은 필수입니다." }),
  priority: z.enum(['high', 'medium', 'low']).optional().default('medium'),
  deadline: z.string().optional(),
});

// 프로젝트 상태 요청 검증 스키마
const projectStatusSchema = z.object({
  projectId: z.string().uuid({ message: "유효한 프로젝트 ID가 필요합니다." }),
});

// 작업 승인 요청 검증 스키마
const approveTaskSchema = z.object({
  projectId: z.string().uuid({ message: "유효한 프로젝트 ID가 필요합니다." }),
  taskId: z.string().uuid({ message: "유효한 작업 ID가 필요합니다." }),
});

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

// 인-메모리 프로젝트 생성 함수
function createProject(projectData) {
  const projectId = uuidv4();
  const project = {
    id: projectId,
    name: projectData.name,
    description: projectData.description,
    timeline: projectData.timeline || '미정',
    requirements: projectData.requirements || [],
    createdAt: new Date().toISOString(),
    status: 'active',
    tasks: [],
    completedTasks: [],
    agentStatus: {
      designer: 'idle',
      frontend: 'idle',
      backend: 'idle',
      ai_engineer: 'idle',
    },
  };
  
  projects.set(projectId, project);
  
  return {
    success: true,
    projectId,
    name: project.name,
  };
}

// 인-메모리 작업 할당 함수
function assignTask(taskData) {
  const { projectId, agentType, taskDescription, priority, deadline } = taskData;
  
  // 프로젝트 존재 여부 확인
  if (!projects.has(projectId)) {
    throw new Error('프로젝트를 찾을 수 없습니다.');
  }
  
  const project = projects.get(projectId);
  
  // 작업 할당
  const taskId = uuidv4();
  const task = {
    id: taskId,
    agentType,
    description: taskDescription,
    priority: priority || 'medium',
    deadline: deadline || '미정',
    status: 'pending',
    createdAt: new Date().toISOString(),
    completedAt: null,
  };
  
  project.tasks.push(task);
  project.agentStatus[agentType] = 'working';
  
  return {
    success: true,
    taskId,
    projectId,
    agentType,
  };
}

// 인-메모리 프로젝트 상태 조회 함수
function getProjectStatus(projectId) {
  // 프로젝트 존재 여부 확인
  if (!projects.has(projectId)) {
    throw new Error('프로젝트를 찾을 수 없습니다.');
  }
  
  const project = projects.get(projectId);
  
  // 프로젝트 상태 정보 구성
  const status = {
    id: project.id,
    name: project.name,
    status: project.status,
    createdAt: project.createdAt,
    pendingTasks: project.tasks.length,
    completedTasks: project.completedTasks.length,
    agentStatus: project.agentStatus,
    recentTasks: project.tasks.slice(0, 5).map(task => ({
      id: task.id,
      description: task.description,
      agentType: task.agentType,
      status: task.status,
    })),
  };
  
  return {
    success: true,
    data: status,
  };
}

// 인-메모리 작업 승인 함수
function approveTask(approveData) {
  const { projectId, taskId } = approveData;
  
  // 프로젝트 존재 여부 확인
  if (!projects.has(projectId)) {
    throw new Error('프로젝트를 찾을 수 없습니다.');
  }
  
  const project = projects.get(projectId);
  
  // 작업 찾기
  const taskIndex = project.tasks.findIndex(task => task.id === taskId);
  
  if (taskIndex === -1) {
    throw new Error('작업을 찾을 수 없습니다.');
  }
  
  // 작업 승인 처리
  const task = project.tasks[taskIndex];
  task.status = 'completed';
  task.completedAt = new Date().toISOString();
  
  // 작업 목록에서 제거하고 완료된 작업 목록에 추가
  project.tasks.splice(taskIndex, 1);
  project.completedTasks.push(task);
  
  // 에이전트 상태 업데이트
  // 해당 에이전트의 다른 작업이 없으면 'idle' 상태로 변경
  if (!project.tasks.some(t => t.agentType === task.agentType)) {
    project.agentStatus[task.agentType] = 'idle';
  }
  
  return {
    success: true,
    taskId,
    projectId,
    agentType: task.agentType,
  };
}

// 인-메모리 모든 프로젝트 목록 조회 함수
function getAllProjects() {
  const projectList = Array.from(projects.values()).map(project => ({
    id: project.id,
    name: project.name,
    status: project.status,
    pendingTasks: project.tasks.length,
    completedTasks: project.completedTasks.length,
  }));
  
  return {
    success: true,
    data: projectList,
  };
}

// 프로젝트 생성 API
router.post('/create-project', validateRequest(createProjectSchema), async (req, res) => {
  try {
    const result = createProject(req.validatedBody);
    
    res.status(201).json({
      status: 'success',
      message: '프로젝트가 성공적으로 생성되었습니다.',
      data: {
        projectId: result.projectId,
        name: result.name,
      },
    });
  } catch (error) {
    console.error('프로젝트 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 생성 중 오류가 발생했습니다.',
    });
  }
});

// 작업 할당 API
router.post('/assign-task', validateRequest(assignTaskSchema), async (req, res) => {
  try {
    const result = assignTask(req.validatedBody);
    
    res.status(200).json({
      status: 'success',
      message: '작업이 성공적으로 할당되었습니다.',
      data: {
        taskId: result.taskId,
        projectId: result.projectId,
        agentType: result.agentType,
      },
    });
  } catch (error) {
    console.error('작업 할당 API 오류:', error);
    const statusCode = error.message.includes('찾을 수 없습니다') ? 404 : 500;
    
    res.status(statusCode).json({
      status: 'error',
      message: error.message || '작업 할당 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트 상태 조회 API
router.post('/project-status', validateRequest(projectStatusSchema), async (req, res) => {
  try {
    const { projectId } = req.validatedBody;
    const result = getProjectStatus(projectId);
    
    res.status(200).json({
      status: 'success',
      data: result.data,
    });
  } catch (error) {
    console.error('프로젝트 상태 조회 API 오류:', error);
    const statusCode = error.message.includes('찾을 수 없습니다') ? 404 : 500;
    
    res.status(statusCode).json({
      status: 'error',
      message: error.message || '프로젝트 상태 조회 중 오류가 발생했습니다.',
    });
  }
});

// 작업 승인 API
router.post('/approve-task', validateRequest(approveTaskSchema), async (req, res) => {
  try {
    const result = approveTask(req.validatedBody);
    
    res.status(200).json({
      status: 'success',
      message: '작업이 성공적으로 승인되었습니다.',
      data: {
        taskId: result.taskId,
        projectId: result.projectId,
        agentType: result.agentType,
      },
    });
  } catch (error) {
    console.error('작업 승인 API 오류:', error);
    const statusCode = error.message.includes('찾을 수 없습니다') ? 404 : 500;
    
    res.status(statusCode).json({
      status: 'error',
      message: error.message || '작업 승인 중 오류가 발생했습니다.',
    });
  }
});

// 모든 프로젝트 목록 조회 API
router.get('/projects', async (req, res) => {
  try {
    const result = getAllProjects();
    
    res.status(200).json({
      status: 'success',
      data: result.data,
    });
  } catch (error) {
    console.error('프로젝트 목록 조회 API 오류:', error);
    
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 목록 조회 중 오류가 발생했습니다.',
    });
  }
});

export default router; 