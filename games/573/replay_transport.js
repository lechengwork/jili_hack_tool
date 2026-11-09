// Offline replay only: route API transport to this HTTP origin.
(function(){
 function local(value){try{var u=new URL(String(value),location.href);if(u.protocol==='https:'||u.protocol==='http:')return location.origin+u.pathname+u.search;}catch(e){}return value;}

 [ [HTMLScriptElement,'src'],[HTMLLinkElement,'href'],[HTMLImageElement,'src'],[HTMLIFrameElement,'src'],[HTMLMediaElement,'src'] ].forEach(function(pair){var d=Object.getOwnPropertyDescriptor(pair[0].prototype,pair[1]);if(d&&d.set)Object.defineProperty(pair[0].prototype,pair[1],Object.assign({},d,{set:function(value){d.set.call(this,local(value));}}));});
 var setAttr=Element.prototype.setAttribute;
 Element.prototype.setAttribute=function(name,value){if((name==='src'&&['SCRIPT','IMG','IFRAME','AUDIO','VIDEO'].indexOf(this.tagName)>=0)||(name==='href'&&this.tagName==='LINK'))value=local(value);return setAttr.call(this,name,value);};
 var fetch0=window.fetch;
 window.fetch=function(input,init){
  var original=input&&typeof input.url==='string'?input.url:input;var mapped=local(original);
  if(input&&typeof input.url==='string'){
   var opts={method:input.method,headers:new Headers(input.headers),mode:'same-origin',credentials:'omit',redirect:'follow',cache:'no-store'};
   if(init)Object.assign(opts,init);
   if(input.method!=='GET'&&input.method!=='HEAD')return input.clone().arrayBuffer().then(function(body){opts.body=body;return fetch0.call(window,mapped,opts);});
   return fetch0.call(window,mapped,opts);
  }
  return fetch0.call(window,mapped,init);
 };
 var open=XMLHttpRequest.prototype.open;
 XMLHttpRequest.prototype.open=function(method,url){var args=Array.prototype.slice.call(arguments);args[1]=local(url);return open.apply(this,args);};
 var beacon=navigator.sendBeacon;
 if(beacon)navigator.sendBeacon=function(url,data){return beacon.call(this,local(url),data);};
 var WS=window.WebSocket;
 function LocalSocket(url,protocols){var u=new URL(url,location.href);var target='ws://'+location.host+u.pathname+u.search;return protocols===undefined?new WS(target):new WS(target,protocols);}
 LocalSocket.prototype=WS.prototype;['CONNECTING','OPEN','CLOSING','CLOSED'].forEach(function(k){LocalSocket[k]=WS[k];});window.WebSocket=LocalSocket;
})();
// Local diagnostics: keep queries and all token values out of reports.
(function(){
 var F=window.fetch.bind(window),count=0;
 function report(kind,value){if(String(value).indexOf('16334')>=0)return;if(count++>160)return;try{F('/__replay_diagnostic',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:kind,value:String(value).slice(0,1200)})}).catch(function(){});}catch(e){}}
 function path(value){try{return new URL(String(value),location.href).pathname;}catch(e){return String(value).split('?')[0];}}
 var f=window.fetch;window.fetch=function(input,init){var p=path(input&&input.url||input);if(!/assets\/|cocos-js|\.js$|__replay|__err__/.test(p)){var u=input&&input.url||input;var origin='';try{origin=new URL(String(u),location.href).origin;}catch(e){}report('fetch',p+' origin='+origin+' kind='+Object.prototype.toString.call(input)+' mode='+(input&&input.mode||init&&init.mode||'')+' method='+(input&&input.method||init&&init.method||''));}return f.call(this,input,init);};
 var o=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(method,url){var p=path(url);if(!/assets\/|cocos-js|\.js$/.test(p))report('xhr',method+' '+p);this.addEventListener('error',function(){report('xhr-error',p);});return o.apply(this,arguments);};
 window.addEventListener('error',function(e){report('error',e.message||('resource '+(e.target&&path(e.target.src||e.target.href)||'unknown')));},true);
 var E=console.error;console.error=function(){report('console-error',Array.prototype.map.call(arguments,function(x){return x&&x.stack||String(x);}).join(' '));return E.apply(this,arguments);};
})();
