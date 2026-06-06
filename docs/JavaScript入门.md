# JavaScript 入门 — 用你的错题本项目学

> 你有 HTML/CSS 基础，这篇文章只讲 JS，全用你 app.js 里的代码当例子

---

## 一、JS 在网页里干什么？

HTML 是骨架，CSS 是皮肤，**JS 是大脑**。

```
HTML: <button onclick="doOCR()">识别</button>   ← 画了个按钮
CSS:  .btn { background: purple }              ← 按钮变紫色
JS:   function doOCR() { 发请求、改文字 }        ← 点了之后发生什么
```

**JS 做三件事**：
1. 找元素：`document.getElementById('txt')`
2. 改元素：`.value = '新文字'` 或 `.style.display = 'none'`
3. 发请求：`fetch('/ocr')` 跟服务器通信

---

## 二、变量

```javascript
var name = '张三';        // 文字用引号
var age = 20;             // 数字不用引号
var isStudent = true;     // 真假值
var list = [1, 2, 3];    // 数组（列表）
var obj = {name: '张三', age: 20};  // 对象（字典）

// ES6 新写法（更好）
let count = 0;      // let 代替 var（作用域更安全）
const PI = 3.14;    // const 是常量，不能改
```

---

## 三、找元素：document 对象

`document` 代表整个网页。所有的"找到某个元素"都从这里开始。

```javascript
// 通过 id 找（最常用）
var box = document.getElementById('txt');

// 通过 class 找（返回一组）
var pages = document.querySelectorAll('.page');

// 通过 CSS 选择器找
var btn = document.querySelector('.btn-p');
```

你的项目里到处都是：
```javascript
document.getElementById('txt')        // 题目输入框
document.getElementById('errList')    // 错题列表容器
document.getElementById('subj')       // 学科输入框
document.querySelectorAll('.page')    // 所有页面 div（录入/列表/统计）
```

---

## 四、改元素

### 4.1 改文字内容

```javascript
// 输入框的值
document.getElementById('txt').value = '新题目';

// 普通元素的文字
document.getElementById('result').textContent = '识别完成';
```

### 4.2 改 HTML（innerHTML）

```javascript
// 把一段 HTML 塞进一个 div 里
document.getElementById('errList').innerHTML =
    '<div class="card">' +
        '<div>第1题</div>' +
        '<div>第2题</div>' +
    '</div>';

// 你的 loadErrors() 函数就是干这个的：
// 查数据库 → 拼接 HTML 字符串 → innerHTML 塞到 errList 里
```

### 4.3 改样式

```javascript
// 隐藏/显示
document.getElementById('detail').style.display = 'none';   // 隐藏
document.getElementById('detail').style.display = 'block';  // 显示

// 改颜色
document.getElementById('result').style.color = 'red';
```

### 4.4 改 class

```javascript
var el = document.querySelector('.reason-tag');
el.classList.add('active');       // 加 class
el.classList.remove('active');    // 去 class
el.classList.toggle('active');    // 有就去掉，没有就加上
el.classList.contains('active');  // 检查有没有
```

---

## 五、函数

```javascript
// 定义函数
function sayHello(name) {
    return '你好，' + name;
}

// 调用函数
var result = sayHello('张三');  // result = '你好，张三'

// 箭头函数（简写，用于回调）
(page) => { page.style.display = 'none'; }
// 等价于
function(page) { page.style.display = 'none'; }
```

你的项目里每个按钮对应一个函数：

```javascript
function doOCR()     { /* 拍照识别 */ }
function doSave()    { /* 保存错题 */ }
function loadErrors(){ /* 加载错题列表 */ }
function switchTab() { /* 切换页面 */ }
function toast()     { /* 弹出提示 */ }
```

---

## 六、事件：点按钮触发函数

### 6.1 HTML 里绑定（你的项目用的方式）

```html
<button onclick="doOCR()">识别</button>
<!--        ↑ 点了就调 doOCR() 函数 -->

<select onchange="loadErrors()">
<!--           ↑ 选项变了就调 loadErrors() -->

<textarea oninput="updatePreview()">
<!--             ↑ 输入了就调 updatePreview() -->
```

### 6.2 常见事件

| 事件 | 触发时机 |
|------|---------|
| `onclick` | 点击 |
| `onchange` | 下拉框/输入框值改变 |
| `oninput` | 正在输入（每打一个字触发） |
| `onsubmit` | 表单提交 |

---

## 七、异步：fetch — 跟服务器通信

这是最重要的部分。JS 发请求给服务器，**不能等**——如果等了，整个页面就卡死了。

```javascript
// 发 GET 请求
var response = await fetch('/errors?subject=数据结构');
var data = await response.json();  // 把返回的 JSON 转成 JS 对象

// 发 POST 请求（提交数据）
var response = await fetch('/errors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: '1+1=?', subject: '数学' })
});
var result = await response.json();

// 发图片（FormData）
var form = new FormData();
form.append('image', 文件);
var response = await fetch('/ocr', {
    method: 'POST',
    body: form
});
var data = await response.json();
```

### 7.1 `await` 是什么意思？

```javascript
// 没有 await：拿不到结果（太快了）
var data = fetch('/errors').json();  // data = undefined ❌

// 有 await：等服务器回复再继续
var data = await fetch('/errors').json();  // data = {...} ✅
```

`await` = "等一下，等服务器回我了再往下走"。

### 7.2 你的 doOCR() 完整流程

```javascript
async function doOCR() {       // async 表示函数里有 await
    // 1. 拿图片
    var f = document.getElementById('img').files[0];
    if (!f) return;            // 没选图就不干了

    // 2. 打包
    showR('识别中...');
    var d = new FormData();
    d.append('image', f);

    // 3. 发请求，等结果
    ocrData = await (await fetch('/ocr?domain=' + domain, {
        method: 'POST',
        body: d
    })).json();
    // ↑ 两层 await：第一层等网络传输，第二层等 JSON 解析

    // 4. 把结果填到页面上
    document.getElementById('txt').value = ocrData.text || '';
    updatePreview();

    // 5. 填 AI 分类结果
    if (ocrData.ai && !ocrData.ai.error) {
        document.getElementById('subj').value = ocrData.ai.subject || '';
        document.getElementById('chap').value = ocrData.ai.chapter || '';
    }

    // 6. 显示原始 JSON（调试用）
    showR(JSON.stringify(ocrData, null, 2));
}
```

---

## 八、条件判断

```javascript
if (条件) {
    // 条件成立时执行
} else {
    // 条件不成立时执行
}

// 例子
if (ocrData.ai && !ocrData.ai.error) {
    // AI 分类成功了 → 填到页面
    document.getElementById('subj').value = ocrData.ai.subject;
} else {
    // AI 分类失败了 → 什么都不做
}

// 三元运算符（简写的 if-else）
var badge = mastered ? '已掌握' : '未掌握';
// 等价于
var badge;
if (mastered) { badge = '已掌握'; }
else          { badge = '未掌握'; }
```

---

## 九、循环

```javascript
// forEach：遍历数组
var items = [{id:1, name:'题1'}, {id:2, name:'题2'}];
items.forEach(function(item) {
    console.log(item.name);  // '题1', '题2'
});

// 你的项目里：把错题数组拼成 HTML
r.items.forEach(function(e, i) {
    html += '<div class="err-item" onclick="showDetail(' + e.id + ')">' +
        '<span>' + e.question_text + '</span>' +
    '</div>';
});
```

---

## 十、字符串拼接

```javascript
// + 号拼接（你的项目用的方式）
var html = '<div class="card">' + title + '</div>';

// 模板字符串（ES6，更清晰）
var html = `<div class="card">${title}</div>`;
//         ↑ 反引号 ` ` ，不是单引号

// 你的 loadErrors 就是在疯狂拼 HTML 字符串，然后 innerHTML 塞进页面
```

---

## 十一、常用小操作

```javascript
// 字符串
' hello '.trim()          // → 'hello'（去首尾空格）
'hello'.toUpperCase()     // → 'HELLO'
'1,2,3'.split(',')        // → ['1', '2', '3']（拆成数组）
['1','2','3'].join(', ')  // → '1, 2, 3'（合成字符串）

// 数组
list.push('新元素')        // 末尾加
list.filter(x => x > 3)   // 过滤
list.map(x => x * 2)      // 每个乘2

// 对象
obj.name                   // 点取值
obj['name']                // 中括号取值（一样）
obj?.name                  // 安全取值：obj 为 null 时不报错

// 时间
setTimeout(function() { ... }, 100);  // 100毫秒后执行
```

---

## 十二、你的 app.js 结构一览

```javascript
// ── 全局变量 ──
let sessionId, curErrorId, ocrData, currentPage, domain;

// ── 工具函数 ──
function toast(msg)    { /* 弹出提示 */ }
function showR(msg)    { /* 显示调试信息 */ }
function updatePreview(){ /* KaTeX 公式预览 */ }
function renderMath()  { /* 渲染数学公式 */ }

// ── 页面切换 ──
function switchTab(t)  { /* 三个 div 轮流显示 */ }

// ── 录入页 ──
async function doOCR()       { /* 拍照识别 */ }
async function doClassify()  { /* AI分类 */ }
async function doGenerateAnswer() { /* 生成答案 */ }
async function doDescribe()  { /* 图片描述 */ }
async function doSave()      { /* 保存 */ }

// ── 错题列表 ──
async function loadErrors()  { /* 加载列表 */ }
async function showDetail()  { /* 查看详情 */ }
async function toggleMaster(){ /* 切换掌握状态 */ }
async function deleteErr()   { /* 删除 */ }

// ── 费曼复习 ──
async function startReview() { /* 开始复习 */ }
async function submitAnswer(){ /* 提交回答 */ }
async function getHint()     { /* 获取提示 */ }

// ── 统计 ──
async function loadStats()   { /* 加载图表 */ }
```

---

## 十三、调试技巧

```javascript
// 在浏览器 F12 控制台可以试
console.log(变量);     // 打印变量看看是什么
debugger;              // 代码停在这里，一步步看

// 你项目里的 showR() 就是简单的调试输出
showR(JSON.stringify(数据, null, 2));  // 在页面底部显示 JSON
```

---

## 总结

JS 就记住四件事：

| 操作 | 怎么写 |
|------|--------|
| 找元素 | `document.getElementById('id')` |
| 改元素 | `.value = ` / `.innerHTML = ` / `.style.display = ` |
| 点按钮 | `onclick="函数()"` |
| 发请求 | `await fetch('/路由')` → `.json()` |
