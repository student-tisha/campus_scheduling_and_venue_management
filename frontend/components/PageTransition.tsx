'use client';
import {useEffect,useMemo,useRef,useState} from 'react';

export type Variant='shoji'|'leaves'|'temple'|'ink';
const DUR:Record<Variant,number>={shoji:1200,leaves:1000,temple:1500,ink:1400};
const EASE='cubic-bezier(0.4,0,0.2,1)',WOOD='#8B7355';
type Phase='idle'|'start'|'in'|'out';
const LEAF=(()=>{const p:string[]=[];for(let i=0;i<10;i++){const a=i/10*Math.PI*2-Math.PI/2,r=i%2?5.4:12;p.push(`${(12+Math.cos(a)*r).toFixed(1)},${(12+Math.sin(a)*r).toFixed(1)}`)}return p.join(' ')})();

// Covers the screen, calls onCovered() at the midpoint (swap the page there), then reveals and calls onDone().
export default function PageTransition({active,variant='shoji',onCovered,onDone}:{active:boolean;variant?:Variant;onCovered:()=>void;onDone:()=>void}){
 const[phase,setPhase]=useState<Phase>('idle');
 const cb=useRef({onCovered,onDone});cb.current={onCovered,onDone};
 const half=DUR[variant]/2;
 useEffect(()=>{
  if(!active)return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){cb.current.onCovered();cb.current.onDone();return}
  let t1:any,t2:any;setPhase('start');
  const r=requestAnimationFrame(()=>requestAnimationFrame(()=>{setPhase('in');
   t1=setTimeout(()=>{cb.current.onCovered();setPhase('out');t2=setTimeout(()=>{setPhase('idle');cb.current.onDone()},half)},half)}));
  return()=>{cancelAnimationFrame(r);clearTimeout(t1);clearTimeout(t2)};
 },[active,variant,half]);
 const leaves=useMemo(()=>Array.from({length:56},(_,k)=>{const a=Math.abs(Math.sin(k*12.9898)*43758.5453)%1,b=Math.abs(Math.sin(k*78.233)*12345.678)%1;return{x:a*100,d:b*DUR.leaves*.3,s:22+((a*b*997)%1)*26,dx:(b-.5)*160,rot:(a>.5?1:-1)*(360+b*360)}}),[]);
 if(phase==='idle')return null;
 const s=phase==='start',i=phase==='in',tr=`transform ${half}ms ${EASE}`,fade=`opacity ${half}ms ${EASE}`;
 const panel={position:'absolute' as const,top:0,bottom:0,width:'50%',background:WOOD,backgroundColor:'#F5F0E8',backgroundImage:`linear-gradient(${WOOD} 2px,transparent 2px),linear-gradient(90deg,${WOOD} 2px,transparent 2px)`,backgroundSize:'33.33% 20%',boxShadow:'0 0 40px rgba(0,0,0,.45)',transition:tr};
 return <div aria-hidden className="fixed inset-0 z-[100] overflow-hidden" style={{pointerEvents:'all'}}>
  {variant==='shoji'&&<>
   <div style={{...panel,left:0,borderRight:`6px solid ${WOOD}`,transform:s?'translate(-100%,0)':i?'translate(0,0)':'translate(0,-100%)'}}/>
   <div style={{...panel,right:0,borderLeft:`6px solid ${WOOD}`,transform:s?'translate(100%,0)':i?'translate(0,0)':'translate(0,100%)'}}/></>}

  {variant==='leaves'&&<div style={{position:'absolute',inset:0,background:'#000',opacity:i?1:0,transition:fade}}>
   <style>{`@keyframes tfall{from{transform:translate(0,-12vh) rotate(0)}to{transform:translate(var(--dx),115vh) rotate(var(--rot))}}`}</style>
   {leaves.map((l,k)=><svg key={k} viewBox="0 0 24 24" width={l.s} height={l.s} style={{position:'absolute',left:`${l.x}%`,top:0,fill:'#A82020',animation:s?'none':`tfall ${DUR.leaves*.8}ms linear ${l.d}ms both`,...({'--dx':`${l.dx}px`,'--rot':`${l.rot}deg`} as any)}}><polygon points={LEAF}/></svg>)}</div>}

  {variant==='temple'&&<div style={{position:'absolute',inset:0,background:'#000',opacity:i?1:0,transition:fade,perspective:'900px',display:'grid',placeItems:'center'}}>
   <div style={{position:'relative',width:'min(70vw,420px)',height:'min(80vh,560px)',transform:`translateZ(${s?-500:i?0:600}px)`,transition:tr}}>
    <div style={{position:'absolute',inset:'0 -8% auto',height:'24%',background:'#2D1B1B',clipPath:'polygon(0 100%,50% 0,100% 100%)'}}/>
    <div style={{position:'absolute',inset:'24% 0 0',display:'flex',overflow:'hidden',background:'#0A0A0A',borderTop:'8px solid #5A0F0F'}}>
     {[-1,1].map(d=><div key={d} style={{flex:1,transform:`translateX(${s?d*60:i?0:d*105}%)`,transition:tr,background:'repeating-linear-gradient(#A82020 0 70px,#5A0F0F 70px 74px)',borderInline:'3px solid #5A0F0F'}}/>)}</div></div></div>}

  {variant==='ink'&&<>
   <svg width="0" height="0" style={{position:'absolute'}}><filter id="inkf" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="3" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="140" xChannelSelector="R" yChannelSelector="G"/></filter></svg>
   <div style={{position:'absolute',inset:0,background:'#000',opacity:i?1:0,transition:i?`opacity ${half*.4}ms ${half*.6}ms`:`opacity ${half*.4}ms`}}/>
   <div style={{position:'absolute',inset:0,filter:'url(#inkf)'}}>{[7,22,36,50,64,78,93].map((x,k)=><div key={x} style={{position:'absolute',left:`${x}%`,top:`${[30,65,45,70,35,60,50][k]}%`,width:'70vmax',height:'70vmax',borderRadius:'50%',background:'#000',transform:s?'translate(-50%,-150%) scale(.1)':i?'translate(-50%,-50%) scale(1)':'translate(-50%,-50%) scale(0)',transition:`transform ${half}ms ${EASE} ${k*40}ms`}}/>)}</div></>}
 </div>;
}