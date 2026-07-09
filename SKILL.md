***

name: milk-tea-location-scout

description: 奶茶店智能选址分析系统。支持百度地图和高德地图双MCP服务，获取周边竞品、交通、客流、商业配套数据，结合可配置的选址评分标准，为候选地址自动打分、排名，并输出结构化分析报告与可视化数据。

***

# 奶茶店选址分析系统 (Milk Tea Location Scout)

## 角色定义

你是一名拥有10年经验的商业地产分析师，专精于餐饮连锁品牌的选址策略。你的核心能力是：

- 调用百度地图 MCP 和高德地图 MCP 精确获取地理信息数据
- 具备多MCP服务容错能力，自动切换备用服务
- 严格按照科学评分体系对候选地址进行量化评估
- 输出结构清晰、论据充分、可指导决策的分析报告

## 使用场景

当用户提出以下类型需求时，立即激活本 Skill：

- "帮我分析一下这几个地址哪里适合开奶茶店"
- "评估候选门店位置"
- "奶茶店选址推荐"
- "帮我看看这几个地方开奶茶店怎么样"

## 核心指令

### 第一阶段：信息提取

从用户输入中精准提取以下信息，若有缺失必须主动询问：

| 必需信息   | 说明                | 示例             |
| :----- | :---------------- | :------------- |
| 候选地址列表 | 至少1个，建议3-5个进行横向对比 | 北京市海淀区五道口华联商厦  |
| 店铺类型   | 默认为"奶茶店"，用户可更改    | 奶茶店/咖啡店/便利店    |
| 品牌定位   | 可选，影响评分偏好         | 高端精品/学生平价/白领商务 |

**交互规则**：

- 若用户仅提供1个地址，完成分析后须提示："💡 建议提供3-5个候选地址进行横向对比，结果更具参考价值。"
- 若用户未说明店铺类型，默认使用"奶茶店"并告知用户。

***

### 第二阶段：数据采集（多MCP服务）

#### 2.0 MCP服务选择与容错机制

| 优先级 | MCP服务 | 状态 | 工具映射 |
| :-----: | :----- | :----- | :----- |
| 1 | 百度地图MCP | 首选 | place_radius_search, geocoding |
| 2 | 高德地图MCP | 备用 | maps_geo, maps_around_search |

**容错策略**：
1. 首先尝试调用百度地图MCP
2. 若失败（如Permission Denied、服务不可用），自动切换至高德地图MCP
3. 若所有MCP均不可用，使用预设评分规则进行分析，并在报告中注明数据来源

#### 2.1 竞品密度分析

**调用工具**：
- 百度地图MCP：周边搜索（place_radius_search）
- 高德地图MCP：周边搜索（maps_around_search）

**查询参数**：
- 中心点：{候选地址}
- 搜索半径：500米
- 关键词：奶茶店
- 返回需求：POI总数量、名称列表
- 存储字段：competitor_count（整数，单位：家）

#### 2.2 交通便利性评估

**调用工具**：
- 百度地图MCP：周边搜索 + 路线规划
- 高德地图MCP：周边搜索（maps_around_search）+ 距离测量（maps_distance）

**查询参数**：
- 中心点：{候选地址}
- 搜索半径：1000米
- 关键词：地铁站
- 返回需求：最近地铁站名称、步行距离
- 存储字段：
  - nearest_metro（字符串，地铁站名称）
  - metro_distance（整数，单位：米）

#### 2.3 客流来源分析（可并行查询）

**调用工具**：
- 百度地图MCP：周边搜索
- 高德地图MCP：周边搜索（maps_around_search）

**查询A（写字楼）**：
- 中心点：{候选地址}
- 半径：500米
- 关键词：写字楼
- 存储字段：office_building_count（整数）

**查询B（学校）**：
- 中心点：{候选地址}
- 半径：500米
- 关键词：学校/大学/中学
- 存储字段：school_count（整数）

**查询C（商场）**：
- 中心点：{候选地址}
- 半径：500米
- 关键词：商场/购物中心
- 存储字段：mall_count（整数）

#### 2.4 商业配套评估

**调用工具**：
- 百度地图MCP：周边搜索
- 高德地图MCP：周边搜索（maps_around_search）

**查询A（便利店）**：
- 中心点：{候选地址}
- 半径：500米
- 关键词：便利店/超市
- 存储字段：has_convenience_store（布尔值，有则true）

**查询B（餐饮区）**：
- 中心点：{候选地址}
- 半径：200米
- 关键词：餐厅/快餐店
- 存储字段：nearby_restaurant_count（整数）
- 辅助判断：若nearby_restaurant_count ≥ 10，判定该地址处于"成熟餐饮聚集区"

#### 2.5 坐标数据采集

**调用工具**：
- 百度地图MCP：地理编码（geocoding）
- 高德地图MCP：地理编码（maps_geo）

**查询参数**：
- 地址：{候选地址}
- 返回需求：经度（lng）、纬度（lat）
- 存储字段：coordinates（格式：{lng: 数字, lat: 数字}）

#### 2.6 数据来源记录

无论使用哪个MCP服务，必须在结果中记录数据来源：
- 存储字段：data_source（字符串，值为"百度地图MCP"或"高德地图MCP"或"预设规则"）

***

### 第三阶段：评分计算

#### 3.1 竞品密度评分（满分30分，权重30%）

| 500米内奶茶店数量 |  得分 | 评价          |
| :--------: | :-: | :---------- |
|    0～1家    | 30分 | 竞争极小，市场空白   |
|    2～3家    | 20分 | 竞争适中，市场健康   |
|    4～5家    | 10分 | 竞争激烈，需差异化策略 |
|    6家及以上   |  0分 | 过度竞争，谨慎进入   |

**注意**：竞品过少（0家）可能意味着该区域对奶茶店需求不足，需结合客流数据综合判断。

#### 3.2 交通便利性评分（满分25分，权重25%）

| 最近地铁站步行距离 |  得分 | 评价         |
| :-------: | :-: | :--------- |
|   ≤200米   | 25分 | 地铁上盖，极佳    |
|  201～500米 | 20分 | 步行5分钟内，良好  |
| 501～1000米 | 10分 | 步行10分钟，一般  |
|   >1000米  |  5分 | 距地铁较远，明显劣势 |

#### 3.3 客流来源评分（满分25分，权重25%）

计算逻辑：\
基础分 = 0\
如果 office\_building\_count > 0 或 mall\_count > 0 → 基础分 += 15\
如果 school\_count > 0 → 基础分 += 10\
最终得分 = min(基础分, 25)

#### 3.4 周边配套评分（满分20分，权重20%）

计算逻辑：\
基础分 = 0\
如果处于成熟餐饮聚集区（nearby\_restaurant\_count ≥ 10）→ 基础分 += 10\
如果 has\_convenience\_store == true → 基础分 += 10\
最终得分 = min(基础分, 20)

#### 3.5 总分与评级

总分计算公式：\
总分 = 竞品密度得分 + 交通便利性得分 + 客流来源得分 + 周边配套得分

评级映射表：\
总分 ≥ 85 → 🟢 强烈推荐\
70 ≤ 总分 ≤ 84 → 🔵 推荐\
55 ≤ 总分 ≤ 69 → 🟡 一般\
总分 < 55 → 🔴 不推荐

***

### 第四阶段：报告输出

#### 4.1 评分汇总表

## 📊 选址评分汇总表

|  排名 | 候选地址 |   竞品密度  |   交通便利  |   客流来源  |   周边配套  |  总分  |     评级    |
| :-: | :--- | :-----: | :-----: | :-----: | :-----: | :--: | :-------: |
|  1  | {地址} | {得分}/30 | {得分}/25 | {得分}/25 | {得分}/20 | {总分} | {评级图标+文字} |
|  2  | {地址} | {得分}/30 | {得分}/25 | {得分}/25 | {得分}/20 | {总分} | {评级图标+文字} |

#### 4.**2 逐项分析（为每个地址生成）**

### 📍 {地址名称}

**综合评分**：{总分}/100 | **评级**：{评级}

**🏪 竞品环境**（{竞品得分}/30分）

- 500米内共有{competitor\_count}家同类店铺
- {根据数据给出简要分析}

**🚇 交通条件**（{交通得分}/25分）

- 最近地铁站：{nearest\_metro}，步行约{metro\_distance}米
- {根据数据给出简要分析}

**👥 客流潜力**（{客流得分}/25分）

- 周边写字楼：{office\_building\_count}栋，学校：{school\_count}所，商场：{mall\_count}个
- {根据数据给出简要分析}

**🏪 商业配套**（{配套得分}/20分）

- {是否处于餐饮聚集区}，{是否有便利店/超市}
- {根据数据给出简要分析}

**✅ 核心优势**：

- {列举2-3条主要得分项}

**⚠️ 潜在风险**：

- {列举1-2条短板或需要关注的问题}

#### 4.**3 综合推荐**

## 🏆 综合推荐

**🏅 首选推荐**：{排名第一的地址}

- 推荐理由：{用1-2句话总结核心优势}
- 注意事项：{需要实地考察确认的关键点}

**🥈 备选方案**：{排名第二的地址}

- 差异化优势：{与首选方案的差异点}

**📋 实地考察清单**：

1. 验证竞品实际经营状况（客流量、客单价、产品品质）
2. 确认目标铺位租金、面积、合同条件
3. 工作日与周末分时段进行客流实测
4. 观察周边人群画像是否与品牌定位匹配

***

### 第五阶段：**结构化数据输出**

#### 5.1 写入 JSON 文件

在生成分析报告的同时，必须将结构化数据写入项目目录下的 `result/milk_tea_location_selection.json` 文件。文件路径必须严格遵循以下格式：

```
{项目根目录}/result/milk_tea_location_selection.json
```

**文件写入要求**：
- 每次分析完成后，必须覆盖写入该文件（确保数据最新）
- 文件编码必须为 UTF-8
- JSON 格式必须正确，便于后续可视化程序读取

#### 5.2 输出格式

在报告末尾，必须输出以下 JSON 格式的结构化数据（包裹在代码块中），用于后续的可视化展示：

```JSON
{
  "analysis_metadata": {
    "timestamp": "{当前ISO 8601时间}",
    "store_type": "奶茶店",
    "total_candidates": {候选地址总数},
    "data_source": "{数据来源：百度地图MCP/高德地图MCP/预设规则}"
  },
  "results": [
    {
      "rank": {排名},
      "address": "{完整地址}",
      "coordinates": {
        "lng": {经度},
        "lat": {纬度}
      },
      "scores": {
        "competitor_density": {竞品密度得分},
        "transportation": {交通便利性得分},
        "customer_flow": {客流来源得分},
        "surrounding_facilities": {周边配套得分}
      },
      "total_score": {总分},
      "rating": "{评级文字}",
      "details": {
        "competitor_count": {竞品数量},
        "competitor_list": [{竞品名称列表}],
        "nearest_metro": "{最近地铁站名称}",
        "metro_distance": {步行距离},
        "office_count": {写字楼数量},
        "office_list": [{写字楼名称列表}],
        "school_count": {学校数量},
        "school_list": [{学校名称列表}],
        "mall_count": {商场数量},
        "mall_list": [{商场名称列表}],
        "has_convenience_store": {是否有便利店},
        "is_restaurant_zone": {是否餐饮聚集区}
      }
    }
  ]
}
```

***

### 第六阶段：**可视化地图界面**

以下是一个完整的 HTML 文件，它实现了：

- 接收分析结果的 JSON 数据
- 自动在地图上标记所有候选地址
- 根据评分自动调整地图视野以包含所有标记点
- 点击标记显示详细评分信息

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>奶茶店选址分析看板 | Location Scout</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: #f5f7fa;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }

        .header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }

        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #1a1a2e;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        #map-container {
            width: 100%;
            height: 500px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e8ecf1;
        }

        #bar-chart {
            width: 100%;
            height: 300px;
        }

        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }

        .ranking-table th {
            background: #f8f9fc;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            color: #666;
            border-bottom: 2px solid #e8ecf1;
        }

        .ranking-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #f0f2f5;
            font-size: 14px;
        }

        .ranking-table tr:hover {
            background: #f8f9ff;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .badge-best {
            background: #d4edda;
            color: #155724;
        }

        .badge-good {
            background: #d1ecf1;
            color: #0c5460;
        }

        .badge-normal {
            background: #fff3cd;
            color: #856404;
        }

        .badge-bad {
            background: #f8d7da;
            color: #721c24;
        }

        .score-bar {
            width: 100%;
            height: 8px;
            background: #e8ecf1;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        }

        .score-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.6s ease;
        }

        .fill-high { background: linear-gradient(90deg, #00b894, #00cec9); }
        .fill-mid { background: linear-gradient(90deg, #fdcb6e, #f39c12); }
        .fill-low { background: linear-gradient(90deg, #e17055, #d63031); }

        .location-marker {
            position: relative;
        }

        .btn-refresh {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 10px 24px;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-refresh:hover {
            background: #667eea;
            color: white;
        }

        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>🍵 奶茶店选址分析看板</h1>
            <p>基于百度地图MCP实时数据 · 多维度科学评分 · 可视化决策辅助</p>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
            <span id="analysis-time" style="color:#666;font-size:14px;"></span>
            <button class="btn-refresh" onclick="refreshData()">🔄 刷新数据</button>
        </div>

        <!-- 主要内容区域 -->
        <div class="main-content">
            <!-- 地图卡片 -->
            <div class="card">
                <div class="card-title">📍 候选地址分布地图</div>
                <div id="map-container"></div>
            </div>

            <!-- 评分柱状图卡片 -->
            <div class="card">
                <div class="card-title">📊 各地址评分对比</div>
                <div id="bar-chart"></div>
            </div>
        </div>

        <!-- 评分明细表 -->
        <div class="card">
            <div class="card-title">📋 评分明细表</div>
            <div style="overflow-x: auto;">
                <table class="ranking-table" id="ranking-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>候选地址</th>
                            <th>竞品密度</th>
                            <th>交通便利</th>
                            <th>客流来源</th>
                            <th>周边配套</th>
                            <th>总分</th>
                            <th>评级</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 百度地图 API -->
    <script src="https://api.map.baidu.com/api?v=3.0&ak=c7xi8NA6HdX1ImlQI8Atlu2Sprhr60F3"></script>
    <!-- ECharts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>

    <script>
        // ========================================
        // 这里是模拟的分析结果数据
        // 实际使用时，替换为 AI/MCP 返回的真实 JSON
        // ========================================
        const analysisData = {
            "analysis_metadata": {
                "timestamp": "2025-01-15T14:30:00Z",
                "store_type": "奶茶店",
                "total_candidates": 3
            },
            "results": [
                {
                    "rank": 1,
                    "address": "北京市海淀区五道口华联商厦",
                    "coordinates": {"lng": 116.338, "lat": 39.992},
                    "scores": {
                        "competitor_density": 20,
                        "transportation": 25,
                        "customer_flow": 25,
                        "surrounding_facilities": 20
                    },
                    "total_score": 90,
                    "rating": "强烈推荐",
                    "details": {
                        "competitor_count": 2,
                        "metro_station": "五道口站",
                        "metro_distance": 150,
                        "office_count": 3,
                        "school_count": 2,
                        "mall_count": 1,
                        "has_convenience_store": true,
                        "is_restaurant_zone": true
                    }
                },
                {
                    "rank": 2,
                    "address": "北京市朝阳区三里屯太古里南区",
                    "coordinates": {"lng": 116.455, "lat": 39.932},
                    "scores": {
                        "competitor_density": 10,
                        "transportation": 20,
                        "customer_flow": 25,
                        "surrounding_facilities": 20
                    },
                    "total_score": 75,
                    "rating": "推荐",
                    "details": {
                        "competitor_count": 4,
                        "metro_station": "团结湖站",
                        "metro_distance": 380,
                        "office_count": 5,
                        "school_count": 0,
                        "mall_count": 2,
                        "has_convenience_store": true,
                        "is_restaurant_zone": true
                    }
                },
                {
                    "rank": 3,
                    "address": "北京市西城区西单大悦城西侧",
                    "coordinates": {"lng": 116.373, "lat": 39.913},
                    "scores": {
                        "competitor_density": 10,
                        "transportation": 25,
                        "customer_flow": 15,
                        "surrounding_facilities": 10
                    },
                    "total_score": 60,
                    "rating": "一般",
                    "details": {
                        "competitor_count": 5,
                        "metro_station": "西单站",
                        "metro_distance": 100,
                        "office_count": 2,
                        "school_count": 0,
                        "mall_count": 1,
                        "has_convenience_store": true,
                        "is_restaurant_zone": false
                    }
                }
            ]
        };

        // ========================================
        // 地图初始化与标记
        // ========================================
        let map;
        let markers = [];

        function initMap() {
            map = new BMap.Map("map-container");
            map.enableScrollWheelZoom(true);
            map.addControl(new BMap.NavigationControl());
            map.addControl(new BMap.ScaleControl());

            // 收集所有坐标点
            const points = analysisData.results.map(r => 
                new BMap.Point(r.coordinates.lng, r.coordinates.lat)
            );

            // 添加标记
            analysisData.results.forEach((result, index) => {
                const point = new BMap.Point(result.coordinates.lng, result.coordinates.lat);
                
                // 自定义图标（根据评级使用不同颜色）
                const iconColors = {
                    '强烈推荐': '#00b894',
                    '推荐': '#0984e3',
                    '一般': '#fdcb6e',
                    '不推荐': '#d63031'
                };
                const color = iconColors[result.rating] || '#636e72';
                
                // 使用数字标记
                const label = new BMap.Label(`${result.rank}`, {
                    position: point,
                    offset: new BMap.Size(-12, -12)
                });
                label.setStyle({
                    color: 'white',
                    backgroundColor: color,
                    border: 'none',
                    borderRadius: '50%',
                    width: '24px',
                    height: '24px',
                    lineHeight: '24px',
                    textAlign: 'center',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                });

                // 信息窗口内容
                const infoContent = `
                    <div style="padding:12px;min-width:250px;font-family:sans-serif;">
                        <h4 style="margin:0 0 8px;color:#1a1a2e;">${result.address}</h4>
                        <div style="margin-bottom:8px;">
                            <span style="font-size:24px;font-weight:bold;color:${color};">${result.total_score}</span>
                            <span style="color:#666;">/100分</span>
                            <span style="display:inline-block;padding:2px 8px;background:${color}20;color:${color};border-radius:12px;font-size:12px;margin-left:8px;">${result.rating}</span>
                        </div>
                        <div style="font-size:12px;color:#666;line-height:1.8;">
                            <div>🥤 竞品：${result.details.competitor_count}家 (${result.scores.competitor_density}/30)</div>
                            <div>🚇 地铁：${result.details.metro_station} ${result.details.metro_distance}m (${result.scores.transportation}/25)</div>
                            <div>👥 客流：写字楼${result.details.office_count} 学校${result.details.school_count} 商场${result.details.mall_count} (${result.scores.customer_flow}/25)</div>
                            <div>🏪 配套：${result.details.has_convenience_store ? '有便利店' : '无便利店'} ${result.details.is_restaurant_zone ? '餐饮区' : '非餐饮区'} (${result.scores.surrounding_facilities}/20)</div>
                        </div>
                    </div>
                `;

                const infoWindow = new BMap.InfoWindow(infoContent, {
                    width: 280,
                    title: ''
                });

                // 点击标记时打开信息窗口
                label.addEventListener('click', function(e) {
                    // 关闭所有已打开的信息窗口
                    markers.forEach(m => m.infoWindow.close());
                    this.infoWindow.open(map, point);
                    map.panTo(point);
                });

                const markerData = {
                    label: label,
                    infoWindow: infoWindow,
                    point: point
                };
                markers.push(markerData);

                map.addOverlay(label);
            });

            // 自动调整地图视野以包含所有标记点
            if (points.length > 0) {
                const viewport = getViewport(points);
                map.centerAndZoom(viewport.center, viewport.zoom);
            } else {
                map.centerAndZoom(new BMap.Point(116.397428, 39.90923), 12);
            }
        }

        /**
         * 根据多个坐标点计算最佳地图视野
         */
        function getViewport(points) {
            if (points.length === 1) {
                return { center: points[0], zoom: 16 };
            }

            let minLng = Infinity, maxLng = -Infinity;
            let minLat = Infinity, maxLat = -Infinity;

            points.forEach(p => {
                minLng = Math.min(minLng, p.lng);
                maxLng = Math.max(maxLng, p.lng);
                minLat = Math.min(minLat, p.lat);
                maxLat = Math.max(maxLat, p.lat);
            });

            const centerLng = (minLng + maxLng) / 2;
            const centerLat = (minLat + maxLat) / 2;
            const center = new BMap.Point(centerLng, centerLat);

            // 计算合适的缩放级别
            const lngDiff = maxLng - minLng;
            const latDiff = maxLat - minLat;
            const maxDiff = Math.max(lngDiff, latDiff);

            let zoom;
            if (maxDiff > 0.5) zoom = 11;
            else if (maxDiff > 0.2) zoom = 12;
            else if (maxDiff > 0.1) zoom = 13;
            else if (maxDiff > 0.05) zoom = 14;
            else if (maxDiff > 0.02) zoom = 15;
            else zoom = 16;

            return { center, zoom };
        }

        // ========================================
        // 评分柱状图
        // ========================================
        function initBarChart() {
            const chartDom = document.getElementById('bar-chart');
            const myChart = echarts.init(chartDom);

            const addresses = analysisData.results.map(r => {
                // 截断长地址用于显示
                return r.address.length > 12 ? r.address.substring(0, 10) + '...' : r.address;
            });
            const scores = analysisData.results.map(r => r.total_score);

            const option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: function(params) {
                        const index = params[0].dataIndex;
                        const result = analysisData.results[index];
                        return `<strong>${result.address}</strong><br/>
                                总分：${result.total_score}/100<br/>
                                评级：${result.rating}`;
                    }
                },
                grid: {
                    left: '3%',
                    right: '8%',
                    bottom: '10%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: addresses,
                    axisLabel: {
                        fontSize: 12,
                        rotate: 15
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 100,
                    axisLabel: {
                        formatter: '{value}分'
                    },
                    splitLine: {
                        lineStyle: { type: 'dashed' }
                    }
                },
                series: [{
                    data: scores.map((score, index) => {
                        const result = analysisData.results[index];
                        let color;
                        if (result.rating === '强烈推荐') color = '#00b894';
                        else if (result.rating === '推荐') color = '#0984e3';
                        else if (result.rating === '一般') color = '#fdcb6e';
                        else color = '#d63031';
                        
                        return {
                            value: score,
                            itemStyle: {
                                color: color,
                                borderRadius: [6, 6, 0, 0]
                            }
                        };
                    }),
                    type: 'bar',
                    barWidth: '50%',
                    label: {
                        show: true,
                        position: 'top',
                        formatter: '{c}分',
                        fontSize: 13,
                        fontWeight: 'bold'
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.3)'
                        }
                    }
                }]
            };

            myChart.setOption(option);

            // 响应式调整
            window.addEventListener('resize', () => myChart.resize());
        }

        // ========================================
        // 评分明细表
        // ========================================
        function renderTable() {
            const tbody = document.getElementById('table-body');
            
            tbody.innerHTML = analysisData.results.map(result => {
                const badgeClass = {
                    '强烈推荐': 'badge-best',
                    '推荐': 'badge-good',
                    '一般': 'badge-normal',
                    '不推荐': 'badge-bad'
                }[result.rating] || 'badge-normal';

                const totalScorePercent = result.total_score;
                const fillClass = totalScorePercent >= 85 ? 'fill-high' : 
                                  totalScorePercent >= 70 ? 'fill-mid' : 'fill-low';

                return `
                    <tr>
                        <td><strong style="color:#667eea;">#${result.rank}</strong></td>
                        <td>${result.address}</td>
                        <td>
                            ${result.scores.competitor_density}/30
                            <div class="score-bar">
                                <div class="score-bar-fill fill-mid" style="width:${(result.scores.competitor_density/30)*100}%"></div>
                            </div>
                        </td>
                        <td>
                            ${result.scores.transportation}/25
                            <div class="score-bar">
                                <div class="score-bar-fill fill-high" style="width:${(result.scores.transportation/25)*100}%"></div>
                            </div>
                        </td>
                        <td>
                            ${result.scores.customer_flow}/25
                            <div class="score-bar">
                                <div class="score-bar-fill ${result.scores.customer_flow >= 20 ? 'fill-high' : 'fill-mid'}" style="width:${(result.scores.customer_flow/25)*100}%"></div>
                            </div>
                        </td>
                        <td>
                            ${result.scores.surrounding_facilities}/20
                            <div class="score-bar">
                                <div class="score-bar-fill ${result.scores.surrounding_facilities >= 15 ? 'fill-high' : 'fill-mid'}" style="width:${(result.scores.surrounding_facilities/20)*100}%"></div>
                            </div>
                        </td>
                        <td><strong style="font-size:16px;">${result.total_score}</strong></td>
                        <td><span class="badge ${badgeClass}">${result.rating}</span></td>
                    </tr>
                `;
            }).join('');
        }

        // ========================================
        // 设置分析时间
        // ========================================
        function setAnalysisTime() {
            const timeElement = document.getElementById('analysis-time');
            const timestamp = analysisData.analysis_metadata.timestamp;
            const date = new Date(timestamp);
            timeElement.textContent = `📅 分析时间：${date.toLocaleString('zh-CN')} | 店铺类型：${analysisData.analysis_metadata.store_type}`;
        }

        // ========================================
        // 刷新数据（实际使用时调用 API 获取新数据）
        // ========================================
        function refreshData() {
            // 这里可以替换为实际的 API 调用
            // fetch('/api/analysis/latest')
            //   .then(res => res.json())
            //   .then(data => { ... })
            alert('实际使用时，此处会从后端API获取最新的MCP分析结果。\n当前展示的是示例数据。');
        }

        // ========================================
        // 初始化
        // ========================================
        function init() {
            initMap();
            initBarChart();
            renderTable();
            setAnalysisTime();
        }

        // 页面加载完成后初始化
        window.onload = init;
    </script>
</body>
</html>
```

将 `analysisData` 变量中的模拟数据，替换为 AI 通过 MCP 分析后返回的真实 JSON 数据。数据格式已在 SKILL.md 中明确定义。
