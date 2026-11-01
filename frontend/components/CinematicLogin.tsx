'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Role,USERS} from '../lib/mockData';

const BRAND='ACADEMIQ';
const JP='"Noto Sans JP","Yu Gothic","Hiragino Sans",sans-serif';

export function Fx({rain,leaves,size,alpha,z}:{rain:boolean;leaves:number;size:number;alpha:number;z:number}){
 const ref=useRef<HTMLCanvasElement>(null);
 useEffect(()=>{
  const c=ref.current!,x=c.getContext('2d')!;let w=0,h=0,id=0;
  const fit=()=>{w=c.width=innerWidth;h=c.height=innerHeight};fit();addEventListener('resize',fit);
  const drops=Array.from({length:rain?170:0},()=>({x:Math.random()*innerWidth*1.3,y:Math.random()*innerHeight,l:10+Math.random()*18,s:12+Math.random()*14,a:.06+Math.random()*.18}));
  const lv=Array.from({length:leaves},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:size*(.6+Math.random()*.8),s:.6+Math.random()*1.4,ph:Math.random()*6.28,rot:Math.random()*6.28,vr:(Math.random()-.5)*.03}));
  const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const tick=()=>{x.clearRect(0,0,w,h);x.strokeStyle='#cfd8e0';x.lineWidth=1;
   for(const d of drops){x.globalAlpha=d.a;x.beginPath();x.moveTo(d.x,d.y);x.lineTo(d.x-d.l*.35,d.y+d.l);x.stroke();d.x-=d.s*.35;d.y+=d.s;if(d.y>h||d.x<-20){d.y=-20;d.x=Math.random()*w*1.3}}
   x.fillStyle='#A82020';x.globalAlpha=alpha;
   for(const l of lv){l.ph+=.02;l.x+=Math.sin(l.ph)*1.2;l.y+=l.s;l.rot+=l.vr;if(l.y>h+30){l.y=-30;l.x=Math.random()*w}
    x.save();x.translate(l.x,l.y);x.rotate(l.rot);x.beginPath();
    for(let i=0;i<10;i++){const a=i/10*6.283-1.57,r=i%2?l.r*.45:l.r;x.lineTo(Math.cos(a)*r,Math.sin(a)*r)}
    x.closePath();x.fill();x.restore()}
   if(!still)id=requestAnimationFrame(tick)};
  tick();
  return()=>{cancelAnimationFrame(id);removeEventListener('resize',fit)};
 },[rain,leaves,size,alpha]);
 return <canvas ref={ref} aria-hidden className="fixed inset-0 pointer-events-none" style={{zIndex:z}}/>;
}

export default function CinematicLogin({onIn}:{onIn:(r:Role)=>void}){
 const root=useRef<HTMLDivElement>(null);
 const[e,setE]=useState('');const[p,setP]=useState('');const[err,setErr]=useState('');const[target,setTarget]=useState<Role|null>(null);
 const blades=useMemo(()=>Array.from({length:110},(_,i)=>{const x=i*9.1+Math.sin(i*12.9)*4,h=70+(Math.sin(i*7.3)+1)*45,b=Math.sin(i*3.7)*28;return `M${x} 200Q${x+b*.3} ${200-h*.6} ${x+b} ${200-h}Q${x+b*.5} ${200-h*.5} ${x+5} 200Z`}).join(''),[]);
 const move=(ev:React.MouseEvent)=>{const s=root.current!.style;s.setProperty('--mx',String(ev.clientX/innerWidth*2-1));s.setProperty('--my',String(ev.clientY/innerHeight*2-1))};
 const sign=(ev:React.FormEvent)=>{ev.preventDefault();const r=(Object.keys(USERS) as Role[]).find(k=>USERS[k].email===e.trim().toLowerCase());r&&p===USERS[r].password?onIn(r):setErr('Email or password is incorrect.')};
 const quick=(ev:React.FormEvent)=>{ev.preventDefault();target&&p===USERS[target].password?onIn(target):setErr('Incorrect password for this account.')};
 const pick=(r:Role)=>{setTarget(r);setP('');setErr('')};
 const back=()=>{setTarget(null);setP('');setErr('')};
 const rise=(d:number)=>({animation:`rise .8s ease-out ${d}s both`});
 const bg='translate(calc(var(--mx,0)*-12px),calc(var(--my,0)*-8px))',fg='translate(calc(var(--mx,0)*16px),calc(var(--my,0)*6px))';
 const field='w-full bg-transparent border-b-2 border-white/40 py-2 text-sm font-semibold text-white placeholder:text-gray-400 focus:border-white transition-colors duration-150';
 return <div ref={root} onMouseMove={move} className="fixed inset-0 overflow-hidden text-[#F5F5F5]" style={{background:'linear-gradient(#050505,#111)'}}>
  <style>{`@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
  @keyframes flick{0%,100%{opacity:1}35%{opacity:.72}60%{opacity:.92}80%{opacity:.8}}
  @keyframes grain{0%{transform:translate(0,0)}20%{transform:translate(-4%,3%)}40%{transform:translate(3%,-5%)}60%{transform:translate(-5%,-2%)}80%{transform:translate(4%,4%)}100%{transform:translate(0,0)}}
  .flick{animation:flick 3.2s ease-in-out infinite;filter:drop-shadow(0 0 10px #FF9D00)}
  @media (prefers-reduced-motion:reduce){.flick,.grain{animation:none!important}}`}</style>

  {/* Layer 1: moon, temple */}
  <div className="absolute inset-0 z-0" style={{transform:bg,transition:'transform .2s ease-out'}}>
   <div className="absolute rounded-full overflow-hidden top-[9%] right-[8%] w-[26vmin] h-[26vmin]" style={{background:'radial-gradient(circle at 35% 35%,#b02a2a,#8A1C1C 60%,#4a0d0d)',boxShadow:'0 0 140px 50px rgba(138,28,28,.4)'}}>
    <svg className="w-full h-full opacity-30 mix-blend-multiply" aria-hidden><filter id="moon"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4"/></filter><rect width="100%" height="100%" filter="url(#moon)"/></svg></div>
   <svg viewBox="0 0 800 460" aria-hidden className="absolute left-1/2 -translate-x-1/2 bottom-[12%] w-[min(92vw,950px)]" fill="#0A0A0A">
    <path d="M60 120Q400 50 740 120L700 150H100Z"/><rect x="150" y="150" width="500" height="26"/>
    <path d="M30 215Q400 140 770 215L730 248H70Z"/><rect x="130" y="248" width="540" height="24"/>
    <rect x="170" y="272" width="36" height="188"/><rect x="594" y="272" width="36" height="188"/><rect x="290" y="272" width="30" height="188"/><rect x="480" y="272" width="30" height="188"/>
    <g stroke="#0A0A0A" strokeWidth="2">{[250,355,445,550].map(cx=><line key={cx} x1={cx} y1="272" x2={cx} y2="292"/>)}</g>
    {[250,355,445,550,400].map((cx,i)=><ellipse key={cx} className="flick" style={{animationDelay:`${i*.6}s`}} cx={cx} cy={i===4?190:308} rx="13" ry="18" fill="#FF9D00"/>)}
   </svg>
  </div>
  <Fx rain={false} leaves={9} size={26} alpha={.35} z={5}/>

  {/* Layer 2: giant type */}
  <div aria-hidden className="absolute z-10 inset-x-0 top-1/2 -translate-y-1/2 text-center font-black leading-none select-none pointer-events-none" style={{fontSize:'17vw',color:'rgba(255,255,255,.08)',transform:`translateY(-50%) ${bg}`}}>{BRAND}</div>

  {/* Layer 3: UI */}
  <div className="absolute inset-0 z-20 overflow-y-auto">
   <header className="flex items-center justify-between px-6 md:px-14 pt-6" style={rise(.1)}>
    <div className="flex items-center gap-3"><svg width="14" height="22" viewBox="0 0 14 22" aria-hidden><rect x="6" width="2" height="4" fill="#8A8A8A"/><ellipse cx="7" cy="13" rx="6" ry="8" fill="#8A1C1C"/></svg>
     <span className="font-bold text-sm tracking-wide">{BRAND}</span><span className="hidden sm:block text-[10px] tracking-[.25em] text-[#8A8A8A]">THE HIDDEN REALMS OF MANAGEMENT</span></div>
   </header>
   <main className="px-6 md:px-14 pt-10 md:pt-[8vh] pb-48 max-w-[560px]">
    {target?<>
    <p className="flex items-center gap-2 text-[10px] tracking-[.25em] text-[#8A8A8A]" style={rise(.1)}><span className="w-1.5 h-1.5 rounded-full bg-[#8A1C1C]"/>CHAPTER 02 — {target.toUpperCase()} ACCESS</p>
    <h1 className="mt-4 text-4xl md:text-5xl font-bold uppercase leading-[1] tracking-tight max-w-[500px]" style={rise(.2)}>Enter the {target} password.</h1>
    <p className="mt-4 text-base font-medium text-gray-200 max-w-[400px]" style={rise(.3)}>Quick access only needs the password for this account.</p>
    <form onSubmit={quick} className="mt-8 space-y-4 max-w-[380px]" style={rise(.4)}>
     <input type="password" autoFocus aria-label={`${target} password`} placeholder="Password" className={field} value={p} onChange={x=>{setP(x.target.value);setErr('')}}/>
     {err&&<p className="text-xs text-red-400">{err}</p>}
     <div className="flex items-center gap-5"><button className="h-11 px-5 border border-white/80 text-xs font-bold tracking-[.2em] hover:bg-white hover:text-black transition-colors duration-150">ENTER THE REALM →</button>
      <button type="button" onClick={back} className="text-[11px] font-semibold tracking-[.2em] text-white/70 hover:text-white transition-colors duration-150">← BACK</button></div>
    </form></>:<>
    <p className="flex items-center gap-2 text-[10px] tracking-[.25em] text-[#8A8A8A]" style={rise(.3)}><span className="w-1.5 h-1.5 rounded-full bg-[#8A1C1C]"/>CHAPTER 01 — THE LOGIN GATE</p>
    <h1 className="mt-4 text-4xl md:text-5xl font-bold uppercase leading-[1] tracking-tight max-w-[500px]" style={rise(.45)}>Where focus reveals the future.</h1>
    <p className="mt-4 text-base font-medium text-gray-200 max-w-[400px]" style={rise(.6)}>Enter your credentials to access your classes, tasks, and time. All in sync.</p>
    <form onSubmit={sign} className="mt-8 space-y-4 max-w-[380px]" style={rise(.75)}>
     <input type="email" aria-label="Email address" placeholder="Email address" className={field} value={e} onChange={x=>setE(x.target.value)}/>
     <input type="password" aria-label="Password" placeholder="Password" className={field} value={p} onChange={x=>setP(x.target.value)}/>
     {err&&<p className="text-xs text-red-400">{err}</p>}
     <button className="h-11 px-5 border border-white/80 text-xs font-bold tracking-[.2em] hover:bg-white hover:text-black transition-colors duration-150">ENTER THE REALM →</button>
    </form>
    <div className="mt-8 max-w-[380px]" style={rise(.9)}><p className="text-[10px] tracking-[.25em] text-[#8A8A8A] mb-2">QUICK DEMO ACCESS</p>
     <div className="grid grid-cols-2 gap-2">{([['Admin Demo','Admin'],['Coordinator Demo','Coordinator'],['Faculty Demo','Faculty'],['Club Rep Demo','Club Rep']] as [string,Role][]).map(([l,r])=><button key={r} onClick={()=>pick(r)} className="h-8 border border-white/40 bg-black/40 backdrop-blur-sm text-[11px] font-semibold tracking-widest text-white hover:border-white transition-colors duration-150">{l.toUpperCase()}</button>)}</div></div>
   </>}
   </main>
   <div aria-hidden className="hidden md:block fixed right-6 top-1/2 -translate-y-1/2 text-xl tracking-[.4em] text-white/60" style={{writingMode:'vertical-rl',fontFamily:JP}}>影の道</div>
   <div aria-hidden className="hidden md:block fixed right-14 bottom-[23vh] text-right"><div className="text-2xl font-bold" style={{fontFamily:JP}}>山門</div><div className="text-[10px] tracking-[.25em] text-[#8A8A8A]">SANMON — BEFORE THE BELL</div></div>
   <div aria-hidden className="hidden md:block fixed left-14 bottom-[22vh]"><div className="flex items-center gap-3 text-[10px] tracking-[.25em] text-[#8A8A8A] mb-3">SIGN IN TO ENTER<span className="w-16 border-t border-dashed border-[#8A8A8A]"/></div>
    <div className="flex gap-5 text-3xl font-bold"><span>01</span><span className="text-white/20">02</span><span className="text-white/20">03</span><span className="text-white/20">04</span></div></div>
  </div>

  {/* Layer 4: foreground */}
  <svg viewBox="0 0 1000 200" preserveAspectRatio="none" aria-hidden className="absolute z-30 left-[-2%] w-[104%] bottom-0 h-[22vh] pointer-events-none" style={{transform:fg,transition:'transform .2s ease-out'}}>
   <rect y="192" width="1000" height="8" fill="#1A241A"/><path d={blades} fill="#1A241A"/><path d={blades} fill="#101810" transform="translate(4 8)" opacity=".8"/></svg>
  <Fx rain leaves={6} size={34} alpha={.9} z={35}/>

  {/* Overlays */}
  <div aria-hidden className="absolute inset-0 z-40 overflow-hidden pointer-events-none"><div className="grain absolute -inset-[10%] opacity-[.09]" style={{animation:'grain .9s steps(6) infinite',backgroundImage:`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`}}/></div>
  <div aria-hidden className="absolute inset-0 z-[41] pointer-events-none" style={{background:'radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.85) 100%)'}}/>
 </div>;
}