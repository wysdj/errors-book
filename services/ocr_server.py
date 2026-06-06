"""408 错题管理器 — 统一服务"""

from flask import Flask, request, jsonify
import json, urllib.request, os, uuid
from datetime import datetime
from knowledge_408 import SUBJECTS_408
from database import *

app = Flask(__name__)

# DeepSeek API Key — 先读配置文件，读不到就用环境变量
_deepseek_key = ''
try:
    _deepseek_key = json.load(open(
        os.path.expandvars(r'%USERPROFILE%\.openclaw\agents\main\agent\auth-profiles.json'),
        encoding='utf-8'
    ))['profiles']['deepseek:default']['key']
except:
    _deepseek_key = os.environ.get('DEEPSEEK_KEY', '')
DEEPSEEK_KEY = _deepseek_key

sessions = {}
SUBJECT_LIST_408 = ['数据结构','计算机组成原理','操作系统','计算机网络']
SUBJECT_LIST_MATH = ['高等数学','线性代数','概率论与数理统计']
SUBJECT_LIST = SUBJECT_LIST_408 + SUBJECT_LIST_MATH

def ask_deepseek(prompt, max_tokens=500, temperature=0.3):
    req = urllib.request.Request('https://api.deepseek.com/v1/chat/completions',
        data=json.dumps({'model':'deepseek-chat','messages':[{'role':'user','content':prompt}],
        'temperature':temperature,'max_tokens':max_tokens}).encode(),
        headers={'Authorization':f'Bearer {DEEPSEEK_KEY}','Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=30).read())['choices'][0]['message']['content']

def ask_deepseek_multi(messages, max_tokens=500, temperature=0.3):
    req = urllib.request.Request('https://api.deepseek.com/v1/chat/completions',
        data=json.dumps({'model':'deepseek-chat','messages':messages,
        'temperature':temperature,'max_tokens':max_tokens}).encode(),
        headers={'Authorization':f'Bearer {DEEPSEEK_KEY}','Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req,timeout=30).read())['choices'][0]['message']['content']


def classify_by_ai(text, domain='all'):
    subjects = SUBJECT_LIST_408 if domain == '408' else (SUBJECT_LIST_MATH if domain == 'math' else SUBJECT_LIST)
    ctx = retrieve_knowledge(text)
    prompt = f"""你是考研辅导专家。参考知识库分类，严格返回JSON：
{{"subject":"学科","chapter":"章节","topics":["知识点"],"difficulty":"简单/中等/困难"}}
可选学科：{', '.join(subjects)}
参考知识库：{ctx}
题目：{text}"""
    r = ask_deepseek(prompt, max_tokens=300, temperature=0.1)
    s, e = r.find('{'), r.rfind('}')+1
    return json.loads(r[s:e])

def retrieve_knowledge(text, top_n=5):
    matches = []
    for subj, chs in SUBJECTS_408.items():
        for ch, topics in chs.items():
            for tn, kws in topics:
                sc = sum(1 for k in kws if k in text)
                if sc > 0: matches.append((sc, subj, ch, tn, ', '.join(kws[:5])))
    matches.sort(reverse=True, key=lambda x: x[0])
    if not matches: return '无匹配'
    return '\n'.join(f'- {s} > {c} > {t} (匹配{sc}词)' for sc,s,c,t,_ in matches[:top_n])

def generate_questions(text, reference=''):
    sys_prompt = "你是408考研辅导老师，用费曼学习法引导学生讲解题目。每轮问一个问题，学生回答后再追问下一步。"
    ref_info = f"\n\n参考答案：{reference}" if reference else ""
    user_msg = f"请为以下题目生成第一个引导问题（3-5个问题即可，第一个必问核心知识点，最后一个问易错点）。只返回问题文字，不要序号：\\n{text}{ref_info}"
    r = ask_deepseek_multi([
        {'role':'system','content':sys_prompt},
        {'role':'user','content':user_msg}
    ], max_tokens=300)
    qs = [l.strip('- 0123456789.：: ') for l in r.split('\n') if l.strip()]
    qs = [q for q in qs if len(q) > 5 and '?' not in q[:3]]
    if not qs: qs = [l for l in r.split('\n') if len(l.strip()) > 5]
    return qs[:5] if qs else ['考察的核心知识点是什么？','请讲解解题步骤','有什么易错点？']


def evaluate_answer_with_context(text, reference, history):
    sys_prompt = '你是408考研辅导老师，用费曼学习法引导学生。根据参考答案和对话历史判定学生当前回答。返回JSON格式：{"result":"correct/partial/wrong","feedback":"具体分析","next_question":"下一步追问（如果是最后一轮则为空）","completed":false}'
    ref_info = f'\n参考答案：{reference}' if reference else ''
    msgs = [{'role':'system','content':sys_prompt},
            {'role':'user','content':f"这是题目和参考答案：\n{text}{ref_info}\n\n以下是对话历史，请判定学生最后一轮回答并追问："}]
    if history:
        for h in history:
            msgs.append({'role':'user','content':f"提问：{h['q']}\n学生回答：{h['a']}"})
            if h.get('feedback'):
                msgs.append({'role':'assistant','content':h['feedback']})
    r = ask_deepseek_multi(msgs, max_tokens=400)
    try:
        s, e = r.find('{'), r.rfind('}')+1
        return json.loads(r[s:e])
    except:
        return {"result":"partial","feedback":r,"next_question":"","completed":False}

# 通义千问 VL Key
QWEN_KEY = os.environ.get('QWEN_KEY', 'sk-b87f6d1e938c49c4931fd61a50405c2f')

def describe_image(img_path):
    """用通义千问 VL 识别图片内容"""
    import base64
    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    req = urllib.request.Request('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        data=json.dumps({'model':'qwen-vl-plus','messages':[{'role':'user','content':[
            {'type':'text','text':'请直接提取图片中的所有文字内容，逐行输出。不要分析、不要解释，只要原文。如果图片中有图表，请用文字描述图表的关键信息。'},
            {'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{img_b64}'}}
        ]}],'max_tokens':500}).encode(),
        headers={'Authorization':f'Bearer {QWEN_KEY}','Content-Type':'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return r['choices'][0]['message']['content']

def describe_image_to_text(img_path):
    import base64
    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    req = urllib.request.Request('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        data=json.dumps({'model':'qwen-vl-plus','messages':[{'role':'user','content':[
            {'type':'text','text':'请提取图片中的所有题目文字（含选项）。如果有手写笔记只提取印刷体题目，有图表请用文字描述。直接返回题目原文，不要解释。'},
            {'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{img_b64}'}}
        ]}],'max_tokens':800}).encode(),
        headers={'Authorization':f'Bearer {QWEN_KEY}','Content-Type':'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return r['choices'][0]['message']['content']


@app.route('/app.js')
def serve_appjs():
    from flask import Response
    return Response(open('static/app.js', encoding='utf-8').read(), mimetype='application/javascript')
@app.route('/')
def index():
    return open(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), encoding='utf-8').read()

@app.route('/ocr', methods=['POST'])
def ocr():
    f = request.files.get('image')
    if not f or f.filename == '': return {'error':'请上传图片'}, 400
    os.makedirs('temp', exist_ok=True)
    p = os.path.join('temp', str(uuid.uuid4())+'.jpg')
    f.save(p)
    # VL 模型直接提取文字（跳过 OCR）
    try: text = describe_image_to_text(p)
    except Exception as e: return {'error':f'VL识别失败: {str(e)}'}

    # 数学公式转 KaTeX 格式
    try:
        text = ask_deepseek(f"""你是数学公式排版专家。请将以下题目中的所有数学表达式转为KaTeX格式。规则：
1. 矩阵、行列式用 $$\\begin{{bmatrix}}...\\end{{bmatrix}}$$
2. 分数用 $$\\frac{{分子}}{{分母}}$$
3. 上下标用 ^ 和 _，积分用 $$\\int$$
4. 一般公式用 $$...$$，行内用 \\(...\\)
5. 纯中文/非公式文字保持原样
6. 直接返回转换后的完整题目，不要解释

题目：\n{text}""", max_tokens=800, temperature=0.1)
    except: pass
    os.makedirs('images', exist_ok=True)
    img_fname = str(uuid.uuid4()) + '.jpg'
    img_path = os.path.join('images', img_fname)
    import shutil; shutil.copy(p, img_path)
    try: ai = classify_by_ai(text)
    except: ai = {'error':'AI分类失败'}
    return {'text':text, 'ai':ai, 'image_path':img_path, 'confidence':'N/A'}

@app.route('/classify', methods=['POST'])
def classify_text():
    d = request.get_json()
    if not d or 'text' not in d: return {'error':'请提供text'}, 400
    try: return {'ai':classify_by_ai(d['text'].strip(), d.get('domain','all')),'error':None}
    except Exception as e: return {'error':str(e)}, 500

@app.route('/generate-answer', methods=['POST'])
def generate_answer():
    d = request.get_json()
    if not d or 'text' not in d: return {'error':'请提供题目'}, 400
    desc = d.get('img_desc','')
    extra = f'\n图片描述：{desc}' if desc else ''
    prompt = f"你是408专家。输出参考答案：包含关键步骤但简洁。数学公式用\\(...\\)或$$...$$的KaTeX格式输出。{extra}\n题目：{d['text']}"
    return {'answer':ask_deepseek(prompt,max_tokens=800,temperature=0.2),'error':None}

@app.route('/review/start', methods=['POST'])
def review_start():
    d = request.get_json()
    if not d or 'text' not in d: return {'error':'请提供题目'}, 400
    text = d['text'].strip()
    ref = ''
    if d.get('error_id'):
        err = get_error(d['error_id'])
        if err: ref = err.get('reference_answer','')
    qs = generate_questions(text)
    sid = str(uuid.uuid4())[:8]
    sessions[sid] = {'text':text,'questions':qs,'step':0,'history':[],'reference':ref,
                     'error_id': d.get('error_id'),'messages':[{'role':'system','content':'你是408考研辅导老师，用费曼学习法引导学生讲解。根据题目和参考答案，先问核心知识点，再逐步追问解题过程，最后问易错点。每一步判定学生回答并追问下一步。'},{'role':'user','content':f'题目：{text}\n参考答案：{ref}\n请开始提问第一个问题。'}]}
    return {'session_id':sid,'step':1,'total':len(qs),'question':qs[0],'error':None}

@app.route('/review/answer', methods=['POST'])
def review_answer():
    d = request.get_json()
    sid, ans = d.get('session_id'), d.get('answer','').strip()
    if sid not in sessions: return {'error':'会话不存在'}, 400
    s = sessions[sid]; st = s['step']
    if st >= len(s['questions']): return {'completed':True,'message':'已掌握'}
    # 多轮对话判定
    r = evaluate_answer_with_context(s['text'], s.get('reference',''),
        s['history'] + [{'q': s['questions'][st], 'a': ans}])
    s['history'].append({'q':s['questions'][st],'a':ans,'r':r['result']})
    if r['result'] == 'correct': s['step'] += 1
    if s['step'] >= len(s['questions']):
        # 全部通过 → 自动标记掌握
        if s.get('error_id'):
            update_error(s['error_id'], mastered=1, reviewed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return {'completed':True,'message':'恭喜！全部通过，已自动标记为掌握！','feedback':r['feedback']}
    return {'completed':False,'result':r['result'],'feedback':r['feedback'],
            'missing':r.get('missing',''),'step':s['step']+1,'total':len(s['questions']),
            'next_question':s['questions'][s['step']]}

@app.route('/review/hint', methods=['POST'])
def review_hint():
    d = request.get_json()
    sid = d.get('session_id')
    if sid not in sessions: return {'error':'会话不存在'}, 400
    s = sessions[sid]
    return {'hint':ask_deepseek(f"学生卡住了。题目：{s['text']}\n问题：{s['questions'][s['step']]}\n给引导提示别给答案。数学公式用\\(...\\)或$$...$$的KaTeX格式输出。",max_tokens=150)}

@app.route('/suggest-reason', methods=['POST'])
def suggest_reason():
    d = request.get_json()
    if not d or 'text' not in d: return {'error':'请提供题目'}, 400
    prompt = f"分析这道题的常见错误原因（10字以内，如：概念混淆、计算错误、审题不清、公式记错、方法错误、遗漏条件）。题目：{d['text']}"
    return {'reason': ask_deepseek(prompt, max_tokens=50, temperature=0.2), 'error': None}


@app.route('/errors', methods=['POST'])
def save_error():
    d = request.get_json()
    if not d or 'text' not in d: return {'error':'请提供题目文字'}, 400
    if not d.get('reference_answer','').strip(): return {'error':'请填写参考答案'}, 400
    eid = add_error(question_text=d['text'], ocr_text=d.get('ocr_text',''), ocr_confidence=d.get('ocr_confidence',0),
        ai_subject=d.get('ai_subject',''), ai_chapter=d.get('ai_chapter',''), ai_topics=d.get('ai_topics',''), ai_difficulty=d.get('ai_difficulty',''),
        subject=d.get('subject',d.get('ai_subject','')), chapter=d.get('chapter',d.get('ai_chapter','')), topics=d.get('topics',d.get('ai_topics','')),
        answer_text=d.get('answer',''), reference_answer=d.get('reference_answer',''), image_path=d.get('image_path',''), image_desc=d.get('image_desc',''), error_reason=d.get('error_reason',''))
    return {'id':eid,'error':None}

@app.route('/errors', methods=['GET'])
def get_errors_list():
    return list_errors(subject=request.args.get('subject',''), chapter=request.args.get('chapter',''),
        mastered=request.args.get('mastered'), search=request.args.get('search',''),
        page=int(request.args.get('page',1)), limit=int(request.args.get('limit',20)),
        sort=request.args.get('sort','created_at'), order=request.args.get('order','DESC'))

@app.route('/errors/<int:eid>', methods=['GET','PUT','DELETE'])
def error_detail(eid):
    if request.method == 'GET':
        e = get_error(eid); return e if e else ({'error':'不存在'},404)
    elif request.method == 'PUT':
        d = request.get_json()
        if d: update_error(eid, **d)
        return {'ok':True}
    else:
        delete_error(eid); return {'ok':True}

@app.route('/errors/<int:eid>/master', methods=['POST'])
def toggle_mastered(eid):
    err = get_error(eid)
    if not err: return {'error':'不存在'},404
    ns = 0 if err['mastered'] else 1
    update_error(eid, mastered=ns, reviewed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return {'mastered':bool(ns)}

@app.route('/errors/<int:eid>/reviews', methods=['GET','POST'])
def error_reviews(eid):
    if request.method == 'GET': return {'reviews':get_reviews(eid)}
    d = request.get_json() or {}
    rid = add_review(eid, questions=d.get('questions',[]), passed=d.get('passed',False), score=d.get('score',0))
    return {'id':rid,'error':None}

@app.route('/stats', methods=['GET'])
def stats():
    return get_stats()


@app.route('/stats/topics', methods=['GET'])
def topic_stats():
    db = get_db()
    rows = db.execute("SELECT topics, COUNT(*) as cnt, SUM(mastered) as m FROM errors WHERE topics!='' GROUP BY topics ORDER BY cnt DESC LIMIT 15").fetchall()
    db.close()
    return [{'topic': r['topics'], 'total': r['cnt'], 'mastered': r['m'] or 0} for r in rows]


@app.route('/backup', methods=['GET'])
def backup():
    import zipfile, io, time
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        if os.path.exists('errors.db'):
            z.write('errors.db')
        if os.path.exists('images'):
            for f in os.listdir('images'):
                z.write(os.path.join('images', f))
        ts = time.strftime('%Y%m%d_%H%M%S')
        z.writestr('backup_info.txt', f'Backup created: {ts}\n')
    buf.seek(0)
    return buf.read(), 200, {
        'Content-Type': 'application/zip',
        'Content-Disposition': f'attachment; filename=errorbook_backup_{time.strftime("%Y%m%d_%H%M%S")}.zip'
    }


@app.route('/export/csv', methods=['GET'])
def export_csv():
    """导出错题为 CSV"""
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','题目','学科','章节','知识点','状态','日期'])
    result = list_errors(limit=99999)
    for e in result['items']:
        writer.writerow([e['id'], e['question_text'], e['subject'],
                        e['chapter'], e['topics'],
                        '已掌握' if e['mastered'] else '未掌握',
                        e['created_at']])
    return output.getvalue(), 200, {'Content-Type': 'text/csv; charset=utf-8-sig',
                                      'Content-Disposition': 'attachment; filename=errors.csv'}

@app.route('/images/<path:filename>')
def serve_image(filename):
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'images'), filename)


@app.route('/merge', methods=['POST'])
def merge_texts():
    d = request.get_json()
    if not d or 'texts' not in d: return {'error':'请提供要合并的文本列表'}, 400
    texts = d['texts']
    if len(texts) < 2: return {'merged':texts[0] if texts else ''}
    prompt = f"""你是一个文档整理助手。以下文字是从同一道题目的不同页面分别识别出来的，可能存在重复、乱码或顺序不对。请将它们合并为一道完整的题目，去除重复内容，修复OCR错误，保持题目原意。

页面1文字：{texts[0]}
页面2文字：{texts[1]}
{'页面3文字：'+texts[2] if len(texts)>2 else ''}

请返回合并后的完整题目文本（不要加任何解释）。"""
    merged = ask_deepseek(prompt, max_tokens=600)
    return {'merged':merged.strip(),'error':None}


if __name__ == '__main__':
    init_db()
    print('=== 408 错题管理器 ===\nhttp://localhost:8901')
    app.run(host='0.0.0.0', port=8901)
