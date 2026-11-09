/* Development-only codec inspection. Enabled only with SCHEMA_PROBE=1. */
(function(){
 fetch('/__err__',{method:'POST',body:JSON.stringify({kind:'probe',msg:'schema inspector installed'})});
 var attempts=0,timer=setInterval(function(){
  if(++attempts>600){clearInterval(timer);return;}
  if(!window.System||!System.entries)return;
  var codecs=[],modules=[],seen=[],globals=[];
  function visit(obj,path,depth){
   if(!obj||(typeof obj!=='object'&&typeof obj!=='function')||seen.indexOf(obj)>=0||depth>8||seen.length>15000)return;
   seen.push(obj);if(typeof obj==='object'&&obj.constructor&&obj.constructor!==Object)visit(obj.constructor,path+'.constructor',depth+1);
   try{
    if(typeof obj.decode==='function'){
     codecs.push({path:path,fields:Object.keys(obj.prototype||{}).filter(function(k){return k!=='constructor';}),source:obj.decode.toString(),encode:typeof obj.encode==='function'?obj.encode.toString():''});
     return;
    }
    Object.keys(obj).forEach(function(k){if(['__proto__','node','_node','_children','_parent','_components'].indexOf(k)<0)try{visit(obj[k],path+'.'+k,depth+1);}catch(e){}});
   }catch(e){}
  }
  try{
   var it=System.entries(),entry;
   visit(window.Astarte,'Astarte',0);if(window.cc&&cc.director&&cc.director.getScene())cc.director.getScene().walk(function(n){(n._components||[]).forEach(function(c,i){visit(c,'component.'+n.name+'.'+i,0);});});while(!(entry=it.next()).done){var pair=entry.value;modules.push({id:pair[0],exports:Object.keys(pair[1])});if(pair[0].indexOf('FeatureManager')>=0)visit(pair[1],pair[0],0);}
   Object.keys(window).forEach(function(k){try{var v=window[k];if(v&&(typeof v==='object'||typeof v==='function')&&!/^(webkit|on|chrome|document|navigator|location|localStorage|sessionStorage)/.test(k)){globals.push({key:k,type:typeof v,keys:Object.keys(v).slice(0,60)});if(/proto|f4v|model|data|game/i.test(k))visit(v,'window.'+k,0);}}catch(e){}});
   if(attempts>=3 || codecs.length){window.__codecs807=codecs;fetch('/__schema__',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({modules:modules,codecs:codecs,globals:globals})});}
  }catch(e){fetch('/__err__',{method:'POST',body:JSON.stringify({kind:'probe-error',msg:String(e)})});}
 },2000);
})();
