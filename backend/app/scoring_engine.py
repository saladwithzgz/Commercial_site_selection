"""
评分引擎模块
根据评分规则对候选地址进行量化评分
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field
from .config_loader import ConfigLoader
from .mcp_client import LocationData


@dataclass
class ScoreResult:
    """评分结果"""
    competitor_density: int = 0
    transportation: int = 0
    customer_flow: int = 0
    surrounding_facilities: int = 0
    total_score: int = 0
    rating: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "competitor_density": self.competitor_density,
            "transportation": self.transportation,
            "customer_flow": self.customer_flow,
            "surrounding_facilities": self.surrounding_facilities,
            "total_score": self.total_score,
            "rating": self.rating
        }


class ScoringEngine:
    """评分引擎"""
    
    def __init__(self, config_loader: ConfigLoader = None):
        self.config_loader = config_loader or ConfigLoader()
    
    def score_competitor_density(self, competitor_count: int) -> int:
        """竞品密度评分（满分30分）"""
        dimensions = self.config_loader.get_dimensions()
        rules = dimensions.get("竞品密度", {}).get("rules", [])
        
        for rule in rules:
            range_min, range_max = rule["range"]
            if range_max is None:
                if competitor_count >= range_min:
                    return rule["score"]
            elif range_min <= competitor_count <= range_max:
                return rule["score"]
        return 0
    
    def score_transportation(self, metro_distance: int) -> int:
        """交通便利性评分（满分25分）"""
        dimensions = self.config_loader.get_dimensions()
        rules = dimensions.get("交通便利性", {}).get("rules", [])
        
        for rule in rules:
            range_min, range_max = rule["range"]
            if range_max is None:
                if metro_distance >= range_min:
                    return rule["score"]
            elif range_min <= metro_distance <= range_max:
                return rule["score"]
        return 0
    
    def score_customer_flow(self, office_count: int, school_count: int, mall_count: int) -> int:
        """客流来源评分（满分25分）"""
        dimensions = self.config_loader.get_dimensions()
        flow_config = dimensions.get("客流来源", {})
        
        base_score = 0
        # 有写字楼或商场
        if office_count > 0 or mall_count > 0:
            base_score += flow_config.get("has_office_mall", 15)
        # 有学校
        if school_count > 0:
            base_score += flow_config.get("has_school", 10)
        
        # 限制最大分
        max_score = flow_config.get("max_score", 25)
        return min(base_score, max_score)
    
    def score_surrounding_facilities(self, has_convenience_store: bool, is_restaurant_zone: bool) -> int:
        """周边配套评分（满分20分）"""
        dimensions = self.config_loader.get_dimensions()
        facilities_config = dimensions.get("周边配套", {})
        
        base_score = 0
        # 处于餐饮聚集区
        if is_restaurant_zone:
            base_score += facilities_config.get("has_restaurant_zone", 10)
        # 有便利店
        if has_convenience_store:
            base_score += facilities_config.get("has_convenience_store", 10)
        
        return min(base_score, 20)
    
    def calculate_total_score(self, location_data: LocationData) -> ScoreResult:
        """计算总分"""
        # 各维度评分
        competitor_score = self.score_competitor_density(location_data.competitor_count)
        transport_score = self.score_transportation(location_data.metro_distance)
        flow_score = self.score_customer_flow(
            location_data.office_count,
            location_data.school_count,
            location_data.mall_count
        )
        facilities_score = self.score_surrounding_facilities(
            location_data.has_convenience_store,
            location_data.is_restaurant_zone
        )
        
        # 总分
        total_score = competitor_score + transport_score + flow_score + facilities_score
        
        # 评级
        rating = self.config_loader.get_rating_label(total_score)
        
        return ScoreResult(
            competitor_density=competitor_score,
            transportation=transport_score,
            customer_flow=flow_score,
            surrounding_facilities=facilities_score,
            total_score=total_score,
            rating=rating
        )
    
    def score_multiple(self, location_data_list: List[LocationData]) -> List[Dict[str, Any]]:
        """批量评分并排名"""
        results = []
        for location_data in location_data_list:
            score_result = self.calculate_total_score(location_data)
            
            result = {
                "address": location_data.address,
                "coordinates": location_data.coordinates,
                "scores": score_result.to_dict(),
                "total_score": score_result.total_score,
                "rating": score_result.rating,
                "details": {
                    "competitor_count": location_data.competitor_count,
                    "competitor_list": location_data.competitor_list,
                    "nearest_metro": location_data.nearest_metro,
                    "metro_distance": location_data.metro_distance,
                    "office_count": location_data.office_count,
                    "office_list": location_data.office_list,
                    "school_count": location_data.school_count,
                    "school_list": location_data.school_list,
                    "mall_count": location_data.mall_count,
                    "mall_list": location_data.mall_list,
                    "has_convenience_store": location_data.has_convenience_store,
                    "is_restaurant_zone": location_data.is_restaurant_zone
                },
                "data_source": location_data.data_source
            }
            results.append(result)
        
        # 按总分降序排名
        results.sort(key=lambda x: x["total_score"], reverse=True)
        
        # 添加排名
        for rank, result in enumerate(results, 1):
            result["rank"] = rank
        
        return results
