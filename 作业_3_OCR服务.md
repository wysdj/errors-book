# 错题管理器 — 课后作业（3）

> 提交方式：直接在 ocr_server.py 里写代码。下次说"继续错题项目"老师先看你的代码。


## 作业：完成 OCR 服务的识别和返回

当前代码在 `ocr_server.py` 里，PaddleOCR 已经调用了（`result = ocr_engine.ocr(path)`），
但最后一行还是 `return f'收到文件...'` —— 没有把识别结果返回给用户。

请完成以下三步：


### 第 1 步：提取文字（在 file.save(path) 之后）

PaddleOCR 的 result 结构：
```python
result = [
  [  # 第一页
    [[坐标], ('识别出的文字', 0.95)],
    [[坐标], ('又一行文字', 0.88)],
  ]
]
```

你的任务：
- 遍历 `result[0]` 列表
- 取出每行的**文字**和**置信度**
- 把所有行的文字拼成一个字符串
- 算出平均置信度

提示：
```python
texts = []
confs = []
for line in result[0]:
    texts.append(line[1][0])    # 第 1 个元素是坐标，第 2 个是 (文字, 置信度)
    confs.append(line[1][1])    # 置信度是元组的第 2 个
text = '\n'.join(texts)
confidence = sum(confs) / len(confs) if confs else 0.0
```


### 第 2 步：返回 JSON

用 `jsonify` 替代 `return f'收到文件...'`：

- 在前面加 `from flask import Flask, request, jsonify`
- 返回 `{'text': ..., 'confidence': ..., 'error': None}`

如果 result 为空（图片里没识别出文字），返回 `{'error': '未识别到文字'}`


### 第 3 步（加分）：自动分类

根据识别出的文字判断是哪门学科。
提示——定义关键词字典：

```python
KEYWORDS = {
    '数学': ['函数', '方程', '几何', '导数', '三角', '向量'],
    '物理': ['力学', '电场', '磁场', '牛顿', '运动'],
    '化学': ['反应', '元素', '酸碱', '氧化'],
    '英语': ['grammar', 'vocabulary', '语法', '时态', '从句'],
}
```

统计哪门学科的关键词在 `text` 里出现最多，把 `'subject': '数学'` 加到返回里。

---

## 提示

完成任务后，在命令行测试：
```bash
curl -X POST -F "image=@一张错题照片.jpg" http://localhost:8901/ocr
```

会返回类似：
```json
{"text": "已知 f(x)=x²+2x+1，求顶点坐标", "subject": "数学", "confidence": 0.92, "error": null}
```
