"""测试完整流程：录入 → AI生成答案 → 入库 → 复习"""
import urllib.request, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
H = {'Content-Type': 'application/json'}

def post(url, data, timeout=30):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(f'http://localhost:8901{url}',
            data=json.dumps(data).encode(), headers=H), timeout=timeout
    ).read())

text = '已知二叉树前序为ABDCEGF中序为DBAEGCF求后序'

# 步骤1：AI 生成参考答案
print('=== 步骤1：AI 生成参考答案 ===')
ans = post('/generate-answer', {'text': text})
print(ans['answer'][:200] + '...')

# 步骤2：入库（用户确认后）
print('\n=== 步骤2：保存错题 ===')
r = post('/errors', {
    'text': text,
    'subject': '数据结构', 'chapter': '树与二叉树', 'topics': '遍历',
    'reference_answer': ans['answer']
})
eid = r['id']
print(f'已保存, id={eid}')

# 步骤3：开始复习（带参考答案）
print('\n=== 步骤3：费曼复习 ===')
r = post('/review/start', {'text': text, 'error_id': eid})
sid = r['session_id']
print(f'Review session: {sid}, 共{r["total"]}问')
print(f'Q1: {r["question"]}')

# 步骤4：回答第一问
print('\n=== 步骤4：回答第一问 ===')
r = post('/review/answer', {
    'session_id': sid,
    'answer': '考察的是二叉树遍历——通过前序和中序遍历序列反推二叉树结构'
})
print(f'判定: {r.get("result", "?")}')
print(f'反馈: {r.get("feedback", "")[:150]}')

# 步骤5：查看统计
print('\n=== 步骤5：统计 ===')
print(json.dumps(post('/stats', {}), ensure_ascii=False, indent=2))

# 清理测试数据
urllib.request.urlopen(urllib.request.Request(
    f'http://localhost:8901/errors/{eid}', method='DELETE'))
print('\n测试数据已清理')
