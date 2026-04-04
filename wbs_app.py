from flask import Flask, request, jsonify
import json, os, uuid
from datetime import datetime

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'wbs.json')

def load():
    if not os.path.exists(DATA_FILE):
        data = {"projects": [], "tasks": [], "kpis": []}
        save(data)
        return data
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return HTML

@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify(load()['projects'])

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = load()
    b = request.get_json()
    p = {'id': str(uuid.uuid4()), 'name': b.get('name','').strip(), 'description': b.get('description','').strip(), 'created_at': datetime.now().isoformat()}
    if not p['name']: return jsonify({'error': '名前は必須'}), 400
    data['projects'].append(p)
    save(data)
    return jsonify(p), 201

@app.route('/api/projects/<pid>', methods=['DELETE'])
def del_project(pid):
    data = load()
    data['projects'] = [p for p in data['projects'] if p['id'] != pid]
    data['tasks'] = [t for t in data['tasks'] if t.get('project_id') != pid]
    save(data)
    return jsonify({'ok': True})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    data = load()
    pid = request.args.get('project_id')
    tasks = [t for t in data['tasks'] if t.get('project_id') == pid] if pid else data['tasks']
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = load()
    b = request.get_json()
    t = {'id': str(uuid.uuid4()), 'project_id': b.get('project_id',''), 'title': b.get('title','').strip(), 'status': 'todo', 'priority': b.get('priority','medium'), 'due_date': b.get('due_date',''), 'progress': 0, 'created_at': datetime.now().isoformat()}
    if not t['title']: return jsonify({'error': 'タイトルは必須'}), 400
    data['tasks'].append(t)
    save(data)
    return jsonify(t), 201

@app.route('/api/tasks/<tid>', methods=['PUT'])
def update_task(tid):
    data = load()
    for t in data['tasks']:
        if t['id'] == tid:
            b = request.get_json()
            for k in ['title','status','priority','due_date','progress']:
                if k in b: t[k] = b[k]
            save(data)
            return jsonify(t)
    return jsonify({'error': 'not found'}), 404

@app.route('/api/tasks/<tid>', methods=['DELETE'])
def del_task(tid):
    data = load()
    data['tasks'] = [t for t in data['tasks'] if t['id'] != tid]
    save(data)
    return jsonify({'ok': True})

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    return jsonify(load()['kpis'])

@app.route('/api/kpis', methods=['POST'])
def add_kpi():
    data = load()
    b = request.get_json()
    k = {'id': str(uuid.uuid4()), 'project_id': b.get('project_id',''), 'name': b.get('name','').strip(), 'target': float(b.get('target', 100)), 'current': float(b.get('current', 0)), 'unit': b.get('unit',''), 'created_at': datetime.now().isoformat()}
    if not k['name']: return jsonify({'error': '名前は必須'}), 400
    data['kpis'].append(k)
    save(data)
    return jsonify(k), 201

@app.route('/api/kpis/<kid>', methods=['PUT'])
def update_kpi(kid):
    data = load()
    for k in data['kpis']:
        if k['id'] == kid:
            b = request.get_json()
            for key in ['name','target','current','unit']:
                if key in b: k[key] = float(b[key]) if key in ['target','current'] else b[key]
            save(data)
            return jsonify(k)
    return jsonify({'error': 'not found'}), 404

@app.route('/api/kpis/<kid>', methods=['DELETE'])
def del_kpi(kid):
    data = load()
    data['kpis'] = [k for k in data['kpis'] if k['id'] != kid]
    save(data)
    return jsonify({'ok': True})

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WBSアクション管理</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Helvetica Neue',Arial,sans-serif;background:#f0f2f5;color:#333}
header{background:linear-gradient(135deg,#1a237e,#1976d2);color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px}
header h1{font-size:20px}
nav{display:flex;background:#fff;border-bottom:2px solid #e0e0e0;overflow-x:auto}
nav button{flex:1;min-width:80px;padding:14px 8px;border:none;background:none;font-size:14px;cursor:pointer;color:#666;border-bottom:3px solid transparent;transition:.2s}
nav button.active{color:#1976d2;border-bottom-color:#1976d2;font-weight:bold}
.page{display:none;padding:16px}
.page.active{display:block}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.form-row{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.form-row input,.form-row select{flex:1;min-width:120px;padding:10px;border:1px solid #ddd;border-radius:8px;font-size:14px}
.btn{padding:10px 16px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:bold;transition:.2s}
.btn-primary{background:#1976d2;color:#fff}
.btn-primary:hover{background:#1565c0}
.btn-danger{background:#ef5350;color:#fff;padding:6px 10px;font-size:12px}
.btn-small{padding:6px 10px;font-size:12px}
.item{display:flex;align-items:center;gap:10px;padding:12px;border-radius:8px;background:#f9f9f9;margin-bottom:8px}
.item-title{flex:1;font-size:14px;font-weight:500}
.badge{padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold}
.badge-todo{background:#e3f2fd;color:#1976d2}
.badge-doing{background:#fff3e0;color:#f57c00}
.badge-done{background:#e8f5e9;color:#388e3c}
.badge-high{background:#ffebee;color:#c62828}
.badge-medium{background:#fff8e1;color:#f9a825}
.badge-low{background:#f3e5f5;color:#7b1fa2}
.progress-bar{height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden;width:100px}
.progress-fill{height:100%;background:linear-gradient(90deg,#1976d2,#42a5f5);border-radius:4px;transition:.3s}
.kpi-card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.kpi-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.kpi-name{font-weight:bold;font-size:15px}
.kpi-value{font-size:22px;font-weight:bold;color:#1976d2}
.kpi-target{font-size:12px;color:#999}
.kpi-progress{height:10px;background:#e0e0e0;border-radius:5px;overflow:hidden;margin:8px 0}
.kpi-fill{height:100%;background:linear-gradient(90deg,#43a047,#66bb6a);border-radius:5px;transition:.3s}
.project-card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:4px solid #1976d2}
.project-header{display:flex;justify-content:space-between;align-items:center}
.project-name{font-weight:bold;font-size:16px}
.project-desc{color:#666;font-size:13px;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.stat-card{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.stat-num{font-size:28px;font-weight:bold;color:#1976d2}
.stat-label{font-size:12px;color:#999;margin-top:4px}
.select-project{width:100%;padding:10px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px}
h3{font-size:16px;margin-bottom:12px;color:#333}
.empty{text-align:center;color:#bbb;padding:24px;font-size:14px}
</style>
</head>
<body>
<header>
  <span style="font-size:24px">📋</span>
  <h1>WBSアクション管理</h1>
</header>
<nav>
  <button class="active" onclick="showPage('dashboard')">📊 ダッシュボード</button>
  <button onclick="showPage('projects')">📁 プロジェクト</button>
  <button onclick="showPage('tasks')">✅ タスク</button>
  <button onclick="showPage('kpis')">📈 KPI</button>
</nav>

<div id="dashboard" class="page active">
  <div class="stats">
    <div class="stat-card"><div class="stat-num" id="stat-projects">0</div><div class="stat-label">プロジェクト</div></div>
    <div class="stat-card"><div class="stat-num" id="stat-tasks">0</div><div class="stat-label">タスク</div></div>
    <div class="stat-card"><div class="stat-num" id="stat-done">0</div><div class="stat-label">完了</div></div>
  </div>
  <div class="card">
    <h3>📌 直近タスク（未完了）</h3>
    <div id="dash-tasks"></div>
  </div>
  <div class="card">
    <h3>📈 KPI進捗</h3>
    <div id="dash-kpis"></div>
  </div>
</div>

<div id="projects" class="page">
  <div class="card">
    <h3>➕ プロジェクト追加</h3>
    <div class="form-row">
      <input id="proj-name" placeholder="プロジェクト名" />
      <input id="proj-desc" placeholder="説明（任意）" />
      <button class="btn btn-primary" onclick="addProject()">追加</button>
    </div>
  </div>
  <div id="projects-list"></div>
</div>

<div id="tasks" class="page">
  <div class="card">
    <h3>➕ タスク追加</h3>
    <div class="form-row">
      <input id="task-title" placeholder="タスク名" />
      <select id="task-project"><option value="">プロジェクト選択</option></select>
      <select id="task-priority">
        <option value="high">高</option>
        <option value="medium" selected>中</option>
        <option value="low">低</option>
      </select>
      <input id="task-due" type="date" />
      <button class="btn btn-primary" onclick="addTask()">追加</button>
    </div>
  </div>
  <div class="form-row" style="padding:0 4px">
    <select class="select-project" id="filter-project" onchange="loadTasks()">
      <option value="">全プロジェクト</option>
    </select>
  </div>
  <div id="tasks-list"></div>
</div>

<div id="kpis" class="page">
  <div class="card">
    <h3>➕ KPI追加</h3>
    <div class="form-row">
      <input id="kpi-name" placeholder="KPI名" />
      <select id="kpi-project"><option value="">プロジェクト選択</option></select>
      <input id="kpi-target" type="number" placeholder="目標値" style="max-width:100px" />
      <input id="kpi-unit" placeholder="単位" style="max-width:80px" />
      <button class="btn btn-primary" onclick="addKpi()">追加</button>
    </div>
  </div>
  <div id="kpis-list"></div>
</div>

<script>
let projects=[], tasks=[], kpis=[];

async function api(method, path, body){
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(path,opts);
  return r.json();
}

async function loadAll(){
  [projects,tasks,kpis]=await Promise.all([
    api('GET','/api/projects'),
    api('GET','/api/tasks'),
    api('GET','/api/kpis')
  ]);
  renderDashboard();
  renderProjects();
  renderTasks();
  renderKpis();
  updateSelects();
}

function updateSelects(){
  const opts=projects.map(p=>`<option value="${p.id}">${p.name}</option>`).join('');
  ['task-project','kpi-project'].forEach(id=>{
    const el=document.getElementById(id);
    el.innerHTML='<option value="">選択なし</option>'+opts;
  });
  const f=document.getElementById('filter-project');
  f.innerHTML='<option value="">全プロジェクト</option>'+opts;
}

function showPage(id){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}

function renderDashboard(){
  document.getElementById('stat-projects').textContent=projects.length;
  document.getElementById('stat-tasks').textContent=tasks.length;
  document.getElementById('stat-done').textContent=tasks.filter(t=>t.status==='done').length;
  const pending=tasks.filter(t=>t.status!=='done').slice(0,5);
  document.getElementById('dash-tasks').innerHTML=pending.length
    ?pending.map(t=>`<div class="item"><span class="item-title">${t.title}</span><span class="badge badge-${t.status}">${statusLabel(t.status)}</span><span class="badge badge-${t.priority}">${priorityLabel(t.priority)}</span></div>`).join('')
    :'<div class="empty">未完了タスクなし</div>';
  document.getElementById('dash-kpis').innerHTML=kpis.length
    ?kpis.map(k=>{const pct=Math.min(100,Math.round(k.current/k.target*100));return`<div class="kpi-card"><div class="kpi-header"><span class="kpi-name">${k.name}</span><span class="kpi-value">${k.current}${k.unit}</span></div><div class="kpi-target">目標: ${k.target}${k.unit}</div><div class="kpi-progress"><div class="kpi-fill" style="width:${pct}%"></div></div><small>${pct}%</small></div>`}).join('')
    :'<div class="empty">KPIなし</div>';
}

function renderProjects(){
  const el=document.getElementById('projects-list');
  if(!projects.length){el.innerHTML='<div class="empty">プロジェクトなし</div>';return;}
  el.innerHTML=projects.map(p=>{
    const ptasks=tasks.filter(t=>t.project_id===p.id);
    const done=ptasks.filter(t=>t.status==='done').length;
    return`<div class="project-card">
      <div class="project-header">
        <div><div class="project-name">📁 ${p.name}</div><div class="project-desc">${p.description||''}</div></div>
        <button class="btn btn-danger" onclick="delProject('${p.id}')">削除</button>
      </div>
      <div style="margin-top:8px;font-size:13px;color:#666">タスク: ${ptasks.length}件 / 完了: ${done}件</div>
    </div>`;
  }).join('');
}

async function loadTasks(){
  const pid=document.getElementById('filter-project').value;
  tasks=await api('GET','/api/tasks'+(pid?'?project_id='+pid:''));
  renderTasks();
}

function renderTasks(){
  const el=document.getElementById('tasks-list');
  if(!tasks.length){el.innerHTML='<div class="empty">タスクなし</div>';return;}
  el.innerHTML=tasks.map(t=>`
    <div class="item" id="task-${t.id}">
      <div style="flex:1">
        <div class="item-title">${t.title}</div>
        <div style="display:flex;gap:6px;margin-top:6px;align-items:center;flex-wrap:wrap">
          <span class="badge badge-${t.priority}">${priorityLabel(t.priority)}</span>
          ${t.due_date?`<span style="font-size:11px;color:#999">📅${t.due_date}</span>`:''}
          <div class="progress-bar"><div class="progress-fill" style="width:${t.progress}%"></div></div>
          <span style="font-size:11px">${t.progress}%</span>
        </div>
      </div>
      <select style="padding:6px;border:1px solid #ddd;border-radius:6px;font-size:13px" onchange="updateTaskStatus('${t.id}',this.value)">
        <option value="todo" ${t.status==='todo'?'selected':''}>未着手</option>
        <option value="doing" ${t.status==='doing'?'selected':''}>進行中</option>
        <option value="done" ${t.status==='done'?'selected':''}>完了</option>
      </select>
      <input type="range" min="0" max="100" value="${t.progress}" style="width:80px" onchange="updateProgress('${t.id}',this.value)" />
      <button class="btn btn-danger" onclick="delTask('${t.id}')">削除</button>
    </div>`).join('');
}

function renderKpis(){
  const el=document.getElementById('kpis-list');
  if(!kpis.length){el.innerHTML='<div class="empty">KPIなし</div>';return;}
  el.innerHTML=kpis.map(k=>{
    const pct=Math.min(100,Math.round(k.current/k.target*100));
    return`<div class="kpi-card">
      <div class="kpi-header">
        <span class="kpi-name">${k.name}</span>
        <button class="btn btn-danger" onclick="delKpi('${k.id}')">削除</button>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin:8px 0">
        <span class="kpi-value">${k.current}${k.unit}</span>
        <span class="kpi-target">/ 目標 ${k.target}${k.unit}</span>
      </div>
      <div class="kpi-progress"><div class="kpi-fill" style="width:${pct}%"></div></div>
      <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:12px">
        <span>${pct}%達成</span>
        <div style="display:flex;gap:6px">
          <input type="number" value="${k.current}" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:6px;font-size:13px" id="kpi-cur-${k.id}" />
          <button class="btn btn-primary btn-small" onclick="updateKpi('${k.id}')">更新</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function statusLabel(s){return{todo:'未着手',doing:'進行中',done:'完了'}[s]||s}
function priorityLabel(p){return{high:'高',medium:'中',low:'低'}[p]||p}

async function addProject(){
  const name=document.getElementById('proj-name').value.trim();
  const desc=document.getElementById('proj-desc').value.trim();
  if(!name){alert('プロジェクト名を入力してください');return;}
  await api('POST','/api/projects',{name,description:desc});
  document.getElementById('proj-name').value='';
  document.getElementById('proj-desc').value='';
  loadAll();
}

async function delProject(id){
  if(!confirm('削除しますか？関連タスクも削除されます。'))return;
  await api('DELETE','/api/projects/'+id);
  loadAll();
}

async function addTask(){
  const title=document.getElementById('task-title').value.trim();
  const project_id=document.getElementById('task-project').value;
  const priority=document.getElementById('task-priority').value;
  const due_date=document.getElementById('task-due').value;
  if(!title){alert('タスク名を入力してください');return;}
  await api('POST','/api/tasks',{title,project_id,priority,due_date});
  document.getElementById('task-title').value='';
  loadAll();
}

async function updateTaskStatus(id,status){
  await api('PUT','/api/tasks/'+id,{status});
  loadAll();
}

async function updateProgress(id,progress){
  await api('PUT','/api/tasks/'+id,{progress:parseInt(progress)});
  loadAll();
}

async function delTask(id){
  if(!confirm('削除しますか？'))return;
  await api('DELETE','/api/tasks/'+id);
  loadAll();
}

async function addKpi(){
  const name=document.getElementById('kpi-name').value.trim();
  const project_id=document.getElementById('kpi-project').value;
  const target=document.getElementById('kpi-target').value;
  const unit=document.getElementById('kpi-unit').value;
  if(!name||!target){alert('KPI名と目標値を入力してください');return;}
  await api('POST','/api/kpis',{name,project_id,target,unit});
  document.getElementById('kpi-name').value='';
  document.getElementById('kpi-target').value='';
  document.getElementById('kpi-unit').value='';
  loadAll();
}

async function updateKpi(id){
  const current=document.getElementById('kpi-cur-'+id).value;
  await api('PUT','/api/kpis/'+id,{current});
  loadAll();
}

async function delKpi(id){
  if(!confirm('削除しますか？'))return;
  await api('DELETE','/api/kpis/'+id);
  loadAll();
}

loadAll();
</script>
</body>
</html>"""

if __name__ == '__main__':
    app.run(debug=True, port=5001)
