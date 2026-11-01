import {DAYS,EVENTS,GROUPS,FACULTY,ROOMS,USERS,Ev} from './mockData';
const API=process.env.NEXT_PUBLIC_API_URL||'http://127.0.0.1:8000';
const H=(p:number)=>p<=5?7+p:8+p;
export async function loadLive(){
 const u=USERS.Admin;
 const lr=await fetch(API+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:u.email,password:u.password})});
 if(!lr.ok)throw new Error('login '+lr.status);
 const tok=(await lr.json()).access_token;
 const h={Authorization:'Bearer '+tok};
 const o=await (await fetch(API+'/api/timetable/options',{headers:h})).json();
 const gs:string[]=(o.groups||[]).map((g:any)=>g.id);
 const lists=await Promise.all(gs.map(g=>fetch(API+'/api/timetable/view?by=group&id='+g,{headers:h}).then(r=>r.json())));
 const seen=new Set<string>(),evs:Ev[]=[],ids:Record<string,number>={};let n=1;
 const idOf=(k:string)=>ids[k]??(ids[k]=n++);
 lists.forEach((v:any)=>(v.entries||[]).forEach((e:any)=>{
  if(seen.has(e.session_id))return;seen.add(e.session_id);
  evs.push({id:e.basket_slot?idOf('B'+e.basket_slot+e.day+e.start_period):idOf(e.session_id),subject:e.course_title+(e.kind==='lecture'?'':' ('+e.kind+')'),faculty:e.faculty_name,group:(e.groups||[]).join('+'),room:e.room_id,day:DAYS.findIndex((d:string)=>d.toUpperCase()===e.day),start:H(e.start_period),end:H(e.end_period)+1});
 }));
 if(!evs.length)throw new Error('empty timetable');
 EVENTS.length=0;EVENTS.push(...evs);
 GROUPS.length=0;GROUPS.push(...gs);
 const fac=Array.from(new Set(evs.map(e=>e.faculty))).sort();
 FACULTY.length=0;FACULTY.push(...fac);
 Object.keys(ROOMS).forEach(k=>delete ROOMS[k]);
 const caps:Record<string,number>={};(o.rooms||[]).forEach((r:any)=>{caps[r.id]=r.capacity});
 Array.from(new Set(evs.map(e=>e.room))).sort().forEach(r=>{ROOMS[r]=caps[r]||100});
}
