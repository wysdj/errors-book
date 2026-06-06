# Flask 入门 — 用你的错题本项目学

> 每一行代码都解释，从零开始

---

## 一、Flask 是什么？

Flask 就是 Python 写的"接电话的"。

```
你手机发请求 → Flask 收到 → 调用对应函数 → 返回结果
```

类比餐馆：你是厨师（写函数），Flask 是服务员（接单、上菜）。

---

## 二、最小例子：5 行代码跑一个网站

```python
from flask import Flask        # 1. 导入 Flask
app = Flask(__name__)          # 2. 创建应用

@app.route('/')                # 3. 定义路由：访问 "/" 时
def hello():                   # 4. 执行这个函数
    return '你好，世界！'       # 5. 返回这个文字

app.run(host='0.0.0.0', port=8901)  # 启动！
```

```bash
python app.py
# 浏览器打开 http://localhost:8901 → 看到 "你好，世界！"
```

**逐行解释**：

```python
from flask import Flask
# 从 flask 包里拿 Flask 这个类。就像 from math import sqrt

app = Flask(__name__)
# __name__ 是 Python 的内置变量，等于当前文件名（去掉 .py）
# Flask(__name__) 创建了一个"应用"，一切请求处理都在这个 app 里

@app.route('/')
# @ 开头的是"装饰器"（先不用深究，理解为"贴标签"）
# 意思是：把下面这个函数贴到 "/" 这个网址上
# 有人访问 "/" → 就调用这个函数

def hello():
    return '你好，世界！'
# 一个普通的 Python 函数，返回一段文字
# Flask 会自动把返回值包装成 HTTP 响应发给浏览器

app.run(host='0.0.0.0', port=8901)
# 启动服务器
# host='0.0.0.0'：接受任何 IP 的请求（手机、电脑都能访问）
# port=8901：在 8901 端口监听（类似门牌号）
```

---

## 三、路由：不同的网址做不同的事

打开你项目里的 `ocr_server.py`，每一个 `@app.route(...)` 就是一个"网址→函数"的映射：

```python
@app.route('/')                    # 访问 首页
def index():
    return '首页的HTML'

@app.route('/ocr', methods=['POST'])  # POST 请求才管用
def ocr():
    return '这里是拍照识别'

@app.route('/errors', methods=['GET'])  # GET 请求
def get_errors_list():
    return '这里是错题列表'

@app.route('/errors/<int:eid>', methods=['DELETE'])
def error_detail(eid):
    return f'删除了第 {eid} 号错题'
```

### 3.1 `methods=['POST']` 是什么意思？

HTTP 有几种"动词"：

| 动词 | 含义 | 例子 |
|------|------|------|
| GET | 拿数据 | 打开网页、查错题列表 |
| POST | 提交数据 | 拍照上传、保存错题 |
| DELETE | 删除 | 删一条错题 |

```python
@app.route('/errors', methods=['GET'])   # GET /errors  → 查列表
@app.route('/errors', methods=['POST'])  # POST /errors → 新增
# 同一个网址，不同动词干不同事！
```

### 3.2 `<int:eid>` 是什么意思？

网址里可以带参数：

```python
@app.route('/errors/<int:eid>')
def error_detail(eid):
    # 如果访问 /errors/42 → eid = 42
    # 如果访问 /errors/7  → eid = 7
    return f'查看第 {eid} 号错题'
```

---

## 四、接收数据：request 对象

Flask 用 `request` 对象来拿客户端发来的数据。

### 4.1 接收 JSON（POST 请求的 body）

```python
from flask import Flask, request

@app.route('/errors', methods=['POST'])
def save_error():
    d = request.get_json()          # 把请求里的 JSON 转成 Python 字典
    text = d['text']                # 取 "text" 字段
    subject = d.get('subject', '')  # 取 "subject"，没有就默认空字符串
    return {'id': 1, 'ok': True}    # 返回 JSON
```

前端发的请求：
```javascript
fetch('/errors', {
  method: 'POST',
  body: JSON.stringify({
    text: '1+1等于几？',
    subject: '高等数学'
  })
})
```
→ Flask 收到 → `request.get_json()` → `{'text': '1+1等于几？', 'subject': '高等数学'}`

### 4.2 接收图片文件

```python
@app.route('/ocr', methods=['POST'])
def ocr():
    f = request.files.get('image')   # 取名为 "image" 的文件
    if not f: return {'error': '没图'}

    f.save('uploaded.jpg')           # 保存到硬盘
    return {'ok': True}
```

前端：
```javascript
var form = new FormData();
form.append('image', 文件);          // 字段名 "image" 对应后端 get('image')
fetch('/ocr', {method: 'POST', body: form});
```

### 4.3 接收 URL 参数

```python
@app.route('/errors', methods=['GET'])
def list_errors():
    subject = request.args.get('subject', '')   # /errors?subject=数据结构
    page = int(request.args.get('page', 1))     # /errors?page=3
    #    ↑ request.args 是 URL 问号后面的参数字典
    return {'subject': subject, 'page': page}
```

URL：`/errors?subject=数据结构&page=3`
→ `request.args` = `{'subject': '数据结构', 'page': '3'}`

---

## 五、返回数据

### 5.1 返回字典 → 自动变 JSON

```python
return {'name': '张三', 'age': 20}
# Flask 自动转成 JSON → {"name": "张三", "age": 20}
```

### 5.2 返回错误

```python
return {'error': '没找到'}, 404
#              返回值       状态码
# Flask 把字典 + 404 一起发回去
```

### 5.3 返回文件/图片

```python
from flask import send_from_directory

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory('images', filename)
# /images/abc.jpg → 返回 images/abc.jpg 文件
```

### 5.4 返回 HTML

```python
@app.route('/')
def index():
    return open('static/index.html', encoding='utf-8').read()
    # 直接读 HTML 文件内容，作为响应发回去
```

---

## 六、你的 ocr_server.py 全路线图

```
浏览器/手机 打开 http://121.40.212.86:8901
    │
    ├─ GET / ──────────────────→ index() 返回 index.html
    │
    ├─ GET /static/style.css ──→ Flask 自动从 static/ 文件夹找
    ├─ GET /static/app.js ────→ Flask 自动从 static/ 文件夹找
    │
    ├─ POST /ocr ─────────────→ ocr()
    │   request.files['image']  ← 图片
    │   → describe_image_to_text() → VL 模型提取文字
    │   → ask_deepseek() → 数学转 KaTeX
    │   → classify_by_ai() → 自动分类
    │   return {'text':..., 'ai':...}
    │
    ├─ POST /errors ──────────→ save_error()
    │   request.get_json()  ← JSON
    │   → database.add_error() → 写入 SQLite
    │   return {'id': 42}
    │
    ├─ GET /errors?subject=数学&page=2 → get_errors_list()
    │   request.args.get('subject') → '数学'
    │   → database.list_errors() → 查数据库
    │   return {'items':[...], 'total':20}
    │
    ├─ GET /errors/42 ────────→ error_detail(42)
    │   return 第42号错题的完整数据
    │
    ├─ POST /review/start ────→ review_start()
    │   → DeepSeek 生成 3-5 个问题
    │   → 创建会话，存到内存 sessions = {}
    │
    ├─ POST /review/answer ───→ review_answer()
    │   → DeepSeek 判定回答
    │   → 全部通过 → 自动标记掌握
    │
    └─ GET /stats ────────────→ stats()
        → 返回统计数字
```

---

## 七、sessions 字典：怎么记住"刚才聊到哪了"

费曼复习是多轮对话，需要记住上下文。用 Python 字典：

```python
sessions = {}   # 全局字典，key=会话ID, value=会话数据

@app.route('/review/start', methods=['POST'])
def review_start():
    sid = 'abc123'                           # 生成唯一ID
    sessions[sid] = {
        'questions': ['什么是矩阵？', ...],    # 预设问题
        'step': 0,                            # 当前第几步
        'history': []                          # 对话历史
    }
    return {'session_id': sid, 'question': sessions[sid]['questions'][0]}

@app.route('/review/answer', methods=['POST'])
def review_answer():
    d = request.get_json()
    sid = d['session_id']                     # 拿会话ID
    s = sessions[sid]                         # 找回之前的对话
    # 用 s['step'] 知道问到第几步了
    # 用 s['history'] 带上下文给 AI 判定
    return {'feedback': '回答正确！'}
```

**为什么不用数据库？**
因为复习对话是临时的——刷新页面就没了，不需要永久保存。用内存字典够快。

---

## 八、Flask 常见问题

### Q: `return` 和 `print` 有什么区别？
```python
return 'Hello'   # 发给浏览器，用户能看到
print('Hello')   # 打印到服务器终端，用户看不到
```

### Q: 为什么用 `0.0.0.0` 而不是 `127.0.0.1`？
```
127.0.0.1 = 只允许本机访问（手机访问不了）
0.0.0.0   = 允许任何 IP 访问（手机用 WiFi 能连上）
```

### Q: Flask 的 `static/` 文件夹有什么特殊的？
```python
# 任何放在 static/ 下的文件，自动可以通过 /static/XXX 访问
static/style.css    →  http://121.40.212.86:8901/static/style.css
static/app.js       →  http://121.40.212.86:8901/static/app.js
static/icon-192.png →  http://121.40.212.86:8901/static/icon-192.png
# 这是 Flask 的约定，不需要写路由！
```

### Q: `import *` from database 是什么意思？
```python
from database import *
# 把 database.py 里所有的函数都导入，可以直接用
# add_error(...)、list_errors(...)、get_error(...)
# 不用写 database.add_error(...)
```

---

## 九、自己动手：加一个新功能

假设加一个"获取今日新增错题数"的功能：

**步骤1**：在 `database.py` 加查询函数
```python
def count_today():
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM errors WHERE date(created_at)=date('now')"
    ).fetchone()[0]
```

**步骤2**：在 `ocr_server.py` 加路由
```python
@app.route('/today-count')
def today_count():
    return {'count': count_today()}
```

**步骤3**：浏览器访问 `http://121.40.212.86:8901/today-count`
```json
{"count": 3}
```

三步搞定——这就是 Flask 的开发节奏。
