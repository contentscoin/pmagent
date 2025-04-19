import os
import json
import requests
from typing import Dict, List, Any, Optional, Union
from .base_tool import BaseTool

class AIEngineerAgentOllama(BaseTool):
    """
    Ollama API를 사용하는 AI Engineer Agent
    
    AI/ML 관련 작업을 지원하는 Ollama 기반 에이전트
    - 텍스트 생성 서비스 구현
    - 추천 시스템 생성
    - 이미지 처리 서비스 구현
    - AI 모델 통합
    """
    
    name = "ai_engineer_agent_ollama"
    description = "Ollama 기반 AI Engineer Agent - AI/ML 서비스 구현 지원"
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, 
                 model: str = "llama3.2:latest", use_mcp: bool = False, 
                 mcp_helper: Optional[Any] = None, **kwargs):
        """
        Ollama 기반 AI Engineer Agent 초기화
        
        Args:
            api_key: 사용되지 않음 (Ollama 호환성 유지용)
            api_base: Ollama API 기본 URL
            model: 사용할 Ollama 모델명
            use_mcp: MCP(Model Context Protocol) 사용 여부
            mcp_helper: MCPAgentHelper 인스턴스
        """
        # API 설정
        self.api_key = api_key  # Ollama는 API 키를 사용하지 않지만 호환성을 위해 유지
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
        
        # MCP 설정
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
        # 프로젝트 설정 초기화
        self.project_config = self._initialize_project_config()
        
        # 모델 가용성 확인
        self._check_model_availability()
    
    def _initialize_project_config(self) -> Dict[str, Any]:
        """
        프로젝트 설정 초기화
        
        Returns:
            Dict[str, Any]: 프로젝트 설정
        """
        return {
            "paths": {
                "ai_models": "src/models",
                "services": "src/services",
                "utils": "src/utils",
            },
            "backend_framework": "express",
            "use_typescript": True,
            "default_ai_service": "openai",
            "model_specs": {
                "text_completion": {
                    "openai": "gpt-3.5-turbo",
                    "huggingface": "gpt2"
                },
                "image_processing": {
                    "openai": "dall-e-3",
                    "huggingface": "stable-diffusion"
                }
            }
        }
    
    def get_available_models(self) -> List[str]:
        """
        Ollama에서 사용 가능한 모델 목록을 가져옵니다.
        
        Returns:
            List[str]: 사용 가능한 모델 목록
        """
        try:
            url = f"{self.api_base.rstrip('/')}/tags"
            response = requests.get(url)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model.get("name") for model in models]
        except Exception as e:
            print(f"모델 목록을 가져오는 중 오류 발생: {str(e)}")
            return []
    
    def _check_model_availability(self):
        """사용 가능한 Ollama 모델 확인"""
        try:
            available_models = self.get_available_models()
            if self.model not in available_models:
                available_model_str = ", ".join(available_models)
                
                # 대체 모델 사용 시도
                if len(available_models) > 0:
                    fallback_model = available_models[0]
                    print(f"⚠️ 경고: 모델 '{self.model}'은(는) 사용할 수 없습니다. 사용 가능한 모델: {available_model_str}")
                    print(f"⚠️ 대체 모델 '{fallback_model}'(을)를 사용합니다.")
                    self.model = fallback_model
                else:
                    print(f"⚠️ 경고: 모델 '{self.model}'은(는) 사용할 수 없으며, 사용 가능한 대체 모델이 없습니다.")
                    print("Ollama가 실행 중이고 모델이 정확한지 확인하세요.")
        except Exception as e:
            print(f"⚠️ Ollama 모델 확인 중 오류 발생: {str(e)}")
            print("Ollama가 실행 중인지 확인하세요.")
    
    def _call_ollama_api(self, prompt: str, system_prompt: Optional[str] = None, 
                         temperature: float = 0.7, max_tokens: int = 2000, 
                         json_output: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Ollama API 호출
        
        Args:
            prompt: 프롬프트 텍스트
            system_prompt: 시스템 프롬프트 (지시사항)
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            json_output: JSON 형식 출력 요청 여부
            
        Returns:
            Union[str, Dict[str, Any]]: API 응답 (텍스트 또는 JSON)
        """
        url = f"{self.api_base.rstrip('/')}/generate"
        
        # JSON 출력을 요청하는 경우 프롬프트 수정
        if json_output and system_prompt:
            system_prompt += "\n응답은 반드시 올바른 JSON 형식으로 제공하세요."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "options": {}
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json().get("response", "응답을 받을 수 없습니다.")
            
            # JSON 형식으로 반환 요청된 경우 파싱 시도
            if json_output:
                try:
                    # JSON 형식 문자열 추출 (코드 블록에서)
                    if "```json" in result:
                        json_str = result.split("```json")[1].split("```")[0].strip()
                    elif "```" in result:
                        json_str = result.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = result
                    
                    return json.loads(json_str)
                except Exception:
                    # JSON 파싱 실패 시 원본 텍스트 반환
                    return {"error": "JSON 파싱 실패", "text": result}
            
            return result
        except Exception as e:
            if json_output:
                return {"error": f"Ollama API 호출 오류: {str(e)}"}
            return f"Ollama API 호출 중 오류 발생: {str(e)}"
    
    def _run(self, task: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """
        AI Engineer Agent로 작업을 실행합니다.
        
        Args:
            task: 작업 정보 딕셔너리
            
        Returns:
            Union[str, Dict[str, Any]]: 작업 결과
        """
        task_type = task.get('type', 'general_ai')
        task_desc = task.get('task', '')
        
        # 작업 유형에 따른 처리
        if task_type == 'text_completion_service':
            ai_provider = task.get('ai_provider', self.project_config['default_ai_service'])
            return self.create_text_completion_service(ai_provider)
            
        elif task_type == 'recommendation_system':
            data_type = task.get('data_type', 'products')
            return self.create_recommendation_system(data_type)
            
        elif task_type == 'image_processing_service':
            processing_type = task.get('processing_type', 'generation')
            return self.create_image_processing_service(processing_type)
            
        elif task_type == 'ai_model_integration':
            model_type = task.get('model_type', 'language_model')
            model_source = task.get('model_source', 'openai')
            return self.integrate_ai_model(model_type, model_source)
            
        else:
            # 일반 AI 관련 작업
            return self._general_ai_task(task_desc)
    
    def _general_ai_task(self, task_desc: str) -> str:
        """
        일반 AI 관련 작업 수행
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: AI 작업 제안
        """
        system_prompt = """
        당신은 경험 많은 AI 엔지니어입니다. 요청에 따라 구체적이고 실행 가능한 AI 솔루션을 제안하세요.
        - 최신 AI 기술과 모델을 활용하세요
        - 구현 방법과 API 사용 예시를 포함하세요
        - 성능과 확장성을 고려하세요
        - 데이터 처리 방법도 설명하세요
        
        명확하고 조직적인 형식으로 답변하세요.
        """
        
        prompt = f"다음 AI 관련 작업에 대한 해결책을 제안해주세요: {task_desc}"
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.7)
    
    def create_text_completion_service(self, ai_provider: str = "openai") -> Dict[str, Any]:
        """
        텍스트 완성 서비스 생성
        
        Args:
            ai_provider: AI 제공자 ("openai" 또는 "huggingface")
            
        Returns:
            Dict[str, Any]: 서비스 코드 및 정보
        """
        system_prompt = f"""
        당신은 AI 서비스 개발 전문가입니다. {ai_provider} API를 사용하는 텍스트 완성 서비스를 개발해야 합니다.
        
        다음 요소를 포함한 코드를 생성하세요:
        1. API 클라이언트 설정
        2. 텍스트 완성 요청 처리 함수
        3. 오류 처리 및 재시도 로직
        4. API 응답 파싱 및 처리
        5. 필요한 타입 정의
        
        TypeScript를 사용하고, 모듈화된 구조로 코드를 작성하세요.
        """
        
        prompt = f"{ai_provider} API를 사용하는 텍스트 완성 서비스를 구현해주세요."
        
        # 서비스 경로 생성
        file_path = f"{self.project_config['paths']['services']}/text_completion_{ai_provider}.ts"
        
        # Ollama API 호출하여 서비스 코드 생성
        result = self._call_ollama_api(prompt, system_prompt, temperature=0.6, max_tokens=2500, json_output=True)
        
        # JSON이 아닌 경우 변환
        if isinstance(result, str):
            return {
                "service_path": file_path,
                "service_code": result,
                "dependencies": self._get_dependencies_for_service(ai_provider),
                "usage_example": self._get_usage_example("text_completion", ai_provider)
            }
        
        # 결과에 코드가 없는 경우 처리
        if "code" not in result and "service_code" not in result:
            result["service_code"] = result.get("text", "// 코드를 생성할 수 없습니다.")
        
        return {
            "service_path": file_path,
            "service_code": result.get("code", result.get("service_code", result.get("text", ""))),
            "dependencies": self._get_dependencies_for_service(ai_provider),
            "usage_example": self._get_usage_example("text_completion", ai_provider)
        }
    
    def create_recommendation_system(self, data_type: str = "products") -> Dict[str, Any]:
        """
        추천 시스템 생성
        
        Args:
            data_type: 데이터 타입 ("products", "content", "users" 등)
            
        Returns:
            Dict[str, Any]: 추천 시스템 코드 및 정보
        """
        system_prompt = f"""
        당신은 추천 시스템 개발 전문가입니다. {data_type}를 위한 추천 시스템을 개발해야 합니다.
        
        다음 요소를 포함한 코드를 생성하세요:
        1. 데이터 모델 및 스키마
        2. 추천 알고리즘 구현
        3. 유사도 계산 함수
        4. 추천 결과 필터링 및 정렬
        5. API 엔드포인트 및 사용 예시
        
        TypeScript를 사용하고, 모듈화된 구조로 코드를 작성하세요.
        협업 필터링 또는 콘텐츠 기반 필터링 알고리즘을 선택하고, 그 이유를 설명하세요.
        """
        
        prompt = f"{data_type}에 대한 추천 시스템을 구현해주세요."
        
        # 서비스 경로 생성
        file_path = f"{self.project_config['paths']['services']}/{data_type}_recommendation_service.ts"
        
        # Ollama API 호출하여 추천 시스템 코드 생성
        result = self._call_ollama_api(prompt, system_prompt, temperature=0.6, max_tokens=2500, json_output=True)
        
        # JSON이 아닌 경우 변환
        if isinstance(result, str):
            return {
                "service_path": file_path,
                "service_code": result,
                "algorithm_type": "collaborative_filtering",  # 기본값
                "data_requirements": self._get_data_requirements(data_type),
                "usage_example": f"// {data_type} 추천 시스템 사용 예시:\n// const recommendations = await recommendationService.getRecommendations(userId, limit);"
            }
        
        # 결과에 코드가 없는 경우 처리
        if "code" not in result and "service_code" not in result:
            result["service_code"] = result.get("text", "// 코드를 생성할 수 없습니다.")
        
        return {
            "service_path": file_path,
            "service_code": result.get("code", result.get("service_code", result.get("text", ""))),
            "algorithm_type": result.get("algorithm_type", "collaborative_filtering"),
            "data_requirements": self._get_data_requirements(data_type),
            "usage_example": result.get("usage_example", f"// {data_type} 추천 시스템 사용 예시:\n// const recommendations = await recommendationService.getRecommendations(userId, limit);")
        }
    
    def create_image_processing_service(self, processing_type: str = "generation") -> Dict[str, Any]:
        """
        이미지 처리 서비스 생성
        
        Args:
            processing_type: 처리 유형 ("generation", "recognition", "classification" 등)
            
        Returns:
            Dict[str, Any]: 이미지 처리 서비스 코드 및 정보
        """
        # 처리 유형에 따른 설명 제공
        processing_descriptions = {
            "generation": "이미지 생성 서비스",
            "recognition": "이미지 인식 서비스",
            "classification": "이미지 분류 서비스",
            "segmentation": "이미지 세그멘테이션 서비스"
        }
        
        description = processing_descriptions.get(processing_type, "이미지 처리 서비스")
        
        system_prompt = f"""
        당신은 이미지 처리 서비스 개발 전문가입니다. {description}를 개발해야 합니다.
        
        다음 요소를 포함한 코드를 생성하세요:
        1. 적절한 AI API 또는 라이브러리 통합
        2. 이미지 처리 및 변환 함수
        3. 결과 처리 및 반환
        4. 오류 처리
        5. API 엔드포인트 및 사용 예시
        
        TypeScript를 사용하고, 모듈화된 구조로 코드를 작성하세요.
        """
        
        prompt = f"{description}를 구현해주세요."
        
        # 서비스 경로 생성
        file_path = f"{self.project_config['paths']['services']}/image_{processing_type}_service.ts"
        
        # AI 제공자 결정 (이미지 생성은 OpenAI 또는 다른 제공자 사용)
        ai_provider = "openai" if processing_type == "generation" else "tensorflow"
        
        # Ollama API 호출하여 이미지 처리 서비스 코드 생성
        result = self._call_ollama_api(prompt, system_prompt, temperature=0.6, max_tokens=2500, json_output=True)
        
        # JSON이 아닌 경우 변환
        if isinstance(result, str):
            return {
                "service_path": file_path,
                "service_code": result,
                "ai_provider": ai_provider,
                "dependencies": self._get_dependencies_for_service(ai_provider),
                "usage_example": self._get_usage_example("image_processing", processing_type)
            }
        
        # 결과에 코드가 없는 경우 처리
        if "code" not in result and "service_code" not in result:
            result["service_code"] = result.get("text", "// 코드를 생성할 수 없습니다.")
        
        return {
            "service_path": file_path,
            "service_code": result.get("code", result.get("service_code", result.get("text", ""))),
            "ai_provider": ai_provider,
            "dependencies": self._get_dependencies_for_service(ai_provider),
            "usage_example": self._get_usage_example("image_processing", processing_type)
        }
    
    def integrate_ai_model(self, model_type: str, model_source: str) -> Dict[str, Any]:
        """
        AI 모델 통합 서비스 생성
        
        Args:
            model_type: 모델 유형 ("language_model", "vision_model" 등)
            model_source: 모델 소스 ("openai", "huggingface", "tensorflow" 등)
            
        Returns:
            Dict[str, Any]: AI 모델 통합 코드 및 정보
        """
        system_prompt = f"""
        당신은 AI 모델 통합 전문가입니다. {model_source}의 {model_type}을 프로젝트에 통합해야 합니다.
        
        다음 요소를 포함한 코드를 생성하세요:
        1. 모델 로딩 및 초기화
        2. 추론 또는 예측 함수
        3. 입력 전처리 및 출력 후처리
        4. 캐싱 및 성능 최적화
        5. API 엔드포인트 및 사용 예시
        
        TypeScript를 사용하고, 모듈화된 구조로 코드를 작성하세요.
        """
        
        prompt = f"{model_source}의 {model_type}을 프로젝트에 통합하는 코드를 작성해주세요."
        
        # 모델 경로 생성
        file_path = f"{self.project_config['paths']['ai_models']}/{model_type}_{model_source}.ts"
        
        # Ollama API 호출하여 모델 통합 코드 생성
        result = self._call_ollama_api(prompt, system_prompt, temperature=0.6, max_tokens=2500, json_output=True)
        
        # JSON이 아닌 경우 변환
        if isinstance(result, str):
            return {
                "model_path": file_path,
                "model_code": result,
                "dependencies": self._get_dependencies_for_service(model_source),
                "usage_example": f"// {model_type} 사용 예시:\n// const result = await {model_type}Service.predict(input);"
            }
        
        # 결과에 코드가 없는 경우 처리
        if "code" not in result and "model_code" not in result:
            result["model_code"] = result.get("text", "// 코드를 생성할 수 없습니다.")
        
        return {
            "model_path": file_path,
            "model_code": result.get("code", result.get("model_code", result.get("text", ""))),
            "dependencies": self._get_dependencies_for_service(model_source),
            "usage_example": result.get("usage_example", f"// {model_type} 사용 예시:\n// const result = await {model_type}Service.predict(input);")
        }
    
    def _get_dependencies_for_service(self, service_type: str) -> Dict[str, str]:
        """
        서비스에 필요한 의존성 패키지 정보 반환
        
        Args:
            service_type: 서비스 유형
            
        Returns:
            Dict[str, str]: 의존성 패키지 및 버전
        """
        dependencies = {
            "openai": {
                "openai": "^4.0.0",
                "dotenv": "^16.0.0"
            },
            "huggingface": {
                "@huggingface/inference": "^2.3.0",
                "dotenv": "^16.0.0"
            },
            "tensorflow": {
                "@tensorflow/tfjs-node": "^4.4.0",
                "sharp": "^0.32.1"
            }
        }
        
        return dependencies.get(service_type, {"dotenv": "^16.0.0"})
    
    def _get_usage_example(self, service_type: str, subtype: str = "") -> str:
        """
        서비스 사용 예시 생성
        
        Args:
            service_type: 서비스 유형
            subtype: 서비스 하위 유형
            
        Returns:
            str: 사용 예시 코드
        """
        examples = {
            "text_completion": {
                "openai": """
                // OpenAI 텍스트 완성 서비스 사용 예시:
                import { TextCompletionService } from '../services/text_completion_openai';
                
                const completionService = new TextCompletionService();
                
                async function getCompletion() {
                  try {
                    const prompt = "Write a short story about a robot learning to paint.";
                    const result = await completionService.generateCompletion(prompt);
                    console.log(result);
                  } catch (error) {
                    console.error("Error generating completion:", error);
                  }
                }
                
                getCompletion();
                """,
                "huggingface": """
                // HuggingFace 텍스트 완성 서비스 사용 예시:
                import { TextCompletionService } from '../services/text_completion_huggingface';
                
                const completionService = new TextCompletionService();
                
                async function getCompletion() {
                  try {
                    const prompt = "Write a short story about a robot learning to paint.";
                    const result = await completionService.generateCompletion(prompt);
                    console.log(result);
                  } catch (error) {
                    console.error("Error generating completion:", error);
                  }
                }
                
                getCompletion();
                """
            },
            "image_processing": {
                "generation": """
                // 이미지 생성 서비스 사용 예시:
                import { ImageGenerationService } from '../services/image_generation_service';
                
                const imageService = new ImageGenerationService();
                
                async function generateImage() {
                  try {
                    const prompt = "A serene mountain landscape with a lake at sunset";
                    const image = await imageService.generateImage(prompt);
                    console.log("Image URL:", image.url);
                  } catch (error) {
                    console.error("Error generating image:", error);
                  }
                }
                
                generateImage();
                """,
                "recognition": """
                // 이미지 인식 서비스 사용 예시:
                import { ImageRecognitionService } from '../services/image_recognition_service';
                
                const recognitionService = new ImageRecognitionService();
                
                async function recognizeImage() {
                  try {
                    const imageUrl = "https://example.com/sample-image.jpg";
                    const result = await recognitionService.recognizeObjects(imageUrl);
                    console.log("Detected objects:", result.objects);
                  } catch (error) {
                    console.error("Error recognizing image:", error);
                  }
                }
                
                recognizeImage();
                """
            }
        }
        
        service_examples = examples.get(service_type, {})
        return service_examples.get(subtype, "// 사용 예시를 생성할 수 없습니다.")
    
    def _get_data_requirements(self, data_type: str) -> Dict[str, List[str]]:
        """
        데이터 요구사항 정보 반환
        
        Args:
            data_type: 데이터 유형
            
        Returns:
            Dict[str, List[str]]: 필요한 데이터 필드 목록
        """
        requirements = {
            "products": {
                "required_fields": ["id", "name", "category", "price", "features", "ratings", "viewCount"],
                "optional_fields": ["description", "imageUrl", "brand", "relatedProducts"]
            },
            "content": {
                "required_fields": ["id", "title", "type", "tags", "viewCount", "createdAt"],
                "optional_fields": ["description", "author", "category", "likeCount", "duration"]
            },
            "users": {
                "required_fields": ["id", "preferences", "history", "demographics"],
                "optional_fields": ["friends", "followedCategories", "explicitRatings"]
            }
        }
        
        return requirements.get(data_type, {
            "required_fields": ["id", "name", "category", "features"],
            "optional_fields": ["description", "metadata"]
        })
    
    def run_task(self, task_description: str) -> Union[str, Dict[str, Any]]:
        """
        작업 실행 (호환성을 위한 메서드)
        
        Args:
            task_description: 작업 설명
            
        Returns:
            Union[str, Dict[str, Any]]: 작업 결과
        """
        return self._run({"task": task_description, "type": "general_ai"})

# 테스트 코드
if __name__ == "__main__":
    # Ollama 기반 AI Engineer Agent 초기화
    agent = AIEngineerAgentOllama(model="llama3.2:latest")
    
    # 텍스트 완성 서비스 생성 테스트
    text_service = agent.create_text_completion_service("openai")
    print("=== 텍스트 완성 서비스 경로 ===")
    print(text_service["service_path"])
    
    # 이미지 처리 서비스 생성 테스트
    image_service = agent.create_image_processing_service("generation")
    print("\n=== 이미지 생성 서비스 경로 ===")
    print(image_service["service_path"]) 