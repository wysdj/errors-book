# 错题管理器 — 系统设计说明书 (SDD)

> 版本：v1.0 | 日期：2026-05-24 | 作者：DJ + wysdj

---

## 1. 系统架构总览

```
┌──────────────────────────────────────────────────┐
│                    前端 (SPA)                     │
│  拍照上传 │ 错题浏览 │ 费曼复习 │ 统计分析        │
│  HTML5 + CSS3 + Vanilla JS + Chart.js            │
│  Web Speech API (语音输入)                        │
└──────────────────┬───────────────────────────────┘
                   │ HTTP REST (JSON)
┌──────────────────┴───────────────────────────────┐
│              C++ 后端 (Crow 框架)                  │
│                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 路由控制器│ │ 业务逻辑 │ │ 数据库层 │          │
│  │ Router   │ │ Service  │ │ SQLite   │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│                      │                            │
│             内部调用 (HTTP / subprocess)           │
└──────────┬───────────┴───────────┬────────────────┘
           │                       │
┌──────────┴──────────┐  ┌─────────┴───────────┐
│  Python OCR 服务     │  │  Python 费曼服务     │
│  (Flask)            │  │  (Flask)            │
│                     │  │                     │
│  - PaddleOCR 识别   │  │  - 自由讲解判定     │
│  - 题目分类         │  │  - 引导问答生成     │
│  - 知识点标注       │  │  - 语音转文字(STT)  │
│  - 手写/印刷切换    │  │  - 对话管理         │
└─────────────────────┘  └─────────────────────┘
```

---

## 2. 技术选型详细说明

| 组件 | 选型 | 版本 | 理由 |
|------|------|------|------|
| C++ 标准 | C++17 | - | filesystem, optional, string_view |
| HTTP 框架 | Crow | 1.2+ | header-only, 类 Flask 路由风格 |
| JSON 解析 | nlohmann/json | 3.11+ | 标准库级 API，header-only |
| 数据库 | SQLite3 | 3.40+ | C 原生接口，零配置 |
| 图片处理 | stb_image | 2.28 | header-only, JPEG/PNG 解码 |
| HTTP 客户端 | cpp-httplib | 0.14+ | 调用 Python 服务 |
| OCR 引擎 | PaddleOCR | 2.8+ | 中文识别 SOTA |
| Python 框架 | Flask | 3.1+ | 轻量，快速开发 |
| STT | whisper.cpp / Web Speech | - | 语音转文字 |
| 前端图表 | Chart.js | 4.x | 轻量统计可视化 |
| 编译工具 | CMake | 3.20+ | 跨平台构建 |

---

## 3. API 设计

Base URL: `http://localhost:8899/api/v1`

### 3.1 错题管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/errors` | 拍照录入错题 |
| GET | `/errors` | 错题列表（分页、筛选、排序） |
| GET | `/errors/:id` | 错题详情 |
| PUT | `/errors/:id` | 编辑错题 |
| DELETE | `/errors/:id` | 删除错题 |
| PATCH | `/errors/:id/mastered` | 标记/取消已掌握 |

#### POST /errors — 拍照录入

```
Request (multipart/form-data):
  image: <file>           # JPEG/PNG 图片
  ocr_mode: "print"|"hand"  # OCR 模式

Response 201:
{
  "id": 42,
  "subject": "数学",
  "topic": "二次函数",
  "difficulty": "中等",
  "question_text": "已知 f(x) = x² + 2x + 1，求...",
  "answer_text": "",
  "ocr_confidence": 0.92,
  "image_path": "/data/images/42.jpg",
  "created_at": "2026-05-24T10:00:00Z"
}
```

#### GET /errors — 列表查询

```
Query Params:
  subject    # 学科筛选
  topic      # 知识点筛选
  difficulty # 难度筛选
  mastered   # true/false/null
  search     # 关键词搜索
  page       # 页码，默认 1
  limit      # 每页数量，默认 20
  sort       # created_at|reviewed_at|error_count
  order      # asc|desc

Response 200:
{
  "items": [ {...}, ... ],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

### 3.2 费曼复习

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/review/free` | 自由讲解提交 |
| POST | `/review/guided/start` | 开始引导问答 |
| POST | `/review/guided/answer` | 回答当前问题 |
| POST | `/review/ask` | 自由提问求助 |
| GET | `/review/history/:error_id` | 某题的复习记录 |

#### POST /review/free — 自由讲解

```
Request:
{
  "error_id": 42,
  "explanation": "这道题考察的是二次函数的顶点公式...",
  "mode": "text"     # "text" | "voice"（语音先转文字）
}

Response 200:
{
  "passed": false,
  "score": 3,           # 4 分制 (0-4)
  "dimensions": {
    "knowledge": {"passed": true, "comment": "知识点判断正确"},
    "logic": {"passed": true, "comment": "推导步骤正确"},
    "completeness": {"passed": false, "comment": "遗漏了定义域讨论"},
    "clarity": {"passed": true, "comment": "表达清晰"}
  },
  "suggestion": "请补充说明 x 的取值范围为什么是 R"
}
```

#### POST /review/guided/start — 开始引导问答

```
Request:
{
  "error_id": 42
}

Response 200:
{
  "session_id": "sess_abc123",
  "total_steps": 4,
  "current_step": 1,
  "question": "这道题考察的核心知识点是什么？",
  "hint": "（提示：和函数的图像特征有关）"
}
```

#### POST /review/guided/answer — 回答引导问题

```
Request:
{
  "session_id": "sess_abc123",
  "answer": "二次函数的顶点坐标和对称轴"
}

Response 200:
{
  "result": "correct",     // correct | partial | wrong
  "feedback": "正确！",
  "next": {
    "current_step": 2,
    "total_steps": 4,
    "question": "你是如何求出顶点坐标的？说说具体的步骤。"
  }
}
// 如果是最后一题且全部通过：
{
  "result": "correct",
  "feedback": "全部答对！",
  "completed": true,
  "mastered": true
}
```

### 3.3 统计分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/stats/summary` | 总览统计 |
| GET | `/stats/subjects` | 学科分布 |
| GET | `/stats/trend` | 录入/复习趋势 |
| GET | `/stats/weakpoints` | 薄弱知识点排行 |

#### GET /stats/summary

```
Response 200:
{
  "total_errors": 150,
  "mastered": 45,
  "mastered_rate": 0.30,
  "total_reviews": 320,
  "avg_score": 2.8,
  "this_week_new": 12,
  "this_week_reviewed": 25
}
```

### 3.4 数据管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/export/csv` | 导出 CSV |
| GET | `/export/pdf` | 导出 PDF |
| POST | `/backup` | 备份数据库 |
| DELETE | `/errors/batch` | 批量删除已掌握 |

---

## 4. 数据流设计

### 4.1 拍照录入流程

```
用户拍照/选图
     │
     ▼
前端压缩图片 (≤ 1920px, JPEG quality 85%)
     │
     ▼
POST /errors (multipart) ──→ C++ 后端
     │                          │
     │                    保存原图到磁盘
     │                          │
     │                    调用 Python OCR 服务
     │                          │
     │              ┌────── Flask OCR ──────┐
     │              │  预处理 (去噪/增强)    │
     │              │  PaddleOCR 文字提取    │
     │              │  分类器判断学科/知识点  │
     │              │  返回 JSON 结果        │
     │              └────────────────────────┘
     │                          │
     │                    INSERT INTO errors
     │                          │
     ▼                          ▼
返回错题 JSON ◀────────── HTTP 201
```

### 4.2 费曼复习流程

```
学生选择错题 + 模式
     │
     ├── 自由讲解 ─────────────────────────────┐
     │   输入文字 / 语音 → STT 转文字            │
     │         │                                │
     │         ▼                                │
     │   POST /review/free ──→ C++ 后端          │
     │                              │           │
     │                        调用 Tutor 服务    │
     │                              │           │
     │              ┌────── Flask Tutor ────┐   │
     │              │  语义分析讲解内容      │   │
     │              │  四维度逐项检查        │   │
     │              │  生成反馈建议          │   │
     │              └───────────────────────┘   │
     │                              │           │
     │                        返回判定结果       │
     │                                           │
     ├── 引导问答 ─────────────────────────────┐
     │   POST /review/guided/start              │
     │         │                                │
     │   Tutor 分析题目 → 拆解为 N 个问题        │
     │         │                                │
     │   ┌─→ 返回问题 1                          │
     │   │   学生回答 → Tutor 判定               │
     │   │   返回判定 + 问题 2                    │
     │   │   学生回答 → ...                      │
     │   └── 循环 N 轮                           │
     │         │                                │
     │   全部通过 → 标记已掌握                    │
     │                                           │
     └── 自由提问 ─────────────────────────────┐
         POST /review/ask                       │
         Tutor 返回引导提示（不给答案）           │
```

---

## 5. 模块划分

### 5.1 C++ 后端模块

```
backend/
├── CMakeLists.txt
├── src/
│   ├── main.cpp           # 入口：启动 HTTP 服务
│   ├── router.cpp         # 路由注册（/api/v1/...）
│   ├── error_handler.cpp  # 错题 CRUD 处理器
│   ├── review_handler.cpp # 复习接口处理器
│   ├── stats_handler.cpp  # 统计接口处理器
│   ├── image_service.cpp  # 图片保存、压缩、调用 OCR
│   ├── review_service.cpp # 调用 Tutor 服务
│   ├── db.cpp             # SQLite 封装（连接、查询、事务）
│   └── config.cpp         # 配置管理
├── include/
│   ├── router.h
│   ├── error_handler.h
│   ├── review_handler.h
│   ├── stats_handler.h
│   ├── image_service.h
│   ├── review_service.h
│   ├── db.h
│   └── config.h
└── third_party/
    ├── crow/              # Crow header-only
    ├── json/              # nlohmann/json header-only
    └── stb/               # stb_image header-only
```

### 5.2 Python OCR 服务模块

```
services/ocr/
├── ocr_server.py          # Flask 服务入口 (端口 8901)
├── recognizer.py          # PaddleOCR 封装（印刷/手写切换）
├── preprocessor.py        # 图片预处理（OpenCV）
├── classifier.py          # 题目分类（学科/知识点/难度）
├── knowledge_base.py      # 知识点词典（学科 → 章节 → 知识点）
└── requirements.txt
```

### 5.3 Python 费曼服务模块

```
services/tutor/
├── tutor_server.py        # Flask 服务入口 (端口 8902)
├── free_evaluator.py      # 自由讲解四维度判定
├── guided_generator.py    # 引导问答生成器
├── question_analyzer.py   # 题目拆解为知识点链
├── stt_service.py         # 语音转文字 (whisper)
└── requirements.txt
```

---

## 6. 数据库设计（概要）

### 6.0 数据库抽象层设计

采用 **Repository 模式**，业务代码不直接写 SQL：

```cpp
// include/db.h — 数据库抽象接口
class Database {
public:
    virtual ~Database() = default;
    
    // 错题
    virtual int addError(const Error& e) = 0;
    virtual std::optional<Error> getError(int id) = 0;
    virtual std::vector<Error> listErrors(const Filter& f) = 0;
    virtual bool updateError(int id, const Error& e) = 0;
    virtual bool deleteError(int id) = 0;
    
    // 复习记录
    virtual int addReview(const Review& r) = 0;
    virtual std::vector<Review> getReviewHistory(int errorId) = 0;
    
    // 统计
    virtual StatsSummary getSummary() = 0;
    virtual std::vector<SubjectStat> getSubjectStats() = 0;
};

// 工厂函数：根据配置创建对应实现
std::unique_ptr<Database> createDatabase(const Config& cfg);
```

**迁移路径**：

| 阶段 | 数据库 | 连接方式 | 适用场景 |
|------|--------|---------|---------|
| 开发期 | SQLite | 本地文件 `data/errors.db` | 你一个人用，快速迭代 |
| 共享期 | PostgreSQL | TCP 连接 `192.168.x.x:5432` | 局域网内多人访问 |
| 部署期 | PostgreSQL + Redis | 连接池 + 缓存 | 公网访问，多人并发 |

切换时只需改 `config.json` 里的 `database.type` 字段，代码一行不动。

### 核心表

```sql
-- 错题表
errors (
  id INTEGER PRIMARY KEY,
  subject VARCHAR(20),        -- 学科
  topic VARCHAR(100),         -- 知识点
  difficulty VARCHAR(10),     -- 难度
  question_text TEXT,         -- OCR 识别的题目文字
  answer_text TEXT,           -- 正确答案/解析
  image_path VARCHAR(500),    -- 原图路径
  ocr_confidence REAL,        -- OCR 置信度
  mastered BOOLEAN DEFAULT 0, -- 是否已掌握
  created_at DATETIME,
  updated_at DATETIME
)

-- 复习记录表
reviews (
  id INTEGER PRIMARY KEY,
  error_id INTEGER,           -- FK → errors
  mode VARCHAR(20),           -- "free" | "guided"
  content TEXT,               -- 学生讲解内容（JSON）
  score INTEGER,              -- 评分 0-4
  feedback TEXT,              -- 系统反馈
  passed BOOLEAN,
  created_at DATETIME
)

-- 引导问答记录表
guided_steps (
  id INTEGER PRIMARY KEY,
  review_id INTEGER,          -- FK → reviews
  step_number INTEGER,
  question TEXT,              -- 系统提问
  student_answer TEXT,        -- 学生回答
  result VARCHAR(20),         -- correct/partial/wrong
  feedback TEXT
)
```

> 完整 SQL DDL 在 `docs/schema.sql` 中给出（下个阶段）。

---

## 7. 部署架构

```
开发环境：所有服务运行在本机
┌──────────────────────────────────────────┐
│  Windows 11 (localhost)                   │
│                                           │
│  Port 8899: C++ 后端 (Crow)              │
│  Port 8901: Python OCR (Flask)           │
│  Port 8902: Python Tutor (Flask)         │
│  Port 8080: 前端 (静态文件服务)           │
│                                           │
│  SQLite 文件: D:\错题项目\data\errors.db  │
│  图片存储:    D:\错题项目\data\images\    │
└──────────────────────────────────────────┘
```

---

> 📌 下一步：数据库详细设计 (schema.sql)
