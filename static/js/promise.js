!function n(t, e, o) {
    function i(u, f) {
        if (!e[u]) {
            if (!t[u]) {
                var c = "function" == typeof require && require;
                if (!f && c)
                    return c(u, !0);
                if (r)
                    return r(u, !0);
                var s = new Error("Cannot find module '" + u + "'");
                throw s.code = "MODULE_NOT_FOUND", s
            }
            var a = e[u] = {
                exports: {}
            };
            t[u][0].call(a.exports, function(n) {
                var e = t[u][1][n];
                return i(e ? e : n)
            }, a, a.exports, n, t, e, o)
        }
        return e[u].exports
    }
    for (var r = "function" == typeof require && require, u = 0; u < o.length; u++)
        i(o[u]);
    return i
}({
    1: [function(n, t) {
        function e() {}
        var o = t.exports = {};
        o.nextTick = function() {
            var n = "undefined" != typeof window && window.setImmediate,
                t = "undefined" != typeof window && window.postMessage && window.addEventListener;
            if (n)
                return function(n) {
                    return window.setImmediate(n)
                };
            if (t) {
                var e = [];
                return window.addEventListener("message", function(n) {
                    var t = n.source;
                    if ((t === window || null === t) && "process-tick" === n.data && (n.stopPropagation(), e.length > 0)) {
                        var o = e.shift();
                        o()
                    }
                }, !0), function(n) {
                    e.push(n), window.postMessage("process-tick", "*")
                }
            }
            return function(n) {
                setTimeout(n, 0)
            }
        }(), o.title = "browser", o.browser = !0, o.env = {}, o.argv = [], o.on = e, o.addListener = e, o.once = e, o.off = e, o.removeListener = e, o.removeAllListeners = e, o.emit = e, o.binding = function() {
            throw new Error("process.binding is not supported")
        }, o.cwd = function() {
            return "/"
        }, o.chdir = function() {
            throw new Error("process.chdir is not supported")
        }
    }, {}],
    2: [function(n, t) {
        "use strict";
        function e(n) {
            function t(n) {
                return null === c ? void a.push(n) : void r(function() {
                    var t = c ? n.onFulfilled : n.onRejected;
                    if (null === t)
                        return void (c ? n.resolve : n.reject)(s);
                    var e;
                    try {
                        e = t(s)
                    } catch (o) {
                        return void n.reject(o)
                    }
                    n.resolve(e)
                })
            }
            function e(n) {
                try {
                    if (n === l)
                        throw new TypeError("A promise cannot be resolved with itself.");
                    if (n && ("object" == typeof n || "function" == typeof n)) {
                        var t = n.then;
                        if ("function" == typeof t)
                            return void i(t.bind(n), e, u)
                    }
                    c = !0, s = n, f()
                } catch (o) {
                    u(o)
                }
            }
            function u(n) {
                c = !1, s = n, f()
            }
            function f() {
                for (var n = 0, e = a.length; e > n; n++)
                    t(a[n]);
                a = null
            }
            if ("object" != typeof this)
                throw new TypeError("Promises must be constructed via new");
            if ("function" != typeof n)
                throw new TypeError("not a function");
            var c = null,
                s = null,
                a = [],
                l = this;
            this.then = function(n, e) {
                return new l.constructor(function(i, r) {
                    t(new o(n, e, i, r))
                })
            }, i(n, e, u)
        }
        function o(n, t, e, o) {
            this.onFulfilled = "function" == typeof n ? n : null, this.onRejected = "function" == typeof t ? t : null, this.resolve = e, this.reject = o
        }
        function i(n, t, e) {
            var o = !1;
            try {
                n(function(n) {
                    o || (o = !0, t(n))
                }, function(n) {
                    o || (o = !0, e(n))
                })
            } catch (i) {
                if (o)
                    return;
                o = !0, e(i)
            }
        }
        var r = n("asap");
        t.exports = e
    }, {
        asap: 4
    }],
    3: [function(n, t) {
        "use strict";
        function e(n) {
            this.then = function(t) {
                return "function" != typeof t ? this : new o(function(e, o) {
                    i(function() {
                        try {
                            e(t(n))
                        } catch (i) {
                            o(i)
                        }
                    })
                })
            }
        }
        var o = n("./core.js"),
            i = n("asap");
        t.exports = o, e.prototype = o.prototype;
        var r = new e(!0),
            u = new e(!1),
            f = new e(null),
            c = new e(void 0),
            s = new e(0),
            a = new e("");
        o.resolve = function(n) {
            if (n instanceof o)
                return n;
            if (null === n)
                return f;
            if (void 0 === n)
                return c;
            if (n === !0)
                return r;
            if (n === !1)
                return u;
            if (0 === n)
                return s;
            if ("" === n)
                return a;
            if ("object" == typeof n || "function" == typeof n)
                try {
                    var t = n.then;
                    if ("function" == typeof t)
                        return new o(t.bind(n))
                } catch (i) {
                    return new o(function(n, t) {
                        t(i)
                    })
                }
            return new e(n)
        }, o.all = function(n) {
            var t = Array.prototype.slice.call(n);
            return new o(function(n, e) {
                function o(r, u) {
                    try {
                        if (u && ("object" == typeof u || "function" == typeof u)) {
                            var f = u.then;
                            if ("function" == typeof f)
                                return void f.call(u, function(n) {
                                    o(r, n)
                                }, e)
                        }
                        t[r] = u, 0 === --i && n(t)
                    } catch (c) {
                        e(c)
                    }
                }
                if (0 === t.length)
                    return n([]);
                for (var i = t.length, r = 0; r < t.length; r++)
                    o(r, t[r])
            })
        }, o.reject = function(n) {
            return new o(function(t, e) {
                e(n)
            })
        }, o.race = function(n) {
            return new o(function(t, e) {
                n.forEach(function(n) {
                    o.resolve(n).then(t, e)
                })
            })
        }, o.prototype["catch"] = function(n) {
            return this.then(null, n)
        }
    }, {
        "./core.js": 2,
        asap: 4
    }],
    4: [function(n, t) {
        (function(n) {
            function e() {
                for (; i.next;) {
                    i = i.next;
                    var n = i.task;
                    i.task = void 0;
                    var t = i.domain;
                    t && (i.domain = void 0, t.enter());
                    try {
                        n()
                    } catch (o) {
                        if (c)
                            throw t && t.exit(), setTimeout(e, 0), t && t.enter(), o;
                        setTimeout(function() {
                            throw o
                        }, 0)
                    }
                    t && t.exit()
                }
                u = !1
            }
            function o(t) {
                r = r.next = {
                    task: t,
                    domain: c && n.domain,
                    next: null
                }, u || (u = !0, f())
            }
            var i = {
                    task: void 0,
                    next: null
                },
                r = i,
                u = !1,
                f = void 0,
                c = !1;
            if ("undefined" != typeof n && n.nextTick)
                c = !0, f = function() {
                    n.nextTick(e)
                };
            else if ("function" == typeof setImmediate)
                f = "undefined" != typeof window ? setImmediate.bind(window, e) : function() {
                    setImmediate(e)
                };
            else if ("undefined" != typeof MessageChannel) {
                var s = new MessageChannel;
                s.port1.onmessage = e, f = function() {
                    s.port2.postMessage(0)
                }
            } else
                f = function() {
                    setTimeout(e, 0)
                };
            t.exports = o
        }).call(this, n("_process"))
    }, {
        _process: 1
    }],
    5: [function() {
        "function" != typeof Promise.prototype.done && (Promise.prototype.done = function() {
            var n = arguments.length ? this.then.apply(this, arguments) : this;
            n.then(null, function(n) {
                setTimeout(function() {
                    throw n
                }, 0)
            })
        })
    }, {}],
    6: [function(n) {
        n("asap");
        "undefined" == typeof Promise && (Promise = n("./lib/core.js"), n("./lib/es6-extensions.js")), n("./polyfill-done.js")
    }, {
        "./lib/core.js": 2,
        "./lib/es6-extensions.js": 3,
        "./polyfill-done.js": 5,
        asap: 4
    }]
}, {}, [6]);

