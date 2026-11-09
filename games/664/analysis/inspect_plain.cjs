const fs=require('fs'),vm=require('vm');const regs=[];
const ctx=vm.createContext({console,System:{register(...a){regs.push(a)}},setTimeout(){},setInterval(){}});
for(const f of process.argv.slice(2))try{vm.runInContext(fs.readFileSync(f,'utf8'),ctx,{timeout:3000});console.log('OK',f)}catch(e){console.log(e.message,e.stack.split('\n').slice(3,8).join('\n'))}
console.log('regs',regs.length);
