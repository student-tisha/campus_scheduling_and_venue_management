export type Role='Admin'|'Coordinator'|'Faculty'|'Club Rep';
export type Ev={id:number;subject:string;faculty:string;group:string;room:string;day:number;start:number;end:number};
export type Req={id:string;requester:string;type:string;priority:'High'|'Med'|'Low';conflicts:number;status:'Pending'|'Approved'|'Rejected'};
export const DAYS=['Mon','Tue','Wed','Thu','Fri'];
export const USERS:Record<Role,{name:string;email:string;password:string}>={
 Admin:{name:'Institute Admin',email:'admin@cit.edu',password:'Admin@123'},
 Coordinator:{name:'Dr. S. Panda',email:'coordinator@cit.edu',password:'Coord@123'},
 Faculty:{name:'Dr. A. Sahoo',email:'faculty@cit.edu',password:'Faculty@123'},
 'Club Rep':{name:'Ananya Das',email:'club@cit.edu',password:'Club@123'}};
export const GROUPS=['CSE-Y2-A','CSE-Y2-B','ECE-Y2-A','ECE-Y3-A','ME-Y1-A'];
export const FACULTY=['Dr. A. Sahoo','Dr. S. Panda','Dr. B. Nayak','Dr. K. Rout'];
export const ROOMS:Record<string,number>={R101:80,R204:60,R302:40,Lab3:30};
export const EVENTS:Ev[]=[
 {id:1,subject:'CS201 Data Structures',faculty:'Dr. A. Sahoo',group:'CSE-Y2-A',room:'R204',day:0,start:9,end:10},
 {id:2,subject:'CS201 Data Structures',faculty:'Dr. A. Sahoo',group:'CSE-Y2-B',room:'R204',day:1,start:10,end:11},
 {id:3,subject:'EC204 Signals and Systems',faculty:'Dr. S. Panda',group:'ECE-Y2-A',room:'R204',day:1,start:10.5,end:11.5},
 {id:4,subject:'CS205 DBMS',faculty:'Dr. A. Sahoo',group:'CSE-Y2-A',room:'Lab3',day:2,start:11,end:13},
 {id:5,subject:'EC301 Embedded Systems',faculty:'Dr. B. Nayak',group:'ECE-Y3-A',room:'Lab3',day:0,start:14,end:16},
 {id:6,subject:'ME102 Engineering Mechanics',faculty:'Dr. K. Rout',group:'ME-Y1-A',room:'R302',day:3,start:9,end:11},
 {id:7,subject:'CS201 Data Structures',faculty:'Dr. A. Sahoo',group:'CSE-Y2-A',room:'R204',day:3,start:9,end:10},
 {id:8,subject:'CS210 Algorithms',faculty:'Dr. A. Sahoo',group:'CSE-Y2-A',room:'R302',day:2,start:9,end:11},
 {id:9,subject:'CS215 Operating Systems',faculty:'Dr. A. Sahoo',group:'CSE-Y2-B',room:'R204',day:2,start:14,end:16},
 {id:10,subject:'EC210 Electrical Machines',faculty:'Dr. S. Panda',group:'ECE-Y2-A',room:'R101',day:4,start:10,end:12},
 {id:11,subject:'EC301 Embedded Systems',faculty:'Dr. B. Nayak',group:'ECE-Y3-A',room:'Lab3',day:3,start:14,end:16}];
export const EXAMS:Ev[]=[
 {id:101,subject:'CS201 Data Structures',faculty:'Dr. K. Rout',group:'',room:'R204',day:0,start:10,end:12},
 {id:102,subject:'EC204 Signals and Systems',faculty:'Dr. B. Nayak',group:'',room:'R204',day:0,start:11,end:13},
 {id:103,subject:'CS205 DBMS',faculty:'Dr. S. Panda',group:'',room:'R101',day:1,start:10,end:12},
 {id:104,subject:'ME102 Engineering Mechanics',faculty:'Dr. A. Sahoo',group:'',room:'R302',day:2,start:14,end:16},
 {id:105,subject:'EC301 Embedded Systems',faculty:'Dr. K. Rout',group:'',room:'R101',day:3,start:10,end:12}];
export const REQS:Req[]=[
 {id:'RQ-101',requester:'Ananya Das',type:'Club event, R101',priority:'Low',conflicts:1,status:'Pending'},
 {id:'RQ-102',requester:'Dr. S. Panda',type:'Guest lecture, R302',priority:'Med',conflicts:0,status:'Pending'},
 {id:'RQ-103',requester:'Dr. A. Sahoo',type:'Extra class, Lab3',priority:'Med',conflicts:2,status:'Pending'},
 {id:'RQ-104',requester:'Ananya Das',type:'Spectra workshop, R204',priority:'High',conflicts:0,status:'Approved'},
 {id:'RQ-105',requester:'Ananya Das',type:'Club meeting, R302',priority:'Low',conflicts:1,status:'Rejected'}];