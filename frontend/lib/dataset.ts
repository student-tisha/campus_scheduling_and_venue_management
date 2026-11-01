import {EVENTS,EXAMS,FACULTY,GROUPS,ROOMS,Ev} from './mockData';

export type Dataset={events:Ev[];exams:Ev[];rooms:Record<string,number>;faculty:string[];groups:string[];errors:string[];warnings:string[]};
const KEY='cit-dataset';
const snap=JSON.stringify({events:EVENTS,exams:EXAMS,rooms:ROOMS,faculty:FACULTY,groups:GROUPS});

export const TEMPLATE=JSON.stringify({
 rooms:[{id:'R101',capacity:80},{id:'Lab3',capacity:30}],faculty:['Dr. A. Sahoo'],groups:['CSE-Y2-A'],
 sessions:[{subject:'CS201 Data Structures',faculty:'Dr. A. Sahoo',group:'CSE-Y2-A',room:'R101',day:'Mon',start:'09:00',end:'10:00'}],
 exams:[{subject:'CS201 Data Structures',faculty:'Dr. A. Sahoo',room:'R101',day:'Tue',start:'10:00',end:'12:00'}]},null,2);

const pick=(o:any,...k:string[])=>{for(const x of k){const v=o?.[x];if(v!==undefined&&v!==null&&v!=='')return v}};
const DAYN=['mon','tue','wed','thu','fri'];
const day=(v:any)=>{if(typeof v==='number')return v;const i=DAYN.indexOf(String(v??'').slice(0,3).toLowerCase());return i>=0?i:(v!==undefined&&v!==''&&!isNaN(+v)?+v:-1)};
const hr=(v:any)=>{if(typeof v==='number')return v;const m=String(v??'').match(/^(\d{1,2}):(\d{2})/);return m?+m[1]+(+m[2])/60:NaN};
const rows=(v:any):any[]=>Array.isArray(v)?v:[];
const names=(v:any,...k:string[])=>rows(v).map(x=>String(typeof x==='string'?x:pick(x,...k)??'')).filter(Boolean);

export function parseCSV(t:string):any[]{
 const L=t.split(/\r?\n/).filter(l=>l.trim());if(L.length<2)return [];
 const cut=(l:string)=>l.split(',').map(c=>c.trim().replace(/^"|"$/g,''));const h=cut(L[0]).map(x=>x.toLowerCase());
 return L.slice(1).map(l=>{const c=cut(l);return Object.fromEntries(h.map((k,i)=>[k,c[i]]))});
}

// Maps a parsed file to the shape the app uses. Rows that fail are skipped and reported, never guessed.
export function normalize(raw:any):Dataset{
 const errors:string[]=[],warnings:string[]=[];
 const conv=(list:any[],label:string,base:number):Ev[]=>{
  const out:Ev[]=[];let bad=0;
  list.forEach((o,i)=>{
   const subject=pick(o,'subject','course','course_name','title'),room=pick(o,'room','venue','room_id'),d=day(pick(o,'day','weekday')),s=hr(pick(o,'start','start_time'));
   const endRaw=pick(o,'end','end_time'),e=endRaw!==undefined?hr(endRaw):s+Number(pick(o,'duration'));
   const why=!subject?'subject':!room?'room':!(d>=0&&d<=4)?'day (use Mon to Fri)':!(s>=8&&e<=18&&e>s)?'time (start and end must be between 08:00 and 18:00)':'';
   if(why){bad++;if(bad<=8)errors.push(`${label} row ${i+1}: missing or invalid ${why}`);return}
   out.push({id:base+out.length,subject:String(subject),faculty:String(pick(o,'faculty','teacher','instructor','invigilator')??''),group:String(pick(o,'group','student_group','class')??''),room:String(room),day:d,start:s,end:e});
  });
  if(bad>8)errors.push(`${label}: ${bad-8} more rows skipped`);
  return out;
 };
 const events=conv(rows(raw?.sessions??raw?.events??raw?.timetable),'Session',1);
 const exams=conv(rows(raw?.exams??raw?.midsems??raw?.midsem),'Exam',101);
 if(!events.length)errors.push('No valid sessions found.');
 if(!exams.length)warnings.push('No exams found; the midsem screen will be empty.');
 const rooms:Record<string,number>={};const rr=raw?.rooms;
 if(Array.isArray(rr))rr.forEach((r:any)=>{const id=typeof r==='string'?r:pick(r,'id','name','code','room');if(id)rooms[String(id)]=typeof r==='string'?0:Number(pick(r,'capacity','cap','seats'))||0});
 else if(rr&&typeof rr==='object')Object.entries(rr).forEach(([k,v])=>{rooms[k]=Number(v)||0});
 let assumed=false;
 [...events,...exams].forEach(e=>{if(!rooms[e.room]){rooms[e.room]=60;assumed=true}});
 if(assumed)warnings.push('Some rooms had no capacity in the file; 60 was assumed for them.');
 const faculty=Array.from(new Set([...names(raw?.faculty,'name','faculty'),...events.map(e=>e.faculty)].filter(Boolean)));
 const groups=Array.from(new Set([...names(raw?.groups,'name','id','group'),...events.map(e=>e.group)].filter(Boolean)));
 return {events,exams,rooms,faculty,groups,errors,warnings};
}

// The app reads these shared arrays directly, so they are replaced in place.
export function applyDataset(d:Dataset,save=true){
 EVENTS.splice(0,EVENTS.length,...d.events);EXAMS.splice(0,EXAMS.length,...d.exams);
 GROUPS.splice(0,GROUPS.length,...d.groups);FACULTY.splice(0,FACULTY.length,...d.faculty);
 Object.keys(ROOMS).forEach(k=>delete ROOMS[k]);Object.assign(ROOMS,d.rooms);
 if(save)try{localStorage.setItem(KEY,JSON.stringify({events:d.events,exams:d.exams,rooms:d.rooms,faculty:d.faculty,groups:d.groups}))}catch{}
}
export function restoreDataset(){
 try{localStorage.removeItem(KEY)}catch{}
 applyDataset({...JSON.parse(snap),errors:[],warnings:[]},false);
}
if(typeof window!=='undefined')try{const s=localStorage.getItem(KEY);if(s)applyDataset({...JSON.parse(s),errors:[],warnings:[]},false)}catch{}