import React,{useState}from"react";
import{createRoot}from"react-dom/client";
import{Play,CheckCircle2,XCircle,BrainCircuit,ShieldCheck,Search,LineChart}from"lucide-react";
import"./styles.css";
const API=import.meta.env.VITE_API_URL||"http://localhost:8001";
const icons={planner:BrainCircuit,researcher:Search,analyst:LineChart,reviewer:ShieldCheck,executor:CheckCircle2,human:ShieldCheck};
function App(){
 const[objective,setObjective]=useState("Create a launch plan for an AI customer-support copilot with measurable quality and safety gates.");
 const[run,setRun]=useState(null);const[busy,setBusy]=useState(false);
 async function request(path,options={}){const response=await fetch(API+path,{headers:{"Content-Type":"application/json"},...options});const data=await response.json();if(!response.ok)throw new Error(data.detail||"Request failed");return data;}
 async function start(){setBusy(true);try{setRun(await request("/api/runs",{method:"POST",body:JSON.stringify({objective})}));}catch(e){alert(e.message);}finally{setBusy(false);}}
 async function decide(action){setBusy(true);try{setRun(await request("/api/runs/"+run.id+"/"+action,{method:"POST",body:JSON.stringify({feedback:action==="approve"?"Approved after human review.":"Needs a narrower scope."})}));}catch(e){alert(e.message);}finally{setBusy(false);}}
 return <main><header><div className="brand"><BrainCircuit/> RelayOps</div><span>Agent orchestration console</span></header><section className="hero"><span className="eyebrow">LANGGRAPH CONTROL PLANE</span><h1>Turn objectives into<br/><em>reviewed execution.</em></h1><p>Plan, research, analyze, review, and approve complex work through an observable agent graph.</p><div className="composer"><textarea value={objective} onChange={e=>setObjective(e.target.value)}/><button onClick={start} disabled={busy||objective.length<10}><Play size={18}/> Launch run</button></div></section>{run&&<section className="workspace"><div className="summary"><div><span>Status</span><b className={"status "+run.status}>{run.status.replace("_"," ")}</b></div><div><span>Risk</span><b>{run.review?.risk_level||"—"}</b></div><div><span>Revisions</span><b>{run.revision}</b></div></div><div className="grid"><article><h2>Agent timeline</h2>{run.events.map((e,i)=>{const Icon=icons[e.agent]||BrainCircuit;return <div className="event" key={i}><Icon size={17}/><div><b>{e.agent}</b><p>{e.message}</p></div></div>})}</article><article><h2>Decision brief</h2><div className="brief">{run.result||run.analysis}</div>{run.status==="awaiting_approval"&&<div className="actions"><button className="approve" onClick={()=>decide("approve")}><CheckCircle2/>Approve</button><button className="reject" onClick={()=>decide("reject")}><XCircle/>Reject</button></div>}</article></div></section>}</main>
}
createRoot(document.getElementById("root")).render(<App/>);
