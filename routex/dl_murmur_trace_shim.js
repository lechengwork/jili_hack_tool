// dl_murmur_trace_shim.js — Phase 3 步驟(a):抓 code-integrity 的 MurmurHash3 實際輸入字串 + 切窗方案。
//
// 靜態已解(bundle.24017.js @~33500-37800 / 54539):
//   • integrity = 鏈式 MurmurHash3_x86_32;t4z = murmur(x0Z, x0Z.length, H_9) & (f2Ε+b4с)
//     c1=0xcc9e2d51 明碼,其餘減法藏(fmix1=c1-1186095846=0x85ebca6b;c2=c1-2971072446=0x1b873593;0xe6546b64=431373843+c1)
//   • 每位元組 = charCodeAt(i) & 0xff;4-byte LE;rotl15/rotl13;種子鏈 H_9 初值 96582,視窗 25000
//   • 被雜湊字串 f0Ο = F2Р.call(О_O) = 某函式 О_O 的 toString(用早期快照的原始 FPT,繞過我們的 hook)
//
// 本 shim 用「未被守的原語」(記憶已證 hook charCodeAt/String 方法【不】觸發自衛;只有 eval/FPT 被守)
// 純側錄,不改任何 byte、不碰 eval/FPT:
//   [1] hook substring/slice/substr → 抓被切的長字串(=О_O 源碼);記 len/頭尾/fnv + 每個(off,size)視窗
//   [2] hook charCodeAt → 確認逐位元組掃描(備援)
// ★重入保護:所有內部字串操作只用「hook 前抓的原始方法」,絕不呼叫被換掉的 prototype 方法。★
(function(){
  var Sp = String.prototype;
  // --- 先抓原始方法(在覆寫之前),內部一律用這些,避免重入 ---
  var oCCA  = Sp.charCodeAt;
  var oSlice= Sp.slice;
  var oSub  = Sp.substring;
  var oSubr = Sp.substr;
  function _cca(s,i){ return oCCA.call(s,i); }
  function _slice(s,a,b){ return oSlice.call(s,a,b); }

  var busy = false;   // 重入旗標:算 fnv/組字串時不重複觸發
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('MURMUR '+m); }catch(e){} }

  // FNV-1a 32-bit,與位元組讀法對齊(char & 0xff),Python 端 dl_murmur_verify.py 可重現。
  function fnv(s){
    var h=0x811c9dc5>>>0, n=s.length;
    for(var i=0;i<n;i++){ h ^= (_cca(s,i) & 0xff); h = (h + ((h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24)))>>>0; }
    return ('00000000'+(h>>>0).toString(16)).slice(-8);
  }
  function esc(s){
    var out='', n=s.length;
    for(var i=0;i<n;i++){ var c=_cca(s,i); out += (c>=0x20 && c<=0x7e) ? String.fromCharCode(c) : ('\\u'+('0000'+c.toString(16)).slice(-4)); }
    return out;
  }

  var BIG = 200000;                 // bundle.24017.js 源碼 ~1e6 code units;一般 app 字串遠短於此
  var bigSig = {};                  // 便宜簽章(len+head32) -> checksum;fnv 每個 distinct 字串只算一次
  var winSig = {}, winCap = 0, WIN_MAX = 200;

  // 回傳該長字串的 checksum(第一次見到才算 fnv 並回報頭尾)
  function idBig(str, via){
    var len = str.length;
    if(len < BIG) return null;
    var head32 = _slice(str,0,32);
    var sig = len+'|'+head32;
    if(bigSig[sig] !== undefined) return bigSig[sig];
    busy = true;
    var cs = fnv(str);
    var head = esc(_slice(str,0,48));
    var tail = esc(_slice(str,len-48,len));
    busy = false;
    bigSig[sig] = cs;
    rep('BIGSTR via='+via+' len='+len+' fnv='+cs);
    rep('BIGSTR-head cs='+cs+' "'+head+'"');
    rep('BIGSTR-tail cs='+cs+' "'+tail+'"');
    return cs;
  }

  // [1] substring / slice / substr —— 主通道:切窗
  ['substring','slice','substr'].forEach(function(name){
    var orig = Sp[name];
    if(typeof orig!=='function') return;
    try{
      Object.defineProperty(Sp, name, { writable:true, configurable:true, value:function(a,b){
        if(!busy){ try{
          var self=this;
          if(self && typeof self.length==='number' && self.length>=BIG){
            var cs = idBig(self, name);
            if(cs!==null){
              var off = (typeof a==='number')? a : 0;
              var sz;
              if(name==='substr'){ sz=(typeof b==='number')? b : (self.length-off); }
              else { var end=(typeof b==='number')? b : self.length; sz=end-off; }
              var s = cs+'|'+off+'|'+sz;
              if(!winSig[s] && winCap<WIN_MAX){ winSig[s]=1; winCap++; rep('WIN '+name+' cs='+cs+' off='+off+' size='+sz); }
            }
          }
        }catch(e){} }
        return orig.apply(this, arguments);
      }});
      try{ Sp[name].toString=function(){return orig.toString();}; }catch(e){}
    }catch(e){ rep('hook-err '+name+' '+((e&&e.message)||e)); }
  });

  // [2] charCodeAt —— 備援:確認對長字串逐位元組讀 + 抓非 substring 的切法
  (function(){
    var scan = {}, lastReport = 0;
    try{
      Object.defineProperty(Sp,'charCodeAt',{ writable:true, configurable:true, value:function(i){
        if(!busy){ try{
          var self=this;
          if(self && typeof self.length==='number' && self.length>=BIG){
            var cs = idBig(self,'charCodeAt');
            if(cs!==null){
              var st=scan[cs]||(scan[cs]={min:i,max:i,count:0});
              if(i<st.min)st.min=i; if(i>st.max)st.max=i; st.count++;
              var now=Date.now();
              if(st.count%50000===0 || (now-lastReport>1500 && st.count>2000)){
                lastReport=now; rep('CCA-scan cs='+cs+' min='+st.min+' max='+st.max+' count='+st.count+' len='+self.length);
              }
            }
          }
        }catch(e){} }
        return oCCA.apply(this, arguments);
      }});
      try{ Sp.charCodeAt.toString=function(){return oCCA.toString();}; }catch(e){}
    }catch(e){ rep('hook-err charCodeAt '+((e&&e.message)||e)); }
  })();

  rep('armed (log-only; hooks substring/slice/substr/charCodeAt; BIG>='+BIG+'; reentry-guarded)');
})();
