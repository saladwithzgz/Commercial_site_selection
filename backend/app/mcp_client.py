"""
MCP服务客户端模块
封装高德地图和百度地图MCP的调用逻辑
提供统一的接口和容错机制
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LocationData:
    """地址数据结构"""
    address: str
    coordinates: Dict[str, float] = field(default_factory=dict)
    competitor_count: int = 0
    competitor_list: List[str] = field(default_factory=list)
    nearest_metro: str = ""
    metro_distance: int = 0
    office_count: int = 0
    office_list: List[str] = field(default_factory=list)
    school_count: int = 0
    school_list: List[str] = field(default_factory=list)
    mall_count: int = 0
    mall_list: List[str] = field(default_factory=list)
    has_convenience_store: bool = False
    is_restaurant_zone: bool = False
    data_source: str = ""


class AmapMCPClient:
    """高德地图MCP客户端（模拟）"""
    
    SERVICE_NAME = "高德地图MCP"
    
    def __init__(self):
        self.available = True
    
    async def geocode(self, address: str, city: str = "北京") -> Optional[Dict[str, float]]:
        """地理编码"""
        # 模拟返回（实际应调用MCP）
        # 此处应该是真正的MCP调用，但作为后端，我们可以使用HTTP API或调用本地MCP服务
        mock_data = {
            "海淀区五道口地铁站附近": {"lng": 116.337742, "lat": 39.992894},
            "朝阳区三里屯太古里": {"lng": 116.453990, "lat": 39.934871},
            "西城区西单大悦城附近": {"lng": 116.372960, "lat": 39.910884},
        }
        return mock_data.get(address)
    
    async def around_search(self, location: str, keywords: str, radius: int = 500) -> List[Dict]:
        """周边搜索"""
        # 模拟返回
        return []
    
    def is_available(self) -> bool:
        return self.available


class BaiduMCPClient:
    """百度地图MCP客户端（模拟）"""
    
    SERVICE_NAME = "百度地图MCP"
    
    def __init__(self):
        self.available = False  # 当前不可用
    
    def is_available(self) -> bool:
        return self.available


class MCPServiceManager:
    """MCP服务管理器 - 提供容错和切换机制"""
    
    def __init__(self):
        self.amap_client = AmapMCPClient()
        self.baidu_client = BaiduMCPClient()
        self.primary_service = "baidu"  # 首选服务
        self.fallback_service = "amap"  # 备用服务
        logger.info("MCP服务管理器初始化完成")
    
    async def geocode(self, address: str, city: str = "北京") -> Tuple[Optional[Dict[str, float]], str]:
        """地理编码（带容错）"""
        # 尝试首选服务
        if self.primary_service == "baidu" and self.baidu_client.is_available():
            result = await self._baidu_geocode(address, city)
            if result:
                return result, BaiduMCPClient.SERVICE_NAME
        
        # 切换到备用服务
        if self.amap_client.is_available():
            result = await self.amap_client.geocode(address, city)
            if result:
                return result, AmapMCPClient.SERVICE_NAME
        
        # 全部失败，返回预设数据
        return self._get_fallback_coordinates(address), "预设规则"
    
    async def _baidu_geocode(self, address: str, city: str) -> Optional[Dict[str, float]]:
        """百度地图地理编码"""
        try:
            # 实际调用百度MCP
            # result = await baidu_mcp.geocode(address=address, city=city)
            # return {"lng": result["lng"], "lat": result["lat"]}
            return None  # 当前不可用
        except Exception as e:
            logger.warning(f"百度地图MCP调用失败: {e}")
            return None
    
    def _get_fallback_coordinates(self, address: str) -> Dict[str, float]:
        """获取预设坐标（兜底方案）"""
        fallback = {
            "海淀区五道口地铁站附近": {"lng": 116.337742, "lat": 39.992894},
            "朝阳区三里屯太古里": {"lng": 116.453990, "lat": 39.934871},
            "西城区西单大悦城附近": {"lng": 116.372960, "lat": 39.910884},
        }
        # 模糊匹配
        for key, coords in fallback.items():
            if key in address or address in key:
                return coords
        # 默认返回北京中心
        return {"lng": 116.397428, "lat": 39.90923}
    
    async def collect_location_data(self, address: str) -> LocationData:
        """采集地址的完整数据"""
        logger.info(f"开始采集地址数据: {address}")
        
        # 1. 地理编码
        coords, data_source = await self.geocode(address)
        
        if coords is None:
            logger.error(f"无法获取坐标: {address}")
            return LocationData(address=address, data_source="失败")
        
        # 2. 周边搜索（模拟数据，实际应调用MCP）
        location_data = LocationData(
            address=address,
            coordinates=coords,
            data_source=data_source
        )
        
        # 模拟周边数据采集
        await self._collect_competitor_data(location_data)
        await self._collect_transportation_data(location_data)
        await self._collect_customer_flow_data(location_data)
        await self._collect_facilities_data(location_data)
        
        logger.info(f"地址数据采集完成: {address} (来源: {data_source})")
        return location_data
    
    async def _collect_competitor_data(self, location_data: LocationData):
        """采集竞品数据"""
        # 模拟数据
        mock_competitors = {
            "海淀区五道口地铁站附近": {
                "count": 18,
                "list": ["CoCo都可", "蜜雪冰城", "茶百道", "喜茶", "霸王茶姬"]
            },
            "朝阳区三里屯太古里": {
                "count": 20,
                "list": ["阿嬷手作", "喜茶", "1点点", "茶百道", "蜜雪冰城"]
            },
            "西城区西单大悦城附近": {
                "count": 21,
                "list": ["奈雪的茶", "乐乐茶", "兰熊鲜奶", "喜茶", "蜜雪冰城"]
            }
        }
        for key, data in mock_competitors.items():
            if key in location_data.address:
                location_data.competitor_count = data["count"]
                location_data.competitor_list = data["list"]
                break
    
    async def _collect_transportation_data(self, location_data: LocationData):
        """采集交通数据"""
        mock_metro = {
            "海淀区五道口地铁站附近": {"name": "五道口站", "distance": 50},
            "朝阳区三里屯太古里": {"name": "工人体育场站", "distance": 300},
            "西城区西单大悦城附近": {"name": "西单站", "distance": 100}
        }
        for key, data in mock_metro.items():
            if key in location_data.address:
                location_data.nearest_metro = data["name"]
                location_data.metro_distance = data["distance"]
                break
    
    async def _collect_customer_flow_data(self, location_data: LocationData):
        """采集客流数据"""
        mock_flow = {
            "海淀区五道口地铁站附近": {
                "office": 20, "office_list": ["东源大厦", "优盛大厦"],
                "school": 5, "school_list": ["清华大学", "北京大学"],
                "mall": 2, "mall_list": ["五道口购物中心"]
            },
            "朝阳区三里屯太古里": {
                "office": 8, "office_list": ["三里屯SOHO"],
                "school": 0, "school_list": [],
                "mall": 3, "mall_list": ["三里屯太古里"]
            },
            "西城区西单大悦城附近": {
                "office": 3, "office_list": ["通港大厦"],
                "school": 0, "school_list": [],
                "mall": 5, "mall_list": ["西单大悦城", "君太百货"]
            }
        }
        for key, data in mock_flow.items():
            if key in location_data.address:
                location_data.office_count = data["office"]
                location_data.office_list = data["office_list"]
                location_data.school_count = data["school"]
                location_data.school_list = data["school_list"]
                location_data.mall_count = data["mall"]
                location_data.mall_list = data["mall_list"]
                break
    
    async def _collect_facilities_data(self, location_data: LocationData):
        """采集配套设施数据"""
        mock_facilities = {
            "海淀区五道口地铁站附近": {"convenience": True, "restaurant_zone": True},
            "朝阳区三里屯太古里": {"convenience": True, "restaurant_zone": True},
            "西城区西单大悦城附近": {"convenience": True, "restaurant_zone": False}
        }
        for key, data in mock_facilities.items():
            if key in location_data.address:
                location_data.has_convenience_store = data["convenience"]
                location_data.is_restaurant_zone = data["restaurant_zone"]
                break
