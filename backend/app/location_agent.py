"""
选址分析Agent模块
负责协调整个分析流程：信息提取 → 数据采集 → 评分计算 → 报告生成
使用DeepSeek API进行智能信息提取
"""
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config_loader import ConfigLoader
from .mcp_client import MCPServiceManager, LocationData
from .scoring_engine import ScoringEngine
from .deepseek_client import DeepSeekClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocationAnalysisAgent:
    """选址分析Agent"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.mcp_manager = MCPServiceManager()
        self.scoring_engine = ScoringEngine(self.config_loader)
        self.deepseek_client = DeepSeekClient()
        logger.info("选址分析Agent初始化完成")
    
    async def extract_addresses(self, user_input: str) -> List[str]:
        """从用户输入中提取候选地址（优先使用DeepSeek）"""
        if self.deepseek_client.is_configured():
            logger.info("使用DeepSeek API提取地址")
            addresses = await self.deepseek_client.extract_addresses(user_input)
            if addresses:
                return addresses
        
        logger.info("使用本地规则提取地址（DeepSeek未配置或失败）")
        return self._extract_addresses_local(user_input)
    
    def _extract_addresses_local(self, user_input: str) -> List[str]:
        """本地规则提取候选地址（备用方案）"""
        patterns = [
            r'([\u4e00-\u9fa5]+(?:区|县)[\u4e00-\u9fa5]+(?:地铁站|太古里|大悦城|商场|购物中心|附近|街|路))',
            r'([\u4e00-\u9fa5]+(?:地铁站|太古里|大悦城)附近?)',
            r'((?:北京|上海|广州|深圳)[\u4e00-\u9fa5]+)',
        ]
        
        addresses = []
        for pattern in patterns:
            matches = re.findall(pattern, user_input)
            addresses.extend(matches)
        
        seen = set()
        unique_addresses = []
        for addr in addresses:
            if addr not in seen:
                seen.add(addr)
                unique_addresses.append(addr)
        
        return unique_addresses
    
    async def extract_store_type(self, user_input: str) -> str:
        """提取店铺类型（优先使用DeepSeek）"""
        if self.deepseek_client.is_configured():
            info = await self.deepseek_client.extract_store_info(user_input)
            return info.get("store_type", "奶茶店")
        
        return self._extract_store_type_local(user_input)
    
    def _extract_store_type_local(self, user_input: str) -> str:
        """本地规则提取店铺类型（备用方案）"""
        store_types = ["奶茶店", "咖啡店", "便利店", "餐厅", "面包店"]
        for store_type in store_types:
            if store_type in user_input:
                return store_type
        return "奶茶店"
    
    async def extract_brand_positioning(self, user_input: str) -> Optional[str]:
        """提取品牌定位（优先使用DeepSeek）"""
        if self.deepseek_client.is_configured():
            info = await self.deepseek_client.extract_store_info(user_input)
            return info.get("brand_positioning")
        
        return self._extract_brand_positioning_local(user_input)
    
    def _extract_brand_positioning_local(self, user_input: str) -> Optional[str]:
        """本地规则提取品牌定位（备用方案）"""
        positioning_map = {
            "高端": "高端精品",
            "平价": "学生平价",
            "白领": "白领商务",
            "精品": "高端精品",
            "学生": "学生平价",
            "商务": "白领商务"
        }
        for keyword, positioning in positioning_map.items():
            if keyword in user_input:
                return positioning
        return None
    
    async def analyze(self, user_input: str) -> Dict[str, Any]:
        """分析选址"""
        logger.info(f"开始分析，用户输入: {user_input}")
        
        # 第一阶段：信息提取（使用DeepSeek API）
        addresses = await self.extract_addresses(user_input)
        store_type = await self.extract_store_type(user_input)
        brand_positioning = await self.extract_brand_positioning(user_input)
        
        if not addresses:
            return {
                "status": "error",
                "message": "未能从输入中识别到候选地址，请明确提供地址列表"
            }
        
        logger.info(f"提取到地址: {addresses}")
        
        # 第二阶段：数据采集（使用MCP服务）
        location_data_list = []
        for address in addresses:
            location_data = await self.mcp_manager.collect_location_data(address)
            location_data_list.append(location_data)
        
        # 第三阶段：评分计算
        scored_results = self.scoring_engine.score_multiple(location_data_list)
        
        # 第四阶段：生成报告
        report = self._generate_report(
            user_input, addresses, store_type, brand_positioning, scored_results
        )
        
        # 第五阶段：保存JSON
        self._save_result_json(scored_results, store_type)
        
        return report
    
    def _generate_report(
        self,
        user_input: str,
        addresses: List[str],
        store_type: str,
        brand_positioning: Optional[str],
        scored_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成完整分析报告"""
        timestamp = datetime.now().isoformat()
        data_source = scored_results[0].get("data_source", "未知") if scored_results else "未知"
        
        report = {
            "status": "success",
            "analysis_metadata": {
                "timestamp": timestamp,
                "user_input": user_input,
                "store_type": store_type,
                "brand_positioning": brand_positioning or "未指定",
                "total_candidates": len(addresses),
                "data_source": data_source,
                "agent_mode": "DeepSeek API" if self.deepseek_client.is_configured() else "本地规则"
            },
            "results": scored_results,
            "recommendation": self._generate_recommendation(scored_results),
            "summary_table": self._generate_summary_table(scored_results)
        }
        
        return report
    
    def _generate_recommendation(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成推荐结论"""
        if not scored_results:
            return {}
        
        best = scored_results[0]
        second = scored_results[1] if len(scored_results) > 1 else None
        
        recommendation = {
            "primary": {
                "address": best["address"],
                "score": best["total_score"],
                "rating": best["rating"],
                "reason": self._get_recommendation_reason(best)
            }
        }
        
        if second:
            recommendation["secondary"] = {
                "address": second["address"],
                "score": second["total_score"],
                "rating": second["rating"],
                "difference": f"较首选低{best['total_score'] - second['total_score']}分"
            }
        
        return recommendation
    
    def _get_recommendation_reason(self, result: Dict[str, Any]) -> str:
        """生成推荐理由"""
        details = result["details"]
        scores = result["scores"]
        reasons = []
        
        if scores["transportation"] >= 20:
            reasons.append(f"交通便利（距{details['nearest_metro']}{details['metro_distance']}米）")
        
        if details["school_count"] > 0:
            reasons.append(f"学生客群丰富（{details['school_count']}所学校）")
        
        if details["office_count"] > 5:
            reasons.append(f"写字楼密集（{details['office_count']}栋）")
        
        if details["is_restaurant_zone"]:
            reasons.append("处于成熟餐饮聚集区")
        
        return "；".join(reasons) if reasons else "综合评分较高"
    
    def _generate_summary_table(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成汇总表"""
        table = []
        for result in scored_results:
            table.append({
                "rank": result["rank"],
                "address": result["address"],
                "competitor_density": f"{result['scores']['competitor_density']}/30",
                "transportation": f"{result['scores']['transportation']}/25",
                "customer_flow": f"{result['scores']['customer_flow']}/25",
                "surrounding_facilities": f"{result['scores']['surrounding_facilities']}/20",
                "total_score": result["total_score"],
                "rating": result["rating"]
            })
        return table
    
    def _save_result_json(self, scored_results: List[Dict[str, Any]], store_type: str):
        """保存结果到JSON文件"""
        try:
            result_dir = Path(__file__).parent.parent.parent / "result"
            result_dir.mkdir(exist_ok=True)
            
            output_path = result_dir / "milk_tea_location_selection.json"
            
            data = {
                "analysis_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "store_type": store_type,
                    "total_candidates": len(scored_results),
                    "data_source": scored_results[0].get("data_source", "未知") if scored_results else "未知",
                    "agent_mode": "DeepSeek API" if self.deepseek_client.is_configured() else "本地规则"
                },
                "results": scored_results
            }
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
