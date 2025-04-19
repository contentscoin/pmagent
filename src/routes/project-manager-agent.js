// 프로젝트 매니저 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const projects = new Map();
const tasks = new Map();
const sprints = new Map();
const projectMembers = new Map();

// 프로젝트 생성 검증 스키마
const createProjectSchema = z.object({
  name: z.string().min(1, { message: "프로젝트 이름은 필수입니다." }),
  description: z.string(),
  goals: z.array(z.string()).optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  budget: z.number().positive().optional(),
  tech: z.array(z.string()).optional(),
  client: z.string().optional(),
});

// 작업 할당 검증 스키마
const assignTaskSchema = z.object({
  title: z.string().min(1, { message: "작업 제목은 필수입니다." }),
  description: z.string(),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  projectId: z.string(), 
  assigneeId: z.string().optional(),
  dueDate: z.string().optional(),
  estimatedHours: z.number().positive().optional(),
  status: z.enum(['todo', 'in_progress', 'review', 'done']).default('todo'),
  tags: z.array(z.string()).optional(),
  sprintId: z.string().optional(),
});

// 스프린트 관리 검증 스키마
const manageSprintSchema = z.object({
  name: z.string().min(1, { message: "스프린트 이름은 필수입니다." }),
  projectId: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  goals: z.array(z.string()).optional(),
  status: z.enum(['planning', 'active', 'completed']).default('planning'),
});

// 팀원 관리 검증 스키마
const manageTeamMemberSchema = z.object({
  name: z.string().min(1, { message: "팀원 이름은 필수입니다." }),
  email: z.string().email({ message: "유효한 이메일 형식이 필요합니다." }),
  role: z.string(),
  projectId: z.string(),
  skills: z.array(z.string()).optional(),
  hourlyRate: z.number().positive().optional(),
  availability: z.number().min(0).max(100).optional(),
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

// 프로젝트 생성 API
router.post('/create-project', validateRequest(createProjectSchema), (req, res) => {
  try {
    const { 
      name, description, goals, startDate, 
      endDate, budget, tech, client 
    } = req.validatedBody;
    
    const projectId = uuidv4();
    
    const project = {
      id: projectId,
      name,
      description,
      goals: goals || [],
      startDate: startDate || new Date().toISOString(),
      endDate,
      budget,
      tech: tech || [],
      client,
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    projects.set(projectId, project);
    
    res.status(201).json({
      status: 'success',
      message: '프로젝트가 성공적으로 생성되었습니다.',
      data: {
        projectId,
        name: project.name,
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
router.post('/assign-task', validateRequest(assignTaskSchema), (req, res) => {
  try {
    const { 
      title, description, priority, projectId, assigneeId,
      dueDate, estimatedHours, status, tags, sprintId
    } = req.validatedBody;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    const taskId = uuidv4();
    
    const task = {
      id: taskId,
      title,
      description,
      priority,
      projectId,
      assigneeId,
      dueDate,
      estimatedHours,
      status,
      tags: tags || [],
      sprintId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      completedAt: null,
    };
    
    tasks.set(taskId, task);
    
    res.status(201).json({
      status: 'success',
      message: '작업이 성공적으로 할당되었습니다.',
      data: {
        taskId,
        title: task.title,
        assigneeId: task.assigneeId,
      },
    });
  } catch (error) {
    console.error('작업 할당 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '작업 할당 중 오류가 발생했습니다.',
    });
  }
});

// 스프린트 생성 API
router.post('/create-sprint', validateRequest(manageSprintSchema), (req, res) => {
  try {
    const { 
      name, projectId, startDate, endDate, goals, status 
    } = req.validatedBody;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    const sprintId = uuidv4();
    
    const sprint = {
      id: sprintId,
      name,
      projectId,
      startDate,
      endDate,
      goals: goals || [],
      status,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    sprints.set(sprintId, sprint);
    
    res.status(201).json({
      status: 'success',
      message: '스프린트가 성공적으로 생성되었습니다.',
      data: {
        sprintId,
        name: sprint.name,
      },
    });
  } catch (error) {
    console.error('스프린트 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '스프린트 생성 중 오류가 발생했습니다.',
    });
  }
});

// 팀원 추가 API
router.post('/add-team-member', validateRequest(manageTeamMemberSchema), (req, res) => {
  try {
    const { 
      name, email, role, projectId, skills, hourlyRate, availability 
    } = req.validatedBody;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    // 이메일 중복 확인
    const existingMembers = Array.from(projectMembers.values())
      .filter(member => member.projectId === projectId && member.email === email);
    
    if (existingMembers.length > 0) {
      return res.status(409).json({
        status: 'error',
        message: '이미 해당 이메일로 등록된 팀원이 있습니다.',
      });
    }
    
    const memberId = uuidv4();
    
    const member = {
      id: memberId,
      name,
      email,
      role,
      projectId,
      skills: skills || [],
      hourlyRate,
      availability,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    projectMembers.set(memberId, member);
    
    res.status(201).json({
      status: 'success',
      message: '팀원이 성공적으로 추가되었습니다.',
      data: {
        memberId,
        name: member.name,
        role: member.role,
      },
    });
  } catch (error) {
    console.error('팀원 추가 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '팀원 추가 중 오류가 발생했습니다.',
    });
  }
});

// 특정 프로젝트 조회 API
router.get('/project/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    const project = projects.get(projectId);
    
    res.status(200).json({
      status: 'success',
      data: project,
    });
  } catch (error) {
    console.error('프로젝트 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 조회 중 오류가 발생했습니다.',
    });
  }
});

// 특정 작업 조회 API
router.get('/task/:taskId', (req, res) => {
  try {
    const { taskId } = req.params;
    
    // 작업 존재 여부 확인
    if (!tasks.has(taskId)) {
      return res.status(404).json({
        status: 'error',
        message: '작업을 찾을 수 없습니다.',
      });
    }
    
    const task = tasks.get(taskId);
    
    res.status(200).json({
      status: 'success',
      data: task,
    });
  } catch (error) {
    console.error('작업 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '작업 조회 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트의 모든 작업 조회 API
router.get('/project-tasks/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    // 프로젝트의 모든 작업 필터링
    const projectTasks = Array.from(tasks.values())
      .filter(task => task.projectId === projectId);
    
    res.status(200).json({
      status: 'success',
      data: projectTasks,
    });
  } catch (error) {
    console.error('프로젝트 작업 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 작업 조회 중 오류가 발생했습니다.',
    });
  }
});

// 작업 상태 업데이트 API
router.patch('/update-task-status/:taskId', (req, res) => {
  try {
    const { taskId } = req.params;
    const { status } = req.body;
    
    // 상태 유효성 검증
    if (!['todo', 'in_progress', 'review', 'done'].includes(status)) {
      return res.status(400).json({
        status: 'error',
        message: '유효하지 않은 작업 상태입니다.',
      });
    }
    
    // 작업 존재 여부 확인
    if (!tasks.has(taskId)) {
      return res.status(404).json({
        status: 'error',
        message: '작업을 찾을 수 없습니다.',
      });
    }
    
    const task = tasks.get(taskId);
    
    // 작업 상태 업데이트
    task.status = status;
    task.updatedAt = new Date().toISOString();
    
    // 작업이 완료된 경우 완료 시간 설정
    if (status === 'done') {
      task.completedAt = new Date().toISOString();
    } else {
      task.completedAt = null;
    }
    
    // 업데이트된 작업 저장
    tasks.set(taskId, task);
    
    res.status(200).json({
      status: 'success',
      message: '작업 상태가 성공적으로 업데이트되었습니다.',
      data: {
        taskId,
        status: task.status,
      },
    });
  } catch (error) {
    console.error('작업 상태 업데이트 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '작업 상태 업데이트 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트 리포트 생성 API
router.get('/project-report/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트 존재 여부 확인
    if (!projects.has(projectId)) {
      return res.status(404).json({
        status: 'error',
        message: '프로젝트를 찾을 수 없습니다.',
      });
    }
    
    const project = projects.get(projectId);
    
    // 프로젝트의 모든 작업 필터링
    const projectTasks = Array.from(tasks.values())
      .filter(task => task.projectId === projectId);
    
    // 상태별 작업 수 계산
    const todoTasks = projectTasks.filter(task => task.status === 'todo').length;
    const inProgressTasks = projectTasks.filter(task => task.status === 'in_progress').length;
    const reviewTasks = projectTasks.filter(task => task.status === 'review').length;
    const doneTasks = projectTasks.filter(task => task.status === 'done').length;
    
    // 우선순위별 작업 수 계산
    const criticalTasks = projectTasks.filter(task => task.priority === 'critical').length;
    const highTasks = projectTasks.filter(task => task.priority === 'high').length;
    const mediumTasks = projectTasks.filter(task => task.priority === 'medium').length;
    const lowTasks = projectTasks.filter(task => task.priority === 'low').length;
    
    // 프로젝트 팀원 필터링
    const teamMembers = Array.from(projectMembers.values())
      .filter(member => member.projectId === projectId);
    
    // 프로젝트 스프린트 필터링
    const projectSprints = Array.from(sprints.values())
      .filter(sprint => sprint.projectId === projectId);
    
    const report = {
      projectInfo: {
        id: project.id,
        name: project.name,
        startDate: project.startDate,
        endDate: project.endDate,
        status: project.status,
      },
      taskSummary: {
        total: projectTasks.length,
        byStatus: {
          todo: todoTasks,
          inProgress: inProgressTasks,
          review: reviewTasks,
          done: doneTasks
        },
        byPriority: {
          critical: criticalTasks,
          high: highTasks,
          medium: mediumTasks,
          low: lowTasks
        },
        completionRate: projectTasks.length > 0 ? (doneTasks / projectTasks.length) * 100 : 0
      },
      teamSummary: {
        totalMembers: teamMembers.length,
        members: teamMembers.map(member => ({
          id: member.id,
          name: member.name,
          role: member.role
        }))
      },
      sprintSummary: {
        total: projectSprints.length,
        active: projectSprints.filter(sprint => sprint.status === 'active').length,
        completed: projectSprints.filter(sprint => sprint.status === 'completed').length
      },
      generatedAt: new Date().toISOString()
    };
    
    res.status(200).json({
      status: 'success',
      data: report,
    });
  } catch (error) {
    console.error('프로젝트 리포트 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 리포트 생성 중 오류가 발생했습니다.',
    });
  }
});

export default router; 