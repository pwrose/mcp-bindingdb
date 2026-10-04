/* Interactive scatter layer for Figures 1 and 3.
   Falls back silently to the static PNG if anything here is unsupported. */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";

  var DARK_SERIES = ["#3987e5","#d95926","#199e70","#c98500","#d55181",
                     "#008300","#9085e9","#e66767"];
  var RAMP_L = ["#cde2fb","#9ec5f4","#6da7ec","#3987e5","#256abf","#184f95","#0d366b"];

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] !== null && attrs[k] !== undefined)
      e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, cls, parent, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    if (parent) parent.appendChild(e);
    return e;
  }
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t === "dark") return true;
    if (t === "light") return false;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  /* ---- marker shapes, matching the matplotlib markers in the static figures ---- */
  function symbol(mk, x, y, s) {
    var r = s, p;
    function poly(n, rot, inner) {
      var d = [], i, ang, rad;
      for (i = 0; i < n * (inner ? 2 : 1); i++) {
        ang = rot + i * Math.PI * 2 / (n * (inner ? 2 : 1));
        rad = inner && (i % 2) ? r * inner : r;
        d.push((i ? "L" : "M") + (x + rad * Math.cos(ang)).toFixed(1) + "," +
               (y + rad * Math.sin(ang)).toFixed(1));
      }
      return d.join(" ") + "Z";
    }
    switch (mk) {
      case "s": return "M" + (x-r) + "," + (y-r) + "h" + 2*r + "v" + 2*r + "h" + (-2*r) + "Z";
      case "^": return poly(3, -Math.PI/2);
      case "v": return poly(3, Math.PI/2);
      case "<": return poly(3, Math.PI);
      case ">": return poly(3, 0);
      case "D": return poly(4, -Math.PI/2);
      case "p": return poly(5, -Math.PI/2);
      case "h": return poly(6, -Math.PI/2);
      case "*": return poly(5, -Math.PI/2, 0.45);
      case "P": p = r*0.42; return "M" + (x-p) + "," + (y-r) + "h" + 2*p + "v" + (r-p) +
                 "h" + (r-p) + "v" + 2*p + "h" + (-(r-p)) + "v" + (r-p) + "h" + (-2*p) +
                 "v" + (-(r-p)) + "h" + (-(r-p)) + "v" + (-2*p) + "h" + (r-p) + "Z";
      case "X": p = r*0.40;
        return "M" + x + "," + (y-p*1.4) + "l" + p*1.4 + "," + (-p*1.4) + "l" + p*1.4 + "," + p*1.4 +
               "l" + (-p*1.4) + "," + p*1.4 + "l" + p*1.4 + "," + p*1.4 + "l" + (-p*1.4) + "," + p*1.4 +
               "l" + (-p*1.4) + "," + (-p*1.4) + "l" + (-p*1.4) + "," + p*1.4 + "l" + (-p*1.4) + "," + (-p*1.4) +
               "l" + p*1.4 + "," + (-p*1.4) + "l" + (-p*1.4) + "," + (-p*1.4) + "l" + p*1.4 + "," + (-p*1.4) + "Z";
      default: return null; /* circle */
    }
  }
  function mkNode(mk, x, y, s, attrs) {
    var d = symbol(mk, x, y, s);
    if (d === null) { attrs.cx = x; attrs.cy = y; attrs.r = s; return ["circle", attrs]; }
    attrs.d = d; return ["path", attrs];
  }

  function ticks(lo, hi, n) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log(span / n) / Math.LN10)),
        err = span / n / step, out = [], v;
    if (err >= 7.5) step *= 10; else if (err >= 3) step *= 5; else if (err >= 1.5) step *= 2;
    for (v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }
  function lerpColor(a, b, t) {
    function p(c){return [parseInt(c.substr(1,2),16),parseInt(c.substr(3,2),16),parseInt(c.substr(5,2),16)];}
    var A = p(a), B = p(b);
    return "rgb(" + A.map(function (v, i) { return Math.round(v + (B[i]-v)*t); }).join(",") + ")";
  }
  function rampColor(t) {
    t = Math.max(0, Math.min(1, t));
    var i = t * (RAMP_L.length - 1), k = Math.floor(i);
    if (k >= RAMP_L.length - 1) return RAMP_L[RAMP_L.length - 1];
    return lerpColor(RAMP_L[k], RAMP_L[k+1], i - k);
  }

  /* ---------------------------------------------------------------- */
  function build(DATA) {
    var P = DATA.points, CT = DATA.chemotypes, MK = DATA.markers;
    var colors = DATA.colors.slice();
    var pLo = Math.min.apply(null, P.map(function (d) { return d.p; }));
    var pHi = Math.max.apply(null, P.map(function (d) { return d.p; }));
    var hidden = {};                 /* chemotype index -> hidden */
    var selected = null;             /* point object */
    var views = [];                  /* redraw hooks */

    function seriesColor(c) { return (isDark() ? DARK_SERIES : DATA.colors)[c % 8]; }

    function tooltip() {
      var t = h("div", "ipt-tip");
      t.style.display = "none";
      document.body.appendChild(t);
      return t;
    }
    var TIP = tooltip();
    function showTip(e, d) {
      TIP.innerHTML = "<b>" + esc(d.n) + "</b><br>" + esc(CT[d.c]) +
        "<br>pK<sub>i</sub> " + (d.rel === "=" ? "" : (d.rel === ">" ? "&lt;" : "&gt;")) + d.p.toFixed(2);
      TIP.style.display = "block";
      var r = TIP.getBoundingClientRect();
      var x = e.clientX + 14, y = e.clientY + 14;
      if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 14;
      if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - 14;
      TIP.style.left = (x + window.scrollX) + "px";
      TIP.style.top = (y + window.scrollY) + "px";
    }
    function hideTip() { TIP.style.display = "none"; }
    function esc(s) {
      return String(s).replace(/[&<>"]/g, function (c) {
        return { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c]; });
    }

    /* ---------- details card ---------- */
    function card(host) {
      var box = h("div", "ipt-card", host);
      function render() {
        box.innerHTML = "";
        if (!selected) {
          h("p", "ipt-empty", box,
            "Select a point to see its structure and measurement details.");
          return;
        }
        var d = selected;
        var strux = h("div", "ipt-strux", box);
        strux.innerHTML = d.g;
        var meta = h("div", "ipt-meta", box);
        var head = h("div", "ipt-head", meta);
        var dot = h("span", "ipt-dot", head);
        dot.style.background = seriesColor(d.c);
        h("span", "ipt-name", head, d.n);
        var dl = h("dl", "ipt-dl", meta);
        function row(k, v, html) {
          h("dt", null, dl, k);
          var e = h("dd", null, dl);
          if (html) e.innerHTML = v; else e.textContent = v;
        }
        row("Chemotype", CT[d.c]);
        row("Kᵢ", (d.rel === "=" ? "" : d.rel + " ") + d.k.toLocaleString() + " nM" +
            (d.rel === "=" ? "" : "  (censored)"));
        row("pKᵢ", (d.rel === "=" ? "" : (d.rel === ">" ? "< " : "> ")) + d.p.toFixed(2));
        row("Measurements", d.m + (d.m > 1 ? "  (strongest kept)" : ""));
        if (d.yr) row("Year", d.yr);
        if (d.d) row("Reference",
          "<a href='https://doi.org/" + esc(d.d) + "' target='_blank' rel='noopener'>" +
          esc(d.d) + "</a>", true);
        row("SMILES", d.s);
        var sm = dl.lastChild; sm.className = "ipt-smiles";
        var btn = h("button", "ipt-copy", meta, "Copy SMILES");
        btn.addEventListener("click", function () {
          if (navigator.clipboard) navigator.clipboard.writeText(d.s).then(function () {
            btn.textContent = "Copied"; setTimeout(function(){btn.textContent="Copy SMILES";}, 1400);
          });
        });
      }
      render();
      return render;
    }

    /* ---------- legend ---------- */
    function legend(host, onChange) {
      var wrap = h("div", "ipt-legend", host);
      var items = CT.map(function (name, i) {
        var b = h("button", "ipt-lg", wrap);
        b.setAttribute("aria-pressed", "true");
        var sv = el("svg", { width: 13, height: 13, viewBox: "0 0 13 13" });
        var spec = mkNode(MK[i], 6.5, 6.5, 5, { fill: seriesColor(i) });
        el(spec[0], spec[1], sv);
        b.appendChild(sv);
        h("span", null, b, name + "  (" +
          P.filter(function (d) { return d.c === i; }).length + ")");
        b.addEventListener("click", function () {
          hidden[i] = !hidden[i];
          b.setAttribute("aria-pressed", hidden[i] ? "false" : "true");
          b.classList.toggle("off", !!hidden[i]);
          onChange();
        });
        return b;
      });
      return function () {
        items.forEach(function (b, i) {
          b.querySelector("path,circle").setAttribute("fill", seriesColor(i));
        });
      };
    }

    /* ---------- a cartesian panel ---------- */
    function panel(host, title, xKey, yKey, colorBy) {
      var W = 540, H = 440, M = { t: 10, r: 12, b: 42, l: 48 };
      var xs = P.map(function (d) { return d[xKey]; }),
          ys = P.map(function (d) { return d[yKey]; });
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs),
          y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
      var px = (x1 - x0) * 0.05, py = (y1 - y0) * 0.05;
      x0 -= px; x1 += px; y0 -= py; y1 += py;
      var sx = function (v) { return M.l + (v - x0) / (x1 - x0) * (W - M.l - M.r); };
      var sy = function (v) { return H - M.b - (v - y0) / (y1 - y0) * (H - M.t - M.b); };

      var fig = h("div", "ipt-panel", host);
      h("div", "ipt-ptitle", fig, title);
      var svg = el("svg", { viewBox: "0 0 " + W + " " + H, class: "ipt-svg",
                            role: "img", tabindex: "0" });
      svg.setAttribute("aria-label", title + " — interactive scatter, " +
        P.length + " compounds; arrow keys move between points, Enter selects");
      fig.appendChild(svg);

      var gGrid = el("g", { class: "ipt-grid" }, svg);
      var gAx = el("g", { class: "ipt-ax" }, svg);
      var gPts = el("g", {}, svg);
      var nodes = [];

      ticks(x0, x1, 6).forEach(function (t) {
        el("line", { x1: sx(t), x2: sx(t), y1: M.t, y2: H - M.b }, gGrid);
        var tx = el("text", { x: sx(t), y: H - M.b + 15, "text-anchor": "middle" }, gAx);
        tx.textContent = t;
      });
      ticks(y0, y1, 6).forEach(function (t) {
        el("line", { x1: M.l, x2: W - M.r, y1: sy(t), y2: sy(t) }, gGrid);
        var tx = el("text", { x: M.l - 7, y: sy(t) + 3.5, "text-anchor": "end" }, gAx);
        tx.textContent = t;
      });
      el("line", { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b, class: "ipt-axis" }, svg);
      el("line", { x1: M.l, x2: M.l, y1: M.t, y2: H - M.b, class: "ipt-axis" }, svg);
      var xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 6, "text-anchor": "middle",
                            class: "ipt-axlab" }, svg); xl.textContent = "t-SNE 1";
      var yl = el("text", { x: 12, y: (M.t + H - M.b) / 2, "text-anchor": "middle",
                            class: "ipt-axlab",
                            transform: "rotate(-90 12 " + ((M.t + H - M.b) / 2) + ")" }, svg);
      yl.textContent = "t-SNE 2";

      P.forEach(function (d) {
        var spec = mkNode(colorBy === "ct" ? MK[d.c] : "o", sx(d[xKey]), sy(d[yKey]), 5.5, {});
        var n = el(spec[0], spec[1], gPts);
        n.setAttribute("class", "ipt-pt");
        n.addEventListener("mousemove", function (e) { showTip(e, d); });
        n.addEventListener("mouseleave", hideTip);
        n.addEventListener("click", function (e) {
          e.stopPropagation(); selected = d; refreshAll();
        });
        nodes.push({ n: n, d: d });
      });
      svg.addEventListener("click", function () { selected = null; refreshAll(); });
      svg.addEventListener("keydown", function (e) {
        var vis = nodes.filter(function (o) { return !hidden[o.d.c]; });
        if (!vis.length) return;
        var i = selected ? vis.findIndex(function (o) { return o.d.i === selected.i; }) : -1;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          selected = vis[(i + 1) % vis.length].d; e.preventDefault(); refreshAll();
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          selected = vis[(i - 1 + vis.length) % vis.length].d; e.preventDefault(); refreshAll();
        } else if (e.key === "Escape") { selected = null; refreshAll(); }
      });

      return function () {
        nodes.forEach(function (o) {
          var d = o.d, off = hidden[d.c];
          o.n.style.display = off ? "none" : "";
          if (colorBy === "ct") {
            o.n.setAttribute("fill", seriesColor(d.c));
          } else if (d.rel !== "=") {           /* censored: open ring, as in the PNG */
            o.n.setAttribute("fill", "none");
            o.n.style.stroke = "var(--muted)";
            o.n.style.strokeWidth = "1.6";
          } else {
            o.n.setAttribute("fill", rampColor((d.p - pLo) / (pHi - pLo)));
            o.n.style.stroke = ""; o.n.style.strokeWidth = "";
          }
          o.n.classList.toggle("sel", !!(selected && selected.i === d.i));
        });
      };
    }

    /* ---------- polar (IRIS) panel ---------- */
    function polar(host) {
      var S = 580, cx = S / 2, cy = S / 2, R = S / 2 - 34;
      var fig = h("div", "ipt-panel wide", host);
      var svg = el("svg", { viewBox: "0 0 " + S + " " + S, class: "ipt-svg",
                            role: "img", tabindex: "0" });
      svg.setAttribute("aria-label", "IRIS projection — interactive, radius is pKi; " +
        "arrow keys move between points, Enter selects");
      fig.appendChild(svg);
      var sorted = P.slice().sort(function (a, b) { return a.p - b.p; });
      function rOf(pk) {                       /* interpolate pKi -> IRIS radius */
        if (pk <= sorted[0].p) return sorted[0].rr;
        for (var i = 1; i < sorted.length; i++) {
          if (pk <= sorted[i].p) {
            var a = sorted[i-1], b = sorted[i];
            var t = (b.p - a.p) ? (pk - a.p) / (b.p - a.p) : 0;
            return a.rr + (b.rr - a.rr) * t;
          }
        }
        return sorted[sorted.length - 1].rr;
      }
      var gGrid = el("g", { class: "ipt-grid" }, svg);
      var gAx = el("g", { class: "ipt-ax" }, svg);
      [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5].forEach(function (pk) {
        var rr = rOf(pk) * R;
        el("circle", { cx: cx, cy: cy, r: rr.toFixed(1), fill: "none" }, gGrid);
        var t = el("text", { x: cx + 3, y: cy - rr + 11, "text-anchor": "start" }, gAx);
        t.textContent = pk.toFixed(1);
      });
      for (var a = 0; a < 12; a++) {
        var ang = a * Math.PI / 6;
        el("line", { x1: cx, y1: cy, x2: cx + R * Math.cos(ang), y2: cy + R * Math.sin(ang) }, gGrid);
      }
      el("circle", { cx: cx, cy: cy, r: R, fill: "none", class: "ipt-axis" }, svg);
      var lab = el("text", { x: cx + 3, y: cy - R - 6, "text-anchor": "start",
                             class: "ipt-axlab" }, svg);
      lab.textContent = "pKi";

      var gPts = el("g", {}, svg), nodes = [];
      P.forEach(function (d) {
        var rr = d.rr * R, x = cx + rr * Math.cos(d.th), y = cy + rr * Math.sin(d.th);
        var spec = mkNode(MK[d.c], x, y, 5.5, {});
        var n = el(spec[0], spec[1], gPts);
        n.setAttribute("class", "ipt-pt");
        n.addEventListener("mousemove", function (e) { showTip(e, d); });
        n.addEventListener("mouseleave", hideTip);
        n.addEventListener("click", function (e) { e.stopPropagation(); selected = d; refreshAll(); });
        nodes.push({ n: n, d: d });
      });
      svg.addEventListener("click", function () { selected = null; refreshAll(); });
      svg.addEventListener("keydown", function (e) {
        var vis = nodes.filter(function (o) { return !hidden[o.d.c]; });
        if (!vis.length) return;
        var i = selected ? vis.findIndex(function (o) { return o.d.i === selected.i; }) : -1;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          selected = vis[(i + 1) % vis.length].d; e.preventDefault(); refreshAll();
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          selected = vis[(i - 1 + vis.length) % vis.length].d; e.preventDefault(); refreshAll();
        } else if (e.key === "Escape") { selected = null; refreshAll(); }
      });
      return function () {
        nodes.forEach(function (o) {
          o.n.style.display = hidden[o.d.c] ? "none" : "";
          o.n.setAttribute("fill", seriesColor(o.d.c));
          o.n.classList.toggle("sel", !!(selected && selected.i === o.d.i));
        });
      };
    }

    function refreshAll() { views.forEach(function (f) { f(); }); }

    /* ---------- mount figure 1 ---------- */
    var host1 = document.getElementById("fig1-interactive");
    if (host1) {
      var row = h("div", "ipt-row", host1);
      views.push(panel(row, "A · Chemical space by chemotype", "x", "y", "ct"));
      views.push(panel(row, "B · Same coordinates, coloured by pKᵢ", "x", "y", "pki"));
      var bar = h("div", "ipt-cbar", host1);
      h("span", "ipt-cblab", bar, pLo.toFixed(2));
      var grad = h("span", "ipt-cbgrad", bar);
      grad.style.background = "linear-gradient(to right," + RAMP_L.join(",") + ")";
      h("span", "ipt-cblab", bar, pHi.toFixed(2));
      h("span", "ipt-cbname", bar, "panel B colour = pKᵢ");
      views.push(legend(host1, refreshAll));
      views.push(card(host1));
      host1.parentNode.classList.add("live");
    }
    /* ---------- mount figure 3 ---------- */
    var host3 = document.getElementById("fig3-interactive");
    if (host3) {
      views.push(polar(host3));
      views.push(legend(host3, refreshAll));
      views.push(card(host3));
      host3.parentNode.classList.add("live");
    }
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      (mq.addEventListener ? mq.addEventListener.bind(mq, "change") :
       mq.addListener.bind(mq))(refreshAll);
    }
    refreshAll();
  }

  /* ---------------- boot ---------------- */
  async function boot() {
    var node = document.getElementById("ipt-data");
    if (!node || typeof DecompressionStream === "undefined") return;
    var bin = Uint8Array.from(atob(node.textContent.trim()), function (c) {
      return c.charCodeAt(0); });
    var ds = new DecompressionStream("gzip");
    var stream = new Blob([bin]).stream().pipeThrough(ds);
    var text = await new Response(stream).text();
    build(JSON.parse(text));
  }
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", function () { boot().catch(function(){}); });
  else boot().catch(function () {});
})();
