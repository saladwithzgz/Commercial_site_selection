"""
配置加载模块
负责加载评分规则和系统配置
"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = None):
        # 默认配置文件路径
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "scoring_rules.json"
        self.config_path = config_path
        self._config = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置（懒加载）"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Dict[str, Any]:
        """加载JSON配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def get_dimensions(self) -> Dict[str, Any]:
        """获取评分维度"""
        return self.config.get("dimensions", {})
    
    def get_ratings(self) -> list:
        """获取评级标准"""
        return self.config.get("ratings", [])
    
    def get_rating_label(self, score: int) -> str:
        """根据总分获取评级标签"""
        for rating in self.get_ratings():
            if "min" in rating and score >= rating["min"]:
                return rating["label"]
            elif "max" in rating and score <= rating["max"]:
                return rating["label"]
        return "未知"
    
    def get_dimension_weight(self, dimension_name: str) -> int:
        """获取维度权重"""
        dimensions = self.get_dimensions()
        return dimensions.get(dimension_name, {}).get("weight", 0)
