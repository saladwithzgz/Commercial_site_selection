"""
DeepSeek API客户端模块
封装DeepSeek大模型API的调用逻辑
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        
        if not self.api_key:
            logger.warning("未配置DeepSeek API密钥，请设置环境变量DEEPSEEK_API_KEY")
    
    def is_configured(self) -> bool:
        """检查API密钥是否已配置"""
        return bool(self.api_key)
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """调用DeepSeek聊天完成API"""
        if not self.api_key:
            logger.error("DeepSeek API密钥未配置")
            return None
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000)
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
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
        system_prompt = """你是一个地址提取专家。请从用户输入中提取出所有候选地址。

要求：
1. 只提取具体的地址名称，不要包含其他内容
2. 每个地址占一行
3. 如果没有找到地址，返回空列表
4. 不要添加编号或标记，直接输出地址名称

示例输入：
"我想在北京开一家奶茶店，候选地址：朝阳区三里屯太古里、海淀区五道口地铁站附近、西城区西单大悦城附近"

示例输出：
朝阳区三里屯太古里
海淀区五道口地铁站附近
西城区西单大悦城附近"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.chat_completion(messages, temperature=0.1)
        
        if not response:
            return []
        
        addresses = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # 去除可能的编号前缀
                clean_line = re.sub(r'^\d+[\.、]\s*', '', line)
                clean_line = re.sub(r'^[-*]\s*', '', clean_line)
                if clean_line:
                    addresses.append(clean_line)
        
        return addresses
    
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


# 添加re导入（之前遗漏了）
import re
