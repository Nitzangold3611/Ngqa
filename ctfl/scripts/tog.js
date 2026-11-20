const React=require('react'),R=require('react-dom/server'),sharp=require('sharp');const fa=require('react-icons/fa');
(async()=>{for(const [n,c,f] of [['on','#0E9F97','FaToggleOn'],['off','#121133','FaToggleOff']]){
 const svg=R.renderToStaticMarkup(React.createElement(fa[f],{size:600,color:c}));
 await sharp(Buffer.from(svg)).resize(1000,600,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toFile(`assets/toggle_${n}.png`);}})();
