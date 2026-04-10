from flask import Flask, request, jsonify
import os, uuid
from datetime import datetime, date

app = Flask(__name__)

import psycopg2
from psycopg2.extras import RealDictCursor

def get_conn():
    return psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS menus (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sets INTEGER DEFAULT 3,
                    reps INTEGER DEFAULT 10,
                    weight TEXT DEFAULT '',
                    day_of_week TEXT DEFAULT '[]',
                    goal_weeks INTEGER DEFAULT 4,
                    completed_count INTEGER DEFAULT 0,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    menu_id TEXT,
                    log_date TEXT,
                    completed BOOLEAN DEFAULT TRUE,
                    created_at TEXT
                );
            """)
        conn.commit()

init_db()

PRAISE_MESSAGES = [
    ("🎉", "素晴らしい！今日も完璧にこなしましたね！"),
    ("💪", "最高です！その調子で続けましょう！"),
    ("🔥", "やりましたね！あなたは本当に強い！"),
    ("⭐", "完璧な一日！自分を誇りに思ってください！"),
    ("🏆", "チャンピオン！今日も目標達成！"),
]

REWARDS = [
    {"count": 5,  "emoji": "🌟", "title": "5回達成！",   "reward": "好きなスムージーを飲もう！"},
    {"count": 10, "emoji": "🎁", "title": "10回達成！",  "reward": "新しいトレーニングウェアを買おう！"},
    {"count": 20, "emoji": "🏅", "title": "20回達成！",  "reward": "マッサージや温泉で体を癒そう！"},
    {"count": 30, "emoji": "🥇", "title": "30回達成！",  "reward": "憧れのスポーツギアをゲット！"},
    {"count": 50, "emoji": "👑", "title": "50回達成！",  "reward": "特別なディナーでお祝いしよう！"},
    {"count": 100,"emoji": "🚀", "title": "100回達成！", "reward": "旅行に行って自分にご褒美！"},
]

def menu_to_dict(row):
    d = dict(row)
    import json
    if isinstance(d.get('day_of_week'), str):
        try:
            d['day_of_week'] = json.loads(d['day_of_week'])
        except:
            d['day_of_week'] = []
    return d

@app.route('/')
def index():
    return HTML

@app.route('/api/menus', methods=['GET'])
def get_menus():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM menus ORDER BY created_at")
            return jsonify([menu_to_dict(r) for r in cur.fetchall()])

@app.route('/api/menus', methods=['POST'])
def add_menu():
    import json
    b = request.get_json()
    m = {
        'id': str(uuid.uuid4()),
        'name': b.get('name','').strip(),
        'sets': int(b.get('sets',3)),
        'reps': int(b.get('reps',10)),
        'weight': b.get('weight',''),
        'day_of_week': json.dumps(b.get('day_of_week',[])),
        'goal_weeks': int(b.get('goal_weeks',4)),
        'completed_count': 0,
        'created_at': datetime.now().isoformat()
    }
    if not m['name']: return jsonify({'error': '名前は必須'}), 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO menus VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (m['id'],m['name'],m['sets'],m['reps'],m['weight'],m['day_of_week'],m['goal_weeks'],m['completed_count'],m['created_at']))
        conn.commit()
    m['day_of_week'] = b.get('day_of_week',[])
    return jsonify(m), 201

@app.route('/api/menus/<mid>', methods=['PUT'])
def update_menu(mid):
    import json
    b = request.get_json()
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""UPDATE menus SET name=%s, sets=%s, reps=%s, weight=%s,
                day_of_week=%s, goal_weeks=%s WHERE id=%s RETURNING *""",
                (b.get('name'), int(b.get('sets',3)), int(b.get('reps',10)),
                 b.get('weight',''), json.dumps(b.get('day_of_week',[])),
                 int(b.get('goal_weeks',4)), mid))
            row = cur.fetchone()
        conn.commit()
    return jsonify(menu_to_dict(row)) if row else (jsonify({'error': 'not found'}), 404)

@app.route('/api/menus/<mid>', methods=['DELETE'])
def del_menu(mid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM menus WHERE id=%s", (mid,))
        conn.commit()
    return jsonify({'ok': True})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    date_str = request.args.get('date', str(date.today()))
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM logs WHERE log_date=%s", (date_str,))
            return jsonify([dict(r) for r in cur.fetchall()])

@app.route('/api/logs/all', methods=['GET'])
def get_all_logs():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM logs ORDER BY log_date DESC")
            return jsonify([dict(r) for r in cur.fetchall()])

@app.route('/api/logs', methods=['POST'])
def add_log():
    b = request.get_json()
    menu_id = b.get('menu_id')
    date_str = b.get('date', str(date.today()))
    completed = b.get('completed', True)

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM logs WHERE menu_id=%s AND log_date=%s", (menu_id, date_str))
            existing = cur.fetchone()
            if existing:
                cur.execute("UPDATE logs SET completed=%s WHERE id=%s RETURNING *", (completed, existing['id']))
                log = dict(cur.fetchone())
            else:
                log_id = str(uuid.uuid4())
                cur.execute("INSERT INTO logs VALUES (%s,%s,%s,%s,%s) RETURNING *",
                    (log_id, menu_id, date_str, completed, datetime.now().isoformat()))
                log = dict(cur.fetchone())

            # completed_countを更新
            cur.execute("SELECT COUNT(*) FROM logs WHERE menu_id=%s AND completed=TRUE", (menu_id,))
            count = cur.fetchone()['count']
            cur.execute("UPDATE menus SET completed_count=%s WHERE id=%s RETURNING *", (count, menu_id))
            menu = cur.fetchone()
        conn.commit()

    praise = None
    reward = None
    if completed and menu:
        idx = count % len(PRAISE_MESSAGES)
        praise = PRAISE_MESSAGES[idx][0] + " " + PRAISE_MESSAGES[idx][1]
        for r in REWARDS:
            if count == r['count']:
                reward = r
                break

    return jsonify({'log': log, 'praise': praise, 'reward': reward}), 201

@app.route('/api/summary', methods=['GET'])
def summary():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM menus")
            total_menus = cur.fetchone()[0]
            today = str(date.today())
            cur.execute("SELECT COUNT(*) FROM logs WHERE log_date=%s AND completed=TRUE", (today,))
            today_completed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM logs WHERE completed=TRUE")
            total_logs = cur.fetchone()[0]
    return jsonify({'total_menus': total_menus, 'today_completed': today_completed, 'total_logs': total_logs})

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>トレーニング管理</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Helvetica Neue',Arial,sans-serif;background:#f0f4f8;color:#333}
header{background:linear-gradient(135deg,#1b5e20,#43a047);color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px}
header h1{font-size:20px}
nav{display:flex;background:#fff;border-bottom:2px solid #e0e0e0;overflow-x:auto}
nav button{flex:1;min-width:70px;padding:12px 6px;border:none;background:none;font-size:13px;cursor:pointer;color:#666;border-bottom:3px solid transparent}
nav button.active{color:#43a047;border-bottom-color:#43a047;font-weight:bold}
.page{display:none;padding:16px;max-width:600px;margin:0 auto}
.page.active{display:block}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
h3{font-size:16px;margin-bottom:12px;color:#333}
.form-row{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.form-row input,.form-row select{flex:1;min-width:90px;padding:10px;border:1px solid #ddd;border-radius:8px;font-size:14px}
.form-row label{font-size:12px;color:#888;width:100%;margin-bottom:2px}
.btn{padding:10px 16px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:bold}
.btn-primary{background:#43a047;color:#fff}
.btn-edit{background:#1976d2;color:#fff;padding:6px 10px;font-size:12px}
.btn-danger{background:#ef5350;color:#fff;padding:6px 10px;font-size:12px}
.btn-save{background:#43a047;color:#fff;padding:6px 10px;font-size:12px}
.btn-cancel{background:#aaa;color:#fff;padding:6px 10px;font-size:12px}
.menu-item{background:#f9f9f9;border-radius:10px;padding:14px;margin-bottom:10px;border-left:4px solid #43a047}
.menu-name{font-weight:bold;font-size:15px;margin-bottom:4px}
.menu-detail{font-size:13px;color:#666;margin-bottom:8px}
.menu-footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px}
.check-btn{padding:8px 14px;border:none;border-radius:20px;cursor:pointer;font-size:13px;font-weight:bold}
.check-btn.done{background:#43a047;color:#fff}
.check-btn.todo{background:#e8f5e9;color:#43a047;border:2px solid #43a047}
.progress-bar{height:8px;background:#e0e0e0;border-radius:4px;overflow:hidden;margin:6px 0}
.progress-fill{height:100%;background:linear-gradient(90deg,#43a047,#76c442);border-radius:4px;transition:.3s}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.stat-card{background:#fff;border-radius:12px;padding:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.stat-num{font-size:26px;font-weight:bold;color:#43a047}
.stat-label{font-size:11px;color:#999;margin-top:2px}
.praise-box{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border:2px solid #43a047;border-radius:12px;padding:14px;margin-bottom:12px;text-align:center;font-size:15px;font-weight:bold;display:none}
.reward-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:100;align-items:center;justify-content:center}
.reward-overlay.show{display:flex}
.reward-box{background:#fff;border-radius:20px;padding:32px 24px;text-align:center;max-width:320px;width:90%;animation:pop .4s ease}
@keyframes pop{from{transform:scale(.5);opacity:0}to{transform:scale(1);opacity:1}}
.reward-emoji{font-size:64px;margin-bottom:12px}
.reward-title{font-size:22px;font-weight:bold;color:#1b5e20;margin-bottom:8px}
.reward-text{font-size:16px;color:#555;margin-bottom:20px}
.reward-close{background:#43a047;color:#fff;border:none;border-radius:20px;padding:12px 32px;font-size:16px;font-weight:bold;cursor:pointer}
.day-check{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}
.day-badge{padding:5px 10px;border-radius:12px;font-size:12px;background:#e8f5e9;color:#43a047;cursor:pointer;border:1px solid #c8e6c9;user-select:none}
.day-badge.selected{background:#43a047;color:#fff}
.count-badge{background:#43a047;color:#fff;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:4px}
.edit-form{display:none;background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px;margin-top:10px}
.edit-form.show{display:block}
.log-item{display:flex;justify-content:space-between;align-items:center;padding:10px;border-radius:8px;background:#f9f9f9;margin-bottom:6px;font-size:14px}
.badge-done{background:#e8f5e9;color:#43a047;padding:3px 8px;border-radius:10px;font-size:11px}
.empty{text-align:center;color:#bbb;padding:20px;font-size:14px}
.reward-list-item{display:flex;align-items:center;gap:10px;padding:10px;border-radius:8px;background:#fff9c4;border:1px solid #f9a825;margin-bottom:8px}
</style>
</head>
<body>

<div id="reward-overlay" class="reward-overlay" onclick="closeReward()">
  <div class="reward-box" onclick="event.stopPropagation()">
    <div id="reward-emoji" class="reward-emoji">🏆</div>
    <div id="reward-title" class="reward-title">達成！</div>
    <div id="reward-text" class="reward-text"></div>
    <button class="reward-close" onclick="closeReward()">やった！閉じる</button>
  </div>
</div>

<header>
  <span style="font-size:24px">💪</span>
  <h1>トレーニング管理</h1>
</header>
<nav>
  <button class="active" onclick="showPage('today',this)">📅 今日</button>
  <button onclick="showPage('menus',this)">🏋️ メニュー</button>
  <button onclick="showPage('history',this)">📊 履歴</button>
  <button onclick="showPage('rewards',this)">🎁 ご褒美</button>
</nav>

<div id="today" class="page active">
  <div id="praise-box" class="praise-box"></div>
  <div class="stats">
    <div class="stat-card"><div class="stat-num" id="stat-total">0</div><div class="stat-label">メニュー数</div></div>
    <div class="stat-card"><div class="stat-num" id="stat-today">0</div><div class="stat-label">今日完了</div></div>
    <div class="stat-card"><div class="stat-num" id="stat-all">0</div><div class="stat-label">累計完了</div></div>
  </div>
  <div class="card">
    <h3>📅 今日のトレーニング <span id="today-date" style="font-size:12px;color:#999"></span></h3>
    <div id="today-list"></div>
  </div>
</div>

<div id="menus" class="page">
  <div class="card">
    <h3>➕ メニュー追加</h3>
    <div class="form-row">
      <input id="m-name" placeholder="メニュー名（例: ベンチプレス）" style="width:100%" />
    </div>
    <div class="form-row">
      <div style="flex:1"><label>セット数</label><input id="m-sets" type="number" value="3" min="1" /></div>
      <div style="flex:1"><label>レップ数</label><input id="m-reps" type="number" value="10" min="1" /></div>
      <div style="flex:1"><label>重量/強度</label><input id="m-weight" placeholder="例: 60kg" /></div>
    </div>
    <div style="margin-bottom:10px">
      <label style="font-size:12px;color:#888">実施曜日</label>
      <div class="day-check" id="day-selector">
        <span class="day-badge" data-day="月" onclick="toggleDay(this)">月</span>
        <span class="day-badge" data-day="火" onclick="toggleDay(this)">火</span>
        <span class="day-badge" data-day="水" onclick="toggleDay(this)">水</span>
        <span class="day-badge" data-day="木" onclick="toggleDay(this)">木</span>
        <span class="day-badge" data-day="金" onclick="toggleDay(this)">金</span>
        <span class="day-badge" data-day="土" onclick="toggleDay(this)">土</span>
        <span class="day-badge" data-day="日" onclick="toggleDay(this)">日</span>
      </div>
    </div>
    <div class="form-row">
      <div style="flex:1"><label>目標期間（週）</label><input id="m-weeks" type="number" value="4" min="1" /></div>
    </div>
    <button class="btn btn-primary" style="width:100%;margin-top:4px" onclick="addMenu()">追加</button>
  </div>
  <div id="menus-list"></div>
</div>

<div id="history" class="page">
  <div class="card">
    <h3>📊 トレーニング履歴</h3>
    <div id="history-list"></div>
  </div>
</div>

<div id="rewards" class="page">
  <div class="card">
    <h3>🎁 ご褒美マイルストーン</h3>
    <div id="rewards-list"></div>
  </div>
</div>

<script>
const DAYS=['日','月','火','水','木','金','土'];
const REWARD_MILESTONES=[
  {count:5,emoji:'🌟',title:'5回達成！',reward:'好きなスムージーを飲もう！'},
  {count:10,emoji:'🎁',title:'10回達成！',reward:'新しいトレーニングウェアを買おう！'},
  {count:20,emoji:'🏅',title:'20回達成！',reward:'マッサージや温泉で体を癒そう！'},
  {count:30,emoji:'🥇',title:'30回達成！',reward:'憧れのスポーツギアをゲット！'},
  {count:50,emoji:'👑',title:'50回達成！',reward:'特別なディナーでお祝いしよう！'},
  {count:100,emoji:'🚀',title:'100回達成！',reward:'旅行に行って自分にご褒美！'},
];
let menus=[],logs=[],allLogs=[];
const todayStr=new Date().toISOString().slice(0,10);
document.getElementById('today-date').textContent=new Date().toLocaleDateString('ja-JP',{month:'long',day:'numeric',weekday:'long'});

function showPage(id,btn){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if(btn) btn.classList.add('active');
  if(id==='history') renderHistory();
  if(id==='rewards') renderRewards();
}

function toggleDay(el){el.classList.toggle('selected')}

async function api(method,path,body){
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(body) opts.body=JSON.stringify(body);
  const r=await fetch(path,opts);
  return r.json();
}

async function loadAll(){
  [menus,logs,allLogs]=await Promise.all([
    api('GET','/api/menus'),
    api('GET','/api/logs?date='+todayStr),
    api('GET','/api/logs/all')
  ]);
  const summary=await api('GET','/api/summary');
  document.getElementById('stat-total').textContent=summary.total_menus;
  document.getElementById('stat-today').textContent=summary.today_completed;
  document.getElementById('stat-all').textContent=summary.total_logs;
  renderToday();
  renderMenus();
}

function renderToday(){
  const el=document.getElementById('today-list');
  const todayDay=DAYS[new Date().getDay()];
  const todayMenus=menus.filter(m=>!m.day_of_week.length||m.day_of_week.includes(todayDay));
  if(!todayMenus.length){el.innerHTML='<div class="empty">今日のメニューなし<br><small>メニュータブから追加してください</small></div>';return;}
  el.innerHTML=todayMenus.map(m=>{
    const log=logs.find(l=>l.menu_id===m.id);
    const done=log&&log.completed;
    const target=m.goal_weeks*(m.day_of_week.length||3);
    const pct=Math.min(100,Math.round(m.completed_count/target*100));
    const nextReward=REWARD_MILESTONES.find(r=>r.count>m.completed_count);
    return`<div class="menu-item">
      <div class="menu-name">${m.name} <span class="count-badge">${m.completed_count}回</span></div>
      <div class="menu-detail">${m.sets}セット × ${m.reps}レップ ${m.weight?'/ '+m.weight:''}</div>
      ${nextReward?`<div style="font-size:11px;color:#f57c00;margin-bottom:4px">🎯 次のご褒美まであと${nextReward.count-m.completed_count}回: ${nextReward.reward}</div>`:''}
      <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
      <div style="font-size:11px;color:#999;margin-bottom:8px">目標進捗: ${pct}% (${m.completed_count}/${target}回)</div>
      <div class="menu-footer">
        <button class="check-btn ${done?'done':'todo'}" onclick="toggleLog('${m.id}',${done})">
          ${done?'✅ 完了！':'⬜ 未完了'}
        </button>
      </div>
    </div>`;
  }).join('');
}

function renderMenus(){
  const el=document.getElementById('menus-list');
  if(!menus.length){el.innerHTML='<div class="empty">メニューなし</div>';return;}
  el.innerHTML=menus.map(m=>`
    <div class="menu-item" id="menu-item-${m.id}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div class="menu-name">${m.name} <span class="count-badge">${m.completed_count}回</span></div>
          <div class="menu-detail">${m.sets}セット × ${m.reps}レップ ${m.weight?'/ '+m.weight:''}</div>
          <div class="menu-detail">曜日: ${m.day_of_week.length?m.day_of_week.join('・'):'毎日'} / 目標${m.goal_weeks}週</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-edit" onclick="showEdit('${m.id}')">編集</button>
          <button class="btn btn-danger" onclick="delMenu('${m.id}')">削除</button>
        </div>
      </div>
      <div class="edit-form" id="edit-${m.id}">
        <div class="form-row">
          <input id="edit-name-${m.id}" value="${m.name}" placeholder="メニュー名" style="width:100%" />
        </div>
        <div class="form-row">
          <div style="flex:1"><label>セット数</label><input id="edit-sets-${m.id}" type="number" value="${m.sets}" /></div>
          <div style="flex:1"><label>レップ数</label><input id="edit-reps-${m.id}" type="number" value="${m.reps}" /></div>
          <div style="flex:1"><label>重量/強度</label><input id="edit-weight-${m.id}" value="${m.weight||''}" /></div>
        </div>
        <div style="margin-bottom:10px">
          <label style="font-size:12px;color:#888">実施曜日</label>
          <div class="day-check" id="edit-days-${m.id}">
            ${['月','火','水','木','金','土','日'].map(d=>`<span class="day-badge ${m.day_of_week.includes(d)?'selected':''}" data-day="${d}" onclick="this.classList.toggle('selected')">${d}</span>`).join('')}
          </div>
        </div>
        <div class="form-row">
          <div style="flex:1"><label>目標期間（週）</label><input id="edit-weeks-${m.id}" type="number" value="${m.goal_weeks}" /></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn btn-save" onclick="saveEdit('${m.id}')">保存</button>
          <button class="btn btn-cancel" onclick="hideEdit('${m.id}')">キャンセル</button>
        </div>
      </div>
    </div>`).join('');
}

function renderHistory(){
  const el=document.getElementById('history-list');
  if(!allLogs.length){el.innerHTML='<div class="empty">履歴なし</div>';return;}
  const sorted=[...allLogs].sort((a,b)=>b.log_date.localeCompare(a.log_date));
  const byDate={};
  sorted.forEach(l=>{if(!byDate[l.log_date]) byDate[l.log_date]=[];byDate[l.log_date].push(l);});
  el.innerHTML=Object.entries(byDate).slice(0,14).map(([d,logs])=>`
    <div style="margin-bottom:12px">
      <div style="font-weight:bold;color:#555;margin-bottom:6px;font-size:14px">📅 ${d}</div>
      ${logs.map(l=>{
        const m=menus.find(m=>m.id===l.menu_id);
        return`<div class="log-item">
          <span>${m?m.name:'削除済みメニュー'}</span>
          <span class="${l.completed?'badge-done':'badge-skip'}">${l.completed?'✅ 完了':'スキップ'}</span>
        </div>`;
      }).join('')}
    </div>`).join('');
}

function renderRewards(){
  const el=document.getElementById('rewards-list');
  const totalCompleted=allLogs.filter(l=>l.completed).length;
  el.innerHTML=REWARD_MILESTONES.map(r=>{
    const achieved=totalCompleted>=r.count;
    return`<div class="reward-list-item" style="${achieved?'':'opacity:0.5'}">
      <span style="font-size:28px">${r.emoji}</span>
      <div>
        <div style="font-weight:bold;font-size:14px">${r.title} ${achieved?'✅':''}</div>
        <div style="font-size:13px;color:#666">${r.reward}</div>
        ${!achieved?`<div style="font-size:11px;color:#999">あと${r.count-totalCompleted}回で達成！</div>`:''}
      </div>
    </div>`;
  }).join('');
}

function showReward(reward){
  document.getElementById('reward-emoji').textContent=reward.emoji;
  document.getElementById('reward-title').textContent=reward.title;
  document.getElementById('reward-text').textContent=reward.reward;
  document.getElementById('reward-overlay').classList.add('show');
}
function closeReward(){document.getElementById('reward-overlay').classList.remove('show')}

async function toggleLog(menuId,isDone){
  const result=await api('POST','/api/logs',{menu_id:menuId,completed:!isDone});
  if(result.praise&&!isDone){
    const box=document.getElementById('praise-box');
    box.textContent=result.praise;
    box.style.display='block';
    setTimeout(()=>box.style.display='none',4000);
  }
  if(result.reward&&!isDone) setTimeout(()=>showReward(result.reward),500);
  loadAll();
}

async function addMenu(){
  const name=document.getElementById('m-name').value.trim();
  const sets=document.getElementById('m-sets').value;
  const reps=document.getElementById('m-reps').value;
  const weight=document.getElementById('m-weight').value;
  const weeks=document.getElementById('m-weeks').value;
  const days=[...document.querySelectorAll('#day-selector .day-badge.selected')].map(el=>el.dataset.day);
  if(!name){alert('メニュー名を入力してください');return;}
  await api('POST','/api/menus',{name,sets,reps,weight,goal_weeks:weeks,day_of_week:days});
  document.getElementById('m-name').value='';
  document.getElementById('m-weight').value='';
  document.querySelectorAll('#day-selector .day-badge').forEach(el=>el.classList.remove('selected'));
  loadAll();
}

function showEdit(id){document.getElementById('edit-'+id).classList.add('show')}
function hideEdit(id){document.getElementById('edit-'+id).classList.remove('show')}

async function saveEdit(id){
  const name=document.getElementById('edit-name-'+id).value.trim();
  const sets=document.getElementById('edit-sets-'+id).value;
  const reps=document.getElementById('edit-reps-'+id).value;
  const weight=document.getElementById('edit-weight-'+id).value;
  const weeks=document.getElementById('edit-weeks-'+id).value;
  const days=[...document.querySelectorAll('#edit-days-'+id+' .day-badge.selected')].map(el=>el.dataset.day);
  if(!name){alert('メニュー名を入力してください');return;}
  await api('PUT','/api/menus/'+id,{name,sets,reps,weight,goal_weeks:weeks,day_of_week:days});
  loadAll();
}

async function delMenu(id){
  if(!confirm('削除しますか？'))return;
  await api('DELETE','/api/menus/'+id);
  loadAll();
}

loadAll();
</script>
</body>
</html>"""

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
