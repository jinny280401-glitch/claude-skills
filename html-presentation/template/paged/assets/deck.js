/* deck.js — 分页式演示引擎（Engine·paged 模式）
   职责：等比缩放 16:9、键盘翻页、页码 HUD、全屏、讲师备注浮层、刷新恢复页码、QA 定位。
   与内容无关；每页内容写在 index.html 的 .slide 里，讲师备注写在该页的 <template class="notes-src">。
   命名空间 Deck。放映时间轴接口（narration key）在每页 data-key 上。 */
(function(){
'use strict';
var Deck = window.Deck = window.Deck || {};
var KEY = 'html-presentation-deck';          // localStorage 键：刷新恢复当前页

var slides = [], idx = 0;
var $stage, $deck, $hud, $notes, $help;

function clamp(n,a,b){ return Math.min(b, Math.max(a, n)); }

/* 等比缩放：把 1280x720 塞进视口（留 2% 边距），投影不同分辨率都铺满不溢出 */
function fit(){
  var vw = window.innerWidth, vh = window.innerHeight;
  var s = Math.min(vw/1280, vh/720) * 0.98;
  $deck.style.setProperty('--fit', s);
}

function render(){
  slides.forEach(function(s,i){
    s.classList.toggle('current', i===idx);
    s.classList.remove('leaving');
  });
  updateHud();
  if ($notes.classList.contains('on')) fillNotes();
  try{ localStorage.setItem(KEY, String(idx)); }catch(e){}
  if (location.hash.slice(1) !== String(idx+1)) {
    history.replaceState(null,'', '#'+(idx+1));
  }
  var cur = slides[idx];
  Deck._stop = cur ? (cur.dataset.key||('p'+(idx+1))) : null;   // narration key（录音时间轴接口）
}

function go(n){
  n = clamp(n, 0, slides.length-1);
  if (n===idx) return;
  var prev = slides[idx];
  if (prev){ prev.classList.add('leaving'); prev.classList.remove('current'); }
  idx = n;
  render();
}
function next(){ go(idx+1); }
function prev(){ go(idx-1); }

function updateHud(){
  if (!$hud) return;
  $hud.innerHTML = '<b>'+(idx+1)+'</b><span class="dim"> / '+slides.length+'</span>';
}

/* 讲师备注：从当前页的 <template class="notes-src"> 取，渲染进浮层；与屏幕内容分离 */
function fillNotes(){
  var tpl = slides[idx].querySelector('template.notes-src');
  var title = slides[idx].getAttribute('data-title') || ('第 '+(idx+1)+' 页');
  $notes.innerHTML = '<h4>讲师备注 · P'+(idx+1)+'　'+title+'</h4>' +
    (tpl ? tpl.innerHTML : '<p class="np">（本页无备注）</p>') +
    '<div class="hint">S / N 收起备注　·　← → 翻页　·　空格 下一页　·　F 全屏　·　? 帮助</div>';
}
function toggleNotes(){
  var on = !$notes.classList.contains('on');
  $notes.classList.toggle('on', on);
  if (on) fillNotes();
}

function fullscreen(){
  var d=document, el=d.documentElement;
  var on = d.fullscreenElement||d.webkitFullscreenElement;
  var fn = on ? (d.exitFullscreen||d.webkitExitFullscreen) : (el.requestFullscreen||el.webkitRequestFullscreen);
  if (fn){ var r=fn.call(on?d:el); if(r&&r.catch) r.catch(function(){}); }
}
function toggleHelp(){ $help.classList.toggle('on'); }

function onKey(e){
  if (e.metaKey||e.ctrlKey||e.altKey) return;
  var k = e.key;
  if (k==='ArrowRight'||k==='PageDown'||k===' '){ e.preventDefault(); next(); }
  else if (k==='ArrowLeft'||k==='PageUp'){ e.preventDefault(); prev(); }
  else if (k==='Home'){ e.preventDefault(); go(0); }
  else if (k==='End'){ e.preventDefault(); go(slides.length-1); }
  else if (k==='f'||k==='F'){ e.preventDefault(); fullscreen(); }
  else if (k==='s'||k==='S'||k==='n'||k==='N'){ e.preventDefault(); toggleNotes(); }
  else if (k==='?'||k==='/'){ e.preventDefault(); toggleHelp(); }
  else if (k==='Escape'){ $help.classList.remove('on'); }
}

Deck.boot = function(){
  $stage = document.querySelector('.stage');
  $deck  = document.querySelector('.deck');
  $hud   = document.querySelector('.hud');
  $notes = document.querySelector('.notes');
  $help  = document.querySelector('.help');
  slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));

  // 页脚页码（每页右下）
  slides.forEach(function(s,i){
    var f = s.querySelector('.footer .seq');
    if (f) f.textContent = String(i+1).padStart(2,'0') + ' / ' + String(slides.length).padStart(2,'0');
  });

  // 起始页：URL hash (#3) > QA 参数 (?p=3) > localStorage > 0
  var start = 0;
  var qp = new URLSearchParams(location.search).get('p');
  var hp = location.hash.slice(1);
  if (hp && /^\d+$/.test(hp)) start = (+hp)-1;
  else if (qp && /^\d+$/.test(qp)) start = (+qp)-1;
  else { try{ var v=localStorage.getItem(KEY); if(v!=null) start=+v; }catch(e){} }
  idx = clamp(start, 0, slides.length-1);

  var qs0 = new URLSearchParams(location.search);
  if (qs0.has('qa')) document.body.classList.add('no-anim');
  fit(); render();
  if (qs0.has('notes')) toggleNotes();
  window.addEventListener('resize', fit);
  window.addEventListener('keydown', onKey);
  // 点击右半屏下一页、左半屏上一页（投影遥控/触屏兜底）
  $stage.addEventListener('click', function(e){
    if (e.target.closest('.notes,.help,.hud')) return;
    (e.clientX > window.innerWidth*0.5 ? next : prev)();
  });
  window.addEventListener('hashchange', function(){
    var h=location.hash.slice(1); if(/^\d+$/.test(h)) go((+h)-1);
  });
};

Deck.go = function(n){ go(n-1); };   // 1-based 供控制台/QA 调用
Deck.next = next; Deck.prev = prev;
})();
