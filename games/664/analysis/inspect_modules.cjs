const fs=require('fs'),vm=require('vm');
const {JSDOM}=require('../../../deobf/node_modules/jsdom');
const regs=[];
const dom=new JSDOM('<html><body><canvas id="GameCanvas"></canvas></body></html>',{runScripts:'outside-only',pretendToBeVisual:true,url:'https://uat-wbgame.jlfafafa3.com/lj500/?gameID=664'});
const w=dom.window;
w.System={register(...args){regs.push(args);}};
w.requestAnimationFrame=()=>0;w.setTimeout=()=>0;w.setInterval=()=>0;
for(const file of process.argv.slice(2)){
try{vm.runInContext(fs.readFileSync(file,'utf8'),dom.getInternalVMContext(),{timeout:5000,filename:'https://uat-wbgame.jlfafafa3.com/lj500/assets/'+(file.includes('/main/')?'main/':'game/')+file.split('/').pop()});console.log(file,'OK');}catch(e){console.log(file,e.name+": "+e.message+" "+e.stack.split("\n").slice(3,10).join("\n"));}
}
for(let i=0;i<regs.length;i++){const args=regs[i];console.log(i,args.slice(0,-1));fs.writeFileSync(__dirname+'/module-'+i+'.js',args.at(-1).toString());}
console.log('registered',regs.length); try{console.log(vm.runInContext('[87,183,194,198,73,99,167,214].map(n=>[n,n6n4Q.Y51(n)])',dom.getInternalVMContext()));}catch(e){console.log(e.message)};dom.window.close();
