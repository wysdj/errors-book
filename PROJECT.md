# 408 错题管理器 — 项目主控

> **项目代号**：ErrorBook-408 | **启动**：2026-05-24 | **学生**：wysdj | **老师**：DJ

---

## 当前状态

| 模块 | 状态 |
|------|------|
| OCR 拍照识别 | ✅ PaddleOCR 2.7 + Python 3.9 |
| AI 分类（RAG） | ✅ DeepSeek Chat + 408 考纲知识库 |
| AI 生成参考答案 | ✅ |
| 费曼引导复习 | ✅ 自动标记掌握 |
| 错题数据库 | ✅ SQLite + 6 个 API |
| 前端页面 | ✅ 录入/列表/统计图表 |
| CSV 导出 | ✅ |
| 数学知识库 | ✅ 高等数学/线代/概率 |
| 领域分离 | ✅ 408/数学独立分类 |
| 章节联动筛选 | ✅ |
| 标签云统计 | ✅ |
| AI 错因分析 | ✅ |
| C++ 后端 | ❌ 不需要 |

---

## 启动

```bash
cd D:\错题项目\services
.venv39\Scripts\python.exe ocr_server.py
# 浏览器 → http://localhost:8901
```

## 技术栈

| 层 | 技术 |
|----|------|
| OCR | PaddleOCR 2.7.3 |
| AI | DeepSeek Chat API |
| 后端 | Flask 3.1 |
| 数据库 | SQLite |
| 前端 | HTML/CSS/JS + Chart.js |
| Python | 3.9 (.venv39) |

## 目录

```
D:\错题项目\services\
├── ocr_server.py       ← 统一服务
├── database.py         ← SQLite 数据库
├── knowledge_408.py    ← 408 + 数学 完整考纲
├── static/
│   ├── index.html      ← 页面结构
│   ├── style.css       ← 样式
│   └── app.js          ← 前端逻辑
└── .venv39\            ← Python 3.9 环境
```

## 未来改进方向

- **多用户版本**：加登录系统，每个人独立数据库，云端部署
- **PWA/移动端**：做成手机 App，拍照更方便
- **间隔复习算法**：根据艾宾浩斯曲线自动安排复习计划
- **语音讲解**：费曼复习时语音输入，更贴近真实讲解
- **错题社区**：匿名分享典型错题，看别人怎么错的
- **PDF 导入**：直接导入试卷 PDF，批量 OCR 录入
- **导出 Anki**：一键同步到 Anki 记忆卡片
- **数据面板**：更丰富的可视化——正确率曲线、时间热力图
