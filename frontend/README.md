CIT Scheduler (frontend)

Next.js (App Router) + Tailwind. Runs on mock data in lib/mockData.ts; the room-booking parser in components/App.tsx is a local stand-in for the LLM endpoint.

npm install && npm run dev

Demo accounts (password demo1234, or use the buttons on the login screen): admin@cit.demo, coordinator@cit.demo, faculty@cit.demo, club@cit.demo. Admin > Admin Tools resets demo data and exports schedule.json (shape must be mapped to the official validator schema). Custom domain: add it in your host's project settings, point a CNAME at the host, then set it as primary. Still to write before submission: AI_USAGE.md, THIRD_PARTY.md (Next.js, React, Tailwind, lucide-react, Inter, JetBrains Mono).