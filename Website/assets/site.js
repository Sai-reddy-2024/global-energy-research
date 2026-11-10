// Global Energy Analysis: navigation, theme toggle and charts (no external libraries)
(function () {
  // ---------- menu and theme
  var btn = document.querySelector('.menu'), nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  document.querySelectorAll('.droptoggle').forEach(function (b) {
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      var d = b.parentNode, open = d.classList.toggle('open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.drop.open').forEach(function (d) { d.classList.remove('open'); });
  });
  var tbtn = document.querySelector('.theme');
  if (tbtn) tbtn.addEventListener('click', function () {
    var root = document.documentElement;
    var cur = root.getAttribute('data-theme') ||
      (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
    drawAll();
  });

  // ---------- tooltip
  var tip = document.createElement('div');
  tip.className = 'tip'; tip.setAttribute('role', 'status');
  document.body.appendChild(tip);
  function showTip(htmlText, x, y) {
    tip.innerHTML = htmlText; tip.style.display = 'block';
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var left = x + 14, top = y + 14;
    if (left + w > window.innerWidth - 8) left = x - w - 14;
    if (top + h > window.innerHeight - 8) top = y - h - 14;
    tip.style.left = Math.max(8, left) + 'px'; tip.style.top = Math.max(8, top) + 'px';
  }
  function hideTip() { tip.style.display = 'none'; }
  window.addEventListener('scroll', hideTip, { passive: true });

  // ---------- helpers
  var NS = 'http://www.w3.org/2000/svg';
  function el(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function slot(n) { return css('--series-' + n); }
  function fmt(v, d) {
    if (v == null || isNaN(v)) return '–';
    return Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function niceStep(range, count) {
    var raw = range / count, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p;
    return (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p;
  }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function t(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)); }
  function dateLabel(ms, mode, long) {
    var d = new Date(ms);
    if (mode === 'year') return String(d.getUTCFullYear());
    if (mode === 'month') return (long ? d.getUTCDate() + ' ' : '') + MON[d.getUTCMonth()];
    return long ? d.getUTCDate() + ' ' + MON[d.getUTCMonth()] + ' ' + d.getUTCFullYear()
                : MON[d.getUTCMonth()] + ' ' + String(d.getUTCFullYear()).slice(2);
  }
  function legend(host, items) {
    var lg = document.createElement('div'); lg.className = 'legend';
    items.forEach(function (it) {
      var s = document.createElement('span');
      s.innerHTML = '<i class="' + (it.band ? 'band' : '') + '" style="background:' + it.color + '"></i>' + it.name;
      lg.appendChild(s);
    });
    host.appendChild(lg);
  }

  // ---------- line chart (time x-axis, one y-axis)
  function line(host, spec) {
    var W = host.clientWidth, H = W < 480 ? 220 : 260, L = 46, R = 14, T = 12, B = 28;
    var series = spec.series.map(function (s) {
      return { name: s.name, color: slot(s.slot), pts: s.data.map(function (p) { return [t(p[0]), p[1]]; }) };
    });
    var band = spec.band ? spec.band.data.map(function (p) { return [t(p[0]), p[1], p[2]]; }) : null;
    var xs = [], ys = [];
    series.forEach(function (s) { s.pts.forEach(function (p) { xs.push(p[0]); ys.push(p[1]); }); });
    if (band) band.forEach(function (p) { xs.push(p[0]); ys.push(p[1], p[2]); });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    var lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys);
    if (spec.zero || lo > 0 && lo < (hi - lo) * 0.6) lo = Math.min(0, lo);
    if (spec.yMax != null) hi = Math.max(hi, spec.yMax);
    var step = niceStep(hi - lo || 1, 4);
    lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
    var X = function (v) { return L + (W - L - R) * (v - x0) / ((x1 - x0) || 1); };
    var Y = function (v) { return T + (H - T - B) * (1 - (v - lo) / ((hi - lo) || 1)); };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'img', 'aria-label': spec.title || '' }, host);
    for (var g = lo; g <= hi + 1e-9; g += step) {
      el('line', { x1: L, x2: W - R, y1: Y(g), y2: Y(g), class: g === 0 && lo < 0 ? 'zero' : 'grid' }, svg);
      el('text', { x: L - 6, y: Y(g) + 4, class: 'axis', 'text-anchor': 'end' }, svg).textContent = fmt(g, step < 1 ? 1 : 0);
    }
    var n = Math.max(2, Math.min(6, Math.floor((W - L - R) / 90)));
    for (var i = 0; i <= n; i++) {
      var xv = x0 + (x1 - x0) * i / n;
      el('text', { x: X(xv), y: H - 8, class: 'axis', 'text-anchor': i === 0 ? 'start' : i === n ? 'end' : 'middle' }, svg).textContent = dateLabel(xv, spec.xfmt);
    }
    if (band) {
      var d = band.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]) + ',' + Y(p[2]); }).join('') +
              band.slice().reverse().map(function (p) { return 'L' + X(p[0]) + ',' + Y(p[1]); }).join('') + 'Z';
      el('path', { d: d, class: 'bandfill' }, svg);
    }
    series.slice().reverse().forEach(function (s) {
      var d = s.pts.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1); }).join('');
      el('path', { d: d, fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
      var last = s.pts[s.pts.length - 1];
      if (last) el('circle', { cx: X(last[0]), cy: Y(last[1]), r: 4, fill: s.color, stroke: css('--surface'), 'stroke-width': 2 }, svg);
    });
    var items = series.map(function (s) { return { name: s.name, color: s.color }; });
    if (band) items.push({ name: spec.band.name, color: css('--band'), band: true });
    if (items.length > 1) legend(host, items);
    // crosshair
    var cross = el('line', { y1: T, y2: H - B, class: 'cross', visibility: 'hidden' }, svg);
    var dots = series.map(function (s) { return el('circle', { r: 4, fill: s.color, stroke: css('--surface'), 'stroke-width': 2, visibility: 'hidden' }, svg); });
    var hit = el('rect', { x: L, y: T, width: W - L - R, height: H - T - B, fill: 'transparent' }, svg);
    function nearest(pts, xv) {
      var best = null, bd = Infinity;
      for (var i = 0; i < pts.length; i++) { var dd = Math.abs(pts[i][0] - xv); if (dd < bd) { bd = dd; best = pts[i]; } }
      return best;
    }
    function move(ev) {
      var r = svg.getBoundingClientRect(), cx = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left;
      var xv = x0 + (cx - L) / (W - L - R) * (x1 - x0);
      var ref = nearest(series[0].pts, xv) || [xv];
      cross.setAttribute('x1', X(ref[0])); cross.setAttribute('x2', X(ref[0])); cross.setAttribute('visibility', 'visible');
      var rows = '<b>' + dateLabel(ref[0], spec.xfmt, true) + '</b>';
      series.forEach(function (s, i) {
        var p = nearest(s.pts, ref[0]);
        if (p && Math.abs(p[0] - ref[0]) < 40 * 864e5) {
          dots[i].setAttribute('cx', X(p[0])); dots[i].setAttribute('cy', Y(p[1])); dots[i].setAttribute('visibility', 'visible');
          rows += '<div><i style="background:' + s.color + '"></i>' + s.name + ' <b>' + fmt(p[1], spec.decimals != null ? spec.decimals : 2) + '</b> ' + (spec.unit || '') + '</div>';
        } else dots[i].setAttribute('visibility', 'hidden');
      });
      if (band) {
        var b = nearest(band, ref[0]);
        if (b) rows += '<div class="muted">' + spec.band.name + ': ' + fmt(b[1], 0) + '–' + fmt(b[2], 0) + ' ' + (spec.unit || '') + '</div>';
      }
      showTip(rows, ev.touches ? ev.touches[0].clientX : ev.clientX, ev.touches ? ev.touches[0].clientY : ev.clientY);
    }
    function leave() { cross.setAttribute('visibility', 'hidden'); dots.forEach(function (d) { d.setAttribute('visibility', 'hidden'); }); hideTip(); }
    hit.addEventListener('mousemove', move); hit.addEventListener('mouseleave', leave);
    hit.addEventListener('touchstart', move, { passive: true }); hit.addEventListener('touchmove', move, { passive: true });
    hit.addEventListener('touchend', leave);
  }

  // ---------- horizontal bars (one or more series per category)
  function bars(host, spec) {
    var W = host.clientWidth, cats = spec.categories, ser = spec.series;
    var labelW = Math.min(170, Math.max(90, W * 0.32)), R = 64, barH = ser.length > 1 ? 12 : 18, gap = 2, groupGap = 12;
    var groupH = ser.length * barH + (ser.length - 1) * gap;
    var H = cats.length * (groupH + groupGap) + 6;
    var max = 0;
    ser.forEach(function (s) { s.values.forEach(function (v) { if (v > max) max = v; }); });
    var X = function (v) { return (W - labelW - R) * v / (max || 1); };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'img' }, host);
    cats.forEach(function (c, i) {
      var y0 = 3 + i * (groupH + groupGap);
      var lab = el('text', { x: labelW - 10, y: y0 + groupH / 2 + 4, class: 'lbl', 'text-anchor': 'end' }, svg);
      lab.textContent = c.length > 26 ? c.slice(0, 25) + '…' : c;
      ser.forEach(function (s, j) {
        var v = s.values[i]; if (v == null) return;
        var y = y0 + j * (barH + gap), w = Math.max(2, X(v)), color = slot(s.slot);
        var g = el('g', { class: 'hitbar' }, svg);
        var r = Math.min(4, w / 2);
        el('path', { d: 'M' + labelW + ',' + y + 'h' + (w - r) + 'a' + r + ',' + r + ' 0 0 1 ' + r + ',' + r + 'v' + (barH - 2 * r) + 'a' + r + ',' + r + ' 0 0 1 -' + r + ',' + r + 'h-' + (w - r) + 'z', fill: color }, g);
        el('text', { x: labelW + w + 6, y: y + barH / 2 + 4, class: 'val' }, g).textContent = fmt(v, spec.decimals != null ? spec.decimals : 1);
        el('rect', { x: 0, y: y - gap / 2, width: W, height: barH + gap, fill: 'transparent' }, g);
        var text = '<b>' + c + '</b><div><i style="background:' + color + '"></i>' + s.name + ' <b>' + fmt(v, spec.decimals != null ? spec.decimals : 1) + '</b> ' + (spec.unit || '') + '</div>';
        g.addEventListener('mousemove', function (ev) { showTip(text, ev.clientX, ev.clientY); });
        g.addEventListener('mouseleave', hideTip);
        g.addEventListener('touchstart', function (ev) { showTip(text, ev.touches[0].clientX, ev.touches[0].clientY); }, { passive: true });
      });
    });
    if (ser.length > 1) legend(host, ser.map(function (s) { return { name: s.name, color: slot(s.slot) }; }));
  }

  // ---------- floating range bars (low to high)
  function ranges(host, spec) {
    var W = host.clientWidth, rows = spec.rows, labelW = Math.min(170, Math.max(100, W * 0.32)), R = 20, barH = 14, gapY = 12, top = 6, axisH = 22;
    var H = rows.length * (barH + gapY) + top + axisH;
    var max = 0; rows.forEach(function (r) { if (r[2] > max) max = r[2]; });
    var step = niceStep(max, 5); max = Math.ceil(max / step) * step;
    var X = function (v) { return labelW + (W - labelW - R) * v / max; };
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'img' }, host);
    for (var g = 0; g <= max + 1e-9; g += step) {
      el('line', { x1: X(g), x2: X(g), y1: top, y2: H - axisH, class: 'grid' }, svg);
      el('text', { x: X(g), y: H - 6, class: 'axis', 'text-anchor': 'middle' }, svg).textContent = fmt(g, 0);
    }
    var color = slot(1);
    rows.forEach(function (r, i) {
      var y = top + i * (barH + gapY);
      el('text', { x: labelW - 10, y: y + barH / 2 + 4, class: 'lbl', 'text-anchor': 'end' }, svg).textContent = r[0].length > 26 ? r[0].slice(0, 25) + '…' : r[0];
      var g = el('g', { class: 'hitbar' }, svg);
      el('rect', { x: X(r[1]), y: y, width: Math.max(2, X(r[2]) - X(r[1])), height: barH, rx: 4, fill: color }, g);
      el('rect', { x: 0, y: y - gapY / 2, width: W, height: barH + gapY, fill: 'transparent' }, g);
      var text = '<b>' + r[0] + '</b><div>' + fmt(r[1], 0) + '–' + fmt(r[2], 0) + ' ' + spec.unit + '</div>';
      g.addEventListener('mousemove', function (ev) { showTip(text, ev.clientX, ev.clientY); });
      g.addEventListener('mouseleave', hideTip);
      g.addEventListener('touchstart', function (ev) { showTip(text, ev.touches[0].clientX, ev.touches[0].clientY); }, { passive: true });
    });
  }

  // ---------- draw everything, redraw on resize and theme change
  var vizzes = Array.prototype.slice.call(document.querySelectorAll('.viz[data-spec]'));
  function drawAll() {
    vizzes.forEach(function (host) {
      var spec; try { spec = JSON.parse(host.getAttribute('data-spec')); } catch (e) { return; }
      host.innerHTML = '';
      if (spec.type === 'line') line(host, spec);
      else if (spec.type === 'bar') bars(host, spec);
      else if (spec.type === 'range') ranges(host, spec);
    });
  }
  drawAll();
  var lastW = window.innerWidth, timer;
  window.addEventListener('resize', function () {
    if (window.innerWidth === lastW) return;
    lastW = window.innerWidth; clearTimeout(timer); timer = setTimeout(drawAll, 150);
  });
  if (window.matchMedia) {
    var mq = matchMedia('(prefers-color-scheme: dark)');
    if (mq.addEventListener) mq.addEventListener('change', drawAll);
  }
})();
