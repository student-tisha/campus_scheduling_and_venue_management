'use client';

import { useState, useEffect, useMemo, useRef } from 'react';

// ============ TYPES ============
type Role = 'admin' | 'coordinator' | 'faculty' | 'club';
type WidgetType = 'clashes' | 'pending' | 'utilization' | 'load' | 'hours' | 'requests';

interface WidgetData {
  type: WidgetType;
  title: string;
  jp: string;
  value?: string | number;
  description?: string;
  color: string;
  chartData?: { label: string; value: number; max?: number }[];
}

interface NavItem {
  id: string;
  label: string;
  icon: string;
}

// ============ MOCK DATA ============
const MOCK_DATA: Record<Role, WidgetData[]> = {
  admin: [
    { type: 'clashes', title: 'ACTIVE CLASHES', jp: '衝突', value: 1, description: 'Overlaps on room, faculty or group', color: 'text-red-500' },
    { type: 'pending', title: 'PENDING REQUESTS', jp: '保留', value: 3, description: 'Waiting for a decision', color: 'text-amber-500' },
    { type: 'utilization', title: 'ROOM UTILIZATION', jp: '部屋', color: 'text-blue-400', chartData: [
      { label: 'R101', value: 4 }, { label: 'R204', value: 12 }, { label: 'R302', value: 8 }, { label: 'Lab3', value: 12 }
    ]},
    { type: 'load', title: 'WEEK 7 LOAD (TEACHING HOURS)', jp: '授業', color: 'text-emerald-400', chartData: [
      { label: 'Mon', value: 3, max: 8 }, { label: 'Tue', value: 2, max: 8 }, { label: 'Wed', value: 6, max: 8 }, { label: 'Thu', value: 5, max: 8 }, { label: 'Fri', value: 2, max: 8 }
    ]},
  ],
  coordinator: [
    { type: 'pending', title: 'PENDING REQUESTS', jp: '保留', value: 3, description: 'Awaiting your approval', color: 'text-amber-500' },
    { type: 'utilization', title: 'ROOM UTILIZATION', jp: '部屋', color: 'text-blue-400', chartData: [
      { label: 'R101', value: 4 }, { label: 'R204', value: 12 }, { label: 'R302', value: 8 }, { label: 'Lab3', value: 12 }
    ]},
    { type: 'load', title: 'WEEK 7 LOAD', jp: '授業', color: 'text-emerald-400', chartData: [
      { label: 'Mon', value: 3, max: 8 }, { label: 'Tue', value: 2, max: 8 }, { label: 'Wed', value: 6, max: 8 }, { label: 'Thu', value: 5, max: 8 }, { label: 'Fri', value: 2, max: 8 }
    ]},
    { type: 'requests', title: 'RECENT REQUESTS', jp: '依頼', color: 'text-purple-400', chartData: [
      { label: 'Approved', value: 12 }, { label: 'Pending', value: 3 }, { label: 'Rejected', value: 1 }
    ]},
  ],
  faculty: [
    { type: 'hours', title: 'MY TEACHING HOURS', jp: '時間', value: '3.5 / 4.0', description: 'Weekly cap: 4 hours', color: 'text-blue-400' },
    { type: 'load', title: 'WEEKLY SCHEDULE', jp: '授業', color: 'text-emerald-400', chartData: [
      { label: 'Mon', value: 2, max: 4 }, { label: 'Tue', value: 1, max: 4 }, { label: 'Wed', value: 3, max: 4 }, { label: 'Thu', value: 2, max: 4 }, { label: 'Fri', value: 0, max: 4 }
    ]},
    { type: 'requests', title: 'MY REQUESTS', jp: '依頼', color: 'text-purple-400', chartData: [
      { label: 'Approved', value: 4 }, { label: 'Pending', value: 1 }, { label: 'Rejected', value: 0 }
    ]},
    { type: 'clashes', title: 'SCHEDULE CONFLICTS', jp: '衝突', value: 0, description: 'No conflicts detected', color: 'text-emerald-400' },
  ],
  club: [
    { type: 'requests', title: 'MY REQUESTS', jp: '依頼', color: 'text-purple-400', chartData: [
      { label: 'Approved', value: 2 }, { label: 'Pending', value: 1 }, { label: 'Rejected', value: 0 }
    ]},
    { type: 'pending', title: 'PENDING STATUS', jp: '保留', value: 1, description: '1 request awaiting review', color: 'text-amber-500' },
    { type: 'utilization', title: 'ROOM AVAILABILITY', jp: '部屋', color: 'text-blue-400', chartData: [
      { label: 'Hall A', value: 20 }, { label: 'Hall B', value: 45 }, { label: 'Lab 1', value: 60 }
    ]},
    { type: 'clashes', title: 'BOOKING CONFLICTS', jp: '衝突', value: 0, description: 'No conflicts', color: 'text-emerald-400' },
  ],
};

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { id: 'group', label: 'Group Timetable', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
  { id: 'faculty', label: 'Faculty Timetable', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { id: 'room', label: 'Room Timetable', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { id: 'midsem', label: 'Midsem Schedule', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
  { id: 'book', label: 'New Booking', icon: 'M12 4v16m8-8H4' },
  { id: 'req', label: 'Requests', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
  { id: 'diff', label: 'Reschedule Diff', icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
];

// ============ SVG LEAF PATH ============
const LEAF_PATH = (() => {
  const p: string[] = [];
  for (let i = 0; i < 10; i++) {
    const a = (i / 10) * Math.PI * 2 - Math.PI / 2;
    const r = i % 2 ? 5.4 : 12;
    p.push(`${(12 + Math.cos(a) * r).toFixed(1)},${(12 + Math.sin(a) * r).toFixed(1)}`);
  }
  return p.join(' ');
})();

// ============ SUB-COMPONENTS ============

const Lantern = () => (
  <svg viewBox="0 0 100 160" aria-hidden className="h-full w-auto drop-shadow-2xl">
    <g fill="#262626" stroke="#0e0e0e" strokeWidth="2">
      <rect x="28" y="142" width="44" height="12" />
      <rect x="42" y="102" width="16" height="40" />
      <rect x="30" y="98" width="40" height="8" />
      <rect x="32" y="64" width="36" height="36" fill="#161616" />
      <polygon points="18,64 50,38 82,64" />
      <circle cx="50" cy="32" r="7" />
    </g>
    <rect className="kflick" x="38" y="70" width="24" height="24" fill="#FF9D00" />
  </svg>
);

function BarChart({ data, color }: { data: { label: string; value: number; max?: number }[]; color: string }) {
  const maxVal = Math.max(...data.map(d => d.max || d.value), 1);
  return (
    <div className="space-y-2.5 mt-3">
      {data.map((d, i) => (
        <div key={i} className="group">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-medium text-white/90">{d.label}</span>
            <span className="text-xs text-white/70">{d.value}{d.max ? ` / ${d.max}` : '%'}{!d.max && '%'}</span>
          </div>
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${color.includes('red') ? 'bg-gradient-to-r from-red-900 to-red-500' : color.includes('blue') ? 'bg-gradient-to-r from-blue-900 to-blue-400' : color.includes('emerald') ? 'bg-gradient-to-r from-emerald-900 to-emerald-400' : color.includes('amber') ? 'bg-gradient-to-r from-amber-900 to-amber-400' : 'bg-gradient-to-r from-purple-900 to-purple-400'}`}
              style={{ width: `${(d.value / maxVal) * 100}%`, animationDelay: `${i * 100}ms` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function Widget({ data, index }: { data: WidgetData; index: number }) {
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), index * 150);
    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 transition-all duration-700 ease-out hover:scale-[1.02] hover:border-white/20 hover:shadow-2xl hover:shadow-red-900/10 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-[10px] tracking-[0.25em] text-gray-400 uppercase font-medium">
            {data.title}
          </h3>
        </div>
        {data.jp && (
          <span
            className="text-white/30 text-lg font-light"
            style={{ fontFamily: '"Noto Sans JP", sans-serif', writingMode: 'vertical-rl' }}
          >
            {data.jp}
          </span>
        )}
      </div>

      {/* Content */}
      {data.type === 'clashes' || data.type === 'pending' || data.type === 'hours' ? (
        <>
          <div className={`text-5xl font-bold ${data.color} mb-2`}>
            {data.value}
          </div>
          {data.description && (
            <p className="text-sm text-gray-500">{data.description}</p>
          )}
        </>
      ) : data.chartData ? (
        <BarChart data={data.chartData} color={data.color} />
      ) : null}

      {/* Decorative corner accent */}
      <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-white/5 to-transparent rounded-bl-full pointer-events-none" />
    </div>
  );
}

// ============ MAIN DASHBOARD COMPONENT ============

export default function KageDashboard() {
  const [role, setRole] = useState<Role>('admin');
  const [activeNav, setActiveNav] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);

  const widgets = MOCK_DATA[role];

  // Mouse parallax
  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: (e.clientY / window.innerHeight - 0.5) * 2,
      });
    };
    const handleScroll = () => setScrollY(window.scrollY);
    
    window.addEventListener('mousemove', handleMouse);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('mousemove', handleMouse);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Falling leaves
  const leaves = useMemo(() =>
    Array.from({ length: 25 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      duration: 8 + Math.random() * 7,
      delay: Math.random() * 10,
      size: 0.6 + Math.random() * 0.8,
      color: ['#A82020', '#C94B4B', '#8B1A1A'][i % 3],
    })), []);

  // Cherry blossom petals
  const petals = useMemo(() =>
    Array.from({ length: 14 }, (_, i) => ({
      id: i,
      left: (i * 73) % 100,
      duration: 9 + (i * 2.3) % 7,
      delay: (i * 1.7) % 9,
    })), []);

  const parallaxBg = { transform: `translate(${mousePos.x * -12}px, ${mousePos.y * -8}px) translateY(${scrollY * 0.1}px)` };
  const parallaxFg = { transform: `translate(${mousePos.x * 16}px, ${mousePos.y * 6}px) translateY(${scrollY * 0.3}px)` };

  return (
    <div ref={rootRef} className="fixed inset-0 overflow-hidden text-white" style={{ background: 'linear-gradient(#0A0A0A, #111)' }}>
      {/* CSS Animations */}
      <style>{`
        @keyframes moonPulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.85; transform: scale(1.05); } }
        @keyframes branchSway { 0%, 100% { transform: rotate(-1.2deg); } 50% { transform: rotate(1.4deg); } }
        @keyframes lanternFlicker { 0%, 100% { opacity: 1; filter: drop-shadow(0 0 14px rgba(255,157,0,0.7)); } 30% { opacity: 0.7; filter: drop-shadow(0 0 18px rgba(255,157,0,0.9)); } 55% { opacity: 0.95; filter: drop-shadow(0 0 12px rgba(255,157,0,0.6)); } 80% { opacity: 0.78; filter: drop-shadow(0 0 16px rgba(255,157,0,0.8)); } }
        @keyframes fallLeaf { 0% { transform: translateY(-10vh) translateX(0) rotate(0deg); opacity: 0; } 10% { opacity: 1; } 100% { transform: translateY(110vh) translateX(100px) rotate(720deg); opacity: 0.8; } }
        @keyframes petal { from { transform: translate(0, -6vh) rotate(0); } to { transform: translate(90px, 106vh) rotate(540deg); } }
        @keyframes kgrain { 0% { transform: translate(0, 0); } 25% { transform: translate(-4%, 3%); } 50% { transform: translate(3%, -5%); } 75% { transform: translate(-5%, -2%); } 100% { transform: translate(0, 0); } }
        .kflick { animation: lanternFlicker 3s ease-in-out infinite; }
        .leaf-anim { animation: fallLeaf linear infinite; }
        @media (prefers-reduced-motion: reduce) { .kflick, .leaf-anim, .kanim { animation: none !important; } }
      `}</style>

      {/* ============ BACKGROUND LAYERS ============ */}
      
      {/* Carbon fiber texture */}
      <div aria-hidden className="absolute inset-0 z-0 opacity-[0.12]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Cpath d='M0 0L4 4M4 0L0 4' stroke='%23444' stroke-width='1'/%3E%3C/svg%3E")`
      }} />

      {/* Parallax background layer */}
      <div aria-hidden className="absolute inset-0 overflow-hidden transition-transform duration-200 ease-out" style={parallaxBg}>
        {/* Blood Red Moon */}
        <div className="absolute z-[1] rounded-full overflow-hidden top-[8%] right-[10%] w-[220px] md:w-[320px] aspect-square"
          style={{
            background: 'radial-gradient(circle at 40% 40%, #C94B4B, #8B1A1A)',
            boxShadow: '0 0 60px rgba(139,26,26,0.6), 0 0 100px rgba(139,26,26,0.3)',
            animation: 'moonPulse 8s ease-in-out infinite',
          }}>
          <svg className="w-full h-full opacity-30 mix-blend-multiply">
            <filter id="km"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4" /></filter>
            <rect width="100%" height="100%" filter="url(#km)" />
          </svg>
        </div>

        {/* Temple Silhouette */}
        <svg viewBox="0 0 800 460" className="absolute z-[2] left-[2%] bottom-[8%] w-[min(85vw,750px)] opacity-75">
          <g fill="#0A0A0A">
            <path d="M60 120Q400 50 740 120L700 150H100Z" />
            <path d="M30 215Q400 140 770 215L730 248H70Z" />
            <path d="M100 90Q400 30 700 90L680 110H120Z" fill="#1a1a1a" />
          </g>
          <g fill="#8B1A1A">
            <rect x="150" y="150" width="500" height="22" />
            <rect x="130" y="248" width="540" height="20" />
            <rect x="170" y="268" width="36" height="192" />
            <rect x="594" y="268" width="36" height="192" />
            <rect x="200" y="110" width="400" height="12" />
          </g>
          {/* Lanterns on temple */}
          <g className="kflick">
            {[280, 340, 400, 460, 520].map((x, i) => (
              <rect key={x} x={x} y="285" width="14" height="20" fill="#FF9D00"
                style={{ animationDelay: `${i * 0.5}s`, filter: 'drop-shadow(0 0 10px rgba(255,157,0,0.8))' }} />
            ))}
          </g>
        </svg>
      </div>

      {/* Midground foliage */}
      <div aria-hidden className="absolute inset-0 pointer-events-none" style={parallaxFg}>
        <svg viewBox="0 0 300 300" className="absolute z-[12] right-0 bottom-0 w-[40vw] max-w-[380px] opacity-60">
          <g fill="#0d130d">
            <ellipse cx="220" cy="280" rx="110" ry="70" />
            <ellipse cx="130" cy="300" rx="90" ry="60" />
            <ellipse cx="270" cy="200" rx="50" ry="80" />
          </g>
          {[[200, 230, 10], [240, 260, -30], [150, 270, 50], [270, 180, 20]].map(([x, y, r]) => (
            <polygon key={x} points={LEAF_PATH} fill="#A82020"
              transform={`translate(${x} ${y}) rotate(${r}) scale(1.6)`} />
          ))}
        </svg>

        {/* Stone Lantern */}
        <div aria-hidden className="absolute z-[15] bottom-[2%] left-[3%] h-[100px] md:h-[140px]">
          <Lantern />
        </div>
      </div>

      {/* Falling Leaves */}
      <div aria-hidden className="absolute inset-0 z-[18] pointer-events-none overflow-hidden">
        {leaves.map((l) => (
          <svg key={l.id} viewBox="0 0 24 24" className="absolute leaf-anim"
            style={{
              left: `${l.left}%`,
              width: `${l.size * 24}px`,
              height: `${l.size * 24}px`,
              animationDuration: `${l.duration}s`,
              animationDelay: `${l.delay}s`,
            }}>
            <polygon points={LEAF_PATH} fill={l.color} />
          </svg>
        ))}
      </div>

      {/* Foreground Maple Branch */}
      <svg aria-hidden viewBox="0 0 400 400"
        className="kanim absolute z-20 bottom-0 left-0 w-[min(55vw,480px)] pointer-events-none"
        style={{
          transformOrigin: '0% 100%',
          animation: 'branchSway 6s ease-in-out infinite',
          ...parallaxFg,
        }}>
        <g stroke="#1a0f0b" strokeWidth="12" strokeLinecap="round" fill="none">
          <path d="M0 400C60 330 110 300 170 240S280 130 380 70" />
          <path d="M120 280C150 250 150 200 190 170" strokeWidth="7" />
          <path d="M230 190C260 200 300 190 330 160" strokeWidth="6" />
        </g>
        {Array.from({ length: 20 }, (_, i) => (
          <polygon key={i} points={LEAF_PATH}
            fill={i % 2 ? '#C94B4B' : '#A82020'}
            transform={`translate(${40 + i * 17 + Math.sin(i * 5) * 14} ${380 - i * 15 + Math.cos(i * 3) * 18}) rotate(${(i * 47) % 360}) scale(${1.1 + (i % 3) * 0.35})`} />
        ))}
        {Array.from({ length: 12 }, (_, i) => (
          <g key={i} transform={`translate(${70 + i * 24 + Math.cos(i * 4) * 12} ${340 - i * 19 + Math.sin(i * 2) * 14})`}>
            <circle r="6" fill={i % 2 ? '#FFB7C5' : '#FFD1DC'} />
            <circle r="2" fill="#C94B4B" />
          </g>
        ))}
      </svg>

      {/* Falling Cherry Blossom Petals */}
      {petals.map((p) => (
        <span key={p.id} aria-hidden
          className="kanim absolute z-[19] w-2 h-2 rounded-full bg-[#FFB7C5]/70 pointer-events-none"
          style={{
            left: `${p.left}%`,
            top: '-10px',
            animation: `petal ${p.duration}s linear ${p.delay}s infinite`,
          }} />
      ))}

      {/* ============ UI OVERLAY ============ */}

      {/* Top Navigation */}
      <nav className="fixed top-0 inset-x-0 z-40 h-16 px-6 md:px-12 flex items-center justify-between bg-gradient-to-b from-black/90 via-black/60 to-transparent backdrop-blur-sm border-b border-white/5">
        <div className="flex items-center gap-3">
          <svg width="14" height="22" viewBox="0 0 14 22" aria-hidden>
            <rect x="6" width="2" height="4" fill="#8A8A8A" />
            <ellipse cx="7" cy="13" rx="6" ry="8" fill="#8B1A1A" />
          </svg>
          <div>
            <div className="font-bold text-sm tracking-wide">ACADEMIQ</div>
            <div className="hidden sm:block text-[9px] tracking-[0.25em] text-gray-400">THE HIDDEN REALMS OF MANAGEMENT</div>
          </div>
        </div>

        {/* Role Switcher */}
        <div className="flex items-center gap-3">
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            className="bg-black/60 border border-white/20 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-red-700 transition-colors"
          >
            <option value="admin">Admin</option>
            <option value="coordinator">Coordinator</option>
            <option value="faculty">Faculty</option>
            <option value="club">Club Rep</option>
          </select>
        </div>
      </nav>

      {/* Left Sidebar */}
      <aside className={`fixed left-0 top-16 bottom-0 z-30 w-64 bg-black/60 backdrop-blur-md border-r border-white/10 transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
        <div className="p-4 overflow-y-auto h-full">
          <div className="mb-6 px-3">
            <div className="text-[10px] tracking-[0.25em] text-gray-400 uppercase mb-1">Welcome</div>
            <div className="text-sm font-semibold text-white">Dr. S. Panda</div>
            <div className="text-[10px] text-gray-500 capitalize">{role}</div>
          </div>

          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                  activeNav === item.id
                    ? 'bg-white/10 text-white border-l-2 border-red-700'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                </svg>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="absolute bottom-4 left-4 right-4">
            <button className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-400 hover:text-white hover:bg-white/5 transition-colors border border-white/10">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-20 left-4 z-50 md:hidden p-2 bg-black/80 border border-white/20 rounded-lg"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Main Content */}
      <main className="absolute inset-0 z-30 overflow-y-auto pt-24 pb-16 px-6 md:px-8 md:pl-72 scroll-smooth">
        {/* Page Header */}
        <div className="mb-8 max-w-[1400px]">
          <div className="flex items-center gap-2 text-[10px] tracking-[0.25em] text-gray-400 uppercase mb-2">
            <span className="inline-block w-1.5 h-1.5 bg-red-600 rounded-full" />
            <span>Chapter 01 — The Dashboard</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            Where Focus Reveals the Future
          </h1>
          <p className="text-sm text-gray-400 mt-2 max-w-xl">
            Your scheduling command center. Monitor clashes, manage requests, and oversee room utilization.
          </p>
        </div>

        {/* Widgets Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-[1400px]">
          {widgets.map((widget, i) => (
            <Widget key={widget.type} data={widget} index={i} />
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 max-w-[1400px]">
          <h2 className="text-[10px] tracking-[0.25em] text-gray-400 uppercase mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'New Booking', icon: 'M12 4v16m8-8H4' },
              { label: 'View Requests', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
              { label: 'Timetables', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
              { label: 'Export Data', icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4' },
            ].map((action) => (
              <button
                key={action.label}
                className="flex items-center gap-3 px-4 py-3 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl text-sm text-white hover:border-white/30 hover:bg-white/5 transition-all duration-300"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d={action.icon} />
                </svg>
                {action.label}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Film Grain Overlay */}
      <div aria-hidden className="absolute inset-0 z-[45] overflow-hidden pointer-events-none">
        <div className="kanim absolute -inset-[10%] opacity-[0.07]"
          style={{
            animation: 'kgrain 0.9s steps(6) infinite',
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`,
          }} />
      </div>

      {/* Vignette */}
      <div aria-hidden className="absolute inset-0 z-[46] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.6) 75%, rgba(0,0,0,0.9) 100%)' }} />
    </div>
  );
}