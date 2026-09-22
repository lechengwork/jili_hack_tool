(window.webpackJsonp=window.webpackJsonp||[]).push([[1],{
/***/1279:
/***/function(e,t,i){var n=i(19),r=i(38),s=i(73),o=/"/g,a=function(e,t,i,n){var r=String(s(e)),a="<"+t;return""!==i&&(a+=" "+i+'="'+String(n).replace(o,"&quot;")+'"'),a+">"+r+"</"+t+">"};e.exports=function(e,t){var i={};i[e]=t(a),n(n.P+n.F*r((function(){var t=""[e]('"');return t!==t.toLowerCase()||t.split('"').length>3})),"String",i)}},
/***/1300:
/***/function(e,t,i){"use strict";
// 22.1.3.6 Array.prototype.fill(value, start = 0, end = this.length)
var n=i(70),r=i(273),s=i(55);e.exports=function(e/* , start = 0, end = @length */){for(var t=n(this),i=s(t.length),o=arguments.length,a=r(o>1?arguments[1]:void 0,i),l=o>2?arguments[2]:void 0,h=void 0===l?i:r(l,i);h>a;)t[a++]=e;return t}},
/***/1311:
/***/function(e,t,i){
// https://github.com/tc39/proposal-object-values-entries
var n=i(19),r=i(431)(!1);n(n.S,"Object",{values:function(e){return r(e)}})},
/***/1387:
/***/function(e,t,i){"use strict";
// https://tc39.github.io/proposal-flatMap/#sec-Array.prototype.flatMap
var n=i(19),r=i(1686),s=i(70),o=i(55),a=i(123),l=i(430);n(n.P,"Array",{flatMap:function(e/* , thisArg */){var t,i,n=s(this);return a(e),t=o(n.length),i=l(n,0),r(i,n,n,t,0,1,e,arguments[1]),i}}),i(143)("flatMap")},
/***/1396:
/***/function(e,t,i){
// 20.1.2.2 Number.isFinite(number)
var n=i(19),r=i(29).isFinite;n(n.S,"Number",{isFinite:function(e){return"number"==typeof e&&r(e)}})},
/***/1401:
/***/function(e,t,i){for(var n,r=i(29),s=i(71),o=i(119),a=o("typed_array"),l=o("view"),h=!(!r.ArrayBuffer||!r.DataView),c=h,u=0,d="Int8Array,Uint8Array,Uint8ClampedArray,Int16Array,Uint16Array,Int32Array,Uint32Array,Float32Array,Float64Array".split(",");u<9;)(n=r[d[u++]])?(s(n.prototype,a,!0),s(n.prototype,l,!0)):c=!1;e.exports={ABV:h,CONSTR:c,TYPED:a,VIEW:l}},
/***/1402:
/***/function(e,t,i){
// https://tc39.github.io/ecma262/#sec-toindex
var n=i(117),r=i(55);e.exports=function(e){if(void 0===e)return 0;var t=n(e),i=r(t);if(t!==i)throw RangeError("Wrong length!");return i}},
/***/1654:
/***/function(e,t,i){i(1655)("Uint8",1,(function(e){return function(t,i,n){return e(this,t,i,n)}}));
/***/},
/***/1655:
/***/function(e,t,i){"use strict";if(i(42)){var n=i(118),r=i(29),s=i(38),o=i(19),a=i(1401),l=i(1656),h=i(72),c=i(144),u=i(121),d=i(71),f=i(145),_=i(117),p=i(55),g=i(1402),w=i(273),m=i(146),v=i(65),y=i(148),b=i(36),x=i(70),S=i(287),k=i(147),O=i(429),I=i(120).f,C=i(288),R=i(119),A=i(30),D=i(99),P=i(286),j=i(189),N=i(285),M=i(122),E=i(191),z=i(190),T=i(1300),$=i(1657),F=i(47),q=i(125),L=F.f,J=q.f,V=r.RangeError,B=r.TypeError,U=r.Uint8Array,W="ArrayBuffer",K="Shared"+W,Q="BYTES_PER_ELEMENT",Y="prototype",G=Array[Y],H=l.ArrayBuffer,Z=l.DataView,X=D(0),ee=D(2),te=D(3),ie=D(4),ne=D(5),re=D(6),se=P(!0),oe=P(!1),ae=N.values,le=N.keys,he=N.entries,ce=G.lastIndexOf,ue=G.reduce,de=G.reduceRight,fe=G.join,_e=G.sort,pe=G.slice,ge=G.toString,we=G.toLocaleString,me=A("iterator"),ve=A("toStringTag"),ye=R("typed_constructor"),be=R("def_constructor"),xe=a.CONSTR,Se=a.TYPED,ke=a.VIEW,Oe="Wrong length!",Ie=D(1,(function(e,t){return Pe(j(e,e[be]),t)})),Ce=s((function(){
// eslint-disable-next-line no-undef
return 1===new U(new Uint16Array([1]).buffer)[0]})),Re=!!U&&!!U[Y].set&&s((function(){new U(1).set({})})),Ae=function(e,t){var i=_(e);if(i<0||i%t)throw V("Wrong offset!");return i},De=function(e){if(b(e)&&Se in e)return e;throw B(e+" is not a typed array!")},Pe=function(e,t){if(!b(e)||!(ye in e))throw B("It is not a typed array constructor!");return new e(t)},je=function(e,t){return Ne(j(e,e[be]),t)},Ne=function(e,t){for(var i=0,n=t.length,r=Pe(e,n);n>i;)r[i]=t[i++];return r},Me=function(e,t,i){L(e,t,{get:function(){return this._d[i]}})},Ee=function(e/* , mapfn, thisArg */){var t,i,n,r,s,o,a=x(e),l=arguments.length,c=l>1?arguments[1]:void 0,u=void 0!==c,d=C(a);if(null!=d&&!S(d)){for(o=d.call(a),n=[],t=0;!(s=o.next()).done;t++)n.push(s.value);a=n}for(u&&l>2&&(c=h(c,arguments[2],2)),t=0,i=p(a.length),r=Pe(this,i);i>t;t++)r[t]=u?c(a[t],t):a[t];return r},ze=function(){for(var e=0,t=arguments.length,i=Pe(this,t);t>e;)i[e]=arguments[e++];return i},Te=!!U&&s((function(){we.call(new U(1))})),$e=function(){return we.apply(Te?pe.call(De(this)):De(this),arguments)},Fe={copyWithin:function(e,t/* , end */){return $.call(De(this),e,t,arguments.length>2?arguments[2]:void 0)},every:function(e/* , thisArg */){return ie(De(this),e,arguments.length>1?arguments[1]:void 0)},fill:function(e/* , start, end */){// eslint-disable-line no-unused-vars
return T.apply(De(this),arguments)},filter:function(e/* , thisArg */){return je(this,ee(De(this),e,arguments.length>1?arguments[1]:void 0))},find:function(e/* , thisArg */){return ne(De(this),e,arguments.length>1?arguments[1]:void 0)},findIndex:function(e/* , thisArg */){return re(De(this),e,arguments.length>1?arguments[1]:void 0)},forEach:function(e/* , thisArg */){X(De(this),e,arguments.length>1?arguments[1]:void 0)},indexOf:function(e/* , fromIndex */){return oe(De(this),e,arguments.length>1?arguments[1]:void 0)},includes:function(e/* , fromIndex */){return se(De(this),e,arguments.length>1?arguments[1]:void 0)},join:function(e){// eslint-disable-line no-unused-vars
return fe.apply(De(this),arguments)},lastIndexOf:function(e/* , fromIndex */){// eslint-disable-line no-unused-vars
return ce.apply(De(this),arguments)},map:function(e/* , thisArg */){return Ie(De(this),e,arguments.length>1?arguments[1]:void 0)},reduce:function(e/* , initialValue */){// eslint-disable-line no-unused-vars
return ue.apply(De(this),arguments)},reduceRight:function(e/* , initialValue */){// eslint-disable-line no-unused-vars
return de.apply(De(this),arguments)},reverse:function(){for(var e,t=this,i=De(t).length,n=Math.floor(i/2),r=0;r<n;)e=t[r],t[r++]=t[--i],t[i]=e;return t},some:function(e/* , thisArg */){return te(De(this),e,arguments.length>1?arguments[1]:void 0)},sort:function(e){return _e.call(De(this),e)},subarray:function(e,t){var i=De(this),n=i.length,r=w(e,n);return new(j(i,i[be]))(i.buffer,i.byteOffset+r*i.BYTES_PER_ELEMENT,p((void 0===t?n:w(t,n))-r))}},qe=function(e,t){return je(this,pe.call(De(this),e,t))},Le=function(e/* , offset */){De(this);var t=Ae(arguments[1],1),i=this.length,n=x(e),r=p(n.length),s=0;if(r+t>i)throw V(Oe);for(;s<r;)this[t+s]=n[s++]},Je={entries:function(){return he.call(De(this))},keys:function(){return le.call(De(this))},values:function(){return ae.call(De(this))}},Ve=function(e,t){return b(e)&&e[Se]&&"symbol"!=typeof t&&t in e&&String(+t)==String(t)},Be=function(e,t){return Ve(e,t=m(t,!0))?u(2,e[t]):J(e,t)},Ue=function(e,t,i){return!(Ve(e,t=m(t,!0))&&b(i)&&v(i,"value"))||v(i,"get")||v(i,"set")||i.configurable||v(i,"writable")&&!i.writable||v(i,"enumerable")&&!i.enumerable?L(e,t,i):(e[t]=i.value,e)};xe||(q.f=Be,F.f=Ue),o(o.S+o.F*!xe,"Object",{getOwnPropertyDescriptor:Be,defineProperty:Ue}),s((function(){ge.call({})}))&&(ge=we=function(){return fe.call(this)});var We=f({},Fe);f(We,Je),d(We,me,Je.values),f(We,{slice:qe,set:Le,constructor:function(){/* noop */},toString:ge,toLocaleString:$e}),Me(We,"buffer","b"),Me(We,"byteOffset","o"),Me(We,"byteLength","l"),Me(We,"length","e"),L(We,ve,{get:function(){return this[Se]}}),
// eslint-disable-next-line max-statements
e.exports=function(e,t,i,l){var h=e+((l=!!l)?"Clamped":"")+"Array",u="get"+e,f="set"+e,_=r[h],w=_||{},m=_&&O(_),v=!_||!a.ABV,x={},S=_&&_[Y],C=function(e,i){L(e,i,{get:function(){return function(e,i){var n=e._d;return n.v[u](i*t+n.o,Ce)}(this,i)},set:function(e){return function(e,i,n){var r=e._d;l&&(n=(n=Math.round(n))<0?0:n>255?255:255&n),r.v[f](i*t+r.o,n,Ce)}(this,i,e)},enumerable:!0})};v?(_=i((function(e,i,n,r){c(e,_,h,"_d");var s,o,a,l,u=0,f=0;if(b(i)){if(!(i instanceof H||(l=y(i))==W||l==K))return Se in i?Ne(_,i):Ee.call(_,i);s=i,f=Ae(n,t);var w=i.byteLength;if(void 0===r){if(w%t)throw V(Oe);if((o=w-f)<0)throw V(Oe)}else if((o=p(r)*t)+f>w)throw V(Oe);a=o/t}else a=g(i),s=new H(o=a*t);for(d(e,"_d",{b:s,o:f,l:o,e:a,v:new Z(s)});u<a;)C(e,u++)})),S=_[Y]=k(We),d(S,"constructor",_)):s((function(){_(1)}))&&s((function(){new _(-1);// eslint-disable-line no-new
}))&&E((function(e){new _,// eslint-disable-line no-new
new _(null),// eslint-disable-line no-new
new _(1.5),// eslint-disable-line no-new
new _(e)}),!0)||(_=i((function(e,i,n,r){var s;
// `ws` module bug, temporarily remove validation length for Uint8Array
// https://github.com/websockets/ws/pull/645
return c(e,_,h),b(i)?i instanceof H||(s=y(i))==W||s==K?void 0!==r?new w(i,Ae(n,t),r):void 0!==n?new w(i,Ae(n,t)):new w(i):Se in i?Ne(_,i):Ee.call(_,i):new w(g(i))})),X(m!==Function.prototype?I(w).concat(I(m)):I(w),(function(e){e in _||d(_,e,w[e])})),_[Y]=S,n||(S.constructor=_));var R=S[me],A=!!R&&("values"==R.name||null==R.name),D=Je.values;d(_,ye,!0),d(S,Se,h),d(S,ke,!0),d(S,be,_),(l?new _(1)[ve]==h:ve in S)||L(S,ve,{get:function(){return h}}),x[h]=_,o(o.G+o.W+o.F*(_!=w),x),o(o.S,h,{BYTES_PER_ELEMENT:t}),o(o.S+o.F*s((function(){w.of.call(_,1)})),h,{from:Ee,of:ze}),Q in S||d(S,Q,t),o(o.P,h,Fe),z(h),o(o.P+o.F*Re,h,{set:Le}),o(o.P+o.F*!A,h,Je),n||S.toString==ge||(S.toString=ge),o(o.P+o.F*s((function(){new _(1).slice()})),h,{slice:qe}),o(o.P+o.F*(s((function(){return[1,2].toLocaleString()!=new _([1,2]).toLocaleString()}))||!s((function(){S.toLocaleString.call([1,2])}))),h,{toLocaleString:$e}),M[h]=A?R:D,n||A||d(S,me,D)}}else e.exports=function(){/* empty */};
/***/},
/***/1656:
/***/function(e,t,i){"use strict";var n=i(29),r=i(42),s=i(118),o=i(1401),a=i(71),l=i(145),h=i(38),c=i(144),u=i(117),d=i(55),f=i(1402),_=i(120).f,p=i(47).f,g=i(1300),w=i(124),m="ArrayBuffer",v="DataView",y="prototype",b="Wrong index!",x=n[m],S=n[v],k=n.Math,O=n.RangeError,I=n.Infinity,C=x,R=k.abs,A=k.pow,D=k.floor,P=k.log,j=k.LN2,N="buffer",M="byteLength",E="byteOffset",z=r?"_b":N,T=r?"_l":M,$=r?"_o":E;
// IEEE754 conversions based on https://github.com/feross/ieee754
function F(e,t,i){var n,r,s,o=new Array(i),a=8*i-t-1,l=(1<<a)-1,h=l>>1,c=23===t?A(2,-24)-A(2,-77):0,u=0,d=e<0||0===e&&1/e<0?1:0;for(
// eslint-disable-next-line no-self-compare
(e=R(e))!=e||e===I?(
// eslint-disable-next-line no-self-compare
r=e!=e?1:0,n=l):(n=D(P(e)/j),e*(s=A(2,-n))<1&&(n--,s*=2),(e+=n+h>=1?c/s:c*A(2,1-h))*s>=2&&(n++,s/=2),n+h>=l?(r=0,n=l):n+h>=1?(r=(e*s-1)*A(2,t),n+=h):(r=e*A(2,h-1)*A(2,t),n=0));t>=8;o[u++]=255&r,r/=256,t-=8);for(n=n<<t|r,a+=t;a>0;o[u++]=255&n,n/=256,a-=8);return o[--u]|=128*d,o}function q(e,t,i){var n,r=8*i-t-1,s=(1<<r)-1,o=s>>1,a=r-7,l=i-1,h=e[l--],c=127&h;for(h>>=7;a>0;c=256*c+e[l],l--,a-=8);for(n=c&(1<<-a)-1,c>>=-a,a+=t;a>0;n=256*n+e[l],l--,a-=8);if(0===c)c=1-o;else{if(c===s)return n?NaN:h?-I:I;n+=A(2,t),c-=o}return(h?-1:1)*n*A(2,c-t)}function L(e){return e[3]<<24|e[2]<<16|e[1]<<8|e[0]}function J(e){return[255&e]}function V(e){return[255&e,e>>8&255]}function B(e){return[255&e,e>>8&255,e>>16&255,e>>24&255]}function U(e){return F(e,52,8)}function W(e){return F(e,23,4)}function K(e,t,i){p(e[y],t,{get:function(){return this[i]}})}function Q(e,t,i,n){var r=f(+i);if(r+t>e[T])throw O(b);var s=e[z]._b,o=r+e[$],a=s.slice(o,o+t);return n?a:a.reverse()}function Y(e,t,i,n,r,s){var o=f(+i);if(o+t>e[T])throw O(b);for(var a=e[z]._b,l=o+e[$],h=n(+r),c=0;c<t;c++)a[l+c]=h[s?c:t-c-1]}if(o.ABV){if(!h((function(){x(1)}))||!h((function(){new x(-1);// eslint-disable-line no-new
}))||h((function(){// eslint-disable-line no-new
return new x,// eslint-disable-line no-new
new x(1.5),// eslint-disable-line no-new
new x(NaN),x.name!=m}))){for(var G,H=(x=function(e){return c(this,x),new C(f(e))})[y]=C[y],Z=_(C),X=0;Z.length>X;)(G=Z[X++])in x||a(x,G,C[G]);s||(H.constructor=x)}
// iOS Safari 7.x bug
var ee=new S(new x(2)),te=S[y].setInt8;ee.setInt8(0,2147483648),ee.setInt8(1,2147483649),!ee.getInt8(0)&&ee.getInt8(1)||l(S[y],{setInt8:function(e,t){te.call(this,e,t<<24>>24)},setUint8:function(e,t){te.call(this,e,t<<24>>24)}},!0)}else x=function(e){c(this,x,m);var t=f(e);this._b=g.call(new Array(t),0),this[T]=t},S=function(e,t,i){c(this,S,v),c(e,x,v);var n=e[T],r=u(t);if(r<0||r>n)throw O("Wrong offset!");if(r+(i=void 0===i?n-r:d(i))>n)throw O("Wrong length!");this[z]=e,this[$]=r,this[T]=i},r&&(K(x,M,"_l"),K(S,N,"_b"),K(S,M,"_l"),K(S,E,"_o")),l(S[y],{getInt8:function(e){return Q(this,1,e)[0]<<24>>24},getUint8:function(e){return Q(this,1,e)[0]},getInt16:function(e/* , littleEndian */){var t=Q(this,2,e,arguments[1]);return(t[1]<<8|t[0])<<16>>16},getUint16:function(e/* , littleEndian */){var t=Q(this,2,e,arguments[1]);return t[1]<<8|t[0]},getInt32:function(e/* , littleEndian */){return L(Q(this,4,e,arguments[1]))},getUint32:function(e/* , littleEndian */){return L(Q(this,4,e,arguments[1]))>>>0},getFloat32:function(e/* , littleEndian */){return q(Q(this,4,e,arguments[1]),23,4)},getFloat64:function(e/* , littleEndian */){return q(Q(this,8,e,arguments[1]),52,8)},setInt8:function(e,t){Y(this,1,e,J,t)},setUint8:function(e,t){Y(this,1,e,J,t)},setInt16:function(e,t/* , littleEndian */){Y(this,2,e,V,t,arguments[2])},setUint16:function(e,t/* , littleEndian */){Y(this,2,e,V,t,arguments[2])},setInt32:function(e,t/* , littleEndian */){Y(this,4,e,B,t,arguments[2])},setUint32:function(e,t/* , littleEndian */){Y(this,4,e,B,t,arguments[2])},setFloat32:function(e,t/* , littleEndian */){Y(this,4,e,W,t,arguments[2])},setFloat64:function(e,t/* , littleEndian */){Y(this,8,e,U,t,arguments[2])}});w(x,m),w(S,v),a(S[y],o.VIEW,!0),t[m]=x,t[v]=S},
/***/1657:
/***/function(e,t,i){"use strict";
// 22.1.3.3 Array.prototype.copyWithin(target, start, end = this.length)
var n=i(70),r=i(273),s=i(55);e.exports=[].copyWithin||function(e/* = 0 */,t/* = 0, end = @length */){var i=n(this),o=s(i.length),a=r(e,o),l=r(t,o),h=arguments.length>2?arguments[2]:void 0,c=Math.min((void 0===h?o:r(h,o))-l,o-a),u=1;for(l<a&&a<l+c&&(u=-1,l+=c-1,a+=c-1);c-- >0;)l in i?i[a]=i[l]:delete i[a],a+=u,l+=u;return i}},
/***/1686:
/***/function(e,t,i){"use strict";
// https://tc39.github.io/proposal-flatMap/#sec-FlattenIntoArray
var n=i(290),r=i(36),s=i(55),o=i(72),a=i(30)("isConcatSpreadable");e.exports=function e(t,i,l,h,c,u,d,f){for(var _,p,g=c,w=0,m=!!d&&o(d,f,3);w<h;){if(w in l){if(_=m?m(l[w],w,i):l[w],p=!1,r(_)&&(p=void 0!==(p=_[a])?!!p:n(_)),p&&u>0)g=e(t,i,_,s(_.length),g,u-1)-1;else{if(g>=9007199254740991)throw TypeError();t[g]=_}g++}w++}return g}},
/***/1713:
/***/function(e,t,i){"use strict";
// B.2.3.3 String.prototype.big()
i(1279)("big",(function(e){return function(){return e(this,"big","","")}}))},
/***/1718:
/***/function(e,t,i){var n=i(1719),r=i(60),s=i(210),o=i(211),a=i(43);function l(e,t){var i="undefined"!=typeof Symbol&&e[Symbol.iterator]||e["@@iterator"];if(!i){if(Array.isArray(e)||(i=function(e,t){if(e){if("string"==typeof e)return h(e,t);var i={}.toString.call(e).slice(8,-1);return"Object"===i&&e.constructor&&(i=e.constructor.name),"Map"===i||"Set"===i?Array.from(e):"Arguments"===i||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(i)?h(e,t):void 0}}(e))||t&&e&&"number"==typeof e.length){i&&(e=i);var n=0,r=function(){};return{s:r,n:function(){return n>=e.length?{done:!0}:{done:!1,value:e[n++]}},e:function(e){throw e},f:r}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var s,o=!0,a=!1;return{s:function(){i=i.call(e)},n:function(){var e=i.next();return o=e.done,e},e:function(e){a=!0,s=e},f:function(){try{o||null==i.return||i.return()}finally{if(a)throw s}}}}function h(e,t){(null==t||t>e.length)&&(t=e.length);for(var i=0,n=Array(t);i<t;i++)n[i]=e[i];return n}i(32),i(8),i(7),i(22),i(18),i(20),i(26),i(424),i(880),i(25),i(15),i(21),i(10),i(46),i(28),i(27);var c=function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:[];return Object.keys(e).filter((function(e){return t.includes(e)})).reduce((function(t,i){return Object.assign(t,a({},i,e[i]))}),{})},u=function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:[];return Object.keys(e).filter((function(e){return!t.includes(e)})).reduce((function(t,i){return Object.assign(t,a({},i,e[i]))}),{})},d=function(){"use strict";
/**
   * Select a subset of fields
   * @param {Array} keys - Array of fields to be picked.
   * @returns {QueryBuilder} Returns current instance to be chained
   */
return o((function e(t,i){var n=t.query,r=t.path,o=t.init,a=t.text,l=t.postprocess,h=void 0===l?[]:l;s(this,e),this.query=n,this.path=r,this.init=o,this.postprocess=h,this.options=i||{},this.onlyKeys=null,this.withoutKeys=null,this.sortKeys=[],this.limitN=null,this.skipN=null,a||
// Remove text field from response
this.postprocess.unshift((function(e){return e.map((function(e){return u(e,["text"])}))}))}),[{key:"only",value:function(e){
// Return current instance
// Assign keys to this.onlyKeys to be processed in fetch
return this.onlyKeys=Array.isArray(e)?e:[e],this}
/**
     * Remove a subset of fields
     * @param {Array} keys - Array of fields to be picked.
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"without",value:function(e){
// Return current instance
// Assign keys to this.withoutKeys to be processed in fetch
return this.withoutKeys=Array.isArray(e)?e:[e],this}
/**
     * Sort results
     * @param {string} field - Field key to sort on.
     * @param {string} direction - Direction of sort (asc / desc).
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"sortBy",value:function(e,t){return this.sortKeys.push([e,"desc"===t]),this}
/**
     * Filter results
     * @param {object} query - Where query.
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"where",value:function(e){return this.query=this.query.find(e),this}
/**
     * Search results
     * @param {(Object|string)} query - Search query object or field or search value.
     * @param {string} value - Value of search (means query equals to field).
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"search",value:function(e,t){
// Passing an empty or falsey value as query will avoid triggering a search to allow optional chaining
return e?(i="object"===r(e)?e:t?{query:{type:"match",field:e,value:t,prefix_length:1,fuzziness:1,extended:!0,minimum_should_match:1}}:{query:{type:"bool",should:this.options.fullTextSearchFields.map((function(t){return{type:"match",field:t,value:e,prefix_length:1,operator:"and",minimum_should_match:1,fuzziness:1,extended:!0}}))}},this.query=this.query.find({$fts:i}).sortByScoring(),this):this;var i}
/**
     * Surround results
     * @param {string} slugOrPath - Slug or path of the file to surround.
     * @param {Object} options - Options to surround (before / after).
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"surround",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{},i=t.before,n=void 0===i?1:i,r=t.after,s=void 0===r?1:r,o=0===e.indexOf("/")?"path":"slug";
// Add slug or path to onlyKeys if only method has been called before
this.onlyKeys&&this.onlyKeys.push(o),
// Remove slug or path from withoutKeys if without method has been called before
this.withoutKeys&&(this.withoutKeys=this.withoutKeys.filter((function(e){return e!==o})));return this.postprocess.push((function(t){var i=t.findIndex((function(t){return t[o]===e})),r=new Array(n+s).fill(null,0);if(-1===i)return r;for(var a=t.slice(i-n,i),l=t.slice(i+1,i+1+s),h=0,c=n-1;c>=0;c--)r[c]=a[h]||null,h++;for(var u=0,d=n;d<=s;d++)r[d]=l[u]||null,u++;return r})),this}
/**
     * Limit number of results
     * @param {number} n - Limit number.
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"limit",value:function(e){return"string"==typeof e&&(e=parseInt(e)),this.limitN=e,this}
/**
     * Skip number of results
     * @param {number} n - Skip number.
     * @returns {QueryBuilder} Returns current instance to be chained
     */},{key:"skip",value:function(e){return"string"==typeof e&&(e=parseInt(e)),this.skipN=e,this}
/**
     * Collect data and apply process filters
     * @returns {(Object|Array)} Returns processed data
     */
// eslint-disable-next-line require-await
},{key:"fetch",value:(e=n(regeneratorRuntime.mark((function e(){var t,i,n,r,s,o,a=this;return regeneratorRuntime.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:this.sortKeys&&this.sortKeys.length&&(this.query=this.query.compoundsort(this.sortKeys)),this.skipN&&(this.query=this.query.offset(this.skipN)),this.limitN&&(this.query=this.query.limit(this.limitN)),
// Collect data without meta fields
t=this.query.data({removeMeta:!0}),// Handle only keys
this.onlyKeys&&(
// Add `path` and `extension` to onlyKeys if watch to ensure live edit
this.options.watch&&this.onlyKeys.push("path","extension"),
// Map data and returns object picked by keys
i=function(e){return e.map((function(e){return c(e,a.onlyKeys)}))},// Apply pick during postprocess
this.postprocess.unshift(i)),
// Handle without keys
this.withoutKeys&&(
// Remove `path` and `extension` from withoutKeys if watch to ensure live edit
this.options.watch&&(this.withoutKeys=this.withoutKeys.filter((function(e){return!["path","extension"].includes(e)}))),
// Map data and returns object picked by keys
n=function(e){return e.map((function(e){return u(e,a.withoutKeys)}))},// Apply pick during postprocess
this.postprocess.unshift(n)),
// Apply postprocess fns to data
r=l(this.postprocess);try{for(r.s();!(s=r.n()).done;)o=s.value,t=o(t)}catch(e){r.e(e)}finally{r.f()}if(t){e.next=10;break}throw new Error("".concat(this.path," not found"));case 10:return e.abrupt("return",JSON.parse(JSON.stringify(t)));case 11:case"end":return e.stop()}}),e,this)}))),function(){return e.apply(this,arguments)})}]);var e}();e.exports=d},
/***/1719:
/***/function(e,t){function i(e,t,i,n,r,s,o){try{var a=e[s](o),l=a.value}catch(e){return void i(e)}a.done?t(l):Promise.resolve(l).then(n,r)}e.exports=function(e){return function(){var t=this,n=arguments;return new Promise((function(r,s){var o=e.apply(t,n);function a(e){i(o,r,s,a,l,"next",e)}function l(e){i(o,r,s,a,l,"throw",e)}a(void 0)}))}},e.exports.__esModule=!0,e.exports.default=e.exports},
/***/1720:
/***/function(e,t,i){var n;"undefined"!=typeof self&&self,n=function(){/******/
return function(e){// webpackBootstrap
/******/ // The module cache
/******/var t={};
/******/
/******/ // The require function
/******/function i(n){
/******/
/******/ // Check if module is in cache
/******/if(t[n])
/******/return t[n].exports;
/******/
/******/ // Create a new module (and put it into the cache)
/******/var r=t[n]={
/******/i:n,
/******/l:!1,
/******/exports:{}
/******/};
/******/
/******/ // Execute the module function
/******/
/******/
/******/ // Return the exports of the module
/******/return e[n].call(r.exports,r,r.exports,i),
/******/
/******/ // Flag the module as loaded
/******/r.l=!0,r.exports;
/******/}
/******/
/******/
/******/ // expose the modules object (__webpack_modules__)
/******/
/******/
/******/
/******/ // Load entry module and return exports
/******/return i.m=e,
/******/
/******/ // expose the module cache
/******/i.c=t,
/******/
/******/ // define getter function for harmony exports
/******/i.d=function(e,t,n){
/******/i.o(e,t)||
/******/Object.defineProperty(e,t,{enumerable:!0,get:n})
/******/},
/******/
/******/ // define __esModule on exports
/******/i.r=function(e){
/******/"undefined"!=typeof Symbol&&Symbol.toStringTag&&
/******/Object.defineProperty(e,Symbol.toStringTag,{value:"Module"})
/******/,Object.defineProperty(e,"__esModule",{value:!0})},
/******/
/******/ // create a fake namespace object
/******/ // mode & 1: value is a module id, require it
/******/ // mode & 2: merge all properties of value into the ns
/******/ // mode & 4: return value when already ns object
/******/ // mode & 8|1: behave like require
/******/i.t=function(e,t){
/******/if(
/******/1&t&&(e=i(e)),8&t)return e;
/******/if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;
/******/var n=Object.create(null);
/******/
/******/if(i.r(n),
/******/Object.defineProperty(n,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)i.d(n,r,function(t){return e[t]}.bind(null,r));
/******/return n;
/******/},
/******/
/******/ // getDefaultExport function for compatibility with non-harmony modules
/******/i.n=function(e){
/******/var t=e&&e.__esModule?
/******/function(){return e.default}:
/******/function(){return e};
/******/
/******/return i.d(t,"a",t),t;
/******/},
/******/
/******/ // Object.prototype.hasOwnProperty.call
/******/i.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},
/******/
/******/ // __webpack_public_path__
/******/i.p="",i(i.s=8);
/******/}
/************************************************************************/
/******/([
/* 0 */
/***/function(e,t,i){"use strict";
/* harmony export (binding) */i.d(t,"a",(function(){return r}));
/* unused harmony export CreateJavascriptComparator */
/* unused harmony export CreateAbstractJavascriptComparator */
/* unused harmony export CreateAbstractDateJavascriptComparator */
/* unused harmony export CreateLokiComparator */
/* harmony import */var n=i(2);
/**
 * This file contains LokiOperatorPackages, RangedIndex and Comparator interfaces, as well as
 * global map object instances for registered LokiOperatorPackages, RangedIndex implementations, and Comparator functions
 */
/** Map/Register of named ILokiComparer functions returning -1, 0, 1 for lt/eq/gt assertions for two passed parameters */let r={js:(e,t)=>e===t?0:e<t?-1:1,"abstract-js":(e,t)=>e==t?0:e<t?-1:1,"abstract-date":(e,t)=>{let i=new Date(e).toISOString(),n=new Date(t).toISOString();return i==n?0:i<n?-1:1},loki:(e,t)=>Object(n.b)(e,t)?0:Object(n.c)(e,t,!1)?-1:1};
/** Typescript-friendly factory for strongly typed 'js' comparators */},
/* 1 */
/***/function(e,t,i){"use strict";
/* WEBPACK VAR INJECTION */(function(e){function n(){let t;return function(e){t=e}(void 0!==e&&e||this),t}/* harmony export (binding) */i.d(t,"a",(function(){return r}));
/**
 * @hidden
 */
const r=function(){const e=n(),t=Symbol.for("LOKI");return void 0===e[t]&&(e[t]={}),e[t]}();
/* WEBPACK VAR INJECTION */}).call(this,i(7))
/***/},
/* 2 */
/***/function(e,t,i){"use strict";
/* harmony export (binding) */
/**
 * Helper function for determining 'loki' abstract equality which is a little more abstract than ==
 *     aeqHelper(5, '5') === true
 *     aeqHelper(5.0, '5') === true
 *     aeqHelper(new Date("1/1/2011"), new Date("1/1/2011")) === true
 *     aeqHelper({a:1}, {z:4}) === true (all objects sorted equally)
 *     aeqHelper([1, 2, 3], [1, 3]) === false
 *     aeqHelper([1, 2, 3], [1, 2, 3]) === true
 *     aeqHelper(undefined, null) === true
 * @param {any} prop1
 * @param {any} prop2
 * @returns {boolean}
 * @hidden
 */
function n(e,t){if(e===t)return!0;
// 'falsy' and Boolean handling
if(!e||!t||!0===e||!0===t||e!=e||t!=t){let i,n;
// dates and NaN conditions (typed dates before serialization)
switch(e){case void 0:case null:i=1;break;case!1:i=3;break;case!0:i=4;break;case"":i=5;break;default:i=e==e?9:0}switch(t){case void 0:case null:n=1;break;case!1:n=3;break;case!0:n=4;break;case"":n=5;break;default:n=t==t?9:0}
// one or both is edge case
if(9!==i||9!==n)return i===n}
// Handle 'Number-like' comparisons
let i=Number(e),n=Number(t);
// if one or both are 'number-like'...
return i==i||n==n?i===n:(
// not strict equal nor less than nor gt so must be mixed types, convert to string and use that to compare
i=e.toString(),n=t.toString(),i==n)}
/**
 * Helper function for determining 'less-than' conditions for ops, sorting, and binary indices.
 *     In the future we might want $lt and $gt ops to use their own functionality/helper.
 *     Since binary indices on a property might need to index [12, NaN, new Date(), Infinity], we
 *     need this function (as well as gtHelper) to always ensure one value is LT, GT, or EQ to another.
 * @hidden
 */function r(e,t,i){
// if one of the params is falsy or strictly true or not equal to itself
// 0, 0.0, "", NaN, null, undefined, not defined, false, true
if(!e||!t||!0===e||!0===t||e!=e||t!=t){let n,r;switch(e){case void 0:case null:n=1;break;case!1:n=3;break;case!0:n=4;break;case"":n=5;break;
// if strict equal probably 0 so sort higher, otherwise probably NaN so sort lower than even null
default:n=e==e?9:0}switch(t){case void 0:case null:r=1;break;case!1:r=3;break;case!0:r=4;break;case"":r=5;break;default:r=t==t?9:0}
// one or both is edge case
if(9!==n||9!==r)return n===r?i:n<r}
// if both are numbers (string encoded or not), compare as numbers
let n=Number(e),r=Number(t);return n==n&&r==r?n<r||!(n>r)&&i:n==n&&r!=r||(r!=r||n==n)&&(e<t||!(e>t)&&(e==t?i:(
// not strict equal nor less than nor gt so must be mixed types, convert to string and use that to compare
n=e.toString(),r=t.toString(),n<r||n==r&&i)))}
/**
 * @hidden
 * @param {any} prop1
 * @param {any} prop2
 * @param {boolean} equal
 * @returns {boolean}
 */function s(e,t,i){
// 'falsy' and Boolean handling
if(!e||!t||!0===e||!0===t||e!=e||t!=t){let n,r;switch(e){case void 0:case null:n=1;break;case!1:n=3;break;case!0:n=4;break;case"":n=5;break;
// NaN 0
default:n=e==e?9:0}switch(t){case void 0:case null:r=1;break;case!1:r=3;break;case!0:r=4;break;case"":r=5;break;default:r=t==t?9:0}
// one or both is edge case
if(9!==n||9!==r)return n===r?i:n>r}
// if both are numbers (string encoded or not), compare as numbers
let n=Number(e),r=Number(t);return n==n&&r==r?n>r||!(n<r)&&i:(n!=n||r==r)&&(r==r&&n!=n||e>t||!(e<t)&&(e==t?i:(
// not strict equal nor less than nor gt so must be dates or mixed types
// convert to string and use that to compare
n=e.toString(),r=t.toString(),n>r||n==r&&i)))}
/**
 * @param {any} prop1
 * @param {any} prop2
 * @param {boolean} descending
 * @returns {number}
 * @hidden
 */function o(e,t,i){return n(e,t)?0:r(e,t,!1)?i?1:-1:s(e,t,!1)?i?-1:1:0}
/**
 * Default implementation of LokiOperatorPackage, using fastest javascript comparison operators.
 */i.d(t,"b",(function(){return n})),
/* harmony export (binding) */i.d(t,"c",(function(){return r})),
/* unused harmony export gtHelper */
/* harmony export (binding) */i.d(t,"d",(function(){return o})),
/* unused harmony export LokiOperatorPackage */
/* unused harmony export LokiAbstractOperatorPackage */
/* unused harmony export ComparatorOperatorPackage */
/* harmony export (binding) */i.d(t,"a",(function(){return l}));class a{
// comparison operators
// a is the value in the collection
// b is the query value
$eq(e,t){return e===t}$ne(e,t){return e!==t}$gt(e,t){return e>t}$gte(e,t){return e>=t}$lt(e,t){return e<t}$lte(e,t){return e<=t}$between(e,t){return null!=e&&e>=t[0]&&e<=t[1]}$in(e,t){return-1!==t.indexOf(e)}$nin(e,t){return-1===t.indexOf(e)}$keyin(e,t){return e in t}$nkeyin(e,t){return!(e in t)}$definedin(e,t){return void 0!==t[e]}$undefinedin(e,t){return void 0===t[e]}$regex(e,t){return t.test(e)}$containsNone(e,t){return!this.$containsAny(e,t)}$containsAny(e,t){const i=this.containsCheckFn(e);return null!==i&&(Array.isArray(t)?t.some(i):i(t))}$contains(e,t){const i=this.containsCheckFn(e);return null!==i&&(Array.isArray(t)?t.every(i):i(t))}$type(e,t){let i=typeof e;return"object"===i&&(Array.isArray(e)?i="array":e instanceof Date&&(i="date")),"object"!=typeof t?i===t:this.doQueryOp(i,t)}$finite(e,t){return t===isFinite(e)}$size(e,t){return!!Array.isArray(e)&&("object"!=typeof t?e.length===t:this.doQueryOp(e.length,t))}$len(e,t){return"string"==typeof e&&("object"!=typeof t?e.length===t:this.doQueryOp(e.length,t))}$where(e,t){return!0===t(e)}
// field-level logical operators
// a is the value in the collection
// b is the nested query operation (for '$not')
//   or an array of nested query operations (for '$and' and '$or')
$not(e,t){return!this.doQueryOp(e,t)}$and(e,t){for(let i=0,n=t.length;i<n;i++)if(!this.doQueryOp(e,t[i]))return!1;return!0}$or(e,t){for(let i=0,n=t.length;i<n;i++)if(this.doQueryOp(e,t[i]))return!0;return!1}doQueryOp(e,t){for(let i in t)if(Object.hasOwnProperty.call(t,i))return this[i](e,t[i]);return!1}containsCheckFn(e){return"string"==typeof e||Array.isArray(e)?t=>-1!==e.indexOf(t):"object"==typeof e&&null!==e?t=>Object.hasOwnProperty.call(e,t):null}}
/**
 * LokiOperatorPackage which utilizes abstract 'loki' comparisons for basic relational equality op implementations.
 */
/**
 * Map/Register of named LokiOperatorPackages which implement all unindexed query ops within 'find' query objects
 */
let l={js:new a,loki:new class extends a{constructor(){super()}$eq(e,t){return n(e,t)}$ne(e,t){return!n(e,t)}$gt(e,t){return s(e,t,!1)}$gte(e,t){return s(e,t,!0)}$lt(e,t){return r(e,t,!1)}$lte(e,t){return r(e,t,!0)}$between(e,t){return null!=e&&s(e,t[0],!0)&&r(e,t[1],!0)}}
/**
 * LokiOperatorPackage which utilizes provided comparator for basic relational equality op implementations.
 */};
/***/},
/* 3 */
/***/function(e,t,i){"use strict";
// EXTERNAL MODULE: ./packages/loki/src/event_emitter.ts
var n=i(5);
// CONCATENATED MODULE: ./packages/loki/src/unique_index.ts
class r{
/**
     * Constructs an unique index object.
     * @param {string} propertyField - the property field to index
     */
constructor(e){this._field=e,this._lokiMap={},this._valMap={}}
/**
     * Sets a document's unique index.
     * @param {number} id loki id to associate with value
     * @param {*} value  value to associate with id
     */set(e,t){
// unique index should not include null/undefined values
if(null!=t){if(t in this._lokiMap)throw new Error("Duplicate key for property "+this._field+": "+t);if(e in this._valMap)throw new Error("Duplicate key for property $loki : "+e);this._lokiMap[t]=e,this._valMap[e]=t}}
/**
     * Returns the $loki id of an unique value.
     * @param {*} value the value to retrieve a loki id match for
     */get(e){return this._lokiMap[e]}
/**
     * Updates a document's unique index.
     * @param {number} id (loki) id of document to update the value to
     * @param {*} value value to associate with loki id
     */update(e,t){
// if the value has not changed, do nothing
if(t!==this._valMap[e]){
// the value must have changed, so check if new value already exists
if(t in this._lokiMap)throw new Error("Duplicate key for property "+this._field+": "+t);this.remove(e),this.set(e,t)}}
/**
     * Removes an unique index.
     * @param {number} id (loki) id to remove from index
     */remove(e){if(!(e in this._valMap))throw new Error("Key is not in unique index: "+this._field);let t=this._valMap[e];delete this._lokiMap[t],delete this._valMap[e]}
/**
     * Clears the unique index.
     */clear(){this._lokiMap={},this._valMap={}}}
// CONCATENATED MODULE: ./packages/loki/src/clone.ts
function s(e,t,i){return e instanceof Array?(e.push(i),e[e.length-1]):e instanceof Object?(e[t]=i,e[t]):void 0}function o(e,t){for(let i in e){let n=e[i];n instanceof Date?s(t,i,new Date(n.getTime())):n instanceof Function?s(t,i,n):n instanceof Array?o(n,s(t,i,[])):n instanceof Object?o(n,s(t,i,{})):s(t,i,n)}}
// Deep copy from Simeon Velichkov.
/**
 * @param target
 * @returns {any}
 */function a(e){if(/number|string|boolean/.test(typeof e))return e;if(e instanceof Date)return new Date(e.getTime());const t=e instanceof Array?[]:{};return o(e,t),t}
/**
 * @hidden
 */function l(e,t="parse-stringify"){if(null==e)return null;let i;switch(t){case"parse-stringify":i=JSON.parse(JSON.stringify(e));break;case"deep":i=a(e);break;case"shallow":i=Object.create(e.constructor.prototype),Object.assign(i,e);break;case"shallow-recurse":
// shallow clone top level properties
i=l(e,"shallow");const t=Object.keys(e);
// for each of the top level properties which are object literals, recursively shallow copy
for(let n=0;n<t.length;n++){const r=t[n];"object"==typeof e[r]&&"Object"===e[r].constructor.name&&(i[r]=l(e[r],"shallow-recurse"))}}return i}
// EXTERNAL MODULE: ./packages/loki/src/operator_packages.ts
var h=i(2),c=i(0);
// EXTERNAL MODULE: ./packages/loki/src/comparators.ts
// CONCATENATED MODULE: ./packages/loki/src/result_set.ts
// used to recursively scan hierarchical transform step object for param substitution
function u(e,t,i=0){if(++i>=10)return e;for(const n in e)if("string"==typeof e[n]&&0===e[n].indexOf("[%lktxp]")){const i=e[n].substring(8);void 0!==t[i]&&(e[n]=t[i])}else"object"==typeof e[n]&&(e[n]=u(e[n],t,i));return e}
// top level utility to resolve an entire (single) transform (array of steps) for parameter substitution
/**
 * @hidden
 */
// if an op is registered in this object, our 'calculateRange' can use it with our binary indices.
// if the op is registered to a function, we will run that function/op as a 2nd pass filter on results.
// those 2nd pass filter functions should be similar to LokiOps functions, accepting 2 vals to compare.
const d={$eq:!0,$dteq:!0,$gt:!0,$gte:!0,$lt:!0,$lte:!0,$in:!0,$between:!0};
/**
 * ResultSet class allowing chainable queries.  Intended to be instanced internally.
 *    Collection.find(), Collection.where(), and Collection.chain() instantiate this.
 *
 * @example
 *    mycollection.chain()
 *      .find({ 'doors' : 4 })
 *      .where(function(obj) { return obj.name === 'Toyota' })
 *      .data();
 *
 * @param <TData> - the data type
 * @param <TNested> - nested properties of data type
 */class f{
/**
     * Constructor.
     * @param {Collection} collection - the collection which this ResultSet will query against
     */
constructor(e){this._filteredRows=[],this._filterInitialized=!1,
// Holds the scoring result of the last full-text search.
this._scoring=null,
// retain reference to collection we are querying against
this._collection=e}
/**
     * Reset the ResultSet to its initial state.
     * @returns {ResultSet} Reference to this ResultSet, for future chain operations.
     */reset(){return this._filteredRows.length>0&&(this._filteredRows=[]),this._filterInitialized=!1,this}
/**
     * Override of toJSON to avoid circular references
     */toJSON(){const e=this.copy();return e._collection=null,e}
/**
     * Allows you to limit the number of documents passed to next chain operation.
     * A ResultSet copy() is made to avoid altering original ResultSet.
     * @param {int} qty - The number of documents to return.
     * @returns {ResultSet} Returns a copy of the ResultSet, limited by qty, for subsequent chain ops.
     */limit(e){
// if this has no filters applied, we need to populate filteredRows first
return this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex()),this._filteredRows=this._filteredRows.slice(0,e),this._filterInitialized=!0,this}
/**
     * Used for skipping 'pos' number of documents in the ResultSet.
     * @param {int} pos - Number of documents to skip; all preceding documents are filtered out.
     * @returns {ResultSet} Returns a copy of the ResultSet, containing docs starting at 'pos' for subsequent chain ops.
     */offset(e){
// if this has no filters applied, we need to populate filteredRows first
return this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex()),this._filteredRows=this._filteredRows.slice(e),this._filterInitialized=!0,this}
/**
     * To support reuse of ResultSet in branched query situations.
     * @returns {ResultSet} Returns a copy of the ResultSet (set) but the underlying document references will be the same.
     */copy(){const e=new f(this._collection);return e._filteredRows=this._filteredRows.slice(),e._filterInitialized=this._filterInitialized,e}
/**
     * Executes a named collection transform or raw array of transform steps against the ResultSet.
     * @param {(string|array)} transform - name of collection transform or raw transform array
     * @param {object} [parameters=] - object property hash of parameters, if the transform requires them.
     * @returns {ResultSet} either (this) ResultSet or a clone of of this ResultSet (depending on steps)
     */transform(e,t){
// if transform is name, then do lookup first
"string"==typeof e&&(e=this._collection._transforms[e]),void 0!==t&&(e=function(e,t){if(void 0===t)return e;
// iterate all steps in the transform array
const i=[];for(let n=0;n<e.length;n++){
// clone transform so our scan/replace can operate directly on cloned transform
const r=l(e[n],"shallow-recurse");i.push(u(r,t))}return i}(e,t));let i=this;for(let t=0;t<e.length;t++){const n=e[t];switch(n.type){case"find":i.find(n.value);break;case"where":i.where(n.value);break;case"simplesort":i.simplesort(n.property,n.options);break;case"compoundsort":i.compoundsort(n.value);break;case"sort":i.sort(n.value);break;case"sortByScoring":i.sortByScoring(n.desc);break;case"limit":i=i.limit(n.value);break;// limit makes copy so update reference
case"offset":i=i.offset(n.value);break;// offset makes copy so update reference
case"map":i=i.map(n.value,n.dataOptions);break;case"eqJoin":i=i.eqJoin(n.joinData,n.leftJoinKey,n.rightJoinKey,n.mapFun,n.dataOptions);break;
// following cases break chain by returning array data so make any of these last in transform steps
case"mapReduce":i=i.mapReduce(n.mapFunction,n.reduceFunction);break;
// following cases update documents in current filtered ResultSet (use carefully)
case"update":i.update(n.value);break;case"remove":i.remove()}}return i}
/**
     * User supplied compare function is provided two documents to compare. (chainable)
     * @example
     *    rslt.sort(function(obj1, obj2) {
       *      if (obj1.name === obj2.name) return 0;
       *      if (obj1.name > obj2.name) return 1;
       *      if (obj1.name < obj2.name) return -1;
       *    });
     * @param {function} comparefun - A javascript compare function used for sorting.
     * @returns {ResultSet} Reference to this ResultSet, sorted, for future chain operations.
     */sort(e){
// if this has no filters applied, just we need to populate filteredRows first
this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex());const t=this._collection._data;return this._filteredRows.sort(((i,n)=>e(t[i],t[n]))),this}
/**
     * Simpler, loose evaluation for user to sort based on a property name. (chainable).
     * Sorting based on the same lt/gt helper functions used for binary indices.
     * @param {string} propname - name of property to sort by.
     * @param {boolean|object=} options - boolean for sort descending or options object
     * @param {boolean} [options.desc=false] - whether to sort descending
     * @param {string} [options.sortComparator] override default with name of comparator registered in ComparatorMap
     * @returns {ResultSet} Reference to this ResultSet, sorted, for future chain operations.
     */simplesort(e,t={desc:!1}){if("boolean"==typeof t&&(t={desc:t}),!this._filterInitialized&&this._collection._rangedIndexes.hasOwnProperty(e)){let i=this._collection._rangedIndexes[e].index.rangeRequest(),n=[];
// until we refactor resultset to store $loki ids in filteredrows,
// we need to convert $loki ids to data array positions
for(let e of i)n.push(this._collection.get(e,!0)[1]);return this._filteredRows=t.desc?n.reverse():n,this._filterInitialized=!0,this}
// if this has no filters applied, just we need to populate filteredRows first
this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex());const i=this._collection._data;let n=t.sortComparator?c.a[t.sortComparator]:c.a[this._collection._unindexedSortComparator];return this._filteredRows.sort(((t,r)=>n(i[t][e],i[r][e]))),t.desc&&this._filteredRows.reverse(),this}
/**
     * Allows sorting a ResultSet based on multiple columns.
     * @example
     * // to sort by age and then name (both ascending)
     * rs.compoundsort(['age', 'name']);
     * // to sort by age (ascending) and then by name (descending)
     * rs.compoundsort(['age', ['name', true]);
     * @param {array} properties - array of property names or subarray of [propertyname, isdesc] used evaluate sort order
     * @returns {ResultSet} Reference to this ResultSet, sorted, for future chain operations.
     */compoundsort(e){if(0===e.length)throw new Error("Invalid call to compoundsort, need at least one property");if(1===e.length){const t=e[0];return"string"==typeof t?this.simplesort(t,!1):this.simplesort(t[0],t[1])}
// unify the structure of 'properties' to avoid checking it repeatedly while sorting
for(let t=0,i=e.length;t<i;t++){const i=e[t];"string"==typeof i&&(e[t]=[i,!1])}
// if this has no filters applied, just we need to populate filteredRows first
this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex());const t=this._collection._data;return this._filteredRows.sort(((i,n)=>this._compoundeval(e,t[i],t[n]))),this}
/**
     * Helper function for compoundsort(), performing individual object comparisons
     * @param {Array} properties - array of property names, in order, by which to evaluate sort order
     * @param {object} obj1 - first object to compare
     * @param {object} obj2 - second object to compare
     * @returns {number} 0, -1, or 1 to designate if identical (sortwise) or which should be first
     */_compoundeval(e,t,i){for(let n=0,r=e.length;n<r;n++){const r=e[n],s=r[0],o=Object(h.d)(t[s],i[s],r[1]);if(0!==o)return o}return 0}
/**
     * Sorts the ResultSet based on the last full-text-search scoring.
     * @param {boolean} [ascending=false] - sort ascending
     * @returns {ResultSet}
     */sortByScoring(e=!1){if(null===this._scoring)throw new Error("No scoring available");return e?this._filteredRows.sort(((e,t)=>this._scoring[e].score-this._scoring[t].score)):this._filteredRows.sort(((e,t)=>this._scoring[t].score-this._scoring[e].score)),this}
/**
     * Returns the scoring of the last full-text-search.
     * @returns {ScoreResult[]}
     */getScoring(){if(null===this._scoring)throw new Error("No scoring available");const e=[];for(let t=0;t<this._filteredRows.length;t++)e.push(this._scoring[this._filteredRows[t]]);return e}
/**
     * Oversee the operation of OR'ed query expressions.
     * OR'ed expression evaluation runs each expression individually against the full collection,
     * and finally does a set OR on each expression's results.
     * Each evaluation can utilize a binary index to prevent multiple linear array scans.
     * @param {array} expressionArray - array of expressions
     * @returns {ResultSet} this ResultSet for further chain ops.
     */findOr(e){const t=[],i=[],n=this.count();
// If filter is already initialized, then we query against only those items already in filter.
// This means no index utilization for fields, so hopefully its filtered to a smallish filteredRows.
for(let r=0,s=e.length;r<s;r++){
// we need to branch existing query to run each filter separately and combine results
const s=this.copy().find(e[r])._filteredRows,o=s.length;
// if the find operation did not reduce the initial set, then the initial set is the actual result
if(o===n)return this;
// add any document 'hits'
for(let e=0;e<o;e++){const n=s[e];void 0===i[n]&&(i[n]=!0,t.push(n))}}return this._filteredRows=t,this._filterInitialized=!0,this}$or(e){return this.findOr(e)}
/**
     * Oversee the operation of AND'ed query expressions.
     * AND'ed expression evaluation runs each expression progressively against the full collection,
     * internally utilizing existing chained ResultSet functionality.
     * Only the first filter can utilize a binary index.
     * @param {array} expressionArray - array of expressions
     * @returns {ResultSet} this ResultSet for further chain ops.
     */findAnd(e){
// we have already implementing method chaining in this (our ResultSet class)
// so lets just progressively apply user supplied and filters
for(let t=0,i=e.length;t<i;t++){if(0===this.count())return this;this.find(e[t])}return this}$and(e){return this.findAnd(e)}
/**
     * Used for querying via a mongo-style query object.
     *
     * @param {object} query - A mongo-style query object used for filtering current results.
     * @param {boolean} firstOnly - (Optional) Used by collection.findOne() - flag if this was invoked via findOne()
     * @returns {ResultSet} this ResultSet for further chain ops.
     */find(e,t=!1){if(0===this._collection._data.length)return this._filteredRows=[],this._filterInitialized=!0,this;const i=e||"getAll";let n,r,s;if("object"==typeof i){let e=[];for(let t in i){let s={};s[t]=i[t],e.push(s),void 0!==i[t]&&(n=t,r=i[t])}
// if more than one expression in single query object,
// convert implicit $and to explicit $and
if(e.length>1)return this.find({$and:e},t)}
// apply no filters if they want all
if(!n||"getAll"===i)return t&&(this._filteredRows=this._collection._data.length>0?[0]:[],this._filterInitialized=!0),this;
// injecting $and and $or expression tree evaluation here.
if("$and"===n||"$or"===n)return this[n](r),
// for chained find with firstOnly,
t&&this._filteredRows.length>1&&(this._filteredRows=this._filteredRows.slice(0,1)),this;
// see if query object is in shorthand mode (assuming eq operator)
let o="";if(null===r||"object"!=typeof r||r instanceof Date)o="$eq",s=r;else{if("object"!=typeof r)throw new Error("Do not know what you want to do.");
// for regex ops, precompile
for(let e in r)if(void 0!==r[e]){o=e,s=r[e];break}}"$regex"===o&&(Array.isArray(s)?s=new RegExp(s[0],s[1]):s instanceof RegExp||(s=new RegExp(s)));
// if an index exists for the property being queried against, use it
// for now only enabling where it is the first filter applied and prop is indexed
let a=!1;!this._filterInitialized&&this._collection._rangedIndexes[n]&&d[o]&&(a=!0);
// the comparison function
const l=h.a[this._collection._defaultLokiOperatorPackage],c=this._collection._data;
// "shortcut" for collection data
// Query executed differently depending on :
//    - whether the property being queried has an index defined
//    - if chained, we handle first pass differently for initial filteredRows[] population
// For performance reasons, each case has its own if block to minimize in-loop calculations
let u=[];
// If the filteredRows[] is already initialized, use it
if(this._filterInitialized){let e=this._filteredRows;if("$fts"===n){this._scoring=this._collection._fullTextSearch.search(i.$fts);let t=Object.keys(this._scoring);for(let i=0;i<t.length;i++)-1!==e.indexOf(+t[i])&&u.push(+t[i])}else if(void 0!==this._collection._constraints.unique[n]&&"$eq"===o){
// convert back to position for filtered rows (until we refactor filteredrows to store $loki instead of data pos)
const t=this._collection._constraints.unique[n].get(s);if(void 0!==t){const i=this._collection.get(t,!0)[1];-1!==e.indexOf(i)&&u.push(i)}}else for(let t=0;t<e.length;t++){let i=e[t];
// calling operator as method property of operator package preserves 'this'
l[o](c[i][n],s)&&u.push(i)}// next time work against filteredRows[]
return this._filteredRows=u,this._filterInitialized=!0,this}// next time work against filteredRows[]
if(this._filteredRows=u,this._filterInitialized=!0,"$fts"===n){this._scoring=this._collection._fullTextSearch.search(i.$fts);let e=Object.keys(this._scoring);for(let t=0;t<e.length;t++)u.push(+e[t]);return this}
// Use unique constraint for search.
if(void 0!==this._collection._constraints.unique[n]&&"$eq"===o){
// convert back to position for filtered rows (until we refactor filteredrows to store $loki instead of data pos)
const e=this._collection._constraints.unique[n].get(s);return void 0!==e&&u.push(this._collection.get(e,!0)[1]),this}
// if not searching by index
if(!a){
// determine comparator to use for ops
for(let e=0;e<c.length;e++)
// calling operator as method property of operator package preserves 'this'
if(l[o](c[e][n],s)&&(u.push(e),t))return this;return this}
// If we have a rangedIndex defined, use that and bail
if(this._collection._rangedIndexes[n]){if("$in"===o){let e=this._collection._rangedIndexes[n];
// iterate each $in array value
for(let t of s){
// request matches where val eq current iterated val
let i=e.index.rangeRequest({op:"$eq",val:t});
// for each result in match
for(let e of i)
// convert $loki id to data position and add to result (filteredrows)
u.push(this._collection.get(e,!0)[1])}return this}if("$between"===o){let e=this._collection._rangedIndexes[n].index.rangeRequest({op:o,val:s[0],high:s[1]});
// for now we will have to 'shim' the binary tree index's $loki ids back
// into data array indices, ideally i would like to repurpose filteredrows to use loki ids
for(let t of e)u.push(this._collection.get(t,!0)[1]);return this}let e=this._collection._rangedIndexes[n].index.rangeRequest({op:o,val:s});
// if our op requires 'second pass'
if(!0!==d[o])for(let t of e){let e=this._collection.get(t,!0)[1];d[o](c[e][n],s)&&u.push(e)}else
// for now we will have to 'shim' the binary tree index's $loki ids back
// into data array indices, ideally i would like to repurpose filteredrows to use loki ids
for(let t of e)u.push(this._collection.get(t,!0)[1])}return this}
/**
     * Used for filtering via a javascript filter function.
     * @param {function} fun - A javascript function used for filtering current results by.
     * @returns {ResultSet} this ResultSet for further chain ops.
     */where(e){let t,i=[];if("function"!=typeof e)throw new TypeError("Argument is not a stored view or a function");
// If the filteredRows[] is already initialized, use it
if(t=e,this._filterInitialized){let e=this._filteredRows.length;for(;e--;)!0===t(this._collection._data[this._filteredRows[e]])&&i.push(this._filteredRows[e]);return this._filteredRows=i,this}
// otherwise this is initial chained op, work against data, push into filteredRows[]
{let e=this._collection._data.length;for(;e--;)!0===t(this._collection._data[e])&&i.push(e);return this._filteredRows=i,this._filterInitialized=!0,this}}
/**
     * Returns the number of documents in the ResultSet.
     * @returns {number} The number of documents in the ResultSet.
     */count(){return this._filterInitialized?this._filteredRows.length:this._collection.count()}
/**
     * Terminates the chain and returns array of filtered documents
     * @param {object} options
     * @param {boolean} [options.forceClones] - Allows forcing the return of cloned objects even when
     *        the collection is not configured for clone object.
     * @param {string} [options.forceCloneMethod] - Allows overriding the default or collection specified cloning method.
     *        Possible values 'parse-stringify', 'deep', and 'shallow' and
     * @param {boolean} [options.removeMeta] - will force clones and strip $loki and meta properties from documents
     *
     * @returns {Array} Array of documents in the ResultSet
     */data(e={}){let t,i,n;({forceClones:t=!1,forceCloneMethod:i=this._collection._cloneMethod,removeMeta:n=!1}=e);let r,s,o=[],a=this._collection._data;
// if this has no filters applied, just return collection.data
if(
// if user opts to strip meta, then force clones and use 'shallow' if 'force' options are not present
n&&!t&&(t=!0,i="shallow"),
// if collection has delta changes active, then force clones and use CloneMethod.DEEP for effective change tracking of nested objects
this._collection._disableDeltaChangesApi||(t=!0,i="deep"),!this._filterInitialized){if(0===this._filteredRows.length){
// determine whether we need to clone objects or not
if(this._collection._cloneObjects||t){s=i;for(let e=0;e<a.length;e++)r=this._collection._defineNestedProperties(l(a[e],s)),n&&(delete r.$loki,delete r.meta),o.push(r);return o}
// otherwise we are not cloning so return sliced array with same object references
return a.slice()}
// filteredRows must have been set manually, so use it
this._filterInitialized=!0}const h=this._filteredRows;if(this._collection._cloneObjects||t){s=i;for(let e=0;e<h.length;e++)r=this._collection._defineNestedProperties(l(a[h[e]],s)),n&&(delete r.$loki,delete r.meta),o.push(r)}else for(let e=0;e<h.length;e++)o.push(a[h[e]]);return o}
/**
     * Used to run an update operation on all documents currently in the ResultSet.
     * @param {function} updateFunction - User supplied updateFunction(obj) will be executed for each document object.
     * @returns {ResultSet} this ResultSet for further chain ops.
     */update(e){
// if this has no filters applied, we need to populate filteredRows first
this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex());const t=this._filteredRows.length,i=this._collection._data;
// pass in each document object currently in ResultSet to user supplied updateFunction
for(let n=0;n<t;n++)
// if we have cloning option specified or are doing differential delta changes, clone object first
if(this._collection._cloneObjects||!this._collection._disableDeltaChangesApi){const t=l(i[this._filteredRows[n]],this._collection._cloneMethod);e(t),this._collection.update(t)}else
// no need to clone, so just perform update on collection data object instance
e(i[this._filteredRows[n]]),this._collection.update(i[this._filteredRows[n]]);return this}
/**
     * Removes all document objects which are currently in ResultSet from collection (as well as ResultSet)
     * @returns {ResultSet} this (empty) ResultSet for further chain ops.
     */remove(){
// if this has no filters applied, we need to populate filteredRows first
return this._filterInitialized||0!==this._filteredRows.length||(this._filteredRows=this._collection._prepareFullDocIndex()),this._collection.remove(this.data()),this._filteredRows=[],this}
/**
     * data transformation via user supplied functions
     *
     * @param {function} mapFunction - this function accepts a single document for you to transform and return
     * @param {function} reduceFunction - this function accepts many (array of map outputs) and returns single value
     * @returns {value} The output of your reduceFunction
     */mapReduce(e,t){try{return t(this.data().map(e))}catch(e){throw e}}
/**
     * Left joining two sets of data. Join keys can be defined or calculated properties
     * eqJoin expects the right join key values to be unique.  Otherwise left data will be joined on the last joinData object with that key
     * @param {Array|ResultSet|Collection} joinData - Data array to join to.
     * @param {(string|function)} leftJoinKey - Property name in this result set to join on or a function to produce a value to join on
     * @param {(string|function)} rightJoinKey - Property name in the joinData to join on or a function to produce a value to join on
     * @param {function} [mapFun=] - a function that receives each matching pair and maps them into output objects - function(left,right){return joinedObject}
     * @param {object} [dataOptions=] - optional options to apply to data() calls for left and right sides
     * @param {boolean} dataOptions.removeMeta - allows removing meta before calling mapFun
     * @param {boolean} dataOptions.forceClones - forcing the return of cloned objects to your map object
     * @param {string} dataOptions.forceCloneMethod - allows overriding the default or collection specified cloning method
     * @returns {ResultSet} A ResultSet with data in the format [{left: leftObj, right: rightObj}]
     */eqJoin(e,t,i,n,r){let s,o,a=[],l=[],h="function"==typeof t,c="function"==typeof i,u={},d=this.data(r),_=d.length;
//get the right data
if(e instanceof v)a=e.chain().data(r);else if(e instanceof f)a=e.data(r);else{if(!Array.isArray(e))throw new TypeError("joinData needs to be an array or result set");a=e}s=a.length;
//construct a lookup table
for(let e=0;e<s;e++)o=c?i(a[e]):a[e][i],u[o]=a[e];n||(n=(e,t)=>({left:e,right:t}));
//Run map function over each object in the ResultSet
for(let e=0;e<_;e++)o=h?t(d[e]):d[e][t],l.push(n(d[e],u[o]||{}));
//return a new ResultSet with no filters
return this._collection=new v("joinData"),this._collection.insert(l),this._filteredRows=[],this._filterInitialized=!1,this}
/**
     * Applies a map function into a new collection for further chaining.
     * @param {function} mapFun - javascript map function
     * @param {object} [dataOptions=] - options to data() before input to your map function
     * @param {boolean} dataOptions.removeMeta - allows removing meta before calling mapFun
     * @param {boolean} dataOptions.forceClones - forcing the return of cloned objects to your map object
     * @param {string} dataOptions.forceCloneMethod - Allows overriding the default or collection specified cloning method
     * @return {ResultSet}
     */map(e,t){const i=this.data(t).map(e);
//return return a new ResultSet with no filters
return this._collection=new v("mappedData"),this._collection.insert(i),this._filteredRows=[],this._filterInitialized=!1,this}}
// CONCATENATED MODULE: ./packages/loki/src/dynamic_view.ts
/**
 * DynamicView class is a versatile 'live' view class which can have filters and sorts applied.
 *    Collection.addDynamicView(name) instantiates this DynamicView object and notifies it
 *    whenever documents are add/updated/removed so it can remain up-to-date. (chainable)
 *
 * @example
 * let mydv = mycollection.addDynamicView('test');  // default is non-persistent
 * mydv.applyFind({ 'doors' : 4 });
 * mydv.applyWhere(function(obj) { return obj.name === 'Toyota'; });
 * let results = mydv.data();
 *
 * @extends LokiEventEmitter

 * @see {@link Collection#addDynamicView} to construct instances of DynamicView
 *
 * @param <TData> - the data type
 * @param <TNested> - nested properties of data type
 */class _ extends n.a{
/**
     * Constructor.
     * @param {Collection} collection - a reference to the collection to work agains
     * @param {string} name - the name of this dynamic view
     * @param {object} options - the options
     * @param {boolean} [options.persistent=false] - indicates if view is to main internal results array in 'resultdata'
     * @param {string} [options.sortPriority="passive"] - the sort priority
     * @param {number} [options.minRebuildInterval=1] - minimum rebuild interval (need clarification to docs here)
     */
constructor(e,t,i={}){super(),this._rebuildPending=!1,this._resultData=[],this._resultDirty=!1,this._cachedResultSet=null,
// keep ordered filter pipeline
this._filterPipeline=[],
// sorting member variables
// we only support one active search, applied using applySort() or applySimpleSort()
this._sortFunction=null,this._sortCriteria=null,this._sortCriteriaSimple=null,this._sortByScoring=null,this._sortDirty=!1,({persistent:this._persistent=!1,
// 'passive' will defer the sort phase until they call data(). (most efficient overall)
// 'active' will sort async whenever next idle. (prioritizes read speeds)
sortPriority:this._sortPriority="passive",minRebuildInterval:this._minRebuildInterval=1}=i),this._collection=e,this.name=t,this._resultSet=new f(e),
// for now just have 1 event for when we finally rebuilt lazy view
// once we refactor transactions, i will tie in certain transactional events
this._events={rebuild:[]}}
/**
     * Internally used immediately after deserialization (loading)
     *    This will clear out and reapply filterPipeline ops, recreating the view.
     *    Since where filters do not persist correctly, this method allows
     *    restoring the view to state where user can re-apply those where filters.
     *
     * @param removeWhereFilters
     * @returns {DynamicView} This dynamic view for further chained ops.
     * @fires DynamicView.rebuild
     */_rematerialize({removeWhereFilters:e=!1}){if(this._resultData=[],this._resultDirty=!0,this._resultSet=new f(this._collection),(this._sortFunction||this._sortCriteria||this._sortCriteriaSimple||null!==this._sortByScoring)&&(this._sortDirty=!0),e){
// for each view see if it had any where filters applied... since they don't
// serialize those functions lets remove those invalid filters
let e=this._filterPipeline.length;for(;e--;)"where"===this._filterPipeline[e].type&&(e!==this._filterPipeline.length-1&&(this._filterPipeline[e]=this._filterPipeline[this._filterPipeline.length-1]),this._filterPipeline.length--)}
// back up old filter pipeline, clear filter pipeline, and reapply pipeline ops
const t=this._filterPipeline;this._filterPipeline=[];
// now re-apply 'find' filterPipeline ops
for(let e=0;e<t.length;e++)this.applyFind(t[e].val);
// during creation of unit tests, i will remove this forced refresh and leave lazy
return this.data(),
// emit rebuild event in case user wants to be notified
this.emit("rebuild",this),this}
/**
     * Makes a copy of the internal ResultSet for branched queries.
     * Unlike this dynamic view, the branched ResultSet will not be 'live' updated,
     * so your branched query should be immediately resolved and not held for future evaluation.
     * @param {(string|array=)} transform - Optional name of collection transform, or an array of transform steps
     * @param {object} parameters - optional parameters (if optional transform requires them)
     * @returns {ResultSet} A copy of the internal ResultSet for branched queries.
     */branchResultSet(e,t){const i=this._resultSet.copy();return void 0===e?i:i.transform(e,t)}
/**
     * Override of toJSON to avoid circular references.
     */toJSON(){return{name:this.name,_persistent:this._persistent,_sortPriority:this._sortPriority,_minRebuildInterval:this._minRebuildInterval,_resultSet:this._resultSet,_filterPipeline:this._filterPipeline,_sortCriteria:this._sortCriteria,_sortCriteriaSimple:this._sortCriteriaSimple,_sortByScoring:this._sortByScoring,_sortDirty:this._sortDirty}}static fromJSONObject(e,t){let i=new _(e,t.name);return i._resultDirty=!0,i._filterPipeline=t._filterPipeline,i._resultData=[],i._sortCriteria=t._sortCriteria,i._sortCriteriaSimple=t._sortCriteriaSimple,i._sortByScoring=t._sortByScoring,i._sortDirty=t._sortDirty,i._resultSet._filteredRows=t._resultSet._filteredRows,i._resultSet._filterInitialized=t._resultSet._filterInitialized,i._rematerialize({removeWhereFilters:!0}),i}
/**
     * Used to clear pipeline and reset dynamic view to initial state.
     * Existing options should be retained.
     * @param {boolean} queueSortPhase - (default: false) if true we will async rebuild view (maybe set default to true in future?)
     */removeFilters({queueSortPhase:e=!1}={}){this._rebuildPending=!1,this._resultSet.reset(),this._resultData=[],this._resultDirty=!0,this._cachedResultSet=null,
// keep ordered filter pipeline
this._filterPipeline=[],
// sorting member variables
// we only support one active search, applied using applySort() or applySimpleSort()
this._sortFunction=null,this._sortCriteria=null,this._sortCriteriaSimple=null,this._sortByScoring=null,this._sortDirty=!1,!0===e&&this._queueSortPhase()}
/**
     * Used to apply a sort to the dynamic view
     * @example
     * dv.applySort(function(obj1, obj2) {
       *   if (obj1.name === obj2.name) return 0;
       *   if (obj1.name > obj2.name) return 1;
       *   if (obj1.name < obj2.name) return -1;
       * });
     * @param {function} comparefun - a javascript compare function used for sorting
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */applySort(e){return this._sortFunction=e,this._sortCriteria=null,this._sortCriteriaSimple=null,this._sortByScoring=null,this._queueSortPhase(),this}
/**
     * Used to specify a property used for view translation.
     * @param {string} field - the field name
     * @param {boolean|object=} options - boolean for sort descending or options object
     * @param {boolean} [options.desc=false] - whether we should sort descending.
     * @param {boolean} [options.disableIndexIntersect=false] - whether we should explicity not use array intersection.
     * @param {boolean} [options.forceIndexIntersect=false] - force array intersection (if binary index exists).
     * @param {boolean} [options.useJavascriptSorting=false] - whether results are sorted via basic javascript sort.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     * @example
     * dv.applySimpleSort("name");
     */applySimpleSort(e,t=!1){return this._sortCriteriaSimple={field:e,options:t},this._sortFunction=null,this._sortCriteria=null,this._sortByScoring=null,this._queueSortPhase(),this}
/**
     * Allows sorting a ResultSet based on multiple columns.
     * @param {Array} criteria - array of property names or subarray of [propertyname, isdesc] used evaluate sort order
     * @returns {DynamicView} Reference to this DynamicView, sorted, for future chain operations.
     * @example
     * // to sort by age and then name (both ascending)
     * dv.applySortCriteria(['age', 'name']);
     * // to sort by age (ascending) and then by name (descending)
     * dv.applySortCriteria(['age', ['name', true]]);
     * // to sort by age (descending) and then by name (descending)
     * dv.applySortCriteria([['age', true], ['name', true]]);
     */applySortCriteria(e){return this._sortCriteria=e,this._sortCriteriaSimple=null,this._sortFunction=null,this._sortByScoring=null,this._queueSortPhase(),this}
/**
     * Used to apply a sort by the latest full-text-search scoring.
     * @param {boolean} [ascending=false] - sort ascending
     */applySortByScoring(e=!1){return this._sortFunction=null,this._sortCriteria=null,this._sortCriteriaSimple=null,this._sortByScoring=e,this._queueSortPhase(),this}
/**
     * Returns the scoring of the last full-text-search.
     * @returns {ScoreResult[]}
     */getScoring(){return this._resultSet.getScoring()}
/**
     * Marks the beginning of a transaction.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */startTransaction(){return this._cachedResultSet=this._resultSet.copy(),this}
/**
     * Commits a transaction.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */commit(){return this._cachedResultSet=null,this}
/**
     * Rolls back a transaction.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */rollback(){return this._resultSet=this._cachedResultSet,this._persistent&&(
// for now just rebuild the persistent dynamic view data in this worst case scenario
// (a persistent view utilizing transactions which get rolled back), we already know the filter so not too bad.
this._resultData=this._resultSet.data(),this.emit("rebuild",this)),this}
/**
     * Find the index of a filter in the pipeline, by that filter's ID.
     * @param {(string|number)} uid - The unique ID of the filter.
     * @returns {number}: index of the referenced filter in the pipeline; -1 if not found.
     */_indexOfFilterWithId(e){if("string"==typeof e||"number"==typeof e)for(let t=0,i=this._filterPipeline.length;t<i;t++)if(e===this._filterPipeline[t].uid)return t;return-1}
/**
     * Add the filter object to the end of view's filter pipeline and apply the filter to the ResultSet.
     * @param {object} filter - The filter object. Refer to applyFilter() for extra details.
     */_addFilter(e){this._filterPipeline.push(e),this._resultSet[e.type](e.val)}
/**
     * Reapply all the filters in the current pipeline.
     *
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */reapplyFilters(){this._resultSet.reset(),this._cachedResultSet=null,this._persistent&&(this._resultData=[],this._resultDirty=!0);const e=this._filterPipeline;this._filterPipeline=[];for(let t=0,i=e.length;t<i;t++)this._addFilter(e[t]);return this._sortFunction||this._sortCriteria||this._sortCriteriaSimple||null!==this._sortByScoring?this._queueSortPhase():this._queueRebuildEvent(),this}
/**
     * Adds or updates a filter in the DynamicView filter pipeline
     * @param {object} filter - A filter object to add to the pipeline.
     *    The object is in the format { 'type': filter_type, 'val', filter_param, 'uid', optional_filter_id }
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */applyFilter(e){const t=this._indexOfFilterWithId(e.uid);return t>=0?(this._filterPipeline[t]=e,this.reapplyFilters()):(this._cachedResultSet=null,this._persistent&&(this._resultData=[],this._resultDirty=!0),this._addFilter(e),this._sortFunction||this._sortCriteria||this._sortCriteriaSimple||null!==this._sortByScoring?this._queueSortPhase():this._queueRebuildEvent(),this)}
/**
     * applyFind() - Adds or updates a mongo-style query option in the DynamicView filter pipeline
     *
     * @param {object} query - A mongo-style query object to apply to pipeline
     * @param {(string|number)} uid - Optional: The unique ID of this filter, to reference it in the future.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */applyFind(e,t=""){return this.applyFilter({type:"find",val:e,uid:t}),this}
/**
     * Adds or updates a javascript filter function in the DynamicView filter pipeline
     * @param {function} fun - A javascript filter function to apply to pipeline
     * @param {(string|number)} uid - Optional: The unique ID of this filter, to reference it in the future.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */applyWhere(e,t){return this.applyFilter({type:"where",val:e,uid:t}),this}
/**
     * Remove the specified filter from the DynamicView filter pipeline
     * @param {(string|number)} uid - The unique ID of the filter to be removed.
     * @returns {DynamicView} this DynamicView object, for further chain ops.
     */removeFilter(e){const t=this._indexOfFilterWithId(e);if(t<0)throw new Error("Dynamic view does not contain a filter with ID: "+e);return this._filterPipeline.splice(t,1),this.reapplyFilters(),this}
/**
     * Returns the number of documents representing the current DynamicView contents.
     * @returns {number} The number of documents representing the current DynamicView contents.
     */count(){
// in order to be accurate we will pay the minimum cost (and not alter dv state management)
// recurring ResultSet data resolutions should know internally its already up to date.
// for persistent data this will not update resultdata nor fire rebuild event.
return this._resultDirty&&(this._resultData=this._resultSet.data()),this._resultSet.count()}
/**
     * Resolves and pending filtering and sorting, then returns document array as result.
     * @param {object} options - optional parameters to pass to ResultSet.data() if non-persistent
     * @param {boolean} [options.forceClones] - Allows forcing the return of cloned objects even when
     *        the collection is not configured for clone object.
     * @param {string} [options.forceCloneMethod] - Allows overriding the default or collection specified cloning method.
     *        Possible values include 'parse-stringify', 'jquery-extend-deep', 'shallow', 'shallow-assign'
     * @param {boolean} [options.removeMeta] - will force clones and strip $loki and meta properties from documents
     *
     * @returns {Array} An array of documents representing the current DynamicView contents.
     */data(e={}){
// using final sort phase as 'catch all' for a few use cases which require full rebuild
return(this._sortDirty||this._resultDirty)&&this._performSortPhase({suppressRebuildEvent:!0}),this._persistent?this._resultData:this._resultSet.data(e)}
/**
     * When the view is not sorted we may still wish to be notified of rebuild events.
     * This event will throttle and queue a single rebuild event when batches of updates affect the view.
     */_queueRebuildEvent(){this._rebuildPending||(this._rebuildPending=!0,setTimeout((()=>{this._rebuildPending&&(this._rebuildPending=!1,this.emit("rebuild",this))}),this._minRebuildInterval))}
/**
     * If the view is sorted we will throttle sorting to either :
     * (1) passive - when the user calls data(), or
     * (2) active - once they stop updating and yield js thread control
     */_queueSortPhase(){
// already queued? exit without queuing again
this._sortDirty||(this._sortDirty=!0,"active"===this._sortPriority?
// active sorting... once they are done and yield js thread, run async performSortPhase()
setTimeout((()=>{this._performSortPhase()}),this._minRebuildInterval):
// must be passive sorting... since not calling performSortPhase (until data call), lets use queueRebuildEvent to
// potentially notify user that data has changed.
this._queueRebuildEvent())}
/**
     * Invoked synchronously or asynchronously to perform final sort phase (if needed)
     */_performSortPhase(e={}){
// async call to this may have been pre-empted by synchronous call to data before async could fire
(this._sortDirty||this._resultDirty)&&(this._sortDirty&&(this._sortFunction?this._resultSet.sort(this._sortFunction):this._sortCriteria?this._resultSet.compoundsort(this._sortCriteria):this._sortCriteriaSimple?this._resultSet.simplesort(this._sortCriteriaSimple.field,this._sortCriteriaSimple.options):null!==this._sortByScoring&&this._resultSet.sortByScoring(this._sortByScoring),this._sortDirty=!1),this._persistent&&(
// persistent view, rebuild local resultdata array
this._resultData=this._resultSet.data(),this._resultDirty=!1),e.suppressRebuildEvent||this.emit("rebuild",this))}
/**
     * (Re)evaluating document inclusion.
     * Called by : collection.insert() and collection.update().
     * @param {int} objIndex - index of document to (re)run through filter pipeline.
     * @param {boolean} isNew - true if the document was just added to the collection.
     * @hidden
     */_evaluateDocument(e,t){
// if no filter applied yet, the result 'set' should remain 'everything'
if(!this._resultSet._filterInitialized)return this._persistent&&(this._resultData=this._resultSet.data()),void(
// need to re-sort to sort new document
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent());const i=this._resultSet._filteredRows,n=t?-1:i.indexOf(+e),r=i.length,s=new f(this._collection);let o;s._filteredRows=[e],s._filterInitialized=!0;for(let e=0,t=this._filterPipeline.length;e<t;e++)o=this._filterPipeline[e],s[o.type](o.val);
// not a true position, but -1 if not pass our filter(s), 0 if passed filter(s)
const a=0===s._filteredRows.length?-1:0;
// wasn't in old, shouldn't be now... do nothing
return-1!==n||-1!==a?
// wasn't in ResultSet, should be now... add
-1===n&&-1!==a?(i.push(e),this._persistent&&this._resultData.push(this._collection._data[e]),void(
// need to re-sort to sort new document
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent())):
// was in ResultSet, shouldn't be now... delete
-1!==n&&-1===a?(n<r-1?(i.splice(n,1),this._persistent&&this._resultData.splice(n,1)):(i.length=r-1,this._persistent&&(this._resultData.length=r-1)),void(
// in case changes to data altered a sort column
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent())):
// was in ResultSet, should still be now... (update persistent only?)
void(-1!==n&&-1!==a&&(this._persistent&&(
// in case document changed, replace persistent view data with the latest collection._data document
this._resultData[n]=this._collection._data[e]),
// in case changes to data altered a sort column
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent())):void 0}
/**
     * Internal function called on collection.delete().
     * @hidden
     */_removeDocument(e){
// if no filter applied yet, the result 'set' should remain 'everything'
if(!this._resultSet._filterInitialized)return this._persistent&&(this._resultData=this._resultSet.data()),void(
// in case changes to data altered a sort column
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent());const t=this._resultSet._filteredRows,i=t.indexOf(+e);let n=t.length;-1!==i&&(
// if not last row in resultdata, swap last to hole and truncate last row
i<n-1?(t[i]=t[n-1],t.length=n-1,this._persistent&&(this._resultData[i]=this._resultData[n-1],this._resultData.length=n-1)):(t.length=n-1,this._persistent&&(this._resultData.length=n-1)),
// in case changes to data altered a sort column
this._sortFunction||this._sortCriteria||this._sortCriteriaSimple?this._queueSortPhase():this._queueRebuildEvent()),
// since we are using filteredRows to store data array positions
// if they remove a document (whether in our view or not),
// we need to adjust array positions -1 for all document array references after that position
n=t.length;for(let i=0;i<n;i++)t[i]>e&&t[i]--}
/**
     * Data transformation via user supplied functions
     * @param {function} mapFunction - this function accepts a single document for you to transform and return
     * @param {function} reduceFunction - this function accepts many (array of map outputs) and returns single value
     * @returns The output of your reduceFunction
     */mapReduce(e,t){try{return t(this.data().map(e))}catch(e){throw e}}}
// EXTERNAL MODULE: ./packages/loki/src/ranged_indexes.ts + 1 modules
var p=i(4),g=i(1);
// EXTERNAL MODULE: ./packages/common/plugin.ts
function w(e){return e.reduce(((e,t)=>e+t),0)/e.length}
/**
 * Returns an array with the value of a nested property of an object.
 * Returns an array of values if the nested property is across child arrays.
 * @param {object} obj - the object
 * @param {string[]} path - the path of the nested property
 * @param {any[]} array - the result array
 * @param {number} pathIdx - the current path idx
 * @returns {boolean} true if nested property is across child arrays, otherwise false
 */
function m(e,t,i,n=0){if(void 0===e)return!1;if(n+1===t.length)return i.push(e[t[n]]),!1;const r=e[t[n]];if(Array.isArray(r)){for(let e=0;e<r.length;e++)m(r[e],t,i,n+1);return!0}return m(r,t,i,n+1)}
/**
 * Collection class that handles documents of same type
 * @extends LokiEventEmitter
 * @param <TData> - the data type
 * @param <TNested> - nested properties of data type
 */
// CONCATENATED MODULE: ./packages/loki/src/collection.ts
/* harmony export (binding) */i.d(t,"a",(function(){return v}));class v extends n.a{
/**
     * @param {string} name - collection name
     * @param {(object)} [options={}] - a configuration object
     * @param {string[]} [options.unique=[]] - array of property names to define unique constraints for
     * @param {string[]} [options.exact=[]] - array of property names to define exact constraints for
     * @param {RangedIndexOptions} [options.rangedIndexes] - configuration object for ranged indexes
     * @param {boolean} [options.asyncListeners=false] - whether listeners are invoked asynchronously
     * @param {boolean} [options.disableMeta=false] - set to true to disable meta property on documents
     * @param {boolean} [options.disableChangesApi=true] - set to false to enable Changes API
     * @param {boolean} [options.disableDeltaChangesApi=true] - set to false to enable Delta Changes API (requires Changes API, forces cloning)
     * @param {boolean} [options.clone=false] - specify whether inserts and queries clone to/from user
     * @param {boolean} [options.serializableIndexes=true] - converts date values on binary indexed property values are serializable
     * @param {string} [options.cloneMethod="deep"] - the clone method
     * @param {number} [options.transactional=false] - ?
     * @param {number} [options.ttl=] - age of document (in ms.) before document is considered aged/stale.
     * @param {number} [options.ttlInterval=] - time interval for clearing out 'aged' documents; not set by default
     * @param {string} [options.unindexedSortComparator="js"] "js", "abstract", "abstract-date", "loki" or other registered comparator name
     * @param {string} [options.defaultLokiOperatorPackage="js"] "js", "loki", "comparator" (or user defined) query ops package
     * @param {FullTextSearch.FieldOptions} [options.fullTextSearch=] - the full-text search options
     * @see {@link Loki#addCollection} for normal creation of collections
     */
constructor(e,t={}){
// Consistency checks.
if(super(),
// the data held by the collection
this._data=[],
// index of id
this._idIndex=[],
// user defined indexes
this._rangedIndexes={},
// loki obj map
this._lokimap={},
// default comparator name to use for unindexed sorting
this._unindexedSortComparator="js",
// default LokiOperatorPackage ('default' uses fastest 'javascript' comparisons)
this._defaultLokiOperatorPackage="js",
/**
         * Unique constraints contain duplicate object references, so they are not persisted.
         * We will keep track of properties which have unique constraints applied here, and regenerate on load.
         */
this._constraints={unique:{}},
/**
         * Transforms will be used to store frequently used query chains as a series of steps which itself can be stored along
         * with the database.
         */
this._transforms={},
/**
         * In autosave scenarios we will use collection level dirty flags to determine whether save is needed.
         * currently, if any collection is dirty we will autosave the whole database if autosave is configured.
         * Defaulting to true since this is called from addCollection and adding a collection should trigger save.
         */
this._dirty=!0,
// private holder for cached data
this._cached=null,
/**
         * Name of path of used nested properties.
         */
this._nestedProperties=[],
/**
         * Option to activate a cleaner daemon - clears "aged" documents at set intervals.
         */
this._ttl={age:null,ttlInterval:null,daemon:null},
// currentMaxId - change manually at your own peril!
this._maxId=0,this._dynamicViews=[],
/**
         * Changes are tracked by collection and aggregated by the db.
         */
this._changes=[],
/**
         * stages: a map of uniquely identified 'stages', which hold copies of objects to be
         * manipulated without affecting the data in the original collection
         */
this._stages={},this._commitLog=[],t&&!0===t.disableMeta){if(!1===t.disableChangesApi)throw new Error("disableMeta option cannot be passed as true when disableChangesApi is passed as false");if(!1===t.disableDeltaChangesApi)throw new Error("disableMeta option cannot be passed as true when disableDeltaChangesApi is passed as false");if("number"==typeof t.ttl&&t.ttl>0)throw new Error("disableMeta option cannot be passed as true when ttl is enabled")}
// the name of the collection
// .
if(this.name=e,
/* OPTIONS */
this._unindexedSortComparator=t.unindexedSortComparator||"js",this._defaultLokiOperatorPackage=t.defaultLokiOperatorPackage||"js",
// exact match and unique constraints
void 0!==t.unique&&(Array.isArray(t.unique)||(t.unique=[t.unique]),t.unique.forEach((e=>{this._constraints.unique[e]=new r(e)}))),
// Full text search
void 0!==g.a.FullTextSearch?this._fullTextSearch=void 0!==t.fullTextSearch?new g.a.FullTextSearch(t.fullTextSearch):null:this._fullTextSearch=null,
// .
this._transactional=void 0!==t.transactional&&t.transactional,
// .
this._cloneObjects=void 0!==t.clone&&t.clone,
// .
this._asyncListeners=void 0!==t.asyncListeners&&t.asyncListeners,
// .
this._disableMeta=void 0!==t.disableMeta&&t.disableMeta,
// .
this._disableChangesApi=void 0===t.disableChangesApi||t.disableChangesApi,
// .
this._disableDeltaChangesApi=void 0===t.disableDeltaChangesApi||t.disableDeltaChangesApi,
// .
this._cloneMethod=void 0!==t.cloneMethod?t.cloneMethod:"deep",this._disableChangesApi&&(this._disableDeltaChangesApi=!0),
// .
this._serializableIndexes=void 0===t.serializableIndexes||t.serializableIndexes,null!=t.nestedProperties)for(let e=0;e<t.nestedProperties.length;e++){const i=t.nestedProperties[e];"string"==typeof i?this._nestedProperties.push({name:i,path:i.split(".")}):this._nestedProperties.push(i)}this.setTTL(t.ttl||-1,t.ttlInterval),
// events
this._events={insert:[],update:[],"pre-insert":[],"pre-update":[],close:[],flushbuffer:[],error:[],delete:[],warning:[]},
// initialize the id index
this._ensureId();let i=t.rangedIndexes||{};for(let e in i)
// Todo: any way to type annotate this as typesafe generic?
this.ensureRangedIndex(e,i[e].indexTypeName,i[e].comparatorName);this.setChangesApi(this._disableChangesApi,this._disableDeltaChangesApi),
// for de-serialization purposes
this.flushChanges()}toJSON(){return{name:this.name,unindexedSortComparator:this._unindexedSortComparator,defaultLokiOperatorPackage:this._defaultLokiOperatorPackage,_dynamicViews:this._dynamicViews,uniqueNames:Object.keys(this._constraints.unique),transforms:this._transforms,rangedIndexes:this._rangedIndexes,_data:this._data,idIndex:this._idIndex,maxId:this._maxId,_dirty:this._dirty,_nestedProperties:this._nestedProperties,transactional:this._transactional,asyncListeners:this._asyncListeners,disableMeta:this._disableMeta,disableChangesApi:this._disableChangesApi,disableDeltaChangesApi:this._disableDeltaChangesApi,cloneObjects:this._cloneObjects,cloneMethod:this._cloneMethod,changes:this._changes,_fullTextSearch:this._fullTextSearch}}static fromJSONObject(e,t){
// instantiate collection with options needed by constructor
let i=new v(e.name,{disableChangesApi:e.disableChangesApi,disableDeltaChangesApi:e.disableDeltaChangesApi,unindexedSortComparator:e.unindexedSortComparator,defaultLokiOperatorPackage:e.defaultLokiOperatorPackage});
// load each element individually
if(i._transactional=e.transactional,i._asyncListeners=e.asyncListeners,i._disableMeta=e.disableMeta,i._disableChangesApi=e.disableChangesApi,i._cloneObjects=e.cloneObjects,i._cloneMethod=e.cloneMethod||"deep",i._changes=e.changes,i._nestedProperties=e._nestedProperties,i._rangedIndexes=e.rangedIndexes||{},i._dirty=!(!t||!0!==t.retainDirtyFlags)&&e._dirty,t&&void 0!==t[e.name]){let n=function(e){const i=t[e.name];if(i.proto){const e=i.inflate||((e,t)=>{for(let i in e)t[i]=e[i]});return t=>{const n=new i.proto;return e(t,n),n}}return i.inflate}(e);for(let t=0;t<e._data.length;t++)i._data[t]=i._defineNestedProperties(n(e._data[t])),
// regenerate lokimap
i._lokimap[i._data[t].$loki]=i._data[t]}else for(let t=0;t<e._data.length;t++)i._data[t]=i._defineNestedProperties(e._data[t]),
// regenerate lokimap
i._lokimap[i._data[t].$loki]=i._data[t];i._maxId=void 0===e.maxId?0:e.maxId,i._idIndex=e.idIndex,void 0!==e.transforms&&(i._transforms=e.transforms);
// inflate rangedindexes
for(let t in e.rangedIndexes){
// shortcut reference to serialized meta
let n=e.rangedIndexes[t],r=(0,p.a[n.indexTypeName])(t,c.a[n.comparatorName]);
// lookup index factory function in map based on index type name
// now ask new index instance to inflate from plain object
r.restore(n.index),
// attach class instance to our collection's ranged index's (index) instance property
i._rangedIndexes[t].index=r}
// regenerate unique indexes
if(i._ensureId(),void 0!==e.uniqueNames)for(let t=0;t<e.uniqueNames.length;t++)i.ensureUniqueIndex(e.uniqueNames[t]);
// in case they are loading a database created before we added dynamic views, handle undefined
if(void 0!==e._dynamicViews)
// reinflate DynamicViews and attached ResultSets
for(let t=0;t<e._dynamicViews.length;t++)i._dynamicViews.push(_.fromJSONObject(i,e._dynamicViews[t]));return e._fullTextSearch&&(i._fullTextSearch=g.a.FullTextSearch.fromJSONObject(e._fullTextSearch,t.fullTextSearch)),i}
/**
     * Adds a named collection transform to the collection
     * @param {string} name - name to associate with transform
     * @param {array} transform - an array of transformation 'step' objects to save into the collection
     */addTransform(e,t){if(void 0!==this._transforms[e])throw new Error("a transform by that name already exists");this._transforms[e]=t}
/**
     * Retrieves a named transform from the collection.
     * @param {string} name - name of the transform to lookup.
     */getTransform(e){return this._transforms[e]}
/**
     * Updates a named collection transform to the collection
     * @param {string} name - name to associate with transform
     * @param {object} transform - a transformation object to save into collection
     */setTransform(e,t){this._transforms[e]=t}
/**
     * Removes a named collection transform from the collection
     * @param {string} name - name of collection transform to remove
     */removeTransform(e){delete this._transforms[e]}
/*----------------------------+
     | TTL                        |
     +----------------------------*/setTTL(e,t){e<0?clearInterval(this._ttl.daemon):(this._ttl.age=e,this._ttl.ttlInterval=t,this._ttl.daemon=setInterval((()=>{const e=Date.now();this.chain().where((t=>{const i=t.meta.updated||t.meta.created,n=e-i;return this._ttl.age<n})).remove()}),t))}
/*----------------------------+
     | INDEXING                   |
     +----------------------------*/
/**
     * Create a row filter that covers all documents in the collection.
     */_prepareFullDocIndex(){const e=new Array(this._data.length);for(let t=0;t<e.length;t++)e[t]=t;return e}
/**
     * Ensure rangedIndex of a field.
     * @param field
     * @param indexTypeName
     * @param comparatorName
     */ensureIndex(e,t,i){this.ensureRangedIndex(e,t,i)}
/**
     * Ensure rangedIndex of a field.
     * @param field Property to create an index on (need to look into contraining on keyof T)
     * @param indexTypeName Name of IndexType factory within (global?) hashmap to create IRangedIndex from
     * @param comparatorName Name of Comparator within (global?) hashmap
     */ensureRangedIndex(e,t,i){if(t=t||"avl",i=i||"loki",!p.a[t])throw new Error("ensureRangedIndex: Unknown range index type");if(!c.a[i])throw new Error("ensureRangedIndex: Unknown comparator");let n=p.a[t],r=c.a[i];this._rangedIndexes[e]={index:n(e,r),indexTypeName:t,comparatorName:i};let s=this._rangedIndexes[e].index;for(let t=0;t<this._data.length;t++)s.insert(this._data[t].$loki,this._data[t][e])}ensureUniqueIndex(e){let t=new r(e);
// if index already existed, (re)loading it will likely cause collisions, rebuild always
this._constraints.unique[e]=t;for(let i=0;i<this._data.length;i++)t.set(this._data[i].$loki,this._data[i][e]);return t}
/**
     * Quickly determine number of documents in collection (or query)
     * @param {object} query - (optional) query object to count results of
     * @returns {number} number of documents in the collection
     */count(e){return e?this.chain().find(e)._filteredRows.length:this._data.length}
/**
     * Rebuild idIndex
     */_ensureId(){this._idIndex=[];for(let e=0;e<this._data.length;e++)this._idIndex.push(this._data[e].$loki)}
/**
     * Add a dynamic view to the collection
     * @param {string} name - name of dynamic view to add
     * @param {object} options - (optional) options to configure dynamic view with
     * @param {boolean} [options.persistent=false] - indicates if view is to main internal results array in 'resultdata'
     * @param {string} [options.sortPriority=SortPriority.PASSIVE] - the sort priority
     * @param {number} options.minRebuildInterval - minimum rebuild interval (need clarification to docs here)
     * @returns {DynamicView} reference to the dynamic view added
     **/addDynamicView(e,t){const i=new _(this,e,t);return this._dynamicViews.push(i),i}
/**
     * Remove a dynamic view from the collection
     * @param {string} name - name of dynamic view to remove
     **/removeDynamicView(e){for(let t=0;t<this._dynamicViews.length;t++)this._dynamicViews[t].name===e&&this._dynamicViews.splice(t,1)}
/**
     * Look up dynamic view reference from within the collection
     * @param {string} name - name of dynamic view to retrieve reference of
     * @returns {DynamicView} A reference to the dynamic view with that name
     **/getDynamicView(e){for(let t=0;t<this._dynamicViews.length;t++)if(this._dynamicViews[t].name===e)return this._dynamicViews[t];return null}
/**
     * Applies a 'mongo-like' find query object and passes all results to an update function.
     * @param {object} filterObject - the 'mongo-like' query object
     * @param {function} updateFunction - the update function
     */findAndUpdate(e,t){this.chain().find(e).update(t)}
/**
     * Applies a 'mongo-like' find query object removes all documents which match that filter.
     * @param {object} filterObject - 'mongo-like' query object
     */findAndRemove(e){this.chain().find(e).remove()}insert(e){if(!Array.isArray(e))return this.insertOne(e);
// holder to the clone of the object inserted if collections is set to clone objects
let t,i=[];this.emit("pre-insert",e);for(let n=0;n<e.length;n++){if(t=this.insertOne(e[n],!0),!t)return;i.push(t)}
// at the 'batch' level, if clone option is true then emitted docs are clones
return this.emit("insert",i),
// if clone option is set, clone return values
i=this._cloneObjects?l(i,this._cloneMethod):i,1===i.length?i[0]:i}
/**
     * Adds a single object, ensures it has meta properties, clone it if necessary, etc.
     * @param {object} doc - the document to be inserted
     * @param {boolean} bulkInsert - quiet pre-insert and insert event emits
     * @returns {object} document or 'undefined' if there was a problem inserting it
     */insertOne(e,t=!1){let i,n=null;if("object"!=typeof e?n=new TypeError("Document needs to be an object"):null===e&&(n=new TypeError("Object cannot be null")),null!==n)throw this.emit("error",n),n;
// if configured to clone, do so now... otherwise just use same obj reference
const r=this._defineNestedProperties(this._cloneObjects?l(e,this._cloneMethod):e);if(this._disableMeta||void 0!==r.meta||(r.meta={version:0,revision:0,created:0}),
// both 'pre-insert' and 'insert' events are passed internal data reference even when cloning
// insert needs internal reference because that is where loki itself listens to add meta
t||this.emit("pre-insert",r),this._add(r))
// update meta and store changes if ChangesAPI is enabled
// (moved from "insert" event listener to allow internal reference to be used)
return this._disableChangesApi?this._insertMeta(r):this._insertMetaWithChange(r),
// if cloning is enabled, emit insert event with clone of new object
i=this._cloneObjects?l(r,this._cloneMethod):r,t||this.emit("insert",i),i}
/**
     * Refers nested properties of an object to the root of it.
     * @param {T} data - the object
     * @returns {T & TNested} the object with nested properties
     * @hidden
     */_defineNestedProperties(e){for(let t=0;t<this._nestedProperties.length;t++){const i=this._nestedProperties[t].name,n=this._nestedProperties[t].path;Object.defineProperty(e,i,{get(){
// Get the value of the nested property.
const e=[];return m(this,n,e)?e:e[0]},set(e){
// Set the value of the nested property.
n.slice(0,n.length-1).reduce(((e,t)=>e&&e[t]?e[t]:null),this)[n[n.length-1]]=e},enumerable:!1,configurable:!0})}return e}
/**
     * Empties the collection.
     * @param {boolean} [removeIndices=false] - remove indices
     */clear({removeIndices:e=!1}={}){
// if removing indices entirely
if(this._data=[],this._idIndex=[],this._cached=null,this._maxId=0,this._dynamicViews=[],this._dirty=!0,!0===e)this._rangedIndexes={},this._constraints={unique:{}};else{
// re-instance ranged indexes
for(let e in this._rangedIndexes)this.ensureRangedIndex(e,this._rangedIndexes[e].indexTypeName,this._rangedIndexes[e].comparatorName);
// clear entire unique indices definition
const e=Object.keys(this._constraints.unique);for(let t=0;t<e.length;t++)this._constraints.unique[e[t]].clear()}null!==this._fullTextSearch&&this._fullTextSearch.clear()}
/**
     * Updates an object and notifies collection that the document has changed.
     * @param {object} doc - document to update within the collection
     */update(e){if(Array.isArray(e))for(let t=0;t<e.length;t++)this.update(e[t]);else{
// Verify object is a properly formed document.
if(void 0===e.$loki)throw new Error("Trying to update unsynced document. Please save the document first by using insert() or addMany()");try{this.startTransaction();const t=this.get(e.$loki,!0);if(!t)throw new Error("Trying to update a document not in collection.");
// ref to existing obj
let i=t[0],n=t[1],r=this._defineNestedProperties(this._cloneObjects||!this._disableDeltaChangesApi?l(e,this._cloneMethod):e);// -internal- obj ref
this.emit("pre-update",e),Object.keys(this._constraints.unique).forEach((e=>{this._constraints.unique[e].update(r.$loki,r[e])})),
// operate the update
this._data[n]=r,this._lokimap[e.$loki]=r;
// now that we can efficiently determine the data[] position of newly added document,
// submit it for all registered DynamicViews to evaluate for inclusion/exclusion
for(let e=0;e<this._dynamicViews.length;e++)this._dynamicViews[e]._evaluateDocument(n,!1);
// Notify all ranged indexes of (possible) value update
for(let t in this._rangedIndexes)this._rangedIndexes[t].index.update(e.$loki,e[t]);this._idIndex[n]=r.$loki,
// FullTextSearch.
null!==this._fullTextSearch&&this._fullTextSearch.updateDocument(e,n),this.commit(),this._dirty=!0,// for autosave scenarios
// update meta and store changes if ChangesAPI is enabled
this._disableChangesApi?this._updateMeta(r):this._updateMetaWithChange(r,i);let s=r;
// if cloning is enabled, emit 'update' event and return with clone of new object
this._cloneObjects&&(s=l(r,this._cloneMethod)),this.emit("update",s,i)}catch(e){throw this.rollback(),this.emit("error",e),e;// re-throw error so user does not think it succeeded
}}}
/**
     * Add object to collection
     */_add(e){
// if parameter isn't object exit with throw
if("object"!=typeof e)throw new TypeError("Object being added needs to be an object");
// if object you are adding already has id column it is either already in the collection
// or the object is carrying its own 'id' property.  If it also has a meta property,
// then this is already in collection so throw error, otherwise rename to originalId and continue adding.
if(void 0!==e.$loki)throw new Error("Document is already in collection, please use update()");
/*
         * try adding object to collection
         */try{this.startTransaction(),this._maxId++,isNaN(this._maxId)&&(this._maxId=this._data[this._data.length-1].$loki+1);const t=e;t.$loki=this._maxId,this._disableMeta||(t.meta.version=0);const i=this._constraints.unique;for(const e in i)void 0!==i[e]&&i[e].set(t.$loki,t[e]);
// add new obj id to idIndex
this._idIndex.push(t.$loki),
// update lokimap
this._lokimap[t.$loki]=t,
// add the object
this._data.push(t);const n=this._data.length-1,r=this._dynamicViews.length;
// now that we can efficiently determine the data[] position of newly added document,
// submit it for all registered DynamicViews to evaluate for inclusion/exclusion
for(let e=0;e<r;e++)this._dynamicViews[e]._evaluateDocument(n,!0);
// add id/val kvp to ranged index
for(let i in this._rangedIndexes)
// ensure Dates are converted to unix epoch time if serializableIndexes is true
this._serializableIndexes&&t[i]instanceof Date&&(t[i]=t[i].getTime()),this._rangedIndexes[i].index.insert(e.$loki,e[i]);
// FullTextSearch.
// for autosave scenarios
return null!==this._fullTextSearch&&this._fullTextSearch.addDocument(t,n),this.commit(),this._dirty=!0,this._cloneObjects?l(t,this._cloneMethod):t}catch(e){throw this.rollback(),this.emit("error",e),e;// re-throw error so user does not think it succeeded
}}
/**
     * Applies a filter function and passes all results to an update function.
     * @param {function} filterFunction - the filter function
     * @param {function} updateFunction - the update function
     */updateWhere(e,t){const i=this.where(e);try{for(let e=0;e<i.length;e++)this.update(t(i[e]))}catch(e){throw this.rollback(),e}}
/**
     * Remove all documents matching supplied filter function.
     * @param {function} filterFunction - the filter function
     */removeWhere(e){this.remove(this._data.filter(e))}removeDataOnly(){this.remove(this._data.slice())}
/**
     * Remove a document from the collection
     * @param {number|object} doc - document to remove from collection
     */remove(e){if("number"==typeof e&&(e=this.get(e)),Array.isArray(e)){let t=0;const i=e.length;for(;t<i;t++)this.remove(e[t])}else{if(void 0===e.$loki)throw new Error("Object is not a document stored in the collection");try{this.startTransaction();const t=this.get(e.$loki,!0),i=t[1];
// already converted but let's narrow to make typescript happy
let n="number"==typeof e?this.get(e):e;Object.keys(this._constraints.unique).forEach((e=>{e in n&&this._constraints.unique[e].remove(n.$loki)}));
// now that we can efficiently determine the data[] position of newly added document,
// submit it for all registered DynamicViews to remove
for(let e=0;e<this._dynamicViews.length;e++)this._dynamicViews[e]._removeDocument(i);this._data.splice(i,1),
// remove id from idIndex
this._idIndex.splice(i,1),
// remove from lokimap
delete this._lokimap[e.$loki];
// remove id/val kvp from binary tree index
for(let t in this._rangedIndexes)this._rangedIndexes[t].index.remove(e.$loki);
// FullTextSearch.
null!==this._fullTextSearch&&this._fullTextSearch.removeDocument(e,i),this.commit(),this._dirty=!0,// for autosave scenarios
this._disableChangesApi||this._createChange(this.name,"R",t[0]),this.emit("delete",t[0]),delete e.$loki,delete e.meta}catch(e){throw this.rollback(),this.emit("error",e),e}}}
/*------------+
     | Change API |
     +------------*/
/**
     * Returns all changes.
     * @returns {Collection.Change[]}
     */getChanges(){return this._changes}
/**
     * Enables/disables changes api.
     * @param {boolean} disableChangesApi
     * @param {boolean} disableDeltaChangesApi
     */setChangesApi(e,t=!0){this._disableChangesApi=e,this._disableDeltaChangesApi=!!e||t}
/**
     * Clears all the changes.
     */flushChanges(){this._changes=[]}_getObjectDelta(e,t){const i=null!==t&&"object"==typeof t?Object.keys(t):null;if(i&&i.length&&["string","boolean","number"].indexOf(typeof t)<0){const n={};for(let r=0;r<i.length;r++){const s=i[r];if(t.hasOwnProperty(s))if(e.hasOwnProperty(s)&&void 0===this._constraints.unique[s]&&"$loki"!==s&&"meta"!==s){const i=this._getObjectDelta(e[s],t[s]);void 0!==i&&i!=={}&&(n[s]=i)}else n[s]=t[s]}return 0===Object.keys(n).length?void 0:n}return e===t?void 0:t}
/**
     * Compare changed object (which is a forced clone) with existing object and return the delta
     */_getChangeDelta(e,t){return t?this._getObjectDelta(t,e):JSON.parse(JSON.stringify(e))}
/**
     * Creates a clone of the current status of an object and associates operation and collection name,
     * so the parent db can aggregate and generate a changes object for the entire db
     */_createChange(e,t,i,n){this._changes.push({name:e,operation:t,obj:"U"!==t||this._disableDeltaChangesApi?JSON.parse(JSON.stringify(i)):this._getChangeDelta(i,n)})}_createInsertChange(e){this._createChange(this.name,"I",e)}_createUpdateChange(e,t){this._createChange(this.name,"U",e,t)}_insertMetaWithChange(e){this._insertMeta(e),this._createInsertChange(e)}_updateMetaWithChange(e,t){this._updateMeta(e),this._createUpdateChange(e,t)}_insertMeta(e){this._disableMeta||(e.meta||(e.meta={version:0,revision:0,created:0}),e.meta.created=(new Date).getTime(),e.meta.revision=0)}_updateMeta(e){this._disableMeta||(e.meta.updated=(new Date).getTime(),e.meta.revision+=1)}get(e,t=!1){if(!t){let t=this._lokimap[e];return void 0===t?null:t}const i=this._idIndex;let n=i.length-1,r=0,s=r+n>>1;if(e="number"==typeof e?e:parseInt(e,10),isNaN(e))throw new TypeError("Passed id is not an integer");for(;i[r]<i[n];)s=r+n>>1,i[s]<e?r=s+1:n=s;return n===r&&i[r]===e?t?[this._data[r],r]:this._data[r]:null}
/**
     * Retrieve doc by Unique index
     * @param {string} field - name of uniquely indexed property to use when doing lookup
     * @param {any} value - unique value to search for
     * @returns {object} document matching the value passed
     */by(e,t){
// for least amount of overhead, we will directly
// access index rather than use find codepath
let i=this._constraints.unique[e].get(t);return this._cloneObjects?l(this._lokimap[i],this._cloneMethod):this._lokimap[i]}
/**
     * Find one object by index property, by property equal to value
     * @param {object} query - query object used to perform search with
     * @returns {(object|null)} First matching document, or null if none
     */findOne(e){e=e||{};
// Instantiate ResultSet and exec find op passing firstOnly = true param
const t=this.chain().find(e,!0).data();return Array.isArray(t)&&0===t.length?null:this._cloneObjects?l(t[0],this._cloneMethod):t[0]}
/**
     * Chain method, used for beginning a series of chained find() and/or view() operations
     * on a collection.
     *
     * @param {array} transform - Ordered array of transform step objects similar to chain
     * @param {object} parameters - Object containing properties representing parameters to substitute
     * @returns {ResultSet} (this) ResultSet, or data array if any map or join functions where called
     */chain(e,t){const i=new f(this);return void 0===e?i:i.transform(e,t)}
/**
     * Find method, api is similar to mongodb.
     * for more complex queries use [chain()]{@link Collection#chain} or [where()]{@link Collection#where}.
     * @example {@tutorial Query Examples}
     * @param {object} query - 'mongo-like' query object
     * @returns {array} Array of matching documents
     */find(e){return this.chain().find(e).data()}
/**
     * Find object by unindexed field by property equal to value,
     * simply iterates and returns the first element matching the query
     */findOneUnindexed(e,t){let i,n=this._data.length;for(;n--;)if(this._data[n][e]===t)return i=this._data[n],i;return null}
/**
     * Transaction methods
     */
/**
     * start the transation
     */startTransaction(){if(this._transactional){
// backup any ranged indexes
let e={};for(let t in this._rangedIndexes)e[t].indexTypeName=this._rangedIndexes[t].indexTypeName,e[t].comparatorName=this._rangedIndexes[t].comparatorName,e[t].index=this._rangedIndexes[t].index.backup();this._cached={index:this._idIndex,data:l(this._data,this._cloneMethod),rangedIndexes:e};
// propagate startTransaction to dynamic views
for(let e=0;e<this._dynamicViews.length;e++)this._dynamicViews[e].startTransaction()}}
/**
     * Commit the transaction.
     */commit(){if(this._transactional){this._cached=null;
// propagate commit to dynamic views
for(let e=0;e<this._dynamicViews.length;e++)this._dynamicViews[e].commit()}}
/**
     * Rollback the transaction.
     */rollback(){if(this._transactional&&null!==this._cached){this._idIndex=this._cached.index,this._data=this._cached.data;for(let e=0;e<this._data.length;e++)this._data[e]=this._defineNestedProperties(this._data[e]);
// restore ranged indexes
for(let e in this._cached.rangedIndexes){
// shortcut reference to serialized meta
let t=this._cached.rangedIndexes[e],i=(0,p.a[t.indexTypeName])(e,c.a[t.comparatorName]);
// lookup index factory function in map based on index type name
// now ask new index instance to inflate from plain object
i.restore(t.index),
// attach class instance to our collection's ranged index's (index) instance property
this._rangedIndexes[e].index=i}
// propagate rollback to dynamic views
for(let e=0;e<this._dynamicViews.length;e++)this._dynamicViews[e].rollback()}}
/**
     * Query the collection by supplying a javascript filter function.
     * @example
     * let results = coll.where(function(obj) {
       *   return obj.legs === 8;
       * });
     * @param {function} fun - filter function to run against all collection docs
     * @returns {array} all documents which pass your filter function
     */where(e){return this.chain().where(e).data()}
/**
     * Map Reduce operation
     * @param {function} mapFunction - function to use as map function
     * @param {function} reduceFunction - function to use as reduce function
     * @returns {data} The result of your mapReduce operation
     */mapReduce(e,t){return t(this._data.map(e))}
/**
     * Join two collections on specified properties
     * @param {array} joinData - array of documents to 'join' to this collection
     * @param {string} leftJoinProp - property name in collection
     * @param {string} rightJoinProp - property name in joinData
     * @param {function} mapFun - (Optional) map function to use
     * @param dataOptions - options to data() before input to your map function
     * @param [dataOptions.removeMeta] - allows removing meta before calling mapFun
     * @param [dataOptions.forceClones] - forcing the return of cloned objects to your map object
     * @param [dataOptions.forceCloneMethod] - allows overriding the default or collection specified cloning method
     * @returns {ResultSet} Result of the mapping operation
     */eqJoin(e,t,i,n,r){return new f(this).eqJoin(e,t,i,n,r)}
/* ------ STAGING API -------- */
/**
     * (Staging API) create a stage and/or retrieve it
     */getStage(e){return this._stages[e]||(this._stages[e]={}),this._stages[e]}
/**
     * a collection of objects recording the changes applied through a commmitStage
     */
/**
     * (Staging API) create a copy of an object and insert it into a stage
     */stage(e,t){const i=JSON.parse(JSON.stringify(t));return this.getStage(e)[t.$loki]=i,i}
/**
     * (Staging API) re-attach all objects to the original collection, so indexes and views can be rebuilt
     * then create a message to be inserted in the commitlog
     * @param {string} stageName - name of stage
     * @param {string} message
     */commitStage(e,t){const i=this.getStage(e),n=(new Date).getTime();for(const e in i)this.update(i[e]),this._commitLog.push({timestamp:n,message:t,data:JSON.parse(JSON.stringify(i[e]))});this._stages[e]={}}
/**
     * Returns all values of a field.
     * @param {string} field - the field name
     * @return {any}: the array of values
     */extract(e){const t=[];for(let i=0;i<this._data.length;i++)t.push(this._data[i][e]);return t}
/**
     * Finds the minimum value of a field.
     * @param {string} field - the field name
     * @return {number} the minimum value
     */min(e){return Math.min.apply(null,this.extractNumerical(e))}
/**
     * Finds the maximum value of a field.
     * @param {string} field - the field name
     * @return {number} the maximum value
     */max(e){return Math.max.apply(null,this.extractNumerical(e))}
/**
     * Finds the minimum value and its index of a field.
     * @param {string} field - the field name
     * @return {object} - index and value
     */minRecord(e){const t={index:0,value:0};if(0===this._data.length)return t.index=null,t.value=null,t;t.index=this._data[0].$loki,t.value=parseFloat(this._data[0][e]);for(let i=1;i<this._data.length;i++){const n=parseFloat(this._data[i][e]);t.value>n&&(t.value=n,t.index=this._data[i].$loki)}return t}
/**
     * Finds the maximum value and its index of a field.
     * @param {string} field - the field name
     * @return {object} - index and value
     */maxRecord(e){const t={index:0,value:0};if(0===this._data.length)return t.index=null,t.value=null,t;t.index=this._data[0].$loki,t.value=parseFloat(this._data[0][e]);for(let i=1;i<this._data.length;i++){const n=parseFloat(this._data[i][e]);t.value<n&&(t.value=n,t.index=this._data[i].$loki)}return t}
/**
     * Returns all values of a field as numbers (if possible).
     * @param {string} field - the field name
     * @return {number[]} - the number array
     */extractNumerical(e){return this.extract(e).map(parseFloat).filter(Number).filter((e=>!isNaN(e)))}
/**
     * Calculates the average numerical value of a field
     * @param {string} field - the field name
     * @returns {number} average of property in all docs in the collection
     */avg(e){return w(this.extractNumerical(e))}
/**
     * Calculate the standard deviation of a field.
     * @param {string} field - the field name
     * @return {number} the standard deviation
     */stdDev(e){return function(e){const t=w(e),i=w(e.map((e=>{const i=e-t;return i*i})));return Math.sqrt(i)}(this.extractNumerical(e))}
/**
     * Calculates the mode of a field.
     * @param {string} field - the field name
     * @return {number} the mode
     */mode(e){const t={},i=this.extractNumerical(e);let n=i[0],r=-1/0;for(let e=0;e<i.length;e++){const s=i[e];t[s]?t[s]++:t[s]=1,t[s]>r&&(n=s,r=t[s])}return n}
/**
     * Calculates the median of a field.
     * @param {string} field - the field name
     * @return {number} the median
     */median(e){const t=this.extractNumerical(e);t.sort(((e,t)=>e-t));const i=Math.floor(t.length/2);return t.length%2?t[i]:(t[i-1]+t[i])/2}}
/***/},
/* 4 */
/***/function(e,t,i){"use strict";
// CONCATENATED MODULE: ./packages/loki/src/avl_index.ts
/**
 * LokiDB AVL Balanced Binary Tree Index implementation.
 * To support duplicates, we use siblings (array) in tree nodes.
 * Basic AVL components guided by William Fiset tutorials at :
 * https://github.com/williamfiset/data-structures/blob/master/com/williamfiset/datastructures/balancedtree/AVLTreeRecursive.java
 * https://www.youtube.com/watch?v=g4y2h70D6Nk&list=PLDV1Zeh2NRsD06x59fxczdWLhDDszUHKt
 */class n{
/**
     * Initializes index with property name and a comparer function.
     */
constructor(e,t){this.nodes={},this.apex=null,this.name=e,this.comparator=t}backup(){let e=new n(this.name,this.comparator);return e.nodes=JSON.parse(JSON.stringify(this.nodes)),e.apex=this.apex,e}restore(e){this.name=e.name,this.comparator=e.comparator,this.nodes=JSON.parse(JSON.stringify(e.nodes)),this.apex=e.apex}
/**
     * Used for inserting a new value into the BinaryTreeIndex
     * @param id Unique Id (such as $loki) to associate with value
     * @param val Value to be indexed and inserted into binary tree
     */insert(e,t){if(e<=0)throw new Error("avl index ids are required to be numbers greater than zero");let i=this.nodes[e]={id:e,value:t,parent:null,balance:0,height:0,left:null,right:null,siblings:[]};this.apex?this.insertNode(this.nodes[this.apex],i):this.apex=e}
/**
     * Recursively inserts a treenode and re-balances if needed.
     * @param current
     * @param node
     */insertNode(e,t){switch(this.comparator(t.value,e.value)){case 0:
// eq
e.siblings.push(t.id),t.parent=e.id;break;case 1:
// gt
e.right?(this.insertNode(this.nodes[e.right],t),this.updateBalance(e)):(e.right=t.id,t.parent=e.id,this.updateBalance(e));break;case-1:
// lt
e.left?(this.insertNode(this.nodes[e.left],t),this.updateBalance(e)):(e.left=t.id,t.parent=e.id,this.updateBalance(e));break;default:throw new Error("Invalid comparator result")}if(e.balance<-1){if(null===e.left)throw new Error("insertNode.balance() : left child should not be null");this.nodes[e.left].balance<=0?this.leftLeftCase(e):this.leftRightCase(e)}if(e.balance>1){if(null===e.right)throw new Error("insertNode.balance() : right child should not be null");this.nodes[e.right].balance>=0?this.rightRightCase(e):this.rightLeftCase(e)}return e.height}
/**
     * Updates height and balance (calculation) for tree node
     * @param node
     */updateBalance(e){let t=e.left?this.nodes[e.left].height:-1,i=e.right?this.nodes[e.right].height:-1;
//node.height = 1 + Math.max(hl, hr);
e.height=t>i?1+t:1+i,e.balance=i-t}
/**
     * Balance the 'double left-heavy' condition
     * @param node
     */leftLeftCase(e){return this.rotateRight(e)}
/**
     * Balance the '(parent) left heavy, (child) right heavy' condition
     * @param node
     */leftRightCase(e){if(!e.left)throw new Error("leftRightCase: left child not set");return e.left=this.rotateLeft(this.nodes[e.left]).id,this.rotateRight(e)}
/**
     * Balance the 'double right-heavy' condition
     * @param node
     */rightRightCase(e){return this.rotateLeft(e)}
/**
     * Balance the '(parent) right heavy, (child) left heavy' condition
     * @param node
     */rightLeftCase(e){if(!e.right)throw new Error("rightLeftCase: right child not set");return e.right=this.rotateRight(this.nodes[e.right]).id,this.rotateLeft(e)}
/**
     * Left rotation of node. Swaps right child into current location.
     * @param node
     */rotateLeft(e){if(!e.right)throw new Error("rotateLeft: right child was unavailable.");let t=e.parent?this.nodes[e.parent]:null,i=this.nodes[e.right];
// remap parent child pointer to right
if(
// assume rights (old) left branch as our (new) right branch
e.right=i.left,e.right&&(this.nodes[e.right].parent=e.id),
// right will be new parent to node and assume old node's parent
i.left=e.id,i.parent=e.parent,e.parent=i.id,t)if(t.left===e.id)t.left=i.id;else{if(t.right!==e.id)throw new Error("rotateLeft() : attempt to remap parent back to child failed... not found");t.right=i.id}else{if(this.apex!==e.id)throw new Error("rightRotate expecting parentless node to be apex");this.apex=i.id}
// recalculate height and balance for swapped nodes
return this.updateBalance(e),this.updateBalance(i),i}
/**
     * Right rotation of node. Swaps left child into current location.
     * @param node
     */rotateRight(e){if(!e.left)throw new Error("rotateRight : left child unavailable");let t=e.parent?this.nodes[e.parent]:null,i=this.nodes[e.left];if(
// assume left's (old) right branch as our (new) left branch
e.left=i.right,i.right&&(this.nodes[i.right].parent=e.id),
// 'node' will be right child of left
i.right=e.id,i.parent=e.parent,e.parent=i.id,t)t.left===e.id?t.left=i.id:t.right=i.id;else{if(this.apex!==e.id)throw new Error("rightRotate expecting parentless node to be apex");this.apex=i.id}
// recalculate height and balance for swapped nodes
return this.updateBalance(e),this.updateBalance(i),i}
/**
     * Diagnostic method for examining tree contents and structure
     * @param node
     */getValuesAsTree(e){return null===this.apex?null:{id:(e=e||this.nodes[this.apex]).id,val:e.value,siblings:e.siblings,balance:e.balance,height:e.height,left:e.left?this.getValuesAsTree(this.nodes[e.left]):null,right:e.right?this.getValuesAsTree(this.nodes[e.right]):null}}
/**
     * Updates a value, possibly relocating it, within binary tree
     * @param id Unique Id (such as $loki) to associate with value
     * @param val New value to be indexed within binary tree
     */update(e,t){let i=this.nodes[e];
// if the value did not change, or changed to value considered equal to itself, return.
0!==this.comparator(i.value,t)&&(this.remove(e),this.insert(e,t))}
/**
     * Removes a value from the binary tree index
     * @param id
     */remove(e){if(!this.apex)throw new Error("remove() : attempting remove when tree has no apex");this.removeNode(this.nodes[this.apex],e)}
/**
     * Recursive node removal and rebalancer
     * @param node
     * @param val
     */removeNode(e,t){if(!this.nodes[t])throw new Error("removeNode: attempting to remove a node which is not in hashmap");let i=this.nodes[t].value;switch(this.comparator(i,e.value)){case 0:
// eq - handle siblings if present
if(e.siblings.length>0){
// if node to remove is alpha sibling...
if(e.id===t){
// get first sibling as replacement
let i=e.siblings.shift(),n=this.nodes[i];
// remap all properties but id and value from node onto alphasibling
n.parent=e.parent,this.updateChildLink(e.parent,t,i),e.left&&(this.nodes[e.left].parent=i),e.right&&(this.nodes[e.right].parent=i),n.left=e.left,n.right=e.right,n.siblings=e.siblings,n.height=e.height,n.balance=e.balance,this.apex===t&&(this.apex=i);
// parent all remaining siblings alphaSibling (new parent)
for(let e of n.siblings)this.nodes[e].parent=i;
// delete old node from nodes and return
return void delete this.nodes[t]}
// else we are inner sibling
{let i=e.siblings.indexOf(t);if(-1===i)throw new Error("Unable to remove sibling from parented sibling");return e.siblings.splice(i,1),void delete this.nodes[t]}}
// else we have no siblings, node will be removed
// if node to delete has no children
return e.left||e.right?
// if node to delete has only one child we can do simple copy/replace
e.left&&e.right?
// node to delete has two children, need swap with inorder successor
// use find inorder successor by default
void this.promoteSuccessor(e):(e.left&&(this.promoteChild(e,this.nodes[e.left]),this.apex===t&&(this.apex=e.left)),void(e.right&&(this.promoteChild(e,this.nodes[e.right]),this.apex===t&&(this.apex=e.right)))):(
// if we have a parent, remove us from either left or right child link
this.updateChildLink(e.parent,e.id,null),delete this.nodes[t],void(t===this.apex&&(this.apex=null)));case 1:
// gt - search right branch
if(!e.right)throw new Error("removeNode: Unable to find value in tree");this.removeNode(this.nodes[e.right],t);break;case-1:
// lt - search left branch
if(!e.left)throw new Error("removeNode: Unable to find value in tree");this.removeNode(this.nodes[e.left],t)}if(this.updateBalance(e),e.balance<-1){if(null===e.left)throw new Error("insertNode.balance() : left child should not be null");this.nodes[e.left].balance<=0?this.leftLeftCase(e):this.leftRightCase(e)}if(e.balance>1){if(null===e.right)throw new Error("insertNode.balance() : right child should not be null");this.nodes[e.right].balance>=0?this.rightRightCase(e):this.rightLeftCase(e)}}
/**
     * Utility method for updating a parent's child link when it changes
     * @param parentId
     * @param oldChildId
     * @param newChildId
     */updateChildLink(e,t,i){if(null===e)return;let n=this.nodes[e];n.left===t?n.left=i:n.right===t&&(n.right=i)}
/**
     * When removing a parent with only child, this does simple remap of child to grandParent.
     * @param grandParent New parent of 'child'.
     * @param parent Node being removed.
     * @param child Node to reparent to grandParent.
     */promoteChild(e,t){let i=e.parent;if(i){let n=this.nodes[i];n.left===e.id?n.left=t.id:n.right===e.id&&(n.right=t.id)}
// remap (grand) child's parent pointer to grandparent (new parent) or null if new apex
t.parent=i,
// remove parent from bst hashmap
delete this.nodes[e.id]}
/**
     * Finds a successor to a node and replaces that node with it.
     * @param node
     */promoteSuccessor(e){let t=e.id;
// assume successor/right branch (for now)
if(!e.right||!e.left)throw new Error("promoteSuccessor() : node to replace does not have two children");let i,n,r,s=null;
// if tree is already left heavy,
// let's replace with predecessor (greatest val in left branch)
if(e.balance<0){let t=this.nodes[e.left];s=this.findGreaterLeaf(t),i=s.id,n=s.value,r=s.siblings,s.siblings=[],this.removeNode(t,i)}
// otherwise the tree is either balanced or right heavy,
// so let's use sucessor (least value in right branch)
else{let t=this.nodes[e.right];s=this.findLesserLeaf(t),i=s.id,n=s.value,r=s.siblings,
// dont leave any siblings when we (temporarily) 'remove' or they will assume ownership of old node
s.siblings=[],this.removeNode(t,i)}
// update any parent pointers to node being replaced
if(e.parent){let n=this.nodes[e.parent];n.left===t&&(n.left=i),n.right===t&&(n.right=i)}
// update any child points to node being replaced
e.left&&(this.nodes[e.left].parent=i),e.right&&(this.nodes[e.right].parent=i),
// update (reuse) node instance id and value with that of successor
e.id=i,e.value=n,e.siblings=r,
// update hashmap
this.nodes[i]=e,delete this.nodes[t],
// if old was apex, update apex to point to successor
this.apex===t&&(this.apex=i),this.updateBalance(e)}
/**
     * Utility method for finding In-Order predecessor to the provided node
     * @param node Parent node to find leaf node of greatest 'value'
    */findGreaterLeaf(e){if(!e.right)return e;let t=this.findGreaterLeaf(this.nodes[e.right]);return t||e}
/**
     * Utility method for finding In-Order successor to the provided node
     * @param node Parent Node to find leaf node of least 'value'
     */findLesserLeaf(e){if(!e.left)return e;let t=this.findLesserLeaf(this.nodes[e.left]);return t||e}
/**
     *  Interface method to support ranged queries.  Results sorted by index property.
     * @param range Options for ranged request.
     */rangeRequest(e){if(!this.apex)return[];
// if requesting all id's sorted by their value
if(!e)return this.collateIds(this.nodes[this.apex]);if("$eq"===e.op){let t=this.locate(this.nodes[this.apex],e.val);return null===t?[]:t.siblings.length?[t.id,...t.siblings]:[t.id]}return this.collateRequest(this.nodes[this.apex],e)}
/**
     * Implements ranged request operations.
     * @param node
     * @param range
     */collateRequest(e,t){let i=[];if("$eq"===t.op)
// we use locate instead for $eq range requests
throw new Error("collateRequest does not support $eq range request");let n=this.comparator(e.value,t.val),r=0;if("$between"===t.op){if(null===t.high||void 0===t.high)throw new Error("collateRequest: $between request missing high range value");r=this.comparator(e.value,t.high)}if(e.left)switch(t.op){case"$lt":case"$lte":i=this.collateRequest(this.nodes[e.left],t);break;case"$gt":case"$gte":case"$between":
// only pursue left path if current node greater than (low) range val
1===n&&(i=this.collateRequest(this.nodes[e.left],t))}if(t)switch(t.op){case"$lt":-1===n&&(i.push(e.id),i.push(...e.siblings));break;case"$lte":-1!==n&&0!==n||(i.push(e.id),i.push(...e.siblings));break;case"$gt":1===n&&(i.push(e.id),i.push(...e.siblings));break;case"$gte":1!==n&&0!==n||(i.push(e.id),i.push(...e.siblings));break;case"$between":n>=0&&r<=0&&(i.push(e.id),i.push(...e.siblings))}else i.push(e.id),i.push(...e.siblings);if(e.right)if(t)switch(t.op){case"$lt":case"$lte":
// if the current node is still less than compare value,
// it's possible right child will be too
-1===n&&i.push(...this.collateRequest(this.nodes[e.right],t));break;case"$gt":case"$gte":i.push(...this.collateRequest(this.nodes[e.right],t));break;case"$between":
// only pursue right path if current node less than (high) range val
-1===r&&i.push(...this.collateRequest(this.nodes[e.right],t))}else i.push(...this.collateRequest(this.nodes[e.right],t));return i}
/**
     * Used on a branch node to return an array of id within that branch, sorted by their value
     * @param node
     */collateIds(e){let t=[];
// debug diagnostic
return e?(e.left&&(t=this.collateIds(this.nodes[e.left])),t.push(e.id),t.push(...e.siblings),e.right&&t.push(...this.collateIds(this.nodes[e.right])),t):[]}
/**
     * Traverses tree to a node matching the provided value.
     * @param node
     * @param val
     */
/*
    private locate(node: TreeNode<T>, val: any): TreeNode<T> {
       switch (this.comparator.compare(val, node.value)) {
          case 0: return node;
          case 1:
             if (!node.right) {
                return null;
             }
  
             return this.locate(this.nodes[node.right], val);
          case -1:
             if (!node.left) {
                return null;
             }
  
             return this.locate(this.nodes[node.left], val);
       }
    }
    */
/**
     * Inline/Non-recusive 'single value' ($eq) lookup.
     * Traverses tree to a node matching the provided value.
     * @param node
     * @param val
     */locate(e,t){for(;null!==e;)switch(this.comparator(t,e.value)){case 0:return e;case 1:if(!e.right)return null;e=this.nodes[e.right];break;case-1:if(!e.left)return null;e=this.nodes[e.left]}return null}
/**
     * Index integrity check (IRangedIndex interface function)
     */validateIndex(){
// handle null apex condition and verify empty tree and nodes
if(!this.apex)return 0===Object.keys(this.nodes).length;
// ensure apex has no parent
if(null!==this.nodes[this.apex].parent)return!1;
// high level verification - retrieve all node ids ordered by their values
let e=this.collateIds(this.nodes[this.apex]),t=Object.keys(this.nodes).length;
// verify the inorder traversal returned same number of elements as nodes hashmap
if(e.length!==t)return!1;
// if only one result
if(1===e.length)return null===this.nodes[e[0]].parent&&null===this.nodes[e[0]].left&&null===this.nodes[e[0]].right;
// iterate results and ensure next value is greater or equal to current
for(let t=0;t<e.length-1;t++)if(1===this.comparator(this.nodes[e[t]].value,this.nodes[e[t+1]].value))return!1;return this.validateNode(this.nodes[this.apex])}
/**
     * Recursive Node validation routine
     * @param node
     */validateNode(e){
// should never have parent or child pointers reference self
if(-1!==[e.parent,e.left,e.right].indexOf(e.id))return!1;
// validate height and balance
let t=e.left?this.nodes[e.left].height:-1,i=e.right?this.nodes[e.right].height:-1,n=1+Math.max(t,i);if(e.height!==n)return!1;if(e.balance!==i-t)return!1;
// verify any siblings parent back to self
if(e.siblings.length>0)for(let t of e.siblings)if(this.nodes[t].parent!==e.id)return!1;
// if there is a left child, verify it parents to self and recurse it
if(e.left){if(this.nodes[e.left].parent!==e.id)return!1;if(!this.validateNode(this.nodes[e.left]))return!1}
// if there is a right child, verify it parents to self and recurse it
if(e.right){if(this.nodes[e.right].parent!==e.id)return!1;if(!this.validateNode(this.nodes[e.right]))return!1}return!0}}
// CONCATENATED MODULE: ./packages/loki/src/ranged_indexes.ts
/* harmony export (binding) */i.d(t,"a",(function(){return r}));
/** Map/Register of named factory functions returning IRangedIndex instances */
let r={avl:(e,t)=>new n(e,t)};
/***/},
/* 5 */
/***/function(e,t,i){"use strict";
/* harmony export (binding) */i.d(t,"a",(function(){return n}));
/**
 * LokiEventEmitter is a minimalist version of EventEmitter. It enables any
 * constructor that inherits EventEmitter to emit events and trigger
 * listeners that have been added to the event through the on(event, callback) method
 *
 * @constructor LokiEventEmitter
 */
class n{constructor(){
/**
         * A map, with each property being an array of callbacks.
         */
this._events={},
/**
         * Determines whether or not the callbacks associated with each event should happen in an async fashion or not.
         * Default is false, which means events are synchronous
         */
this._asyncListeners=!1}
/**
     * Adds a listener to the queue of callbacks associated to an event
     * @param {string|string[]} eventName - the name(s) of the event(s) to listen to
     * @param {function} listener - callback function of listener to attach
     * @returns {int} the index of the callback in the array of listeners for a particular event
     */on(e,t){let i;return Array.isArray(e)?(e.forEach((e=>{this.on(e,t)})),t):(i=this._events[e],i||(i=this._events[e]=[]),i.push(t),t)}
/**
     * Emits a particular event
     * with the option of passing optional parameters which are going to be processed by the callback
     * provided signatures match (i.e. if passing emit(event, arg0, arg1) the listener should take two parameters)
     * @param {string} eventName - the name of the event
     * @param {object} data - optional object passed with the event
     */emit(e,...t){e&&this._events[e]&&this._events[e].forEach((e=>{this._asyncListeners?setTimeout((()=>{e(...t)}),1):e(...t)}))}
/**
     * Alias of EventEmitter.on().
     */addListener(e,t){return this.on(e,t)}
/**
     * Removes the listener at position 'index' from the event 'eventName'
     * @param {string|string[]} eventName - the name(s) of the event(s) which the listener is attached to
     * @param {function} listener - the listener callback function to remove from emitter
     */removeListener(e,t){if(Array.isArray(e)&&e.forEach((e=>{this.removeListener(e,t)})),this._events[e]){const i=this._events[e];i.splice(i.indexOf(t),1)}}}
/***/},
/* 6 */
/***/function(e,t,i){"use strict";
/* WEBPACK VAR INJECTION */(function(e){/* harmony export (binding) */i.d(t,"a",(function(){return c}));
/* harmony import */var n=i(5),r=i(3),s=i(1),o=i(0),a=i(4),l=i(2);
/* harmony import */function h(){if(void 0!==e&&(e.android||e.NSObject))return"NATIVESCRIPT";if(void 0!==e&&"[object process]"==={}.toString.call(e.process))return e.window,"NODEJS";if(void 0!==document)return-1===document.URL.indexOf("http://")&&-1===document.URL.indexOf("https://")?"CORDOVA":"BROWSER";if(void 0!==window&&"[object Window]"==={}.toString.call(window))return"BROWSER";throw SyntaxError("Unknown environment...")}class c extends n.a{
/**
     * Constructs the main database class.
     * @param {string} filename - name of the file to be saved to
     * @param {object} [options={}] - options
     * @param {Loki.Environment} [options.env] - the javascript environment
     * @param {Loki.SerializationMethod} [options.serializationMethod=NORMAL] - the serialization method
     * @param {string} [options.destructureDelimiter="$<\n"] - string delimiter used for destructured serialization
     * @param {IComparatorMap} [options.comparatorMap] allows injecting or overriding registered comparators
     * @param {IRangedIndexFactoryMap} [options.rangedIndexFactoryMap] allows injecting or overriding registered ranged index factories
     * @param {ILokiOperatorPackageMap} [options.lokiOperatorPackageMap] allows injecting or overriding registered loki operator packages
     */
constructor(e="loki.db",t={}){
// allow users to inject their own comparators
if(super(),
// persist version of code which created the database to the database.
// could use for upgrade scenarios
this.databaseVersion=1.5,// TODO
this.engineVersion=1.5,
// persistenceMethod could be 'fs', 'localStorage', or 'adapter'
// this is optional option param, otherwise environment detection will be used
// if user passes their own adapter we will force this method to 'adapter' later, so no need to pass method option.
this._persistenceMethod=null,
// retain reference to optional (non-serializable) persistenceAdapter 'instance'
this._persistenceAdapter=null,
// flags used to throttle saves
this._throttledSaves=!0,this._throttledSaveRunning=null,this._throttledSavePending=null,
// autosave support (disabled by default)
this._autosave=!1,this._autosaveInterval=5e3,this._autosaveRunning=!1,this._autosaveHandler=Promise.resolve(),this.filename=e,this._collections=[],({serializationMethod:this._serializationMethod="normal",destructureDelimiter:this._destructureDelimiter="$<\n",env:this._env=h()}=t),this._events={init:[],loaded:[],flushChanges:[],close:[],changes:[],warning:[]},t.comparatorMap)for(let e in t.comparatorMap)o.a[e]=t.comparatorMap[e];
// allow users to register their own rangedIndex factory functions
if(t.rangedIndexFactoryMap)for(let e in t.rangedIndexFactoryMap)a.a[e]=t.rangedIndexFactoryMap[e];
// allow users to register their own LokiOperatorPackages or inject functionality within existing ones
if(t.lokiOperatorPackageMap)for(let e in t.lokiOperatorPackageMap)l.a[e]=t.lokiOperatorPackageMap[e];this.on("init",this.clearChanges)}
/**
     * configures options related to database persistence.
     *
     * @param {Loki.PersistenceOptions} [options={}] - options
     * @param {adapter} [options.adapter=auto] - an instance of a loki persistence adapter
     * @param {boolean} [options.autosave=false] - enables autosave
     * @param {int} [options.autosaveInterval=5000] - time interval (in milliseconds) between saves (if dirty)
     * @param {boolean} [options.autoload=false] - enables autoload on loki instantiation
     * @param {object} options.inflate - options that are passed to loadDatabase if autoload enabled
     * @param {boolean} [options.throttledSaves=true] - if true, it batches multiple calls to to saveDatabase reducing number of
     *   disk I/O operations and guaranteeing proper serialization of the calls. Default value is true.
     * @param {Loki.PersistenceMethod} options.persistenceMethod - a persistence method which should be used (FS_STORAGE, LOCAL_STORAGE...)
     * @returns {Promise} a Promise that resolves after initialization and (if enabled) autoloading the database
     */initializePersistence(e={}){let t=this._autosaveDisable();({autosave:this._autosave=!1,autosaveInterval:this._autosaveInterval=5e3,persistenceMethod:this._persistenceMethod,
// TODO
//inflate: this.options.inflate,
throttledSaves:this._throttledSaves=!0}=e);const i={NODEJS:["fs-storage"],BROWSER:["local-storage","indexed-storage"],CORDOVA:["local-storage","indexed-storage"],MEMORY:["memory-storage"]},n={"fs-storage":s.a.FSStorage,"local-storage":s.a.LocalStorage,"indexed-storage":s.a.IndexedStorage,"memory-storage":s.a.MemoryStorage};
// process the options
if(void 0!==this._persistenceMethod){
// check if the specified persistence method is known
if("function"!=typeof n[this._persistenceMethod])throw Error("Unknown persistence method.");this._persistenceAdapter=new n[this._persistenceMethod]}
// if user passes adapter, set persistence mode to adapter and retain persistence adapter instance
// if by now there is no adapter specified by user nor derived from persistenceMethod: use sensible defaults
if(void 0!==e.adapter&&(this._persistenceMethod="adapter",this._persistenceAdapter=e.adapter),null===this._persistenceAdapter){let e=i[this._env];if(e)for(let t=0;t<e.length;t++)if(n[e[t]]){this._persistenceMethod=e[t],this._persistenceAdapter=new n[e[t]];break}}
// if they want to load database on loki instantiation, now is a good time to load... after adapter set and before
// possible autosave initiation
return e.autoload&&(t=t.then((()=>this._loadDatabase(e.inflate,!0)))),t.then((()=>{this._autosaveEnable()}))}
/**
     * Copies 'this' database into a new Loki instance. Object references are shared to make lightweight.
     * @param {object} options - options
     * @param {boolean} options.removeNonSerializable - nulls properties not safe for serialization.
     */copy(e={}){const t=new c(this.filename,{env:this._env});
// currently inverting and letting loadJSONObject do most of the work
// since our toJSON is not invoked for reference database adapters, this will let us mimic
if(t.loadJSONObject(this,{retainDirtyFlags:!0}),e.removeNonSerializable){t._persistenceAdapter=null;for(let e=0;e<t._collections.length;e++)t._collections[e]._constraints=null,t._collections[e]._ttl=null}return t}
/**
     * Adds a collection to the database.
     * @param {string} name - name of collection to add
     * @param {object} [options={}] - options to configure collection with.
     * @param {array} [options.unique=[]] - array of property names to define unique constraints for
     * @param {array} [options.exact=[]] - array of property names to define exact constraints for
     * @param {array} [options.indices=[]] - array property names to define binary indexes for
     * @param {boolean} [options.asyncListeners=false] - whether listeners are called asynchronously
     * @param {boolean} [options.disableMeta=false] - set to true to disable meta property on documents
     * @param {boolean} [options.disableChangesApi=true] - set to false to enable Changes Api
     * @param {boolean} [options.disableDeltaChangesApi=true] - set to false to enable Delta Changes API (requires Changes API, forces cloning)
     * @param {boolean} [options.clone=false] - specify whether inserts and queries clone to/from user
     * @param {string} [options.cloneMethod=CloneMethod.DEEP] - the clone method
     * @param {number} [options.ttl=] - age of document (in ms.) before document is considered aged/stale
     * @param {number} [options.ttlInterval=] - time interval for clearing out 'aged' documents; not set by default
     * @returns {Collection} a reference to the collection which was just added
     */addCollection(e,t={}){
// Return an existing collection if a collection with the same name already exists.
for(let t=0;t<this._collections.length;t++)if(this._collections[t].name===e)return this._collections[t];
// Create a new collection otherwise.
const i=new r.a(e,t);return this._collections.push(i),i}loadCollection(e){if(!e.name)throw new Error("Collection must have a name property to be loaded");this._collections.push(e)}
/**
     * Retrieves reference to a collection by name.
     * @param {string} name - name of collection to look up
     * @returns {Collection} Reference to collection in database by that name, or null if not found
     */getCollection(e){for(let t=0;t<this._collections.length;t++)if(this._collections[t].name===e)return this._collections[t];
// no such collection
return this.emit("warning","collection "+e+" not found"),null}
/**
     * Renames an existing loki collection
     * @param {string} oldName - name of collection to rename
     * @param {string} newName - new name of collection
     * @returns {Collection} reference to the newly renamed collection
     */renameCollection(e,t){const i=this.getCollection(e);return i&&(i.name=t),i}listCollections(){const e=[];for(let t=0;t<this._collections.length;t++)e.push({name:this._collections[t].name,count:this._collections[t].count()});return e}
/**
     * Removes a collection from the database.
     * @param {string} collectionName - name of collection to remove
     */removeCollection(e){for(let t=0;t<this._collections.length;t++)if(this._collections[t].name===e){const i=new r.a(e,{}),n=this._collections[t];for(const e in n)void 0!==n[e]&&void 0!==i[e]&&(n[e]=i[e]);return void this._collections.splice(t,1)}}
/**
     * Serialize database to a string which can be loaded via {@link Loki#loadJSON}
     *
     * @returns {string} Stringified representation of the loki database.
     */serialize(e={}){switch(void 0===e.serializationMethod&&(e.serializationMethod=this._serializationMethod),e.serializationMethod){case"normal":// use default options
default:return JSON.stringify(this);case"pretty":return JSON.stringify(this,null,2);case"destructured":return this.serializeDestructured()}}
// alias of serialize
toJSON(){return{_env:this._env,_serializationMethod:this._serializationMethod,_autosave:this._autosave,_autosaveInterval:this._autosaveInterval,_collections:this._collections,databaseVersion:this.databaseVersion,engineVersion:this.engineVersion,filename:this.filename,_persistenceAdapter:this._persistenceAdapter,_persistenceMethod:this._persistenceMethod,_throttledSaves:this._throttledSaves}}
/**
     * Database level destructured JSON serialization routine to allow alternate serialization methods.
     * Internally, Loki supports destructuring via loki "serializationMethod' option and
     * the optional LokiPartitioningAdapter class. It is also available if you wish to do
     * your own structured persistence or data exchange.
     *
     * @param {object} options - output format options for use externally to loki
     * @param {boolean} [options.partitioned=false] - whether db and each collection are separate
     * @param {int} options.partition - can be used to only output an individual collection or db (-1)
     * @param {boolean} [options.delimited=true] - whether subitems are delimited or subarrays
     * @param {string} options.delimiter - override default delimiter
     *
     * @returns {string|Array} A custom, restructured aggregation of independent serializations.
     */serializeDestructured(e={}){
// 'partitioned' along with 'partition' of 0 or greater is a request for single collection serialization
if(void 0===e.partitioned&&(e.partitioned=!1),void 0===e.delimited&&(e.delimited=!0),void 0===e.delimiter&&(e.delimiter=this._destructureDelimiter),!0===e.partitioned&&void 0!==e.partition&&e.partition>=0)return this.serializeCollection({delimited:e.delimited,delimiter:e.delimiter,collectionIndex:e.partition});
// not just an individual collection, so we will need to serialize db container via shallow copy
let t=new c(this.filename);t.loadJSONObject(this);for(let e=0;e<t._collections.length;e++)t._collections[e]._data=[];
// if we -only- wanted the db container portion, return it now
if(!0===e.partitioned&&-1===e.partition)
// since we are deconstructing, override serializationMethod to normal for here
return t.serialize({serializationMethod:"normal"});
// at this point we must be deconstructing the entire database
// start by pushing db serialization into first array element
const i=[];i.push(t.serialize({serializationMethod:"normal"})),t=null;
// push collection data into subsequent elements
for(let t=0;t<this._collections.length;t++){let n=this.serializeCollection({delimited:e.delimited,delimiter:e.delimiter,collectionIndex:t});
// NDA : Non-Delimited Array : one iterable concatenated array with empty string collection partitions
if(!1===e.partitioned&&!1===e.delimited){if(!Array.isArray(n))throw new Error("a nondelimited, non partitioned collection serialization did not return an expected array");
// Array.concat would probably duplicate memory overhead for copying strings.
// Instead copy each individually, and clear old value after each copy.
// Hopefully this will allow g.c. to reduce memory pressure, if needed.
for(let e=0;e<n.length;e++)i.push(n[e]),n[e]=null;i.push("")}else i.push(n)}
// Reconstruct / present results according to four combinations : D, DA, NDA, NDAA
return e.partitioned?(
// DA : Delimited Array of strings [0] db [1] collection [n] collection { partitioned: true, delimited: true }
// useful for simple future adaptations of existing persistence adapters to save collections separately
e.delimited,i):
// D : one big Delimited string { partitioned: false, delimited : true }
// This is the method Loki will use internally if 'destructured'.
// Little memory overhead improvements but does not require multiple asynchronous adapter call scheduling
e.delimited?(
// indicate no more collections
i.push(""),i.join(e.delimiter)):(
// indicate no more collections
i.push(""),i)}
/**
     * Collection level utility method to serialize a collection in a 'destructured' format
     *
     * @param {object} options - used to determine output of method
     * @param {int} options.delimited - whether to return single delimited string or an array
     * @param {string} options.delimiter - (optional) if delimited, this is delimiter to use
     * @param {int} options.collectionIndex -  specify which collection to serialize data for
     *
     * @returns {string|array} A custom, restructured aggregation of independent serializations for a single collection.
     */serializeCollection(e={}){if(void 0===e.delimited&&(e.delimited=!0),void 0===e.collectionIndex)throw new Error("serializeCollection called without 'collectionIndex' option");const t=this._collections[e.collectionIndex].count();let i=[];for(let n=0;n<t;n++)i.push(JSON.stringify(this._collections[e.collectionIndex]._data[n]));
// D and DA
return e.delimited?(
// indicate no more documents in collection (via empty delimited string)
i.push(""),i.join(e.delimiter)):i}
/**
     * Database level destructured JSON deserialization routine to minimize memory overhead.
     * Internally, Loki supports destructuring via loki "serializationMethod' option and
     * the optional LokiPartitioningAdapter class. It is also available if you wish to do
     * your own structured persistence or data exchange.
     *
     * @param {string|array} destructuredSource - destructured json or array to deserialize from
     * @param {object} options - source format options
     * @param {boolean} [options.partitioned=false] - whether db and each collection are separate
     * @param {int} options.partition - can be used to deserialize only a single partition
     * @param {boolean} [options.delimited=true] - whether subitems are delimited or subarrays
     * @param {string} options.delimiter - override default delimiter
     *
     * @returns {object|array} An object representation of the deserialized database, not yet applied to 'this' db or document array
     */deserializeDestructured(e,t={}){
// Partitioned
// DA : Delimited Array of strings [0] db [1] collection [n] collection { partitioned: true, delimited: true }
// NDAA : Non-Delimited Array with subArrays. db at [0] and collection subarrays at [n] { partitioned: true, delimited : false }
// -or- single partition
if(void 0===t.partitioned&&(t.partitioned=!1),void 0===t.delimited&&(t.delimited=!0),void 0===t.delimiter&&(t.delimiter=this._destructureDelimiter),t.partitioned){
// handle single partition
if(void 0!==t.partition)
// db only
return-1===t.partition?JSON.parse(e[0]):this.deserializeCollection(e[t.partition+1],t);
// single collection, return doc array
// Otherwise we are restoring an entire partitioned db
const i=JSON.parse(e[0]),n=i._collections.length;for(let r=0;r<n;r++)
// attach each collection docarray to container collection data, add 1 to collection array index since db is at 0
i._collections[r]._data=this.deserializeCollection(e[r+1],t);return i}
// Non-Partitioned
// D : one big Delimited string { partitioned: false, delimited : true }
// NDA : Non-Delimited Array : one iterable array with empty string collection partitions { partitioned: false, delimited: false }
let i=[];
// D
if(t.delimited){// lower memory pressure
if(i=e.split(t.delimiter),e=null,0===i.length)return null}else i=e;
// first line is database and collection shells
const n=JSON.parse(i[0]),r=n._collections.length;i[0]=null;let s=0,o=1,a=!1;for(;!a;)
// empty string indicates either end of collection or end of file
""===i[o]?
// if no more collections to load into, we are done
++s>r&&(a=!0):n._collections[s]._data.push(JSON.parse(i[o])),
// lower memory pressure and advance iterator
i[o++]=null;return n}
/**
     * Collection level utility function to deserializes a destructured collection.
     *
     * @param {string|string[]} destructuredSource - destructured representation of collection to inflate
     * @param {object} options - used to describe format of destructuredSource input
     * @param {int} [options.delimited=false] - whether source is delimited string or an array
     * @param {string} options.delimiter - if delimited, this is delimiter to use (if other than default)
     *
     * @returns {Array} an array of documents to attach to collection.data.
     */deserializeCollection(e,t={}){void 0===t.partitioned&&(t.partitioned=!1),void 0===t.delimited&&(t.delimited=!0),void 0===t.delimiter&&(t.delimiter=this._destructureDelimiter);let i=[];t.delimited?(i=e.split(t.delimiter),i.pop()):i=e;for(let e=0;e<i.length;e++)i[e]=JSON.parse(i[e]);return i}
/**
     * Inflates a loki database from a serialized JSON string
     *
     * @param {string} serializedDb - a serialized loki database string
     * @param {object} options - apply or override collection level settings
     * @param {boolean} options.retainDirtyFlags - whether collection dirty flags will be preserved
     */loadJSON(e,t){let i;if(0===e.length)i={};else
// using option defined in instantiated db not what was in serialized db
switch(this._serializationMethod){case"normal":case"pretty":default:i=JSON.parse(e);break;case"destructured":i=this.deserializeDestructured(e)}this.loadJSONObject(i,t)}loadJSONObject(e,t={}){const i=e._collections?e._collections.length:0;this.filename=e.filename,this._collections=[];for(let n=0;n<i;++n)this._collections.push(r.a.fromJSONObject(e._collections[n],t))}
/**
     * Emits the close event. In autosave scenarios, if the database is dirty, this will save and disable timer.
     * Does not actually destroy the db.
     *
     * @returns {Promise} a Promise that resolves after closing the database succeeded
     */close(){
// for autosave scenarios, we will let close perform final save (if dirty)
// For web use, you might call from window.onbeforeunload to shutdown database, saving pending changes
return this._autosave?this._autosaveDisable().then((()=>this._autosaveDirty()?this.saveDatabase():Promise.resolve())):Promise.resolve().then((()=>{this.emit("close")}))}
/**-------------------------+
     | Changes API               |
     +--------------------------*/
/**
     * The Changes API enables the tracking the changes occurred in the collections since the beginning of the session,
     * so it's possible to create a differential dataset for synchronization purposes (possibly to a remote db)
     */
/**
     * (Changes API) : takes all the changes stored in each
     * collection and creates a single array for the entire database. If an array of names
     * of collections is passed then only the included collections will be tracked.
     *
     * @param {Array} [arrayOfCollectionNames=] - array of collection names. No arg means all collections are processed.
     * @returns {Array} array of changes
     * @see private method _createChange() in Collection
     */generateChangesNotification(e){let t=[];const i=e||this._collections.map((e=>e.name));return this._collections.forEach((e=>{-1!==i.indexOf(e.name)&&(t=t.concat(e.getChanges()))})),t}
/**
     * (Changes API) - stringify changes for network transmission
     * @returns {string} string representation of the changes
     */serializeChanges(e){return JSON.stringify(this.generateChangesNotification(e))}
/**
     * (Changes API) : clears all the changes in all collections.
     */clearChanges(){this._collections.forEach((e=>{e.flushChanges&&e.flushChanges()}))}
/**
     * Wait for throttledSaves to complete and invoke your callback when drained or duration is met.
     *
     * @param {object} options - configuration options
     * @param {boolean} [options.recursiveWait=true] - if after queue is drained, another save was kicked off, wait for it
     * @param {boolean} [options.recursiveWaitLimit=false] - limit our recursive waiting to a duration
     * @param {number} [options.recursiveWaitLimitDuration=2000] - cutoff in ms to stop recursively re-draining
     * @param {Date} [options.started=now()] - the start time of the recursive wait duration
     * @returns {Promise} a Promise that resolves when save queue is drained, it is passed a sucess parameter value
     */throttledSaveDrain(e={}){const t=(new Date).getTime();return this._throttledSaves?(void 0===e.recursiveWait&&(e.recursiveWait=!0),void 0===e.recursiveWaitLimit&&(e.recursiveWaitLimit=!1),void 0===e.recursiveWaitLimitDuration&&(e.recursiveWaitLimitDuration=2e3),void 0===e.started&&(e.started=new Date),
// if save is pending
this._throttledSaves&&null!==this._throttledSaveRunning?
// if we want to wait until we are in a state where there are no pending saves at all
e.recursiveWait?Promise.resolve(Promise.all([this._throttledSaveRunning,this._throttledSavePending])).then((()=>null!==this._throttledSaveRunning||null!==this._throttledSavePending?e.recursiveWaitLimit&&t-e.started.getTime()>e.recursiveWaitLimitDuration?Promise.reject({}):this.throttledSaveDrain(e):Promise.resolve())):Promise.resolve(this._throttledSaveRunning):Promise.resolve()):Promise.resolve()}
/**
     * Internal load logic, decoupled from throttling/contention logic
     *
     * @param {object} options - an object containing inflation options for each collection
     * @param {boolean} ignore_not_found - does not raise an error if database is not found
     * @returns {Promise} a Promise that resolves after the database is loaded
     */_loadDatabase(e={},t=!1){
// the persistenceAdapter should be present if all is ok, but check to be sure.
return null===this._persistenceAdapter?Promise.reject(new Error("persistenceAdapter not configured")):Promise.resolve(this._persistenceAdapter.loadDatabase(this.filename)).then((t=>{if("string"==typeof t)this.loadJSON(t,e),this.emit("load",this);else{if("object"!=typeof t||null===t||t instanceof Error)throw t;this.loadJSONObject(t,e),this.emit("load",this)}})).catch((e=>{if(e instanceof Error)throw e;if(null!=e)throw new TypeError("The persistence adapter did not load a serialized DB string or object.");if(!t)throw new Error("Database not found.")}))}
/**
     * Handles manually loading from an adapter storage (such as fs-storage)
     *    This method utilizes loki configuration options (if provided) to determine which
     *    persistence method to use, or environment detection (if configuration was not provided).
     *    To avoid contention with any throttledSaves, we will drain the save queue first.
     *
     * If you are configured with autosave, you do not need to call this method yourself.
     *
     * @param {object} [options={}] - if throttling saves and loads, this controls how we drain save queue before loading
     * @param {boolean} [options.recursiveWait=true] wait recursively until no saves are queued
     * @param {boolean} [options.recursiveWaitLimit=false] limit our recursive waiting to a duration
     * @param {number} [options.recursiveWaitLimitDelay=2000] cutoff in ms to stop recursively re-draining
     * @param {Date} [options.started=now()] - the start time of the recursive wait duration
     * @returns {Promise} a Promise that resolves after the database is loaded
     */loadDatabase(e={}){
// if throttling disabled, just call internal
return this._throttledSaves?this.throttledSaveDrain(e).then((()=>(
// pause/throttle saving until loading is done
this._throttledSaveRunning=this._loadDatabase(e).then((()=>{
// now that we are finished loading, if no saves were throttled, disable flag
this._throttledSaveRunning=null})),this._throttledSaveRunning)),(()=>{throw new Error("Unable to pause save throttling long enough to read database")})):this._loadDatabase(e);
// try to drain any pending saves in the queue to lock it for loading
}_saveDatabase(){
// the persistenceAdapter should be present if all is ok, but check to be sure.
return null===this._persistenceAdapter?Promise.reject(new Error("persistenceAdapter not configured")):
// check if the adapter is requesting (and supports) a 'reference' mode export
"reference"===this._persistenceAdapter.mode&&"function"==typeof this._persistenceAdapter.exportDatabase?Promise.resolve(this._persistenceAdapter.exportDatabase(this.filename,this.copy({removeNonSerializable:!0}))).then((()=>{this._autosaveClearFlags(),this.emit("save")})):(
// otherwise just pass the serialized database to adapter
// persistenceAdapter might be asynchronous, so we must clear `dirty` immediately
// or autosave won't work if an update occurs between here and the callback
this._autosaveClearFlags(),Promise.resolve(this._persistenceAdapter.saveDatabase(this.filename,this.serialize())).then((()=>{this.emit("save")})))}
/**
     * Handles manually saving to an adapter storage (such as fs-storage)
     *    This method utilizes loki configuration options (if provided) to determine which
     *    persistence method to use, or environment detection (if configuration was not provided).
     *
     * If you are configured with autosave, you do not need to call this method yourself.
     *
     * @returns {Promise} a Promise that resolves after the database is persisted
     */saveDatabase(){return this._throttledSaves?(
// if the db save is currently running, a new promise for a next db save is created
// all calls to save db will get this new promise which will be processed right after
// the current db save is finished
null!==this._throttledSaveRunning&&null===this._throttledSavePending&&(this._throttledSavePending=Promise.resolve(this._throttledSaveRunning).then((()=>(this._throttledSaveRunning=null,this._throttledSavePending=null,this.saveDatabase())))),null!==this._throttledSavePending?this._throttledSavePending:(this._throttledSaveRunning=this._saveDatabase().then((()=>{this._throttledSaveRunning=null})),this._throttledSaveRunning)):this._saveDatabase()}
/**
     * Handles deleting a database from the underlying storage adapter
     *
     * @returns {Promise} a Promise that resolves after the database is deleted
     */deleteDatabase(){
// the persistenceAdapter should be present if all is ok, but check to be sure.
return null===this._persistenceAdapter?Promise.reject(new Error("persistenceAdapter not configured")):Promise.resolve(this._persistenceAdapter.deleteDatabase(this.filename))}
/****************
     * Autosave API
     ****************/
/**
     * Check whether any collections are "dirty" meaning we need to save the (entire) database
     * @returns {boolean} - true if database has changed since last autosave, otherwise false
     */_autosaveDirty(){for(let e=0;e<this._collections.length;e++)if(this._collections[e]._dirty)return!0;return!1}
/**
     * Resets dirty flags on all collections.
     */_autosaveClearFlags(){for(let e=0;e<this._collections.length;e++)this._collections[e]._dirty=!1}
/**
     * Starts periodically saves to the underlying storage adapter.
     */_autosaveEnable(){if(!this._autosave||this._autosaveRunning)return;this._autosaveRunning=!0;const e=setInterval((()=>{this._autosaveRunning?this._autosaveDirty()&&(this._autosaveHandler=this._autosaveHandler.then((()=>this.saveDatabase()))):clearInterval(e)}),this._autosaveInterval)}
/**
     * Stops the autosave interval timer.
     */_autosaveDisable(){return this._autosaveRunning=!1,this._autosaveHandler}}
/* WEBPACK VAR INJECTION */}).call(this,i(7))
/***/},
/* 7 */
/***/function(e,t){var i;
// This works in non-strict mode
i=function(){return this}();try{
// This works if eval is allowed (see CSP)
i=i||Function("return this")()||(0,eval)("this")}catch(e){
// This works if the window reference is available
"object"==typeof window&&(i=window)}
// g can still be undefined, but nothing to do about it...
// We return undefined, instead of nothing here, so it's
// easier to handle this case. if(!global) { ...}
e.exports=i},
/* 8 */
/***/function(e,t,i){"use strict";i.r(t);
/* harmony import */var n=i(6);
/* harmony reexport (safe) */i.d(t,"Loki",(function(){return n.a}));
/* harmony import */var r=i(3);
/* harmony reexport (safe) */i.d(t,"Collection",(function(){return r.a})),n.a.Collection=r.a,
/* harmony default export */t.default=n.a}
/******/])},e.exports=n()},
/***/1721:
/***/function(e,t,i){var n;"undefined"!=typeof self&&self,n=function(){/******/
return function(e){// webpackBootstrap
/******/ // The module cache
/******/var t={};
/******/
/******/ // The require function
/******/function i(n){
/******/
/******/ // Check if module is in cache
/******/if(t[n])
/******/return t[n].exports;
/******/
/******/ // Create a new module (and put it into the cache)
/******/var r=t[n]={
/******/i:n,
/******/l:!1,
/******/exports:{}
/******/};
/******/
/******/ // Execute the module function
/******/
/******/
/******/ // Return the exports of the module
/******/return e[n].call(r.exports,r,r.exports,i),
/******/
/******/ // Flag the module as loaded
/******/r.l=!0,r.exports;
/******/}
/******/
/******/
/******/ // expose the modules object (__webpack_modules__)
/******/
/******/
/******/
/******/ // Load entry module and return exports
/******/return i.m=e,
/******/
/******/ // expose the module cache
/******/i.c=t,
/******/
/******/ // define getter function for harmony exports
/******/i.d=function(e,t,n){
/******/i.o(e,t)||
/******/Object.defineProperty(e,t,{enumerable:!0,get:n})
/******/},
/******/
/******/ // define __esModule on exports
/******/i.r=function(e){
/******/"undefined"!=typeof Symbol&&Symbol.toStringTag&&
/******/Object.defineProperty(e,Symbol.toStringTag,{value:"Module"})
/******/,Object.defineProperty(e,"__esModule",{value:!0})},
/******/
/******/ // create a fake namespace object
/******/ // mode & 1: value is a module id, require it
/******/ // mode & 2: merge all properties of value into the ns
/******/ // mode & 4: return value when already ns object
/******/ // mode & 8|1: behave like require
/******/i.t=function(e,t){
/******/if(
/******/1&t&&(e=i(e)),8&t)return e;
/******/if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;
/******/var n=Object.create(null);
/******/
/******/if(i.r(n),
/******/Object.defineProperty(n,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)i.d(n,r,function(t){return e[t]}.bind(null,r));
/******/return n;
/******/},
/******/
/******/ // getDefaultExport function for compatibility with non-harmony modules
/******/i.n=function(e){
/******/var t=e&&e.__esModule?
/******/function(){return e.default}:
/******/function(){return e};
/******/
/******/return i.d(t,"a",t),t;
/******/},
/******/
/******/ // Object.prototype.hasOwnProperty.call
/******/i.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},
/******/
/******/ // __webpack_public_path__
/******/i.p="",i(i.s=1);
/******/}
/************************************************************************/
/******/([
/* 0 */
/***/function(e,t,i){"use strict";
/* WEBPACK VAR INJECTION */(function(e){function n(){let t;return function(e){t=e}(void 0!==e&&e||this),t}/* harmony export (binding) */i.d(t,"a",(function(){return r}));
/**
 * @hidden
 */
const r=function(){const e=n(),t=Symbol.for("LOKI");return void 0===e[t]&&(e[t]={}),e[t]}();
/* WEBPACK VAR INJECTION */}).call(this,i(2))
/***/},
/* 1 */
/***/function(e,t,i){"use strict";
// CONCATENATED MODULE: ./packages/full-text-search/src/analyzer/tokenizer.ts
/**
 * Splits a string at whitespace characters into tokens.
 * @param {string} value - the string
 * @returns {string[]} - the tokens
 */
function n(e){return e.split(/[\s]+/)}
// CONCATENATED MODULE: ./packages/full-text-search/src/analyzer/token_filter.ts
/**
 * Converts a token to lowercase.
 * @param {string} token - the token
 * @returns {string} - the lowercased token
 */function r(e){return e.toLowerCase()}
/**
 * Converts a token to uppercase.
 * @param {string} token - the token
 * @returns {string} - the uppercased token
 */function s(e){return e.toUpperCase()}
// CONCATENATED MODULE: ./packages/full-text-search/src/analyzer/analyzer.ts
/**
 * Analyzes a given string.
 * @param {Analyzer} analyzer - the analyzer
 * @param {string} str - the string
 * @returns {string[]} - the tokens
 */function o(e,t){if(e.char_filter)for(let i=0;i<e.char_filter.length;i++)t=e.char_filter[i](t);const i=e.tokenizer(t);if(e.token_filter)for(let t=0;t<i.length;t++)for(let n=0;n<e.token_filter.length;n++)i[t]=e.token_filter[n](i[t],t,i);
// Remove empty tokens.
return i.filter((e=>e))}
/**
 * An analyzer with the whitespace tokenizer and the lowercase token filter.
 */i.r(t);class a{constructor(){this.tokenizer=n,this.token_filter=[r]}}
// CONCATENATED MODULE: ./packages/full-text-search/src/inverted_index.ts
/**
 * Converts a string into an array of code points.
 * @param str - the string
 * @returns {number[]} to code points
 * @hidden
 */function l(e){const t=[];for(let i=0;i<e.length;){const n=e.charCodeAt(i++);if(n>=55296&&n<=56319){
// surrogate pair
const r=e.charCodeAt(i++);t.push(65536+(n-55296<<10)|r-56320)}else
// ordinary character
t.push(n)}return t}
/**
 * Inverted index class handles featured text search for specific document fields.
 * @hidden
 */class h{
/**
     * @param {boolean} [options.store=true] - inverted index will be stored at serialization rather than rebuilt on load
     * @param {boolean} [options.optimizeChanges=true] - flag to store additional metadata inside the index for better
     *  performance if an existing field is updated or removed
     * @param {Analyzer} [options.analyzer=] - the analyzer of this inverted index
     */
constructor(e={}){this.docCount=0,this.docStore=new Map,this.totalFieldLength=0,this.root=new Map,({store:this._store=!0,optimizeChanges:this._optimizeChanges=!0,analyzer:this.analyzer=new a}=e)}
/**
     * Adds defined fields of a document to the inverted index.
     * @param {string} field - the field to add
     * @param {number} docId - the doc id of the field
     */insert(e,t){if(this.docStore.has(t))throw Error("Field already added.");
// Tokenize document field.
const i=o(this.analyzer,e);if(0==i.length)
// Add empty field at least to document store for query 'exists'.
return void this.docStore.set(t,{fieldLength:0});this.totalFieldLength+=i.length,this.docCount+=1,this.docStore.set(t,{fieldLength:i.length});
// Holds references to each index of a document.
const n=[];this._optimizeChanges&&Object.defineProperties(this.docStore.get(t),{indexRef:{enumerable:!1,configurable:!0,writable:!0,value:n}});
// Iterate over all unique field terms.
for(const e of new Set(i)){
// Calculate term frequency.
let r=0;for(let t=0;t<i.length;t++)i[t]===e&&++r;
// Add term to index tree.
let s=this.root;for(const t of l(e)){let e=s.get(t);void 0===e&&(e=new Map,this._optimizeChanges&&(e.pa=s),s.set(t,e)),s=e}
// Add term info to index leaf.
void 0===s.dc&&(s.dc=new Map,s.df=0),s.dc.set(t,r),s.df+=1,
// Store index leaf for deletion.
n.push(s)}}
/**
     * Removes all relevant terms of a document from the inverted index.
     * @param {number} docId - the document.
     */remove(e){if(!this.docStore.has(e))return;const t=this.docStore.get(e);
// Remove document.
if(this.docStore.delete(e),0!==t.fieldLength)if(this.docCount-=1,
// Reduce total field length.
this.totalFieldLength-=t.fieldLength,this._optimizeChanges){
// Iterate over all term references.
// Remove docId from docs and decrement document frequency.
const i=t.indexRef;for(let t=0;t<i.length;t++){let n=i[t];
// Check if no document is left for current tree.
if(n.df-=1,n.dc.delete(e),0===n.df){
// Check for sub branches.
if(
// Delete unused meta data of branch.
delete n.df,delete n.dc,0!==n.size)continue;
// Delete term branch if not used anymore.
do{
// Go tree upwards.
const e=n.pa;
// Delete parent reference for preventing memory leak (cycle reference).
delete n.pa;
// Iterate over all children.
for(const t of e.keys())
// Remove previous child form parent.
if(e.get(t)===n){e.delete(t);break}n=e}while(void 0!==n.pa&&0===n.size&&void 0===n.df)}}}else this._remove(this.root,e)}
/**
     * Gets the term index of a term.
     * @param {string} term - the term
     * @param {object} root - the term index to start from
     * @param {number} start - the position of the term string to start from
     * @return {object} - The term index or null if the term is not in the term tree.
     */static getTermIndex(e,t,i=0){if(i>=e.length)return null;for(let n=i;n<e.length;n++){let i=t.get(e[n]);if(void 0===i)return null;t=i}return t}
/**
     * Extends a term index to all available term leafs.
     * @param {object} idx - the term index to start from
     * @param {number[]} [term=[]] - the current term
     * @param {Array} termIndices - all extended indices with their term
     * @returns {Array} - Array with term indices and extension
     */static extendTermIndex(e,t=[],i=[]){void 0!==e.df&&i.push({index:e,term:t.slice()}),t.push(0);for(const n of e)t[t.length-1]=n[0],h.extendTermIndex(n[1],t,i);return t.pop(),i}
/**
     * Serialize the inverted index.
     * @returns {{docStore: *, _fields: *, index: *}}
     */toJSON(){return this._store?{_store:!0,_optimizeChanges:this._optimizeChanges,docCount:this.docCount,docStore:[...this.docStore],totalFieldLength:this.totalFieldLength,root:h._serializeIndex(this.root)}:{_store:!1,_optimizeChanges:this._optimizeChanges}}
/**
     * Deserialize the inverted index.
     * @param {{docStore: *, _fields: *, index: *}} serialized - The serialized inverted index.
     * @param {Analyzer} analyzer[undefined] - an analyzer
     */static fromJSONObject(e,t){const i=new h({store:e._store,optimizeChanges:e._optimizeChanges,analyzer:t});return e._store&&(i.docCount=e.docCount,i.docStore=new Map(e.docStore),i.totalFieldLength=e.totalFieldLength,i.root=h._deserializeIndex(e.root)),i._optimizeChanges&&i._regenerate(i.root,null),i}static _serializeIndex(e){const t={};if(void 0!==e.dc&&(t.d={df:e.df,dc:[...e.dc]}),0===e.size)return t;const i=[],n=[];for(const t of e)i.push(t[0]),n.push(h._serializeIndex(t[1]));return t.k=i,t.v=n,t}static _deserializeIndex(e){const t=new Map;if(void 0!==e.k)for(let i=0;i<e.k.length;i++)t.set(e.k[i],h._deserializeIndex(e.v[i]));return void 0!==e.d&&(t.df=e.d.df,t.dc=new Map(e.d.dc)),t}
/**
     * Set parent of to each index and regenerate the indexRef.
     * @param {Index} index - the index
     * @param {Index} parent - the parent
     */_regenerate(e,t){
// Set parent.
null!==t&&(e.pa=t);
// Iterate over subtree.
for(const t of e.values())this._regenerate(t,e);if(void 0!==e.dc)
// Get documents of term.
for(const t of e.dc.keys()){
// Get document store at specific document/field.
const i=this.docStore.get(t);void 0===i.indexRef&&Object.defineProperties(i,{indexRef:{enumerable:!1,configurable:!0,writable:!0,value:[]}}),
// Set reference to term index.
i.indexRef.push(e)}}
/**
     * Iterate over the whole inverted index and remove the document.
     * Delete branch if not needed anymore.
     * Function is needed if index is used without optimization.
     * @param {Index} idx - the index
     * @param {number} docId - the doc id
     * @returns {boolean} true if index is empty
     */_remove(e,t){for(const i of e)
// Checkout branch.
this._remove(i[1],t)&&e.delete(i[0]);
// Remove docId from docs and decrement document frequency.
return void 0!==e.df&&e.dc.has(t)&&(e.df-=1,e.dc.delete(t),
// Delete unused meta data of branch.
0===e.df&&(delete e.df,delete e.dc)),0===e.size&&void 0===e.dc}}
// CONCATENATED MODULE: ./packages/full-text-search/src/scorer.ts
/**
 * @hidden
 */class c{constructor(e){this._cache={},this._invIdxs=e}setDirty(){this._cache={}}score(e,t,i,n,r,s,o=0){if(null===i||void 0===i.dc)return;const a=this._idf(e,o||i.df);for(const[o,l]of i.dc)r.has(o)||r.set(o,[]),!0===n?
// BM25 scoring.
r.get(o).push({tf:l,idf:a,boost:t,fieldName:e,term:s}):!1===n?
// Constant scoring.
r.set(o,[{boost:t}]):
// Zero scoring.
r.set(o,[{boost:0}])}scoreConstant(e,t,i){return i.has(t)||i.set(t,[]),i.get(t).push({boost:e}),i}finalScore(e,t){const i={},n=void 0!==e.bm25?e.bm25.k1:1.2,r=void 0!==e.bm25?e.bm25.b:.75,s=void 0!==e.explain&&e.explain;for(const[e,o]of t){let t=0,a=[];for(let i=0;i<o.length;i++){const l=o[i];let h=0;if(void 0!==l.tf){
// BM25 scoring.
const t=l.tf,i=c._calculateFieldLength(this._invIdxs[l.fieldName].docStore.get(e).fieldLength),o=this._avgFieldLength(l.fieldName),u=t*(n+1)/(t+n*(1-r+r*(i/o)));h=l.idf*u*l.boost,s&&a.push({boost:l.boost,score:h,docID:e,fieldName:l.fieldName,index:String.fromCharCode(...l.term),idf:l.idf,tfNorm:u,tf:t,fieldLength:i,avgFieldLength:o})}else
// Constant scoring.
h=l.boost,s&&a.push({boost:l.boost,score:h});t+=h}i[e]=s?{score:t,explanation:a}:{score:t}}return i}static _calculateFieldLength(e){
// Dummy function to be compatible to lucene in unit tests.
return e}_getCache(e){if(void 0===this._cache[e]){const t=this._invIdxs[e].totalFieldLength/this._invIdxs[e].docCount;this._cache[e]={idfs:{},avgFieldLength:t}}return this._cache[e]}
/**
     * Returns the idf by either calculate it or use a cached one.
     * @param {string} fieldName - the name of the field
     * @param {number} docFreq - the doc frequency of the term
     * @returns {number} the idf
     * @private
     */_idf(e,t){const i=this._getCache(e);return void 0!==i.idfs[t]?i.idfs[t]:i.idfs[t]=Math.log(1+(this._invIdxs[e].docCount-t+.5)/(t+.5))}_avgFieldLength(e){return this._getCache(e).avgFieldLength}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/run_automaton.ts
/**
 * From org/apache/lucene/util/automaton/RunAutomaton.java
 * @hidden
 */class u{constructor(e){const t=e.getNumStates();this._points=e.getStartPoints(),this._accept=new Array(t),this._transitions=new Array(t*this._points.length);for(let i=0;i<t;i++){this._accept[i]=e.isAccept(i);for(let t=0;t<this._points.length;t++)
// assert dest === -1 || dest < size;
this._transitions[i*this._points.length+t]=e.step(i,this._points[t])}this._classmap=new Array(256/* alphaSize */);for(let e=0,t=0;t<this._classmap.length;t++)e+1<this._points.length&&t===this._points[e+1]&&e++,this._classmap[t]=e}getCharClass(e){
// binary search
let t=0,i=this._points.length;for(;i-t>1;){const n=t+i>>>1;if(this._points[n]>e)i=n;else{if(!(this._points[n]<e))return n;t=n}}return t}step(e,t){return t>=this._classmap.length?this._transitions[e*this._points.length+this.getCharClass(t)]:this._transitions[e*this._points.length+this._classmap[t]]}isAccept(e){return this._accept[e]}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/automaton.ts
/**
 * @type {number}
 * @hidden
 */const d=1114111;
/**
 * @type {number}
 * @hidden
 */function f(e,t){return e[0]<t[0]?-1:e[0]>t[0]?1:e[1]<t[1]?-1:e[1]>t[1]?1:e[2]<t[2]?-1:e[2]>t[2]?1:0}function _(e,t){return e[1]<t[1]?-1:e[1]>t[1]?1:e[2]<t[2]?-1:e[2]>t[2]?1:e[0]<t[0]?-1:e[0]>t[0]?1:0}
/**
 * From org/apache/lucene/util/automaton/Automaton.java
 * @hidden
 */class p{constructor(){this._stateTransitions=[],this._stateTransitions=[],this._accept=new Set,this._nextState=0,this._currState=-1,
// this.deterministic = true;
this._transitions={}}isAccept(e){return this._accept.has(e)}createState(){return this._nextState++}setAccept(e,t){t?this._accept.add(e):this._accept.delete(e)}finishState(){-1!==this._currState&&(this._finishCurrentState(),this._currState=-1)}_finishCurrentState(){
// Sort all transitions.
this._stateTransitions.sort(f);let e=0,t=[-1,-1,-1];for(let i=0,n=this._stateTransitions.length;i<n;i++){let n=this._stateTransitions[i];t[0]===n[0]?n[1]<=t[2]+1?n[2]>t[2]&&(t[2]=n[2]):(-1!==t[0]&&(this._stateTransitions[e][0]=t[0],this._stateTransitions[e][1]=t[1],this._stateTransitions[e][2]=t[2],e++),t[1]=n[1],t[2]=n[2]):(-1!==t[0]&&(this._stateTransitions[e][0]=t[0],this._stateTransitions[e][1]=t[1],this._stateTransitions[e][2]=t[2],e++),t[0]=n[0],t[1]=n[1],t[2]=n[2])}-1!==t[0]&&(
// Last transition
this._stateTransitions[e][0]=t[0],this._stateTransitions[e][1]=t[1],this._stateTransitions[e][2]=t[2],e++),this._transitions[this._currState]=this._stateTransitions.slice(0,e).sort(_),
// if (this.deterministic && upto > 1) {
//   let lastMax = this.stateTransitions[0][2];
//   for (let i = 1; i < upto; i++) {
//     let min = this.stateTransitions[i][1];
//     if (min <= lastMax) {
//       this.deterministic = false;
//       break;
//     }
//     lastMax = this.stateTransitions[i][2];
//   }
// }
this._stateTransitions=[]}getStartPoints(){const e=new Set;e.add(0);const t=Object.keys(this._transitions);for(let i=0;i<t.length;i++){let n=this._transitions[t[i]];for(let t=0;t<n.length;t++){let i=n[t];e.add(i[1]),i[2]<d&&e.add(i[2]+1)}}return Array.from(e).sort(((e,t)=>e-t))}step(e,t){let i=this._transitions[e];if(i)for(let e=0;e<i.length;e++){let n=i[e];if(n[1]<=t&&t<=n[2])return n[0]}return-1}getNumStates(){return this._nextState}addTransition(e,t,i,n){this._currState!==e&&(-1!==this._currState&&this._finishCurrentState(),this._currState=e),this._stateTransitions.push([t,i,n])}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/long.ts
/**
 * Class supports 64Bit integer operations.
 * A cut-down version of dcodeIO/long.js.
 * @hidden
 */class g{constructor(e=0,t=0){this._low=e,this._high=t}
/**
     * Returns this long with bits arithmetically shifted to the right by the given amount.
     * @param {number} numBits - number of bits
     * @returns {Long} the long
     */shiftRight(e){return 0==(e&=63)?this:e<32?new g(this._low>>>e|this._high<<32-e,this._high>>e):new g(this._high>>e-32,this._high>=0?0:-1)}
/**
     * Returns this long with bits arithmetically shifted to the left by the given amount.
     * @param {number} numBits - number of bits
     * @returns {Long} the long
     */shiftLeft(e){return 0==(e&=63)?this:e<32?new g(this._low<<e,this._high<<e|this._low>>>32-e):new g(0,this._low<<e-32)}
/**
     * Returns the bitwise AND of this Long and the specified.
     * @param {Long} other - the other Long
     * @returns {Long} the long
     */and(e){return new g(this._low&e._low,this._high&e._high)}
/**
     * Converts the Long to a 32 bit integer, assuming it is a 32 bit integer.
     * @returns {number}
     */toInt(){return this._low}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/parametric_description.ts
const w=[new g(1),new g(3),new g(7),new g(15),new g(31),new g(63),new g(127),new g(255),new g(511),new g(1023),new g(2047),new g(4095),new g(8191),new g(16383),new g(32767),new g(65535),new g(15,8191),new g(15,16383),new g(15,32767),new g(15,65535),new g(255,8191),new g(255,16383),new g(255,32767),new g(255,65535),new g(4095,8191),new g(4095,16383),new g(4095,32767),new g(4095,65535),new g(65535,8191),new g(65535,16383),new g(65535,32767),new g(65535,65535),new g(1048575,8191),new g(1048575,16383),new g(1048575,32767),new g(1048575,65535),new g(16777215,8191),new g(16777215,16383),new g(16777215,32767),new g(16777215,65535),new g(268435455,8191),new g(268435455,16383),new g(268435455,32767),new g(268435455,65535),new g(4294967295,8191),new g(4294967295,16383),new g(4294967295,32767),new g(4294967295,65535),new g(68719476735,8191),new g(68719476735,16383),new g(68719476735,32767),new g(68719476735,65535),new g(0xffffffffff,8191),new g(0xffffffffff,16383),new g(0xffffffffff,32767),new g(0xffffffffff,65535),new g(0xfffffffffff,8191),new g(0xfffffffffff,16383),new g(0xfffffffffff,32767),new g(0xfffffffffff,65535),new g(0xffffffffffff,8191),new g(0xffffffffffff,16383),new g(0xffffffffffff,32767)];
/**
 * From org/apache/lucene/util/automaton/LevenshteinAutomata.java#ParametricDescription
 * @hidden
 */class m{constructor(e,t,i){this._w=e,this._n=t,this._minErrors=i}
/**
     * Return the number of states needed to compute a Levenshtein DFA
     */size(){return this._minErrors.length*(this._w+1)}
/**
     * Returns true if the <code>state</code> in any Levenshtein DFA is an accept state (final state).
     */isAccept(e){
// decode absState -> state, offset
let t=Math.floor(e/(this._w+1)),i=e%(this._w+1);
//assert offset >= 0;
return this._w-i+this._minErrors[t]<=this._n}
/**
     * Returns the position in the input word for a given <code>state</code>.
     * This is the minimal boundary for the state.
     */getPosition(e){return e%(this._w+1)}static unpack(e,t,i){const n=i*t,r=n>>6,s=63&n;if(s+i<=64)
// not split
return e[r].shiftRight(s).and(w[i-1]).toInt();{
// split
const t=64-s;return e[r].shiftRight(s).and(w[t-1]).toInt()+e[1+r].and(w[i-t-1]).shiftLeft(t).toInt()}}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/lev1t_parametric_description.ts
// 1 vectors; 2 states per vector; array length = 2
const v=[new g(2)],y=[new g(0)],b=[new g(2627)],x=[new g(56)],S=[new g(2182348803,877873428),new g(109)],k=[new g(1436680192,21845)],O=[new g(2416705539,559024212),new g(1161073005,1531779490),new g(55860)],I=[new g(553385984,1431678474),new g(1431655765)];
// state map
//   0 -> [(0, 0)]
//   1 -> [(0, 1)]
//   2 -> [(0, 1), (1, 1)]
//   3 -> [(0, 1), (2, 1)]
//   4 -> [t(0, 1), (0, 1), (1, 1), (2, 1)]
//   5 -> [(0, 1), (1, 1), (2, 1)]
/**
 * From org/apache/lucene/util/automaton/Lev1TParametricDescription.java
 * @hidden
 */
class C extends m{constructor(e){super(e,1,[0,1,0,-1,-1,-1])}transition(e,t,i){
// null absState should never be passed in
//assert absState != -1;
// decode absState -> state, offset
let n=Math.floor(e/(this._w+1)),r=e%(this._w+1);
//assert offset >= 0;
if(t===this._w){if(n<2){const e=2*i+n;r+=m.unpack(y,e,1),n=m.unpack(v,e,2)-1}}else if(t===this._w-1){if(n<3){const e=3*i+n;r+=m.unpack(x,e,1),n=m.unpack(b,e,2)-1}}else if(t===this._w-2){if(n<6){const e=6*i+n;r+=m.unpack(k,e,2),n=m.unpack(S,e,3)-1}}else if(n<6){const e=6*i+n;r+=m.unpack(I,e,2),n=m.unpack(O,e,3)-1}return-1===n?-1:n*(this._w+1)+r}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/lev2t_parametric_description.ts
// 1 vectors; 3 states per vector; array length = 3
const R=/*2 bits per value */[new g(35)],A=/*1 bits per value */[new g(0)],D=/*3 bits per value */[new g(325618500)],P=/*1 bits per value */[new g(992)],j=/*4 bits per value */[new g(1375778052,1625010352),new g(654713383,1379082614),new g(338833973,592794674),new g(17236)],N=/*2 bits per value */[new g(8192,1431339176),new g(1431655765,85)],M=/*5 bits per value */[new g(1074107396,3875651625),new g(10813440,2685408800),new g(2705416840,2955709504),new g(822630592,176295986),new g(220770817,826549144),new g(2222426336,1384244520),new g(146941966,2721677523),new g(2841782156,506631345),new g(579396904,2353082526),new g(35310113,289686537),new g(2259748971,295985736),new g(492978372,711088276),new g(1217426605,1344578827),new g(1376534810,344070858),new g(190401092,1485354377),new g(3289490533,2484954400),new g(2909430484,2337837173),new g(441472420)],E=/*2 bits per value */[new g(8192,3195650),new g(3288085308,704655603),new g(2189600800,591003698),new g(850559912,1431655765),new g(1431655765,1431655765),new g(1431655765,1431655765),new g(1431655765,1431655765)],z=/*6 bits per value */[new g(2904068,58725456),new g(3640,3305111883),new g(1363153922,1300),new g(0),new g(335609856,85458955),new g(685900336,166838792),new g(2198499522,564071920),new g(136348160,2181038210),new g(1619003392,134546689),new g(39855683,813828486),new g(1347453028,1164181826),new g(536873009,139461908),new g(2231378050,1094735904),new g(160481793,1164017816),new g(1352667217,137456908),new g(84799712,558175264),new g(340820500,219423040),new g(1350704224,1008844824),new g(3407093895,30086147),new g(407994924,2148016453),new g(545259552,2097672),new g(2266497861,3490060320),new g(613903113,3406463435),new g(1648822737,145860110),new g(2183434377,38340640),new g(13811748,3272876486),new g(356860963,1009861909),new g(3256660288,830815266),new g(740327956,1158959115),new g(1351286865,141656116),new g(1359540421,2999666001),new g(481339408,3894702429),new g(2425032288,337824532),new g(3224154437,813771810),new g(212943372,2216698370),new g(550373456,1545653768),new g(2332913858,545392672),new g(337723912,1107841154),new g(1350765600,153125696),new g(325399954,3323153862),new g(1841617741,3540595740),new g(1423134004,1680136456),new g(50861250,2449943586),new g(614664496,1109422667),new g(633938146,611374880),new g(2539425922,2462657904),new g(76697096,3406332098),new g(3259769985,1165203240),new g(3663819994,3336195509),new g(1563465501,1264399831),new g(2474794210,271614300),new g(34386245,1363419217),new g(740429356,3308790030),new g(1389038960,139543060),new g(2232701250,541788240),new g(1079067660,2450874499),new g(2785961365,1298533965),new g(476956248,2497254628),new g(341103461,2187601497),new g(1359153171,680658732),new g(3408700171,3804373106),new g(542345488,1160540375),new g(1888368785,145935149),new g(3255087694,2177569856),new g(683854372,3661947790),new g(2245419236,499571301),new g(2388496718,3804978483),new g(949191224)],T=/*3 bits per value */[new g(524288,805437440),new g(2146400),new g(67108864,2169044992),new g(276973604,1076138561),new g(1610621058,3680514243),new g(807079296,1815527532),new g(897243,2954387888),new g(2441666669,460338720),new g(114847159,134255104),new g(37758096,76680228),new g(136613897,4784130),new g(672286724,1225265793),new g(306857122,880804100),new g(220463628,3272159376),new g(616713508,1073781257),new g(2449540634,77089286),new g(1898353250,1229784210),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,9362)],$=/*6 bits per value */[new g(2904068,58725456),new g(3640,3305111883),new g(1363153922,1300),new g(0),new g(335609856,85196811),new g(59637984,5570560),new g(100708736,642062416),new g(136348168,2181570690),new g(1082263584,181504),new g(2156659014,1887570488),new g(2620424828,3279691970),new g(545261671,2130440),new g(33562752,2973765664),new g(5341184,2190352419),new g(547298336,137406220),new g(2235429087,1363481680),new g(340820500,370417986),new g(813715536,1613103716),new g(1124606104,621086726),new g(341196820,1107296387),new g(545587281,139461128),new g(336856450,2157513760),new g(136714249,2181140994),new g(2416314689,143787289),new g(3257709122,575218834),new g(23218476,1124599045),new g(2248302630,2151761173),new g(3316920642,935559200),new g(340819988,1107841157),new g(1350893649,21053528),new g(2550763714,1363501440),new g(206610448,3758633325),new g(1351295472,743623468),new g(3257709129,1611476114),new g(407929372,2268864960),new g(63640608,738315028),new g(1159221634,545261601),new g(136347648,1157636098),new g(545724419,141559316),new g(84419023,1946484981),new g(408981504,2471335494),new g(813845808,1277481805),new g(3321943618,25561121),new g(635093620,3265295049),new g(2445440114,745112472),new g(2300846658,2453800992),new g(883951872,2181591424),new g(2963079265,481446262),new g(2635903144,1625695344),new g(359976510,3541325271),new g(633494900,476056888),new g(1111241026,1364284500),new g(335790868,3257672139),new g(558045267,11715080),new g(85217605,54855856),new g(206604056,1427443855),new g(4060419156,141821184),new g(102297744,3797110162),new g(1704116792,1228416601),new g(566624470,1143194388),new g(3408729413,1925357634),new g(2693907828,1110194563),new g(1351298130,11715860),new g(2150936715,4039444593),new g(1162957064,2819666635),new g(1901927600,576776228),new g(2385343694,3864603731),new g(949191224,1108095105),new g(570559665,139494432),new g(3456639182,1891785760),new g(136350477,1107828866),new g(1350702113,203440648),new g(2200719491,554174592),new g(137937428,2768779394),new g(2848166960,2863311530),new g(2678717098,447381162),new g(337691400,2185765072),new g(2228833636,1904530289),new g(460404435,885148935),new g(355783501,2567517762),new g(818021680,137626888),new g(1398349970,886858038),new g(1303698529,2759444188),new g(1227133514,2450169746),new g(2173872170,1925324848),new g(814942496,119845450),new g(2450400290,225575516),new g(3372753479,2463566197),new g(618694956,2282496073),new g(3259505840,747801636),new g(2299037513,2158306440),new g(2865185684,1787173674),new g(2871505528,135998630),new g(120332803,2735288466),new g(1763036764,3614016979),new g(1998285110,1567933020),new g(2301457623,1917716851),new g(142656005,1277460939),new g(1939286210,1635048005),new g(3662525914,1252095430),new g(2252890502,1787206439),new g(813795018,212944144),new g(1142968578,571354193),new g(941690412,3406655685),new g(1363285074,340869640),new g(1258836101,1363414048),new g(339772204,3407106312),new g(1217071240,2486264328),new g(2675866051,4205477370),new g(2124930941,50862570),new g(550507601,1701086552),new g(2473165721,2517850499),new g(956767089,3647288901),new g(2521109812,81828105),new g(85213378,559286324),new g(1625708889,3596674266),new g(3336332676,2449992057),new g(3750905888,2821358087),new g(271614374,2300605125),new g(2999595186,740427564),new g(87593230,1388776818),new g(149129492,2334962391),new g(541795552,481379340),new g(2351735368,2269850802),new g(608733960,1133805922),new g(2602532471,2658691750),new g(3970345447,1359153177),new g(680658732,2386076427),new g(2207475987,1771444057),new g(1161328411,1959672182),new g(149130029,3255099982),new g(2177569856,683854372),new g(3661947790,2245419236),new g(1975966309,1770391529),new g(2582087242,2798283430)],F=/*3 bits per value */[new g(524288,805437440),new g(2146400),new g(67108864,16777216),new g(1348481048,3681400539),new g(11702,2759852034),new g(1092883008,306782344),new g(1065248,1073742080),new g(2450071634,613598240),new g(157651673,204527616),new g(3277862616,2954562566),new g(1815534349,409731075),new g(2954587142,2911241057),new g(1533925085,905970103),new g(230032140,3289526556),new g(3068358150,56077),new g(3674310171,152604166),new g(1907829602,7198427),new g(8390944,1076101705),new g(2420711618,545409280),new g(1074040832,302064768),new g(2760925472,1428467018),new g(38273045,1083326496),new g(1212191753,2454856978),new g(603981856,1226838017),new g(541721760,689080612),new g(349513,2416455890),new g(616710196,154440460),new g(40379539,68708608),new g(1629493832,2588509714),new g(894585300,204767233),new g(2483889154,616827184),new g(153412173,440402074),new g(110231814,1644468298),new g(2456888978,2454277460),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756,1227133513),new g(2454267026,613566756),new g(1227133513,2454267026),new g(613566756)];
// state map
//   0 -> [(0, 0)]
//   1 -> [(0, 2)]
//   2 -> [(0, 1)]
//   3 -> [(0, 1), (1, 1)]
//   4 -> [(0, 2), (1, 2)]
//   5 -> [t(0, 2), (0, 2), (1, 2), (2, 2)]
//   6 -> [(0, 2), (2, 1)]
//   7 -> [(0, 1), (2, 2)]
//   8 -> [(0, 2), (2, 2)]
//   9 -> [(0, 1), (1, 1), (2, 1)]
//   10 -> [(0, 2), (1, 2), (2, 2)]
//   11 -> [(0, 1), (2, 1)]
//   12 -> [t(0, 1), (0, 1), (1, 1), (2, 1)]
//   13 -> [(0, 2), (1, 2), (2, 2), (3, 2)]
//   14 -> [t(0, 2), (0, 2), (1, 2), (2, 2), (3, 2)]
//   15 -> [(0, 2), t(1, 2), (1, 2), (2, 2), (3, 2)]
//   16 -> [(0, 2), (2, 1), (3, 1)]
//   17 -> [(0, 1), t(1, 2), (2, 2), (3, 2)]
//   18 -> [(0, 2), (3, 2)]
//   19 -> [(0, 2), (1, 2), t(1, 2), (2, 2), (3, 2)]
//   20 -> [t(0, 2), (0, 2), (1, 2), (3, 1)]
//   21 -> [(0, 1), (1, 1), (3, 2)]
//   22 -> [(0, 2), (2, 2), (3, 2)]
//   23 -> [(0, 2), (1, 2), (3, 1)]
//   24 -> [(0, 2), (1, 2), (3, 2)]
//   25 -> [(0, 1), (2, 2), (3, 2)]
//   26 -> [(0, 2), (3, 1)]
//   27 -> [(0, 1), (3, 2)]
//   28 -> [(0, 2), (2, 1), (4, 2)]
//   29 -> [(0, 2), t(1, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
//   30 -> [(0, 2), (1, 2), (4, 2)]
//   31 -> [(0, 2), (1, 2), (3, 2), (4, 2)]
//   32 -> [(0, 2), (2, 2), (3, 2), (4, 2)]
//   33 -> [(0, 2), (1, 2), t(2, 2), (2, 2), (3, 2), (4, 2)]
//   34 -> [(0, 2), (1, 2), (2, 2), t(2, 2), (3, 2), (4, 2)]
//   35 -> [(0, 2), (3, 2), (4, 2)]
//   36 -> [(0, 2), t(2, 2), (2, 2), (3, 2), (4, 2)]
//   37 -> [t(0, 2), (0, 2), (1, 2), (2, 2), (4, 2)]
//   38 -> [(0, 2), (1, 2), (2, 2), (4, 2)]
//   39 -> [t(0, 2), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
//   40 -> [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
//   41 -> [(0, 2), (4, 2)]
//   42 -> [t(0, 2), (0, 2), (1, 2), (2, 2), t(2, 2), (3, 2), (4, 2)]
//   43 -> [(0, 2), (2, 2), (4, 2)]
//   44 -> [(0, 2), (1, 2), t(1, 2), (2, 2), (3, 2), (4, 2)]
/**
 * From org/apache/lucene/util/automaton/Lev2TParametricDescription.java
 * @hidden
 */
class q extends m{constructor(e){super(e,2,[0,2,1,0,1,0,-1,0,0,-1,0,-1,-1,-1,-1,-1,-2,-1,-1,-1,-2,-1,-1,-2,-1,-1,-2,-1,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2])}transition(e,t,i){
// null absState should never be passed in
// assert absState != -1;
// decode absState -> state, offset
let n=Math.floor(e/(this._w+1)),r=e%(this._w+1);
// assert offset >= 0;
if(t===this._w){if(n<3){const e=3*i+n;r+=m.unpack(A,e,1),n=m.unpack(R,e,2)-1}}else if(t===this._w-1){if(n<5){const e=5*i+n;r+=m.unpack(P,e,1),n=m.unpack(D,e,3)-1}}else if(t===this._w-2){if(n<13){const e=13*i+n;r+=m.unpack(N,e,2),n=m.unpack(j,e,4)-1}}else if(t===this._w-3){if(n<28){const e=28*i+n;r+=m.unpack(E,e,2),n=m.unpack(M,e,5)-1}}else if(t===this._w-4){if(n<45){const e=45*i+n;r+=m.unpack(T,e,3),n=m.unpack(z,e,6)-1}}else if(n<45){const e=45*i+n;r+=m.unpack(F,e,3),n=m.unpack($,e,6)-1}return-1===n?-1:n*(this._w+1)+r}}
// CONCATENATED MODULE: ./packages/full-text-search/src/fuzzy/levenshtein_automata.ts
/**
 * From org/apache/lucene/util/automaton/LevenshteinAutomata.java
 * @hidden
 */class L{constructor(e,t){this._word=e,this._editDistance=t,this._alphabet=[...new Set(this._word)].sort(((e,t)=>e-t)),this._numRanges=0,this._rangeLower=new Array(this._alphabet.length+2),this._rangeUpper=new Array(this._alphabet.length+2);
// calculate the unicode range intervals that exclude the alphabet
// these are the ranges for all unicode characters not in the alphabet
let i=0;for(let e=0;e<this._alphabet.length;e++){const t=this._alphabet[e];t>i&&(this._rangeLower[this._numRanges]=i,this._rangeUpper[this._numRanges]=t-1,this._numRanges++),i=t+1}
/* add the final endpoint */i<=d&&(this._rangeLower[this._numRanges]=i,this._rangeUpper[this._numRanges]=d,this._numRanges++),this._description=1===t?new C(e.length):new q(e.length)}
/**
     * Transforms the NDFA to a DFA.
     * @returns {Automaton}
     */toAutomaton(){let e=new p;const t=2*this._editDistance+1,i=this._description.size();
// the number of states is based on the length of the word and the edit distance
// Prefix is not needed to be handled by the automaton.
// stateOffset = 0;
e.createState();
// create all states, and mark as accept states if appropriate
for(let t=1;t<i;t++){let i=e.createState();e.setAccept(i,this._description.isAccept(t))}for(let n=0;n<i;n++){const i=this._description.getPosition(n);if(i<0)continue;const r=i+Math.min(this._word.length-i,t);for(let t=0;t<this._alphabet.length;t++){const s=this._alphabet[t],o=this._getVector(s,i,r),a=this._description.transition(n,i,o);a>=0&&e.addTransition(n,a,s,s)}const s=this._description.transition(n,i,0);if(s>=0)for(let t=0;t<this._numRanges;t++)e.addTransition(n,s,this._rangeLower[t],this._rangeUpper[t])}
// assert automat.deterministic;
return e.finishState(),e}_getVector(e,t,i){let n=0;for(let r=t;r<i;r++)n<<=1,this._word[r]===e&&(n|=1);return n}}
// CONCATENATED MODULE: ./packages/full-text-search/src/index_searcher.ts
function J(e,t){if(void 0===t)return 1;if("number"==typeof t)return t<0?e+t:t;let i=e;if(t.includes("<")){
// Parse conditional minimumShouldMatch.;
for(const n of t.split(" ")){const t=n.split("<");if(e<=parseInt(t[0]))return i;i=J(e,t[1])}return i}if(t.includes("%")){
// Parse percentage.
const e=i*parseInt(t.slice(0,-1))*.01;i=e<0?i+Math.ceil(e):Math.floor(e)}else{const e=parseInt(t);i=e<0?i+e:e}return i<1?1:i}
/**
 * @hidden
 */class V{
/**
     * Constructs an index searcher.
     * @param {Dict<InvertedIndex>} invIdxs - the inverted indexes
     * @param {Set<number>} docs - the ids of the documents
     */
constructor(e,t){this._invIdxs=e,this._docs=t,this._scorer=new c(this._invIdxs)}search(e){let t=this._recursive(e.query,!0);
// Do final scoring.
if(void 0===e.calculate_scoring||e.calculate_scoring)return this._scorer.finalScore(e,t);const i={};for(const e of t.keys())i[e]={score:1};return i}setDirty(){this._scorer.setDirty()}_recursive(e,t){let i=new Map;const n=void 0!==e.boost?e.boost:1,r=void 0!==e.field?e.field:null;let s=null,a=null;switch(void 0!==this._invIdxs[r]&&(s=this._invIdxs[r].root,a=this._invIdxs[r].analyzer),e.type){case"bool":if(i=null,void 0!==e.must&&(i=this._getUnique(e.must,t,i)),void 0!==e.filter&&(i=this._getUnique(e.filter,null,i)),void 0!==e.should){const n=this._getAll(e.should,t);let r=!1;null===i&&(r=!0,i=new Map);const s=Math.max(1,J(e.should.length,e.minimum_should_match));if(r&&1===s)
// Take all documents.
i=n;else
// Remove documents with fewer matches.
for(const[e,t]of n)t.length>=s&&(i.has(e)?i.get(e).push(...t):r?i.set(e,t):i.delete(e))}
// Match all documents if must/filter/should is not defined.
if(null===i&&(i=this._recursive({type:"match_all"},!1)),void 0!==e.not){let t=this._getAll(e.not,null);
// Remove all matching documents.
for(const e of t.keys())i.has(e)&&i.delete(e)}
// Boost query results afterwards.
if(1!==n)for(const[e,t]of i)for(let e=0;e<t.length;e++)t[e].boost*=n;break;case"term":{const o=l(e.value);let a=h.getTermIndex(o,s);this._scorer.score(r,n,a,t,i,o);break}case"terms":for(let o=0;o<e.value.length;o++){const a=l(e.value[o]);let c=h.getTermIndex(a,s);this._scorer.score(r,n,c,t,i,a)}break;case"fuzzy":{const[o,a]=
/**
 * Performs a fuzzy search.
 * @param {FuzzyQuery} query - the fuzzy query
 * @param {Index} root - the root index
 * @returns {[FuzzyResult, number]} - the fuzzy results and the maximum df
 */
function(e,t){let i=l(e.value),n=void 0!==e.fuzziness?e.fuzziness:"AUTO";"AUTO"===n&&(n=i.length<=2?0:i.length<=5?1:2);let r=void 0!==e.prefix_length?e.prefix_length:0,s=void 0!==e.extended&&e.extended;
// Do just a prefix search if zero fuzziness.
0===n&&(r=i.length);let o=[],a=t,c=i.slice(0,r),d=i,f=0;
// No startIdx found.
if(
// Perform a prefix search.
0!==r&&(a=h.getTermIndex(c,a),d=d.slice(r)),null===a)return[o,f];
// Fuzzy is not necessary anymore, because prefix search includes the whole query value.
if(0===d.length){if(s){
// Add all terms down the index.
const e=h.extendTermIndex(a);for(let t=0;t<e.length;t++)o.push({index:e[t].index,term:e[t].term,boost:1}),f=Math.max(f,e[t].index.df)}else void 0!==a.dc&&(
// Add prefix search result.
o.push({index:a,term:i,boost:1}),f=a.df);return[o,f]}
// The matching term.
const _=[0],p=new u(new L(d,n).toAutomaton());
// Create an automaton from the fuzzy.
function g(e,t,i){
// Check how many edits this fuzzy can still do.
let r=0;if(-1!==(e=p.step(e,0))&&p.isAccept(e)&&(r++,-1!==(e=p.step(e,0))&&p.isAccept(e)&&r++,t.length<i.length)){if(r!==n)
/**
 * Calculates the levenshtein distance. Specialized version.
 * Copyright Kigiri: https://github.com/kigiri
 *           Milot Mirdita: https://github.com/milot-mirdita
 *           Toni Neubert:  https://github.com/Viatorus/
 * @param {string} a - a string
 * @param {string} b - a string
 */
return function(e,t){let i,n,r,s;const o=Array(e.length+1);
// init the row
for(i=0;i<=e.length;i++)o[i]=i;
// fill in the rest
for(i=1;i<=t.length;i++){for(r=i,n=1;n<=e.length;n++)t[i-1]===e[n-1]?// match
s=o[n-1]:(s=Math.min(o[n-1]+1,// substitution
Math.min(r+1,// insertion
o[n]+1)),// deletion
// transposition
i>1&&n>1&&t[i-2]===e[n-1]&&e[n-2]===t[i-1]&&(s=Math.min(s,o[n-1]-(e[n-1]===t[i-1]?1:0)))),o[n-1]=r,r=s;o[e.length]=r}return o[e.length]}(t,i);
// Include the term and fuzzy length.
r-=i.length-t.length}return n-r}function w(e,t,n){if(_[_.length-1]=t,-1!==(
// Check the current key of term with the automaton.
e=p.step(e,t))){if(p.isAccept(e)){if(s){
// Add all terms down the index.
const e=h.extendTermIndex(n);for(let t=0;t<e.length;t++)o.push({index:e[t].index,term:e[t].term,boost:1}),f=Math.max(f,e[t].index.df);return}if(void 0!==n.df){
// Calculate boost.
const t=g(e,_,d),r=Math.max(0,1-t/Math.min(c.length+_.length,i.length));o.push({index:n,term:[...c,..._],boost:r}),f=Math.max(f,n.df)}}_.push(0);for(const t of n)w(e,t[0],t[1]);_.pop()}}for(const e of a)w(0,e[0],e[1]);return[o,f]}
/**
 * Performs a wildcard search.
 * @param {WildcardQuery} query - the wildcard query
 * @param {Index} root - the root index
 * @returns {Array} - the results
 */(e,s);for(let e=0;e<o.length;e++)this._scorer.score(r,n*o[e].boost,o[e].index,t,i,o[e].term,a);break}case"wildcard":{const o=void 0!==e.enable_scoring&&e.enable_scoring,a=function(e,t){let i=l(e.value),n=[];function r(e,t=0,s=[],o=!1){if(null!==e)if(t!==i.length)
// Escaped character.
if(o||92/* \ */!==i[t])if(o||63/* ? */!==i[t])if(o||42/* * */!==i[t])r(h.getTermIndex([i[t]],e),t+1,[...s,i[t]]);else
// Check if asterisk is last wildcard character
if(t+1===i.length){const i=h.extendTermIndex(e);for(let e=0;e<i.length;e++)r(i[e].index,t+1,[...s,...i[e].term])}else{
// Iterate over the whole tree.
r(e,t+1,s,!1);const i=[{index:e,term:[]}];do{const e=i.pop();for(const n of e.index)r(n[1],t+1,[...s,...e.term,n[0]]),i.push({index:n[1],term:[...e.term,n[0]]})}while(0!==i.length)}else for(const i of e)r(i[1],t+1,[...s,i[0]]);else r(e,t+1,s,!0);else void 0!==e.df&&n.push({index:e,term:s.slice()})}return r(t),n}
// EXTERNAL MODULE: ./packages/common/plugin.ts
(e,s);for(let e=0;e<a.length;e++)this._scorer.score(r,n,a[e].index,t&&o,i,a[e].term);break}case"match_all":for(let e of this._docs)this._scorer.scoreConstant(n,e,i);break;case"constant_score":{let t=this._getAll(e.filter,!1);
// Add to each document a constant score.
for(const e of t.keys())this._scorer.scoreConstant(n,e,i);break}case"prefix":{const o=void 0!==e.enable_scoring&&e.enable_scoring,a=l(e.value),c=h.getTermIndex(a,s);if(null!==c){const e=h.extendTermIndex(c);for(let s=0;s<e.length;s++)this._scorer.score(r,n,e[s].index,t&&o,i,[...a,...e[s].term])}break}case"exists":if(null!==s)for(const e of this._invIdxs[r].docStore.keys())this._scorer.scoreConstant(n,e,i);break;case"match":{const s=o(a,e.value),l={type:"bool"},h=[];if("or"===(void 0!==e.operator?e.operator:"or")?(void 0!==e.minimum_should_match&&(l.minimum_should_match=e.minimum_should_match),
// Create a should query.
l.should=h):
// Create a must query.
l.must=h,l.boost=n,void 0!==e.fuzziness){let t=void 0!==e.prefix_length?e.prefix_length:2,i=void 0!==e.extended&&e.extended;
// Add each fuzzy.
for(let n=0;n<s.length;n++)h.push({type:"fuzzy",field:r,value:s[n],fuzziness:e.fuzziness,prefix_length:t,extended:i})}else
// Add each term.
for(let e=0;e<s.length;e++)h.push({type:"term",field:r,value:s[e]});i=this._recursive(l,t);break}}return i}_getUnique(e,t,i){if(0===e.length)return i;for(let n=0;n<e.length;n++){let r=this._recursive(e[n],t);if(null!==i)for(const e of i.keys())r.has(e)?i.get(e).push(...r.get(e)):i.delete(e);else i=this._recursive(e[0],t)}return i}_getAll(e,t,i=new Map){for(let n=0;n<e.length;n++){let r=this._recursive(e[n],t);for(const e of r.keys())i.has(e)?i.get(e).push(...r.get(e)):i.set(e,r.get(e))}return i}}var B=i(0);
// CONCATENATED MODULE: ./packages/full-text-search/src/full_text_search.ts
class U{
/**
     * Initialize the full-text search for the given fields.
     * @param {object[]} fieldOptions - the field options
     * @param {string} fieldOptions.field - the name of the property field
     * @param {boolean=true} fieldOptions.store - flag to indicate if the full-text search should be stored on serialization or
     *  rebuild on deserialization
     * @param {boolean=true} fieldOptions.optimizeChanges - flag to optimize updating and deleting of documents
     *    (requires more memory but performs faster)
     * @param {Analyzer} fieldOptions.analyzer - an analyzer for the field
     * @param {string} [id] - the property name of the document index
     */
constructor(e=[],t){this._invIdxs={};
// Create an inverted index for each field.
for(let t=0;t<e.length;t++){let i=e[t];this._invIdxs[i.field]=new h(i)}this._id=t,this._docs=new Set,this._idxSearcher=new V(this._invIdxs,this._docs)}
/**
     * Registers the full-text search as plugin.
     */static register(){B.a.FullTextSearch=U}addDocument(e,t=e[this._id]){let i=Object.keys(this._invIdxs);for(let n,r=0;i.length,n=i[r];r++){let i=e[n];
// Skip null and undefined.
if(null!=i){if("string"!=typeof i){
// Convert number to string.
if("number"!=typeof i)throw TypeError("Unsupported field type for full text search.");i=i.toString()}this._invIdxs[n].insert(i,t)}}this._docs.add(t),this._idxSearcher.setDirty()}removeDocument(e,t=e[this._id]){let i=Object.keys(this._invIdxs);for(let e=0;e<i.length;e++)this._invIdxs[i[e]].remove(t);this._docs.delete(t),this._idxSearcher.setDirty()}updateDocument(e,t=e[this._id]){this.removeDocument(e,t),this.addDocument(e,t)}clear(){for(let e of this._docs)this.removeDocument(null,e)}search(e){return this._idxSearcher.search(e)}toJSON(){let e={id:this._id,ii:{}},t=Object.keys(this._invIdxs);for(let i=0;i<t.length;i++){const n=t[i];e.ii[n]=this._invIdxs[n].toJSON()}return e}static fromJSONObject(e,t={}){let i=new U([],e.id),n=Object.keys(e.ii);for(let r=0;r<n.length;r++){const s=n[r];i._invIdxs[s]=h.fromJSONObject(e.ii[s],t[s])}return i}}
// CONCATENATED MODULE: ./packages/full-text-search/src/index.ts
/* concated harmony reexport */i.d(t,"FullTextSearch",(function(){return U})),
/* concated harmony reexport */i.d(t,"analyze",(function(){return o})),
/* concated harmony reexport */i.d(t,"StandardAnalyzer",(function(){return a})),
/* concated harmony reexport */i.d(t,"whitespaceTokenizer",(function(){return n})),
/* concated harmony reexport */i.d(t,"lowercaseTokenFilter",(function(){return r})),
/* concated harmony reexport */i.d(t,"uppercaseTokenFilter",(function(){return s})),U.Analyzer={},U.Analyzer.analyze=o,U.Analyzer.StandardAnalyzer=a,U.Tokenizer={},U.Tokenizer.whitespaceTokenizer=n,U.TokenFilter={},U.TokenFilter.lowercaseTokenFilter=r,U.TokenFilter.uppercaseTokenFilter=s,t.default=U},
/* 2 */
/***/function(e,t){var i;
// This works in non-strict mode
i=function(){return this}();try{
// This works if eval is allowed (see CSP)
i=i||Function("return this")()||(0,eval)("this")}catch(e){
// This works if the window reference is available
"object"==typeof window&&(i=window)}
// g can still be undefined, but nothing to do about it...
// We return undefined, instead of nothing here, so it's
// easier to handle this case. if(!global) { ...}
e.exports=i}
/******/])},e.exports=n()},
/***/1779:
/***/function(e,t,i){"use strict";i.r(t);var n="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$",r=/[<>\b\f\n\r\t\0\u2028\u2029]/g,s=/^(?:do|if|in|for|int|let|new|try|var|byte|case|char|else|enum|goto|long|this|void|with|await|break|catch|class|const|final|float|short|super|throw|while|yield|delete|double|export|import|native|return|switch|throws|typeof|boolean|default|extends|finally|package|private|abstract|continue|debugger|function|volatile|interface|protected|transient|implements|instanceof|synchronized)$/,o={"<":"\\u003C",">":"\\u003E","/":"\\u002F","\\":"\\\\","\b":"\\b","\f":"\\f","\n":"\\n","\r":"\\r","\t":"\\t","\0":"\\0","\u2028":"\\u2028","\u2029":"\\u2029"},a=Object.getOwnPropertyNames(Object.prototype).sort().join("\0");function l(e){return Object(e)!==e}function h(e){if("string"==typeof e)return f(e);if(void 0===e)return"void 0";if(0===e&&1/e<0)return"-0";var t=String(e);return"number"==typeof e?t.replace(/^(-)?0\./,"$1."):t}function c(e){return Object.prototype.toString.call(e).slice(8,-1)}function u(e){return o[e]||e}function d(e){return e.replace(r,u)}function f(e){for(var t='"',i=0;i<e.length;i+=1){var n=e.charAt(i),r=n.charCodeAt(0);if('"'===n)t+='\\"';else if(n in o)t+=o[n];else if(r>=55296&&r<=57343){var s=e.charCodeAt(i+1);
// If this is the beginning of a [high, low] surrogate pair,
// add the next two characters, otherwise escape
t+=r<=56319&&s>=56320&&s<=57343?n+e[++i]:"\\u"+r.toString(16).toUpperCase()}else t+=n}return t+='"'}
/* harmony default export */t.default=function(e){var t=new Map;!function e(i){if("function"==typeof i)throw new Error("Cannot stringify a function");if(t.has(i))t.set(i,t.get(i)+1);else if(t.set(i,1),!l(i))switch(c(i)){case"Number":case"String":case"Boolean":case"Date":case"RegExp":return;case"Array":i.forEach(e);break;case"Set":case"Map":Array.from(i).forEach(e);break;default:var n=Object.getPrototypeOf(i);if(n!==Object.prototype&&null!==n&&Object.getOwnPropertyNames(n).sort().join("\0")!==a)throw new Error("Cannot stringify arbitrary non-POJOs");if(Object.getOwnPropertySymbols(i).length>0)throw new Error("Cannot stringify POJOs with symbolic keys");Object.keys(i).forEach((function(t){return e(i[t])}))}}(e);var i=new Map;function r(e){if(i.has(e))return i.get(e);if(l(e))return h(e);var t=c(e);switch(t){case"Number":case"String":case"Boolean":return"Object("+r(e.valueOf())+")";case"RegExp":return"new RegExp("+f(e.source)+', "'+e.flags+'")';case"Date":return"new Date("+e.getTime()+")";case"Array":var n=e.map((function(t,i){return i in e?r(t):""})),s=0===e.length||e.length-1 in e?"":",";return"["+n.join(",")+s+"]";case"Set":case"Map":return"new "+t+"(["+Array.from(e).map(r).join(",")+"])";default:var o="{"+Object.keys(e).map((function(t){return function(e){return/^[_$a-zA-Z][_$a-zA-Z0-9]*$/.test(e)?e:d(JSON.stringify(e))}(t)+":"+r(e[t])})).join(",")+"}";return null===Object.getPrototypeOf(e)?Object.keys(e).length>0?"Object.assign(Object.create(null),"+o+")":"Object.create(null)":o}}Array.from(t).filter((function(e){return e[1]>1})).sort((function(e,t){return t[1]-e[1]})).forEach((function(e,t){i.set(e[0],function(e){var t="";do{t=n[e%n.length]+t,e=~~(e/n.length)-1}while(e>=0);return s.test(t)?t+"_":t}(t))}));var o=r(e);if(i.size){var u=[],_=[],p=[];return i.forEach((function(e,t){if(u.push(e),l(t))p.push(h(t));else switch(c(t)){case"Number":case"String":case"Boolean":p.push("Object("+r(t.valueOf())+")");break;case"RegExp":p.push(t.toString());break;case"Date":p.push("new Date("+t.getTime()+")");break;case"Array":p.push("Array("+t.length+")"),t.forEach((function(t,i){_.push(e+"["+i+"]="+r(t))}));break;case"Set":p.push("new Set"),_.push(e+"."+Array.from(t).map((function(e){return"add("+r(e)+")"})).join("."));break;case"Map":p.push("new Map"),_.push(e+"."+Array.from(t).map((function(e){var t=e[0],i=e[1];return"set("+r(t)+", "+r(i)+")"})).join("."));break;default:p.push(null===Object.getPrototypeOf(t)?"Object.create(null)":"{}"),Object.keys(t).forEach((function(i){_.push(""+e+function(e){return/^[_$a-zA-Z][_$a-zA-Z0-9]*$/.test(e)?"."+e:"["+d(JSON.stringify(e))+"]"}(i)+"="+r(t[i]))}))}})),_.push("return "+o),"(function("+u.join(",")+"){"+_.join(";")+"}("+p.join(",")+"))"}return o}},
/***/1780:
/***/function(e,t,i){"use strict";i.r(t);
/* harmony import */var n=i(9),r=(i(10),i(46),i(28),i(15),i(27),i(24),i(26),i(291),i(1718)),s=i.n(r),o=i(1720),a=i.n(o),l=i(1721);
/* harmony import */i.n(l).a.register();var h,c,u=["/"],d=function(){var e={},t=[];Array.from(arguments).forEach((function(i){"string"==typeof i?t.push(i):"object"===Object(n.a)(i)&&(e=i)}));var i=e,r=i.text,o=void 0!==r&&r,a=i.deep,l=void 0!==a&&a,h="/".concat(t.join("/").replace(/\/+/g,"/")),d=!h||!!u.find((function(e){return e===h})),f=d?{dir:l?{$regex:new RegExp("^".concat(h))}:h}:{path:h},_=d?[]:[function(e){return e[0]}];return new s.a({query:c.chain().find(f,!d),path:h,postprocess:_,text:o},{fullTextSearchFields:["title","description","slug","text"]})};
/* harmony default export */t.default=function(e){return(h=new a.a("content.db")).loadJSONObject(e),c=h.getCollection("items"),d}},
/***/776:
/***/function(e,t,i){
// 20.2.2.34 Math.trunc(x)
var n=i(19);n(n.S,"Math",{trunc:function(e){return(e>0?Math.floor:Math.ceil)(e)}})},
/***/777:
/***/function(e,t,i){"use strict";
// B.2.3.10 String.prototype.link(url)
i(1279)("link",(function(e){return function(t){return e(this,"a","href",t)}}))},
/***/795:
/***/function(e,t,i){"use strict";
// https://github.com/tc39/proposal-string-pad-start-end
var n=i(19),r=i(434),s=i(289),o=/Version\/10\.\d+(\.\d+)?( Mobile\/\w+)? Safari\//.test(s);n(n.P+n.F*o,"String",{padStart:function(e/* , fillString = ' ' */){return r(this,e,arguments.length>1?arguments[1]:void 0,!0)}})},
/***/880:
/***/function(e,t,i){
// 22.1.3.6 Array.prototype.fill(value, start = 0, end = this.length)
var n=i(19);n(n.P,"Array",{fill:i(1300)}),i(143)("fill")},
/***/938:
/***/function(e,t,i){"use strict";
// B.2.3.13 String.prototype.sub()
i(1279)("sub",(function(e){return function(){return e(this,"sub","","")}}))}}]);