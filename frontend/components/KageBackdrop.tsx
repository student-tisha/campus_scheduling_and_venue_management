'use client';
import {useMemo,useRef} from 'react';
import {Fx} from './CinematicLogin';

const LEAF=(()=>{const p:string[]=[];for(let i=0;i<10;i++){const a=i/10*Math.PI*2-Math.PI/2,r=i%2?5.4:12;p.push(`${(12+Math.cos(a)*r).toFixed(1)},${(12+Math.sin(a)*r).toFixed(1)}`)}return p.join(' ')})();
const Lantern=()=><svg viewBox="0 0 100 160" aria-hidden className="h-full w-auto"><g fill="#262626" stroke="#0e0e0e" strokeWidth="2"><rect x="28" y="142" width="44" height="12"/><rect x="42" y="102" width="16" height="40"/><rect x="30" y="98" width="40" height="8"/><rect x="32" y="64" width="36" height="36" fill="#161616"/><polygon points="18,64 50,38 82,64"/><circle cx="50" cy="32" r="7"/></g><rect className="kflick" x="38" y="70" width="24" height="24" fill="#FF9D00"/></svg>;

// Fixed cinematic scene behind the app. Children render on top (z-30).
export default function KageBackdrop({children}:{children:React.ReactNode}){
 const root=useRef<HTMLDivElement>(null);
 const move=(e:React.MouseEvent)=>{const s=root.current!.style;s.setProperty('--mx',String(e.clientX/innerWidth*2-1));s.setProperty('--my',String(e.clientY/innerHeight*2-1))};
 const petals=useMemo(()=>Array.from({length:14},(_,i)=>({l:(i*73)%100,d:(i*1.7)%9,t:9+(i*2.3)%7})),[]);
 const bg='translate(calc(var(--mx,0)*-12px),calc(var(--my,0)*-8px))',fg='translate(calc(var(--mx,0)*16px),calc(var(--my,0)*6px))';
 return <div ref={root} onMouseMove={move} className="fixed inset-0 overflow-hidden text-white" style={{background:'linear-gradient(#0A0A0A,#111)'}}>
  <style>{`@keyframes moonPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}@keyframes mist{0%,100%{transform:translateX(-2%)}50%{transform:translateX(2%)}}@keyframes cardIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}@keyframes branchSway{0%,100%{transform:rotate(-1.2deg)}50%{transform:rotate(1.4deg)}}
  @keyframes lanternFlicker{0%,100%{opacity:1}30%{opacity:.7}55%{opacity:.95}80%{opacity:.78}}@keyframes petal{from{transform:translate(0,-6vh) rotate(0)}to{transform:translate(90px,106vh) rotate(540deg)}}
  @keyframes kgrain{0%{transform:translate(0,0)}25%{transform:translate(-4%,3%)}50%{transform:translate(3%,-5%)}75%{transform:translate(-5%,-2%)}100%{transform:translate(0,0)}}
  .kflick{animation:lanternFlicker 3s ease-in-out infinite;filter:drop-shadow(0 0 14px rgba(255,157,0,.7))}
  @media (prefers-reduced-motion:reduce){.kflick,.kanim{animation:none!important}}`}</style>
  <div aria-hidden className="absolute inset-0 z-0 opacity-[.15]" style={{backgroundImage:`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Cpath d='M0 0L4 4M4 0L0 4' stroke='%23444' stroke-width='1'/%3E%3C/svg%3E")`}}/>
  <div aria-hidden className="absolute inset-0" style={{transform:bg,transition:'transform .2s ease-out'}}>
   <div className="kanim absolute z-[1] rounded-full overflow-hidden top-[9%] right-[8%] w-[200px] md:w-[300px] aspect-square" style={{background:'radial-gradient(circle at 40% 40%,#C94B4B,#8B1A1A)',boxShadow:'0 0 60px rgba(139,26,26,.6),0 0 100px rgba(139,26,26,.3)',animation:'moonPulse 8s ease-in-out infinite'}}>
    <svg className="w-full h-full opacity-30 mix-blend-multiply"><filter id="km"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4"/></filter><rect width="100%" height="100%" filter="url(#km)"/></svg></div>
   <svg viewBox="0 0 800 460" className="absolute z-[2] right-[-4%] bottom-[6%] w-[min(88vw,780px)]"><g fill="#0A0A0A"><path d="M60 120Q400 50 740 120L700 150H100Z"/><path d="M30 215Q400 140 770 215L730 248H70Z"/></g><g fill="#8B1A1A"><rect x="150" y="150" width="500" height="22"/><rect x="130" y="248" width="540" height="20"/><rect x="170" y="268" width="36" height="192"/><rect x="594" y="268" width="36" height="192"/></g>{[300,400,500].map((x,i)=><rect key={x} className="kflick" style={{animationDelay:`${i*.7}s`}} x={x} y="300" width="18" height="26" fill="#FF9D00"/>)}</svg>
  </div>
  <svg aria-hidden viewBox="0 0 300 300" className="absolute z-[12] right-0 bottom-0 w-[40vw] max-w-[380px] opacity-70"><g fill="#0d130d"><ellipse cx="220" cy="280" rx="110" ry="70"/><ellipse cx="130" cy="300" rx="90" ry="60"/><ellipse cx="270" cy="200" rx="50" ry="80"/></g>{[[200,230,10],[240,260,-30],[150,270,50],[270,180,20]].map(([x,y,r])=><polygon key={x} points={LEAF} fill="#A82020" transform={`translate(${x} ${y}) rotate(${r}) scale(1.6)`}/>)}</svg>
  <div aria-hidden className="absolute z-[15] bottom-[3%] left-[5%] h-[110px] md:h-[160px]" style={{transform:fg,transition:'transform .2s ease-out'}}><Lantern/></div>
  <Fx rain={false} leaves={16} size={22} alpha={.5} z={18}/>
  <svg aria-hidden viewBox="0 0 400 400" className="kanim absolute z-20 bottom-0 left-0 w-[min(60vw,520px)] pointer-events-none" style={{transformOrigin:'0% 100%',animation:'branchSway 6s ease-in-out infinite'}}>
   <g stroke="#1a0f0b" strokeWidth="12" strokeLinecap="round" fill="none"><path d="M0 400C60 330 110 300 170 240S280 130 380 70"/><path d="M120 280C150 250 150 200 190 170" strokeWidth="7"/><path d="M230 190C260 200 300 190 330 160" strokeWidth="6"/></g>
   {Array.from({length:18},(_,i)=><polygon key={i} points={LEAF} fill={i%2?'#C94B4B':'#A82020'} transform={`translate(${40+i*19+Math.sin(i*5)*14} ${380-i*16+Math.cos(i*3)*18}) rotate(${i*47%360}) scale(${1.1+(i%3)*.35})`}/>)}
   {Array.from({length:11},(_,i)=><g key={i} transform={`translate(${70+i*27+Math.cos(i*4)*12} ${340-i*21+Math.sin(i*2)*14})`}><circle r="6" fill={i%2?'#FFB7C5':'#FFD1DC'}/><circle r="2" fill="#C94B4B"/></g>)}</svg>
  {petals.map((p,i)=><span key={i} aria-hidden className="kanim absolute z-[19] w-2 h-1.5 rounded-full bg-[#FFB7C5]/80" style={{left:`${p.l}%`,top:0,animation:`petal ${p.t}s linear ${p.d}s infinite`}}/>)}

  
  <div aria-hidden className="kanim absolute inset-x-0 bottom-0 h-[45%] z-[22] pointer-events-none" style={{background:'radial-gradient(ellipse at 30% 100%,rgba(180,190,200,.12),transparent 60%),radial-gradient(ellipse at 75% 100%,rgba(180,190,200,.09),transparent 55%)',animation:'mist 20s ease-in-out infinite'}}/>
  <div aria-hidden className="absolute inset-0 z-[25] bg-black/35 pointer-events-none"/>
  <div className="absolute inset-0 z-30">{children}</div>
  <div aria-hidden className="absolute inset-0 z-[45] overflow-hidden pointer-events-none"><div className="kanim absolute -inset-[10%] opacity-[.09]" style={{animation:'kgrain .9s steps(6) infinite',backgroundImage:`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`}}/></div>
  <div aria-hidden className="absolute inset-0 z-[46] pointer-events-none" style={{background:'radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.8) 100%)'}}/>
 </div>;
}