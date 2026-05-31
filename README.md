# 项目初始化

Python 3.11 及以上

```bash
pip install -r requirements.txt
```

# 依赖说明

## Web 框架核心

- fastapi：现代、高性能的 Python Web 框架，支持异步，自动生成 API 文档
- uvicorn：ASGI 服务器，用于运行 FastAPI 应用
- python-multipart：处理 multipart/form-data 请求（文件上传）

## 加密安全

- pycryptodome：加密库，用于 RSA 加解密
- bcrypt：密码哈希库，用于存储用户密码（加盐哈希）
- PyJWT：JSON Web Token 库，用于用户认证

## 数据处理与流量解析

- numpy：数值计算库
- dpkt：pcap 文件解析库，用于提取 QUIC 流量特征
- scikit-learn：机器学习库，用于模型评估

## 数据库

- sqlalchemy：ORM 框架，用于数据库操作
- pymysql：MySQL 数据库驱动

## 工具

- python-dotenv：环境变量管理，用于加载 .env 配置文件

# 项目结构说明

```text
QUIC_Classifier_Backend/
├── app/
│   ├── api/                 # API 接口层
│   │   └── v1/endpoints/    # 版本化接口
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置文件
│   │   ├── database.py      # 数据库连接
│   │   └── security.py      # 加密工具（RSA）
│   ├── models/              # 数据库模型（SQLAlchemy）
│   │   ├── user.py          # 用户表
│   │   ├── task.py          # 任务表
│   │   └── analysis_result.py # 分析结果表
│   ├── schemas/             # Pydantic 模型（请求/响应）
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py  # 认证服务
│   │   └── analysis_service.py # 分析服务
│   ├── utils/               # 工具函数
│   │   └── response.py      # 统一响应格式
│   └── ml/                  # 机器学习模块
│       ├── feature_extractor.py # 特征提取
│       └── model_engine.py      # 模型引擎
├── models/                  # 模型权重文件
│   └── weights/
├── uploads/                 # 临时上传文件目录（分析后自动清理）
├── requirements.txt         # 依赖列表
├── .env                     # 环境变量（不提交）
├── .env.example             # 环境变量模板
└── run.py                   # 项目启动入口
```

# 环境变量配置

```text
# JWT 配置
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS 配置
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=quic_db
DB_CHARSET=utf8mb4

# 调试模式
DEBUG=true
```

# 启动项目

```bash
python run.py
```

# API 文档

启动后访问Swagger UI：http://localhost:5000/docs

