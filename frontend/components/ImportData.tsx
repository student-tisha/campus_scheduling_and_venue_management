'use client';
import {useState} from 'react';
import {Dataset,TEMPLATE,applyDataset,normalize,parseCSV,restoreDataset} from '../lib/dataset';

const btn='h-9 px-3 rounded border border-gray-300 text-sm hover:bg-gray-100 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed';
const pri='h-9 px-3 rounded bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed';

export default function ImportData({onApplied,say}:{onApplied:()=>void;say:(m:string)=>void}){
 const[res,setRes]=useState<{name:string;d:Dataset}|null>(null);const[err,setErr]=useState('');const[drag,setDrag]=useState(false);
 const read=async(f?:File)=>{
  if(!f)return;setErr('');setRes(null);
  if(f.size>10*1024*1024){setErr('File is larger than 10 MB.');return}
  try{const t=await f.text();const raw=f.name.toLowerCase().endsWith('.csv')?{sessions:parseCSV(t)}:JSON.parse(t);setRes({name:f.name,d:normalize(raw)})}
  catch{setErr('Could not read this file. It must be valid JSON or CSV.')}
 };
 const download=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([TEMPLATE],{type:'application/json'}));a.download='dataset-template.json';a.click()};
 const d=res?.d;
 return <div className="space-y-6 max-w-3xl">
  <p className="text-sm text-gray-600">Load your own timetable data. The file is read in your browser and is not uploaded anywhere. Accepted: JSON with <code>sessions</code>, <code>exams</code>, <code>rooms</code>, <code>faculty</code>, <code>groups</code>, or a CSV of sessions. Days are Mon to Fri, times are HH:MM between 08:00 and 18:00.</p>
  <label onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);read(e.dataTransfer.files[0])}}
   className={`block rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors duration-150 ${drag?'border-blue-600 bg-blue-50':'border-gray-300 hover:bg-gray-50'}`}>
   <span className="text-sm font-medium">Drop a .json or .csv file here, or click to choose</span>
   <input type="file" accept=".json,.csv,application/json,text/csv" className="sr-only" onChange={e=>{read(e.target.files?.[0]);e.target.value=''}}/></label>
  {err&&<p className="text-sm text-red-600">{err}</p>}
  {d&&<div className="space-y-4">
   <h2 className="font-semibold">{res!.name}</h2>
   <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">{([['Sessions',d.events.length],['Exams',d.exams.length],['Rooms',Object.keys(d.rooms).length],['Faculty',d.faculty.length],['Groups',d.groups.length]] as [string,number][]).map(([l,n])=><div key={l} className="rounded border border-gray-200 p-3"><div className="text-2xl font-semibold">{n}</div><div className="text-xs text-gray-500">{l}</div></div>)}</div>
   {d.errors.length>0&&<ul className="text-sm text-red-600 list-disc pl-5">{d.errors.map((x,i)=><li key={i}>{x}</li>)}</ul>}
   {d.warnings.length>0&&<ul className="text-sm text-amber-700 list-disc pl-5">{d.warnings.map((x,i)=><li key={i}>{x}</li>)}</ul>}
   <button className={pri} disabled={!d.events.length} onClick={()=>{applyDataset(d);onApplied();say(`Dataset loaded: ${d.events.length} sessions`)}}>Use this dataset</button></div>}
  <div className="flex flex-wrap gap-2 border-t border-gray-200 pt-4">
   <button className={btn} onClick={download}>Download template</button>
   <button className={btn} onClick={()=>{restoreDataset();onApplied();say('Built-in sample data restored')}}>Restore sample data</button></div>
 </div>;
}