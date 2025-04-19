import { v4 as uuidv4 } from 'uuid';
import Project from '../models/Project.js';

/**
 * 프로젝트 생성
 */
export async function createProject(projectData) {
  try {
    const projectId = uuidv4();
    
    const project = new Project({
      id: projectId,
      name: projectData.name,
      description: projectData.description,
      timeline: projectData.timeline || '미정',
      requirements: projectData.requirements || [],
      status: 'active',
      tasks: [],
      completedTasks: [],
      agentStatus: {
        designer: 'idle',
        frontend: 'idle',
        backend: 'idle',
        ai_engineer: 'idle',
      }
    });
    
    await project.save();
    
    return {
      success: true,
      projectId,
      name: project.name,
    };
  } catch (error) {
    console.error('프로젝트 생성 오류:', error);
    throw new Error(`프로젝트 생성 실패: ${error.message}`);
  }
}

/**
 * 작업 할당
 */
export async function assignTask(taskData) {
  try {
    const { projectId, agentType, taskDescription, priority, deadline } = taskData;
    
    // 프로젝트 존재 여부 확인
    const project = await Project.findOne({ id: projectId });
    
    if (!project) {
      throw new Error('프로젝트를 찾을 수 없습니다.');
    }
    
    // 작업 할당
    const taskId = uuidv4();
    const task = {
      id: taskId,
      agentType,
      description: taskDescription,
      priority: priority || 'medium',
      deadline: deadline || '미정',
      status: 'pending',
      createdAt: new Date(),
      completedAt: null,
    };
    
    // 작업 추가 및 에이전트 상태 변경
    project.tasks.push(task);
    project.agentStatus[agentType] = 'working';
    
    await project.save();
    
    return {
      success: true,
      taskId,
      projectId,
      agentType,
    };
  } catch (error) {
    console.error('작업 할당 오류:', error);
    throw new Error(`작업 할당 실패: ${error.message}`);
  }
}

/**
 * 프로젝트 상태 조회
 */
export async function getProjectStatus(projectId) {
  try {
    const project = await Project.findOne({ id: projectId });
    
    if (!project) {
      throw new Error('프로젝트를 찾을 수 없습니다.');
    }
    
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
  } catch (error) {
    console.error('프로젝트 상태 조회 오류:', error);
    throw new Error(`프로젝트 상태 조회 실패: ${error.message}`);
  }
}

/**
 * 작업 승인
 */
export async function approveTask(approveData) {
  try {
    const { projectId, taskId } = approveData;
    
    // 프로젝트 존재 여부 확인
    const project = await Project.findOne({ id: projectId });
    
    if (!project) {
      throw new Error('프로젝트를 찾을 수 없습니다.');
    }
    
    // 작업 찾기
    const taskIndex = project.tasks.findIndex(task => task.id === taskId);
    
    if (taskIndex === -1) {
      throw new Error('작업을 찾을 수 없습니다.');
    }
    
    // 작업 승인 처리
    const task = project.tasks[taskIndex];
    task.status = 'completed';
    task.completedAt = new Date();
    
    // 작업 목록에서 제거하고 완료된 작업 목록에 추가
    project.tasks.splice(taskIndex, 1);
    project.completedTasks.push(task);
    
    // 에이전트 상태 업데이트
    // 해당 에이전트의 다른 작업이 없으면 'idle' 상태로 변경
    if (!project.tasks.some(t => t.agentType === task.agentType)) {
      project.agentStatus[task.agentType] = 'idle';
    }
    
    await project.save();
    
    return {
      success: true,
      taskId,
      projectId,
      agentType: task.agentType,
    };
  } catch (error) {
    console.error('작업 승인 오류:', error);
    throw new Error(`작업 승인 실패: ${error.message}`);
  }
}

/**
 * 모든 프로젝트 목록 조회
 */
export async function getAllProjects() {
  try {
    const projects = await Project.find();
    
    const projectList = projects.map(project => ({
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
  } catch (error) {
    console.error('프로젝트 목록 조회 오류:', error);
    throw new Error(`프로젝트 목록 조회 실패: ${error.message}`);
  }
} 