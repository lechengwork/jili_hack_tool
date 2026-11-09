System.register([], function (_export, _context) {
  "use strict";

  var cc, Application;
  function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
  function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
  function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
  function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return typeof key === "symbol" ? key : String(key); }
  function _toPrimitive(input, hint) { if (typeof input !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (typeof res !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
  function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
  return {
    setters: [],
    execute: function () {
      !function (t, e) {
        "object" == (typeof exports === "undefined" ? "undefined" : _typeof(exports)) && "object" == (typeof module === "undefined" ? "undefined" : _typeof(module)) ? module.exports = e() : "function" == typeof define && define.amd ? define("safeAreaInsets", [], e) : "object" == (typeof exports === "undefined" ? "undefined" : _typeof(exports)) ? exports.safeAreaInsets = e() : t.safeAreaInsets = e();
      }("undefined" != typeof self ? self : void 0, function () {
        return function (t) {
          function e(o) {
            if (n[o]) return n[o].exports;
            var r = n[o] = {
              i: o,
              l: !1,
              exports: {}
            };
            return t[o].call(r.exports, r, r.exports, e), r.l = !0, r.exports;
          }
          var n = {};
          return e.m = t, e.c = n, e.d = function (t, n, o) {
            e.o(t, n) || Object.defineProperty(t, n, {
              configurable: !1,
              enumerable: !0,
              get: o
            });
          }, e.n = function (t) {
            var n = t && t.__esModule ? function () {
              return t["default"];
            } : function () {
              return t;
            };
            return e.d(n, "a", n), n;
          }, e.o = function (t, e) {
            return Object.prototype.hasOwnProperty.call(t, e);
          }, e.p = "", e(e.s = 0);
        }([function (t, e, n) {
          "use strict";

          function o() {
            return a = "CSS" in window && "function" == typeof CSS.supports ? CSS.supports("top: env(safe-area-inset-top)") ? "env" : CSS.supports("top: constant(safe-area-inset-top)") ? "constant" : "" : "";
          }
          function r() {
            function t(t, e) {
              var n = t.style;
              Object.keys(e).forEach(function (t) {
                var o = e[t];
                n[t] = o;
              });
            }
            function e(t) {
              t ? r.push(t) : r.forEach(function (t) {
                t();
              });
            }
            function n(n, o) {
              var r = document.createElement("div"),
                f = document.createElement("div"),
                s = document.createElement("div"),
                u = document.createElement("div"),
                p = 1e4,
                l = {
                  position: "absolute",
                  width: "100px",
                  height: "200px",
                  boxSizing: "border-box",
                  overflow: "hidden",
                  paddingBottom: a + "(safe-area-inset-" + o + ")"
                };
              t(r, l), t(f, l), t(s, {
                transition: "0s",
                animation: "none",
                width: "400px",
                height: "400px"
              }), t(u, {
                transition: "0s",
                animation: "none",
                width: "250%",
                height: "250%"
              }), r.appendChild(s), f.appendChild(u), n.appendChild(r), n.appendChild(f), e(function () {
                function t() {
                  this.scrollTop !== (this === r ? e : n) && (r.scrollTop = f.scrollTop = p, e = r.scrollTop, n = f.scrollTop, c(o));
                }
                r.scrollTop = f.scrollTop = p;
                var e = r.scrollTop,
                  n = f.scrollTop;
                r.addEventListener("scroll", t, i), f.addEventListener("scroll", t, i);
              });
              var h = getComputedStyle(r);
              Object.defineProperty(d, o, {
                configurable: !0,
                get: function get() {
                  return parseFloat(h.paddingBottom);
                }
              });
            }
            if (!(a = "string" == typeof a ? a : o())) return void p.forEach(function (t) {
              d[t] = 0;
            });
            var r = [],
              i = !1;
            try {
              var f = Object.defineProperty({}, "passive", {
                get: function get() {
                  i = {
                    passive: !0
                  };
                }
              });
              window.addEventListener("test", null, f);
            } catch (t) {}
            var s = document.createElement("div");
            t(s, {
              position: "absolute",
              left: "0",
              top: "0",
              width: "0",
              height: "0",
              zIndex: "-1",
              overflow: "hidden",
              visibility: "hidden"
            }), p.forEach(function (t) {
              n(s, t);
            }), document.body.appendChild(s), e(), u = !0;
          }
          function i(t) {
            return u || r(), d[t];
          }
          function c(t) {
            l.length || setTimeout(function () {
              var t = {};
              l.forEach(function (e) {
                t[e] = d[e];
              }), l.length = 0, h.forEach(function (e) {
                e(t);
              });
            }, 0), l.push(t);
          }
          function f(t) {
            o() && (u || r(), "function" == typeof t && h.push(t));
          }
          function s(t) {
            var e = h.indexOf(t);
            e >= 0 && h.splice(e, 1);
          }
          var u,
            a,
            p = ["top", "left", "right", "bottom"],
            d = {},
            l = [],
            h = [],
            b = {
              get support() {
                return 0 != ("string" == typeof a ? a : o()).length;
              },
              get top() {
                return i("top");
              },
              get left() {
                return i("left");
              },
              get right() {
                return i("right");
              },
              get bottom() {
                return i("bottom");
              },
              onChange: f,
              offChange: s
            };
          t.exports = b;
        }]);
      });
      _export("Application", Application = /*#__PURE__*/function () {
        function Application() {
          _classCallCheck(this, Application);
        }
        _createClass(Application, [{
          key: "init",
          value: function init(engine) {
            cc = engine;
          }
        }, {
          key: "start",
          value: function start() {
            // 手機上關閉 WEBGL_ANTIALIAS (巨集設定)
            if (cc.sys.isBrowser && cc.sys.isMobile) {
              cc.macro.ENABLE_WEBGL_ANTIALIAS = false;
            }

            // 引擎初始化
            return cc.game.init({
              settingsPath: 'src/settings.db164.json',
              overrideSettings: {
                splashScreen: {
                  enabled: false
                }
              },
              debugMode: cc.DebugMode.ERROR
            }).then(function () {
              if (cc.sys.isBrowser) {
                // 調整動態合圖最大數量
                if (cc.sys.isMobile) {
                  cc.dynamicAtlasManager.maxAtlasCount = 2;
                }
                cc.assetManager.downloader.maxConcurrency = 15;
                cc.assetManager.downloader.maxRequestsPerFrame = 64;
              }
              cc.game.run();
            });
          }
        }]);
        return Application;
      }());
    }
  };
});