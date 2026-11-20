const React=require('react'),R=require('react-dom/server'),sharp=require('sharp');
const fa=require('react-icons/fa'),md=require('react-icons/md');
const names=['FaSearch','FaUsers','FaFileAlt','FaCode','FaClipboardCheck','FaTools','FaTrophy','FaQuestion','FaBug','FaTasks','FaProjectDiagram','FaChartBar','FaWrench','FaUserTie','FaPen','FaClock','FaExclamationTriangle','FaCheckCircle','FaComments','FaBook','FaLaptopCode','FaLightbulb','FaCogs','FaSitemap','FaShieldAlt','FaDatabase','FaRocket','FaGraduationCap','FaListOl','FaBalanceScale','FaMoneyBillWave','FaHandshake','FaEye','FaRedo','FaLayerGroup','FaRobot','FaChalkboardTeacher','FaUserCheck','FaFlagCheckered','FaCalendarAlt'];
(async()=>{for(const n of names){const I=fa[n];
 const svg=R.renderToStaticMarkup(React.createElement(I,{size:256,color:'#FFFFFF'}));
 const icon=await sharp(Buffer.from(svg)).resize(250,250,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toBuffer();
 const circ=Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><circle cx="256" cy="256" r="250" fill="#121133"/><circle cx="256" cy="256" r="214" fill="none" stroke="#14DACD" stroke-width="10"/><circle cx="452" cy="132" r="22" fill="#F38911"/></svg>`);
 const ic2=await sharp(Buffer.from(svg.replace(/#FFFFFF/g,'#14DACD'))).resize(250,250,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toBuffer();
 await sharp(circ).composite([{input:ic2,left:131,top:131}]).png().toFile(`assets/icons/${n}.png`);}
 console.log('done')})();
