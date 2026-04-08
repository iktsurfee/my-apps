from flask import Flask, request, jsonify
import json, os, uuid
from datetime import datetime, date

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wbs.json')

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

# ── Projects ──
@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify(load()['projects'])

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = load()
    b = request.get_json()
    p = {'id': str(uuid.uuid4()), 'name': b.get('name','').strip(), 'description': b.get('description','').strip(), 'color': b.get('color','#1976d2'), 'created_at': datetime.now().isoformat()}
    if not p['name']: return jsonify({'error': '名前は必須'}), 400
    data['projects'].append(p)
    save(data)
    return jsonify(p), 201

@app.route('/api/projects/<pid>', methods=['PUT'])
def update_project(pid):
    data = load()
    b = request.get_json()
    for p in data['projects']:
        if p['id'] == pid:
            p['name'] = b.get('name', p['name']).strip()
            p['description'] = b.get('description', p['description']).strip()
            p['color'] = b.get('color', p['color'])
            save(data)
            return jsonify(p)
    return jsonify({'error': 'not found'}), 404

@app.route('/api/projects/<pid>', methods=['DELETE'])
def del_project(pid):
    data = load()
    data['projects'] = [p for p in data['projects'] if p['id'] != pid]
    data['tasks'] = [t for t in data['tasks'] if t.get('project_id') != pid]
    data['kpis'] = [k for k in data['kpis'] if k.get('project_id') != pid]
    save(data)
    return jsonify({'ok': True})

# ── Tasks ──
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
    t = {'id': str(uuid.uuid4()), 'project_id': b.get('project_id',''), 'title': b.get('title','').strip(), 'description': b.get('description','').strip(), 'assignee': b.get('assignee','').strip(), 'priority': b.get('priority','medium'), 'status': 'todo', 'progress': 0, 'due_date': b.get('due_date',''), 'created_at': datetime.now().isoformat()}
    if not t['title']: return jsonify({'error': 'タイトルは必須'}), 400
    data['tasks'].append(t)
    save(data)
    return jsonify(t), 201

@app.route('/api/tasks/<tid>', methods=['PUT'])
def update_task(tid):
    data = load()
    b = request.get_json()
    for t in data['tasks']:
        if t['id'] == tid:
            for k in ['title','description','assignee','priority','status','progress','due_date']:
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

# ── KPIs ──
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    data = load()
    pid = request.args.get('project_id')
    kpis = [k for k in data['kpis'] if k.get('project_id') == pid] if pid else data['kpis']
    return jsonify(kpis)

@app.route('/api/kpis', methods=['POST'])
def add_kpi():
    data = load()
    b = request.get_json()
    k = {'id': str(uuid.uuid4()), 'project_id': b.get('project_id',''), 'name': b.get('name','').strip(), 'target': float(b.get('target',100)), 'current': float(b.get('current',0)), 'unit': b.get('unit','').strip(), 'created_at': datetime.now().isoformat()}
    if not k['name']: return jsonify({'error': '名前は必須'}), 400
    data['kpis'].append(k)
    save(data)
    return jsonify(k), 201

@app.route('/api/kpis/<kid>', methods=['PUT'])
def update_kpi(kid):
    data = load()
    b = request.get_json()
    for k in data['kpis']:
        if k['id'] == kid:
            for key in ['name','unit']:
                if key in b: k[key] = b[key]
            for key in ['target','current']:
                if key in b: k[key] = float(b[key])
            save(data)
            return jsonify(k)
    return jsonify({'error': 'not found'}), 404

@app.route('/api/kpis/<kid>', methods=['DELETE'])
def del_kpi(kid):
    data = load()
    data['kpis'] = [k for k in data['kpis'] if k['id'] != kid]
    save(data)
    return jsonify({'ok': True})

@app.route('/api/summary', methods=['GET'])
def summary():
    data = load()
    tasks = data['tasks']
    today = str(date.today())
    overdue = sum(1 for t in tasks if t.get('due_date') and t['status'] != 'done' and t['due_date'] < today)
    return jsonify({
        'total_projects': len(data['projects']),
        'total_tasks': len(tasks),
        'done_tasks': sum(1 for t in tasks if t['status'] == 'done'),
        'doing_tasks': sum(1 for t in tasks if t['status'] == 'doing'),
        'overdue_tasks': overdue,
    })

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WBSアクション管理</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Helvetica Neue',Arial,sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
header{background:linear-gradient(135deg,#0d47a1,#1976d2);color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px}
header h1{font-size:20px;font-weight:700}
nav{display:flex;background:#fff;border-bottom:2px solid #e0e0e0;overflow-x:auto}
nav button{flex:1;min-width:80px;padding:12px 8px;border:none;background:none;font-size:13px;cursor:pointer;color:#666;border-bottom:3px solid transparent;transition:.2s}
nav button.active{color:#1976d2;border-bottom-color:#1976d2;font-weight:700}
.page{display:none;padding:16px;max-width:900px;margin:0 auto}
.page.active{display:block}

/* Stats */
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}
.stat-card{background:#fff;border-radius:12px;padding:14px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.stat-num{font-size:24px;font-weight:700;color:#1976d2}
.stat-num.danger{color:#e53935}
.stat-label{font-size:11px;color:#999;margin-top:2px}

/* Project Card */
.project-block{background:#fff;border-radius:14px;margin-bottom:16px;box-shadow:0 2px 10px rgba(0,0,0,.08);overflow:hidden}
.project-header{padding:14px 16px;display:flex;align-items:center;justify-content:space-between;cursor:pointer}
.project-header-left{display:flex;align-items:center;gap:10px}
.project-color-bar{width:4px;height:40px;border-radius:2px}
.project-name{font-size:16px;font-weight:700}
.project-desc{font-size:12px;color:#999;margin-top:2px}
.project-meta{display:flex;gap:8px;align-items:center}
.project-stats{display:flex;gap:6px}
.ps-badge{padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600}
.ps-total{background:#e3f2fd;color:#1565c0}
.ps-done{background:#e8f5e9;color:#2e7d32}
.ps-doing{background:#fff3e0;color:#e65100}
.chevron{font-size:12px;color:#aaa;transition:.2s}
.chevron.open{transform:rotate(180deg)}
.project-body{display:none;border-top:1px solid #f0f0f0;padding:16px}
.project-body.open{display:block}

/* Sections inside project */
.section-title{font-size:13px;font-weight:700;color:#555;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.add-btn{padding:5px 10px;border:1px dashed #aaa;border-radius:8px;background:none;cursor:pointer;font-size:12px;color:#888;margin-bottom:10px;transition:.2s}
.add-btn:hover{border-color:#1976d2;color:#1976d2}

/* Task item */
.task-item{background:#f8f9fb;border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #e0e0e0}
.task-item.status-doing{border-left-color:#fb8c00}
.task-item.status-done{border-left-color:#43a047;opacity:.8}
.task-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.task-title{font-size:14px;font-weight:600;flex:1}
.task-title.done-text{text-decoration:line-through;color:#aaa}
.task-meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px}
.badge{padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.badge-todo{background:#e3f2fd;color:#1565c0}
.badge-doing{background:#fff3e0;color:#e65100}
.badge-done{background:#e8f5e9;color:#2e7d32}
.badge-high{background:#ffebee;color:#c62828}
.badge-medium{background:#fff8e1;color:#f57f17}
.badge-low{background:#f3e5f5;color:#6a1b9a}
.progress-bar{height:6px;background:#e0e0e0;border-radius:3px;overflow:hidden;width:80px}
.progress-fill{height:100%;background:linear-gradient(90deg,#1976d2,#42a5f5);border-radius:3px}
.task-actions{display:flex;gap:4px}
.btn-sm{padding:4px 8px;border:none;border-radius:6px;cursor:pointer;font-size:11px;font-weight:600}
.btn-edit{background:#e3f2fd;color:#1565c0}
.btn-del{background:#ffebee;color:#c62828}
.btn-save{background:#e8f5e9;color:#2e7d32}
.btn-cancel{background:#f5f5f5;color:#666}

/* KPI item */
.kpi-item{background:#f8f9fb;border-radius:10px;padding:12px;margin-bottom:8px}
.kpi-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.kpi-name{font-size:14px;font-weight:600}
.kpi-value{font-size:18px;font-weight:700;color:#1976d2}
.kpi-bar{height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden;margin:4px 0}
.kpi-fill{height:100%;background:linear-gradient(90deg,#43a047,#76c442);border-radius:4px;transition:.4s}
.kpi-footer{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#999}

/* Inline edit form */
.edit-form{background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:12px;margin-top:8px;display:none}
.edit-form.show{display:block}
.form-row{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.form-row input,.form-row select,.form-row textarea{flex:1;min-width:100px;padding:8px;border:1px solid #ddd;border-radius:8px;font-size:13px}
.form-row label{font-size:11px;color:#888;width:100%;margin-bottom:2px}
.form-actions{display:flex;gap:6px;margin-top:8px}

/* Add form */
.add-form{background:#f0f7ff;border:1px dashed #90caf9;border-radius:10px;padding:12px;margin-bottom:10px;display:none}
.add-form.show{display:block}

/* Utility */
.empty{text-align:center;color:#bbb;padding:16px;font-size:13px}
.divider{border:none;border-top:1px solid #f0f0f0;margin:12px 0}
.color-dot{width:12px;height:12px;border-radius:50%;display:inline-block}
select.status-select{padding:4px 6px;border:1px solid #ddd;border-radius:6px;font-size:12px;cursor:pointer}

/* Dashboard */
.dash-project{background:#fff;border-radius:12px;padding:14px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:4px solid #1976d2}
.dash-proj-name{font-weight:700;font-size:15px;margin-bottom:8px}
.dash-task-row{display:flex;justify-content:space-between;align-items:center;font-size:13px;padding:4px 0;border-bottom:1px solid #f5f5f5}
.dash-task-row:last-child{border-bottom:none}
</style>
</head>
<body>
<header>
  <span style="font-size:26px">📋</span>
  <h1>WBSアクション管理</h1>
</header>
<nav>
  <button class="active" onclick="showPage('dashboard',this)">📊 ダッシュボード</button>
  <button onclick="showPage('projects',this)">📁 プロジェクト</button>
</nav>

<!-- Dashboard -->
<div id="dashboard" class="page active">
  <div class="stats">
    <div class="stat-card"><div class="stat-num" id="s-proj">0</div><div class="stat-label">プロジェクト</div></div>
    <div class="stat-card"><div class="stat-num" id="s-tasks">0</div><div class="stat-label">総タスク</div></div>
    <div class="stat-card"><div class="stat-num" id="s-done">0</div><div class="stat-label">完了</div></div>
    <div class="stat-card"><div class="stat-num" id="s-doing">0</div><div class="stat-label">進行中</div></div>
    <div class="stat-card"><div class="stat-num danger" id="s-over">0</div><div class="stat-label">期限超過</div></div>
  </div>
  <div id="dash-content"></div>
</div>

<!-- Projects (main view) -->
<div id="projects" class="page">
  <!-- Add Project Form -->
  <div style="background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h3 style="font-size:15px">📁 プロジェクト一覧</h3>
      <button class="add-btn" onclick="toggleAddProject()">＋ プロジェクト追加</button>
    </div>
    <div class="add-form" id="add-project-form">
      <div class="form-row">
        <input id="np-name" placeholder="プロジェクト名" />
        <input id="np-desc" placeholder="説明（任意）" />
        <input id="np-color" type="color" value="#1976d2" style="max-width:50px;padding:4px" />
      </div>
      <div class="form-actions">
        <button class="btn-sm btn-save" onclick="addProject()">追加</button>
        <button class="btn-sm btn-cancel" onclick="toggleAddProject()">キャンセル</button>
      </div>
    </div>
  </div>
  <div id="projects-list"></div>
</div>

<script>
let projects=[], tasks=[], kpis=[];

async function api(method,path,body){
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(path,opts);
  return r.json();
}

function showPage(id,btn){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if(btn) btn.classList.add('active');
}

async function loadAll(){
  [projects,tasks,kpis]=await Promise.all([
    api('GET','/api/projects'),
    api('GET','/api/tasks'),
    api('GET','/api/kpis')
  ]);
  const s=await api('GET','/api/summary');
  document.getElementById('s-proj').textContent=s.total_projects;
  document.getElementById('s-tasks').textContent=s.total_tasks;
  document.getElementById('s-done').textContent=s.done_tasks;
  document.getElementById('s-doing').textContent=s.doing_tasks;
  document.getElementById('s-over').textContent=s.overdue_tasks;
  renderDashboard();
  renderProjects();
}

// ── Dashboard ──
function renderDashboard(){
  const el=document.getElementById('dash-content');
  if(!projects.length){el.innerHTML='<div class="empty">プロジェクトなし</div>';return;}
  el.innerHTML=projects.map(p=>{
    const ptasks=tasks.filter(t=>t.project_id===p.id);
    const pkpis=kpis.filter(k=>k.project_id===p.id);
    const done=ptasks.filter(t=>t.status==='done').length;
    const doing=ptasks.filter(t=>t.status==='doing').length;
    const pct=ptasks.length?Math.round(done/ptasks.length*100):0;
    return`<div class="dash-project" style="border-left-color:${p.color||'#1976d2'}">
      <div class="dash-proj-name"><span class="color-dot" style="background:${p.color||'#1976d2'}"></span> ${p.name}</div>
      <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
        <span class="ps-badge ps-total">タスク ${ptasks.length}</span>
        <span class="ps-badge ps-done">完了 ${done}</span>
        <span class="ps-badge ps-doing">進行 ${doing}</span>
        ${pkpis.length?`<span class="ps-badge" style="background:#f3e5f5;color:#6a1b9a">KPI ${pkpis.length}</span>`:''}
      </div>
      <div class="progress-bar" style="width:100%;height:8px;margin-bottom:8px"><div class="progress-fill" style="width:${pct}%"></div></div>
      ${ptasks.filter(t=>t.status!=='done').slice(0,3).map(t=>`
        <div class="dash-task-row">
          <span>${t.title}</span>
          <span class="badge badge-${t.status}">${statusLabel(t.status)}</span>
        </div>`).join('')}
      ${pkpis.map(k=>{const pp=Math.min(100,Math.round(k.current/k.target*100));return`
        <div class="dash-task-row">
          <span>📈 ${k.name}: ${k.current}/${k.target}${k.unit}</span>
          <span style="color:#43a047;font-weight:bold">${pp}%</span>
        </div>`}).join('')}
    </div>`;
  }).join('');
}

// ── Projects ──
function renderProjects(){
  const el=document.getElementById('projects-list');
  if(!projects.length){el.innerHTML='<div class="empty">プロジェクトなし</div>';return;}
  el.innerHTML=projects.map(p=>renderProjectBlock(p)).join('');
}

function renderProjectBlock(p){
  const ptasks=tasks.filter(t=>t.project_id===p.id);
  const pkpis=kpis.filter(k=>k.project_id===p.id);
  const done=ptasks.filter(t=>t.status==='done').length;
  const doing=ptasks.filter(t=>t.status==='doing').length;
  return`<div class="project-block" id="pb-${p.id}">
    <div class="project-header" onclick="toggleProject('${p.id}')">
      <div class="project-header-left">
        <div class="project-color-bar" style="background:${p.color||'#1976d2'}"></div>
        <div>
          <div class="project-name">${p.name}</div>
          ${p.description?`<div class="project-desc">${p.description}</div>`:''}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <div class="project-stats">
          <span class="ps-badge ps-total">${ptasks.length}件</span>
          <span class="ps-badge ps-done">✅${done}</span>
          ${doing?`<span class="ps-badge ps-doing">🔄${doing}</span>`:''}
          ${pkpis.length?`<span class="ps-badge" style="background:#f3e5f5;color:#6a1b9a">📈${pkpis.length}</span>`:''}
        </div>
        <div style="display:flex;gap:4px" onclick="event.stopPropagation()">
          <button class="btn-sm btn-edit" onclick="showEditProject('${p.id}')">編集</button>
          <button class="btn-sm btn-del" onclick="delProject('${p.id}')">削除</button>
        </div>
        <span class="chevron" id="chev-${p.id}">▼</span>
      </div>
    </div>

    <!-- Project Edit Form -->
    <div class="edit-form" id="edit-proj-${p.id}" style="margin:0 16px 8px">
      <div class="form-row">
        <input id="ep-name-${p.id}" value="${p.name}" placeholder="プロジェクト名" />
        <input id="ep-desc-${p.id}" value="${p.description||''}" placeholder="説明" />
        <input id="ep-color-${p.id}" type="color" value="${p.color||'#1976d2'}" style="max-width:50px;padding:4px" />
      </div>
      <div class="form-actions">
        <button class="btn-sm btn-save" onclick="saveProject('${p.id}')">保存</button>
        <button class="btn-sm btn-cancel" onclick="hideEditProject('${p.id}')">キャンセル</button>
      </div>
    </div>

    <div class="project-body" id="body-${p.id}">
      <!-- Tasks Section -->
      <div class="section-title">✅ タスク</div>
      <button class="add-btn" onclick="showAddTask('${p.id}')">＋ タスク追加</button>
      <div class="add-form" id="add-task-${p.id}">
        <div class="form-row">
          <input id="nt-title-${p.id}" placeholder="タスク名" />
          <input id="nt-assignee-${p.id}" placeholder="担当者" style="max-width:120px" />
        </div>
        <div class="form-row">
          <div style="flex:1"><label>優先度</label>
            <select id="nt-priority-${p.id}">
              <option value="high">高</option>
              <option value="medium" selected>中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div style="flex:1"><label>期限</label><input id="nt-due-${p.id}" type="date" /></div>
        </div>
        <div class="form-actions">
          <button class="btn-sm btn-save" onclick="addTask('${p.id}')">追加</button>
          <button class="btn-sm btn-cancel" onclick="hideAddTask('${p.id}')">キャンセル</button>
        </div>
      </div>
      <div id="tasks-${p.id}">
        ${ptasks.length?ptasks.map(t=>renderTask(t)).join(''):'<div class="empty">タスクなし</div>'}
      </div>

      <hr class="divider">

      <!-- KPI Section -->
      <div class="section-title">📈 KPI</div>
      <button class="add-btn" onclick="showAddKpi('${p.id}')">＋ KPI追加</button>
      <div class="add-form" id="add-kpi-${p.id}">
        <div class="form-row">
          <input id="nk-name-${p.id}" placeholder="KPI名" />
          <input id="nk-target-${p.id}" type="number" placeholder="目標値" style="max-width:100px" />
          <input id="nk-unit-${p.id}" placeholder="単位" style="max-width:80px" />
        </div>
        <div class="form-actions">
          <button class="btn-sm btn-save" onclick="addKpi('${p.id}')">追加</button>
          <button class="btn-sm btn-cancel" onclick="hideAddKpi('${p.id}')">キャンセル</button>
        </div>
      </div>
      <div id="kpis-${p.id}">
        ${pkpis.length?pkpis.map(k=>renderKpi(k)).join(''):'<div class="empty">KPIなし</div>'}
      </div>
    </div>
  </div>`;
}

function renderTask(t){
  return`<div class="task-item status-${t.status}" id="ti-${t.id}">
    <div class="task-top">
      <div class="task-title ${t.status==='done'?'done-text':''}">${t.title}${t.assignee?` <span style="font-size:11px;color:#999">@${t.assignee}</span>`:''}</div>
      <div class="task-actions">
        <button class="btn-sm btn-edit" onclick="showEditTask('${t.id}')">編集</button>
        <button class="btn-sm btn-del" onclick="delTask('${t.id}')">削除</button>
      </div>
    </div>
    <div class="task-meta">
      <span class="badge badge-${t.priority}">${priorityLabel(t.priority)}</span>
      <select class="status-select badge-${t.status}" onchange="updateTaskStatus('${t.id}',this.value)">
        <option value="todo" ${t.status==='todo'?'selected':''}>未着手</option>
        <option value="doing" ${t.status==='doing'?'selected':''}>進行中</option>
        <option value="done" ${t.status==='done'?'selected':''}>完了</option>
      </select>
      ${t.due_date?`<span style="font-size:11px;color:#999">📅${t.due_date}</span>`:''}
      <div class="progress-bar"><div class="progress-fill" style="width:${t.progress}%"></div></div>
      <span style="font-size:11px">${t.progress}%</span>
      <input type="range" min="0" max="100" value="${t.progress}" style="width:70px" onchange="updateTaskProgress('${t.id}',this.value)" />
    </div>
    <div class="edit-form" id="edit-task-${t.id}">
      <div class="form-row">
        <input id="et-title-${t.id}" value="${t.title}" placeholder="タスク名" />
        <input id="et-assignee-${t.id}" value="${t.assignee||''}" placeholder="担当者" style="max-width:120px" />
      </div>
      <div class="form-row">
        <div style="flex:1"><label>優先度</label>
          <select id="et-priority-${t.id}">
            <option value="high" ${t.priority==='high'?'selected':''}>高</option>
            <option value="medium" ${t.priority==='medium'?'selected':''}>中</option>
            <option value="low" ${t.priority==='low'?'selected':''}>低</option>
          </select>
        </div>
        <div style="flex:1"><label>期限</label><input id="et-due-${t.id}" type="date" value="${t.due_date||''}" /></div>
      </div>
      <div class="form-actions">
        <button class="btn-sm btn-save" onclick="saveTask('${t.id}')">保存</button>
        <button class="btn-sm btn-cancel" onclick="hideEditTask('${t.id}')">キャンセル</button>
      </div>
    </div>
  </div>`;
}

function renderKpi(k){
  const pct=Math.min(100,Math.round(k.current/k.target*100));
  return`<div class="kpi-item" id="ki-${k.id}">
    <div class="kpi-top">
      <span class="kpi-name">${k.name}</span>
      <div style="display:flex;gap:4px">
        <button class="btn-sm btn-edit" onclick="showEditKpi('${k.id}')">編集</button>
        <button class="btn-sm btn-del" onclick="delKpi('${k.id}')">削除</button>
      </div>
    </div>
    <div class="kpi-bar"><div class="kpi-fill" style="width:${pct}%"></div></div>
    <div class="kpi-footer">
      <span>${pct}%達成</span>
      <span class="kpi-value">${k.current}<span style="font-size:12px;color:#999">/${k.target}${k.unit}</span></span>
    </div>
    <div class="edit-form" id="edit-kpi-${k.id}">
      <div class="form-row">
        <input id="ek-name-${k.id}" value="${k.name}" placeholder="KPI名" />
        <input id="ek-current-${k.id}" type="number" value="${k.current}" placeholder="現在値" style="max-width:100px" />
        <input id="ek-target-${k.id}" type="number" value="${k.target}" placeholder="目標値" style="max-width:100px" />
        <input id="ek-unit-${k.id}" value="${k.unit||''}" placeholder="単位" style="max-width:80px" />
      </div>
      <div class="form-actions">
        <button class="btn-sm btn-save" onclick="saveKpi('${k.id}')">保存</button>
        <button class="btn-sm btn-cancel" onclick="hideEditKpi('${k.id}')">キャンセル</button>
      </div>
    </div>
  </div>`;
}

// ── Toggle ──
function toggleProject(id){
  const body=document.getElementById('body-'+id);
  const chev=document.getElementById('chev-'+id);
  body.classList.toggle('open');
  chev.classList.toggle('open');
}
function toggleAddProject(){document.getElementById('add-project-form').classList.toggle('show')}
function showAddTask(pid){document.getElementById('add-task-'+pid).classList.add('show')}
function hideAddTask(pid){document.getElementById('add-task-'+pid).classList.remove('show')}
function showAddKpi(pid){document.getElementById('add-kpi-'+pid).classList.add('show')}
function hideAddKpi(pid){document.getElementById('add-kpi-'+pid).classList.remove('show')}
function showEditTask(id){document.getElementById('edit-task-'+id).classList.add('show')}
function hideEditTask(id){document.getElementById('edit-task-'+id).classList.remove('show')}
function showEditKpi(id){document.getElementById('edit-kpi-'+id).classList.add('show')}
function hideEditKpi(id){document.getElementById('edit-kpi-'+id).classList.remove('show')}
function showEditProject(id){document.getElementById('edit-proj-'+id).classList.add('show')}
function hideEditProject(id){document.getElementById('edit-proj-'+id).classList.remove('show')}

// ── CRUD ──
async function addProject(){
  const name=document.getElementById('np-name').value.trim();
  const desc=document.getElementById('np-desc').value.trim();
  const color=document.getElementById('np-color').value;
  if(!name){alert('プロジェクト名を入力してください');return;}
  await api('POST','/api/projects',{name,description:desc,color});
  document.getElementById('np-name').value='';
  document.getElementById('np-desc').value='';
  toggleAddProject();
  loadAll();
}
async function saveProject(id){
  const name=document.getElementById('ep-name-'+id).value.trim();
  const desc=document.getElementById('ep-desc-'+id).value.trim();
  const color=document.getElementById('ep-color-'+id).value;
  if(!name){alert('プロジェクト名を入力してください');return;}
  await api('PUT','/api/projects/'+id,{name,description:desc,color});
  loadAll();
}
async function delProject(id){
  if(!confirm('プロジェクトと関連タスク・KPIを全て削除しますか？'))return;
  await api('DELETE','/api/projects/'+id);
  loadAll();
}
async function addTask(pid){
  const title=document.getElementById('nt-title-'+pid).value.trim();
  const assignee=document.getElementById('nt-assignee-'+pid).value.trim();
  const priority=document.getElementById('nt-priority-'+pid).value;
  const due_date=document.getElementById('nt-due-'+pid).value;
  if(!title){alert('タスク名を入力してください');return;}
  await api('POST','/api/tasks',{title,assignee,priority,due_date,project_id:pid});
  document.getElementById('nt-title-'+pid).value='';
  hideAddTask(pid);
  loadAll();
}
async function saveTask(id){
  const title=document.getElementById('et-title-'+id).value.trim();
  const assignee=document.getElementById('et-assignee-'+id).value.trim();
  const priority=document.getElementById('et-priority-'+id).value;
  const due_date=document.getElementById('et-due-'+id).value;
  await api('PUT','/api/tasks/'+id,{title,assignee,priority,due_date});
  loadAll();
}
async function updateTaskStatus(id,status){await api('PUT','/api/tasks/'+id,{status});loadAll()}
async function updateTaskProgress(id,progress){await api('PUT','/api/tasks/'+id,{progress:parseInt(progress)});loadAll()}
async function delTask(id){if(!confirm('削除しますか？'))return;await api('DELETE','/api/tasks/'+id);loadAll()}
async function addKpi(pid){
  const name=document.getElementById('nk-name-'+pid).value.trim();
  const target=document.getElementById('nk-target-'+pid).value;
  const unit=document.getElementById('nk-unit-'+pid).value;
  if(!name||!target){alert('KPI名と目標値を入力してください');return;}
  await api('POST','/api/kpis',{name,target,unit,project_id:pid});
  document.getElementById('nk-name-'+pid).value='';
  document.getElementById('nk-target-'+pid).value='';
  hideAddKpi(pid);
  loadAll();
}
async function saveKpi(id){
  const name=document.getElementById('ek-name-'+id).value.trim();
  const current=document.getElementById('ek-current-'+id).value;
  const target=document.getElementById('ek-target-'+id).value;
  const unit=document.getElementById('ek-unit-'+id).value;
  await api('PUT','/api/kpis/'+id,{name,current,target,unit});
  loadAll();
}
async function delKpi(id){if(!confirm('削除しますか？'))return;await api('DELETE','/api/kpis/'+id);loadAll()}

function statusLabel(s){return{todo:'未着手',doing:'進行中',done:'完了'}[s]||s}
function priorityLabel(p){return{high:'高',medium:'中',low:'低'}[p]||p}

loadAll();
</script>
</body>
</html>"""

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
