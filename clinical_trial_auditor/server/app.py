# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - FastAPI Server
# Implements OpenEnv HTTP API + Professional Dashboard UI

import os
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .environment import ClinicalTrialAuditorEnvironment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Clinical Trial Protocol Auditor",
    description="OpenEnv environment for AI-powered clinical trial protocol auditing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = ClinicalTrialAuditorEnvironment()


# ── Request/Response Models ───────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = Field(default="section_completeness")
    seed: Optional[int] = Field(default=None)

class StepRequest(BaseModel):
    action_type: str = Field(...)
    section: Optional[str] = Field(None)
    issue_type: Optional[str] = Field(None)
    severity: Optional[str] = Field(None)
    description: str = Field(...)
    recommendation: Optional[str] = Field(None)

class ObservationResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float = 0.0
    done: bool = False
    info: Dict[str, Any] = Field(default_factory=dict)


# ── Dashboard HTML ────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CTA — Clinical Trial Protocol Auditor</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0e1a;--surface:#111827;--surface2:#1a2236;--surface3:#232d45;
  --border:#2a3550;--text:#e2e8f0;--text2:#94a3b8;--text3:#64748b;
  --accent:#06b6d4;--accent2:#0891b2;--green:#10b981;--red:#ef4444;
  --orange:#f59e0b;--purple:#8b5cf6;--pink:#ec4899;
  --mono:'JetBrains Mono',monospace;--sans:'DM Sans',sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--sans);overflow-x:hidden;min-height:100vh}

/* ── Header ── */
.header{background:linear-gradient(135deg,#0d1525 0%,#1a1040 50%,#0d1525 100%);
  border-bottom:1px solid var(--border);padding:14px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}
.header-left{display:flex;align-items:center;gap:14px}
.logo{width:38px;height:38px;background:linear-gradient(135deg,var(--accent),var(--purple));border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;letter-spacing:-0.5px}
.brand h1{font-size:18px;font-weight:700;letter-spacing:-0.3px;background:linear-gradient(135deg,#fff 0%,var(--accent) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand span{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:2px;font-weight:500}
.header-badges{display:flex;gap:8px;align-items:center}
.badge{padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600;font-family:var(--mono);letter-spacing:0.5px}
.badge-openenv{background:rgba(6,182,212,0.15);color:var(--accent);border:1px solid rgba(6,182,212,0.3)}
.badge-live{background:rgba(16,185,129,0.15);color:var(--green);border:1px solid rgba(16,185,129,0.3)}
.header-stats{display:flex;gap:20px;font-family:var(--mono);font-size:12px;color:var(--text2)}
.header-stats strong{color:var(--text);font-weight:700}

/* ── Grid ── */
.grid{display:grid;grid-template-columns:280px 1fr 300px;gap:0;height:calc(100vh - 60px)}

/* ── Left Panel ── */
.panel-left{background:var(--surface);border-right:1px solid var(--border);overflow-y:auto;padding:0}
.panel-section{padding:18px;border-bottom:1px solid var(--border)}
.panel-label{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text3);font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.panel-label::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--green);display:inline-block}
.protocol-id{font-family:var(--mono);font-size:15px;color:var(--accent);font-weight:600}
.protocol-excerpt{font-size:12.5px;line-height:1.7;color:var(--text2);font-family:var(--mono);background:var(--surface2);padding:12px;border-radius:8px;margin-top:10px;max-height:300px;overflow-y:auto;white-space:pre-wrap;border:1px solid var(--border)}
.task-cards{display:flex;flex-direction:column;gap:6px}
.task-card{padding:10px 12px;border-radius:8px;cursor:pointer;border:1px solid var(--border);transition:all 0.2s;background:var(--surface2)}
.task-card:hover,.task-card.active{border-color:var(--accent);background:rgba(6,182,212,0.08)}
.task-card .task-name{font-size:12px;font-weight:600;color:var(--text)}
.task-card .task-meta{font-size:10px;color:var(--text3);margin-top:2px;font-family:var(--mono)}
.diff-easy{border-left:3px solid var(--green)}
.diff-medium{border-left:3px solid var(--orange)}
.diff-hard{border-left:3px solid var(--red)}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;font-size:12px}
.stat-row .label{color:var(--text3)}
.stat-row .value{font-family:var(--mono);color:var(--text);font-weight:600}

/* ── Center Panel ── */
.panel-center{overflow-y:auto;background:var(--bg);padding:20px}
.center-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.center-title{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text3);font-weight:600;display:flex;align-items:center;gap:6px}
.center-title::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent);display:inline-block}
.btn{padding:8px 18px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all 0.2s;font-family:var(--sans)}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--purple));color:#fff}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(6,182,212,0.3)}
.btn-secondary{background:var(--surface2);color:var(--text);border:1px solid var(--border)}
.btn-danger{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid rgba(239,68,68,0.3)}
.btn:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.controls{display:flex;gap:8px}

/* ── Step Log ── */
.step-log{display:flex;flex-direction:column;gap:8px}
.step-entry{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;animation:fadeIn 0.3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.step-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.step-num{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--accent);background:rgba(6,182,212,0.1);padding:2px 8px;border-radius:4px}
.step-reward{font-family:var(--mono);font-size:13px;font-weight:700}
.step-reward.positive{color:var(--green)}
.step-reward.negative{color:var(--red)}
.step-reward.zero{color:var(--text3)}
.step-action{font-size:11px;color:var(--text3);font-family:var(--mono)}
.step-action strong{color:var(--text)}
.step-desc{font-size:12px;color:var(--text2);margin-top:6px;line-height:1.5}
.step-done{background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(6,182,212,0.08));border-color:var(--green)}
.empty-state{text-align:center;padding:60px 20px;color:var(--text3)}
.empty-state .icon{font-size:48px;margin-bottom:12px;opacity:0.3}
.empty-state p{font-size:13px;line-height:1.6}

/* ── Right Panel ── */
.panel-right{background:var(--surface);border-left:1px solid var(--border);overflow-y:auto;padding:0}
.metric-big{text-align:center;padding:24px 18px;border-bottom:1px solid var(--border)}
.metric-big .score{font-family:var(--mono);font-size:48px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.metric-big .score-label{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text3);margin-top:4px}
.metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:0}
.metric-cell{padding:16px;border-bottom:1px solid var(--border);border-right:1px solid var(--border);text-align:center}
.metric-cell:nth-child(2n){border-right:none}
.metric-cell .val{font-family:var(--mono);font-size:20px;font-weight:700;color:var(--text)}
.metric-cell .lbl{font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text3);margin-top:4px}
.capability-section{padding:18px}
.capability-title{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text3);font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.capability-title::before{content:'⚡';font-size:12px}
.cap-bar{margin-bottom:10px}
.cap-bar-header{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px}
.cap-bar-header .name{color:var(--text2)}
.cap-bar-header .score-val{font-family:var(--mono);font-weight:700}
.cap-bar-track{height:6px;background:var(--surface2);border-radius:3px;overflow:hidden}
.cap-bar-fill{height:100%;border-radius:3px;transition:width 0.8s cubic-bezier(0.4,0,0.2,1)}
.per-task{padding:18px;border-top:1px solid var(--border)}
.per-task-title{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--text3);font-weight:600;margin-bottom:10px}
.task-score-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;font-size:12px;border-bottom:1px solid rgba(42,53,80,0.5)}
.task-score-row .name{color:var(--text2)}
.task-score-row .scores{font-family:var(--mono);display:flex;gap:12px}
.task-score-row .scores span{min-width:36px;text-align:right}

/* ── Footer ── */
.footer{position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-top:1px solid var(--border);padding:8px 28px;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--text3);z-index:100;font-family:var(--mono)}
.footer .status{display:flex;align-items:center;gap:6px}
.footer .status::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--green)}

/* ── Input Area ── */
.input-area{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin-top:12px}
.input-row{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.input-row select,.input-row input{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:6px;font-size:12px;font-family:var(--mono)}
.input-row select{cursor:pointer}
.input-row input{flex:1;min-width:160px}
.input-row textarea{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:8px 10px;border-radius:6px;font-size:12px;font-family:var(--mono);width:100%;min-height:60px;resize:vertical}

@media(max-width:1024px){.grid{grid-template-columns:1fr;height:auto}.panel-left,.panel-right{border:none}}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="logo">CT</div>
    <div class="brand">
      <h1>Clinical Trial Protocol Auditor</h1>
      <span>Agentic Clinical Trial Audit Benchmark</span>
    </div>
  </div>
  <div class="header-badges">
    <span class="badge badge-openenv">OPENENV V1</span>
    <span class="badge badge-live" id="statusBadge">● RUNNING</span>
  </div>
  <div class="header-stats">
    <div><strong>3</strong> Tasks</div>
    <div>EASY → HARD</div>
    <div><strong>22</strong> GROUND TRUTH ISSUES</div>
  </div>
</div>

<div class="grid">
  <!-- Left Panel -->
  <div class="panel-left">
    <div class="panel-section">
      <div class="panel-label">Active Episode Protocol</div>
      <div class="protocol-id" id="protocolId">Awaiting reset()</div>
      <div id="protocolExcerpt" class="protocol-excerpt" style="display:none"></div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Select Task</div>
      <div class="task-cards">
        <div class="task-card diff-easy active" onclick="selectTask('section_completeness',this)">
          <div class="task-name">🟢 Section Completeness</div>
          <div class="task-meta">Easy · 5 issues · 10 steps</div>
        </div>
        <div class="task-card diff-medium" onclick="selectTask('eligibility_validation',this)">
          <div class="task-name">🟡 Eligibility Validation</div>
          <div class="task-meta">Medium · 7 issues · 12 steps</div>
        </div>
        <div class="task-card diff-hard" onclick="selectTask('full_protocol_audit',this)">
          <div class="task-name">🔴 Full Protocol Audit</div>
          <div class="task-meta">Hard · 10 issues · 15 steps</div>
        </div>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Episode State</div>
      <div class="stat-row"><span class="label">Steps</span><span class="value" id="stepCount">0 / —</span></div>
      <div class="stat-row"><span class="label">Findings</span><span class="value" id="findingCount">0</span></div>
      <div class="stat-row"><span class="label">Cumulative Reward</span><span class="value" id="cumReward">0.00</span></div>
      <div class="stat-row"><span class="label">Status</span><span class="value" id="epStatus">Idle</span></div>
    </div>
  </div>

  <!-- Center Panel -->
  <div class="panel-center">
    <div class="center-header">
      <div class="center-title">Live Agent Telemetry</div>
      <div class="controls">
        <button class="btn btn-primary" id="btnStart" onclick="startAudit()">▶ Start Audit</button>
        <button class="btn btn-secondary" id="btnStep" onclick="manualStep()" disabled>⏭ Manual Step</button>
        <button class="btn btn-danger" id="btnSubmit" onclick="submitReport()" disabled>⏹ Submit Report</button>
      </div>
    </div>

    <div id="stepLog" class="step-log">
      <div class="empty-state">
        <div class="icon">🔬</div>
        <p>Select a task and click <strong>Start Audit</strong><br>to watch the reasoning loop in real time.</p>
        <p style="margin-top:12px;font-size:11px">The benchmark evaluates agents on <strong>22 planted issues</strong><br>across 3 procedurally designed clinical trial protocols.</p>
      </div>
    </div>

    <div class="input-area" id="inputArea" style="display:none">
      <div class="input-row">
        <select id="actionType" onchange="toggleInputs()">
          <option value="identify_issue">identify_issue</option>
          <option value="request_section">request_section</option>
          <option value="submit_report">submit_report</option>
        </select>
        <select id="section">
          <option value="">Section...</option>
          <option value="title">title</option>
          <option value="background">background</option>
          <option value="objectives">objectives</option>
          <option value="study_design">study_design</option>
          <option value="eligibility_criteria">eligibility_criteria</option>
          <option value="study_procedures">study_procedures</option>
          <option value="statistical_design">statistical_design</option>
          <option value="safety_monitoring">safety_monitoring</option>
          <option value="endpoints">endpoints</option>
          <option value="ethical_considerations">ethical_considerations</option>
          <option value="data_management">data_management</option>
        </select>
        <select id="issueType">
          <option value="">Issue type...</option>
          <option value="missing_section">missing_section</option>
          <option value="logical_inconsistency">logical_inconsistency</option>
          <option value="statistical_error">statistical_error</option>
          <option value="safety_gap">safety_gap</option>
          <option value="regulatory_violation">regulatory_violation</option>
          <option value="endpoint_issue">endpoint_issue</option>
          <option value="consent_issue">consent_issue</option>
        </select>
        <select id="severity">
          <option value="">Severity...</option>
          <option value="critical">critical</option>
          <option value="major">major</option>
          <option value="minor">minor</option>
        </select>
      </div>
      <div class="input-row">
        <textarea id="description" placeholder="Describe the finding..."></textarea>
      </div>
      <div class="input-row">
        <button class="btn btn-primary" onclick="sendAction()">Send Action</button>
      </div>
    </div>
  </div>

  <!-- Right Panel -->
  <div class="panel-right">
    <div class="metric-big">
      <div class="score" id="bigScore">0.00</div>
      <div class="score-label">Benchmark Score</div>
    </div>
    <div class="metric-grid">
      <div class="metric-cell"><div class="val" id="mPrecision">—</div><div class="lbl">Precision</div></div>
      <div class="metric-cell"><div class="val" id="mRecall">—</div><div class="lbl">Recall</div></div>
      <div class="metric-cell"><div class="val" id="mWorkflow">—</div><div class="lbl">Severity Acc</div></div>
      <div class="metric-cell"><div class="val" id="mEfficiency">—</div><div class="lbl">Efficiency</div></div>
    </div>
    <div class="capability-section">
      <div class="capability-title">LLM Capability Gap (Expected)</div>
      <div class="cap-bar">
        <div class="cap-bar-header"><span class="name">Naive</span><span class="score-val" style="color:var(--red)">0.10</span></div>
        <div class="cap-bar-track"><div class="cap-bar-fill" style="width:10%;background:var(--red)"></div></div>
      </div>
      <div class="cap-bar">
        <div class="cap-bar-header"><span class="name">Heuristic</span><span class="score-val" style="color:var(--orange)">0.45</span></div>
        <div class="cap-bar-track"><div class="cap-bar-fill" style="width:45%;background:var(--orange)"></div></div>
      </div>
      <div class="cap-bar">
        <div class="cap-bar-header"><span class="name">Reasoning</span><span class="score-val" style="color:var(--green)">0.82</span></div>
        <div class="cap-bar-track"><div class="cap-bar-fill" style="width:82%;background:var(--green)"></div></div>
      </div>
    </div>
    <div class="per-task">
      <div class="per-task-title">Per-Task Breakdown</div>
      <div class="task-score-row"><span class="name">Agent</span><span class="scores"><span>Easy</span><span>Med</span><span>Hard</span><span>Avg</span></span></div>
      <div class="task-score-row" id="taskScoreRow"><span class="name">Current</span><span class="scores"><span id="sEasy">—</span><span id="sMed">—</span><span id="sHard">—</span><span id="sAvg">—</span></span></div>
    </div>
  </div>
</div>

<div class="footer">
  <div class="status" id="footerStatus">Environment ready</div>
  <div>OpenEnv Spec v1 · Phase III Oncology · Procedural Generation</div>
  <div id="footerTime"></div>
</div>

<script>
let selectedTask='section_completeness',episodeActive=false,stepNum=0,totalReward=0,taskScores={};

function selectTask(t,el){
  selectedTask=t;
  document.querySelectorAll('.task-card').forEach(c=>c.classList.remove('active'));
  if(el)el.classList.add('active');
}

async function startAudit(){
  try{
    document.getElementById('btnStart').disabled=true;
    document.getElementById('stepLog').innerHTML='';
    const r=await fetch('/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:selectedTask})});
    const d=await r.json();
    const obs=d.observation;
    episodeActive=true;stepNum=0;totalReward=0;
    document.getElementById('protocolId').textContent=obs.protocol_id||selectedTask;
    const excerpt=(obs.protocol_text||'').substring(0,500)+'...';
    document.getElementById('protocolExcerpt').textContent=excerpt;
    document.getElementById('protocolExcerpt').style.display='block';
    document.getElementById('stepCount').textContent=`0 / ${obs.max_steps}`;
    document.getElementById('findingCount').textContent='0';
    document.getElementById('cumReward').textContent='0.00';
    document.getElementById('epStatus').textContent='Running';
    document.getElementById('btnStep').disabled=false;
    document.getElementById('btnSubmit').disabled=false;
    document.getElementById('inputArea').style.display='block';
    document.getElementById('footerStatus').textContent='Episode started — '+selectedTask;
    addStepEntry(0,null,'reset()',0,false,'Protocol loaded. Begin audit.');
  }catch(e){
    document.getElementById('footerStatus').textContent='Error: '+e.message;
  }finally{
    document.getElementById('btnStart').disabled=false;
  }
}

async function sendAction(){
  if(!episodeActive)return;
  const action={
    action_type:document.getElementById('actionType').value,
    section:document.getElementById('section').value||null,
    issue_type:document.getElementById('issueType').value||null,
    severity:document.getElementById('severity').value||null,
    description:document.getElementById('description').value||'Audit finding',
    recommendation:null
  };
  await doStep(action);
}

async function manualStep(){
  await sendAction();
}

async function submitReport(){
  await doStep({action_type:'submit_report',description:'Finalizing audit report'});
}

async function doStep(action){
  try{
    const r=await fetch('/step',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(action)});
    const d=await r.json();
    const obs=d.observation;
    stepNum=obs.step_number;
    const reward=d.reward||0;
    totalReward+=reward;
    document.getElementById('stepCount').textContent=`${stepNum} / ${obs.max_steps}`;
    document.getElementById('findingCount').textContent=''+(obs.identified_issues||[]).length;
    document.getElementById('cumReward').textContent=totalReward.toFixed(2);
    const actionStr=action.action_type+(action.section?`(${action.section})`:'');
    addStepEntry(stepNum,action.action_type,actionStr,reward,d.done,obs.feedback||'');
    if(d.done){
      episodeActive=false;
      document.getElementById('epStatus').textContent='Done';
      document.getElementById('btnStep').disabled=true;
      document.getElementById('btnSubmit').disabled=true;
      document.getElementById('inputArea').style.display='none';
      document.getElementById('footerStatus').textContent='Episode complete';
      await fetchGrade();
    }
  }catch(e){document.getElementById('footerStatus').textContent='Step error: '+e.message}
}

function addStepEntry(num,type,action,reward,done,feedback){
  const log=document.getElementById('stepLog');
  const rclass=reward>0?'positive':reward<0?'negative':'zero';
  const doneClass=done?' step-done':'';
  log.innerHTML+=`<div class="step-entry${doneClass}">
    <div class="step-header">
      <span class="step-num">STEP ${num}</span>
      <span class="step-reward ${rclass}">${reward>=0?'+':''}${reward.toFixed(4)}</span>
    </div>
    <div class="step-action"><strong>${action}</strong></div>
    <div class="step-desc">${feedback.substring(0,200)}</div>
  </div>`;
  log.scrollTop=log.scrollHeight;
}

async function fetchGrade(){
  try{
    const r=await fetch('/grade');
    const g=await r.json();
    document.getElementById('bigScore').textContent=(g.total_score||0).toFixed(2);
    document.getElementById('mPrecision').textContent=(g.precision||0).toFixed(2);
    document.getElementById('mRecall').textContent=(g.recall||0).toFixed(2);
    document.getElementById('mWorkflow').textContent=(g.severity_accuracy||0).toFixed(2);
    document.getElementById('mEfficiency').textContent=(g.efficiency||0).toFixed(2);
    const diff={section_completeness:'sEasy',eligibility_validation:'sMed',full_protocol_audit:'sHard'};
    const key=diff[selectedTask];
    if(key)document.getElementById(key).textContent=(g.total_score||0).toFixed(2);
    taskScores[selectedTask]=g.total_score||0;
    const vals=Object.values(taskScores);
    if(vals.length>0)document.getElementById('sAvg').textContent=(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(2);
  }catch(e){}
}

function toggleInputs(){
  const t=document.getElementById('actionType').value;
  document.getElementById('issueType').style.display=t==='identify_issue'?'':'none';
  document.getElementById('severity').style.display=t==='identify_issue'?'':'none';
}

setInterval(()=>{document.getElementById('footerTime').textContent=new Date().toLocaleTimeString()},1000);
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the professional dashboard UI."""
    return DASHBOARD_HTML


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api")
async def api_info():
    """JSON info endpoint for programmatic access."""
    return {
        "name": "Clinical Trial Protocol Auditor",
        "version": "1.0.0",
        "spec": "openenv",
        "status": "ready",
        "description": "AI agents audit clinical trial protocols for compliance issues.",
        "tasks": env.get_tasks(),
    }


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    try:
        observation = env.reset(task_id=request.task_id, seed=request.seed)
        return ObservationResponse(
            observation=observation,
            reward=0.0,
            done=False,
            info={"episode_id": observation.get("metadata", {}).get("episode_id", "")},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step(request: StepRequest):
    try:
        action = {
            "action_type": request.action_type,
            "section": request.section,
            "issue_type": request.issue_type,
            "severity": request.severity,
            "description": request.description,
            "recommendation": request.recommendation,
        }
        observation = env.step(action)
        return ObservationResponse(
            observation=observation,
            reward=observation.get("reward", 0.0),
            done=observation.get("done", False),
            info=observation.get("metadata", {}),
        )
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state():
    try:
        return env.state
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def get_tasks():
    return {"tasks": env.get_tasks()}


@app.get("/grade")
async def grade():
    try:
        return env.grade()
    except Exception as e:
        logger.error(f"Grade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup():
    logger.info("Clinical Trial Protocol Auditor environment ready.")
    logger.info(f"Available tasks: {[t['id'] for t in env.get_tasks()]}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
