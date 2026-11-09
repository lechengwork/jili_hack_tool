System.register([], function (_export, _context) {
  "use strict";

  var cc, Application;
  function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
  function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
  function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
  function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
  function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return typeof key === "symbol" ? key : String(key); }
  function _toPrimitive(input, hint) { if (_typeof(input) !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (_typeof(res) !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
  return {
    setters: [],
    execute: function () {
      _export("Application", Application = /*#__PURE__*/function () {
        function Application() {
          _classCallCheck(this, Application);
        }
        _createClass(Application, [{
          key: "init",
          value: function init(engine) {
            cc = engine;
            cc.game.onPostProjectInitDelegate.add(this.onPostProjectInit.bind(this));
            window.pageLoadTiming.logTime('log851');
            window.pageLoadTiming.calculateDuration(851, 'headStartTime', 'log851');
          }
        }, {
          key: "onPostProjectInit",
          value: function onPostProjectInit() {
            cc.view.resizeWithBrowserSize(true);
          }
        }, {
          key: "GetLinkParameterByName",
          value: function GetLinkParameterByName(name) {
            var url = window.location.href;
            name = name.replace(/[\[\]]/g, '\\$&');
            var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
              results = regex.exec(url);
            if (!results) return null;
            if (!results[2]) return '';
            return decodeURIComponent(results[2].replace(/\+/g, ' '));
          }
        }, {
          key: "start",
          value: function start() {
            // ����W���� WEBGL_ANTIALIAS (�����]�w)
            if (cc.sys.isBrowser && cc.sys.isMobile) {
              cc.macro.ENABLE_WEBGL_ANTIALIAS = false;
            }
            window.pageLoadTiming.logTime('log852');
            window.pageLoadTiming.calculateDuration(852, 'headStartTime', 'log852');
            window.pageLoadTiming.logTime('log852');
            window.pageLoadTiming.calculateDuration(852, 'headStartTime', 'log852');
            window.SetProgressInterval(30);
            window.__loadStage = 'engine_init';

            // 只有啟用的遊戲（index.ejs 的 ENABLE_GAME_IDS）才做失敗回報與重整，其他遊戲維持原行為
            // 卡住逾時改由 index.ejs 的看門狗統一處理
            var isGuard = !!window.IsLoadErrorReportGame;
            var RETRY_KEY = 'slotEngineInitRetry';
            var MAX_RETRY = 1;
            var getRetryCount = function getRetryCount() {
              try {
                return parseInt(sessionStorage.getItem(RETRY_KEY) || '0', 10) || 0;
              } catch (e) {
                return MAX_RETRY;
              }
            };
            var setRetryCount = function setRetryCount(n) {
              try {
                n > 0 ? sessionStorage.setItem(RETRY_KEY, String(n)) : sessionStorage.removeItem(RETRY_KEY);
              } catch (e) {}
            };
            return cc.game.init({
              settingsPath: 'src/settings.fd5f0.json',
              overrideSettings: {
                splashScreen: {
                  enabled: false
                }
              },
              debugMode: cc.DebugMode.ERROR
            }).then(function () {
              window.__loadStage = 'engine_ready';
              if (cc.sys.isBrowser) {
                // �վ�ʺA�X�ϳ̤j�ƶq
                if (cc.sys.isMobile) {
                  cc.dynamicAtlasManager.maxAtlasCount = 2;
                }
                cc.assetManager.downloader.maxConcurrency = 15;
                cc.assetManager.downloader.maxRequestsPerFrame = 64;
              }
              window.SetProgressInterval(50);
              window.pageLoadTiming.logTime('log853');
              window.pageLoadTiming.calculateDuration(853, 'headStartTime', 'log853');
              cc.game.run();
              // 放在 run 之後：run 若持續拋錯也不會無限重整
              setRetryCount(0);
            })["catch"](function (err) {
              if (!isGuard) {
                throw err;
              }
              var retry = getRetryCount();
              window.ReportLoadError && window.ReportLoadError('init_fail', 'retry=' + retry + ' ' + (err && (err.stack || err.message) || err));
              if (retry < MAX_RETRY) {
                setRetryCount(retry + 1);
                // 讓回報請求有時間送出再重整；標記為自動重整，index.ejs 不會當成玩家離開
                window.__loadReloading = true;
                setTimeout(function () {
                  return location.reload();
                }, 500);
              }
            });
          }
        }]);
        return Application;
      }());
    }
  };
});