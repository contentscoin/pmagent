/**
 * PPLShop Agent Client
 * 파이썬 에이전트를 자바스크립트에서 호출하기 위한 클라이언트 래퍼
 */

const { spawn } = require('child_process');
const path = require('path');

class AgentClient {
  /**
   * 에이전트 클라이언트 초기화
   * @param {Object} config - 설정 객체
   * @param {string} config.pythonPath - 파이썬 실행 경로 (기본값: 'python')
   * @param {string} config.agentDir - 에이전트 디렉토리 (기본값: '../agents')
   * @param {Object} config.env - 환경 변수
   */
  constructor(config = {}) {
    this.pythonPath = config.pythonPath || 'python';
    this.agentDir = config.agentDir || path.join(__dirname, '../agents');
    this.env = {
      ...process.env,
      ...(config.env || {})
    };
  }

  /**
   * PM 에이전트 실행
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   */
  async runPMAgent(task) {
    return this._runAgent('pm_agent', task);
  }

  /**
   * 디자이너 에이전트 실행
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   */
  async runDesignerAgent(task) {
    return this._runAgent('designer_agent', task);
  }

  /**
   * 프론트엔드 에이전트 실행
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   */
  async runFrontendAgent(task) {
    return this._runAgent('frontend_agent', task);
  }

  /**
   * 백엔드 에이전트 실행
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   */
  async runBackendAgent(task) {
    return this._runAgent('backend_agent', task);
  }

  /**
   * AI 엔지니어 에이전트 실행
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   */
  async runAIEngineerAgent(task) {
    return this._runAgent('ai_engineer_agent', task);
  }

  /**
   * 에이전트 실행 내부 메서드
   * @param {string} agentModule - 에이전트 모듈 이름
   * @param {string} task - 실행할 작업 설명
   * @returns {Promise<string>} - 작업 결과
   * @private
   */
  _runAgent(agentModule, task) {
    return new Promise((resolve, reject) => {
      // 파이썬 스크립트 생성
      const scriptContent = `
from agents.${agentModule} import ${this._getClassName(agentModule)}
import sys
import json

try:
    agent = ${this._getClassName(agentModule)}()
    result = agent.run_task(${JSON.stringify(task)})
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
      `.trim();

      // 임시 스크립트 파일 경로
      const tempScriptPath = path.join(__dirname, `_temp_${agentModule}_script.py`);
      
      // 파일 시스템 액세스
      const fs = require('fs');
      fs.writeFileSync(tempScriptPath, scriptContent);

      try {
        // 파이썬 프로세스 실행
        const pythonProcess = spawn(this.pythonPath, [tempScriptPath], {
          env: this.env
        });

        let outputData = '';
        let errorData = '';

        // 출력 데이터 수집
        pythonProcess.stdout.on('data', (data) => {
          outputData += data.toString();
        });

        // 오류 데이터 수집
        pythonProcess.stderr.on('data', (data) => {
          errorData += data.toString();
        });

        // 프로세스 종료 이벤트
        pythonProcess.on('close', (code) => {
          // 임시 파일 삭제
          try {
            fs.unlinkSync(tempScriptPath);
          } catch (err) {
            console.error('임시 파일 삭제 오류:', err);
          }

          if (code !== 0) {
            reject(new Error(`Process exited with code ${code}: ${errorData}`));
            return;
          }

          try {
            // JSON 응답 파싱
            const lastLine = outputData.trim().split('\n').pop();
            const response = JSON.parse(lastLine);
            
            if (response.success) {
              resolve(response.result);
            } else {
              reject(new Error(response.error));
            }
          } catch (err) {
            reject(new Error(`응답 파싱 오류: ${err.message}\n출력: ${outputData}`));
          }
        });
      } catch (err) {
        // 임시 파일 삭제 시도
        try {
          fs.unlinkSync(tempScriptPath);
        } catch (cleanupErr) {
          console.error('임시 파일 삭제 오류:', cleanupErr);
        }
        
        reject(err);
      }
    });
  }

  /**
   * 모듈 이름에서 클래스 이름 추출
   * @param {string} moduleName - 모듈 이름
   * @returns {string} - 클래스 이름
   * @private
   */
  _getClassName(moduleName) {
    // 스네이크 케이스를 파스칼 케이스로 변환
    return moduleName.split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join('');
  }
}

module.exports = AgentClient; 