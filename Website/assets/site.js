// Mobile menu toggle
(function () {
  var btn = document.querySelector('.menu');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
})();

// Chart tooltips: any element with data-tip shows it on hover or tap
(function () {
  var tip = document.createElement('div');
  tip.className = 'tip';
  document.body.appendChild(tip);
  function show(e) {
    var t = e.currentTarget.getAttribute('data-tip');
    if (!t) return;
    tip.textContent = t;
    tip.style.display = 'block';
    move(e);
  }
  function move(e) {
    var x = (e.touches ? e.touches[0].clientX : e.clientX) + 12;
    var y = (e.touches ? e.touches[0].clientY : e.clientY) + 12;
    if (x + 290 > window.innerWidth) x = window.innerWidth - 290;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = y + 'px';
  }
  function hide() { tip.style.display = 'none'; }
  document.querySelectorAll('[data-tip]').forEach(function (el) {
    el.addEventListener('mouseenter', show);
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', hide);
    el.addEventListener('touchstart', show, { passive: true });
  });
  document.addEventListener('scroll', hide, { passive: true });
})();
