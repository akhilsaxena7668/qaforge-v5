/**
 * QAForge Landing — Particle Canvas + Animations
 * SCROLL JUMP FIX: smoothScroll() accounts for fixed nav height
 */
(function () {
  "use strict";

  /* ── SMOOTH SCROLL with nav offset (fixes jump) ── */
  window.smoothScroll = function (id) {
    const el = document.getElementById(id);
    if (!el) return;
    const navH = document.getElementById("mainNav")?.offsetHeight || 64;
    const top  = el.getBoundingClientRect().top + window.scrollY - navH;
    window.scrollTo({ top, behavior: "smooth" });
  };

  /* ── CANVAS PARTICLES ── */
  const canvas = document.getElementById("bgCanvas");
  const ctx    = canvas.getContext("2d");
  let W, H, particles = [], frame = 0;
  
  function getThemeColors() {
    const style = getComputedStyle(document.documentElement);
    return [
      style.getPropertyValue('--primary').trim() || "#00e5ff",
      style.getPropertyValue('--accent-1').trim() || "#bf5fff",
      style.getPropertyValue('--accent-2').trim() || "#39ff14",
      style.getPropertyValue('--accent-3').trim() || "#ff6b35"
    ];
  }
  let COLORS = getThemeColors();
  
  // Update colors when theme changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'qaf-theme') {
      setTimeout(() => { COLORS = getThemeColors(); }, 50);
    }
  });

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", () => { resize(); initParticles(); });
  resize();

  class Particle {
    constructor() { this.reset(true); }
    reset(init = false) {
      this.x  = Math.random() * W;
      this.y  = init ? Math.random() * H : H + 10;
      this.vx = (Math.random() - 0.5) * 0.35;
      this.vy = -(Math.random() * 0.45 + 0.1);
      this.r  = Math.random() * 1.5 + 0.4;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.alpha = Math.random() * 0.45 + 0.08;
      this.life  = 0;
      this.maxLife = Math.random() * 450 + 200;
      this.type = Math.random() > 0.85 ? "node" : "dot";
      if (this.type === "node") { this.r = Math.random() * 3 + 1.5; this.pulse = 0; }
    }
    update() {
      this.x += this.vx; this.y += this.vy; this.life++;
      if (this.type === "node") this.pulse += 0.04;
      if (this.x < -60) this.x = W + 60;
      if (this.x > W + 60) this.x = -60;
      if (this.y < -60 || this.life > this.maxLife) this.reset();
    }
    draw() {
      const fade = Math.min(this.life/60,1) * Math.min((this.maxLife-this.life)/60,1);
      ctx.globalAlpha = this.alpha * fade;
      if (this.type === "node") {
        const pr = this.r + Math.sin(this.pulse) * 1.5;
        ctx.beginPath(); ctx.arc(this.x, this.y, pr, 0, Math.PI*2);
        ctx.fillStyle = this.color; ctx.fill();
        ctx.beginPath(); ctx.arc(this.x, this.y, pr+4+Math.sin(this.pulse)*2, 0, Math.PI*2);
        ctx.strokeStyle = this.color; ctx.lineWidth = 0.4;
        ctx.globalAlpha = this.alpha * fade * 0.25; ctx.stroke();
      } else {
        ctx.beginPath(); ctx.arc(this.x, this.y, this.r, 0, Math.PI*2);
        ctx.fillStyle = this.color; ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
  }

  function initParticles() {
    const count = Math.floor((W * H) / 14000);
    particles = Array.from({ length: count }, () => new Particle());
  }
  initParticles();

  function drawConnections() {
    const nodes = particles.filter(p => p.type === "node");
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i+1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
        const d = Math.sqrt(dx*dx + dy*dy);
        if (d < 150) {
          ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = nodes[i].color; ctx.lineWidth = 0.4;
          ctx.globalAlpha = (1 - d/150) * 0.1; ctx.stroke(); ctx.globalAlpha = 1;
        }
      }
    }
  }

  function drawHex() {
    const sz = 60, cols = Math.ceil(W/(sz*1.5))+2, rows = Math.ceil(H/(sz*Math.sqrt(3)))+2;
    ctx.strokeStyle = "rgba(0,229,255,0.02)"; ctx.lineWidth = 0.5;
    for (let r = -1; r < rows; r++) for (let c = -1; c < cols; c++) {
      const x = c*sz*1.5, y = r*sz*Math.sqrt(3)+(c%2===0?0:sz*Math.sqrt(3)/2);
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI/3)*i - Math.PI/6;
        i===0 ? ctx.moveTo(x+sz*.5*Math.cos(a), y+sz*.5*Math.sin(a)) : ctx.lineTo(x+sz*.5*Math.cos(a), y+sz*.5*Math.sin(a));
      }
      ctx.closePath(); ctx.stroke();
    }
  }

  let scanY = 0;
  function drawScanLine() {
    scanY = (scanY + 0.4) % H;
    const g = ctx.createLinearGradient(0, scanY-50, 0, scanY+50);
    g.addColorStop(0,"rgba(0,229,255,0)"); g.addColorStop(.5,"rgba(0,229,255,0.015)"); g.addColorStop(1,"rgba(0,229,255,0)");
    ctx.fillStyle = g; ctx.fillRect(0, scanY-50, W, 100);
  }

  let scrollY = 0;
  // SCROLL JUMP FIX: passive listener so scroll isn't blocked
  window.addEventListener("scroll", () => { scrollY = window.scrollY; }, { passive: true });

  function drawGrid() {
    const off = (frame*0.25 + scrollY*0.08) % 60;
    ctx.strokeStyle = "rgba(0,229,255,0.025)"; ctx.lineWidth = 0.5;
    for (let x = -off; x < W; x+=60) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
    for (let y = -off; y < H; y+=60) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
  }

  function animate() {
    requestAnimationFrame(animate);
    ctx.clearRect(0, 0, W, H);
    const bg = ctx.createRadialGradient(W*.3,H*.4,0,W*.3,H*.4,W*.8);
    bg.addColorStop(0,"rgba(0,18,36,0.35)"); bg.addColorStop(1,"rgba(2,8,16,0)");
    ctx.fillStyle = bg; ctx.fillRect(0,0,W,H);
    drawGrid(); drawHex(); drawConnections();
    particles.forEach(p => { p.update(); p.draw(); });
    drawScanLine(); frame++;
  }
  animate();

  /* ── CURSOR GLOW ── */
  const glow = document.getElementById("cursorGlow");
  // SCROLL JUMP FIX: use requestAnimationFrame for cursor to avoid layout thrashing
  let mx = 0, my = 0;
  document.addEventListener("mousemove", e => { mx = e.clientX; my = e.clientY; }, { passive: true });
  function moveCursor() { glow.style.left = mx+"px"; glow.style.top = my+"px"; requestAnimationFrame(moveCursor); }
  moveCursor();

  /* ── NAVBAR SCROLL ── */
  const nav = document.getElementById("mainNav");
  window.addEventListener("scroll", () => {
    nav.classList.toggle("scrolled", window.scrollY > 50);
  }, { passive: true });

  /* ── SCROLL REVEAL ── */
  const revEls = document.querySelectorAll(".reveal");
  const obs = new IntersectionObserver(entries => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        setTimeout(() => e.target.classList.add("visible"), i * 70);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });
  revEls.forEach(el => obs.observe(el));

  /* ── TYPEWRITER ── */
  const phrases = ["BEFORE USERS DO","BEFORE LAUNCH DAY","WITH GEMINI AI","AUTOMATICALLY","ACROSS ALL PLATFORMS"];
  let pi = 0, ci = 0, del = false;
  const typedEl = document.getElementById("typedLine");
  if (typedEl) {
    function tick() {
      const phrase = phrases[pi];
      if (!del) {
        ci++; typedEl.textContent = phrase.slice(0, ci);
        if (ci === phrase.length) { del = true; setTimeout(tick, 2200); return; }
      } else {
        ci--; typedEl.textContent = phrase.slice(0, ci);
        if (ci === 0) { del = false; pi = (pi+1)%phrases.length; }
      }
      setTimeout(tick, del ? 40 : 75);
    }
    setTimeout(tick, 2000);
  }

  /* ── COUNT-UP STATS ── */
  document.querySelectorAll(".stn[data-target]").forEach(el => {
    const target = parseInt(el.dataset.target);
    const cObs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        let cur = 0; const inc = target/40;
        const t = setInterval(() => {
          cur = Math.min(cur+inc, target);
          el.textContent = Math.floor(cur);
          if (cur >= target) clearInterval(t);
        }, 28);
        cObs.disconnect();
      }
    }, { threshold: 0.5 });
    cObs.observe(el);
  });

  /* ── GLITCH EFFECT ── */
  const heroTitle = document.querySelector(".hero-title");
  if (heroTitle) {
    setInterval(() => {
      heroTitle.style.textShadow = `${(Math.random()-0.5)*4}px 0 rgba(0,229,255,0.5)`;
      setTimeout(() => heroTitle.style.textShadow = "", 70);
    }, 4500);
  }

})();
