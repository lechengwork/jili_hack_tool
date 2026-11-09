(window.webpackJsonp=window.webpackJsonp||[]).push([[2299,98,188,1433],{
/***/1488:
/***/function(e,t,r){"use strict";
// ESM COMPAT FLAG
r.r(t);
// CONCATENATED MODULE: ./node_modules/.pnpm/babel-loader@8.3.0_@babel+core@7.25.2_webpack@4.47.0/node_modules/babel-loader/lib??ref--2-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/.pnpm/@nuxt+components@2.2.1_consola@3.2.3/node_modules/@nuxt/components/dist/loader.js??ref--0-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib??vue-loader-options!./node_modules/.pnpm/windicss-webpack-plugin@1.8.0/node_modules/windicss-webpack-plugin/dist/loaders/windicss-template.cjs!./components/Game/RecordDetail/index.vue?vue&type=template&id=4fd4e2c6
r(7),r(10),r(8),r(14),r(16);var n=r(5),a=(r(63),r(12)),o=r(36);
// CONCATENATED MODULE: ./node_modules/.pnpm/babel-loader@8.3.0_@babel+core@7.25.2_webpack@4.47.0/node_modules/babel-loader/lib??ref--2-0!./node_modules/.pnpm/@nuxt+components@2.2.1_consola@3.2.3/node_modules/@nuxt/components/dist/loader.js??ref--0-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib??vue-loader-options!./node_modules/.pnpm/windicss-webpack-plugin@1.8.0/node_modules/windicss-webpack-plugin/dist/loaders/windicss-template.cjs!./components/Game/RecordDetail/index.vue?vue&type=script&lang=js
function s(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),r.push.apply(r,n)}return r}function i(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{};t%2?s(Object(r),!0).forEach((function(t){Object(n.a)(e,t,r[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(r)):s(Object(r)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(r,t))}))}return e}
/* harmony default export */var u={name:"GameRecordDetail",props:{gameId:{type:String,default:""},gameNo:{type:[String,Number],default:""}},data:function(){return{
// 按上一頁是否要回到大廳
isBackToGameList:!1}},computed:i(i({},Object(a.e)("control",["isUseDetailBackButton"])),{},{
// 回上頁按鈕路徑
backUrl:function(){return this.isBackToGameList?"/ingame/gamehistory":"/ingame/gamehistory/".concat(this.gameId)},
// 回上一頁按鈕的網址參數
backQuery:function(){var e=this.$utils.merge({},this.$route.query);return delete e.li,e},
// 動態元件名稱
componentName:function(){var e=this.$utils.getCaseInsensitiveProperty(this.$route.query),t=e.symbolstyle||e.style,r="";return""===this.gameNo||""===this.gameId?"GameNotFound":t&&(r=Object(o.b)("lazy-game-record-detail-id-style-".concat(t,"-").concat(this.gameId)),this.$nuxt.$options.components[r])?r:(r=Object(o.b)("lazy-game-record-detail-id-".concat(this.gameId)),this.$nuxt.$options.components[r]?Object(o.b)(r):"GameNotFound")}})},c=r(11),d=Object(c.a)(u,(function(){var e=this,t=e._self._c;return e.componentName?t(e.componentName,e._g(e._b({tag:"component",staticClass:"space-y-4 record-detail relative bg-[var(--site-bg-color-2)] rounded",attrs:{"game-id":e.gameId}},"component",e.$attrs,!1),e.$listeners),[e.isUseDetailBackButton?t("button-link",{staticClass:"mx-auto text-center mb-2 w-[70%] block",attrs:{link:e.backUrl,query:e.backQuery}},[e._v("\n    "+e._s(e.$t("i18_BackToPreviousPage"))+"\n  ")]):e._e()],1):t("game-not-found")}),[],!1,null,null,null)
/* harmony default export */;
// CONCATENATED MODULE: ./components/Game/RecordDetail/index.vue?vue&type=script&lang=js
/* harmony default export */t.default=d.exports;
/* nuxt-component-imports */
installComponents(d,{ButtonLink:r(786).default,GameNotFound:r(925).default})
/***/},
/***/1841:
/***/function(e,t,r){"use strict";
// ESM COMPAT FLAG
r.r(t);
// CONCATENATED MODULE: ./node_modules/.pnpm/babel-loader@8.3.0_@babel+core@7.25.2_webpack@4.47.0/node_modules/babel-loader/lib??ref--2-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/.pnpm/@nuxt+components@2.2.1_consola@3.2.3/node_modules/@nuxt/components/dist/loader.js??ref--0-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib??vue-loader-options!./node_modules/.pnpm/windicss-webpack-plugin@1.8.0/node_modules/windicss-webpack-plugin/dist/loaders/windicss-template.cjs!./pages/ingame/gamehistory/_gameId/_roundIndex.vue?vue&type=template&id=68c31998
r(10),r(8),r(14),r(16);var n=r(302),a=r(23),o=r(5),s=r(17),i=r(6),u=(r(32),r(26),r(20),r(28),r(15),r(27),r(22),r(18),r(7),r(48),r(24),r(135),r(12)),c=r(36),d=r(52),l=r(57),f=["Bet","Win"];function m(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),r.push.apply(r,n)}return r}function p(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{};t%2?m(Object(r),!0).forEach((function(t){Object(o.a)(e,t,r[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(r)):m(Object(r)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(r,t))}))}return e}
/* eslint-disable no-case-declarations */var b={name:"RoundIndex",provide:function(){var e=this;return{getFeatureOptions:function(){return{displayAccount:e.displayAccount,displayPreMoney:e.displayPreMoney,displayPostMoney:e.displayPostMoney,displayJpContribution:e.displayJpContribution,isRtpItemDisplay:e.featureOptions.isRtpItemDisplay}},symbolStylePath:this.stylePath}},data:function(){return{
// 單局資訊
record:this.$store.state.cache.historyDetailHeader?this.$store.state.cache.historyDetailHeader:{},
// 單局擴充資訊
recordExtend:{},
// log 列表
summaryList:[],
// 炸彈打到的魚種列表
bombDetailList:[],
// 棋牌類押注列表
stepDetailList:[],
// 輪盤資訊
rouletteInfo:{Info:{},Details:[],Tickets:[]},
// 西遊資訊
syInfo:{BetList:[],ExtraList:[],OddList:[],WinList:[]},
// 賓果資訊
bingoInfo:{Balls:[],ExtraBalls:[],Cards:[]},
// dtm 押注資訊
dtmDetailInfo:{Info:{},Details:[]},
// 刮刮樂資訊
scratchDetailInfo:{},
// 搜尋選項
searchOptions:{startRecord:1,endRecord:50,lastSearchType:"createTime",
// 是否以小單號為主，目前魚機廠商要跟玩家對帳務問題需要用到
logIndexAsRoundIndex:!1,infiniteId:0,pageSize:50},NO_DETAIL_TYPE:"NoDetail",noDetail:!1,errors:{history:null,RecordSummary:null,fishDetail:null,bombDetail:null,stepDetailList:null,tpPlateInfo:null,syInfo:null,rouletteInfo:null,minigame1Info:null,bingoInfo:null,dtmDetailInfo:null,scratchDetailInfo:null}}},fetch:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n,a,o,u,c,l,f,m,p,b,g,I,x,h,y,v,O,k,R,D,L,j,S,w,A,P,G,C;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(""!==e.gameNo){t.next=2;break}return t.abrupt("return");case 2:h=e.historyDetail.find((function(t){return t.key===e.logIndex})),y=e.historyDetail.find((function(t){return t.key===e.roundIndex})),v=e.historyDetailList.find((function(t){return t.key===e.roundIndex})),O=[],k=[],R=[],t.t0=e.gameType,t.next="CS"===t.t0||"GOCS"===t.t0||"ROLL"===t.t0||"GOROLL"===t.t0?11:"CSV2"===t.t0||"GOCSV2"===t.t0?28:"CSV3"===t.t0||"GOCSV3"===t.t0?42:"FISH11"===t.t0||"GOFISH11"===t.t0?56:"GOFISH11V2"===t.t0?64:"PLINKO"===t.t0||"GOPLINKO"===t.t0?71:"TP"===t.t0||"GOTP"===t.t0?78:"MINESWEEPER"===t.t0||"GOMINESWEEPER"===t.t0?97:"ROULETTE1"===t.t0||"GOROULETTE1"===t.t0||"TX"===t.t0||"GOTX"===t.t0?122:"SY"===t.t0||"GOSY"===t.t0?132:"BINGO1"===t.t0||"GOBINGO1"===t.t0||"GOBINGO1V2"===t.t0||"KENO1"===t.t0||"GOKENO1"===t.t0?140:"MINIGAME1"===t.t0||"GOMINIGAME1"===t.t0?154:"DTM"===t.t0||"GODTM"===t.t0||"GL"===t.t0||"GOGL"===t.t0?164:"SUDM"===t.t0||"GOSUDM"===t.t0?179:"CG"===t.t0||"GOCG"===t.t0?196:"PAPPU"===t.t0||"GOPAPPU"===t.t0||"ROULETTE3"===t.t0||"GOROULETTE3"===t.t0||"ROULETTE4"===t.t0||"GOROULETTE4"===t.t0||"JOGODO"===t.t0||"GOJOGODO"===t.t0?209:"SICBOM"===t.t0||"GOSICBOM"===t.t0?220:"POOLRUMMY"===t.t0||"GOPR"===t.t0||"BACCARAT"===t.t0||"GOBACCARAT"===t.t0?237:"LD"===t.t0||"GOLD"===t.t0||"LQ"===t.t0||"GOLQ"===t.t0?251:"SCRATCH"===t.t0||"GOSCRATCH"===t.t0?269:277;break;case 11:return t.next=13,e.getRecord();case 13:if(!y){t.next=17;break}return y.error&&(e.errors.RecordSummary=y.error),e.summaryList=y.value,t.abrupt("break",278);case 17:if(219!==e.record.AlterId){t.next=21;break}e.summaryList=[{Title:[e.$t("i18_SpinBonus")],Desc:[],plate:[]}],t.next=27;break;case 21:return t.next=23,e.getRecordSummary();case 23:return D=e.summaryList.map(function(){var t=Object(i.a)(regeneratorRuntime.mark((function t(r){var n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,e.getPlateInfo(r.LogIndex);case 2:return n=t.sent,
// 如果是錯誤訊息
Object(d.d)(n)?r.plate=[n]:r.plate=n,t.abrupt("return",r);case 5:case"end":return t.stop()}}),t)})));return function(e){return t.apply(this,arguments)}}()),t.next=26,Promise.all(D);case 26:e.summaryList=t.sent;case 27:return t.abrupt("break",278);case 28:return t.next=30,e.getRecord();case 30:if(!y){t.next=33;break}return e.summaryList=y.value,t.abrupt("break",278);case 33:if(219!==e.record.AlterId){t.next=37;break}e.summaryList=[{Title:[e.$t("i18_SpinBonus")],Desc:[],plate:[]}],t.next=41;break;case 37:return t.next=39,e.getCSV2PlateInfo();case 39:L=t.sent,
// 如果是錯誤訊息
Object(d.d)(L)?e.summaryList=[L]:e.summaryList=L;case 41:return t.abrupt("break",278);case 42:return t.next=44,e.getRecord();case 44:if(!y){t.next=47;break}return e.summaryList=y.value,t.abrupt("break",278);case 47:if(219!==e.record.AlterId){t.next=51;break}e.summaryList=[{Title:[e.$t("i18_SpinBonus")],Desc:[],plate:[]}],t.next=55;break;case 51:return t.next=53,e.getCSV3PlateInfo();case 53:j=t.sent,
// 如果是錯誤訊息
Object(d.d)(j)?e.summaryList=[j]:e.summaryList=j;case 55:return t.abrupt("break",278);case 56:if(e.searchOptions.logIndexAsRoundIndex=!0,e.resetRowIndex(),!e.historyDetailHeader){t.next=61;break}t.next=63;break;case 61:return t.next=63,e.getRecord();case 63:return t.abrupt("break",278);case 64:if(e.resetRowIndex(),!e.historyDetailHeader){t.next=68;break}t.next=70;break;case 68:return t.next=70,e.getRecord();case 70:return t.abrupt("break",278);case 71:if(e.resetRowIndex(),!e.historyDetailHeader){t.next=75;break}t.next=77;break;case 75:return t.next=77,e.getRecord();case 77:return t.abrupt("break",278);case 78:
// 重置
return e.errors.tpPlateInfo=null,e.errors.stepDetailList=null,t.next=82,e.getRecord();case 82:if(!y){t.next=87;break}k=y.value,R=v.value,t.next=94;break;case 87:if(70===(null===(r=e.record)||void 0===r?void 0:r.AlterId)){t.next=94;break}return t.next=90,Promise.all([e.getTpPlateInfo(),e.getTpStepDetailRecords()]);case 90:S=t.sent,w=Object(s.a)(S,2),k=w[0],R=w[1];case 94:
// 如果是錯誤訊息
return Object(d.d)(k)?(e.errors.tpPlateInfo=k,e.summaryList=[]):e.summaryList=k,
// 如果是錯誤訊息
Object(d.d)(R)?(e.errors.stepDetailList=R,e.stepDetailList=[]):e.stepDetailList=R,t.abrupt("break",278);case 97:if(!y){t.next=102;break}y.error&&(e.errors.recordExtend=y.error),e.recordExtend=y.value,t.next=120;break;case 102:if(70===(null===(n=e.record)||void 0===n?void 0:n.AlterId)){t.next=118;break}t.t1=e.gameId,t.next="crashfireworks"===t.t1||"crashaviatorm"===t.t1?106:113;break;case 106:return t.next=108,e.getRecord();case 108:if("ItemCard"!==e.record.Type){t.next=110;break}return t.abrupt("break",116);case 110:return t.next=112,e.getMinesweeperDetailInfo();case 112:return t.abrupt("break",116);case 113:return t.next=115,Promise.all([e.getRecord(),e.getMinesweeperDetailInfo()]);case 115:return t.abrupt("break",116);case 116:t.next=120;break;case 118:return t.next=120,e.getRecord();case 120:return e.record=e.$utils.mergeWithOverwriteArray.all([{},e.record,e.recordExtend]),t.abrupt("break",278);case 122:return t.next=124,e.getRecord();case 124:if(!y){t.next=129;break}e.rouletteInfo=y.value,y.error&&(e.errors.rouletteInfo=y.error),t.next=131;break;case 129:return t.next=131,e.getRouletteInfo();case 131:return t.abrupt("break",278);case 132:if(!y){t.next=137;break}e.syInfo=y.value,y.error&&(e.errors.syInfo=y.error),t.next=139;break;case 137:return t.next=139,Promise.all([e.getRecord(),e.getSyDetailInfo()]);case 139:return t.abrupt("break",278);case 140:return t.next=142,e.getRecord();case 142:if(null===(a=e.record.Type)||void 0===a||!a.includes(e.NO_DETAIL_TYPE)){t.next=145;break}return e.noDetail=!0,t.abrupt("break",278);case 145:if(!y){t.next=151;break}e.bingoInfo=y.value,e.setupBingoSummaryList(),y.error&&(e.errors.bingoInfo=y.error),t.next=153;break;case 151:return t.next=153,e.getBingoInfo();case 153:return t.abrupt("break",278);case 154:if(!y){t.next=161;break}return t.next=157,e.getRecord();case 157:e.summaryList=y.value,y.error&&(e.errors.minigame1Info=y.error),t.next=163;break;case 161:return t.next=163,Promise.all([e.getRecord(),e.getMinigame1PlateInfo()]);case 163:return t.abrupt("break",278);case 164:if(null===(o=e.record.Type)||void 0===o||!o.includes("ItemCard")){t.next=166;break}return t.abrupt("break",278);case 166:if(!y){t.next=173;break}return t.next=169,e.getRecord();case 169:e.dtmDetailInfo=y.value,y.error&&(e.errors.dtmDetailInfo=y.error),t.next=178;break;case 173:return t.next=175,e.getRecord();case 175:if(null!==(A=e.record.Type)&&void 0!==A&&A.includes("ItemCard")){t.next=178;break}return t.next=178,e.getDtmDetailInfo();case 178:return t.abrupt("break",278);case 179:if(null===(u=e.record.Type)||void 0===u||!u.includes("ItemCard")){t.next=181;break}return t.abrupt("break",278);case 181:if(!y){t.next=189;break}return t.next=184,e.getRecord();case 184:e.summaryList=y.value.summaryList,e.recordExtend=y.value.recordExtend,y.error&&(e.errors.RecordSummary=y.error),t.next=194;break;case 189:return t.next=191,e.getRecord();case 191:if(null!==(P=e.record.Type)&&void 0!==P&&P.includes("ItemCard")){t.next=194;break}return t.next=194,e.getSudmDetailInfo();case 194:return e.record=e.$utils.mergeWithOverwriteArray.all([{},e.record,e.recordExtend]),t.abrupt("break",278);case 196:return t.next=198,e.getRecord();case 198:if(!y){t.next=204;break}e.summaryList=y.value.summaryList,e.recordExtend=y.value.recordExtend,y.error&&(e.errors.RecordSummary=y.error),t.next=207;break;case 204:if("ItemCard"===(null===(c=e.record)||void 0===c?void 0:c.Type)||4===(null===(l=e.record)||void 0===l?void 0:l.Options)){t.next=207;break}return t.next=207,e.getSudmDetailInfo();case 207:return e.record=e.$utils.mergeWithOverwriteArray.all([{},e.record,e.recordExtend]),t.abrupt("break",278);case 209:return t.next=211,e.getRecord();case 211:if(!y){t.next=216;break}e.dtmDetailInfo=y.value,y.error&&(e.errors.dtmDetailInfo=y.error),t.next=219;break;case 216:if("ItemCard"===(null===(f=e.record)||void 0===f?void 0:f.Type)||70===(null===(m=e.record)||void 0===m?void 0:m.AlterId)){t.next=219;break}return t.next=219,e.getPappuDetailInfo();case 219:return t.abrupt("break",278);case 220:if(null===(p=e.record.Type)||void 0===p||!p.includes("ItemCard")){t.next=222;break}return t.abrupt("break",278);case 222:if(!y){t.next=230;break}return t.next=225,e.getRecord();case 225:e.summaryList=y.value.summaryList,e.recordExtend=y.value.recordExtend,y.error&&(e.errors.RecordSummary=y.error),t.next=235;break;case 230:return t.next=232,e.getRecord();case 232:if(null!==(G=e.record.Type)&&void 0!==G&&G.includes("ItemCard")){t.next=235;break}return t.next=235,e.getSicbomDetailInfo();case 235:return e.record=e.$utils.mergeWithOverwriteArray.all([{},e.record,e.recordExtend]),t.abrupt("break",278);case 237:
// 重置
return e.errors.tpPlateInfo=null,O=[],t.next=241,e.getRecord();case 241:if(!y){t.next=245;break}O=y.value,t.next=249;break;case 245:if(70===(null===(b=e.record)||void 0===b?void 0:b.AlterId)){t.next=249;break}return t.next=248,e.getTpPlateInfo();case 248:O=t.sent;case 249:
// 如果是錯誤訊息
return Object(d.d)(O)?(e.errors.tpPlateInfo=O,e.summaryList=[]):e.summaryList=O,t.abrupt("break",278);case 251:
// 重置
return e.errors.tpPlateInfo=null,t.next=254,e.getRecord();case 254:if(O=[],!h){t.next=259;break}O=h.value,t.next=263;break;case 259:if(70===(null===(g=e.record)||void 0===g?void 0:g.AlterId)){t.next=263;break}return t.next=262,e.getTpPlateInfo();case 262:O=t.sent;case 263:if(null===(I=e.record)||void 0===I||!I.LogIndex||70===(null===(x=e.record)||void 0===x?void 0:x.AlterId)){t.next=268;break}return t.next=266,e.getTpPlateInfo(e.record.LogIndex);case 266:C=t.sent,
// 如果是錯誤訊息
Object(d.d)(C)?(e.errors.tpPlateInfo=C,e.summaryList=[]):e.summaryList=C;case 268:return t.abrupt("break",278);case 269:if(!y){t.next=274;break}e.scratchDetailInfo=y.value,y.error&&(e.errors.scratchDetailInfo=y.error),t.next=276;break;case 274:return t.next=276,Promise.all([e.getRecord(),e.getScratchDetailInfo()]);case 276:case 277:return t.abrupt("break",278);case 278:
// FISH11 和 PLINKO 還有內容要載入，等到 searchNext 才能算載入完成
// if (this.gameType !== 'FISH11' &&
// this.gameType !== 'GOFISH11' &&
// this.gameType !== 'PLINKO' &&
// this.gameType !== 'GOPLINKO') {
// this.$store.commit('loading/setRangeEnd', '明細頁載入時間')
// }
// 額外廠商id顯示處理
// 加入防呆必須要有查詢到資料才做
e.isItaAuthId&&e.record&&Object.keys(e.record).length>0&&e.$dfAuthApi.getItaAuthId(e.roundIndex).then((function(t){t&&(e.record=e.$utils.deepset(e.record,"ItaAuthId",t))}));case 279:case"end":return t.stop()}}),t)})))()},computed:p(p(p(p(p({},Object(u.e)(["webApiUrl","zoomStyle","gameSettings","featureOptions"])),Object(u.e)("control",["isUseMenu","isUseHeaderOnly"])),Object(u.e)("cache",["historyDetailHeader","historyDetail","historyDetailList"])),Object(u.c)(["lang","token","apiId","isItaAuthId"])),{},{gameId:function(){var e,t;
// 從url來的是全小寫，轉 kebabCase 後會跟db或設定檔內全大寫的轉出來的結果不同
// 故需要先轉成全大寫
return null!==(e=Object(c.a)(null===(t=this.$route.params.gameId)||void 0===t?void 0:t.toUpperCase()))&&void 0!==e?e:""},gameNo:function(){return this.$utils.getGameNo(this.gameId)},gameType:function(){var e,t=this,r=this.gameSettings.find((function(e){return Object(c.a)(Object(c.a)(e.Id))===Object(c.a)(Object(c.a)(t.gameId))}));
// 全大寫跟全小寫的gameId轉出來的字串不太相同，轉2次確保一致性
return r?null==r||null===(e=r.HistoryType)||void 0===e?void 0:e.toUpperCase():(console.log("尚未設定 DB gameInfoList 正確 HistoryType"),null)},roundIndex:function(){return this.$route.params.roundIndex||""},logIndex:function(){return this.$route.query.li||""},scrollWrapName:function(){return!this.isUseMenu&&!this.isUseHeaderOnly||".layout-main-content"},stylePath:function(){
// TODO: UFA 換皮目前為應急處理，後續會合併回 Custom，要記得刪除，並添加相關設定。
var e=this.caseInsensitiveQuery.ufa;if(e&&"true"===e&&null!=Object(l.d)(this.gameNo,l.c,l.c))return"".concat(this.$store.state.style.pathName).concat(l.c,"/");
// 廠商自定義樣式
var t=this.caseInsensitiveQuery.custom;if(null!=Object(l.d)(this.gameNo,t,l.a))return"".concat(this.$store.state.style.pathName).concat(l.a).concat(t,"/");
// 節慶樣式
var r=this.caseInsensitiveQuery.festival;if(null!=Object(l.d)(this.gameNo,r,l.b))return"".concat(this.$store.state.style.pathName).concat(l.b).concat(r,"/");
// 容舊規格樣式
var n=this.caseInsensitiveQuery.symbolstyle||this.caseInsensitiveQuery.style||this.$store.state.style.default;if(n){var a=parseInt(n,10),o=a>=100?l.a:l.b,s=o===l.a?(a/100).toString():n;if(null!=Object(l.d)(this.gameNo,s,o))return"".concat(this.$store.state.style.pathName).concat(o).concat(s,"/")}return""},caseInsensitiveQuery:function(){return this.$utils.getCaseInsensitiveProperty(this.$route.query)},displayAccount:function(){var e,t=!0;return"false"===(null===(e=this.caseInsensitiveQuery.account)||void 0===e?void 0:e.toLowerCase())&&(t=!1),t},displayPreMoney:function(){var e,t=!1;return"true"===(null===(e=this.caseInsensitiveQuery.premoney)||void 0===e?void 0:e.toLowerCase())&&(t=!0),t},displayPostMoney:function(){var e,t=!0;return"false"===(null===(e=this.caseInsensitiveQuery.postmoney)||void 0===e?void 0:e.toLowerCase())&&(t=!1),t},displayJpContribution:function(){var e,t=!1;return"true"===(null===(e=this.caseInsensitiveQuery.jpcontribution)||void 0===e?void 0:e.toLowerCase())&&(t=!0),t}}),mounted:function(){
// 因為 頁面目前捲軸做在 .history-wrap 這個元件上，所以nuxt預設捲到最上方的功能會無效
var e=document.querySelector(this.scrollWrapName);e&&(e.scrollTop=0),
// 明細表格欄位較多，main-content 不套用預設的 max-w 限制，離開頁面時要記得還原
this.setUseWideMainContent(!0)},beforeDestroy:function(){this.setUseWideMainContent(!1)},created:function(){var e,t,r=this.$utils.getCaseInsensitiveProperty(this.$route.query);
// 當 passgamelistpage=true 與 backhistorylobby=true 同時存在時，
// 在 DOM 渲染前將 passgamelistpage 改為 false，避免按鈕閃爍
if("true"===(null===(e=r.passgamelistpage)||void 0===e?void 0:e.toLowerCase())&&"true"===(null===(t=r.backhistorylobby)||void 0===t?void 0:t.toLowerCase())){
// 先移除所有大小寫變體的 passgamelistpage，避免 URL 出現重複的 query key
var n=this.$route.query||{},a=Object.keys(n).reduce((function(e,t){return"passgamelistpage"!==t.toLowerCase()&&(e[t]=n[t]),e}),{});this.$router.replace({query:p(p({},a),{},{passgamelistpage:"false"})})}},methods:p(p(p({},Object(u.d)("gamehistory",["setRecord"])),Object(u.d)("control",["setUseWideMainContent"])),{},{
// 只取一筆列表資料
getRecord:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 檢查是否有 cache
if(
// 重置
e.errors.history=null,!e.historyDetailHeader){t.next=5;break}return e.setRecord(e.historyDetailHeader),
// 清除 cache
e.$store.commit("cache/setHistoryDetailHeader",null),t.abrupt("return");case 5:return r={gameId:e.gameId,lang:e.lang,apiId:e.apiId,roundIndex:e.roundIndex,logIndex:e.logIndex,startRecord:1,endRecord:1,logIndexAsRoundIndex:e.searchOptions.logIndexAsRoundIndex},t.next=8,e.$dfAuthApi.getGoHistoryRecord(r);case 8:if(n=t.sent,!Object(d.d)(n)){t.next=14;break}return e.record={},e.errors.history=n,e.setRecord({}),t.abrupt("return");case 14:
// 給值
e.record=null!=n&&n[0]?n[0]:{},e.setRecord(e.record);case 16:case"end":return t.stop()}}),t)})))()},
// 取得單筆歷程摘要列表
getRecordSummary:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if("sajp"!==e.gameId&&"superacejp2"!==e.gameId&&"superacejppac"!==e.gameId||!(e.record.JpType>0)){t.next=2;break}return t.abrupt("return");case 2:
// 重置
return e.errors.RecordSummary=null,t.next=5,e.$dfAuthApi.getGoRecordSummary(e.gameId,e.lang,e.roundIndex);case 5:if(r=t.sent,!Object(d.d)(r)){t.next=10;break}return e.summaryList=[],e.errors.RecordSummary=r,t.abrupt("return");case 10:e.summaryList=r||[];case 11:case"end":return t.stop()}}),t)})))()},
// 取得盤面資訊
getPlateInfo:function(e){var t=this;return Object(i.a)(regeneratorRuntime.mark((function r(){var n;return regeneratorRuntime.wrap((function(r){for(;;)switch(r.prev=r.next){case 0:return r.next=2,t.$dfAuthApi.getGoPlateInfo(t.gameId,t.roundIndex,e);case 2:return n=r.sent,r.abrupt("return",n);case 4:case"end":return r.stop()}}),r)})))()},
// 取得盤面資訊
getCSV2PlateInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,e.$dfAuthApi.getGoCSV2PlateInfo(e.gameId,e.roundIndex,e.lang,e.record.CreateTime);case 2:return t.abrupt("return",t.sent);case 3:case"end":return t.stop()}}),t)})))()},
// 取得盤面資訊
getCSV3PlateInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,e.$dfAuthApi.getGoCSV3PlateInfo(e.gameId,e.roundIndex,e.lang);case 2:return t.abrupt("return",t.sent);case 3:case"end":return t.stop()}}),t)})))()},
// 取得單局明細補充資訊
getDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,e.$dfAuthApi.getGoDetailInfo(e.gameId,e.roundIndex,e.logIndex);case 2:if(r=t.sent,!Object(d.d)(r)){t.next=7;break}return e.recordExtend={},e.errors.history=r,t.abrupt("return");case 7:e.recordExtend=r;case 8:case"end":return t.stop()}}),t)})))()},
// 取得sy明細資訊
getSyDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.syInfo=null,t.next=3,e.$dfAuthApi.getGoSyDetailInfo(e.gameId,e.roundIndex);case 3:if(r=t.sent,!Object(d.d)(r)){t.next=8;break}return e.syInfo={BetList:[],ExtraList:[],OddList:[],WinList:[]},e.errors.syInfo=r,t.abrupt("return");case 8:e.syInfo=r;case 9:case"end":return t.stop()}}),t)})))()},
// 取得炸彈打到的魚種列表
getBombDetailList:function(e,t){var r=this;return Object(i.a)(regeneratorRuntime.mark((function n(){var a;return regeneratorRuntime.wrap((function(n){for(;;)switch(n.prev=n.next){case 0:return r.errors.bombDetail=null,n.next=3,r.$dfAuthApi.getGoBombDetailRecord(r.gameId,e,t);case 3:if(a=n.sent,!Object(d.d)(a)){n.next=8;break}return r.bombDetailList=[],r.errors.bombDetail=a,n.abrupt("return");case 8:r.bombDetailList=a;case 9:case"end":return n.stop()}}),n)})))()},
// 取得TP類型盤面資訊
getTpPlateInfo:function(e){var t=this;return Object(i.a)(regeneratorRuntime.mark((function r(){var n,a;return regeneratorRuntime.wrap((function(r){for(;;)switch(r.prev=r.next){case 0:return n=e||t.roundIndex,r.next=3,t.$dfAuthApi.getGoTpPlateInfo(t.gameId,n);case 3:return a=r.sent,r.abrupt("return",a);case 5:case"end":return r.stop()}}),r)})))()},
// 取得TP類型逐步下注資訊
getTpStepDetailRecords:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(!["teenpatti","teenpatti2","teenpatti3","miniflush","fivecardpoker","ultitexasholdem","gallinafortunata","spandarbahar","potiontwist","jackpotfootball"].includes(e.gameId)){t.next=6;break}return t.next=4,e.$dfAuthApi.getGoTpStepDetailRecords(e.gameId,e.roundIndex);case 4:return r=t.sent,t.abrupt("return",r);case 6:return t.abrupt("return",[]);case 7:case"end":return t.stop()}}),t)})))()},
// 切換得獎連線顯示 event 由 game-detail-award-list 發起
chageSummaryList:function(e){this.summaryList=e},
// 取得下一批明細資料，魚機類型使用
searchNext:function(e,t){var r=this;return Object(i.a)(regeneratorRuntime.mark((function n(){var o;return regeneratorRuntime.wrap((function(n){for(;;)switch(n.prev=n.next){case 0:return r.errors.fishDetail=null,
// 處理子層傳上來條件
void 0!==t&&"pageSize"in t&&(r.searchOptions.pageSize=t.pageSize,1===r.searchOptions.startRecord&&(r.searchOptions.endRecord=t.pageSize)),n.next=4,r.searchQuery();case 4:if(o=n.sent,!Object(d.d)(o)){n.next=13;break}return console.log("error"),r.summaryList=[],r.errors.fishDetail=o,n.next=11,r.$nextTick();case 11:return e.error(),n.abrupt("return");case 13:if(0!==o.length){n.next=16;break}return e.complete(),n.abrupt("return");case 16:if(!(o.length>0)){n.next=25;break}if(r.summaryList=[].concat(Object(a.a)(r.summaryList),Object(a.a)(o)),!(o.length<r.searchOptions.pageSize)){n.next=22;break}e.complete(),n.next=25;break;case 22:return n.next=24,r.$nextTick();case 24:e.loaded();case 25:case"end":return n.stop()}}),n)})))()},
// 取得sy明細資訊
getMinesweeperDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.recordExtend=null,t.next=3,e.$dfAuthApi.getGoDetailRoundIndexInfo(e.gameId,e.roundIndex,e.record.RoundInfoIndex);case 3:if(r=t.sent,!Object(d.d)(r)){t.next=8;break}return e.recordExtend={},e.errors.recordExtend=r,t.abrupt("return");case 8:e.recordExtend=r;case 9:case"end":return t.stop()}}),t)})))()},
// 取得魚機單局明細魚種列表
searchQuery:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n,o,s;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:// 如果有 cache 就不用再打 api
if(r=[],!(n=e.historyDetailList.find((function(t){return t.key===e.logIndex})))||1!==e.searchOptions.startRecord){t.next=7;break}
// 用一個變數暫存cacheDetailList 才不會影響到真正的cacheDetailList
o=Object(a.a)(n.value),"Win"===e.searchOptions.lastSearchType?(o.sort((function(e,t){return t.Win-e.Win})),r=o):r=n.value,t.next=18;break;case 7:if("GOFISH11V2"!==e.gameType){t.next=15;break}return t.next=10,e.$dfAuthApi.getGoFish11V2DetailRecord(e.gameId,e.lang,e.roundIndex);case 10:r=t.sent,r=null===(s=r)||void 0===s?void 0:s.map((function(e,t){return p(p({},e),{},{SummaryListIndex:t})})),
// 遠端 /report/detail 一次回傳整局所有明細、不分頁也不吃 OrderField，
// 因此贏分排序只能在前端做（同上面 cache 命中時的處理）
Array.isArray(r)&&"Win"===e.searchOptions.lastSearchType&&r.sort((function(e,t){return t.Win-e.Win})),t.next=18;break;case 15:return t.next=17,e.$dfAuthApi.getGoDetailRecord(e.gameId,e.lang,e.roundIndex,e.searchOptions.lastSearchType,e.searchOptions.startRecord,e.searchOptions.endRecord,e.searchOptions.logIndexAsRoundIndex?e.logIndex:null);case 17:r=t.sent;case 18:return e.addRowIndex(e.searchOptions.pageSize),t.abrupt("return",r);case 20:case"end":return t.stop()}}),t)})))()},resetRowIndex:function(){this.searchOptions.startRecord=1,this.searchOptions.endRecord=this.searchOptions.pageSize,this.summaryList=[],this.searchOptions.infiniteId+=1},addRowIndex:function(e){this.searchOptions.startRecord+=e,this.searchOptions.endRecord+=e},changeSearchType:function(e){this.searchOptions.lastSearchType=e,this.resetRowIndex()},
// 取得輪盤資訊
getRouletteInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n,a;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.rouletteInfo=null,n={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex,historyId:(null===(r=e.record)||void 0===r?void 0:r.HistoryId)||"error"},t.next=4,e.$dfAuthApi.getGoRouletteInfo(n);case 4:if(a=t.sent,!Object(d.d)(a)){t.next=9;break}return e.rouletteInfo={Info:{},Details:[],Tickets:[]},e.errors.rouletteInfo=a,t.abrupt("return");case 9:e.rouletteInfo=a;case 10:case"end":return t.stop()}}),t)})))()},
// 取得賓果資訊
getBingoInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.bingoInfo=null,r={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoBingoInfo(r);case 4:if(n=t.sent,!Object(d.d)(n)){t.next=10;break}return e.bingoInfo={Balls:[],ExtraBalls:[],Cards:[]},e.summaryList=[],e.errors.bingoInfo=n,t.abrupt("return");case 10:e.bingoInfo=n,e.setupBingoSummaryList();case 12:case"end":return t.stop()}}),t)})))()},setupBingoSummaryList:function(){var e,t=[];
// 將 Bonus 遊戲的卡片接在一般卡片後面，才能使用原本的 summaryList 做連線的切換
null===(e=this.bingoInfo.Bonus)||void 0===e||e.forEach((function(e){t=t.concat(e.Cards)})),this.summaryList=this.bingoInfo.Cards.concat(t)},getMinigame1PlateInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.minigame1Info=null,r={gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoMinigame1Info(r);case 4:if(n=t.sent,!Object(d.d)(n)){t.next=9;break}return e.summaryList=[],e.errors.minigame1Info=n,t.abrupt("return");case 9:e.summaryList=n;case 10:case"end":return t.stop()}}),t)})))()},
// 取得 dtm 類型單局押注明細
getDtmDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.dtmDetailInfo=null,r={gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoDtmDetailInfo(r);case 4:if(n=t.sent,!Object(d.d)(n)){t.next=9;break}return e.dtmDetailInfo={Info:{},Details:[]},e.errors.dtmDetailInfo=n,t.abrupt("return");case 9:e.dtmDetailInfo=n;case 10:case"end":return t.stop()}}),t)})))()},
// 取得 sudm 類型單局押注明細
getSudmDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n,a,o;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.RecordSummary=null,a={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoSudmDetailInfo(a);case 4:if(o=t.sent,!Object(d.d)(o)){t.next=10;break}return e.summaryList=[],e.recordExtend={},e.errors.RecordSummary=o,t.abrupt("return");case 10:e.summaryList=null!==(r=null==o?void 0:o.Details)&&void 0!==r?r:[],e.recordExtend=null!==(n=null==o?void 0:o.Info)&&void 0!==n?n:{};case 12:case"end":return t.stop()}}),t)})))()},
// 取得 PAPPU 類型單局押注明細
getPappuDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:
// 重置
return e.errors.RecordSummary=null,r={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoSudmDetailInfo(r);case 4:if(n=t.sent,!Object(d.d)(n)){t.next=9;break}return e.dtmDetailInfo={Info:{},Details:[]},e.errors.dtmDetailInfo=n,t.abrupt("return");case 9:e.dtmDetailInfo=n;case 10:case"end":return t.stop()}}),t)})))()},getSicbomDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,a,o,s,i,u,c,l;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(
// 重置
e.errors.RecordSummary=null,r={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex},10!==e.record.AlterId&&11!==e.record.AlterId&&12!==e.record.AlterId){t.next=14;break}return t.next=5,e.$dfAuthApi.getGoSicbomBoxDetailInfo(r);case 5:if(a=t.sent,!Object(d.d)(a)){t.next=11;break}return e.summaryList=[],e.recordExtend={},e.errors.RecordSummary=a,t.abrupt("return");case 11:a?(o=a.Bet,s=a.Win,i=Object(n.a)(a,f),e.summaryList=[{Bet:o,Win:s}],e.recordExtend=i):(e.summaryList=[],e.recordExtend={}),t.next=24;break;case 14:return t.next=16,e.$dfAuthApi.getGoSicbomDetailInfo(r);case 16:if(l=t.sent,!Object(d.d)(l)){t.next=22;break}return e.summaryList=[],e.recordExtend={},e.errors.RecordSummary=l,t.abrupt("return");case 22:e.summaryList=null!==(u=null==l?void 0:l.Details)&&void 0!==u?u:[],e.recordExtend=null!==(c=null==l?void 0:l.Info)&&void 0!==c?c:{};case 24:case"end":return t.stop()}}),t)})))()},getScratchDetailInfo:function(){var e=this;return Object(i.a)(regeneratorRuntime.mark((function t(){var r,n;return regeneratorRuntime.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return e.errors.scratchDetailInfo=null,r={lang:e.lang,gameId:e.gameId,roundIndex:e.roundIndex},t.next=4,e.$dfAuthApi.getGoSudmDetailInfo(r);case 4:if(n=t.sent,!Object(d.d)(n)){t.next=9;break}return e.scratchDetailInfo={},e.errors.scratchDetailInfo=n,t.abrupt("return");case 9:e.scratchDetailInfo=n;case 10:case"end":return t.stop()}}),t)})))()}})},g=b,I=r(11),x=Object(I.a)(g,(function(){var e=this,t=e._self._c;return t("div",[e.noDetail?t("game-not-found",[e._v("\n    "+e._s(e.$t("i18_NoDetail"))+"\n  ")]):t("game-record-detail",{staticClass:"mx-auto p-2 xs:p-5",attrs:{"game-id":e.gameId,"game-no":e.gameNo,record:e.record,"summary-list":e.summaryList,"infinite-id":e.searchOptions.infiniteId,"log-index-as-round-index":e.searchOptions.logIndexAsRoundIndex,"bomb-detail-list":e.bombDetailList,"step-detail-list":e.stepDetailList,"roulette-info":e.rouletteInfo,"sy-info":e.syInfo,"bingo-info":e.bingoInfo,"dtm-detail-info":e.dtmDetailInfo,"scratch-detail-info":e.scratchDetailInfo,errors:e.errors,"symbol-style-path":e.stylePath},on:{clickAward:e.chageSummaryList,onInfinite:e.searchNext,clickFishOrder:e.changeSearchType,showBombDetail:e.getBombDetailList}})],1)}),[],!1,null,null,null)
/* harmony default export */;t.default=x.exports;
/* nuxt-component-imports */
installComponents(x,{GameNotFound:r(925).default,GameRecordDetail:r(1488).default})
/***/},
/***/786:
/***/function(e,t,r){"use strict";
// ESM COMPAT FLAG
r.r(t);
// EXTERNAL MODULE: ./node_modules/.pnpm/core-js@2.6.12/node_modules/core-js/modules/es6.string.link.js
r(781),r(63),r(64);
// CONCATENATED MODULE: ./node_modules/.pnpm/babel-loader@8.3.0_@babel+core@7.25.2_webpack@4.47.0/node_modules/babel-loader/lib??ref--2-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/.pnpm/@nuxt+components@2.2.1_consola@3.2.3/node_modules/@nuxt/components/dist/loader.js??ref--0-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib??vue-loader-options!./node_modules/.pnpm/windicss-webpack-plugin@1.8.0/node_modules/windicss-webpack-plugin/dist/loaders/windicss-template.cjs!./components/Button/Link.vue?vue&type=template&id=8a776606
var n={name:"ButtonLink",props:{link:{type:String,default:""},query:{type:Object||null,default:null},go:{type:Number,default:0},customClass:{type:[String,Boolean],default:!1}},data:function(){return{defaultClass:"bg-[#626263] text-white text-center rounded-md px-3 py-1"}},computed:{isGlobalLink:function(){return!!this.link&&!!this.link.match(/^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!@:%_+.~#?&//=]*)/)},currentClass:function(){return this.customClass?this.customClass:this.defaultClass},customQuery:function(){return this.query?this.query:this.$route.query}},methods:{chageRouteWithGo:function(){0!==this.go&&null!=this.go&&this.$router.go(this.go)}}},a=r(11),o=Object(a.a)(n,(function(){var e=this,t=e._self._c;return e.link&&!e.isGlobalLink?t("nuxt-link",e._b({class:e.currentClass,attrs:{to:{path:e.localePath(e.link),query:e.customQuery}}},"nuxt-link",e.$attrs,!1),[e._t("default")],2):e.link&&e.isGlobalLink?t("a",e._b({class:e.currentClass,attrs:{href:e.link}},"a",e.$attrs,!1),[e._t("default")],2):0!==e.go?t("a",e._b({class:e.currentClass,attrs:{href:"javascript:void(0)"},on:{click:function(t){return t.preventDefault(),e.chageRouteWithGo.apply(null,arguments)}}},"a",e.$attrs,!1),[e._t("default")],2):t("a",e._g(e._b({class:e.currentClass,attrs:{href:"javascript:void(0)"}},"a",e.$attrs,!1),e.$listeners),[e._t("default")],2)}),[],!1,null,null,null)
/* harmony default export */;t.default=o.exports},
/***/925:
/***/function(e,t,r){"use strict";
// ESM COMPAT FLAG
r.r(t);
// CONCATENATED MODULE: ./node_modules/.pnpm/babel-loader@8.3.0_@babel+core@7.25.2_webpack@4.47.0/node_modules/babel-loader/lib??ref--2-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib/loaders/templateLoader.js??ref--6!./node_modules/.pnpm/@nuxt+components@2.2.1_consola@3.2.3/node_modules/@nuxt/components/dist/loader.js??ref--0-0!./node_modules/.pnpm/vue-loader@15.11.1_babel-core@6.26.3_cache-loader@4.1.0_webpack@4.47.0__css-loader@5.2.7_webp_7a7hvw2t2ee2w5pfkpsqnacmqm/node_modules/vue-loader/lib??vue-loader-options!./node_modules/.pnpm/windicss-webpack-plugin@1.8.0/node_modules/windicss-webpack-plugin/dist/loaders/windicss-template.cjs!./components/Game/NotFound.vue?vue&type=template&id=6c36f16e
var n={name:"GameNotFound"},a=r(11),o=Object(a.a)(n,(function(){var e=this;return(0,e._self._c)("div",{staticClass:"flex h-screen text-white text-4xl justify-center items-center"},[e._t("default",(function(){return[e._v(e._s(e.$t("i18_PageNotFound")))]}))],2)}),[],!1,null,null,null)
/* harmony default export */;t.default=o.exports}}]);