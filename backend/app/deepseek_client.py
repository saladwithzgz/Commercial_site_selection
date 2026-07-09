"""
DeepSeek API客户端模块
封装DeepSeek大模型API的调用逻辑
支持从.env文件读取配置
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("已加载.env配置文件")
except ImportError:
    pass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.timeout = int(os.environ.get("DEEPSEEK_TIMEOUT", 30))
        self.temperature = float(os.environ.get("DEEPSEEK_TEMPERATURE", 0.7))
        self.max_tokens = int(os.environ.get("DEEPSEEK_MAX_TOKENS", 4000))
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        
        if not self.api_key:
            logger.warning("未配置DeepSeek API密钥，请设置环境变量DEEPSEEK_API_KEY或在.env文件中配置")
        else:
            logger.info(f"DeepSeek客户端已初始化，模型: {self.model}")
    
    def is_configured(self) -> bool:
        """检查API密钥是否已配置"""
        return bool(self.api_key)
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取当前配置信息（不包含密钥）"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "configured": self.is_configured()
        }
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """调用DeepSeek聊天完成API"""
        if not self.api_key:
            logger.error("DeepSeek API密钥未配置")
            return None
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API调用失败: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
                    if result.get("choices"):
                        content = result["choices"][0]["message"]["content"]
                        return content
                    return None
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {e}")
            return None
    
    async def extract_addresses(self, user_input: str) -> List[str]:
        """使用DeepSeek提取候选地址"""
        addresses, _ = await self.extract_addresses_with_city(user_input)
        return addresses
    
    async def extract_addresses_with_city(self, user_input: str) -> Tuple[List[str], str]:
        """使用DeepSeek提取候选地址和城市"""
        system_prompt = """你是一个地址提取专家。请从用户输入中提取出所有候选地址和所在城市。

要求：
1. 返回JSON格式
2. "city"字段为城市名称（如北京、上海、广州等）
3. "addresses"字段为地址列表，每个地址占一个元素
4. 如果没有找到城市，city字段返回空字符串""

请以JSON格式返回，格式如下：
{
    "city": "北京",
    "addresses": ["朝阳区三里屯太古里", "海淀区五道口地铁站附近"]
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.chat_completion(messages, temperature=0.1)
        
        if not response:
            return [], ""
        
        try:
            result = json.loads(response)
            return result.get("addresses", []), result.get("city", "")
        except json.JSONDecodeError:
            return [], ""
    
    async def extract_store_info(self, user_input: str) -> Dict[str, Any]:
        """使用DeepSeek提取店铺信息"""
        system_prompt = """你是一个商业分析专家。请从用户输入中提取以下信息：

1. store_type: 店铺类型（奶茶店、咖啡店、便利店、餐厅、面包店等），如果未提及默认为"奶茶店"
2. brand_positioning: 品牌定位（高端精品、学生平价、白领商务），如果未提及返回null

请以JSON格式返回，格式如下：
{
    "store_type": "奶茶店",
    "brand_positioning": "高端精品"
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.chat_completion(messages, temperature=0.1)
        
        if not response:
            return {"store_type": "奶茶店", "brand_positioning": None}
        
        try:
            result = json.loads(response)
            return {
                "store_type": result.get("store_type", "奶茶店"),
                "brand_positioning": result.get("brand_positioning")
            }
        except json.JSONDecodeError:
            return {"store_type": "奶茶店", "brand_positioning": None}


import re
