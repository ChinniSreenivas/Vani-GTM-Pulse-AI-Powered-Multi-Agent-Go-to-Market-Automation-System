import sqlite3, json
from pathlib import Path
DB = Path(__file__).resolve().parent.parent / 'gtm_pulse.db'

def connect():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init_db():
    with connect() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, industry TEXT, location TEXT, target_role TEXT, score INTEGER, status TEXT, pain_points TEXT, signals TEXT, outreach_subject TEXT, outreach_body TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, status TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

def save_result(p, result):
    profile, out = result['customer_profiling'], result['outbound']
    manager = result.get('manager', {})
    checks = manager.get('validation_checks', {})
    # A high heuristic score alone is not qualification: require a relevant
    # public-source candidate and route it for human review.
    source_ready = bool(checks.get('public_source_candidate_available'))
    status = (
        'Qualified for Review'
        if profile['lead_score'] >= 70 and source_ready
        else 'Needs Research'
    )
    with connect() as c:
        cur = c.execute(
            'INSERT INTO leads(company,industry,location,target_role,score,status,pain_points,signals,outreach_subject,outreach_body) VALUES(?,?,?,?,?,?,?,?,?,?)',
            (p.company,p.industry,p.location,p.target_role,profile['lead_score'],status,
             json.dumps(p.pain_points),json.dumps(p.signals),out['subject'],out['body'])
        )
        lead_id = cur.lastrowid
        c.execute('INSERT INTO runs(company,status) VALUES(?,?)',(p.company,manager.get('decision', 'needs_review')))
    return lead_id

def get_leads():
    with connect() as c: rows = c.execute('SELECT * FROM leads ORDER BY id DESC').fetchall()
    out=[]
    for row in rows:
        d=dict(row); d['pain_points']=json.loads(d['pain_points'] or '[]'); d['signals']=json.loads(d['signals'] or '[]'); out.append(d)
    return out

def get_runs():
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 100').fetchall()]

def get_analytics():
    with connect() as c:
        total=c.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        qualified=c.execute("SELECT COUNT(*) FROM leads WHERE score>=70 AND status IN ('Qualified','Qualified for Review')").fetchone()[0]
        avg=c.execute('SELECT COALESCE(AVG(score),0) FROM leads').fetchone()[0]
        runs=c.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
    return {'total_leads':total,'qualified_leads':qualified,'average_score':round(avg,1),'pipeline_runs':runs}
