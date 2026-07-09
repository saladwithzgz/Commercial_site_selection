"""
Flask API服务
提供REST API接口供前端调用
"""
import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

from .location_agent import LocationAnalysisAgent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder=None)
CORS(app)  # 启用跨域支持

# 初始化Agent
agent = LocationAnalysisAgent()

# 前端静态文件目录
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@app.route('/')
def index():
    """提供前端首页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """提供前端静态文件"""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析选址API"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "请提供query参数"
            }), 400
        
        user_input = data['query']
        logger.info(f"收到分析请求: {user_input}")
        
        # 异步调用Agent分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze(user_input))
        finally:
            loop.close()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "milk-tea-location-scout",
        "version": "1.0.0"
    })


@app.route('/api/scoring-rules', methods=['GET'])
def scoring_rules():
    """获取评分规则"""
    try:
        config = agent.config_loader.config
        return jsonify({
            "status": "success",
            "data": config
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "status": "error",
        "message": "接口不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        "status": "error",
        "message": "服务器内部错误"
    }), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """启动服务器"""
    logger.info(f"启动服务器: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
