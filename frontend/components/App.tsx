'use client';
import {useState} from 'react';
import * as Lu from 'lucide-react';
import CinematicLogin from './CinematicLogin';
import PageTransition,{Variant} from './PageTransition';
import KageBackdrop from './KageBackdrop';
import ImportData from './ImportData';
import {DAYS,EVENTS,EXAMS,Ev,FACULTY,GROUPS,REQS,ROOMS,Req,Role,USERS} from '../lib/mockData';

// Looks icons up by name so renamed icons in newer lucide-react versions don't crash the app.
const ic=(...n:string[]):any=>{const m=Lu as any;return m[n.find(k=>m[k])!]};
const AlertTriangle=ic('TriangleAlert','AlertTriangle'),Bell=ic('Bell'),Check=ic('Check'),DoorOpen=ic('DoorOpen'),FileText=ic('FileText'),GitCompare=ic('GitCompare'),
 LayoutDashboard=ic('LayoutDashboard'),ListChecks=ic('ListChecks'),Loader2=ic('LoaderCircle','Loader2'),LogOut=ic('LogOut'),PanelLeft=ic('PanelLeft'),Pencil=ic('Pencil'),
 PlusSquare=ic('SquarePlus','PlusSquare'),Settings=ic('Settings'),User=ic('User'),Users=ic('Users'),X=ic('X'),Clock=ic('Clock'),Upload=ic('Upload');

type Screen='dash'|'import'|'group'|'faculty'|'room'|'midsem'|'book'|'req'|'diff'|'admin';
const A:Role[]=['Admin','Coordinator','Faculty','Club Rep'],M:Role[]=['Admin','Coordinator'],F:Role[]=['Admin','Coordinator','Faculty'];
const NAV:{k:Screen;t:string;I:any;r:Role[]}[]=[
 {k:'dash',t:'Dashboard',I:LayoutDashboard,r:A},{k:'group',t:'Group timetable',I:Users,r:M},
 {k:'faculty',t:'Faculty timetable',I:User,r:F},{k:'room',t:'Room timetable',I:DoorOpen,r:F},
 {k:'midsem',t:'Midsem schedule',I:FileText,r:F},{k:'book',t:'New booking',I:PlusSquare,r:A},
 {k:'req',t:'Requests',I:ListChecks,r:A},{k:'diff',t:'Reschedule diff',I:GitCompare,r:M},{k:'import',t:'Import dataset',I:Upload,r:M},{k:'admin',t:'Admin tools',I:Settings,r:['Admin']}];
const btn='h-9 px-3 rounded border border-line text-sm hover:bg-hov transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed';
const pri='h-9 px-3 rounded bg-acc text-white text-sm hover:bg-blue-700 transition-colors duration-150 disabled:opacity-50';
const inp='h-9 w-full rounded border border-line px-2 text-sm bg-white';
const T=(h:number)=>`${String(Math.floor(h)).padStart(2,'0')}:${h%1?'30':'00'}`;
const clash=(a:Ev,b:Ev)=>a.id!==b.id&&a.day===b.day&&a.start<b.end&&b.start<a.end&&(a.room===b.room||a.faculty===b.faculty||(!!a.group&&a.group===b.group));
const pairs=(l:Ev[])=>l.reduce((n,a)=>n+l.filter(b=>a.id<b.id&&clash(a,b)).length,0);
const validate=(room:string,day:number,s:number,e:number)=>[
 {l:`Room ${room} exists (capacity ${ROOMS[room]??'unknown'})`,ok:room in ROOMS},
 {l:'Room is free for this slot',ok:!EVENTS.some(x=>x.room===room&&x.day===day&&s<x.end&&x.start<e)},
 {l:'Does not cross lunch (13:00 to 14:00)',ok:!(s<14&&e>13)},
 {l:'Inside teaching hours (08:00 to 18:00)',ok:s>=8&&e<=18&&e>s}];
// Local stand-in for the LLM parse endpoint. Replace with a call to the API; the validator stays server-side.
const parse=(t:string)=>{
 const room=t.match(/room\s*(\d+)/i)?.[1],tm=t.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)/i),dy=DAYS.findIndex(d=>new RegExp(d,'i').test(t)),sub=t.match(/for\s+(.+?)\s+(?:class|lecture|exam|event|session)/i)?.[1];
 if(!room||!tm)return null;
 return {room:'R'+room,day:dy<0?0:dy,start:(+tm[1]%12)+(tm[3].toLowerCase()==='pm'?12:0)+(tm[2]?+tm[2]/60:0),dur:1,subject:sub??''};
};
const Card=({t,children}:{t:string;children:React.ReactNode})=><section className="border border-line rounded-md p-4"><h2 className="text-xs font-medium text-mute uppercase tracking-wide mb-3">{t}</h2>{children}</section>;
const Bar=({v,max,bad}:{v:number;max:number;bad?:boolean})=><div className="h-2 bg-hov rounded-sm"><div className={`h-2 rounded-sm ${bad?'bg-bad':'bg-acc'}`} style={{width:Math.min(100,v/max*100)+'%'}}/></div>;
const Badge=({c,children}:{c:string;children:React.ReactNode})=><span className={`px-2 py-0.5 rounded text-xs font-medium ${c}`}>{children}</span>;
const stat:Record<string,string>={Approved:'bg-green-50 text-green-700',Pending:'bg-amber-50 text-amber-700',Rejected:'bg-red-50 text-red-700',High:'bg-red-50 text-red-700',Med:'bg-amber-50 text-amber-700',Low:'bg-hov text-mute'};

function Grid({evs,mode,exam}:{evs:Ev[];mode:'group'|'faculty'|'room';exam?:boolean}){
 const hrs=Array.from({length:10},(_,i)=>8+i);
 const sub=(e:Ev)=>mode==='group'?`${e.faculty} · ${e.room}`:mode==='faculty'?`${e.group} · ${e.room}`:`${e.faculty}${e.group?' · '+e.group:''}`;
 const hrsOn=(d:number)=>evs.filter(e=>e.day===d).reduce((s,e)=>s+e.end-e.start,0);
 return <>
 <div className="hidden md:block overflow-x-auto border border-line rounded-md"><div className="min-w-[900px]">
  <div className="flex border-b border-line bg-side text-xs text-mute"><div className="w-28 shrink-0 p-2">Day</div>{hrs.map(h=><div key={h} className="flex-1 p-2 border-l border-line">{T(h)}</div>)}</div>
  {DAYS.map((d,di)=>{const over=mode==='faculty'&&hrsOn(di)>4;return <div key={d} className={`flex border-b border-line last:border-0 ${over?'bg-red-50':''}`}>
   <div className="w-28 shrink-0 p-2 text-sm font-medium">{d}<div className={`text-xs font-normal ${over?'text-bad':'text-mute'}`}>{hrsOn(di).toFixed(1)} h{over?' (over 4 h cap)':''}</div></div>
   <div className="relative flex-1 h-20" style={{backgroundImage:'linear-gradient(to right,#E5E7EB 1px,transparent 1px)',backgroundSize:'10% 100%'}}>
    {evs.filter(e=>e.day===di).map(e=>{const c=evs.some(b=>clash(e,b));return <div key={e.id} className={`absolute rounded border px-1.5 py-0.5 overflow-hidden text-xs ${c?'border-bad bg-red-50':'border-blue-200 bg-blue-50'}`}
     style={{left:`${(e.start-8)*10}%`,width:`calc(${(e.end-e.start)*10}% - 2px)`,top:c?(e.id%2?'50%':0):0,height:c?'50%':'100%',backgroundImage:exam?'repeating-linear-gradient(135deg,transparent 0 6px,rgba(37,99,235,.12) 6px 8px)':undefined}} title={`${e.subject} ${T(e.start)}-${T(e.end)}`}>
     <div className="font-medium truncate">{e.subject}</div><div className="text-mute truncate">{sub(e)}</div>{c&&<div className="text-bad font-medium">CLASH</div>}</div>})}
   </div></div>})}
 </div></div>
 <div className="md:hidden space-y-2">{DAYS.map((d,di)=><details key={d} className="border border-line rounded-md" open={di===0}><summary className="p-3 font-medium cursor-pointer">{d} <span className="text-mute font-normal">· {hrsOn(di).toFixed(1)} h</span></summary>
  <ul className="border-t border-line divide-y divide-line">{evs.filter(e=>e.day===di).sort((a,b)=>a.start-b.start).map(e=><li key={e.id} className="p-3"><div className="font-medium">{e.subject}</div><div className="text-mute text-xs">{T(e.start)} to {T(e.end)} · {sub(e)}</div>{evs.some(b=>clash(e,b))&&<Badge c="bg-red-50 text-red-700">CLASH</Badge>}</li>)}
  {!evs.some(e=>e.day===di)&&<li className="p-3 text-mute">No sessions.</li>}</ul></details>)}</div></>;
}

function Pick({list,field,mode}:{list:string[];field:'group'|'faculty'|'room';mode:'group'|'faculty'|'room'}){
 const[sel,setSel]=useState(list[0]);const[exam,setExam]=useState(false);
 return <div className="space-y-4"><div className="flex flex-wrap items-center gap-3">
  <select aria-label={`Select ${field}`} className={inp+' !w-48'} value={sel} onChange={e=>setSel(e.target.value)}>{list.map(l=><option key={l}>{l}</option>)}</select>
  {mode==='room'&&<><span className="text-sm">Capacity: <b>{exam?Math.floor(ROOMS[sel]/2):ROOMS[sel]}</b>{exam&&<span className="text-mute"> (halved for exams)</span>}</span>
   <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={exam} onChange={e=>setExam(e.target.checked)}/>Exam mode</label></>}</div>
  <div key={sel} className="fade"><Grid evs={EVENTS.filter(e=>e[field]===sel)} mode={mode} exam={exam}/></div></div>;
}

function Tbl({h,rows}:{h:string[];rows:React.ReactNode[][]}){return <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr className="border-b border-line text-xs text-mute">{h.map(x=><th key={x} className="py-2 pr-4 font-medium">{x}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i} className="border-b border-line last:border-0">{r.map((c,j)=><td key={j} className="py-2 pr-4">{c}</td>)}</tr>)}</tbody></table></div>}

const GCard=({t,i,children}:{t:string;i:number;children:React.ReactNode})=><section className="kanim glass-panel p-6 min-h-[220px]" style={{animation:`cardIn .6s ease-out ${i*.2}s backwards`}}><h2 className="text-[10px] uppercase tracking-[.25em] text-[#8A8A8A] mb-4">{t}</h2>{children}</section>;
const GBar=({v,max}:{v:number;max:number})=><div className="h-1.5 rounded-full bg-white/5"><div className="bar-fill h-full rounded-full bg-gradient-to-r from-red-900 to-red-500" style={{width:Math.min(100,v/max*100)+'%'}}/></div>;
const GRow=({l,r,v,max}:{l:string;r:React.ReactNode;v:number;max:number})=><div><div className="flex justify-between text-[13px] text-white mb-1.5"><span>{l}</span><span>{r}</span></div><GBar v={v} max={max}/></div>;

function Dash({role,name,reqs}:{role:Role;name:string;reqs:Req[]}){
 const hrs=(l:Ev[])=>l.reduce((s,e)=>s+e.end-e.start,0);
 if(role==='Club Rep')return <div className="max-w-3xl"><GCard t="My request status" i={0}><Tbl h={['ID','Type','Status']} rows={reqs.filter(r=>r.requester===name).slice(0,3).map(r=>[r.id,r.type,<Badge key="s" c={stat[r.status]}>{r.status}</Badge>])}/></GCard></div>;
 if(role==='Faculty'){const mine=EVENTS.filter(e=>e.faculty===name);return <div className="grid md:grid-cols-2 gap-6">
  <GCard t="My teaching hours per day (cap 4.0)" i={0}><div className="space-y-3">{DAYS.map((d,i)=>{const h=hrs(mine.filter(e=>e.day===i));return <GRow key={d} l={d} r={<span className={h>4?'text-red-500 font-medium':''}>{h.toFixed(1)} / 4.0</span>} v={h} max={4}/>})}</div></GCard>
  <GCard t="Upcoming classes" i={1}><ul className="divide-y divide-white/10">{[...mine].sort((a,b)=>a.day-b.day||a.start-b.start).map(e=><li key={e.id} className="py-2 text-sm text-white"><b>{e.subject}</b><div className="text-gray-500">{DAYS[e.day]} {T(e.start)} to {T(e.end)} · {e.room} · {e.group}</div></li>)}</ul></GCard></div>}
 const load=DAYS.map((_,d)=>hrs(EVENTS.filter(e=>e.day===d)));
 return <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-6">
  <GCard t="Active clashes" i={0}><div className="flex justify-between items-start"><div className="text-[56px] leading-none font-bold text-red-500">{pairs(EVENTS)}</div><AlertTriangle size={48} strokeWidth={1.5} className="text-red-500"/></div><p className="mt-4 text-[13px] text-gray-500">Overlaps on room, faculty or group</p></GCard>
  <GCard t="Pending requests" i={1}><div className="flex justify-between items-start"><div className="text-[56px] leading-none font-bold text-amber-500">{reqs.filter(r=>r.status==='Pending').length}</div><Clock size={48} strokeWidth={1.5} className="text-amber-500"/></div><p className="mt-4 text-[13px] text-gray-500">Waiting for a decision</p></GCard>
  <GCard t="Room utilization" i={2}><div className="space-y-4">{Object.keys(ROOMS).map(r=>{const h=hrs(EVENTS.filter(e=>e.room===r));return <GRow key={r} l={r} r={Math.round(h/50*100)+'%'} v={h} max={50}/>})}</div></GCard>
  <GCard t="Week 7 load (teaching hours)" i={3}><div className="space-y-3">{DAYS.map((d,i)=><GRow key={d} l={d} r={load[i]+' h'} v={load[i]} max={8}/>)}</div></GCard></div>;
}

function Midsem(){
 const[tab,setTab]=useState<'grid'|'list'>('grid');const[k,setK]=useState<keyof Ev>('day');
 const rows=[...EXAMS].sort((a,b)=>a[k]>b[k]?1:-1);const hd:[string,keyof Ev][]=[['Date','day'],['Time','start'],['Subject','subject'],['Room','room'],['Invigilator','faculty']];
 return <div className="space-y-4"><div className="flex gap-2">{(['grid','list'] as const).map(t=><button key={t} onClick={()=>setTab(t)} aria-pressed={tab===t} className={`${btn} ${tab===t?'bg-hov font-medium':''}`}>{t==='grid'?'Grid View':'List View'}</button>)}</div>
 <p className="text-sm text-bad">{pairs(EXAMS)} exam clash(es) found.</p>
 <div key={tab} className="fade">{tab==='grid'?<Grid evs={EXAMS} mode="room" exam/>:<div className="border border-line rounded-md p-3 overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr className="text-xs text-mute border-b border-line">{hd.map(([l,f])=><th key={l} className="py-2 pr-4"><button onClick={()=>setK(f)} className="font-medium hover:text-ink">{l}{k===f?' ↑':''}</button></th>)}<th/></tr></thead>
 <tbody>{rows.map(e=><tr key={e.id} className="border-b border-line last:border-0"><td className="py-2 pr-4">{DAYS[e.day]} (Wk 7)</td><td className="pr-4">{T(e.start)} to {T(e.end)}</td><td className="pr-4">{e.subject}</td><td className="pr-4">{e.room}</td><td className="pr-4">{e.faculty}</td><td>{EXAMS.some(b=>clash(e,b))&&<Badge c="bg-red-50 text-red-700">CLASH</Badge>}</td></tr>)}</tbody></table></div>}</div></div>;
}

function Book({role,name,add}:{role:Role;name:string;add:(r:Req)=>void}){
 const[f,setF]=useState({day:0,start:9,dur:1,room:Object.keys(ROOMS)[0]??'R204',subject:''});
 const[txt,setTxt]=useState('');const[st,setSt]=useState<'idle'|'loading'|'done'|'fail'>('idle');const[v,setV]=useState(f);
 const checks=(x:typeof f)=>validate(x.room,x.day,x.start,x.start+x.dur);
 const submit=(x:typeof f)=>{const c=checks(x).filter(k=>!k.ok).length;add({id:'RQ-'+(106+Math.floor(Math.random()*900)),requester:name,type:`${x.subject||'Booking'}, ${x.room}`,priority:role==='Admin'?'High':role==='Club Rep'?'Low':'Med',conflicts:c,status:'Pending'});setSt('idle')};
 const go=()=>{setSt('loading');setTimeout(()=>{const p=parse(txt);if(p){setV({...p});setSt('done')}else setSt('fail')},700)};
 const set=(o:Partial<typeof f>)=>setF({...f,...o});
 return <div className="grid lg:grid-cols-2 gap-6">
  <Card t="Manual booking"><div className="space-y-3">
   <label className="block text-sm">Subject or event<input className={inp} value={f.subject} onChange={e=>set({subject:e.target.value})}/></label>
   <div className="grid grid-cols-2 gap-3"><label className="text-sm">Day<select className={inp} value={f.day} onChange={e=>set({day:+e.target.value})}>{DAYS.map((d,i)=><option key={d} value={i}>{d}</option>)}</select></label>
    <label className="text-sm">Room<select className={inp} value={f.room} onChange={e=>set({room:e.target.value})}>{Object.keys(ROOMS).map(r=><option key={r}>{r}</option>)}</select></label>
    <label className="text-sm">Start (hour)<input type="number" step={0.5} min={8} max={18} className={inp} value={f.start} onChange={e=>set({start:+e.target.value})}/></label>
    <label className="text-sm">Duration (h)<input type="number" step={0.5} min={0.5} max={4} className={inp} value={f.dur} onChange={e=>set({dur:+e.target.value})}/></label></div>
   <ul className="text-sm space-y-1">{checks(f).map(c=><li key={c.l} className="flex gap-2 items-center">{c.ok?<Check size={16} className="text-ok"/>:<X size={16} className="text-bad"/>}{c.l}</li>)}</ul>
   <button className={pri} onClick={()=>submit(f)}>Submit for approval</button></div></Card>
  <Card t="Describe it in words"><textarea aria-label="Natural language request" className="w-full h-32 rounded border border-line p-2 text-sm" placeholder="e.g., Book room 302 for AI class next Tuesday at 10 AM" value={txt} onChange={e=>setTxt(e.target.value)}/>
   <button className={pri+' mt-3'} onClick={go} disabled={!txt.trim()||st==='loading'}>Parse with AI</button>
   {st==='fail'&&<p className="mt-3 text-sm text-amber-700 flex gap-2"><AlertTriangle size={16}/>AI parsing incomplete. Please use the manual form on the left.</p>}</Card>
  {(st==='loading'||st==='done')&&<div className="fixed inset-0 bg-black/30 flex justify-end z-40" onClick={()=>setSt('idle')}><aside role="dialog" aria-label="Review parsed request" onClick={e=>e.stopPropagation()} className="fade w-full max-w-md bg-white h-full p-6 overflow-y-auto space-y-4">
   <div className="flex justify-between"><h2 className="text-lg font-semibold">Review parsed request</h2><button aria-label="Close" onClick={()=>setSt('idle')}><X size={20}/></button></div>
   {st==='loading'?<p className="flex gap-2 items-center text-mute"><Loader2 size={16} className="animate-spin"/>Parsing request</p>:<>
    {([['Subject','subject','text'],['Room','room','text'],['Start (hour)','start','number'],['Duration (h)','dur','number']] as const).map(([l,k,t])=><label key={k} className="block text-sm text-mute">{l}<div className="relative"><input type={t} step={0.5} className={inp+' pr-8 text-ink'} value={v[k]} onChange={e=>setV({...v,[k]:t==='number'?+e.target.value:e.target.value})}/><Pencil size={14} aria-hidden className="absolute right-2 top-3 text-mute"/></div></label>)}
    <label className="block text-sm text-mute">Day<select className={inp+' text-ink'} value={v.day} onChange={e=>setV({...v,day:+e.target.value})}>{DAYS.map((d,i)=><option key={d} value={i}>{d}</option>)}</select></label>
    <h3 className="text-sm font-medium">Validator results</h3>
    <ul className="text-sm space-y-1">{checks(v).map(c=><li key={c.l} className="flex gap-2 items-center">{c.ok?<Check size={16} className="text-ok"/>:<X size={16} className="text-bad"/>}{c.l}</li>)}</ul>
    <button className={pri} onClick={()=>submit(v)}>Submit for approval</button></>}</aside></div>}
 </div>;
}

function Requests({role,name,reqs,set}:{role:Role;name:string;reqs:Req[];set:(id:string,s:Req['status'])=>void}){
 const mgr=M.includes(role),rows=mgr?reqs:reqs.filter(r=>r.requester===name);
 return <Tbl h={['ID','Requester','Type','Priority','Conflicts','Status',...(mgr?['Actions']:[])]} rows={rows.map(r=>{const own=r.requester===name,done=r.status!=='Pending';return [
  <span key="i" className="font-mono text-xs">{r.id}</span>,r.requester,r.type,<Badge key="p" c={stat[r.priority]}>{r.priority}</Badge>,
  r.conflicts?<span key="c" className="flex gap-1 items-center text-bad"><AlertTriangle size={16}/>{r.conflicts}</span>:'None',<Badge key="s" c={stat[r.status]}>{r.status}</Badge>,
  ...(mgr?[<span key="a" className="flex gap-2" title={own?'Cannot approve own request':''}>
   <button disabled={own||done} onClick={()=>set(r.id,'Approved')} className="h-8 px-3 rounded border border-ok text-ok text-sm hover:bg-green-50 disabled:opacity-40 disabled:cursor-not-allowed">Approve</button>
   <button disabled={own||done} onClick={()=>set(r.id,'Rejected')} className="h-8 px-3 rounded border border-bad text-bad text-sm hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed">Reject</button></span>]:[])]})}/>;
}

function Diff(){
 const side=(t:string,rows:[string,boolean][],dim?:boolean)=><div className={`border border-line rounded-md p-4 ${dim?'bg-side text-mute':''}`}><h2 className="font-semibold mb-3">{t}</h2><ul className="space-y-2 text-sm">{rows.map(([x,m],i)=><li key={i} className={`p-2 rounded border ${m?'bg-yellow-100 border-yellow-300 text-ink':'border-line'}`}>{x}</li>)}</ul></div>;
 return <div className="space-y-4"><p className="text-sm text-mute">Request RQ-103: move one CS201 session to clear the Tuesday R204 clash. One session moves; nothing else changes.</p>
 <div className="grid md:grid-cols-2 gap-4">{side('Current schedule',[['CS201 Data Structures, CSE-Y2-B, Tue 10:00 to 11:00, R204',true],['EC204 Signals and Systems, ECE-Y2-A, Tue 10:30 to 11:30, R204',false],['CS215 Operating Systems, CSE-Y2-B, Wed 14:00 to 16:00, R204',false]],true)}
 {side('Proposed schedule',[['CS201 Data Structures, CSE-Y2-B, Fri 09:00 to 10:00, R101',true],['EC204 Signals and Systems, ECE-Y2-A, Tue 10:30 to 11:30, R204',false],['CS215 Operating Systems, CSE-Y2-B, Wed 14:00 to 16:00, R204',false]])}</div>
 <Card t="Affected"><ul className="text-sm space-y-1"><li>CSE-Y2-B: time and room changed</li><li>Dr. A. Sahoo: Tuesday load drops from 1.0 h to 0 h, Friday rises to 1.0 h</li><li>ECE-Y2-A: no change, clash on R204 cleared</li></ul></Card></div>;
}

function Admin({reqs,reset,say}:{reqs:Req[];reset:()=>void;say:(m:string)=>void}){
 const[ask,setAsk]=useState(false);
 const exp=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({events:EVENTS,exams:EXAMS,requests:reqs},null,2)],{type:'application/json'}));a.download='schedule.json';a.click();say('schedule.json downloaded')};
 return <div className="space-y-4 max-w-2xl"><Card t="Export"><p className="text-sm text-mute mb-3">Downloads the current events, exams and requests as JSON.</p><button className={pri} onClick={exp}>Export schedule</button></Card>
 <Card t="Reset demo data"><p className="text-sm text-mute mb-3">Restores requests to their starting state.</p><button className="h-9 px-3 rounded border border-bad text-bad text-sm hover:bg-red-50" onClick={()=>setAsk(true)}>Reset Demo Data</button></Card>
 <Card t="Demo accounts"><ul className="divide-y divide-line">{(Object.keys(USERS) as Role[]).map(r=><li key={r} className="py-2 flex justify-between items-center text-sm gap-2"><span><b>{r}</b> <span className="font-mono text-xs text-mute">{USERS[r].email}</span></span><button className={btn} onClick={()=>say(`Password for ${USERS[r].email} reset to ${USERS[r].password}`)}>Reset password</button></li>)}</ul></Card>
 {ask&&<div className="fixed inset-0 bg-black/30 flex items-center justify-center z-40"><div role="dialog" aria-label="Confirm reset" className="fade bg-white rounded-md p-6 max-w-sm w-full mx-4 space-y-4"><h2 className="font-semibold">Reset demo data?</h2><p className="text-sm text-mute">All new and decided requests will be discarded.</p><div className="flex gap-2 justify-end"><button className={btn} onClick={()=>setAsk(false)}>Cancel</button><button className="h-9 px-3 rounded bg-bad text-white text-sm" onClick={()=>{reset();setAsk(false);say('Demo data reset')}}>Reset</button></div></div></div>}</div>;
}

function Main({role,setRole}:{role:Role;setRole:(r:Role|null)=>void}){
 const[scr,setScr]=useState<Screen>('dash');const[col,setCol]=useState(false);const[ver,setVer]=useState(0);
 const[reqs,setReqs]=useState<Req[]>(REQS);const[toast,setToast]=useState('');
 const say=(m:string)=>{setToast(m);setTimeout(()=>setToast(''),3000)};
 const name=USERS[role].name,nav=NAV.filter(n=>n.r.includes(role)),cur=NAV.find(n=>n.k===scr)!;
 return <KageBackdrop><div className="flex h-full">
  <aside className={`hidden md:flex ${col?'w-14':'w-[280px]'} shrink-0 flex-col glass-sidebar border-r border-white/10 transition-all duration-200`}>
   <div className="h-16 flex items-center gap-3 px-4"><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden className="shrink-0"><polygon points="12,0 15.2,7.6 23.4,8.3 17.1,13.7 19.1,21.7 12,17.4 4.9,21.7 6.9,13.7 0.6,8.3 8.8,7.6" fill="#C94B4B"/></svg>{!col&&<span className="font-bold text-base text-white">CIT Scheduling</span>}</div>
   <nav className="flex-1 py-2 px-2 space-y-2 overflow-y-auto" aria-label="Main">{nav.map(n=><button key={n.k} onClick={()=>setScr(n.k)} aria-current={scr===n.k?'page':undefined} title={n.t} className={`w-full flex items-center gap-3 px-3 h-10 rounded-lg text-sm tracking-wide transition-colors duration-150 ${scr===n.k?'text-white bg-red-900/30 shadow-[inset_3px_0_0_#C94B4B,0_0_22px_rgba(201,75,75,.25)]':'text-white/80 hover:text-white hover:bg-white/5'}`}><n.I size={20} className={scr===n.k?'text-[#C94B4B]':'text-gray-500'}/>{!col&&n.t}</button>)}</nav>
   <div className="border-t border-white/10 p-4 space-y-3">{!col&&<><div className="text-sm font-medium text-white truncate">{name}</div><div className="text-xs text-gray-400">{role}</div><button onClick={()=>setRole(null)} className="h-9 w-full rounded-md border border-white/10 bg-black/60 text-white text-sm hover:bg-white/10 transition-colors duration-150">Switch role (sign in again)</button></>}
    <div className="flex gap-2"><button aria-label="Collapse sidebar" className="h-9 w-9 grid place-items-center rounded-full border border-white/10 bg-black/60 text-white hover:bg-white/10" onClick={()=>setCol(!col)}><PanelLeft size={16}/></button><button aria-label="Sign out" className="h-9 w-9 grid place-items-center rounded-md border border-white/10 bg-black/60 text-white hover:bg-white/10" onClick={()=>setRole(null)}><LogOut size={16}/></button></div></div></aside>
  <div className="flex-1 min-w-0 flex flex-col h-full"><header className="h-16 shrink-0 flex items-center justify-between px-4 md:px-8 bg-white/[.03] backdrop-blur-xl border-b border-white/10">
   <div><div className="text-[10px] tracking-[.25em] uppercase text-[#8A8A8A]">CIT Scheduling / {cur.t}</div><h1 className="text-2xl font-bold uppercase tracking-tight text-white">{cur.t}</h1></div>
   <div className="flex items-center gap-2"><select aria-label="Go to page" className="md:hidden h-9 w-36 rounded-md border border-white/10 bg-black/60 text-white px-2 text-sm" value={scr} onChange={e=>setScr(e.target.value as Screen)}>{nav.map(n=><option key={n.k} value={n.k}>{n.t}</option>)}</select>
    <button aria-label="Notifications" className="h-9 w-9 grid place-items-center rounded-lg border border-white/10 bg-white/5 text-white hover:border-white/30 hover:shadow-[0_0_14px_rgba(201,75,75,.45)] transition-all duration-150"><Bell size={20}/></button>
    <button aria-label="Sign out" className="md:hidden h-9 w-9 grid place-items-center rounded-md border border-white/10 bg-black/60 text-white" onClick={()=>setRole(null)}><LogOut size={16}/></button></div></header>
   <main className="flex-1 overflow-y-auto p-4 md:p-8"><div key={scr+'-'+ver} className="fade max-w-[1400px]">
    {scr==='dash'&&<Dash role={role} name={name} reqs={reqs}/>}{scr!=='dash'&&<div className="rounded-2xl bg-white/95 text-[#111827] p-4 md:p-8">
    {scr==='group'&&<Pick list={GROUPS} field="group" mode="group"/>}{scr==='faculty'&&<Pick list={FACULTY} field="faculty" mode="faculty"/>}{scr==='room'&&<Pick list={Object.keys(ROOMS)} field="room" mode="room"/>}
    {scr==='midsem'&&<Midsem/>}{scr==='book'&&<Book role={role} name={name} add={r=>{setReqs([r,...reqs]);say(`${r.id} submitted`)}}/>}
    {scr==='req'&&<Requests role={role} name={name} reqs={reqs} set={(id,s)=>{setReqs(reqs.map(r=>r.id===id?{...r,status:s}:r));say(`${id} ${s.toLowerCase()}`)}}/>}
    {scr==='diff'&&<Diff/>}{scr==='import'&&<ImportData say={say} onApplied={()=>setVer(v=>v+1)}/>}{scr==='admin'&&<Admin reqs={reqs} reset={()=>setReqs(REQS)} say={say}/>}</div>}</div></main></div>
  {toast&&<div role="status" className="slide fixed top-4 right-4 z-50 bg-ink text-white text-sm rounded px-4 py-2 shadow-lg">{toast}</div>}</div></KageBackdrop>;
}

const TRANSITION:Variant='shoji'; // 'shoji' | 'leaves' | 'temple' | 'ink'
export default function App(){
 const[role,setRole]=useState<Role|null>(null);const[pending,setPending]=useState<Role|null>(null);
 return <>{role?<Main role={role} setRole={setRole}/>:<CinematicLogin onIn={r=>{if(!pending)setPending(r)}}/>}
  <PageTransition active={pending!==null} variant={TRANSITION} onCovered={()=>setRole(pending)} onDone={()=>setPending(null)}/></>;
}