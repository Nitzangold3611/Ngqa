const React=require('react'),R=require('react-dom/server'),sharp=require('sharp'),fa=require('react-icons/fa');
const W=1200,H=675,NAVY='#121133',TEAL='#14DACD',OR='#F38911';
function inner(name){const s=R.renderToStaticMarkup(React.createElement(fa[name]));const vb=s.match(/viewBox="([^"]+)"/)[1].split(' ').map(Number);const body=s.replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'');return {vb,body}}
function place(name,cx,cy,size,color){const {vb,body}=inner(name);const sc=size/Math.max(vb[2],vb[3]);
 return `<g transform="translate(${cx-vb[2]*sc/2},${cy-vb[3]*sc/2}) scale(${sc})" fill="${color}">${body}</g>`}
function traces(seed){let s='',r=seed;const rnd=()=>(r=(r*9301+49297)%233280)/233280;
 for(let i=0;i<10;i++){const y=H-12-i*26,a=60+rnd()*300,b=20+rnd()*50,c=30+rnd()*160,col=i%4==2?OR:TEAL;
  s+=`<path d="M0 ${y}H${a}l${b} -${b}H${a+b+c}" stroke="${col}" stroke-width="3" fill="none" opacity=".5"/><circle cx="${a+b+c}" cy="${y-b}" r="6" fill="${col}" opacity=".7"/>`}
 for(let i=0;i<7;i++){const y=14+i*26,a=60+rnd()*260,b=20+rnd()*40,c=30+rnd()*140,col=i%3==1?OR:TEAL;
  s+=`<path d="M${W} ${y}H${W-a}l-${b} ${b}H${W-a-b-c}" stroke="${col}" stroke-width="3" fill="none" opacity=".45"/><circle cx="${W-a-b-c}" cy="${y+b}" r="6" fill="none" stroke="${col}" stroke-width="3" opacity=".7"/>`}
 return s}
const CH=[[1,'FaSearch','FaBug'],[2,'FaSyncAlt','FaCode'],[3,'FaFileAlt','FaSearch'],[4,'FaSitemap','FaCheckCircle'],[5,'FaTasks','FaChartLine'],[6,'FaCogs','FaRobot']];
(async()=>{for(const [n,a,b] of CH){
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
 <rect width="${W}" height="${H}" fill="${NAVY}"/>${traces(n*77)}
 <circle cx="${W/2}" cy="${H/2}" r="215" fill="#1B1A4F"/>
 <circle cx="${W/2}" cy="${H/2}" r="215" fill="none" stroke="${TEAL}" stroke-width="6" opacity=".9"/>
 <circle cx="${W/2}" cy="${H/2}" r="250" fill="none" stroke="${TEAL}" stroke-width="2" opacity=".35" stroke-dasharray="6 12"/>
 ${place(a,W/2-20,H/2-10,230,TEAL)}
 <circle cx="${W/2+150}" cy="${H/2+120}" r="92" fill="${NAVY}"/>
 <circle cx="${W/2+150}" cy="${H/2+120}" r="82" fill="${OR}"/>
 ${place(b,W/2+150,H/2+120,96,'#FFFFFF')}
 <circle cx="${W/2-190}" cy="${H/2-150}" r="14" fill="${OR}"/></svg>`;
 await sharp(Buffer.from(svg)).jpeg({quality:85}).toFile(`site/img/ch${n}.jpg`);}
 console.log('ok')})();
