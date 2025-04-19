import { v4 as uuidv4 } from 'uuid';
import { Design, DesignSystem } from '../models/Design.js';
import Project from '../models/Project.js';

/**
 * 디자인 시스템 생성
 */
export async function createDesignSystem(systemData) {
  try {
    const systemId = uuidv4();
    
    const designSystem = new DesignSystem({
      id: systemId,
      name: systemData.name,
      description: systemData.description,
      colors: systemData.colors || {},
      typography: systemData.typography || {},
      spacing: systemData.spacing || {}
    });
    
    await designSystem.save();
    
    return {
      success: true,
      designSystemId: systemId,
      name: designSystem.name
    };
  } catch (error) {
    console.error('디자인 시스템 생성 오류:', error);
    throw new Error(`디자인 시스템 생성 실패: ${error.message}`);
  }
}

/**
 * 디자인 생성
 */
export async function createDesign(designData) {
  try {
    const { name, type, description, designSystemId, properties, projectId } = designData;
    
    // 프로젝트 존재 여부 확인
    if (projectId) {
      const projectExists = await Project.exists({ id: projectId });
      if (!projectExists) {
        throw new Error('프로젝트를 찾을 수 없습니다.');
      }
    }
    
    // 디자인 시스템 존재 여부 확인 (있는 경우)
    if (designSystemId) {
      const designSystemExists = await DesignSystem.exists({ id: designSystemId });
      if (!designSystemExists) {
        throw new Error('디자인 시스템을 찾을 수 없습니다.');
      }
    }
    
    const designId = uuidv4();
    
    const design = new Design({
      id: designId,
      name,
      type,
      description,
      designSystemId,
      properties: properties || {},
      projectId: projectId || null,
      assets: designData.assets || []
    });
    
    await design.save();
    
    return {
      success: true,
      designId,
      name: design.name,
      type: design.type
    };
  } catch (error) {
    console.error('디자인 생성 오류:', error);
    throw new Error(`디자인 생성 실패: ${error.message}`);
  }
}

/**
 * 디자인 시스템 조회
 */
export async function getDesignSystem(designSystemId) {
  try {
    const designSystem = await DesignSystem.findOne({ id: designSystemId });
    
    if (!designSystem) {
      throw new Error('디자인 시스템을 찾을 수 없습니다.');
    }
    
    return {
      success: true,
      data: {
        id: designSystem.id,
        name: designSystem.name,
        description: designSystem.description,
        colors: designSystem.colors,
        typography: designSystem.typography,
        spacing: designSystem.spacing
      }
    };
  } catch (error) {
    console.error('디자인 시스템 조회 오류:', error);
    throw new Error(`디자인 시스템 조회 실패: ${error.message}`);
  }
}

/**
 * 프로젝트의 모든 디자인 조회
 */
export async function getProjectDesigns(projectId) {
  try {
    // 프로젝트 존재 여부 확인
    const projectExists = await Project.exists({ id: projectId });
    if (!projectExists) {
      throw new Error('프로젝트를 찾을 수 없습니다.');
    }
    
    const designs = await Design.find({ projectId });
    
    const designList = designs.map(design => ({
      id: design.id,
      name: design.name,
      type: design.type,
      description: design.description,
      createdAt: design.createdAt
    }));
    
    return {
      success: true,
      data: designList
    };
  } catch (error) {
    console.error('프로젝트 디자인 조회 오류:', error);
    throw new Error(`프로젝트 디자인 조회 실패: ${error.message}`);
  }
}

/**
 * 디자인 상세 조회
 */
export async function getDesignDetail(designId) {
  try {
    const design = await Design.findOne({ id: designId });
    
    if (!design) {
      throw new Error('디자인을 찾을 수 없습니다.');
    }
    
    // 디자인 시스템 정보도 함께 가져오기 (있는 경우)
    let designSystem = null;
    if (design.designSystemId) {
      designSystem = await DesignSystem.findOne({ id: design.designSystemId });
    }
    
    return {
      success: true,
      data: {
        id: design.id,
        name: design.name,
        type: design.type,
        description: design.description,
        properties: design.properties,
        assets: design.assets,
        projectId: design.projectId,
        createdAt: design.createdAt,
        designSystem: designSystem ? {
          id: designSystem.id,
          name: designSystem.name
        } : null
      }
    };
  } catch (error) {
    console.error('디자인 상세 조회 오류:', error);
    throw new Error(`디자인 상세 조회 실패: ${error.message}`);
  }
} 