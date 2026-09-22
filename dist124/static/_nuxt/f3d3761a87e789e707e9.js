/*! For license information please see LICENSES */
(window.webpackJsonp=window.webpackJsonp||[]).push([[7],{
/***/12:
/***/function(t,e,n){"use strict";
/* WEBPACK VAR INJECTION */(function(t){/* unused harmony export Store */
/* unused harmony export createLogger */
/* unused harmony export createNamespacedHelpers */
/* unused harmony export install */
/* harmony export (binding) */n.d(e,"b",(function(){return S})),
/* harmony export (binding) */n.d(e,"c",(function(){return w})),
/* harmony export (binding) */n.d(e,"d",(function(){return P})),
/* harmony export (binding) */n.d(e,"e",(function(){return j}));var r=("undefined"!=typeof window?window:void 0!==t?t:{}).__VUE_DEVTOOLS_GLOBAL_HOOK__;
/**
 * Deep copy the given object considering circular structure.
 * This function caches all nested objects and its copies.
 * If it detects circular structure, use cached copy to avoid infinite loop.
 *
 * @param {*} obj
 * @param {Array<Object>} cache
 * @return {*}
 */
function o(t,e){
// just return if obj is immutable value
if(void 0===e&&(e=[]),null===t||"object"!=typeof t)return t;
// if obj is hit, it is in circular structure
var n,r=(n=function(e){return e.original===t},e.filter(n)[0]);if(r)return r.copy;var a=Array.isArray(t)?[]:{};
// put the copy into cache at first
// because we want to refer it in recursive deepCopy
return e.push({original:t,copy:a}),Object.keys(t).forEach((function(n){a[n]=o(t[n],e)})),a}
/**
 * forEach for object
 */function a(t,e){Object.keys(t).forEach((function(n){return e(t[n],n)}))}function i(t){return null!==t&&"object"==typeof t}
// Base data struct for store's module, package with some attribute and method
var c=function(t,e){this.runtime=e,
// Store some children item
this._children=Object.create(null),
// Store the origin module object which passed by programmer
this._rawModule=t;var n=t.state;
// Store the origin module's state
this.state=("function"==typeof n?n():n)||{}},u={namespaced:{configurable:!0}};u.namespaced.get=function(){return!!this._rawModule.namespaced},c.prototype.addChild=function(t,e){this._children[t]=e},c.prototype.removeChild=function(t){delete this._children[t]},c.prototype.getChild=function(t){return this._children[t]},c.prototype.hasChild=function(t){return t in this._children},c.prototype.update=function(t){this._rawModule.namespaced=t.namespaced,t.actions&&(this._rawModule.actions=t.actions),t.mutations&&(this._rawModule.mutations=t.mutations),t.getters&&(this._rawModule.getters=t.getters)},c.prototype.forEachChild=function(t){a(this._children,t)},c.prototype.forEachGetter=function(t){this._rawModule.getters&&a(this._rawModule.getters,t)},c.prototype.forEachAction=function(t){this._rawModule.actions&&a(this._rawModule.actions,t)},c.prototype.forEachMutation=function(t){this._rawModule.mutations&&a(this._rawModule.mutations,t)},Object.defineProperties(c.prototype,u);var s=function(t){
// register root module (Vuex.Store options)
this.register([],t,!1)};function l(t,e,n){
// update nested modules
if(
// update target module
e.update(n),n.modules)for(var r in n.modules){if(!e.getChild(r))return void 0;l(t.concat(r),e.getChild(r),n.modules[r])}}s.prototype.get=function(t){return t.reduce((function(t,e){return t.getChild(e)}),this.root)},s.prototype.getNamespace=function(t){var e=this.root;return t.reduce((function(t,n){return t+((e=e.getChild(n)).namespaced?n+"/":"")}),"")},s.prototype.update=function(t){l([],this.root,t)},s.prototype.register=function(t,e,n){var r=this;void 0===n&&(n=!0);var o=new c(e,n);0===t.length?this.root=o:this.get(t.slice(0,-1)).addChild(t[t.length-1],o);
// register nested modules
e.modules&&a(e.modules,(function(e,o){r.register(t.concat(o),e,n)}))},s.prototype.unregister=function(t){var e=this.get(t.slice(0,-1)),n=t[t.length-1],r=e.getChild(n);r&&r.runtime&&e.removeChild(n)},s.prototype.isRegistered=function(t){var e=this.get(t.slice(0,-1)),n=t[t.length-1];return!!e&&e.hasChild(n)};var f;// bind on install
var g=function(t){var e=this;void 0===t&&(t={}),
// Auto install if it is not done yet and `window` has `Vue`.
// To allow users to avoid auto-installation in some cases,
// this code should be placed here. See #731
!f&&"undefined"!=typeof window&&window.Vue&&I(window.Vue);var n=t.plugins;void 0===n&&(n=[]);var o=t.strict;void 0===o&&(o=!1),
// store internal state
this._committing=!1,this._actions=Object.create(null),this._actionSubscribers=[],this._mutations=Object.create(null),this._wrappedGetters=Object.create(null),this._modules=new s(t),this._modulesNamespaceMap=Object.create(null),this._subscribers=[],this._watcherVM=new f,this._makeLocalGettersCache=Object.create(null);
// bind commit and dispatch to self
var a=this,i=this.dispatch,c=this.commit;this.dispatch=function(t,e){return i.call(a,t,e)},this.commit=function(t,e,n){return c.call(a,t,e,n)},
// strict mode
this.strict=o;var u=this._modules.root.state;
// init root module.
// this also recursively registers all sub-modules
// and collects all module getters inside this._wrappedGetters
v(this,u,[],this._modules.root),
// initialize the store vm, which is responsible for the reactivity
// (also registers _wrappedGetters as computed properties)
h(this,u),
// apply plugins
n.forEach((function(t){return t(e)})),(void 0!==t.devtools?t.devtools:f.config.devtools)&&function(t){r&&(t._devtoolHook=r,r.emit("vuex:init",t),r.on("vuex:travel-to-state",(function(e){t.replaceState(e)})),t.subscribe((function(t,e){r.emit("vuex:mutation",t,e)}),{prepend:!0}),t.subscribeAction((function(t,e){r.emit("vuex:action",t,e)}),{prepend:!0}))}
/**
 * Get the first item that pass the test
 * by second argument function
 *
 * @param {Array} list
 * @param {Function} f
 * @return {*}
 */(this)},d={state:{configurable:!0}};function p(t,e,n){return e.indexOf(t)<0&&(n&&n.prepend?e.unshift(t):e.push(t)),function(){var n=e.indexOf(t);n>-1&&e.splice(n,1)}}function m(t,e){t._actions=Object.create(null),t._mutations=Object.create(null),t._wrappedGetters=Object.create(null),t._modulesNamespaceMap=Object.create(null);var n=t.state;
// init all modules
v(t,n,[],t._modules.root,!0),
// reset vm
h(t,n,e)}function h(t,e,n){var r=t._vm;
// bind store public getters
t.getters={},
// reset local getters cache
t._makeLocalGettersCache=Object.create(null);var o=t._wrappedGetters,i={};a(o,(function(e,n){
// use computed to leverage its lazy-caching mechanism
// direct inline function use will lead to closure preserving oldVm.
// using partial to return function with only arguments preserved in closure environment.
i[n]=function(t,e){return function(){return t(e)}}(e,t),Object.defineProperty(t.getters,n,{get:function(){return t._vm[n]},enumerable:!0})}));
// use a Vue instance to store the state tree
// suppress warnings just in case the user has added
// some funky global mixins
var c=f.config.silent;f.config.silent=!0,t._vm=new f({data:{$$state:e},computed:i}),f.config.silent=c,
// enable strict mode for new vm
t.strict&&function(t){t._vm.$watch((function(){return this._data.$$state}),(function(){0}),{deep:!0,sync:!0})}(t),r&&(n&&
// dispatch changes in all subscribed watchers
// to force getter re-evaluation for hot reloading.
t._withCommit((function(){r._data.$$state=null})),f.nextTick((function(){return r.$destroy()})))}function v(t,e,n,r,o){var a=!n.length,i=t._modules.getNamespace(n);
// set state
if(
// register in namespace map
r.namespaced&&(t._modulesNamespaceMap[i],t._modulesNamespaceMap[i]=r),!a&&!o){var c=y(e,n.slice(0,-1)),u=n[n.length-1];t._withCommit((function(){f.set(c,u,r.state)}))}var s=r.context=
/**
 * make localized dispatch, commit, getters and state
 * if there is no namespace, just use root ones
 */
function(t,e,n){var r=""===e,o={dispatch:r?t.dispatch:function(n,r,o){var a=b(n,r,o),i=a.payload,c=a.options,u=a.type;return c&&c.root||(u=e+u),t.dispatch(u,i)},commit:r?t.commit:function(n,r,o){var a=b(n,r,o),i=a.payload,c=a.options,u=a.type;c&&c.root||(u=e+u),t.commit(u,i,c)}};
// getters and state object must be gotten lazily
// because they will be changed by vm update
return Object.defineProperties(o,{getters:{get:r?function(){return t.getters}:function(){return function(t,e){if(!t._makeLocalGettersCache[e]){var n={},r=e.length;Object.keys(t.getters).forEach((function(o){
// skip if the target getter is not match this namespace
if(o.slice(0,r)===e){
// extract local getter type
var a=o.slice(r);
// Add a port to the getters proxy.
// Define as getter property because
// we do not want to evaluate the getters in this time.
Object.defineProperty(n,a,{get:function(){return t.getters[o]},enumerable:!0})}})),t._makeLocalGettersCache[e]=n}return t._makeLocalGettersCache[e]}(t,e)}},state:{get:function(){return y(t.state,n)}}}),o}(t,i,n);r.forEachMutation((function(e,n){!function(t,e,n,r){var o=t._mutations[e]||(t._mutations[e]=[]);o.push((function(e){n.call(t,r.state,e)}))}(t,i+n,e,s)})),r.forEachAction((function(e,n){var r=e.root?n:i+n,o=e.handler||e;!function(t,e,n,r){var o=t._actions[e]||(t._actions[e]=[]);o.push((function(e){var o,a=n.call(t,{dispatch:r.dispatch,commit:r.commit,getters:r.getters,state:r.state,rootGetters:t.getters,rootState:t.state},e);return(o=a)&&"function"==typeof o.then||(a=Promise.resolve(a)),t._devtoolHook?a.catch((function(e){throw t._devtoolHook.emit("vuex:error",e),e})):a}))}(t,r,o,s)})),r.forEachGetter((function(e,n){!function(t,e,n,r){if(t._wrappedGetters[e])return void 0;t._wrappedGetters[e]=function(t){return n(r.state,// local state
r.getters,// local getters
t.state,// root state
t.getters)}}(t,i+n,e,s)})),r.forEachChild((function(r,a){v(t,e,n.concat(a),r,o)}))}function y(t,e){return e.reduce((function(t,e){return t[e]}),t)}function b(t,e,n){return i(t)&&t.type&&(n=e,e=t,t=t.type),{type:t,payload:e,options:n}}function I(t){f&&t===f||
/*!
 * vuex v3.6.2
 * (c) 2021 Evan You
 * @license MIT
 */
function(t){if(Number(t.version.split(".")[0])>=2)t.mixin({beforeCreate:n});else{
// override init and inject vuex init procedure
// for 1.x backwards compatibility.
var e=t.prototype._init;t.prototype._init=function(t){void 0===t&&(t={}),t.init=t.init?[n].concat(t.init):n,e.call(this,t)}}
/**
   * Vuex init hook, injected into each instances init hooks list.
   */function n(){var t=this.$options;
// store injection
t.store?this.$store="function"==typeof t.store?t.store():t.store:t.parent&&t.parent.$store&&(this.$store=t.parent.$store)}}(f=t)}
/**
 * Reduce the code which written in Vue.js for getting the state.
 * @param {String} [namespace] - Module's namespace
 * @param {Object|Array} states # Object's item can be a function which accept state and getters for param, you can do something for state and getters in it.
 * @param {Object}
 */d.state.get=function(){return this._vm._data.$$state},d.state.set=function(t){0},g.prototype.commit=function(t,e,n){var r=this,o=b(t,e,n),a=o.type,i=o.payload,c=(o.options,{type:a,payload:i}),u=this._mutations[a];
// check object-style commit
u&&(this._withCommit((function(){u.forEach((function(t){t(i)}))})),this._subscribers.slice().forEach((function(t){return t(c,r.state)})))},g.prototype.dispatch=function(t,e){var n=this,r=b(t,e),o=r.type,a=r.payload,i={type:o,payload:a},c=this._actions[o];
// check object-style dispatch
if(c){try{this._actionSubscribers.slice().filter((function(t){return t.before})).forEach((function(t){return t.before(i,n.state)}))}catch(t){0}var u=c.length>1?Promise.all(c.map((function(t){return t(a)}))):c[0](a);return new Promise((function(t,e){u.then((function(e){try{n._actionSubscribers.filter((function(t){return t.after})).forEach((function(t){return t.after(i,n.state)}))}catch(t){0}t(e)}),(function(t){try{n._actionSubscribers.filter((function(t){return t.error})).forEach((function(e){return e.error(i,n.state,t)}))}catch(t){0}e(t)}))}))}},g.prototype.subscribe=function(t,e){return p(t,this._subscribers,e)},g.prototype.subscribeAction=function(t,e){return p("function"==typeof t?{before:t}:t,this._actionSubscribers,e)},g.prototype.watch=function(t,e,n){var r=this;return this._watcherVM.$watch((function(){return t(r.state,r.getters)}),e,n)},g.prototype.replaceState=function(t){var e=this;this._withCommit((function(){e._vm._data.$$state=t}))},g.prototype.registerModule=function(t,e,n){void 0===n&&(n={}),"string"==typeof t&&(t=[t]),this._modules.register(t,e),v(this,this.state,t,this._modules.get(t),n.preserveState),
// reset store to update getters...
h(this,this.state)},g.prototype.unregisterModule=function(t){var e=this;"string"==typeof t&&(t=[t]),this._modules.unregister(t),this._withCommit((function(){var n=y(e.state,t.slice(0,-1));f.delete(n,t[t.length-1])})),m(this)},g.prototype.hasModule=function(t){return"string"==typeof t&&(t=[t]),this._modules.isRegistered(t)},g.prototype.hotUpdate=function(t){this._modules.update(t),m(this,!0)},g.prototype._withCommit=function(t){var e=this._committing;this._committing=!0,t(),this._committing=e},Object.defineProperties(g.prototype,d);var j=O((function(t,e){var n={};return _(e).forEach((function(e){var r=e.key,o=e.val;n[r]=function(){var e=this.$store.state,n=this.$store.getters;if(t){var r=N(this.$store,"mapState",t);if(!r)return;e=r.context.state,n=r.context.getters}return"function"==typeof o?o.call(this,e,n):e[o]},
// mark vuex getter for devtools
n[r].vuex=!0})),n})),P=O((function(t,e){var n={};return _(e).forEach((function(e){var r=e.key,o=e.val;n[r]=function(){for(var e=[],n=arguments.length;n--;)e[n]=arguments[n];
// Get the commit method from store
var r=this.$store.commit;if(t){var a=N(this.$store,"mapMutations",t);if(!a)return;r=a.context.commit}return"function"==typeof o?o.apply(this,[r].concat(e)):r.apply(this.$store,[o].concat(e))}})),n})),w=O((function(t,e){var n={};return _(e).forEach((function(e){var r=e.key,o=e.val;
// The namespace has been mutated by normalizeNamespace
o=t+o,n[r]=function(){if(!t||N(this.$store,"mapGetters",t))return this.$store.getters[o]},
// mark vuex getter for devtools
n[r].vuex=!0})),n})),S=O((function(t,e){var n={};return _(e).forEach((function(e){var r=e.key,o=e.val;n[r]=function(){for(var e=[],n=arguments.length;n--;)e[n]=arguments[n];
// get dispatch function from store
var r=this.$store.dispatch;if(t){var a=N(this.$store,"mapActions",t);if(!a)return;r=a.context.dispatch}return"function"==typeof o?o.apply(this,[r].concat(e)):r.apply(this.$store,[o].concat(e))}})),n}));
/**
 * Reduce the code which written in Vue.js for committing the mutation
 * @param {String} [namespace] - Module's namespace
 * @param {Object|Array} mutations # Object's item can be a function which accept `commit` function as the first param, it can accept another params. You can commit mutation and do any other things in this function. specially, You need to pass anthor params from the mapped function.
 * @return {Object}
 */
/**
 * Normalize the map
 * normalizeMap([1, 2, 3]) => [ { key: 1, val: 1 }, { key: 2, val: 2 }, { key: 3, val: 3 } ]
 * normalizeMap({a: 1, b: 2, c: 3}) => [ { key: 'a', val: 1 }, { key: 'b', val: 2 }, { key: 'c', val: 3 } ]
 * @param {Array|Object} map
 * @return {Object}
 */
function _(t){
/**
 * Validate whether given map is valid or not
 * @param {*} map
 * @return {Boolean}
 */
return function(t){return Array.isArray(t)||i(t)}
/**
 * Return a function expect two param contains namespace and map. it will normalize the namespace and then the param's function will handle the new namespace and the map.
 * @param {Function} fn
 * @return {Function}
 */(t)?Array.isArray(t)?t.map((function(t){return{key:t,val:t}})):Object.keys(t).map((function(e){return{key:e,val:t[e]}})):[]}function O(t){return function(e,n){return"string"!=typeof e?(n=e,e=""):"/"!==e.charAt(e.length-1)&&(e+="/"),t(e,n)}}
/**
 * Search a special module from store by namespace. if module not exist, print error message.
 * @param {Object} store
 * @param {String} helper
 * @param {String} namespace
 * @return {Object}
 */function N(t,e,n){return t._modulesNamespaceMap[n]}
// Credits: borrowed code from fcomb/redux-logger
function L(t,e,n){var r=n?t.groupCollapsed:t.group;
// render
try{r.call(t,e)}catch(n){t.log(e)}}function T(t){try{t.groupEnd()}catch(e){t.log("—— log end ——")}}function E(){var t=new Date;return" @ "+C(t.getHours(),2)+":"+C(t.getMinutes(),2)+":"+C(t.getSeconds(),2)+"."+C(t.getMilliseconds(),3)}function C(t,e){return n="0",r=e-t.toString().length,new Array(r+1).join(n)+t;var n,r}var k={Store:g,install:I,version:"3.6.2",mapState:j,mapMutations:P,mapGetters:w,mapActions:S,createNamespacedHelpers:function(t){return{mapState:j.bind(null,t),mapGetters:w.bind(null,t),mapMutations:P.bind(null,t),mapActions:S.bind(null,t)}},createLogger:function(t){void 0===t&&(t={});var e=t.collapsed;void 0===e&&(e=!0);var n=t.filter;void 0===n&&(n=function(t,e,n){return!0});var r=t.transformer;void 0===r&&(r=function(t){return t});var a=t.mutationTransformer;void 0===a&&(a=function(t){return t});var i=t.actionFilter;void 0===i&&(i=function(t,e){return!0});var c=t.actionTransformer;void 0===c&&(c=function(t){return t});var u=t.logMutations;void 0===u&&(u=!0);var s=t.logActions;void 0===s&&(s=!0);var l=t.logger;return void 0===l&&(l=console),function(t){var f=o(t.state);void 0!==l&&(u&&t.subscribe((function(t,i){var c=o(i);if(n(t,f,c)){var u=E(),s=a(t),g="mutation "+t.type+u;L(l,g,e),l.log("%c prev state","color: #9E9E9E; font-weight: bold",r(f)),l.log("%c mutation","color: #03A9F4; font-weight: bold",s),l.log("%c next state","color: #4CAF50; font-weight: bold",r(c)),T(l)}f=c})),s&&t.subscribeAction((function(t,n){if(i(t,n)){var r=E(),o=c(t),a="action "+t.type+r;L(l,a,e),l.log("%c action","color: #03A9F4; font-weight: bold",o),T(l)}})))}}};
/* harmony default export */e.a=k}).call(this,n(39))
/***/},
/***/126:
/***/function(t,e,n){"use strict";
/* harmony export (binding) */n.d(e,"a",(function(){return r}));
/* harmony import */n(115),n(28),n(15),n(27)
/* harmony import */;var r=function(t){return new Map([[3,{webId:"TADA",projectI18nTitle:"TaDa",projectTitle:"TaDa",projectIcon:"/web_app_icon_tada.png",gameIconBrandFilename:"tada",projectLogoFilename:"tada"}],[110,{webId:"TH",projectI18nTitle:"JILI",projectTitle:"JILI Plus",projectIcon:"/web_app_icon_plus.png",gameIconBrandFilename:"jili",projectLogoFilename:"jili_plus"}],[202,{webId:"IN",projectI18nTitle:"JILI",projectTitle:"JILI Star",projectIcon:"/web_app_icon_star.png",gameIconBrandFilename:"jili",projectLogoFilename:"jili_star"}],[2e4,{webId:"TADA",projectI18nTitle:"TaDa",projectTitle:"TaDa",projectIcon:"/web_app_icon_tada.png",gameIconBrandFilename:"tada",projectLogoFilename:"tada"}],[20001,{webId:"TADA",projectI18nTitle:"TaDa",projectTitle:"TaDa",projectIcon:"/web_app_icon_tada.png",gameIconBrandFilename:"tada",projectLogoFilename:"tada"}],[20002,{webId:"TADA",projectI18nTitle:"JILI.US",projectTitle:"JILI US",projectIcon:"/web_app_icon_plus.png",gameIconBrandFilename:"jili",projectLogoFilename:"jili_us"}]]).get(t)}},
/***/219:
/***/function(t,e){t.exports=function(t){return t.webpackPolyfill||(t.deprecate=function(){},t.paths=[],
// module.parent = undefined by default
t.children||(t.children=[]),Object.defineProperty(t,"loaded",{enumerable:!0,get:function(){return t.l}}),Object.defineProperty(t,"id",{enumerable:!0,get:function(){return t.i}}),t.webpackPolyfill=1),t};
/***/},
/***/241:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(420);
/* harmony default export */e.a=function(t){var e=t.route,n=t.$config,o=t.store,a=Object(r.a)(),i="production"===n.DEPLOY_ENV;a.addReporter({log:function(t){o.commit("errorHandle/addConsole",t)}}),i&&(a.level=0),i&&e.query.debug&&(a.level=5),a.wrapConsole()}},
/***/242:
/***/function(t,e,n){"use strict";
/* harmony default export */e.a=function(t){t.store}},
/***/243:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(52);
/* harmony default export */e.a=function(t){var e=t.$axios,n=t.store,o=t.req,a=t.$config,i=Object(r.a)(o,a.NEW_WEB_API_URL);e.setBaseURL(i),n.commit("SET_WEB_API_URL",i)}},
/***/244:
/***/function(t,e,n){"use strict";
/* harmony import */n(208);
/* harmony import */var r=n(52);
/* harmony default export */e.a=function(t){t.$axios;var e=t.store,n=t.req,o=t.$config,a=Object(r.a)(n,o.WEB_RESOURCE_CDN_URL);a.endsWith("/static")||(a+="/static"),e.commit("SET_WEB_RESOURCE_CDN_URL",a)}},
/***/245:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(17),o=(n(28),n(15),n(27),n(21),n(3));
/* harmony import */
/* harmony default export */e.a=function(t,e){var a=t.app;
// 使用 import() 但不 await
// 不阻塞 plugin 初始化
// 註冊元件的 Promise
return Promise.all([Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,705,7)),Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,706,7)),Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,707,7)),Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,708,7)),Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,709,7)),Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.t.bind(null,710,7))]).then((function(t){var n=Object(r.a)(t,3),i=n[0],c=n[1],u=n[2];o.default.component(i.default.name,i.default),o.default.component(c.default.name,c.default),e("message",u.default),a.$message=u.default})),Promise.resolve()}},
/***/246:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(5),o=n(6),a=(n(32),n(15),n(21),n(22),n(18),n(20),n(7),n(10),n(8),n(14),n(16),n(79)),i=n(62);
/* harmony import */function c(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);e&&(r=r.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.push.apply(n,r)}return n}function u(t){for(var e=1;e<arguments.length;e++){var n=null!=arguments[e]?arguments[e]:{};e%2?c(Object(n),!0).forEach((function(e){Object(r.a)(t,e,n[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):c(Object(n)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))}))}return t}
// import https from 'https'
// 使用動態導入替換靜態導入
/* harmony default export */e.a=function(){var t=Object(o.a)(regeneratorRuntime.mark((function t(e,r){var c,s,l,f,g,d,p,m,h,v,y,b;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return c=e.$axios,s=e.store,l=e.route,f=e.app,g=e.$config,e.redirect,d={},// 動態導入所需模組
t.next=4,Promise.resolve().then(n.t.bind(null,228,7));case 4:return p=t.sent,m=p.default,t.next=8,Promise.all(/* import() */[n.e(1),n.e(0),n.e(2)]).then(n.bind(null,262));case 8:h=t.sent,v=h.isArray,y=h.isObject,// 需要連線自簽憑證時才需要，目前都直接連測試機，固不需要
// dfApi.onResponse((config) => {
//   // 開發環境不驗證 https 憑證
//   if (process.env.NODE_ENV === 'development') {
//     config.httpsAgent = new https.Agent({
//       rejectUnauthorized: false
//     })
//   }
//   return config
// })
(b=c.create({timeout:6e4,paramsSerializer:function(t){return m.stringify(t,{arrayFormat:"none"})}})).onResponse((function(t){
// debug config.isGlobal
// console.log(
//   `${response.config.url} config.isGlobal: ${response.config.isGlobal}`,
//   response.config
// )
// trigger error
// if (response.config.url.includes('ranking-history')) { response.data.Code = 9100 }
return 0!==t.data.Code?Promise.reject(t):Promise.resolve(t.data.Data)})),b.onResponseError(function(){var t=Object(o.a)(regeneratorRuntime.mark((function t(e){var n,r,o,a,i;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 如果是驗證錯誤或api端有錯誤，重設 store 並導到錯誤頁面
if(console.log("API ResponseError:",e.data?e.data:e),console.log("[".concat(e.config.method,"]").concat(e.config.isGlobal?"[global]":""," ").concat(e.config.baseURL).concat(e.config.url),e),
// console.log(response.headers['x-trace'])
// 新增後端 api header 上的追縱碼，加到 api 回應的 data 內，讓各級錯誤元件能顯示
null!==(n=e.headers)&&void 0!==n&&n["x-trace"]&&(e.data.Trace=e.headers["x-trace"]),!e.config.isGlobal||9101!==e.data.Code&&
// HTTP 401
9100!==e.data.Code){t.next=11;break}return t.next=6,s.commit("cookies/RESET_STORE");case 6:a={redirect:l.fullPath,m:e.data.Code},null!==(r=e.headers)&&void 0!==r&&r["x-trace"]&&(a.trace=e.headers["x-trace"]),(i=f.$utils.getCaseInsensitiveProperty(l.query)).skin&&(a.skin=i.skin),null!==(o=l.name)&&void 0!==o&&o.includes("error")?console.log("已經在錯誤頁，不轉導"):window.onNuxtReady((function(){window.$nuxt.$router.push({path:f.localePath("/error"),query:a})}));case 11:return t.abrupt("return",Promise.reject(e.data));case 12:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}()),
/**
           * 送出前端 log 至後端
           * 觸發端目前寫在 plugin/nuxtReady.js 的 vue 全域錯誤處理
           */
d.sendFrontendLog=function(t,e){
// 沒有設定 log api 的設定就不執行
if(g.LOG_API_URL){var n={SiteId:"dfw_web",DeployVersion:g.DEPLOY_ENV,Lang:s.getters.lang,Identity:""+s.getters.accountId||null};if(v(t)){var r=t.map((function(t){var r=JSON.stringify({stack:t.Trace,console:e||null});return Object(a.a)(u(u({},t),{},{Trace:r}),n)}));
// beforeunload 要用的話，需使用 fetch api
return fetch("".concat(g.LOG_API_URL,"/log/js-web-list"),{method:"POST",body:JSON.stringify(r),headers:new Headers({"Content-Type":"application/json"}),keepalive:!0}).catch((function(){})),void s.commit("errorHandle/emptyLogs")}if(y(t)){var o=JSON.stringify({stack:t.Trace,console:e||null}),i=Object(a.a)(u(u({},t),{},{Trace:o}),n);
// beforeunload 要用的話，需使用 fetch api
fetch("".concat(g.LOG_API_URL,"/log/js-web"),{method:"POST",body:JSON.stringify(i),headers:new Headers({"Content-Type":"application/json"}),keepalive:!0}).catch((function(){})),s.commit("errorHandle/emptyLogs")}}},
/**
           * 取得遊戲列表
           * @returns {Promise<object>} 遊戲列表
           */
d.getGameInfoList=function(){return b.get("/v2/game-setting/game-info-list",{isGlobal:!0})},
/**
           * 取得區塊鏈公鏈網址
           * @returns {Promise<object>} 區塊鏈公鏈網址
           */
d.getBlockInfoWebUrl=function(){return b.get("/v2/game-setting/block-info-web-url")},
/**
           * 取得遊戲群組
           * @returns {Promise<object>} 遊戲群組
           */
d.getGameGroup=function(){return b.get("/v2/game-group")},
/**
           * 取得入口遊戲列表
           * @param {string} apiId
           * @param {number} currencyNumber
           * @param {string} sac
           * @param {string} siteId
           * @returns {Promise<object>} 入口遊戲列表
           */
d.getGameEntrance=function(t,e,n,r){if(Object(i.a)(g.WEB_ID,"getGameEntrance")){var o="/v2/game-entrance/".concat(t,"/").concat(e,"/").concat(n,"/").concat(r);return b.get(o)}return Promise.resolve([])},
/**
           * 取得跑馬燈列表
           * @param {string} apiId
           * @param {string} lang
           * @returns {Promise<object>} 跑馬燈列表
           */
d.getMarquee=function(t,e){if(Object(i.a)(g.WEB_ID,"getMarquee")){var n="/v2/marquee/".concat(t,"/").concat(e);return b.get(n)}return Promise.resolve([])},
/**
           * 取得輪播列表
           * @param {string} apiId
           * @param {string} areaId
           * @param {string} actionId?
           * @param {number} gameNo?
           * @returns {Promise<object>} 輪播列表
           */
d.getBanner=function(t,e,n,r){var o;return Object(i.a)(g.WEB_ID,"getBanner")?(o=n&&r?"/v2/banner/".concat(t,"/").concat(e,"/").concat(n,"/").concat(r):n?"/v2/banner/".concat(t,"/").concat(e,"/lang/").concat(n):"/v2/banner/".concat(t,"/").concat(e),b.get(o)):Promise.resolve([])},
/**
           * 取得動態賠率
           * @param {string} apiId
           * @param {string} gameNo
           * @param {string} sac
           * @returns {Promise<object>} 動態賠率
           */
d.getRtpInfo=function(t,e,n){if(Object(i.a)(g.WEB_ID,"getRtpInfo")){var r="/v2/game-setting/rtp/".concat(t,"/").concat(e);return null!=n&&(r+="/".concat(n)),b.get(r)}return Promise.resolve(null)},
/**
           * 取得幣別顯示
           * @returns {Promise<object>} 幣別顯示
           */
d.getCurrencyDisplay=function(){return b.get("/v2/currency-display")},
/**
           * 使用遊戲 token 換取 web api 站台 token
           * @param {string} gameToken
           * @returns {Promise<object>} token物件
           */
d.getToken=function(t){if("{token}"===t)return Promise.resolve(null);return b.post("/v2/token",{Token:t},{isGlobal:!0})},
/**
           * 取得使用者api資訊(已廢棄)
           * @param {string} apiId
           * @returns {Promise<object>} 使用者api資訊
           */
d.getUserApiInfo=function(t){var e="/v2/game-setting/user-api-info/".concat(t);return b.get(e)},
/**
           * 取得活動頁轉址
           * @param {string} apiId - API ID
           * @param {string} gameNo - 遊戲編號
           * @param {number} typeNo - 活動類型編號
           * @param {string} currency - 幣別
           * @param {string} [sac] - subagent code
           * @param {string} [sn] - 活動唯一碼(紅色後台)
           * @param {string} [settingId] - 活動設定 ID
           * @param {string} [startTimestamp] - 活動開始時間戳記(秒)
           * @returns {Promise<object>} 活動頁轉址
           */
d.getActionUrl=function(t){var e=t.apiId,n=t.gameNo,r=t.typeNo,o=t.currency,a=t.sac,i=t.sn,c=t.settingId,u=t.startTimestamp,s="/v2/action/transfer/".concat(e,"/").concat(n,"/").concat(r,"/").concat(o),l={};return null!=a&&(l.sac=a),null!=i&&(l.sn=i),null!=c&&(l.settingId=c),null!=u&&(l.startTimestamp=u),b.get(s,{params:l})},
/**
           * 取得活動頁排行榜設定
           * @param {string} lang 語系
           * @param {string} startTime 開始時間
           * @param {string} endTime 結束時間
           * @param {string} apiId apiId
           * @param {string} gameNoList 進戲編號列表
           * @param {string} type 類型
           * @returns {Promise<object>} 排行榜設定物件
           */
d.getActionPageRankingSetting=function(t,e,n,r,o,a,i){var c={LangId:t,StartDateTime:e,EndDateTime:n,ApiId:r,GameIds:o,Type:a};null!=i&&(c.Sac=i);return b.get("/v2/rank/ranking-setting",{params:c})},
/**
           * 取得活動頁排行榜
           * @param {string} lang 語系
           * @param {number} sn 排行榜編號
           * @param {number} currencyNo 幣別編號
           * @returns {Promise<object>} 排行榜物件
           */
d.getActionPageRankingHistoryList=function(t,e,n){
// 如果有 token 就帶入，有token時能取得玩家自身排名
s.getters.token&&b.setToken(s.getters.token,"Bearer");var r="/v2/rank/ranking-history/".concat(t,"/").concat(e,"/").concat(n);return b.get(r)},
/**
           * 取得下架遊戲引導設定
           * @param {number} gameNo 遊戲編號
           * @returns 下架遊戲引導設定
           */
d.getGuide=function(t,e){var n="/v2/guide/".concat(t,"/").concat(e);return b.get(n)},
/**
            * 取得維修設定
            * @param {number} apiId apiId
            * @returns 維修設定物件
            */
d.getRepair=function(t){var e="/v2/repair/".concat(t);return b.get(e)},
/**
            * 使用遊戲 token 登入已取得遊戲網址
            * @param {string} gameToken
            * @returns {Promise<object>} token物件
            */
d.tokenLogin=function(t,e,n,r){return b.post("/v2/token/login",{Token:t,GameNo:e,IsJPEnabled:n,Lang:r})},
/**
           * 取得說明頁switch off
           * @param {number} apiId apiId
           * @returns {Promise<object>} 說明頁switch off物件
           */
d.getSwitchOffInfo=function(t){if(Object(i.a)(g.WEB_ID,"getSwitchOffInfo")){var e="/v2/game-setting/switch-off-status/".concat(t);return b.get(e)}return Promise.resolve({})},
/**
           * 取得活動推廣頁列表
           * @param {number} apiId apiId
           * @param {langId} langId langId
           * @returns {Promise<object>} 說明頁switch off物件
           */
d.getPromoteList=function(t,e,n,r){var o="/v2/action/promote-list/".concat(t,"/").concat(e,"/").concat(r);return null!=n&&(o+="/".concat(n)),b.get(o)},
/**
           * 取得活動推廣頁列表
           * @param {number} apiId apiId
           * @param {langId} langId langId
           * @returns {Promise<object>} 說明頁switch off物件
           */
d.getLandingList=function(t,e,n,r){var o="/v2/landing/".concat(t,"/").concat(e,"/").concat(r);return null!=n&&(o+="/".concat(n)),b.get(o)},
/**
            * 取得遊戲推廣設定
            * @param {number} apiId API ID
            * @param {number} gameNo 遊戲編號
            * @param {string} lang 語系 ID
            * @param {number} sac SAC
            * @returns {Promise<object>} 遊戲推廣設定 Promise 物件
            */
d.getActionPromoteGameList=function(t,e,n,r){var o="/v2/action/promote-game-list/".concat(t,"/").concat(e,"/").concat(n);return null!=r&&(o+="/".concat(r)),b.get(o)},
/**
            * 取得TADA API ID 列表，給說明頁使用
            * @returns TADA API ID 列表
            */
d.getTadaApiIdList=function(){return b.get("/v2/game-setting/tada-api-id-list")},d.getEventList=function(t,e){var n="/v2/event/".concat(t,"/").concat(e);return b.get(n).then((function(t){return t.PrizeList=t.PrizeList.map((function(t){if(t.imgSrc="/images/event/prizes/prize_".concat(t.PrizeNo,".png"),t.displayDescI18n="i18_EVENT_PRIZE_".concat("TADA"===g.WEB_ID&&t.PrizeNo>=1&&t.PrizeNo<=5?"TADA_NAME":"NAME","_").concat(t.PrizeNo),t.displayAmount="X ".concat(t.PrizeAmount),t.PrizeNo>300&&t.PrizeNo<400){t.imgSrc="/images/event/prizes/prize_300.png",
// PrizeNo 319 為印尼幣，採用印尼幣系統格式顯示
t.displayAmount=319===t.PrizeNo?f.$utils.formatNumberIDR(t.PrizeAmount,3,{rb:!1}):f.$utils.formatNumberKMBT(t.PrizeAmount,3,{k:!1}),t.symbol=f.i18n.t(t.displayDescI18n)}return t})),t})).catch((function(t){return console.log("getEventList catch: ",t),t}))},
/**
           * 取得giftcode
           * @param {string} guid guid
           * @returns {Promise<object>} giftcode
           */
d.getGiftcode=function(t){var e="/v2/giftcode/get/".concat(t);return b.get(e)},
/**
           * 寄送取得giftcode的email
           * @param {int} eventId eventId
           * @param {string} templateId templateId
           * @param {string} email email
           * @returns {Promise<object>} 狀態沒有錯誤就是成功
           */
d.sendGiftcodeEmail=function(t){var e=t.eventId,n=t.templateId,r=t.email,o=t.configSet,a="/v2/giftcode/send-email/".concat(e);return b.post(a,{Email:r,TemplateId:n,AwsConfigSetName:o})},
/**
           * 記錄頁面載入時間
           * @param {string} PageKey 頁面名稱
           * @param {float} PageInitTime 頁面初始化時間
           * @param {float} PageCompleteTime 頁面完成時間
           * @returns {Promise<object>} 狀態沒有錯誤就是成功
           */
d.logPageLoadingTime=function(t){var e=t.PageKey,n=t.PageInitTime,r=t.PageCompleteTime,o=parseInt(n),a=parseInt(r);return b.post("/v2/page-time",{PageKey:e,PageInitTime:o,PageCompleteTime:a})},r("dfApi",d);case 41:case"end":return t.stop()}}),t)})));return function(e,n){return t.apply(this,arguments)}}()},
/***/247:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(6),o=(n(32),n(15),n(21),n(22),n(18),n(20),n(35),n(228)),a=n.n(o),i=n(48),c=n.n(i),u=n(62);
/* harmony import */
/* eslint-disable prefer-promise-reject-errors */
// import https from 'https'
// 替換 moment 為 dayjs
// 帶入身分的 API
/* harmony default export */e.a=function(t,e){var n=t.$axios,o=t.store,i=(t.redirect,t.app),s=(t.req,t.route),l=t.$config,f=n.create({timeout:6e4,paramsSerializer:function(t){return a.a.stringify(t,{arrayFormat:"none"})}}),g={};f.onRequest((function(t){
// 需要連線自簽憑證時才需要，目前都直接連測試機，固不需要
// 開發環境不驗證 https 憑證
// if (process.env.NODE_ENV === 'development') {
//   config.httpsAgent = new https.Agent({
//     rejectUnauthorized: false
//   })
// }
return o.getters.token&&f.setToken(o.getters.token,"Bearer"),t})),f.onResponse((function(t){
// debug config.isGlobal 查看是否全域的api
// console.log(
//   `${response.config.url} config.isGlobal: ${response.config.isGlobal}`,
//   response.config
// )
// 手動觸發錯誤
// if (response.config.url.includes('get-detail-info')) { response.data.Code = 9100 }
return 0!==t.data.Code?Promise.reject(t):Promise.resolve(t.data.Data)})),f.onResponseError(function(){var t=Object(r.a)(regeneratorRuntime.mark((function t(e){var n,r,a,c,u,l;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 如果是驗證錯誤或api端有錯誤，重設 store 並導到錯誤頁面
if(console.log("API ResponseError:",e.data),r=!0,// 記錄錯誤網址
console.log("[".concat(e.config.method,"]").concat(e.config.isGlobal?"[global]":""," ").concat(e.config.baseURL).concat(e.config.url),e),
// console.log(response.headers['x-trace'])
// 新增後端 api header 上的追縱碼，加到 api 回應的 data 內，讓各級錯誤元件能顯示
null!==(n=e.headers)&&void 0!==n&&n["x-trace"]&&(e.data.Trace=e.headers["x-trace"]),
// 顯示錯誤邏輯，列出例外不顯示的
"/member/vip-setting"===e.config.url&&1005===e.data.Code&&(r=!1),r&&
// 提示使用者錯誤訊息
i.$message({message:e.data.Message,type:"error"}),!e.config.isGlobal||9101!==e.data.Code&&
// HTTP 401
9100!==e.data.Code){t.next=14;break}return t.next=9,o.commit("cookies/RESET_STORE");case 9:u={redirect:s.fullPath,m:e.data.Code},null!==(a=e.headers)&&void 0!==a&&a["x-trace"]&&(u.trace=e.headers["x-trace"]),(l=i.$utils.getCaseInsensitiveProperty(s.query)).skin&&(u.skin=l.skin),null!==(c=s.name)&&void 0!==c&&c.includes("error")?console.log("已經在錯誤頁，不轉導"):window.onNuxtReady((function(){window.$nuxt.$router.push({path:i.localePath("/error"),query:u})}));case 14:return t.abrupt("return",Promise.reject(e.data));case 15:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}()),
/**
   * 取得歷程頁排行榜設定
   * @param {string} lang 語系
   * @param {Number} lang 語系
   * @returns {Promise<object>} 排行榜設定物件
   */
g.getRankingSetting=function(t,e){var n="/v2/rank/ranking-setting/".concat(t);return null!=e&&(n+="/".concat(e)),f.get(n)},
/**
   * 取得歷程頁排行榜
   * @param {string} lang 語系
   * @param {number} sn 排行榜編號
   * @returns {Promise<object>} 排行榜物件
   */
g.getRankingHistoryList=function(t,e){var n="/v2/rank/ranking-history/".concat(t).concat(e?"/"+e:"");return f.get(n)},
/**
   * 取得VIP設定
   * @returns {Promise<object>} VIP設定
   */
g.getVIPSetting=function(){if(Object(u.a)(l.WEB_ID,"getVIPSetting")){return f.get("/v2/member/vip-setting")}return Promise.reject({Code:-1,Message:"".concat(l.WEB_ID,"環境沒有vip設定")})},
/**
   * 取得VIP簽到設定
   * @param {number} gameNo 遊戲編號
   * @returns {Promise<object>} VIP簽到設定
   */
g.getVIPSignSetting=function(t){var e="/v2/member/vip-sign-setting/".concat(t);return f.get(e)},
/**
   * 取得VIP等級
   * @returns {Promise<object>} VIP等級
   */
g.getVIPLevel=function(){return f.get("/v2/member/vip-level")},
/**
   * 暱稱設定是否有開啟
   * @returns {Promise<object>} 暱稱設定是否有開啟
   */
g.isNicknameEnable=function(){if(Object(u.a)(l.WEB_ID,"isNicknameEnable")){return f.get("/v2/game-setting/is-enable/NickNameEnable")}return Promise.resolve({IsEnable:!1})},
/**
   * 取得玩家暱稱
   * @returns {Promise<object>} 玩家暱稱
   */
g.getNickname=function(){return f.get("/v2/member/nickname")},
/**
   * 取得隨機玩家暱稱
   * @param {string} lang 語系
   * @returns {Promise<object>} 隨機玩家暱稱
   */
g.getRandomNickname=function(t){var e="/v2/member/random-nickname/".concat(t);return f.get(e)},
/**
   * 取得獎項
   * @param {string} lang 語系
   * @returns {Promise<object>} 獎項
   */
g.getPrize=function(t){var e="/v2/prize/".concat(t);return f.get(e)},
/**
   * 取得使用者道具
   * @param {string} lang 語系
   * @returns {Promise<object>} 使用者道具
   */
g.getPlayerItemData=function(t){if(Object(u.a)(l.WEB_ID,"getPlayerItemData")){var e="/v2/backpack/".concat(t);return f.get(e)}return Promise.reject(!1)},
/**
   * 更新玩家匿稱
   * @param {string} lang 語系
   * @param {string} updatedNickname 要更新的暱稱
   * @returns {Promise<object>} 是否成功
   */
g.updateNickname=function(t,e){return f.put("/v2/member/nickname",{LangId:t,Nickname:e})},
/**
   * 取得歷程列表
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} queryDate 搜尋日期
   * @param {string} queryMinutes 搜尋分鐘
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋LOG號
   * @param {number} startRecord 從第幾筆開始搜尋
   * @param {number} endRecord 搜尋到第幾筆
   * @param {number} enterTimestamp 進入的時間戳
   * @param {string} offsetStartTime 批次查詢的開始時間
   * @param {number} offsetStartRowIndex 批次查詢得開始行數
   * @param {number} offsetDbIndex 批次查詢的開始 DB
   * @returns {Promise<object>} 是否成功
   */
g.getHistoryRecord=function(t){var e=t.gameId,n=t.lang,r=t.apiId,o=t.queryDate,a=t.queryMinutes,u=t.roundIndex,s=t.logIndex,l=t.startRecord,g=t.endRecord,d=t.enterTimestamp,p=t.logIndexAsRoundIndex,m=void 0!==p&&p,h=t.offsetStartTime,v=void 0===h?null:h,y=t.offsetStartRowIndex,b=void 0===y?null:y,I=t.offsetDbIndex,j=void 0===I?null:I,P={LangId:n,StartRowIndex:l,EndRowIndex:g,LogIndexAsRoundIndex:m,EnterTime:d};return u&&(P.RoundIndex=u),s&&(P.LogIndex=s),o&&(P.Date=o,P.TimeZoneOffsetMinutes=c()().utcOffset()),a&&(P.Minutes=a),
// if (gameId === 'coin01' && store.state.detailCreateTime) {
//   sendData.CreateTime = store.state.detailCreateTime
// }
null!=v&&(P.OffsetStartTime=v),null!=b&&(P.OffsetStartRowIndex=b),null!=j&&(P.OffsetDbIndex=j),f.get("/history/".concat(e,"/get-history-record"),{params:P}).then((function(t){return null==t?[]:t.map((function(t){var o=i.$utils.merge({},t);
// 大獎圖片
return o.prizeTypeImage=i.$utils.getPrizeTypeImagePath(o.Type,n,r),
// 魚機新增FreeSpinType
o.freeSpinImage=i.$utils.getFreeSpinImagePath(o.FreeSpinType,n,r,e),
// 魚機新增道具卡
o.typeImage=i.$utils.getFreeSpinImagePath(o.Type,n,r,e),o}))})).catch((function(t){return console.log("get-history-record catch: ",t),t}))},
/**
   * 取得歷程列表
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} queryDate 搜尋日期
   * @param {string} queryMinutes 搜尋分鐘
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋LOG號
   * @param {number} startRecord 從第幾筆開始搜尋
   * @param {number} endRecord 搜尋到第幾筆
   * @param {number} enterTimestamp 進入的時間戳
   * @param {string} offsetStartTime 批次查詢的開始時間
   * @param {number} offsetStartRowIndex 批次查詢得開始行數
   * @param {number} offsetDbIndex 批次查詢的開始 DB
   * @param {string} offsetPageToken 批次查詢的開始 token
   * @returns {Promise<object>} 是否成功
   */
g.getGoHistoryRecord=function(t){var e=t.gameId,n=t.lang,r=t.apiId,o=t.queryDate,a=t.queryMinutes,u=t.roundIndex,s=t.logIndex,l=t.startRecord,g=t.endRecord,d=t.enterTimestamp,p=t.logIndexAsRoundIndex,m=void 0!==p&&p,h=t.offsetStartTime,v=void 0===h?null:h,y=t.offsetStartRowIndex,b=void 0===y?null:y,I=t.offsetDbIndex,j=void 0===I?null:I,P=t.offsetPageToken,w=void 0===P?null:P,S={LangId:n,StartRowIndex:l,EndRowIndex:g,LogIndexAsRoundIndex:m,EnterTime:d};return u&&(S.RoundIndex=u),s&&(S.LogIndex=s),o&&(S.Date=o,S.TimeZoneOffsetMinutes=c()().utcOffset()),a&&(S.Minutes=a),
// if (gameId === 'coin01' && store.state.detailCreateTime) {
//   sendData.CreateTime = store.state.detailCreateTime
// }
null!=v&&(S.OffsetStartTime=v),null!=b&&(S.OffsetStartRowIndex=b),null!=j&&(S.OffsetDbIndex=j),null!=w&&(S.OffsetPageToken=w),f.get("/v2/history/".concat(e,"/get-history-record"),{params:S}).then((function(t){return null==t?[]:t.map((function(t){var o=i.$utils.merge({},t);
// 大獎圖片
return o.prizeTypeImage=i.$utils.getPrizeTypeImagePath(o.Type,n,r),
// 魚機新增FreeSpinType
o.freeSpinImage=i.$utils.getFreeSpinImagePath(o.FreeSpinType,n,r,e),
// 魚機新增道具卡
o.typeImage=i.$utils.getFreeSpinImagePath(o.Type,n,r,e),o}))})).catch((function(t){return console.log("get-history-record catch: ",t),t}))},
/**
   * 取得單筆歷程詳細資料列表
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 局號
   * @param {string} orderMode 排序方式
   * @param {number} startRecord 從第幾筆開始搜尋
   * @param {number} endRecord 搜尋到第幾筆
   * @returns {Promise<object>} 是否成功
   */
g.getDetailRecord=function(t,e,n,r,o,a,i){var c={LangId:e,RoundIndex:n,OrderField:r,StartRowIndex:o,EndRowIndex:a};return i&&(c.LogIndex=i),f.get("/history/".concat(t,"/get-detail-record"),{params:c}).then((function(t){return null==t?[]:t})).catch((function(t){return console.log("get-detail-record catch: ",t),t}))},
/**
   * 取得單筆歷程詳細資料列表
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 局號
   * @param {string} orderMode 排序方式
   * @param {number} startRecord 從第幾筆開始搜尋
   * @param {number} endRecord 搜尋到第幾筆
   * @returns {Promise<object>} 是否成功
   */
g.getGoFish11V2DetailRecord=function(t,e,n){var r={LangId:e,RoundIndex:n};return f.get("/v2/history/".concat(t,"/get-detail-record"),{params:r}).then((function(t){return null==t?[]:t})).catch((function(t){return console.log("get-detail-record catch: ",t),t}))},
/**
   * 取得單筆歷程詳細資料列表
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 局號
   * @param {string} orderMode 排序方式
   * @param {number} startRecord 從第幾筆開始搜尋
   * @param {number} endRecord 搜尋到第幾筆
   * @returns {Promise<object>} 是否成功
   */
g.getGoDetailRecord=function(t,e,n,r,o,a,i){var c={LangId:e,RoundIndex:n,OrderField:r,StartRowIndex:o,EndRowIndex:a};return i&&(c.LogIndex=i),f.get("/v2/history/".concat(t,"/get-detail-record"),{params:c}).then((function(t){return null==t?[]:t})).catch((function(t){return console.log("get-detail-record catch: ",t),t}))},
/**
   * 取得單局明細補充資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋log號
   * @returns {Promise<object>} 是否成功
   */
g.getDetailInfo=function(t,e,n){return f.get("/history/".concat(t,"/get-detail-info/").concat(e).concat(n?"/"+n:"")).catch((function(t){return t}))},
/**
   * 取得單局明細補充資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋log號
   * @returns {Promise<object>} 是否成功
   */
g.getGoDetailInfo=function(t,e,n){return f.get("/v2/history/".concat(t,"/get-detail-info/").concat(e).concat(n?"/"+n:"")).catch((function(t){return t}))},
/**
   * 取得單局明細詳細資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getDetailRoundIndexInfo=function(t,e){return f.get("/history/".concat(t,"/get-detail-record/").concat(e)).catch((function(t){return t}))},
/**
   * 取得單局明細詳細資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoDetailRoundIndexInfo=function(t,e,n){var r=n>0?"/v2/history/".concat(t,"/get-detail-record/").concat(e,"/").concat(n):"/v2/history/".concat(t,"/get-detail-record/").concat(e);return f.get(r).catch((function(t){return t}))},
/**
   * 取得sy明細資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getSyDetailInfo=function(t,e){return f.get("/history/".concat(t,"/get-detail-info/").concat(e)).catch((function(t){return t}))},
/**
   * 取得sy明細資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoSyDetailInfo=function(t,e){return f.get("/v2/history/".concat(t,"/get-detail-info/").concat(e)).catch((function(t){return t}))},
/**
   * 取得被炸彈打到的魚種列表
   * @param {number} gameId 遊戲id
   * @param {string} logIndex 搜尋log號
   * @param {string} bullet 子彈
   * @returns {Promise<object>} 是否成功
   */
g.getBombDetailRecord=function(t,e,n){return f.get("/history/".concat(t,"/get-bomb-detail-record/").concat(e,"/").concat(n)).catch((function(t){return t}))},
/**
   * 取得被炸彈打到的魚種列表
   * @param {number} gameId 遊戲id
   * @param {string} logIndex 搜尋log號
   * @param {string} bullet 子彈
   * @returns {Promise<object>} 是否成功
   */
g.getGoBombDetailRecord=function(t,e,n){return f.get("/v2/history/".concat(t,"/get-bomb-detail-record/").concat(e,"/").concat(n)).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log摘要集合
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getRecordSummary=function(t,e,n){return f.get("/history/".concat(t,"/get-single-round-log-summary/").concat(e,"/").concat(n)).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log摘要集合
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoRecordSummary=function(t,e,n){return f.get("/v2/history/".concat(t,"/get-single-round-log-summary/").concat(e,"/").concat(n)).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getPlateInfo=function(t,e,n){return f.get("/history/".concat(t,"/get-log-plate-info/").concat(e,"/").concat(n)).then((function(t){return Array.isArray(t)&&t.length>0?t.map((function(t){var e=i.$utils.merge({},t),n=e.SymbolLength?e.SymbolLength.split(""):[],r=e.PlateNumStr?e.PlateNumStr.split(","):[],o=e.PlateMult?e.PlateMult.split(","):[];
// 整理盤面資訊
return e.plateGrid=e.Plate.split("").map((function(t,e){var a={symbol:t,selected:null},i=n[e],c=r[e],u=o[e];return i&&(a.symbolLength=i),
// lbingo 金幣數字
c&&(a.plateNum=c),
// 每格倍率
u&&(a.plateMult="0"===u?null:u),a})),e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} logIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoPlateInfo=function(t,e,n){return f.get("/v2/history/".concat(t,"/get-log-plate-info/").concat(e,"/").concat(n)).then((function(t){return Array.isArray(t)&&t.length>0?t.map((function(t){var e=i.$utils.merge({},t),n=e.SymbolLength?e.SymbolLength.split(""):[],r=e.PlateNumStr?e.PlateNumStr.split(","):[],o=e.PlateMult?e.PlateMult.split(","):[];
// 整理盤面資訊
return e.plateGrid=e.Plate.split("").map((function(t,e){var a={symbol:t,selected:null},i=n[e],c=r[e],u=o[e];return i&&(a.symbolLength=i),
// lbingo 金幣數字
c&&(a.plateNum=c),
// 每格倍率
u&&(a.plateMult="0"===u?null:u),a})),e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} langId 語言
   * @param {string} time 時間
   * @returns {Promise<object>} 是否成功
   */
g.getCSV2PlateInfo=function(t,e,n){var r=arguments.length>3&&void 0!==arguments[3]?arguments[3]:"";return f.get("/history/".concat(t,"/get-log-plate-info/").concat(e,"/").concat(n,"/").concat(r)).then((function(t){return Array.isArray(t)&&t.length>0?t.map((function(t){var e=i.$utils.merge({},t),n=e.Plate;return n.forEach((function(t){
// 整理盤面資訊
var e=t.SymbolLength?t.SymbolLength.split(""):[],n=t.PlateNumStr?t.PlateNumStr.split(","):[],r=t.PlateMult?t.PlateMult.split(","):[],o=t.FrameStr?t.FrameStr.split(","):[];
// lbingo 金幣數字
t.plateGrid=t.Plate.split("").map((function(t,a){var i={symbol:t,selected:null},c=e[a],u=n[a],s=r[a],l=o[a];return c&&(i.symbolLength=c),
// lbingo 金幣數字
u&&(i.plateNum=u),
// 每格倍率
s&&(i.plateMult="0"===s?null:s),
// 盤面乘倍框倍率
l&&(i.frameMult="1"===l||"0"===l?null:l),i}))})),e.plate=n,e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} langId 語言
   * @param {string} time 時間
   * @returns {Promise<object>} 是否成功
   */
g.getGoCSV2PlateInfo=function(t,e,n){var r=arguments.length>3&&void 0!==arguments[3]?arguments[3]:"";return f.get("/v2/history/".concat(t,"/get-log-plate-info/").concat(e,"/").concat(n,"/").concat(r)).then((function(t){return Array.isArray(t)&&t.length>0?t.map((function(t){var e=i.$utils.merge({},t),n=e.Plate;return n.forEach((function(t){
// 整理盤面資訊
var e=t.SymbolLength?t.SymbolLength.split(""):[],n=t.PlateNumStr?t.PlateNumStr.split(","):[],r=t.PlateMult?t.PlateMult.split(","):[],o=t.FrameStr?t.FrameStr.split(","):[];
// lbingo 金幣數字
t.plateGrid=t.Plate.split("").map((function(t,a){var i={symbol:t,selected:null},c=e[a],u=n[a],s=r[a],l=o[a];return c&&(i.symbolLength=c),
// lbingo 金幣數字
u&&(i.plateNum=u),
// 每格倍率
s&&(i.plateMult="0"===s?null:s),
// 盤面乘倍框倍率
l&&(i.frameMult="1"===l||"0"===l?null:l),i}))})),e.plate=n,e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} langId 語言
   * @returns {Promise<object>} 是否成功
   */
g.getCSV3PlateInfo=function(t,e,n){return f.get("/history/".concat(t,"/get-log-plate-info/").concat(n,"/").concat(e)).then((function(t){return Array.isArray(t)&&t.length>0?t.map((function(t){var e=i.$utils.merge({},t),n=e.Plate;return n.forEach((function(t){
// 整理盤面資訊
var e=t.SymbolLength?t.SymbolLength.split(""):[],n=t.PlateNumStr?t.PlateNumStr.split(","):[],r=t.PlateMult?t.PlateMult.split(","):[],o=t.FrameStr?t.FrameStr.split(","):[];
// lbingo 金幣數字
t.plateGrid=t.Plate.split("").map((function(t,a){var i={symbol:t,selected:null},c=e[a],u=n[a],s=r[a],l=o[a];return c&&(i.symbolLength=c),
// lbingo 金幣數字
u&&(i.plateNum=u),
// 每格倍率
s&&(i.plateMult="0"===s?null:s),
// 盤面乘倍框倍率
l&&(i.frameMult="1"===l||"0"===l?null:l),i}))})),e.plate=n,e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} langId 語言
   * @returns {Promise<object>} 是否成功
   */
g.getGoCSV3PlateInfo=function(t,e,n){return f.get("/v2/history/".concat(t,"/get-log-plate-info/").concat(n,"/").concat(e)).then((function(e){return"chickendashdice"===t||"chickendash3"===t?[e]:Array.isArray(e)&&e.length>0?e.map((function(t){var e=i.$utils.merge({},t),n=e.Plate;return n.forEach((function(t){
// 整理盤面資訊
var e=t.SymbolLength?t.SymbolLength.split(""):[],n=t.PlateNumStr?t.PlateNumStr.split(","):[],r=t.PlateMult?t.PlateMult.split(","):[],o=t.FrameStr?t.FrameStr.split(","):[];
// lbingo 金幣數字
t.plateGrid=t.Plate.split("").map((function(t,a){var i={symbol:t,selected:null},c=e[a],u=n[a],s=r[a],l=o[a];return c&&(i.symbolLength=c),
// lbingo 金幣數字
u&&(i.plateNum=u),
// 每格倍率
s&&(i.plateMult="0"===s?null:s),
// 盤面乘倍框倍率
l&&(i.frameMult="1"===l||"0"===l?null:l),i}))})),e.plate=n,e})):[]})).catch((function(t){return t}))},
/**
   * 取得單筆輪盤歷程Log盤面資訊
   * @param {string} lang 語系id
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} historyId 歷史編號(對應開獎資訊)
   * @returns {Promise<object>} 是否成功
   */
g.getRouletteInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex,o=t.historyId;return f.get("/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r,"/").concat(o)).catch((function(t){return t}))},
/**
   * 取得單筆輪盤歷程Log盤面資訊
   * @param {string} lang 語系id
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @param {string} historyId 歷史編號(對應開獎資訊)
   * @returns {Promise<object>} 是否成功
   */
g.getGoRouletteInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex,o=t.historyId;return f.get("/v2/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r,"/").concat(o)).catch((function(t){return t}))},
/**
   * 取得TP類型單筆歷程盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getTpPlateInfo=function(t,e){return f.get("/history/".concat(t,"/get-plate-info/").concat(e)).catch((function(t){return t}))},
/**
   * 取得TP類型單筆歷程盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoTpPlateInfo=function(t,e){return f.get("/v2/history/".concat(t,"/get-plate-info/").concat(e)).catch((function(t){return t}))},
/**
   * 取得TP類型單筆歷程逐步下注資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getTpStepDetailRecords=function(t,e){return f.get("/history/".concat(t,"/get-step-detail-record/").concat(e)).catch((function(t){return t}))},
/**
   * 取得TP類型單筆歷程逐步下注資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoTpStepDetailRecords=function(t,e){return f.get("/v2/history/".concat(t,"/get-step-detail-record/").concat(e)).catch((function(t){return t}))},
/**
   * 取得單筆彩票歷程Log盤面資訊
   * @param {stirng}} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getMinigame1Info=function(t){var e=t.gameId,n=t.roundIndex;return f.get("/history/".concat(e,"/get-log-plate-info/").concat(n)).catch((function(t){return t}))},
/**
   * 取得單筆彩票歷程Log盤面資訊
   * @param {stirng}} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoMinigame1Info=function(t){var e=t.gameId,n=t.roundIndex;return f.get("/v2/history/".concat(e,"/get-log-plate-info/").concat(n)).catch((function(t){return t}))},
/**
   * 取得bingo單筆歷程Log所有(掉落球、追加球、賓果卡)資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getBingoInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).then((function(t){var e,n,r=i.$utils.merge({},t);
// 將 Cards 內容重組成跟 summaryList 一樣
return r.Cards=(null==r||null===(e=r.Cards)||void 0===e?void 0:e.map((function(t){var e,n,r=[],o=(null===(e=t.Balls)||void 0===e?void 0:e.map((function(t){return{selected:null,Number:t.Number,Color:t.Color,Bonus:t.Bonus||0,BonusBallList:t.BonusBallList||null}})))||[],a=(null===(n=t.Awards)||void 0===n?void 0:n.map((function(t){return{S:t.Number,Award:t.Line,L:t.Odds,W:t.Win}})))||[];return r[0]={plateGrid:o,List:a},{plate:r,Win:t.Win}})))||[],null===(n=r.Bonus)||void 0===n||n.forEach((function(t,e){var n;t.Cards=(null===(n=t.Cards)||void 0===n?void 0:n.map((function(t){var n,r,o=[],a=(null===(n=t.Balls)||void 0===n?void 0:n.map((function(t){return{selected:null,Number:t.Number,Color:t.Color,Bonus:t.Bonus||0}})))||[],i=(null===(r=t.Awards)||void 0===r?void 0:r.map((function(t){return{S:t.Number,Award:t.Line,L:t.Odds,W:t.Win}})))||[];return o[0]={plateGrid:a,List:i},{plate:o,Win:t.Win,isBonus:!0,bonusIndex:e}})))||[]})),r})).catch((function(t){return t}))},
/**
   * 取得bingo單筆歷程Log所有(掉落球、追加球、賓果卡)資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoBingoInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/v2/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).then((function(t){var e,n,r=i.$utils.merge({},t);
// 將 Cards 內容重組成跟 summaryList 一樣
return r.Cards=(null==r||null===(e=r.Cards)||void 0===e?void 0:e.map((function(t){var e,n,r=[],o=(null===(e=t.Balls)||void 0===e?void 0:e.map((function(t){return{selected:null,Number:t.Number,Color:t.Color,Bonus:t.Bonus||0,BonusBallList:t.BonusBallList||null}})))||[],a=(null===(n=t.Awards)||void 0===n?void 0:n.map((function(t){return{S:t.Number,Award:t.Line,L:t.Odds,W:t.Win}})))||[];return r[0]={plateGrid:o,List:a},{plate:r,Win:t.Win}})))||[],null===(n=r.Bonus)||void 0===n||n.forEach((function(t,e){var n;t.Cards=(null===(n=t.Cards)||void 0===n?void 0:n.map((function(t){var n,r,o=[],a=(null===(n=t.Balls)||void 0===n?void 0:n.map((function(t){return{selected:null,Number:t.Number,Color:t.Color,Bonus:t.Bonus||0}})))||[],i=(null===(r=t.Awards)||void 0===r?void 0:r.map((function(t){return{S:t.Number,Award:t.Line,L:t.Odds,W:t.Win}})))||[];return o[0]={plateGrid:a,List:i},{plate:o,Win:t.Win,isBonus:!0,bonusIndex:e}})))||[]})),r})).catch((function(t){return t}))},
/**
   * 取得單筆押分機歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getDtmDetailInfo=function(t){var e=t.gameId,n=t.roundIndex;return f.get("/history/".concat(e,"/get-detail-info/").concat(n)).catch((function(t){return t}))},
/**
   * 取得單筆押分機歷程Log盤面資訊
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoDtmDetailInfo=function(t){var e=t.gameId,n=t.roundIndex;return f.get("/v2/history/".concat(e,"/get-detail-info/").concat(n)).catch((function(t){return t}))},
/**
   * 取得sudm單筆押分機歷程Log盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getSudmDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得sudm單筆押分機歷程Log盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoSudmDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/v2/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得 sicbom 單筆押分機歷程 Log 盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getSicbomDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得 sicbom 單筆押分機歷程 Log 盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoSicbomDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/v2/history/".concat(n,"/get-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得 sicbom 單筆押分機歷程 Log 盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getSicbomBoxDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/history/".concat(n,"/get-box-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得 sicbom 單筆押分機歷程 Log 盤面資訊
   * @param {string} lang 語系
   * @param {number} gameId 遊戲id
   * @param {string} roundIndex 搜尋局號
   * @returns {Promise<object>} 是否成功
   */
g.getGoSicbomBoxDetailInfo=function(t){var e=t.lang,n=t.gameId,r=t.roundIndex;return f.get("/v2/history/".concat(n,"/get-box-detail-info/").concat(e,"/").concat(r)).catch((function(t){return t}))},
/**
   * 取得公平驗證工具資料
   * @param {string} gameNo 遊戲編號
   * @param {string} serverSeed 伺服器種子
   * @param {string} clientSeed 客戶端種子
   * @param {string} mineCount  炸彈數量
   * @returns {Promise<object>} 驗證後資料
   */
g.getFairnessData=function(t){return f.get("/v2/fairness/steps",{params:t}).catch((function(t){return t}))},
/**
   * 取得廠商驗證id
   * @param {string} RoundIndex 局號
   * @returns {Promise<object>} 廠商id
   */
g.getItaAuthId=function(t){
// TODO: 待 w204315 上線後，要改成 v2
var e="/history/get-ita-auth-id/".concat(t);return f.get(e).catch((function(t){return t}))},e("dfAuthApi",g)}},
/***/248:
/***/function(t,e,n){"use strict";
/* harmony import */n(21),n(22),n(18)
/* harmony import */;var r=n(3);
/* harmony default export */e.a=function(t){t.app;
// Vue.config.warnHandler 在正式環境會被 vue disable 無效所以只用這個 hook 就夠了
var e=t.store,n=t.route;r.default.config.errorHandler=function(t,r,o){var a,i,c,u;console.log("Logged in Vue global error handler: ",t.name),console.log("component name: ",null!==(a=null==r||null===(i=r.$options)||void 0===i?void 0:i.name)&&void 0!==a?a:null),console.log("info: ",o),e.commit("errorHandle/addLog",{Url:location.origin+n.fullPath,Message:"前端錯誤: ".concat(o),Component:null!==(c=null==r||null===(u=r.$options)||void 0===u?void 0:u.name)&&void 0!==c?c:null,Exception:t.message,Trace:t.stack||null})},
// JS Global Error
window.addEventListener("error",(function(t,r,o,a,i){var c;
// 如果是 chrome 擴充套件的錯誤，不收集
null!=t&&null!==(c=t.includes)&&void 0!==c&&c.call(t,"chrome-extension")||(console.log("JS 錯誤:",t,r,o,a,i),e.commit("errorHandle/addLog",{Url:location.origin+n.fullPath,Message:"前端 JS 錯誤: ".concat(t),Exception:"(Line: ".concat(o,", Column: ").concat(a,") ").concat(t),Trace:JSON.stringify(i)}))})),
// 其他未被錯誤處理的 hook
window.addEventListener("unhandledrejection",(function(t){console.log("有未處理的 Promise Rejection (UNHANDLED PROMISE REJECTION)",t),e.commit("errorHandle/addLog",{Url:location.origin+n.fullPath,Message:"有未處理的 Promise Rejection (UNHANDLED PROMISE REJECTION): ".concat(t.reason)})})),
// desktop 關閉視窗時，傳送錯誤log
window.addEventListener("beforeunload",(function(t){e.dispatch("errorHandle/sendLogs")})),
// mobile 關閉視窗時，傳送錯誤log
document.addEventListener("visibilitychange",(function(t){"hidden"===document.visibilityState&&e.dispatch("errorHandle/sendLogs")}))}},
/***/249:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(3),o=n(408),a=n(401);
/* harmony import */
// eslint-disable-next-line import/no-named-as-default
r.default.use(Object(o.a)()),r.default.use(a.a,{defaultPlacement:"auto",defaultTrigger:"click hover",popover:{defaultAutoHide:!0}})},
/***/251:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(405);
/* harmony import */
/* harmony default export */e.a=function(t,e){t.req;e("ua",new r.UAParser(navigator.userAgent))}},
/***/252:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(6),o=n(17),a=(n(32),n(20),n(8),n(22),n(18),n(91),n(24),n(28),n(15),n(27),n(297)),i=n.n(a),c=n(425),u=n(52);
/* harmony import */
/* harmony default export */e.a=function(t){var e=t.app,a=(t.params,t.$axios),s=t.req,l=t.$config,f=Object(u.a)(s,l.LANG_API_URL),g=function(t,n){var r=(null==n?void 0:n.map((function(t){return"GroupIds[]=".concat(t)})).join("&"))||"",i="".concat(f,"/language/").concat(t,"?").concat(r);return a.$get(i,{timeout:6e4}).then((function(r){if(0!==r.Code)return r;
// 處理 style 合併，從 groupIdList 找出有 style 的 key，並合併到 沒有 style 的 key
var a=(null==n?void 0:n.filter((function(t){return t.toLowerCase().includes("_style")})))||[];a.length>0&&a.forEach((function(e){for(var n=Object(c.a)(r.Data[t],(function(t,n){return n.includes(e)})),a=0,i=Object.entries(n);a<i.length;a++){var u=Object(o.a)(i[a],2),s=u[0],l=u[1],f=s.replace(/_style\w*?_/i,"_");r.Data[t][f]=l}})),e.i18n.mergeLocaleMessage(t,r.Data[t])})).catch((function(t){console.log("更新多語系資料發生錯誤: ",t)}))},d={"zh-TW":"zh-TW","zh-CN":"zh-CN","en-US":"en","th-TH":"th","vi-VN":"vi","id-ID":"id",
// 'my-MM': '',
"ja-JP":"ja",
// 'hi-IN': '',
"ta-IN":"ta",
// 'ms-MY': '',
"ko-KR":"ko",
// 'bn-IN': '',
"es-AR":"es","pt-BR":"pt-br","pt-PT":"pt","de-DE":"de","sv-SE":"sv-SE","it-IT":"it","nl-NL":"nl","ro-RO":"ro","da-DK":"da"},p=function(){var t=Object(r.a)(regeneratorRuntime.mark((function t(e){var r,o;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r=d[e]||"en",t.next=3,n(696)("./"+r);case 3:o=t.sent,i.a.use(o.default);case 5:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}();
// 切換語系時執行更新
e.i18n.onBeforeLanguageSwitch=function(){var t=Object(r.a)(regeneratorRuntime.mark((function t(e,n){return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Promise.all([g(n),p(n)]);case 2:case"end":return t.stop()}}),t)})));return function(e,n){return t.apply(this,arguments)}}(),e.i18n.getRemoteLangMessage=g,e.i18n.changeEelmentUiLocale=p}},
/***/253:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(3),o=n(406),a=n.n(o),i=n(166),c=n(230),u=n(231),s=n(232);
/* harmony import */n(701);i.a.use([c.a,u.a,s.a]),r.default.use(a.a)},
/***/254:
/***/function(t,e,n){"use strict";
/* harmony import */n(64);
/* harmony import */var r=n(3);
/* harmony default export */e.a=function(){var t={install:function(){window.Clipboard=function(t,e,n){var r;function o(){var o,a;n.userAgent.match(/ipad|iphone/i)?((o=e.createRange()).selectNodeContents(r),(a=t.getSelection()).removeAllRanges(),a.addRange(o),r.setSelectionRange(0,999999)):r.select()}return{copy:function(t){!function(t){(r=e.createElement("textArea")).value=t,e.body.appendChild(r)}(t),o(),e.execCommand("Copy"),e.body.removeChild(r)}}}(window,document,navigator)}};r.default.use(t)}},
/***/255:
/***/function(t,e,n){"use strict";
/* harmony default export */e.a=function(t,e){var n=t.app,r=t.store,o=t.route,a=function(){n.$utils.cssVar("mag",n.$utils.cssVar("mag_web")),n.$utils.cssVar("font-size-current",n.$utils.cssVar("font-size-web")),n.$utils.cssVar("font-size-current-md",n.$utils.cssVar("font-size-web-md")),n.$utils.cssVar("font-size-current-xl",n.$utils.cssVar("font-size-web-xl"))},i=function(){n.$utils.cssVar("mag",n.$utils.cssVar("mag_app")),n.$utils.cssVar("font-size-current",n.$utils.cssVar("font-size-app")),n.$utils.cssVar("font-size-current-md",n.$utils.cssVar("font-size-app-md")),n.$utils.cssVar("font-size-current-xl",n.$utils.cssVar("font-size-app-xl"))},c=function(){n.$utils.cssVar("mag",n.$utils.cssVar("mag_webapp")),n.$utils.cssVar("font-size-current",n.$utils.cssVar("font-size-webapp")),n.$utils.cssVar("font-size-current-md",n.$utils.cssVar("font-size-webapp-md")),n.$utils.cssVar("font-size-current-xl",n.$utils.cssVar("font-size-webapp-xl"))},u=function(){n.$utils.cssVar("mag",n.$utils.cssVar("mag_lobby")),n.$utils.cssVar("font-size-current",n.$utils.cssVar("font-size-lobby")),n.$utils.cssVar("font-size-current-md",n.$utils.cssVar("font-size-lobby-md")),n.$utils.cssVar("font-size-current-xl",n.$utils.cssVar("font-size-lobby-xl"))};
// 給遊戲大廳使用
e("zoomStyle",{initDefaultAndIntroAndErrorLayout:function(){
// 調整 viewport 倍率，因為遊戲會以dpr呈現不同的寬度
// adjustViewportScale()
// 如果有帶 zoomstyle=web or zoomstyle=app 參數就修改 css 變數
var t=o.query.zoomstyle;r.commit("SET_ZOOM_STYLE",t),"web"===t?a():"app"===t?i():"webapp"===t?c():"lobby"===t&&u()},initOtherLayout:function(){
// 設定預設字體大小
n.$utils.cssVar("--font-size-current","16px"),n.$utils.cssVar("--font-size-current-md","16px"),n.$utils.cssVar("--font-size-current-xl","16px")},addLobbyStyle:u,addWebStyle:a,addWebAppStyle:c,addAppStyle:i})}},
/***/256:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(6),o=(n(32),n(24),n(92),n(21),n(22),n(18),n(28),n(15),n(27),n(26),n(126));
/* harmony import */function a(){return(a=Object(r.a)(regeneratorRuntime.mark((function t(e){var n,r,a,i,c,u,s,l,f,g,d,p,m,h,v,y;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:// 如果是 404 頁面就不執行呼叫 api 的動作
if(n=e.app,r=e.store,a=e.route,i=e.query,e.isDev,e.redirect,c=e.$config,!n.router.resolve(a.path.replace("/index.html","")).route.name.startsWith("all")){t.next=4;break}return t.abrupt("return");case 4:
// 同步 cookie 狀態
return r.commit("cookies/SYNC_STORE"),
// 設定目前的語系到cookie
r.commit("cookies/SET_LANG",r.state.i18n.locale),
// 網頁標題、網頁 icon、專案多語系標題、webid、遊戲 icon 廠牌名稱、logo 名稱
r.commit("setVal",{webId:c.WEB_ID,timezone:c.TIMEZONE,projectI18nTitle:c.PROJECT_I18N_TITLE,projectTitle:c.PROJECT_TITLE,gameIconBrandFilename:c.GAME_ICON_BRAND_FILENAME,projectIcon:c.PROJECT_ICON,projectLogoFilename:c.PROJECT_LOGO_FILENAME}),
// 檢查有沒有帶query有沒有type
i.layout&&"nomenu"===i.layout.toLowerCase()?r.commit("control/setUseMenu",!1):i.layout&&"headeronly"===i.layout.toLowerCase()?r.commit("control/setUseHeaderOnly",!0):i.layout&&"betlistonly"===i.layout.toLowerCase()?(r.commit("control/setUseHeaderOnly",!0),r.commit("control/setUseBetListOnly",!0)):(r.commit("control/setUseMenu",!0),r.commit("control/setUseHeaderOnly",!1),r.commit("control/setUseBetListOnly",!1)),(u=i.game||r.getters.gameNo)&&r.commit("cookies/SET_GAME",+u),(s=i.device)&&(
// 設定app版本控制項目
"mobileapp"===s.toLowerCase()&&(r.commit("control/setUseAppCloseWindow",!0),r.commit("control/setHideUserItemsPage",!0),r.commit("control/setHidePrizePage",!0),r.commit("control/setUseAppVipContent",!0)),"webapp"===s.toLowerCase()&&(r.commit("control/setHideUserItemsPage",!0),r.commit("control/setHidePrizePage",!0),r.commit("control/setUseAppVipContent",!0)),"history_member"===s.toLowerCase()&&r.commit("control/setHidePrizePage",!0),"history_rewards"===s.toLowerCase()&&r.commit("control/setHideMemberPage",!0),"history_only"===s.toLowerCase()&&(r.commit("control/setHideMemberPage",!0),r.commit("control/setHidePrizePage",!0)),r.commit("SET_DEVICE",s)),
// 依不同 apiId 調整網頁標題、網頁 icon、專案多語系標題、webid、遊戲 icon 廠牌名稱、logo 名稱
// 印度目前以domain來區分
"IN"===r.state.webId&&location.hostname.includes("jilistar")&&(l=Object(o.a)(202))&&r.commit("setVal",l),
// 站台啟動時的必要資訊
f=[n.i18n.getRemoteLangMessage(n.i18n.locale),n.i18n.changeEelmentUiLocale(n.i18n.locale),r.dispatch("getGameSetting"),r.dispatch("getCurrencyDisplayList")],i.token&&!a.path.includes("repair")&&(r.commit("cookies/SET_GAME_TOKEN",i.token),f.push(r.dispatch("getToken",i.token))),t.next=18,Promise.all(f).catch((function(t){console.log("取得 站台啟動時的必要資訊 發生錯誤，錯誤訊息: ",null==t?void 0:t.Message)}));case 18:
// gtHeader 關閉按鈕 postMessage 是否要使用 query 中 posthost 帶入的數值
i.posthost?r.commit("control/setPostMessageHost",i.posthost):r.commit("control/setPostMessageHost",""),
// 如果有帶 gp=true 隱藏歷程頁的會員選單
i.gp&&r.commit("control/setHideMemberPage",!0),i.sac&&r.commit("cookies/SET_SAC",+i.sac),i.game&&(m=null===(g=r.state.gameSettings)||void 0===g?void 0:g.find((function(t){return t.No===+i.game})),h=null!==(d=null==m||null===(p=m.Id)||void 0===p?void 0:p.toLowerCase())&&void 0!==d?d:"",v=h.startsWith("sss-"),r.commit("setVal",{isSSSSeries:v}),
// TaDaSSS 專用設定
"TADA"===r.state.webId&&v&&(y=Object(o.a)(20002))&&r.commit("setVal",y));case 22:case"end":return t.stop()}}),t)})))).apply(this,arguments)}
/***/
/* harmony default export */e.a=function(t){return a.apply(this,arguments)}},
/***/257:
/***/function(t,e,n){"use strict";
/* harmony import */var r=n(6);
/* harmony import */n(32),n(142);
/* harmony default export */e.a=function(t){t.app;
// onNuxtReady
var e=t.store,n=t.route,o=t.redirect,a=t.$utils;window.onNuxtReady(Object(r.a)(regeneratorRuntime.mark((function t(){var r,o,a;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return window.$nuxt.$loading.finish(),
// 記錄載入結束時間
// store.commit('loading/end', performance.now())
// route.name 會因為 index.html 而有差異，所以使用在 middleware 時記錄的 store.state.pageKey
// store.dispatch('loading/sendLogLoadingTime', `${store.state.pageKey}`)
// 儲存被 iframe 呼叫時的網址
e.commit("setVal",{firstPageUrl:"".concat(location.pathname).concat(location.search).concat(location.hash)}),r=n.query.apiid||0,o=r||e.getters.apiId,t.next=6,e.dispatch("getSwitchOffInfo",o);case 6:
// 禁止使用者縮放處理
document.addEventListener("touchstart",(function(t){t.touches.length>1&&t.preventDefault()}),{passive:!1}),a=0,document.addEventListener("touchend",(function(t){var e=(new Date).getTime();e-a<=300&&t.preventDefault(),a=e}),!1),document.addEventListener("touchmove",(function(t){t.touches.length>1&&t.preventDefault()}));case 10:case"end":return t.stop()}}),t)})))),
// 註冊 postmessage 接收事件
window.addEventListener("message",(function(t){
// client 端串接指令範例：
// 停留在關閉時關閉時最後的頁面，並刷新
// document.querySelector('#webview').contentWindow.postMessage(
// '{"cmd": "refresh", "options": { "stayLatestPage": true } }', '歷程網站host url')
// 回到 iframe 的最初網址
// document.querySelector('#webview').contentWindow.postMessage(
// '{"cmd": "refresh" }', '歷程網站host url')
// 舊的指令，只要魚機跟部分押分機有串接
// document.querySelector('#webview').contentWindow.postMessage('{"refresh": true}', 'https://test-history.jlfafafa3.com')
if(t.origin===a.getGameUrl()){var n,r={},i=t.data;try{r=JSON.parse(i)}catch(t){console.log("parse postmessage receive data to object fail: ",t)}
// 新指令
if("refresh"===r.cmd)null!==(n=r.options)&&void 0!==n&&n.stayLatestPage?
// 只刷新api
window.$nuxt.refresh():
// 回到最初的 iframe 網址
o(e.state.firstPageUrl);
// 舊的指令，等魚機類型都串接完可刪除
// 查看更新畫面指令
r.refresh&&window.$nuxt.refresh()}}))}},
/***/293:
/***/function(t,e){t.exports=function(t){if(!t.webpackPolyfill){var e=Object.create(t);
// module.parent = undefined by default
e.children||(e.children=[]),Object.defineProperty(e,"loaded",{enumerable:!0,get:function(){return e.l}}),Object.defineProperty(e,"id",{enumerable:!0,get:function(){return e.i}}),Object.defineProperty(e,"exports",{enumerable:!0}),e.webpackPolyfill=1}return e};
/***/},
/***/324:
/***/function(t,e,n){"use strict";
/* harmony export (binding) */n.d(e,"a",(function(){return m}));
/* unused harmony export useCertControlUi */
/* harmony import */n(7),n(10),n(8),n(14),n(16)
/* harmony import */;var r=n(5);n(260),n(28),n(15),n(27),n(115),n(64),n(63);function o(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);e&&(r=r.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.push.apply(n,r)}return n}function a(t){for(var e=1;e<arguments.length;e++){var n=null!=arguments[e]?arguments[e]:{};e%2?o(Object(n),!0).forEach((function(e){Object(r.a)(t,e,n[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):o(Object(n)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))}))}return t}
// 預設的 UI 顯示設定：不處理（undefined 表示不更動 UI）
var i={historyPreMoney:void 0,
// 顯示「投注前金額」
historyPostMoney:void 0,
// 顯示「投注後金額」
historyNetAndSpecialAward:!0,
// 顯示「淨值及特別獎項」
historyAccount:!0,
// 顯示「帳戶」
introBullet:void 0,
// 顯示「提示項目」
introBuyBonusItem:void 0,
// 顯示「BuyBonus」
introAutoItem:void 0,
// 顯示「自動玩」
introTurboItem:void 0,
// 顯示「快速」
introTurbo2Item:void 0,
// 顯示「超快速」
introExtraBetItem:void 0},c=new Set([1,2,3,4,5,6,7,8,9,11,12]),u=new Set([6,9,11]),s=new Set([19,20,21]),l=new Set([6,7]),f=new Set([6,7]),g=new Set([3,4,6,7,8,12]),d=new Set([3,4,6,7,8,12]),p=[
// 特例：certArea = 6 且 certId = 1，顯示提示項目
{match:function(t,e){return 6===t&&1===e},setting:{introBullet:!0}},
// certArea 為 1~9、11~12，顯示投注後金額，隱藏投注前金額，部分顯示提示項目
{match:function(t,e){return c.has(t)},setting:function(t){return{historyPreMoney:!1,historyPostMoney:!0,introBullet:!!u.has(t)||void 0,introBuyBonusItem:!l.has(t)&&void 0,introAutoItem:!f.has(t)&&void 0,introTurboItem:!g.has(t)&&void 0,introTurbo2Item:!d.has(t)&&void 0}}},
// certArea = 12，關閉淨值及特別獎項、額外壓注
{match:function(t,e){return 12===t},setting:{historyNetAndSpecialAward:!1,introExtraBetItem:!1,historyAccount:!1}},
// certArea = 10，顯示投注前金額、投注後金額與提示項目
{match:function(t,e){return 10===t},setting:{historyPreMoney:!0,historyPostMoney:!0,introBullet:!0}},
// certArea = 15 或 17~21，顯示投注前金額與投注後金額，有些顯示提示項目
{match:function(t,e){return 15===t||t>=17&&t<=21},setting:function(t){return{historyPreMoney:!0,historyPostMoney:!0,introBullet:!!s.has(t)||void 0}}}],m=function(){// 根據實際需求設定最大值
for(var t=new Map,e=function(t,e){return"".concat(t,"-").concat(e)},n=0;n<=21;n++)for(var r=0;r<=1;r++){for(var o=a({},i),c=0,u=p;c<u.length;c++){var s=u[c];if(s.match(n,r)){var l="function"==typeof s.setting?s.setting(n,r):s.setting;o=a(a({},o),l)}}
// 主鍵：certArea + certId
t.set(e(n,r),o);
// 備援鍵：只有 certArea，當 certId 不存在時使用
var f="".concat(n,"-null");t.has(f)||t.set(f,o)}return t};
// 用 Set 儲存要對應的 certArea 值
},
/***/388:
/***/function(t,e,n){"use strict";
/* harmony default export */e.a=function(){for(var t=[8,100,995,996,997,998,10894,10928],e=105;e<=301;e++)t.push(e);return t}},
/***/389:
/***/function(t,e,n){"use strict";
/* harmony default export */e.a=function(){return[1071,1072,1073,1074,1075]}},
/***/39:
/***/function(t,e){var n;
// This works in non-strict mode
n=function(){return this}();try{
// This works if eval is allowed (see CSP)
n=n||new Function("return this")()}catch(t){
// This works if the window reference is available
"object"==typeof window&&(n=window)}
// g can still be undefined, but nothing to do about it...
// We return undefined, instead of nothing here, so it's
// easier to handle this case. if(!global) { ...}
t.exports=n},
/***/52:
/***/function(t,e,n){"use strict";
// EXPORTS
n.d(e,"d",(function(){/* binding */return w})),n.d(e,"a",(function(){/* binding */return _})),n.d(e,"c",(function(){/* binding */return O}));
// UNUSED EXPORTS: screamingSnakeCase, getUserSubDomain, getCaseInsensitiveProperty
// EXTERNAL MODULE: ./node_modules/.pnpm/@babel+runtime@7.25.4/node_modules/@babel/runtime/helpers/esm/defineProperty.js
var r=n(5),o=n(17),a=n(9),i=(n(35),n(24),n(20),n(25),n(15),n(49),n(91),n(26),n(18),n(433),n(186),n(115),n(28),n(27),n(22),n(260),n(8),n(7),n(10),n(14),n(16),n(3)),c=n(89),u=n.n(c),s=n(390),l=n(185),f=n(44),g=n(114),d=n.n(g),p=n(79),m=function(){return["192"]},h=["zh-TW","zh-CN","en-US"],v=new Map([["831",["zh-TW","zh-CN","en-US","th-TH","vi-VN","id-ID","my-MM","ja-JP","hi-IN","ta-IN","ms-MY","ko-KR","bn-IN","es-AR","pt-BR","pt-PT","it-IT","ro-RO","tr-TR","ru-RU"]]]);
// EXTERNAL MODULE: ./node_modules/.pnpm/@babel+runtime@7.25.4/node_modules/@babel/runtime/helpers/esm/slicedToArray.js + 1 modules
/**
 * 取得道具卡大圖要使用的語系
 * @param {string} gameId fishNo 內的 3 碼遊戲編號
 * @param {string} lang 目前語系
 * @param {string} defaultLang 該遊戲沒備此語系圖時要退回的語系
 * @returns {string} 圖片實際使用的語系
 */
function y(t,e){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:"en-US";return(v.get(t)||h).includes(e)?e:n}
// EXTERNAL MODULE: ./setting/useGameSymbolStyle.js
var b=n(57);
// CONCATENATED MODULE: ./plugins/utils.js
function I(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);e&&(r=r.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.push.apply(n,r)}return n}function j(t){for(var e=1;e<arguments.length;e++){var n=null!=arguments[e]?arguments[e]:{};e%2?I(Object(n),!0).forEach((function(e){Object(r.a)(t,e,n[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):I(Object(n)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))}))}return t}
/**
 * 轉換字串為 screamingSnakeCase
 * @param {string} str - 字串
 */function P(t){return Object(f.c)(t).toLocaleUpperCase()}
/**
 * 取得JWT內容
 * @param {string} _strToken - JWT Token
 */function w(t){if(S(t)>0){var e=t.split(".")[1].replace(/-/g,"+").replace(/_/g,"/"),n=decodeURIComponent(atob(e).split("").map((function(t){return"%"+("00"+t.charCodeAt(0).toString(16)).slice(-2)})).join(""));return JSON.parse(n)}return null}
/**
 * 計算字串的長度
 * @param {string} _strValue - 輸入字串
 */function S(t){
/**
 * null or undefined 字串轉為 ''
 * @param {string} _strValue - 輸入字串
 */
return function(t){return null==t?"":t.toString()}
/**
 * 取得使用者當下的 subdomain
 * @param {object} req - nuxt context req 物件
 */(t).length}
/**
 * 替換正確的 api 網址，因廠商會使用不同的domain進來
 * 要依不同的 domain 去呼叫
 * @param {object} context - nuxt context
 * @param {string} originalApiUrl - 原本的設定檔 url
 */
function _(t,e){var n,r,o=(r=(n=location.hostname).indexOf(":"),/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/.test(n)?r>-1?n.substring(0,r):n:r>-1?n.substring(n.indexOf(".")+1,r):n.substring(n.indexOf(".")+1)),a=e;
// 如果是 ip 就使用預設的 api url
if(o&&!/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/.test(o)){var i=e.substring(0,e.indexOf("."));a="".concat(i,".").concat(o)}
// 如果是開發環境就使用預設的 api url
return a}
/**
 * 判斷是否為後端api回傳的錯誤物件格式
 * @param {object} apiReturnObj - api 回傳的物件
 */function O(t){return"object"===Object(a.a)(t)&&void 0!==(null==t?void 0:t.Code)&&0!==(null==t?void 0:t.Code)}
/**
   * 取得不分大小寫的物件屬性
   * @param { object } obj 物件
   * @returns { object } 不分大小寫屬性的物件
   */function N(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{},e={};return Object.entries(t).forEach((function(t){var n=Object(o.a)(t,2),r=n[0],a=n[1];e[r.toLowerCase()]=a})),e}
/* harmony default export */e.b=function(t,e){var n=t.app,r=t.store,o=t.$config,a=(t.req,t.query);
/**
   * 取得遊戲名稱
   * @param {string, Number } gameIdOrNo 遊戲 id 或遊戲編號
   * @param {string} lang 語系
   * @returns
   */
/**
   * 取得遊戲ID
   * @param {int} gameNo - 遊戲編號
   */
function c(t){var e=r.state.gameSettings.find((function(e){return e.No===t}));return e?e.Id:""}
/**
   * 取得遊戲No
   * @param {string} gameId - 遊戲ID
   */function g(t){var e=r.state.gameSettings.find((function(e){
// 全大寫跟全小寫的gameId轉出來的字串不太相同，轉2次確保一致性
return Object(f.a)(Object(f.a)(e.Id))===Object(f.a)(Object(f.a)(t))}));return e?e.No:""}
/**
   * 格式化字串
   * @param {string} format - 將含有 {0} {1} {2} 的字串帶入變數
   */
/**
   * 取得數字逗號格式(數字加上每三位,號，小數點後只保留 exponent 位)
   * @param {string} _strDigital - 傳入數字
   * @param {string} exponent - 小數點位數
   * @param {string} forceExponent - 是否強制顯示小數點後的數字
   */
function h(t,e){var n=arguments.length>2&&void 0!==arguments[2]&&arguments[2],o=
/**
   * 根據語言設置確定小數點與千位分隔符號的適當符號。
   *
   * 對於特定語言（在changeLangList中指定），小數點和千位分隔符號
   * 可以根據thousandThMode設置進行交換：
   * - 模式0：對指定語言使用逗號作為小數點，句點作為千位分隔符
   * - 模式1：使用標準格式（逗號為千位分隔符，句點為小數點）
   * - 模式2：始終交換符號（句點為千位分隔符，逗號為小數點）
   *
   * @returns {Object} 包含確定符號的對象
   * @returns {string} returns.commaSymbol - 用於千位分隔符的符號
   * @returns {string} returns.pointSymbol - 用於小數點的符號
   */
function(){var t=",",e=".";
// 千分位符號
// 專案新需求，特定語系時小數點與千分位要相反,
// 空字串:照目前設定的 changeLangList 語系,
// 'en-US':正常,
// 'vi-VN':相反
return""===r.getters.thousandThMode&&["vi-VN","es-AR","pt-BR","pt-PT","it-IT","sv-SE","de-DE","da-DK","ro-RO","fr-FR","gr-GR","nl-NL","tr-TR"].includes(r.getters.lang)&&(t=".",e=","),"vi-VN"===r.getters.thousandThMode&&(t=".",e=","),{commaSymbol:t,pointSymbol:e}}(),a=o.commaSymbol,i=o.pointSymbol;isNaN(e)&&(e=2);var c="";if(S(t)>0){
// 後端吐出來的小數點，不會因客製調整而改變
var u=null;(u="string"==typeof t?t.split("."):t.toString().split("."))[0]=u[0].replace(/\B(?=(\d{3})+(?!\d))/g,a),
// 處理小數點，超過 exponent 位數刪掉，不足且 forceExponent 補 0
u.length>1&&(u[1].length>e&&(u[1]=u[1].substring(0,e)),u[1].length<e&&n&&(u[1]=u[1].padEnd(e,"0"))),
// 如果是整數且 forceExponent 要強制顯示小數點
1===u.length&&n&&(u[1]="0".repeat(e)),c=u.length>1&&!u[1]?u[0]:u.join(i)}return c}
/**
   * 日期時間格式化
   * @param {string} originalTime - 傳入數字
   * @returns {string} 格式化的日期時間
   */function I(t){if(t<0)return"N/A";if(null!=t||""===t){var e=n.$dayjs(t);return"".concat(e.format("YYYY/MM/DD HH:mm:ss")," (").concat(O(e),")")}return"N/A"}
/**
   * 日期格式化
   * @param {string} originalTime - 傳入數字
   * @returns {string} 格式化的日期
   */function _(t){return t<0?"N/A":null!=t||""===t?n.$dayjs(t).format("YYYY/MM/DD"):"N/A"}
/**
   * 時間格式化
   * @param {string} originalTime - 傳入數字
   * @returns {string} 格式化的時間
   */
/**
   * 取得時區字串
   * @param {dayjs} dayjs - dayjs 物件
   * @param {Boolean} displayZero - 是否顯示 +0
   * @returns {string} 時區字串 ex: GMT+7
   */
function O(t){var e=arguments.length>1&&void 0!==arguments[1]&&arguments[1],n=t.utcOffset();return n>0?"GMT+".concat(Math.abs(n/60)):n<0?"GMT-".concat(Math.abs(n/60)):"GMT".concat(e?"+0":"")}var L=new Map([["tx",["zh-CN","zh-TW","vi-VN"]],["lj",["zh-CN","zh-TW","pt-BR"]],["lj2",["zh-CN","zh-TW","pt-BR"]],["lt",["zh-CN","zh-TW","pt-BR"]],["lm",["zh-CN","zh-TW","pt-BR"]],["col",["zh-CN","zh-TW","es-AR"]],["clb",["zh-CN","zh-TW","pt-BR","tr-TR"]],["yg500",["zh-CN","zh-TW","pt-BR"]],["lj500",["zh-CN","zh-TW","pt-BR"]],["bt",["zh-CN","zh-TW","pt-BR"]],["frogdash10000",["zh-CN","zh-TW","tr-TR"]],["cc4x4uf",["zh-CN","zh-TW","pt-BR"]],["tlbp",["zh-CN","zh-TW","pt-BR"]],["ufafg5",["zh-CN","zh-TW","th-TH"]],["ufafoa",["zh-CN","zh-TW","th-TH"]],["lm2",["zh-CN","zh-TW","pt-BR"]],["hrf",["zh-CN","zh-TW","pt-BR"]],["lju",["zh-CN","zh-TW","pt-BR"]],["ltn2",["zh-CN","zh-TW","pt-BR"]]]);function T(t,e){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:"en-US";return(L.get(t)||["zh-CN","zh-TW"]).includes(e)?e:n}var E=new Map([["tada",new Set(["cashballoon"])],["jili",new Set(["cashballoon"])]]),C=new Map([["tada","_tada"],["jili","_jili"]]),k=new Map([["plinko",function(t){var e=t.brand,n=t.apiId;return"tada"===e||3===n?"_tada":""}]]);
/**
   * 依遊戲、品牌與條件計算需附加的品牌後綴字串
   *
   * 規則說明：
   * 1. 若該遊戲存在特例規則（specialGameIconAppendBrandNameRules），則優先套用
   * 2. 一般情況下，依品牌與遊戲對應關係套用後綴
   * 3. 換皮 icon（style icon）目前不套用品牌後綴
   *
   * @param {string} gameId
   *   遊戲代碼（例如：plinko、cashballoon）
   *
   * @param {string} brand
   *   品牌代碼（例如：tada、jili）
   *
   * @param {number} apiId
   *   API 平台代碼，供特例規則判斷使用
   *
   * @param {boolean} [isStyleIcon=false]
   *   是否為換皮 icon
   *   - true  ：使用換皮 icon，不套用品牌後綴
   *   - false ：使用一般 icon，依品牌與遊戲對應關係套用後綴
   *   說明：若未來換皮 icon 需套用品牌後綴，
   *         可直接移除此判斷，不需調整其他邏輯
   *
   * @returns {string}
   *   回傳需附加的品牌後綴字串，若無則回傳空字串
   */
function x(t,e,n){var r=arguments.length>3&&void 0!==arguments[3]&&arguments[3],o="";
// 處理品牌要顯示什麼
if(k.has(t))o=k.get(t)({brand:e,apiId:n});else if(!r&&E.has(e)){E.get(e).has(t)&&(o=C.get(e)||"")}return o}
/**
   * 取得遊戲 icon 網址
   * @param {number} gameId
   * @param {number} iconType
   * @param {string} lang
   */
/**
   * 取得貨幣顯示
   * @param {number} currencyNo 幣別編號
   * @param {number} value 數值
   * @param {number} customApiId 自訂apiid不使用vuex中的apiid
   * @param {number} forceExponent 是否要強制指定顯示幾個小數位數
   * @returns {string} 貨幣顯示字串
   */
function R(t,e,n,o,a){var i="",c=1,u=2,s=r.state.currencyDisplayList,l=r.getters;
// 使用自訂的幣別符號
if(
// 讀 token 設定
u=l.exponent,c=l.unit,i=l.currencySymbol,
// 是否要強制指定顯示幾個小數位數
null!=o&&(u=o),null!=t&&null!=s&&s.length>0){var f=s.find((function(e){return e.No===t}));f&&(i=null!=f.Symbol?f.Symbol+" ":"",c=f.Unit)}var g="",d="";
// 阿拉伯符號要加 ‎ 避免變成 right to left
return e<0?(g="-",d=(e/c*-1).toString()):(g="",d=(e/c*1).toString()),a?i+"‎"+g+z(d,u):i+"‎"+g+h(d,u)}
/**
     * 取得貨幣顯示
     * @param {number} value 數值
     * @param {number} customApiId 自訂apiid不使用vuex中的apiid
     * @param {number} forceExponent 是否要強制指定顯示幾個小數位數
     * @returns {string} 貨幣顯示字串
     */
/**
   * 取得魚種編號的涵意
   * @param {string} fishNo 魚種編號
   * @returns {object} 分析後的物件
   */
function M(t){var e=t+"";// 序列號 (2 碼) 剩餘的號碼
return 7===e.length?{type:e.substring(0,1),gameId:e.substring(1,4),starLevel:e.substring(4,5),cardSerialNo:e.substring(5)}:{}}
/**
   * 判斷魚機卡片是否為例外
   * @param {array} fishCardExceptionList 例外gameId清單
   * @param {string} gameId 遊戲編號
   * @returns {boolean} true or false
   */function A(t,e){var n=!1;try{n=t.includes(e)}catch(t){n=!1}return n}
/**
   * 取得魚機卡片圖片路徑
   * @param {string} fishNo 魚種編號
   * @param {string} lang 語系
   * @returns {string} 圖片路徑
   */i.default.filter("commaFormat",(function(t){return h(t)})),
/*
   * 時間 Format
   */
i.default.filter("timeFormat",(function(t){return I(t)})),
/*
   * 日期字串只取前10碼(yyyy-MM-dd)
   */
i.default.filter("date",(function(t){return _(t)})),
/*
   * 日期字串取前19碼(yyyy-MM-dd HH:mm:ss)
   */
i.default.filter("datetime",(function(t){return I(t)}));
// 魚機系列共用魚種編號（圖檔統一放在 /images/gamehistory/fishshare）
var D=[10001,10002,10003,10004,10005,10006,10007,10008,10009,10010,10011,10012];
/**
   * 取得魚機魚種圖片路徑
   * 共用魚種且未被遊戲覆蓋時讀 fishshare，否則讀遊戲自己的資料夾
   * @param {string} gameId 遊戲id
   * @param {number} fishNo 魚種編號
   * @param {Array<number>} overrideShareFishList 使用遊戲自己資料夾圖檔的共用魚種編號
   * @returns {string} 圖片路徑
   */
/**
   * 將數字加上KMBT 的轉換，1,000 -> 1k，1,000,000 -> 1m，1,000,000,000 -> 1b，1,000,000,000,000 -> 1t
   * @param {string} number
   * @param {number} toFixedNum 取到小數第幾位 default: 0
   * @param {Object} enable 啟用狀態 default: { k: true, m: true, b: true, t: true }
   * @returns 格式化後字串
   */
function z(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0,n=arguments.length>2?arguments[2]:void 0,r=d()(t),o="",a=r.lt(0),i=Object(p.a)(n,{k:!0,m:!0,b:!0,t:!0});return a&&(r=r.abs()),r.gte(1e12)&&i.t?(r=parseFloat(r.div(1e12).toFixed(e,0)),o="T"):r.gte(1e9)&&i.b?(r=parseFloat(r.div(1e9).toFixed(e,0)),o="B"):r.gte(1e6)&&i.m?(r=parseFloat(r.div(1e6).toFixed(e,0)),o="M"):r.gte(1e3)&&i.k&&(r=parseFloat(r.div(1e3).toFixed(e,0)),o="K"),a&&(r*=-1),h(r.toString(),e)+o}
/**
  * 將數字依印尼幣在地習慣轉換為 rb / jt / M 格式。
  *
  * 單位對應規則（印尼在地用法）：
  * - rb：ribu（千，1,000）
  * - jt：juta（百萬，1,000,000）
  * - M ：miliar（十億，1,000,000,000）
  *
  * 不使用 K / B / T，並以 M 為最大顯示單位。
  * 轉換時會以「可啟用的最大單位」為優先，
  * 若未啟用該單位，則會往下嘗試次一層級。
  *
  * @param {string|number} number
  *  要格式化的數值，可為字串或數字，內部以 Big.js 處理以避免浮點誤差。
  *
  * @param {number} [toFixedNum=0]
  *  小數位數，會在單位轉換後套用 toFixed。
  *
  * @param {Object} [inputEnable]
  *  各印尼幣單位啟用設定，未傳入時預設全開。
  *
  * @param {boolean} [inputEnable.rb=true]
  *  是否啟用 rb（千）單位。
  *
  * @param {boolean} [inputEnable.jt=true]
  *  是否啟用 jt（百萬）單位。
  *
  * @param {boolean} [inputEnable.m=true]
  *  是否啟用 M（十億）單位。
  *
  * @returns {string}
  *  格式化後的字串，會保留原始正負號，並加上對應單位後綴。
  *
  * @example
  * formatNumberIDR(950)                // "950"
  * formatNumberIDR(1500)               // "2rb"
  * formatNumberIDR(12500, 1)           // "12.5rb"
  * formatNumberIDR(1000000)            // "1jt"
  * formatNumberIDR(15800000, 1)        // "15.8jt"
  * formatNumberIDR(1000000000)         // "1M"
  * formatNumberIDR(-12500000, 1)       // "-12.5jt"
  * formatNumberIDR(1500, 0, { rb: false }) // "1500"
  */function B(t,e,n){return e}function $(t){var e=N(a),n=e.custom;
// 廠商自定義樣式
if(null!=Object(b.d)(t,n,b.a))return"".concat(b.a,"-").concat(n);
// 節慶樣式
var o=e.festival;if(null!=Object(b.d)(t,o,b.b))return"".concat(b.b,"-").concat(o);
// 舊規格樣式
var i=e.symbolstyle||e.style||r.state.style.default;if(i){var c=parseInt(i,10),u=c>=100?b.a:b.b,s=u===b.a?(c/100).toString():i;if(null!=Object(b.d)(t,s,u))return"".concat(u,"-").concat(s)}return""}var G={safeLen:S,parseJWT:w,getGameName:function(t,e){var o=/^\d+$/.test(t)?c(t):t,a=g(o);if(S(o)>0){var i="",u="";
// plinko || cockfight 在泰版及 tada 有不同遊戲名稱，需特殊處理
"plinko"!==o.toLowerCase()&&"cockfight"!==o.toLowerCase()||"tada"!==r.state.gameIconBrandFilename&&3!==r.getters.apiId||(i="_tada");var s=$(a);return""!==s&&(u="_"+P(s)),n.i18n.te("i18_Game".concat(P(o.toUpperCase())).concat(i).concat(u),"en-US")?e?n.i18n.t("i18_Game".concat(P(o.toUpperCase())).concat(i).concat(u),e):n.i18n.t("i18_Game".concat(P(o.toUpperCase())).concat(i).concat(u)):e?n.i18n.t("i18_Game".concat(P(o.toUpperCase())).concat(i),e):n.i18n.t("i18_Game".concat(P(o.toUpperCase())).concat(i))}return""},getGameId:c,getGameNo:g,stringFormat:function(t){var e=Array.prototype.slice.call(arguments,1);return t.replace(/{(\d+)}/g,(function(t,n){return void 0!==e[n]?e[n]:t}))},formatComma:h,formatDateTime:I,formatDate:_,formatTime:function(t){return t<0?"N/A":null!=t||""===t?n.$dayjs(t).format("HH:mm:ss"):"N/A"},getTimeZoneString:O,getGameIconUrl:function(t,e,n){var o=e||3,a=Object(f.a)(t),i=T(a,n),c=x(a,r.state.gameIconBrandFilename,r.getters.apiId);return"/images/gamehistory/".concat(a,"/icon").concat(o,"/icon_").concat(i).concat(c,".png")}
/**
   * 取得遊戲 icon 網址
   * @param {number} gameId
   * @param {number} iconType
   * @param {string} lang
   * @param {string} style
   */,getGameIconUrlBySymbolStyle:
/**
   * 取得遊戲 icon 網址
   * @param {number} gameId
   * @param {number} symbolStyle
   * @param {string} lang
   */
function(t,e,n,o){var a=e||3,i=Object(f.a)(t),c=T(i,n),u=x(i,r.state.gameIconBrandFilename,r.getters.apiId,!0);return"/images/gamehistory/".concat(i,"/symbol-style-").concat(o,"/icon").concat(a,"/icon_").concat(c).concat(u,".png")}
/**
   * 取得css變數或設定css變數
   * @param {string} name
   * @param {string} value
   */,getGameIconUrlByStyle:function(t,e,n,o){var a=e||3,i=Object(f.a)(t),c=T(i,n),u=x(i,r.state.gameIconBrandFilename,r.getters.apiId,!0);return"/images/gamehistory/".concat(i,"/style-").concat(o,"/icon").concat(a,"/icon_").concat(c).concat(u,".png")},getCurrencyDisplay:R,getJwtCurrencyDisplay:function(t,e,n,r){return R(null,t,0,n,r)}
/* 取得押注倍率貨幣顯示 (將數值乘以押注倍率)
   * @param {number} currencyNo 幣別編號
   * @param {number} value 數值
   * @returns {number}} 乘以押注倍率後的數值
   */,getCurrencyRatioDisplay:function(t,e){var n=r.state.currencyDisplayList,o=r.getters.ratio,a=e;if(null!=n&&n.length>0){var i=n.find((function(e){return e.No===t}));if(i&&(o=i.Ratio),o>0){
// 避免相乘時浮點數精確度問題，先乘以 10 的 n 次方避免結果為小數再除回來
var c=Math.pow(10,4);a=e*(o*c)/c}return a}}
/**
   * 取得特殊獎項圖片路徑
   * @param {string} type 獎項類型
   * @param {string} lang 語系
   * @returns {string} true or false
   */,cssVar:function(t,e){return"-"!==t[0]&&(t="--"+t),// allow passing with or without --
(e||null===e)&&document.documentElement.style.setProperty(t,e),getComputedStyle(document.documentElement).getPropertyValue(t)},isEmpty:
/**
   * 是否為空物件
   * @param {object} obj 物件
   * @returns {boolean} true or false
   */
function(t){return t&&0===Object.keys(t).length&&t.constructor===Object}
/**
   * 快速設定物件
   * @param {object} obj 物件
   * @param {string | array} path 路徑
   * @param {any} val 數值
   * @returns {object} 新物件
   */,merge:u.a,mergeWithOverwriteArray:Object.assign((function(t,e){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{};return u()(t,e,j({arrayMerge:B},n))}),u.a,{all:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{};return u.a.all(t,j({arrayMerge:B},e))}}),klona:l.a,deepset:function(t,e,n){var r=Object(l.a)(t);return Object(s.a)(r,e,n),r},getPrizeTypeImagePath:function(t,e,n){
// 相容舊規格
if(null==t)return"";var r="zh-TW"===e||"zh-CN"===e?e:"en-US",o="/images/prize/",a="";a=691===n?"Card_Rich":n>=1e4||1002===n?"Card_TaDa":"Card_Jili";
// 改寫設定，太多種類條件
var i={ItemCard:"".concat(o).concat(a,".png"),SpecialPrize:"".concat(o,"SpecialPrize.png"),SpecialPrizeNoDetail:"".concat(o,"SpecialPrize.png"),Buy:"".concat(o,"Buy.png"),MiniJackpot:"".concat(o,"jp/").concat(r,"/mini_jackpot.png"),MajorJackpot:"".concat(o,"jp/").concat(r,"/major_jackpot.png"),GrandJackpot:"".concat(o,"jp/").concat(r,"/grand_jackpot.png"),MiniJackpot4jp:"".concat(o,"4jp/").concat(r,"/mini_jackpot.png"),MinorJackpot4jp:"".concat(o,"4jp/").concat(r,"/minor_jackpot.png"),MajorJackpot4jp:"".concat(o,"4jp/").concat(r,"/major_jackpot.png"),GrandJackpot4jp:"".concat(o,"4jp/").concat(r,"/grand_jackpot.png"),JackpotLegendMiniJackpot:"".concat(o,"/jpl/mini_jackpot.png"),JackpotLegendMinorJackpot:"".concat(o,"/jpl/minor_jackpot.png"),JackpotLegendMajorJackpot:"".concat(o,"/jpl/major_jackpot.png"),JackpotLegendGrandJackpot:"".concat(o,"/jpl/grand_jackpot.png"),TaDaJackpotMini:"".concat(o,"/tadajp/mini_jackpot.png"),TaDaJackpotMinor:"".concat(o,"/tadajp/minor_jackpot.png"),TaDaJackpotMajor:"".concat(o,"/tadajp/major_jackpot.png"),TaDaJackpotGrand:"".concat(o,"/tadajp/grand_jackpot.png"),ExtraBet:"".concat(o,"extrabet.png"),ExtraBuy:"".concat(o,"extrabuy.png"),ExtraFreeGame:"".concat(o,"extrafreegame.png"),MustHitBy:"".concat(o,"MustHitBy.png"),FreeSpin:"".concat(o,"freespin.png"),FreeSpinFreeGame:"".concat(o,"freespinfreegame.png"),Trial:"".concat(o,"trial.png"),TrialEnd:"".concat(o,"trial.png"),TrialFreeGame:"".concat(o,"trialfreegame.png"),SpinBonus:"".concat(o,"spinbonus.png"),SpinBonus2:"".concat(o,"spinbonus2.png"),HotHand:"".concat(o,"hothand.png"),"":""},c=i[t];
// 相容舊規格, 如果上述規則都找不到套用 SpecialPrize
return null==i[t]&&(c="".concat(o,"SpecialPrize.png")),c}
/**
   * 取得魚機特殊獎項圖片路徑
   * @param {string} type 獎項類型
   * @param {string} lang 語系
   * @param {number} apiId ApiID
   * @param {string} gameId 遊戲類型，保留參數，for瘋狂砲手類的例外未來使用
   * @returns {string} true or false
   */,getFreeSpinImagePath:function(t,e,n,r){
// 相容舊規格
if(null==t)return"";
// 遊戲特殊不顯示情況
if("FreeSpin"===t&&("shooting6"===r||"sss-s6"===r))return"";
// 暫時沒有英文以外的語系
// const iconLang = lang === 'zh-CN' ? lang : 'en-US'
var o="/images/prize/fish/",a="";a=691===n?"Card_Rich":n>=1e4||1002===n?"Card_TaDa":"Card_Jili";
// 改寫設定，太多種類條件
var i={FreeSpin:"".concat(o,"/en-US/FreeSpin.png"),BonusPig:"".concat(o,"BonusPig.png"),SpinBonus:"".concat(o,"BonusSpin.png"),ItemCard:"".concat("/images/prize/").concat(a,".png"),Buy:"".concat(o,"Buy.png"),ExtraBet:"".concat(o,"extrabet.png"),"":""}[t];return null==i&&(i=""),i},parseFishNo:M,isFishCardException:A,getFishCardImagePath:function(t,e,n){var o,a,i,c,u,s="",l=M(t),f=l.type,g=l.gameId,d=l.starLevel,p=l.cardSerialNo,h=m();
// 語系一定要在檔名算完之後才決定：isNeedUnifyGameId 會把檔名的遊戲代號換成 000，
// 那是全魚機共用的圖、站上只備繁中／簡中／英文，不能套該遊戲的擴充語系清單。
// size === 'small' 小圖示歷程也已經不使用了，之後可以拿掉小圖的處理
if(
// 卡片名稱，預設以 fishNo 做為名稱，符合特殊規則再加上額外處理
o=t+"",
// 留存炮
"1"===f&&("small"===n?(c=!0,u=!0,"8"===d&&(a=!0)):(
// 大圖示改為依不同星等顯示不同圖示
c=!1,u=!0,a=!1),A(h,g)&&(c=!1,u=!1)),
// 鳳凰 & 新年禮包
"2"===f&&(i=!0,c=!0),
// 雪怪(042 & 212)
"2"===f&&["042","212"].includes(g)&&"01"===p&&(i=!1),
// 冰凍卡
"3"===f&&(i=!0,c=!0),
// 獎金卡
"4"===f&&(i=!0,c=!0,A(h,g)&&(i=!1)),
// 免費子彈
"5"===f&&(i=!0,c=!1,u=!0),
// 免費激光炮
"6"===f&&(i=!0,c=!1,u=!0),
// 三種顏色的鑽頭
"7"===f&&["01","02","03"].includes(p)&&(i=!0),o=(
// 依上述規則重新排列卡片名稱
o=a?"G_":"")+f+(i?"000":g),o+=c?"1":d,o+=u?"01":p,"small"===n)
// 小圖只備簡中、英文
s=["zh-TW","zh-CN"].includes(e)?"zh-CN":"en-US";else if(i)
// 共用圖(X000NNN)：維持原本的三語系收斂
s=y(null,e);else{
// 該遊戲專屬的圖(檔名帶著 gameId)才看 setting/fishCardLangs 有沒有登錄多語系。
// 歷程列表會先把語系收斂成 zh-CN／en-US（那個值還要共用返利圖、JP 圖的路徑），
// 有備多語系圖的遊戲要用實際語系，所以直接讀 store，不受呼叫端收斂結果影響
// （比照 getGameIconUrl 讀 store 的作法）
var b=
/**
 * 該遊戲是否有備多語系道具卡圖
 * @param {string} gameId fishNo 內的 3 碼遊戲編號
 * @returns {boolean}
 */
function(t){return v.has(t)}(g)?r.getters.lang:e;s=y(g,b)}return"/images/fishcard".concat(n?"/"+n:"","/").concat(s,"/").concat(o,".png")},getFishImagePath:function(t,e){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:[];return D.includes(e)&&!n.includes(e)?"/images/gamehistory/fishshare/".concat(e,".png"):"/images/gamehistory/".concat(t,"/").concat(e,".png")}
/**
   * 取得魚機卡片名稱
   * @param {string} fishNo 魚種編號
   * @param {string} lang 語系
   * @returns {string} 卡片名稱
   */,getFishCardNameId:function(t,e){var n,r,o,a=t,i=M(t),c=i.type,u=i.gameId,s=i.starLevel,l=i.cardSerialNo,f=m();
// 一般遊戲卡
return"1"===c&&(o=!0,A(f,u)&&(o=!1)),
// 新年禮包
"2"===c&&(n=!0,r="1"),
// 雪怪(042 & 212)
"2"===c&&["042","212"].includes(u)&&"01"===l&&(n=!1),
// 冰凍卡
"3"===c&&(n=!0),
// 獎金卡
"4"===c&&(n=!0,A(f,u)&&(n=!1)),
// 免費子彈
"5"===c&&(n=!0,o=!0,s>"4"&&(r="8")),
// 免費激光炮
"6"===c&&(n=!0,o=!0,s>"4"&&(r="8")),
// 三種顏色的鑽頭
"7"===c&&["01","02","03"].includes(l)&&(n=!0),a=c+(n?"000":u),a+=r||s,"i18_FishingCardName_"+(a+=o?"01":l)}
/**
   * 取得魚機卡片描述
   * @param {string} fishNo 魚種編號
   * @param {string} lang 語系
   * @returns {string} 卡片描述
   */,getFishCardDescId:function(t,e){var n,r,o,a=t,i=M(t),c=i.type,u=i.gameId,s=i.starLevel,l=i.cardSerialNo,f=m();
// 一般遊戲卡
return"1"===c&&(r=!0,o=!0),
// 新年禮包
"2"===c&&(n=!0,r=!0),
// 雪怪(042 & 212)
"2"===c&&["042","212"].includes(u)&&"01"===l&&(n=!1),
// 冰凍卡
"3"===c&&(n=!0),
// 獎金卡
"4"===c&&(n=!0,A(f,u)&&(n=!1)),
// 免費子彈
"5"===c&&(n=!0,r=!0,o=!0),
// 免費激光炮
"6"===c&&(n=!0,r=!0,o=!0),
// 三種顏色的鑽頭
"7"===c&&["01","02","03"].includes(l)&&(n=!0,r=!0,o=!0),a=c+(n?"000":u),a+=r?"1":s,"i18_FishingCardDesc_"+(a+=o?"01":l)},imageUrl:function(t){return t+"?"+o.TIMESTAMP},getGameUrl:function(){var t="";
// 如果有帶 query posthost 的話就使用它
if(r.state.control.postMessageHost)return t="https://"+r.state.control.postMessageHost;
// GLI 遊戲網址與其他版本不同，設定在環境變數中
if(o.GAME_URL)t=o.GAME_URL;else{var e=location.hostname;
// 印度 webapp 特規
t="webapp"===r.state.device&&"IN"===r.state.webId?"https://"+e.replace("history.","www."):"https://"+e.replace("www.","wbgame.").replace("history.","wbgame.")}return t}
/**
   * 將 BonusArray 數字加上 k 或 m 的轉換，1,000,000 -> 1m，1,000 -> 1k
   * @param {string} number
   * @returns 格式化後字串
   */,screamingSnakeCase:P,formatNumberKM:function(t){var e=d()(t),n="";return e.gte(1e6)?(e=e.div(1e6),n="m"):e.gte(1e3)&&(e=e.div(1e3),n="k"),h(e.toString())+n},formatNumberKMBT:z,formatNumberIDR:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0,n=arguments.length>2?arguments[2]:void 0,r=d()(t),o="",a=r.lt(0),i=Object(p.a)(n,{rb:!0,jt:!0,m:!0});return a&&(r=r.abs()),r.gte(1e9)&&i.m?(r=parseFloat(r.div(1e9).toFixed(e,0)),o="M"):r.gte(1e6)&&i.jt?(r=parseFloat(r.div(1e6).toFixed(e,0)),o="jt"):r.gte(1e3)&&i.rb&&(r=parseFloat(r.div(1e3).toFixed(e,0)),o="rb"),a&&(r*=-1),h(r.toString(),e)+o}
/**
   * 將數字無條件捨去至小數點第二位
   * @param {Number} number
   * @param {Number} toFixedNum
   * @returns 格式化後字串
   */,getCaseInsensitiveProperty:N,getItemCardi18nId:
/**
   * Get ItemCard i18n id.
   * @param {number} apiId
   * @returns i18n id
   */
function(t){return 691===t?"i18_ItemCard_Rich":t>=1e4||1002===t?"i18_ItemCard_TaDa":"i18_ItemCard_Jili"},getFixTo2Number:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2,n=t;return n="".concat(d()(n||0).round(e,0).toFixed(e).toString())},getStyleName:$};e("utils",G)};
/***/},
/***/566:
/***/function(t,e){t.exports=function(){for(var t={},e=0;e<arguments.length;e++){var r=arguments[e];for(var o in r)n.call(r,o)&&(t[o]=r[o])}return t}
/***/;var n=Object.prototype.hasOwnProperty},
/***/57:
/***/function(t,e,n){"use strict";
/* harmony export (binding) */n.d(e,"e",(function(){return i})),
/* harmony export (binding) */n.d(e,"d",(function(){return s})),
/* harmony export (binding) */n.d(e,"a",(function(){return r})),
/* harmony export (binding) */n.d(e,"b",(function(){return o})),
/* harmony export (binding) */n.d(e,"c",(function(){return a}));
/* harmony import */n(15),n(49),n(26),n(22),n(18)
/* harmony import */;var r="custom",o="festival",a="ufa",i=[{type:"custom",
// 廠商自訂
value:"1",
// style編號
gameNoList:[6,27,35,37,44,45,47,48,51,81,87,103,106,109,110,136,137,171,180,183,186,193,198,208,209,214,223,226,228,252,258,264,299,301,304,307,372,375,378,379,393,399,400,422,423,448,460,461,472,505,518,523,526,529,539,540,541,543,545,547,573,581,583,589,590,591,593,595,597,598,605,621,623,635,636,640,641,643,659,661,664,676,705,711,655,686,706,720]},{type:"festival",
// 節慶自訂
value:"1",
// style編號
gameNoList:[
// 遊戲列表
193,258,301,379,421,481,540,545,581,605,623,644,664,696,697]},{type:"festival",
// 節慶自訂
value:"2",
// style編號
gameNoList:[
// 遊戲列表
109,198,223,379,421,540,545]},{type:"festival",
// 節慶自訂
value:"3",
// style編號
gameNoList:[
// 遊戲列表
258,301,681]},{type:"festival",
// 節慶自訂
value:"5",
// style編號
gameNoList:[
// 遊戲列表
258,481,529,540,573,649,664,701,714]},{type:"custom",
// 廠商自訂
value:"2",
// style編號
gameNoList:[
// 遊戲列表
379]},{type:"custom",
// 廠商自訂
value:"3",
// style編號
gameNoList:[
// 遊戲列表
548,681]},{type:"custom",
// 廠商自訂
value:"4",
// style編號
gameNoList:[
// 遊戲列表
552,557]},{type:"custom",
// 廠商自訂
value:"5",
// style編號
gameNoList:[
// 遊戲列表
548]},{type:"custom",
// 廠商自訂
value:"6",
// style編號
gameNoList:[
// 遊戲列表
538,580]},{type:"custom",
// 廠商自訂
value:"7",
// style編號
gameNoList:[
// 遊戲列表
584]},{type:"custom",
// 廠商自訂
value:"8",
// style編號
gameNoList:[
// 遊戲列表
403,585,669]},{type:"custom",
// 廠商自訂
value:"9",
// style編號
gameNoList:[
// 遊戲列表
538,562]},{type:"custom",
// 廠商自訂
value:"10",
// style編號
gameNoList:[
// 遊戲列表
538,670]},{type:"custom",
// 廠商自訂
value:"12",
// style編號
gameNoList:[
// 遊戲列表
557,669]},{type:"custom",
// 廠商自訂
value:"13",
// style編號
gameNoList:[
// 遊戲列表
538]},{type:"custom",
// 廠商自訂
value:"14",
// style編號
gameNoList:[
// 遊戲列表
627]},{type:"custom",
// 廠商自訂
value:"15",
// style編號
gameNoList:[
// 遊戲列表
561,627]},{type:"custom",
// 廠商自訂
value:"16",
// style編號
gameNoList:[
// 遊戲列表
439,441,542,557,560,751]},{type:"custom",
// 廠商自訂
value:"17",
// style編號
gameNoList:[
// 遊戲列表
628]},{type:"custom",
// 廠商自訂
value:"18",
// style編號
gameNoList:[
// 遊戲列表
557]},{type:"custom",
// 廠商自訂
value:"19",
// style編號
gameNoList:[
// 遊戲列表
681]},{type:"custom",
// 廠商自訂
value:"20",
// style編號
gameNoList:[
// 遊戲列表
229]},{type:"custom",
// 廠商自訂
value:"21",
// style編號
gameNoList:[
// 遊戲列表
27]},{type:"custom",
// 廠商自訂
value:"22",
// style編號
gameNoList:[
// 遊戲列表
229]},{type:"custom",
// 廠商自訂
value:"23",
// style編號
gameNoList:[
// 遊戲列表
738]},{type:"custom",
// 廠商自訂
value:"24",
// style編號
gameNoList:[
// 遊戲列表
229]},{type:"custom",
// 廠商自訂
value:"25",
// style編號
gameNoList:[
// 遊戲列表
742]},{type:"custom",
// 廠商自訂
value:"26",
// style編號
gameNoList:[
// 遊戲列表
229]},{type:"custom",
// 廠商自訂
value:"27",
// style編號
gameNoList:[
// 遊戲列表
560]},{type:"custom",
// 廠商自訂
value:"28",
// style編號
gameNoList:[
// 遊戲列表
669]},{type:"custom",
// 廠商自訂
value:"29",
// style編號
gameNoList:[
// 遊戲列表
821,892]},{type:"custom",
// 廠商自訂
value:"30",
// style編號
gameNoList:[
// 遊戲列表
557,560,751]},{type:"custom",
// 廠商自訂
value:"31",
// style編號
gameNoList:[
// 遊戲列表
669]},{type:"custom",
// 廠商自訂
value:"32",
// style編號
gameNoList:[
// 遊戲列表
552,561]},{type:"custom",
// 廠商自訂
value:"33",
// style編號
gameNoList:[
// 遊戲列表
821]},{type:"custom",
// 廠商自訂
value:"34",
// style編號
gameNoList:[
// 遊戲列表
751]},{type:"custom",
// 廠商自訂
value:"35",
// style編號
gameNoList:[
// 遊戲列表
821]},{type:"custom",
// 廠商自訂
value:"36",
// style編號
gameNoList:[
// 遊戲列表
557]},{type:"custom",
// 廠商自訂
value:"38",
// style編號
gameNoList:[
// 遊戲列表
557]},{type:"custom",
// 廠商自訂
value:"39",
// style編號
gameNoList:[
// 遊戲列表
738]},{type:"custom",
// 廠商自訂
value:"40",
// style編號
gameNoList:[
// 遊戲列表
751]},{type:"custom",
// 廠商自訂
value:"41",
// style編號
gameNoList:[
// 遊戲列表
895]},{type:"custom",
// 廠商自訂
value:"42",
// style編號
gameNoList:[
// 遊戲列表
745]},{type:"custom",
// 廠商自訂
value:"43",
// style編號
gameNoList:[
// 遊戲列表
896]},{type:"custom",
// 廠商自訂
value:"44",
// style編號
gameNoList:[
// 遊戲列表
896]},{type:"custom",
// 廠商自訂
value:"45",
// style編號
gameNoList:[
// 遊戲列表
561]},{type:"custom",
// 廠商自訂
value:"47",
// style編號
gameNoList:[
// 遊戲列表
880]},{type:"custom",
// 廠商自訂
value:"20101",
// style編號
gameNoList:[
// 遊戲列表
481,565,616,629]},{type:"custom",
// 廠商自訂
value:"21101",
// style編號
gameNoList:[
// 遊戲列表
616]},{type:"custom",
// 廠商自訂
value:"22101",
// style編號
gameNoList:[
// 遊戲列表
672,714]},{type:"ufa",
// UFA 換皮
value:"ufa",
// style編號
gameNoList:[
// 遊戲列表
557,669,681,744,745,747]}],c=null,u=[],s=function(t){var e,n=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null,r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:null;if(null!=n&&(c=n.toString(),(u=null===(e=i.find((function(t){return t.value===c&&t.type===r})))||void 0===e?void 0:e.gameNoList)&&u.length>0&&u.includes(t)))return c;return null}},
/***/62:
/***/function(t,e,n){"use strict";
/* harmony export (binding) */n.d(e,"a",(function(){return c}));
/* harmony import */n(7),n(10),n(8),n(14),n(16)
/* harmony import */;var r=n(5);function o(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(t);e&&(r=r.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.push.apply(n,r)}return n}
/**
 * api 基礎開關設定，預設全開，key以api名稱命名
 * @param extendObj 覆寫的設定的物件
 */
var a=function(){return function(t){for(var e=1;e<arguments.length;e++){var n=null!=arguments[e]?arguments[e]:{};e%2?o(Object(n),!0).forEach((function(e){Object(r.a)(t,e,n[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):o(Object(n)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(n,e))}))}return t}({
// auth 需 token 驗證
// 取得VIP設定
getVIPSetting:!0,
// 暱稱設定是否有開啟
isNicknameEnable:!0,
// 取得使用者道具
getPlayerItemData:!0,
// public 不需 token 驗證
// 取得輪播列表
getBanner:!0,
// 取得跑馬燈列表
getMarquee:!0,
// 取得入口遊戲列表
getGameEntrance:!0,
// 取得說明頁動態賠率
getRtpInfo:!0,
// 取得說明頁 switch off 設定
getSwitchOffInfo:!0},arguments.length>0&&void 0!==arguments[0]?arguments[0]:{})},i={GLI:a({getVIPSetting:!1,isNicknameEnable:!1,getPlayerItemData:!1}),ROAR:a({getBanner:!1,getMarquee:!1,getGameEntrance:!1}),DONUT:a({getBanner:!1,getMarquee:!1,getGameEntrance:!0,getRtpInfo:!1,getSwitchOffInfo:!1}),PS:a({getBanner:!1,getMarquee:!1,getGameEntrance:!0})},c=function(t,e){
// 判斷有定義需要關閉的api
return i[t]?i[t][e]||!1:a()[e]||!1};
/**
 * api 專案開關設定，要關閉的帶入api名稱設定，不需關閉開關的環境不用填
 */},
/***/692:
/***/function(t,e){
/* WEBPACK VAR INJECTION */(function(e){/* globals __webpack_amd_options__ */
t.exports=e;
/* WEBPACK VAR INJECTION */}).call(this,{})
/***/},
/***/696:
/***/function(t,e,n){var r={"./af-ZA":[435,1,0,2],"./af-ZA.js":[435,1,0,2],"./ar":[436,1,0,2],"./ar.js":[436,1,0,2],"./bg":[437,1,0,2],"./bg.js":[437,1,0,2],"./ca":[438,1,0,2],"./ca.js":[438,1,0,2],"./cs-CZ":[439,1,0,2],"./cs-CZ.js":[439,1,0,2],"./da":[440,1,0,2],"./da.js":[440,1,0,2],"./de":[441,1,0,2],"./de.js":[441,1,0,2],"./ee":[442,1,0,2],"./ee.js":[442,1,0,2],"./el":[443,1,0,2],"./el.js":[443,1,0,2],"./en":[444,1,0,2],"./en.js":[444,1,0,2],"./eo":[445,1,0,2],"./eo.js":[445,1,0,2],"./es":[446,1,0,2],"./es.js":[446,1,0,2],"./eu":[447,1,0,2],"./eu.js":[447,1,0,2],"./fa":[448,1,0,2],"./fa.js":[448,1,0,2],"./fi":[449,1,0,2],"./fi.js":[449,1,0,2],"./fr":[450,1,0,2],"./fr.js":[450,1,0,2],"./he":[451,1,0,2],"./he.js":[451,1,0,2],"./hr":[452,1,0,2],"./hr.js":[452,1,0,2],"./hu":[453,1,0,2],"./hu.js":[453,1,0,2],"./hy-AM":[454,1,0,2],"./hy-AM.js":[454,1,0,2],"./id":[455,1,0,2],"./id.js":[455,1,0,2],"./it":[456,1,0,2],"./it.js":[456,1,0,2],"./ja":[457,1,0,2],"./ja.js":[457,1,0,2],"./kg":[458,1,0,2],"./kg.js":[458,1,0,2],"./km":[459,1,0,2],"./km.js":[459,1,0,2],"./ko":[460,1,0,2],"./ko.js":[460,1,0,2],"./ku":[461,1,0,2],"./ku.js":[461,1,0,2],"./kz":[462,1,0,2],"./kz.js":[462,1,0,2],"./lt":[463,1,0,2],"./lt.js":[463,1,0,2],"./lv":[464,1,0,2],"./lv.js":[464,1,0,2],"./mn":[465,1,0,2],"./mn.js":[465,1,0,2],"./nb-NO":[466,1,0,2],"./nb-NO.js":[466,1,0,2],"./nl":[467,1,0,2],"./nl.js":[467,1,0,2],"./pl":[468,1,0,2],"./pl.js":[468,1,0,2],"./pt":[470,1,0,2],"./pt-br":[469,1,0,2],"./pt-br.js":[469,1,0,2],"./pt.js":[470,1,0,2],"./ro":[471,1,0,2],"./ro.js":[471,1,0,2],"./ru-RU":[472,1,0,2],"./ru-RU.js":[472,1,0,2],"./sk":[473,1,0,2],"./sk.js":[473,1,0,2],"./sl":[474,1,0,2],"./sl.js":[474,1,0,2],"./sr":[475,1,0,2],"./sr.js":[475,1,0,2],"./sv-SE":[476,1,0,2],"./sv-SE.js":[476,1,0,2],"./ta":[477,1,0,2],"./ta.js":[477,1,0,2],"./th":[478,1,0,2],"./th.js":[478,1,0,2],"./tk":[479,1,0,2],"./tk.js":[479,1,0,2],"./tr-TR":[480,1,0,2],"./tr-TR.js":[480,1,0,2],"./ua":[481,1,0,2],"./ua.js":[481,1,0,2],"./ug-CN":[482,1,0,2],"./ug-CN.js":[482,1,0,2],"./uz-UZ":[483,1,0,2],"./uz-UZ.js":[483,1,0,2],"./vi":[484,1,0,2],"./vi.js":[484,1,0,2],"./zh-CN":[223],"./zh-CN.js":[223],"./zh-TW":[485,1,0,2],"./zh-TW.js":[485,1,0,2]};function o(t){if(!n.o(r,t))return Promise.resolve().then((function(){var e=new Error("Cannot find module '"+t+"'");throw e.code="MODULE_NOT_FOUND",e}));var e=r[t],o=e[0];return Promise.all(e.slice(1).map(n.e)).then((function(){return n.t(o,7)}))}o.keys=function(){return Object.keys(r)},o.id=696,t.exports=o}}]);