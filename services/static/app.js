let sessionId=null,curErrorId=null,ocrData=null,searchTimer=null,currentPage=1,domain='all';
if('serviceWorker' in navigator){navigator.serviceWorker.register('/static/sw.js');}
function onDomainChange(){domain=document.getElementById('domain').value;}

const CHAPTERS = {
 '数据结构':['线性表','栈和队列','树与二叉树','图','查找','排序'],
 '计算机组成原理':['计算机系统概述','数据的表示与运算','存储器层次结构','指令系统','中央处理器 CPU','总线','I/O系统'],
 '操作系统':['操作系统概述','进程管理','内存管理','文件管理','I/O管理'],
 '计算机网络':['计算机网络体系结构','物理层','数据链路层','网络层','传输层','应用层'],
 '高等数学':['函数极限连续','一元函数积分学','微分方程','多元函数微积分','无穷级数'],
 '线性代数':['行列式','矩阵','向量','线性方程组','特征值与特征向量'],
 '概率论与数理统计':['随机事件与概率','随机变量','数字特征','数理统计'],
};
function onSubjChange(){
 const s=document.getElementById('fSubj').value;
 const ch=document.getElementById('fChap');
 ch.innerHTML='<option value="">全部章节</option>';
 if(s&&CHAPTERS[s]){CHAPTERS[s].forEach(function(c){ch.innerHTML+='<option value="'+c+'">'+c+'</option>';});}
 loadErrors();
}

if(typeof renderMathInElement !== 'undefined'){
 document.addEventListener('DOMContentLoaded',function(){
  renderMathInElement(document.body,{delimiters:[
   {left:'$$',right:'$$',display:true},
   {left:'\\(',right:'\\)',display:false},
   {left:'\\[',right:'\\]',display:true}
  ]});
 });
}

function switchTab(t,el){
 document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active');});
 var pid=t==='capture'?'pageCapture':t==='list'?'pageList':'pageStats';
 document.getElementById(pid).classList.add('active');
 document.querySelectorAll('.sidebar a').forEach(function(a){a.classList.remove('active');});
 if(el)el.classList.add('active');
 if(t==='list')loadErrors();
 if(t==='stats'){setTimeout(loadStats,200);}
}

function toast(m,t){var d=document.createElement('div');d.className='toast toast-'+(t||'s');d.textContent=m;document.body.appendChild(d);setTimeout(function(){d.remove();},2500);}
function showR(m){document.getElementById('result').textContent=m;}

function updatePreview(){
 var t=document.getElementById('txt').value;
 var p=document.getElementById('mathPreview');
 if(!p)return;
 if(!t){p.innerHTML='';return}
 p.innerHTML=t;
 try{renderMathInElement(p,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\(',right:'\\)',display:false},{left:'\\[',right:'\\]',display:true}]})}catch(e){}
}

function renderMath(){
 if(typeof renderMathInElement !== 'undefined'){
  renderMathInElement(document.body,{delimiters:[
   {left:'$$',right:'$$',display:true},
   {left:'\\(',right:'\\)',display:false},
   {left:'\\[',right:'\\]',display:true}
  ]});
 }
}
function debounceSearch(){clearTimeout(searchTimer);searchTimer=setTimeout(loadErrors,400);}

var selectedReasonTags=[];
function toggleReasonTag(el){
 el.classList.toggle('active');
 var t=el.textContent;
 if(el.classList.contains('active')){selectedReasonTags.push(t)}
 else{selectedReasonTags=selectedReasonTags.filter(function(x){return x!==t});}
}

async function doOCR(){
 var f=document.getElementById('img').files[0];if(!f)return;showR('识别中...');
 var d=new FormData();d.append('image',f);
 ocrData=await(await fetch('/ocr?domain='+domain,{method:'POST',body:d})).json();
 document.getElementById('txt').value=ocrData.text||'';updatePreview();
 if(ocrData.ai&&!ocrData.ai.error){
  document.getElementById('subj').value=ocrData.ai.subject||'';
  document.getElementById('chap').value=ocrData.ai.chapter||'';
  document.getElementById('diff').value=ocrData.ai.difficulty||'';
  document.getElementById('topics').value=(ocrData.ai.topics||[]).join(', ');
 }
 showR(JSON.stringify(ocrData,null,2));
}
async function doClassify(){
 var t=document.getElementById('txt').value.trim();if(!t)return toast('请先输入题目','e');showR('分类中...');
 var r=await(await fetch('/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,domain})})).json();
 if(r.ai&&!r.ai.error){
  document.getElementById('subj').value=r.ai.subject||'';
  document.getElementById('chap').value=r.ai.chapter||'';
  document.getElementById('diff').value=r.ai.difficulty||'';
  document.getElementById('topics').value=(r.ai.topics||[]).join(', ');
  fetch('/suggest-reason',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})}).then(function(r){return r.json();}).then(function(r){document.getElementById('reason').value=r.reason||'';});
 }
 showR(JSON.stringify(r,null,2));
}
async function doGenerateAnswer(){
 var t=document.getElementById('txt').value.trim();if(!t)return toast('请先输入题目','e');showR('生成中...');
 var r=await(await fetch('/generate-answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,domain})})).json();
 document.getElementById('refAns').value=r.answer||'';showR('答案已生成');toast('答案已生成');var ap=document.getElementById('ansPreview');if(ap){ap.innerHTML=r.answer||'';try{renderMathInElement(ap,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\(',right:'\\)',display:false},{left:'\\[',right:'\\]',display:true}]})}catch(e){}}
}
async function doDescribe(){
 var f=document.getElementById('img').files[0];if(!f)return;
 showR('分析图片中...');var d=new FormData();d.append('image',f);
 var r=await(await fetch('/describe',{method:'POST',body:d})).json();
 var desc=r.description||'';
 var existing=document.getElementById('txt').value;
 document.getElementById('txt').value=existing+(existing?'\n[图片描述] ':'')+desc;
 showR('图片描述已追加到题目');toast('图片已分析');
}
async function doOCRAnswer(){
 var f=document.getElementById('ansImg').files[0];if(!f)return;
 showR('识别答案中...');var d=new FormData();d.append('image',f);
 var r=await(await fetch('/ocr?domain='+domain,{method:'POST',body:d})).json();
 var existing=document.getElementById('refAns').value;
 document.getElementById('refAns').value=existing+(existing?'\n':'')+r.text;
 showR('答案已追加到文本框');toast('答案已识别');
}
async function doSave(){
 var t=document.getElementById('txt').value.trim();if(!t)return toast('请输入题目','e');
 var r=await(await fetch('/errors',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
  text:t,ocr_text:ocrData?.text||'',ocr_confidence:ocrData?.confidence||0,
  ai_subject:ocrData?.ai?.subject||'',ai_chapter:ocrData?.ai?.chapter||'',
  ai_topics:(ocrData?.ai?.topics||[]).join(','),ai_difficulty:ocrData?.ai?.difficulty||'',
  subject:document.getElementById('subj').value,chapter:document.getElementById('chap').value,
  topics:document.getElementById('topics').value,reference_answer:document.getElementById('refAns').value,
  image_path:ocrData?.image_path||'',error_reason:(selectedReasonTags.join(';')+(';'+document.getElementById('reason').value).replace(/^;/,'')).replace(/;$/,'')
 })})).json();
 curErrorId=r.id;toast('保存成功 #'+r.id);showR('已保存, id='+r.id);
}

async function loadErrors(pg){
 if(pg)currentPage=pg; else currentPage=1;
 var q='subject='+encodeURIComponent(document.getElementById('fSubj').value)+'&mastered='+document.getElementById('fMastered').value+'&chapter='+encodeURIComponent(document.getElementById('fChap').value)+'&reason='+encodeURIComponent(document.getElementById('fReason').value)+'&search='+encodeURIComponent(document.getElementById('fSearch').value)+'&page='+currentPage;
 var r=await(await fetch('/errors?'+q)).json();
 var h='';r.items.forEach(function(e,i){
  h+='<div class="err-wrapper"><div class="err-item" onclick="toggleDetail('+e.id+')"><span class="idx">'+((currentPage-1)*20+i+1)+'</span><div class="info"><div class="title">'+(e.question_text||'无题目')+'</div><div class="meta"><span>'+(e.subject||'?')+'</span><span>&middot;</span><span>'+(e.chapter||'?')+'</span></div></div><span class="badge '+(e.mastered?'badge-m':'badge-p')+'">'+(e.mastered?'已掌握':'未掌握')+'</span></div><div class="err-detail" id="errDetail-'+e.id+'"></div></div>';
 });
 if(!h)h='<div style="text-align:center;padding:60px;color:var(--t3)"><div style="font-size:48px;margin-bottom:16px">📭</div><div style="font-size:15px;font-weight:500">还没有错题</div><div style="font-size:13px;margin-top:4px">去录入第一道吧</div></div>';
 var pgs='';
 if(r.pages>1){
  pgs='<div class="pagination">';
  if(currentPage>1)pgs+='<div class="pg" onclick="loadErrors('+(currentPage-1)+')">←</div>';
  for(var i=1;i<=r.pages;i++)pgs+='<div class="pg '+(i==currentPage?'active':'')+'" onclick="loadErrors('+i+')">'+i+'</div>';
  if(currentPage<r.pages)pgs+='<div class="pg" onclick="loadErrors('+(currentPage+1)+')">→</div>';
  pgs+='</div>';
 }
 document.getElementById('errList').innerHTML='<div class="card" style="padding:0;overflow:hidden">'+h+pgs+'</div>';
}

function toggleAccordion(header){
 var item=header.parentElement;
 var accordion=item.parentElement;
 var isActive=item.classList.contains('active');
 accordion.querySelectorAll('.accordion-item.active').forEach(function(i){i.classList.remove('active');});
 if(!isActive)item.classList.add('active');
}

async function toggleDetail(eid){
 var detailEl=document.getElementById('errDetail-'+eid);
 if(!detailEl)return;
 // 如果已经展开则关闭
 if(detailEl.classList.contains('open')){
  detailEl.classList.remove('open');
  detailEl.innerHTML='';
  curErrorId=null;
  return;
 }
 // 关闭其他展开的
 document.querySelectorAll('.err-detail.open').forEach(function(el){
  el.classList.remove('open');
  el.innerHTML='';
 });
 renderDetailContent(eid, detailEl);
}

async function renderDetailContent(eid, container){
 var r=await(await fetch('/errors/'+eid)).json();
 if(!r||!r.id){toast('题目不存在','e');return}
 curErrorId=eid;
 var acc='';
 if(r.reference_answer){
  acc+='<div class="accordion-item"><div class="accordion-header" onclick="toggleAccordion(this)"><span>📝 参考答案</span><span class="acc-arrow">▶</span></div><div class="accordion-body">'+r.reference_answer+'</div></div>';
 }
 acc+='<div class="accordion-item"><div class="accordion-header" onclick="toggleAccordion(this)"><span>🧠 费曼复习</span><span class="acc-arrow">▶</span></div><div class="accordion-body" id="reviewAcc-'+eid+'"><div style="padding:8px 0;color:var(--t3);font-size:13px">点击上方「费曼复习」按钮开始</div></div></div>';
 var det=[];
 if(r.topics)det.push('<b>知识点：</b>'+r.topics);
 if(r.difficulty)det.push('<b>难度：</b>'+r.difficulty);
 if(r.error_reason)det.push('<b>错误原因：</b>'+r.error_reason);
 if(r.ocr_confidence)det.push('<b>OCR置信度：</b>'+(r.ocr_confidence*100).toFixed(1)+'%');
 if(r.image_path)det.push('<b>图片：</b>'+r.image_path);
 if(det.length){
  acc+='<div class="accordion-item"><div class="accordion-header" onclick="toggleAccordion(this)"><span>📋 详细信息</span><span class="acc-arrow">▶</span></div><div class="accordion-body">'+det.join('<br>')+'</div></div>';
 }
 var h='<div class="err-detail-inner">';
 h+='<p><b>题目：</b>'+(r.question_text||'')+'</p>';
 h+='<p><b>分类：</b>'+(r.subject||'?')+' > '+(r.chapter||'?')+'</p>';
 h+='<div class="btn-group"><button class="btn btn-p btn-sm" onclick="startReview('+eid+')">费曼复习</button>';
 h+='<button class="btn btn-g btn-sm" onclick="toggleMaster('+eid+')">'+(r.mastered?'取消掌握':'标记掌握')+'</button>';
 h+='<button class="btn btn-d btn-sm" onclick="deleteErr('+eid+')">删除</button></div>';
 h+='<div class="accordion">'+acc+'</div>';
 h+='</div>';
 container.innerHTML=h;
 container.classList.add('open');
 setTimeout(renderMath,100);
}

async function startReview(eid){
 var r=await(await fetch('/errors/'+eid)).json();
 if(!r||!r.question_text){toast('题目数据错误','e');return}
 var rev=await(await fetch('/review/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:r.question_text,error_id:eid})})).json();
 sessionId=rev.session_id;
 var accBody=document.getElementById('reviewAcc-'+eid);
 if(!accBody)return;
 accBody.innerHTML='<div class="review-qcard">'+
  '<div style="font-size:12px;color:var(--t2);margin-bottom:8px">'+r.question_text+'</div>'+
  '<div id="reviewQ">('+rev.step+'/'+rev.total+') '+rev.question+'</div>'+
  '<textarea id="ans" rows="3" placeholder="输入你的回答..."></textarea>'+
  '<div class="btn-group" style="margin-top:8px">'+
   '<button class="btn btn-p btn-sm" onclick="submitAnswer()">提交</button>'+
   '<button class="btn btn-g btn-sm" onclick="getHint()">提示</button>'+
  '</div></div>';
 // auto open the accordion
 var accItem=accBody.closest('.accordion-item');
 if(accItem)accItem.classList.add('active');
 setTimeout(function(){var el=document.getElementById('ans');if(el)el.focus();},100);
 setTimeout(renderMath,100);
}

async function submitAnswer(){
 var a=document.getElementById('ans').value.trim();if(!a||!sessionId)return;
 var r=await(await fetch('/review/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,answer:a})})).json();
 if(r.completed){document.getElementById('reviewQ').innerHTML='<div style="color:var(--s);font-weight:700">'+r.message+'</div>';document.getElementById('ans').style.display='none';sessionId=null;toast('复习完成');setTimeout(renderMath,100);}
 else{var cls='r-'+(r.result||'p');document.getElementById('reviewQ').innerHTML='<div class="review-box '+cls+'"><b>'+(r.result=='correct'?'正确':r.result=='wrong'?'错误':'部分正确')+'</b> '+r.feedback+'</div><div style="font-weight:600;margin-top:8px">('+r.step+'/'+r.total+') '+r.next_question+'</div>';document.getElementById('ans').value='';document.getElementById('ans').focus();setTimeout(renderMath,100);}
}

async function getHint(){if(!sessionId)return;var r=await(await fetch('/review/hint',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId})})).json();document.getElementById('reviewQ').innerHTML+='<div style="margin-top:8px;padding:8px 12px;background:var(--bg);border-radius:8px;font-size:13px;color:var(--p)">'+r.hint+'</div>';setTimeout(renderMath,100);}

async function toggleAnswer(eid){
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
async function toggleMaster(eid){
 await fetch('/errors/'+eid+'/master',{method:'POST'});
 var detailEl=document.getElementById('errDetail-'+eid);
 if(detailEl&&detailEl.classList.contains('open')){
  renderDetailContent(eid, detailEl);
 }
 loadErrors();
}

async function deleteErr(eid){
 if(!confirm('确认删除？'))return;
 await fetch('/errors/'+eid,{method:'DELETE'});
 var detailEl=document.getElementById('errDetail-'+eid);
 if(detailEl){detailEl.classList.remove('open');detailEl.innerHTML='';}
 loadErrors();toast('已删除');
}

async function exportCSV(){window.open('/export/csv','_blank');toast('CSV已下载');}
async function doBackup(){window.open('/backup','_blank');toast('备份已下载');}

async function loadStats(){
 var r=await(await fetch('/stats')).json();
 var tp=await(await fetch('/stats/topics')).json();
 document.getElementById('statCards').innerHTML='<div class="stat-card"><div class="num">'+r.total+'</div><div class="label">总错题</div></div><div class="stat-card"><div class="num">'+r.mastered+'</div><div class="label">已掌握</div></div><div class="stat-card"><div class="num">'+Math.round(r.mastered_rate*100)+'%</div><div class="label">掌握率</div></div><div class="stat-card"><div class="num">'+Object.keys(r.subjects||{}).length+'</div><div class="label">覆盖学科</div></div>';
 var sl=Object.keys(r.subjects||{}),sd=Object.values(r.subjects||{}),colors=['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
 if(sl.length>0){if(window._cs)window._cs.destroy();window._cs=new Chart(document.getElementById('chartSubject'),{type:'doughnut',data:{labels:sl,datasets:[{data:sd,backgroundColor:colors,borderWidth:0}]},options:{plugins:{legend:{position:'bottom',labels:{padding:16,font:{size:12}}}}}});}
 if(r.weak_chapters&&r.weak_chapters.length>0){if(window._cw)window._cw.destroy();window._cw=new Chart(document.getElementById('chartWeak'),{type:'bar',data:{labels:r.weak_chapters.slice(0,10).map(function(c){return c.chapter}),datasets:[{label:'未掌握',data:r.weak_chapters.slice(0,10).map(function(c){return c.unmastered}),backgroundColor:'#6366f1',borderRadius:6}]},options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{stepSize:1}}}}});}
 if(tp&&tp.length>0){
  var tc='';tp.forEach(function(t){var s=14+t.total*2;tc+='<span style="display:inline-block;margin:4px 8px;padding:4px 12px;background:var(--bg);border-radius:20px;font-size:'+s+'px;color:var(--p);font-weight:600">'+t.topic+'('+t.total+')</span>';});
  document.getElementById('tagCloud').innerHTML='<div class="card-header"><span class="dot dot-s"></span>知识点分布</div><div style="line-height:2.5">'+tc+'</div>';
 }
}
