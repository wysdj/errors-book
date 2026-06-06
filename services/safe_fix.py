c = open(r'D:\错题项目\services\static\app.js', encoding='utf-8').read()

# 1. Fix showDetail - add answer toggle button
old_show = """async function showDetail(eid){
 var r=await(await fetch('/errors/'+eid)).json();
 if(!r||!r.id){toast('题目不存在','e');return}
 curErrorId=eid;
 var h='<p><b>题目：</b>'+(r.question_text||'')+'</p>';
 h+='<p><b>分类：</b>'+(r.subject||'?')+' > '+(r.chapter||'?')+'</p>';
 h+='<div class="btn-group"><button class="btn btn-p btn-sm" onclick="startReview('+eid+')">费曼复习</button>';
 h+='<button class="btn btn-g btn-sm" onclick="toggleMaster('+eid+')">'+(r.mastered?'取消掌握':'标记掌握')+'</button>';
 h+='<button class="btn btn-d btn-sm" onclick="deleteErr('+eid+')">删除</button></div>';
 document.getElementById('detailContent').innerHTML=h;
 document.getElementById('detail').style.display='block';setTimeout(renderMath,100);
}"""

new_show = """async function showDetail(eid){
 var r=await(await fetch('/errors/'+eid)).json();
 if(!r||!r.id){toast('题目不存在','e');return}
 curErrorId=eid;
 var h='<p><b>题目：</b>'+(r.question_text||'')+'</p>';
 h+='<p><b>分类：</b>'+(r.subject||'?')+' > '+(r.chapter||'?')+'</p>';
 h+='<div class="btn-group"><button class="btn btn-p btn-sm" onclick="startReview('+eid+')">费曼复习</button>';
 h+='<button class="btn btn-g btn-sm" onclick="toggleMaster('+eid+')">'+(r.mastered?'取消掌握':'标记掌握')+'</button>';
 h+='<button class="btn btn-d btn-sm" onclick="deleteErr('+eid+')">删除</button></div>';
 if(r.reference_answer){
  h+='<div id="ansToggle-'+eid+'"><button class="btn btn-s btn-sm" onclick="toggleAnswer('+eid+')" style="margin-top:8px">显示答案</button></div>';
 }
 document.getElementById('detailContent').innerHTML=h;
 document.getElementById('detail').style.display='block';setTimeout(renderMath,100);
}"""

c = c.replace(old_show, new_show)

# 2. Fix startReview - append, show question
old_start = """document.getElementById('detailContent').innerHTML='<div style="margin-top:16px;padding-top:16px;border-top:2px solid var(--b)"><b>费曼复习</b><div id="reviewQ">('+rev.step+'/'+rev.total+') '+rev.question+'</div><textarea id="ans" rows="3" placeholder="输入你的回答..."></textarea><div class="btn-group"><button class="btn btn-p btn-sm" onclick="submitAnswer()">提交</button><button class="btn btn-g btn-sm" onclick="getHint()">提示</button></div></div>';"""

new_start = """document.getElementById('detailContent').innerHTML+='<div style="margin-top:16px;padding-top:16px;border-top:2px solid var(--b)"><b>费曼复习</b><div style="font-size:12px;color:var(--t2);margin-bottom:8px">'+r.question_text+'</div><div id="reviewQ">('+rev.step+'/'+rev.total+') '+rev.question+'</div><textarea id="ans" rows="3" placeholder="输入你的回答..."></textarea><div class="btn-group"><button class="btn btn-p btn-sm" onclick="submitAnswer()">提交</button><button class="btn btn-g btn-sm" onclick="getHint()">提示</button></div></div>';"""

c = c.replace(old_start, new_start)

# 3. Add toggleAnswer function
old_toggle = "async function toggleMaster(eid){await fetch('/errors/'+eid+'/master',{method:'POST'});showDetail(eid);loadErrors();}"
new_toggle = """async function toggleAnswer(eid){
 var d=document.getElementById('ansToggle-'+eid);
 if(!d)return;
 if(d.dataset.loaded){
  var p=d.querySelector('.ans-content');
  if(p)p.style.display=p.style.display==='none'?'block':'none';
  d.querySelector('button').textContent=p.style.display==='none'?'显示答案':'隐藏答案';
  return;
 }
 var r=await(await fetch('/errors/'+eid)).json();
 if(!r||!r.reference_answer){d.innerHTML='暂无答案';return}
 d.innerHTML='<div class="ans-content" style="margin-top:8px;padding:12px;background:var(--bg);border-radius:8px;font-size:14px;line-height:1.7">'+r.reference_answer+'</div><button class="btn btn-s btn-sm" onclick="toggleAnswer('+eid+')" style="margin-top:4px">隐藏答案</button>';
 d.dataset.loaded='1';
 setTimeout(renderMath,100);
}
async function toggleMaster(eid){await fetch('/errors/'+eid+'/master',{method:'POST'});showDetail(eid);loadErrors();}"""
c = c.replace(old_toggle, new_toggle)

open(r'D:\错题项目\services\static\app.js', 'w', encoding='utf-8').write(c)

import re
from collections import Counter
funcs = re.findall(r'function (\w+)', c)
dupes = {k:v for k,v in Counter(funcs).items() if v>1}
print('Duplicates:', dupes if dupes else 'None')
print('Lines:', len(c.splitlines()))
print('toggleAnswer:', 'toggleAnswer' in c)
print('innerHTML+=:', 'innerHTML+=' in c)
