"""
模型配置模块
统一管理不同 API 提供商的模型配置
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class SimpleLanguageModel:
    """简化的语言模型基类"""
    
    def __init__(self, provider: str, model_name: str, api_key: str, base_url: str = None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
    
    def invoke(self, messages):
        """调用模型，返回响应"""
        if hasattr(messages[0], 'content'):
            content = messages[0].content
        else:
            content = str(messages[0])
        
        if self.provider == "openai" or self.provider == "kimi":
            return self._call_openai_api(content)
        elif self.provider == "anthropic":
            return self._call_anthropic_api(content)
        elif self.provider == "zhipu":
            return self._call_zhipu_api(content)
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _call_openai_api(self, content: str):
        """调用 OpenAI 兼容的 API"""
        try:
            import openai
            
            if self.base_url:
                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            else:
                client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": content}],
                temperature=0.1
            )
            
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            return MockResponse(response.choices[0].message.content)
            
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")
        except Exception as e:
            raise RuntimeError(f"API 调用失败: {e}")
    
    def _call_anthropic_api(self, content: str):
        """调用 Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                messages=[{"role": "user", "content": content}]
            )
            
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            return MockResponse(response.content[0].text)
            
        except ImportError:
            raise ImportError("请安装 anthropic 包: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic API 调用失败: {e}")
    
    def _call_zhipu_api(self, content: str):
        """调用智谱 AI API"""
        try:
            import zhipuai
            
            client = zhipuai.ZhipuAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": content}],
                temperature=0.1
            )
            
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            return MockResponse(response.choices[0].message.content)
            
        except ImportError:
            raise ImportError("请安装 zhipuai 包: pip install zhipuai")
        except Exception as e:
            raise RuntimeError(f"智谱 AI API 调用失败: {e}")


class ModelConfig:
    """模型配置管理器"""
    
    @staticmethod
    def get_model() -> SimpleLanguageModel:
        """根据环境变量获取对应的模型实例"""
        provider = os.getenv("MODEL_PROVIDER", "openai").lower()
        model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        
        if provider == "openai":
            return SimpleLanguageModel(
                provider="openai",
                model_name=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )
        
        elif provider == "anthropic":
            return SimpleLanguageModel(
                provider="anthropic",
                model_name=model_name,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        
        elif provider == "zhipu":
            return SimpleLanguageModel(
                provider="zhipu",
                model_name=model_name,
                api_key=os.getenv("ZHIPU_API_KEY")
            )
        
        elif provider == "kimi":
            return SimpleLanguageModel(
                provider="kimi",
                model_name=model_name,
                api_key=os.getenv("KIMI_API_KEY"),
                base_url=os.getenv("KIMI_BASE_URL")
            )
        
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
