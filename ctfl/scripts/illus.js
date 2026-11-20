const React=require('react'),R=require('react-dom/server'),sharp=require('sharp');
const fa=require('react-icons/fa');
const T={
quality:['FaClipboardCheck','FaCheckCircle','FaSearch'],bug:['FaBug','FaExclamationTriangle','FaSearch'],
docs:['FaFileAlt','FaPen','FaListUl'],code:['FaCode','FaLaptopCode','FaCogs'],team:['FaUsers','FaComments','FaHandshake'],
process:['FaProjectDiagram','FaSyncAlt','FaCogs'],agile:['FaRedo','FaUsers','FaTasks'],plan:['FaCalendarAlt','FaClock','FaTasks'],
risk:['FaShieldAlt','FaExclamationTriangle','FaBalanceScale'],metrics:['FaChartBar','FaChartLine','FaClipboardList'],
tools:['FaTools','FaRobot','FaCogs'],review:['FaEye','FaSearch','FaFileAlt'],design:['FaSitemap','FaLightbulb','FaPencilRuler'],
cost:['FaMoneyBillWave','FaChartLine','FaBalanceScale'],learn:['FaGraduationCap','FaBook','FaLightbulb'],data:['FaDatabase','FaServer','FaCogs'],
security:['FaLock','FaShieldAlt','FaUserSecret'],perf:['FaTachometerAlt','FaServer','FaChartLine'],config:['FaCodeBranch','FaLayerGroup','FaHistory'],
users:['FaUserCheck','FaThumbsUp','FaHandshake'],goal:['FaBullseye','FaFlagCheckered','FaTrophy'],levels:['FaLayerGroup','FaSitemap','FaCubes'],
roles:['FaUserTie','FaUserFriends','FaBalanceScale'],devops:['FaInfinity','FaRocket','FaCodeBranch'],question:['FaQuestion','FaLightbulb','FaComments'],
change:['FaWrench','FaSyncAlt','FaTools'],estimate:['FaCalculator','FaClock','FaChartBar'],env:['FaServer','FaNetworkWired','FaDesktop'],
time:['FaHourglassHalf','FaClock','FaCalendarAlt'],rocket:['FaRocket','FaFlagCheckered','FaStar'],
};
const NAVY='#121133',TEAL='#14DACD',TD='#0E9F97',OR='#F38911',TINT='#E8F9F8';
const ic=(n,c,s)=>{const I=fa[n]; if(!I) throw n; return R.renderToStaticMarkup(React.createElement(I,{size:s,color:c}));};
const place=(svg,x,y,s)=>svg.replace('<svg',`<svg x="${x-s/2}" y="${y-s/2}" width="${s}" height="${s}"`).replace(/ (height|width)="\d+"(?=[^>]*viewBox)/g,'');
function A(m,a,b){return `<circle cx="450" cy="470" r="380" fill="${TINT}"/>
<circle cx="450" cy="470" r="300" fill="none" stroke="${TEAL}" stroke-width="4" stroke-dasharray="6 18" stroke-linecap="round"/>
<circle cx="450" cy="470" r="190" fill="${NAVY}"/><circle cx="450" cy="470" r="160" fill="none" stroke="${TEAL}" stroke-width="8"/>
${place(ic(m,TEAL,200),450,470,200)}
<circle cx="700" cy="240" r="95" fill="${TEAL}"/>${place(ic(a,'#FFFFFF',100),700,240,100)}
<circle cx="210" cy="720" r="80" fill="${OR}"/>${place(ic(b,'#FFFFFF',84),210,720,84)}
<circle cx="170" cy="250" r="16" fill="${OR}"/><circle cx="760" cy="720" r="12" fill="${NAVY}"/><circle cx="800" cy="440" r="9" fill="${TEAL}"/>`;}
function B(m,a,b){return `<circle cx="470" cy="450" r="390" fill="${TINT}"/>
<rect x="150" y="190" width="600" height="470" rx="40" fill="#FFFFFF" stroke="${NAVY}" stroke-width="10"/>
<path d="M150 230 a40 40 0 0 1 40 -40 h520 a40 40 0 0 1 40 40 v50 h-600z" fill="${NAVY}"/>
<circle cx="200" cy="236" r="12" fill="${OR}"/><circle cx="240" cy="236" r="12" fill="${TEAL}"/><circle cx="280" cy="236" r="12" fill="#FFFFFF"/>
${place(ic(m,NAVY,210),450,450,210)}
<rect x="250" y="590" width="400" height="14" rx="7" fill="${TEAL}"/>
<circle cx="740" cy="660" r="100" fill="${OR}"/>${place(ic(a,'#FFFFFF',104),740,660,104)}
<circle cx="150" cy="150" r="78" fill="${TEAL}"/>${place(ic(b,'#FFFFFF',80),150,150,80)}
<circle cx="820" cy="250" r="14" fill="${TEAL}"/><circle cx="110" cy="640" r="18" fill="${OR}"/>`;}
function C(m,a,b){return `<path d="M450 70 C700 70 840 230 830 450 C820 690 650 840 440 830 C220 820 70 680 80 450 C90 220 220 70 450 70z" fill="${TINT}"/>
<circle cx="450" cy="400" r="200" fill="#FFFFFF" stroke="${TEAL}" stroke-width="12"/>
${place(ic(m,NAVY,230),450,400,230)}
<rect x="300" y="660" width="300" height="70" rx="35" fill="${NAVY}"/><circle cx="335" cy="695" r="18" fill="${TEAL}"/><rect x="370" y="687" width="190" height="16" rx="8" fill="#FFFFFF" opacity="0.8"/>
<circle cx="160" cy="400" r="78" fill="${NAVY}"/>${place(ic(a,TEAL,84),160,400,84)}
<circle cx="740" cy="400" r="78" fill="${OR}"/>${place(ic(b,'#FFFFFF',84),740,400,84)}
<circle cx="230" cy="180" r="14" fill="${OR}"/><circle cx="690" cy="170" r="10" fill="${NAVY}"/>`;}
(async()=>{for(const [k,[m,a,b]] of Object.entries(T)){ let v=0; for(const F of [A,B,C]){
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900">${F(m,a,b)}</svg>`;
  await sharp(Buffer.from(svg)).png().toFile(`assets/illus/${k}_${v++}.png`);}}
 console.log('ok',Object.keys(T).length)})();
