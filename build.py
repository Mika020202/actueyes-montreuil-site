#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for ACTU EYES multi-page site.
Generates static HTML files from shared header/footer/CSS + per-page content,
to avoid manually duplicating markup across files.
"""
import os
import re
import json
import hashlib

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://actueyes-montreuil.fr"

# ----------------------------------------------------------------------------
# SHARED CSS (base, from original single-page site) + new components for
# multi-page layouts (page-hero, split-grid, story blocks)
# ----------------------------------------------------------------------------
SHARED_CSS = """
  :root{
    --cream:#FFFFFF;
    --cream-2:#F5F4F2;
    --wood:#9B9B96;
    --wood-dark:#3A3A38;
    --terracotta:#161616;
    --terracotta-dark:#000000;
    --charcoal:#1A1A1A;
    --charcoal-soft:#55554F;
    --sage:#6E7A66;
    --line:#E6E5E1;
    --accent-red:#C0392B;
    --shadow: 0 20px 50px -20px rgba(20,20,20,0.22);
    --radius-arch: 4px;
    --header-h: 104px;
    --hero-pos: 15%;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    font-family:'Inter',sans-serif;
    color:var(--charcoal);
    background:var(--cream);
    line-height:1.6;
    -webkit-font-smoothing:antialiased;
    overflow-x:hidden;
    /* Le header est desormais opaque en permanence (31/07/2026) : on decale
       tout le contenu de sa hauteur pour que la photo commence sous le menu
       au lieu de passer derriere. */
    padding-top:var(--header-h);
  }
  h1,h2,h3,h4{font-family:'Fraunces',serif;font-weight:500;line-height:1.15;color:var(--charcoal);}
  a{text-decoration:none;color:inherit;}
  ul{list-style:none;}
  img{max-width:100%;display:block;}
  .container{max-width:1180px;margin:0 auto;padding:0 28px;}
  .container-narrow{max-width:760px;margin:0 auto;padding:0 28px;}
  .eyebrow{
    font-family:'Inter',sans-serif;
    text-transform:uppercase;
    letter-spacing:0.18em;
    font-size:12.5px;
    font-weight:600;
    color:var(--accent-red);
    display:inline-block;
    margin-bottom:14px;
  }
  .section-head{max-width:640px;margin-bottom:56px;}
  .section-head h2{font-size:clamp(28px,3.6vw,42px);margin-bottom:14px;font-weight:400;letter-spacing:-0.4px;}
  .section-head p{color:var(--charcoal-soft);font-size:16.5px;}
  .section-head.center{margin-left:auto;margin-right:auto;text-align:center;}
  section{padding:110px 0;}
  .btn{
    display:inline-flex;align-items:center;gap:10px;
    padding:15px 30px;border-radius:3px;
    font-weight:600;font-size:14.5px;letter-spacing:0.02em;
    transition:all .25s ease; border:1.5px solid transparent; cursor:pointer;
  }
  .btn-primary{background:var(--terracotta);color:var(--cream);}
  .btn-primary:hover{background:var(--terracotta-dark);transform:translateY(-2px);box-shadow:0 12px 24px -10px rgba(163,79,44,0.55);}
  .btn-ghost{border-color:rgba(251,246,239,0.55);color:var(--cream);}
  .btn-ghost:hover{background:rgba(251,246,239,0.12);}
  .btn-outline{border-color:var(--wood-dark);color:var(--charcoal);}
  .btn-outline:hover{background:var(--wood-dark);color:var(--cream);}

  /* HEADER */
  header{
    position:fixed;top:0;left:0;right:0;z-index:100;
    padding:22px 0; transition:all .35s ease;
  }
  header.scrolled{
    background:rgba(255,255,255,0.96);
    border-bottom:2.5px solid #C0392B;
    backdrop-filter:blur(10px);
    padding:5px 0;
    box-shadow:0 6px 24px -16px rgba(20,20,20,0.18);
  }
  header .container{display:flex;align-items:center;justify-content:space-between;min-height:78px;}
  .logo{display:flex;align-items:center;gap:12px;font-family:'Fraunces',serif;}
  .logo-img{height:90px;width:auto;display:block;}
  .footer-logo-img{height:40px;width:auto;display:block;}
  .logo-mark{
    width:42px;height:42px;border-radius:50%;background:var(--terracotta);
    color:var(--cream);display:flex;align-items:center;justify-content:center;
    font-size:19px;flex-shrink:0;
  }
  .logo{flex-shrink:0;}
  .logo-text{line-height:1.1;}
  .logo-text .name{font-size:17px;font-weight:600;color:var(--cream);transition:color .35s;white-space:nowrap;}
  header.scrolled .logo-text .name{color:var(--charcoal);}
  .logo-text .tag{font-family:'Inter',sans-serif;font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(251,246,239,0.75);transition:color .35s;white-space:nowrap;}
  header.scrolled .logo-text .tag{color:var(--wood-dark);}
  /* La marge negative compense le rembourrage horizontal des bulles : sans
     elle, les six onglets occuperaient ~120px de plus qu'avant et viendraient
     toucher le logo autour de 1000px de large. */
  nav.main-nav{display:flex;align-items:center;gap:0;flex-shrink:1;margin:0 -12px;}
  nav.main-nav a{
    font-size:13px;font-weight:500;color:var(--cream);position:relative;
    padding:8px 12px;border-radius:100px;border:1px solid transparent;
    transition:color .35s, background .25s ease, border-color .25s ease;white-space:nowrap;
  }
  header.scrolled nav.main-nav a{color:var(--charcoal-soft);}
  nav.main-nav a:hover{color:var(--terracotta);}
  /* Onglet de la page en cours : bulle « voile translucide » (piste 1 validee
     par le client le 30/07/2026). Le marquage .active est deja emis par
     render_header(), donc c'est un changement purement CSS. */
  nav.main-nav a.active{
    background:rgba(251,246,239,0.18);
    border-color:rgba(251,246,239,0.30);
    color:var(--cream);
  }
  header.scrolled nav.main-nav a.active{
    background:rgba(20,20,20,0.06);
    border-color:rgba(20,20,20,0.16);
    color:var(--charcoal);
  }
  .header-actions{display:flex;align-items:center;gap:14px;flex-shrink:0;}
  .header-phone-bubble{
    display:flex;align-items:center;gap:7px;white-space:nowrap;
    background:var(--terracotta);color:var(--cream);
    font-size:13px;font-weight:600;
    padding:9px 18px;border-radius:100px;border:1.5px solid transparent;
    transition:background .25s ease, transform .25s ease, box-shadow .25s ease;
  }
  .header-phone-bubble:hover{background:var(--terracotta-dark);transform:translateY(-2px);box-shadow:0 10px 20px -10px rgba(163,79,44,0.55);}
  .burger{display:none;width:26px;height:20px;position:relative;cursor:pointer;background:none;border:none;}
  .burger span{position:absolute;left:0;right:0;height:2px;background:var(--cream);transition:all .3s;}
  header.scrolled .burger span{background:var(--charcoal);}
  .burger span:nth-child(1){top:0;} .burger span:nth-child(2){top:9px;} .burger span:nth-child(3){top:18px;}

  /* HERO (homepage full) */
  .hero{
    min-height:calc(100vh - var(--header-h));position:relative;display:flex;align-items:center;
    background:linear-gradient(180deg, rgba(43,38,33,0.55), rgba(43,38,33,0.72)),
      url('https://picsum.photos/id/1074/1800/1100') center/cover no-repeat;
  }
  .hero::after{
    content:"";position:absolute;inset:0;
    background:linear-gradient(180deg, rgba(140,98,57,0.25), rgba(43,38,33,0.55));
    mix-blend-mode:multiply;pointer-events:none;
  }
  .hero-content{position:relative;z-index:2;color:var(--cream);max-width:680px;padding-top:0;}
  .hero-content .eyebrow{color:#E7B08C;}
  .hero-content h1{font-size:clamp(38px,5.4vw,66px);margin-bottom:22px;color:var(--cream);}
  .hero-content p{font-size:18px;color:rgba(251,246,239,0.88);max-width:520px;margin-bottom:38px;}
  .hero-actions{display:flex;gap:16px;flex-wrap:wrap;}
  .hero-scroll{
    position:absolute;bottom:36px;left:50%;transform:translateX(-50%);z-index:2;
    color:var(--cream);font-size:11px;letter-spacing:0.15em;text-transform:uppercase;
    display:flex;flex-direction:column;align-items:center;gap:10px;opacity:.85;
  }
  .hero-scroll .line{width:1px;height:34px;background:rgba(251,246,239,0.6);animation:scrollLine 1.8s infinite;}
  @keyframes scrollLine{0%{transform:scaleY(0);transform-origin:top;}50%{transform:scaleY(1);transform-origin:top;}51%{transform-origin:bottom;}100%{transform:scaleY(0);transform-origin:bottom;}}

  /* PAGE HERO (inner pages) */
  .page-hero{
    position:relative;padding:56px 0 56px;color:var(--cream);
    /* 31/07/2026 : cadrage descendu (demande du client). Le bandeau garde sa
       hauteur, on remonte la fenetre de cadrage dans l'image (15% au lieu de
       50%) : la photo parait descendue et c'est son bas qui est rogne. */
    background:linear-gradient(180deg, rgba(16,16,16,0.48), rgba(16,16,16,0.70)),
      var(--hero-img) center var(--hero-pos, 15%)/cover no-repeat;
  }
  .page-hero .eyebrow{color:#F2867B;}
  .page-hero h1{color:var(--cream);font-weight:300;letter-spacing:-0.5px;font-size:clamp(32px,4.6vw,52px);max-width:760px;}
  .page-hero p{color:rgba(251,246,239,0.85);max-width:600px;margin-top:16px;font-size:16.5px;}
  .page-hero.page-hero--compact{padding:66px 0 50px;}
  .breadcrumb{font-size:12.5px;color:rgba(251,246,239,0.65);margin-bottom:18px;}
  .breadcrumb a{color:rgba(251,246,239,0.85);}
  .breadcrumb a:hover{color:var(--cream);text-decoration:underline;}

  /* PAGE HERO — SCROLLING PHOTO MARQUEE (defile de mode) */
  .hero-marquee{
    position:relative;min-height:267px;overflow:hidden;
    padding:100px 0 37px; /* hauteur de bandeau conservee : le contenu est cale en bas, ce padding pilote la hauteur de la frise */
    display:flex;align-items:flex-end;background:var(--wood-dark);
  }
  .hero-marquee-track{
    position:absolute;inset:0;display:flex;align-items:stretch;gap:5px;
    width:max-content;animation:marqueeScroll 160s linear infinite;
    will-change:transform;
  }
  .hero-marquee-track img{
    height:100%;width:auto;aspect-ratio:3/4;object-fit:cover;flex:none;
    filter:sepia(22%) saturate(74%) contrast(103%) brightness(109%) grayscale(6%);
  }
  .hero-marquee-overlay{
    position:absolute;inset:0;pointer-events:none;
    background:linear-gradient(180deg, rgba(74,56,33,0.12) 0%, rgba(74,56,33,0.22) 45%, rgba(43,38,33,0.62) 100%);
  }
  .hero-marquee .container{position:relative;z-index:2;}
  .hero-marquee .breadcrumb,
  .hero-marquee .eyebrow{color:rgba(251,246,239,0.9);}
  @keyframes marqueeScroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}
  @media (prefers-reduced-motion: reduce){.hero-marquee-track{animation:none;}}

  /* ARCH IMAGE FRAME */
  .arch-frame{
    border-radius:var(--radius-arch);
    overflow:hidden;box-shadow:var(--shadow);
    aspect-ratio:3/4;position:relative;
  }
  .arch-frame img{width:100%;height:100%;object-fit:cover;filter:sepia(18%) saturate(115%) contrast(102%);}

  /* SPLIT / STORY BLOCKS (reusable across pages) */
  .split{background:var(--cream);}
  .split.alt{background:var(--cream-2);}
  .split-grid{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center;}
  .split-grid .split-text{order:1;}
  .split-grid .arch-frame{order:2;}
  .split-grid.reverse .split-text{order:2;}
  .split-grid.reverse .arch-frame{order:1;}
  .split-text .eyebrow{color:var(--terracotta);}
  .split-text h2{font-size:clamp(26px,3.2vw,36px);margin-bottom:20px;}
  .split-text p{color:var(--charcoal-soft);margin-bottom:16px;font-size:16px;}
  .split-text .check-list{margin-top:20px;display:flex;flex-direction:column;gap:14px;}
  .split-text .check-list li{display:flex;gap:12px;align-items:flex-start;font-size:14.5px;color:var(--charcoal-soft);}
  .split-text .check-list .check{
    width:20px;height:20px;border-radius:50%;background:var(--sage);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;margin-top:2px;
  }
  .story-block + .story-block{border-top:1px solid var(--line);}
  .story-block{padding:86px 0;}
  .page-hero--tall{min-height:400px;display:flex;flex-direction:column;justify-content:center;}
  .page-hero--plain{background:var(--cream);border-bottom:1px solid var(--line);color:var(--charcoal);padding:70px 0 44px;}
  .page-hero--plain .eyebrow{color:var(--accent-red);}
  .page-hero--plain h1{color:var(--charcoal);font-weight:300;letter-spacing:-.5px;}
  .page-hero--plain p{color:var(--charcoal-soft);}
  .page-hero--plain .breadcrumb{color:#9a9a94;}
  .page-hero--plain .breadcrumb a{color:var(--charcoal-soft);}

  /* Listes a puce : la puce devient un repere, le texte (gras + description) coule ensemble */
  .check-list li, .check-list-grid li{
    display:block !important; position:relative; padding-left:30px; line-height:1.6;
  }
  .check-list .check, .check-list-grid .check{
    position:absolute !important; left:0; top:3px; margin-top:0 !important;
  }

  .founders{
    margin-top:28px;display:flex;gap:14px;align-items:center;
    padding:18px 22px;background:var(--cream-2);border-radius:4px;border:1px solid var(--line);
  }
  .founders .initials{display:flex;}
  .founders .initials span{
    width:40px;height:40px;border-radius:50%;background:var(--wood);color:var(--cream);
    display:flex;align-items:center;justify-content:center;font-family:'Fraunces',serif;font-size:15px;
    border:2px solid var(--cream-2);margin-left:-10px;
  }
  .founders .initials span:first-child{margin-left:0;}
  .founders .meta{font-size:13.5px;color:var(--charcoal-soft);}
  .founders .meta strong{color:var(--charcoal);display:block;font-size:14.5px;font-family:'Fraunces',serif;font-weight:500;}

  .pull-quote{
    font-family:'Fraunces',serif;font-style:italic;font-weight:500;
    font-size:clamp(20px,2.4vw,27px);line-height:1.4;color:var(--wood-dark);
    border-left:3px solid var(--terracotta);padding:6px 0 6px 26px;margin:34px 0;
  }

  /* SERVICES GRID (teasers) */
  .services{background:var(--cream-2);}
  .services-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}
  .services-grid.grid-3{grid-template-columns:repeat(3,1fr);}
  .service-card{
    background:var(--cream);padding:36px 26px;border-radius:4px;border:1px solid var(--line);
    transition:all .3s ease;
  }
  .service-card:hover{transform:translateY(-6px);box-shadow:var(--shadow);border-color:transparent;}
  .service-icon{
    width:56px;height:56px;border-radius:4px;background:var(--terracotta);
    display:flex;align-items:center;justify-content:center;margin-bottom:22px;color:var(--cream);
  }
  .service-card h3{font-size:19px;margin-bottom:10px;}
  .service-card p{font-size:14.5px;color:var(--charcoal-soft);}
  .service-card .more{display:inline-block;margin-top:14px;font-size:13.5px;font-weight:600;color:var(--terracotta);}

  /* HOMEPAGE — aperçu des 4 univers (cartes photo) */
  .services-refined{background:var(--cream-2);padding:96px 0;}
  .section-head-split{
    display:grid;grid-template-columns:1.1fr 0.9fr;gap:40px;align-items:end;
    margin-bottom:56px;padding-bottom:28px;border-bottom:1px solid var(--line);
  }
  .section-head-split h2{font-size:clamp(28px,3.2vw,36px);margin-top:10px;font-weight:400;letter-spacing:-0.4px;}
  .section-head-split > p{color:var(--charcoal-soft);font-size:15.5px;max-width:420px;margin:0;}
  .refined-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:22px;}
  /* Accueil — hero editorial (Mix 1) + bandeau marques defilant */
  .edito-hero{padding:0;border-top:1px solid var(--line);}
  .edito-grid{display:grid;grid-template-columns:1.05fr .95fr;min-height:clamp(430px,50vw,565px);}
  .edito-tx{padding:56px clamp(28px,6vw,92px);display:flex;flex-direction:column;justify-content:center;}
  .edito-tx h1{font-weight:300;font-size:clamp(38px,5vw,62px);line-height:1.02;letter-spacing:-.5px;}
  .edito-tx h1 em{font-style:italic;font-weight:600;}
  .edito-tx p{color:var(--charcoal-soft);font-size:17px;max-width:410px;margin:22px 0 32px;}
  .edito-img{background:var(--cream-2) center 58%/cover no-repeat;border-left:1px solid var(--line);}
  .brand-ticker{border-top:2px solid var(--charcoal);border-bottom:2px solid var(--charcoal);overflow:hidden;white-space:nowrap;background:var(--cream);}
  .brand-ticker-run{display:inline-block;padding:15px 0;font-family:'Space Grotesk','Inter',sans-serif;font-weight:600;font-size:15px;letter-spacing:.06em;animation:tickerMove 42s linear infinite;}
  .brand-ticker-run span{margin:0 26px;color:var(--charcoal);}
  .brand-ticker-run span.c{color:var(--accent-red);}
  @keyframes tickerMove{to{transform:translateX(-50%);}}
  @media (max-width:820px){
    .edito-grid{grid-template-columns:1fr;}
    .edito-img{min-height:280px;order:2;}
    .edito-tx{order:1;padding:44px 28px;}
  }
  .refined-card{
    display:block;background:var(--cream);border-radius:4px;overflow:hidden;
    border:1px solid var(--line);text-decoration:none;color:inherit;
    transition:transform .35s ease, box-shadow .35s ease, border-color .35s ease;
  }
  .refined-card:hover{transform:translateY(-6px);box-shadow:var(--shadow);border-color:transparent;}
  .refined-photo{
    position:relative;height:148px;background:var(--img) center/cover no-repeat;
    transition:transform .6s ease;
  }
  .refined-photo::after{
    content:"";position:absolute;inset:0;
    background:linear-gradient(180deg, rgba(43,38,33,0) 55%, rgba(43,38,33,0.4) 100%);
  }
  .refined-card:hover .refined-photo{transform:scale(1.07);}
  .refined-photo.contain{height:172px;background:var(--img) center/contain no-repeat;background-color:#EAF3FA;}
  .refined-photo.contain::after{display:none;}
  .refined-card:hover .refined-photo.contain{transform:none;}
  .refined-icon{
    position:absolute;left:18px;bottom:-22px;z-index:2;width:44px;height:44px;border-radius:13px;
    background:var(--terracotta);color:var(--cream);display:flex;align-items:center;justify-content:center;
    box-shadow:0 10px 22px -8px rgba(43,38,33,0.45);transition:background .3s ease;
  }
  .refined-card:hover .refined-icon{background:var(--terracotta-dark);}
  .refined-body{padding:36px 22px 26px;}
  .refined-body h3{font-size:19px;margin-bottom:9px;}
  .refined-body p{font-size:14px;color:var(--charcoal-soft);margin-bottom:15px;}
  .refined-body .more{display:inline-block;font-size:13.5px;font-weight:600;color:var(--terracotta);transition:transform .25s ease;}
  .refined-card:hover .more{transform:translateX(3px);}
  @media (max-width:900px){.refined-grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:760px){
    .section-head-split{grid-template-columns:1fr;gap:14px;}
    .refined-grid{grid-template-columns:1fr;}
  }

  /* AMBIANCE GALLERY */
  .ambiance{background:var(--cream);}
  .ambiance-grid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:22px;align-items:end;}
  .ambiance-grid .arch-frame:first-child{aspect-ratio:4/5;}
  .ambiance-grid .arch-frame{aspect-ratio:3/4;}
  .ambiance-caption{
    margin-top:34px;text-align:center;color:var(--charcoal-soft);font-family:'Fraunces',serif;
    font-style:italic;font-size:18px;
  }

  /* MARQUES */
  .marques{background:var(--cream-2);}
  .marques-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:18px;}
  .marque-item{
    background:var(--cream);border:1px solid var(--line);border-radius:4px;
    padding:26px 18px;display:flex;align-items:center;justify-content:center;
    font-family:'Fraunces',serif;font-size:17px;color:var(--wood-dark);text-align:center;
    min-height:88px;transition:all .25s;
  }
  .marque-item:hover{border-color:var(--terracotta);color:var(--terracotta);}

  /* BRAND STATS STRIP (page Nos Marques) */
  .brand-stats{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;margin:26px 0 6px;}
  .brand-stat{
    display:flex;align-items:baseline;gap:8px;background:var(--cream);border:1px solid var(--line);
    border-radius:100px;padding:10px 22px;
  }
  .brand-stat strong{font-family:'Fraunces',serif;font-size:20px;color:var(--terracotta);}
  .brand-stat span{font-size:12.5px;text-transform:uppercase;letter-spacing:0.06em;color:var(--charcoal-soft);font-weight:600;}

  /* BRAND CARDS (page Nos Marques) */
  .brand-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .brand-card{
    background:var(--cream);border:1px solid var(--line);border-radius:4px;
    padding:0 0 30px;overflow:hidden;transition:transform .3s ease, box-shadow .3s ease, border-color .3s ease;
    position:relative;
  }
  .brand-card::before{
    content:"";display:block;height:7px;
    background:linear-gradient(90deg, var(--accent,var(--terracotta)), var(--accent,var(--terracotta)) 40%, transparent 40%, transparent 100%);
    background-size:200% 100%;background-position:0 0;
    transition:background-position .35s ease;
  }
  .brand-card:hover::before{background-position:-100% 0;}
  .brand-card:hover{transform:translateY(-7px);box-shadow:var(--shadow);border-color:transparent;}
  .brand-card-body{padding:26px 26px 0;}
  .brand-logo-plate{
    background:var(--accent-bg,var(--cream-2));border-radius:4px;padding:20px 22px;
    display:flex;align-items:center;min-height:64px;margin-bottom:18px;transition:transform .3s ease;
  }
  .brand-card:hover .brand-logo-plate{transform:scale(1.04);}
  .brand-wordmark{font-size:23px;color:var(--charcoal);line-height:1.15;}
  .brand-logo{display:block;max-width:150px;max-height:42px;width:auto;height:auto;object-fit:contain;object-position:left center;}
  .brand-meta{
    display:inline-flex;align-items:center;gap:6px;font-size:11.5px;text-transform:uppercase;letter-spacing:0.07em;
    color:var(--accent,var(--terracotta));font-weight:700;margin-bottom:14px;
    background:var(--accent-bg,rgba(193,101,59,0.12));padding:6px 13px;border-radius:100px;
  }
  .brand-card p{font-size:14px;color:var(--charcoal-soft);padding:0 26px;line-height:1.55;}

  /* Wordmark type treatments — fonts chosen to evoke each maison's real
     visual identity as closely as free web fonts allow. These are NOT the
     brands' actual proprietary logo artwork (those are bespoke, unlicensed
     custom typefaces) — just a stylistic nod using freely licensed fonts. */
  .wm-stencil{font-family:'Poppins',sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:-0.01em;}                 /* Ray-Ban — bold, sporty */
  .wm-serif-caps{font-family:'Archivo Black',sans-serif;text-transform:uppercase;letter-spacing:0.01em;}                        /* Fendi — chunky, bold */
  .wm-script{font-family:'Playfair Display',serif;font-style:italic;font-weight:500;}                                           /* Fred — elegant jewelry italic */
  .wm-thin-caps-a{font-family:'Inter',sans-serif;font-weight:300;text-transform:uppercase;letter-spacing:0.18em;}               /* Loewe — minimal thin wide */
  .wm-thin-caps-b{font-family:'Inter',sans-serif;font-weight:400;text-transform:uppercase;letter-spacing:0.14em;}               /* Celine — thin caps */
  .wm-lower-bold{font-family:'Poppins',sans-serif;font-weight:700;text-transform:lowercase;letter-spacing:-0.01em;}             /* Marc Jacobs — bold lowercase */
  .wm-geo-caps{font-family:'Poppins',sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:0.02em;}                /* Prada — bold geometric caps */
  .wm-plain{font-family:'Inter',sans-serif;font-weight:500;}                                                                    /* Andy Brook — simple, clean */
  .wm-lower-round{font-family:'Comfortaa',sans-serif;font-weight:600;text-transform:lowercase;letter-spacing:0.01em;}           /* CHIMI — rounded Scandinavian */
  .wm-italic{font-family:'Fraunces',serif;font-style:italic;font-weight:500;}                                                   /* Miu Miu — playful serif italic */
  .wm-lower-wide{font-family:'Space Grotesk',sans-serif;font-weight:700;text-transform:lowercase;letter-spacing:0.02em;}        /* LOOL — geometric, architectural */
  .wm-classic-serif{font-family:'Playfair Display',serif;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;}       /* Ralph Lauren — heritage serif */
  .wm-thin-wide{font-family:'Inter',sans-serif;font-weight:200;text-transform:uppercase;letter-spacing:0.24em;}                 /* Armani — ultra-thin, luxe */
  .wm-elegant-caps{font-family:'Marcellus',serif;text-transform:uppercase;letter-spacing:0.08em;}                               /* Longchamp — refined inscription serif */
  .wm-bold-condensed{font-family:'Anton',sans-serif;text-transform:uppercase;letter-spacing:0.01em;}                            /* Guess — bold blocky impact */
  .wm-wide-caps{font-family:'Inter',sans-serif;font-weight:500;text-transform:uppercase;letter-spacing:0.2em;}                  /* Givenchy — fallback en attente du vrai logo */

  /* BRAND PILLS (homepage teaser) */
  .brand-pills{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;}
  .brand-pill{
    padding:10px 22px;background:var(--cream);border:1px solid var(--line);border-radius:100px;
    font-size:13.5px;font-weight:600;color:var(--charcoal-soft);
  }

  /* AUDITION — signes / auto-évaluation */
  .check-list-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px 32px;margin-top:8px;}
  .check-list-grid li{display:flex;gap:12px;align-items:flex-start;font-size:15px;color:var(--charcoal-soft);}
  .check-list-grid .check{
    width:22px;height:22px;border-radius:50%;background:var(--terracotta);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:12px;margin-top:1px;
  }

  /* AUDITION — degrés de perte auditive */
  .degree-scale{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
  .degree-card{
    background:var(--cream);border:1px solid var(--line);border-radius:4px;
    padding:26px 22px;position:relative;overflow:hidden;
  }
  .degree-card::before{content:"";position:absolute;top:0;left:0;right:0;height:6px;background:var(--bar,var(--terracotta));}
  .degree-card .db{font-family:'Fraunces',serif;font-size:15px;color:var(--terracotta-dark);font-weight:500;margin-bottom:6px;}
  .degree-card h3{font-size:17px;margin-bottom:8px;}
  .degree-card p{font-size:13.5px;color:var(--charcoal-soft);}

  /* AUDITION — types d'appareils */
  .device-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .device-card{
    background:var(--cream-2);border:1px solid var(--line);border-radius:4px;padding:32px 28px;
  }
  .device-card .discretion{display:flex;gap:5px;margin-bottom:16px;}
  .device-card .discretion span{width:22px;height:6px;border-radius:3px;background:var(--line);}
  .device-card .discretion span.on{background:var(--terracotta);}
  .device-card h3{font-size:19px;margin-bottom:10px;}
  .device-card p{font-size:14.5px;color:var(--charcoal-soft);margin-bottom:12px;}
  .device-card .suited{font-size:12px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:var(--wood-dark);}

  /* AUDITION — 100% Santé / reste à charge */
  .reimburse-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
  .reimburse-card{background:var(--cream);border:1px solid var(--line);border-radius:4px;padding:32px 30px;}
  .reimburse-card.highlight{border-color:var(--terracotta);box-shadow:var(--shadow);}
  .reimburse-card .tag{
    display:inline-block;font-size:11.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;
    color:var(--terracotta);background:rgba(193,101,59,0.1);padding:5px 12px;border-radius:100px;margin-bottom:14px;
  }
  .reimburse-card h3{font-size:20px;margin-bottom:10px;}
  .reimburse-card p{font-size:14.5px;color:var(--charcoal-soft);}

  /* AUDITION — FAQ accordion */
  .faq-list{display:flex;flex-direction:column;gap:12px;max-width:780px;margin:0 auto;}
  .faq-item{background:var(--cream);border:1px solid var(--line);border-radius:4px;padding:6px 26px;}
  .faq-item summary{
    list-style:none;cursor:pointer;padding:20px 0;font-family:'Fraunces',serif;font-size:17px;
    display:flex;justify-content:space-between;align-items:center;gap:16px;color:var(--charcoal);
  }
  .faq-item summary::-webkit-details-marker{display:none;}
  .faq-item summary .plus{
    width:26px;height:26px;border-radius:50%;border:1.5px solid var(--terracotta);color:var(--terracotta);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;transition:transform .25s;
  }
  .faq-item[open] summary .plus{transform:rotate(45deg);}
  .faq-item p{font-size:14.5px;color:var(--charcoal-soft);padding-bottom:22px;}

  /* ACTUALITÉS — filtre par thématique */
  .article-filter-bar{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:48px;}
  .filter-pill{
    padding:9px 20px;border-radius:100px;border:1.5px solid var(--line);background:var(--cream);
    font-size:13px;font-weight:600;color:var(--charcoal-soft);cursor:pointer;transition:all .2s ease;
    font-family:'Inter',sans-serif;
  }
  .filter-pill:hover{border-color:var(--terracotta);color:var(--terracotta);}
  .filter-pill.active{background:var(--terracotta);border-color:var(--terracotta);color:var(--cream);}

  /* ACTUALITÉS — grille d'articles ("bulles" cliquables : voir .article-modal-* plus bas) */
  .article-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;}
  .article-card{
    background:var(--cream);border:1px solid var(--line);border-radius:28px;overflow:hidden;cursor:pointer;
    transition:transform .3s ease, box-shadow .3s ease, border-color .3s ease; display:flex; flex-direction:column;
  }
  .article-card:hover{transform:translateY(-6px) scale(1.015);box-shadow:var(--shadow);border-color:transparent;}
  .article-card .article-img{aspect-ratio:4/3;overflow:hidden;}
  .article-card .article-img img{width:100%;height:100%;object-fit:cover;filter:sepia(14%) saturate(108%) contrast(101%);transition:transform .4s ease;}
  .article-card:hover .article-img img{transform:scale(1.06);}
  .article-card-body{padding:24px 24px 28px;display:flex;flex-direction:column;flex:1;}
  .article-tag{
    display:inline-flex;align-self:flex-start;align-items:center;font-size:11.5px;text-transform:uppercase;
    letter-spacing:0.07em;color:var(--accent,var(--terracotta));font-weight:700;
    background:var(--accent-bg,rgba(193,101,59,0.12));padding:6px 13px;border-radius:100px;margin-bottom:14px;
  }
  .article-card h3{font-size:19px;margin-bottom:10px;line-height:1.3;}
  .article-card p{font-size:14px;color:var(--charcoal-soft);margin-bottom:16px;flex:1;}
  .article-card .article-meta{font-size:12.5px;color:var(--charcoal-soft);display:flex;justify-content:space-between;align-items:center;margin-top:auto;}
  .article-card .article-meta .more{font-weight:600;color:var(--terracotta);display:inline-flex;align-items:center;gap:5px;}

  /* ARTICLE — page individuelle */
  .article-meta-row{display:flex;gap:14px;align-items:center;margin-top:18px;flex-wrap:wrap;}
  .article-meta-row .article-tag{margin-bottom:0;}
  .article-meta-row .article-date{font-size:13px;color:rgba(251,246,239,0.75);}
  .article-prose{background:var(--cream);}
  .article-prose h2{font-size:clamp(22px,2.6vw,28px);margin:44px 0 16px;}
  .article-prose h2:first-child{margin-top:0;}
  .article-prose p{font-size:16px;color:var(--charcoal-soft);margin-bottom:18px;line-height:1.75;}
  .article-prose .check-list{display:flex;flex-direction:column;gap:12px;margin:22px 0;}
  .article-prose .check-list li{display:flex;gap:12px;align-items:flex-start;font-size:15px;color:var(--charcoal-soft);}
  .article-prose .check-list .check{
    width:20px;height:20px;border-radius:50%;background:var(--sage);color:var(--cream);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:11px;margin-top:2px;
  }
  .article-prose .pull-quote{margin:30px 0;}

  /* ====================================================================
     GABARIT SEO EDITORIAL (31/07/2026, soir)
     1. .answer-lead  : reponse directe de 40-60 mots placee juste sous le
        titre. C'est ce bloc que Google et les moteurs de reponse IA
        extraient en priorite. Doit rester court : au-dela de ~60 mots il
        cesse d'etre extractible tel quel.
     2. .article-prose h3 / table / ol : sous-niveaux, tableaux
        comparatifs et listes numerotees, formats les plus repris par les
        AI Overviews et les extraits enrichis.
     3. .article-faq  : FAQ VISIBLE en HTML. Le rich result FAQ a ete
        supprime par Google en mai-juin 2026, mais le format reste lu par
        les moteurs de reponse et utile au lecteur — on le garde donc en
        HTML lisible, sans compter sur un affichage enrichi.
     ==================================================================== */
  .answer-lead{
    margin:0 0 34px;padding:22px 26px;background:var(--cream-2);
    border:1px solid var(--line);border-left:3px solid var(--sage);border-radius:4px;
  }
  .answer-lead p{font-size:17px;line-height:1.65;color:var(--charcoal);margin-bottom:0;font-weight:500;}
  .answer-lead .eyebrow{margin-bottom:8px;display:block;}

  .article-prose h3{font-size:clamp(17px,1.9vw,20px);margin:30px 0 12px;color:var(--charcoal);}
  .article-prose ol{margin:20px 0 24px;padding-left:22px;list-style:decimal;}
  .article-prose ol li{font-size:15.5px;color:var(--charcoal-soft);line-height:1.7;margin-bottom:10px;padding-left:4px;}
  .article-prose ul.plain-list{margin:20px 0 24px;padding-left:20px;list-style:disc;}
  .article-prose ul.plain-list li{font-size:15.5px;color:var(--charcoal-soft);line-height:1.7;margin-bottom:9px;}

  .table-wrap{overflow-x:auto;margin:26px 0 30px;-webkit-overflow-scrolling:touch;}
  .article-prose table{
    width:100%;border-collapse:collapse;font-size:14.5px;background:var(--cream-2);
    border:1px solid var(--line);border-radius:4px;overflow:hidden;
  }
  .article-prose thead th{
    background:var(--sage);color:var(--cream);text-align:left;font-weight:600;
    padding:12px 16px;font-size:13.5px;letter-spacing:.02em;
  }
  .article-prose tbody td{
    padding:12px 16px;border-top:1px solid var(--line);color:var(--charcoal-soft);
    line-height:1.6;vertical-align:top;
  }
  .article-prose tbody tr td:first-child{font-weight:600;color:var(--charcoal);}

  .article-faq{margin:46px 0 4px;}
  .article-faq h2{margin-bottom:8px;}
  .article-faq .faq-intro{font-size:15px;color:var(--charcoal-soft);margin-bottom:22px;}
  .article-faq .faq-item{
    padding:20px 24px;background:var(--cream-2);border:1px solid var(--line);
    border-radius:4px;margin-bottom:12px;
  }
  .article-faq .faq-item h3{margin:0 0 8px;font-size:16.5px;line-height:1.4;}
  .article-faq .faq-item p{font-size:15px;margin-bottom:0;}

  .article-source-note{
    margin-top:40px;padding:18px 22px;background:var(--cream-2);border-radius:4px;
    font-size:12.5px;color:var(--charcoal-soft);border:1px solid var(--line);
  }

  /* Bandeau de fraicheur : pose par le navigateur, a chaque visite, sur les
     articles de plus de six mois. Le calcul est volontairement fait cote
     client et non a la generation : il reste donc exact des mois plus tard,
     sans avoir a regenerer le site. */
  .article-freshness-notice{
    margin:0 0 32px;padding:14px 18px;background:var(--cream-2);
    border-left:3px solid var(--terracotta);border-radius:4px;
    font-size:13.5px;line-height:1.6;color:var(--charcoal-soft);
  }
  .related-articles{background:var(--cream-2);}

  /* ====================================================================
     MAILLAGE INTERNE (31/07/2026)
     Les liens du corps de page etaient invisibles : la regle globale
     a{text-decoration:none;color:inherit} les rendait indistinguables du
     texte. On style donc explicitement les liens contextuels, dans les
     articles comme dans les pages (classe .ilink).
     ==================================================================== */
  .article-prose p a, .article-prose li a, .ilink{
    color:var(--terracotta-dark);
    border-bottom:1px solid rgba(193,101,59,0.38);
    transition:color .2s ease, border-color .2s ease;
  }
  .article-prose p a:hover, .article-prose li a:hover, .ilink:hover{
    color:var(--terracotta);border-bottom-color:var(--terracotta);
  }

  /* Encadre "Pour aller plus loin", en fin de corps d'article */
  .go-further{
    margin:46px 0 4px;padding:26px 28px;background:var(--cream-2);
    border:1px solid var(--line);border-left:3px solid var(--terracotta);
    border-radius:4px;
  }
  .go-further .eyebrow{margin-bottom:8px;}
  .go-further h3{font-size:19px;margin-bottom:18px;}
  .go-further ul{display:flex;flex-direction:column;gap:14px;}
  .go-further li{display:flex;gap:12px;align-items:flex-start;}
  .go-further .arrow{color:var(--terracotta);flex-shrink:0;font-size:13px;line-height:1.7;}
  .article-prose .go-further a, .go-further a{
    font-weight:600;color:var(--charcoal);font-size:15px;line-height:1.45;border-bottom:none;
  }
  .article-prose .go-further a:hover, .go-further a:hover{color:var(--terracotta);border-bottom:none;}
  .go-further .go-desc{display:block;font-weight:400;font-size:13.5px;color:var(--charcoal-soft);margin-top:3px;}

  /* Lien discret en fin de bloc de page (accueil, pages de service) */
  .block-more{
    display:inline-block;margin-top:22px;font-size:14px;font-weight:600;
    color:var(--terracotta);border-bottom:1px solid rgba(193,101,59,0.4);
    transition:color .2s ease,border-color .2s ease;
  }
  .block-more:hover{color:var(--terracotta-dark);border-bottom-color:var(--terracotta-dark);}
  .block-more-center{text-align:center;margin-top:36px;}

  /* ACTUALITÉS — bulle agrandie (modale) : le contenu complet de l'article est
     chargé depuis sa page dédiée (fetch) et affiché sans quitter la page en
     cours, tout en gardant cette page dédiée pleinement fonctionnelle pour le
     SEO, le partage de lien et la navigation sans JavaScript. */
  .article-modal-overlay{
    position:fixed;inset:0;background:rgba(43,38,33,0.55);backdrop-filter:blur(3px);
    display:flex;align-items:center;justify-content:center;padding:24px;
    z-index:999;opacity:0;visibility:hidden;transition:opacity .3s ease, visibility .3s ease;
  }
  .article-modal-overlay.open{opacity:1;visibility:visible;}
  .article-modal{
    background:var(--cream);border-radius:32px;max-width:800px;width:100%;max-height:88vh;
    overflow-y:auto;position:relative;box-shadow:0 40px 100px -20px rgba(43,38,33,0.5);
    transform:scale(0.92) translateY(20px);opacity:0;
    transition:transform .35s cubic-bezier(.2,.8,.2,1), opacity .3s ease;
  }
  .article-modal-overlay.open .article-modal{transform:scale(1) translateY(0);opacity:1;}
  .article-modal-close{
    position:absolute;top:18px;right:18px;width:40px;height:40px;border-radius:50%;
    background:var(--cream);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;
    cursor:pointer;z-index:2;font-size:16px;line-height:1;color:var(--charcoal);
    transition:background .2s ease, color .2s ease, transform .2s ease;
  }
  .article-modal-close:hover{background:var(--terracotta);color:var(--cream);border-color:var(--terracotta);transform:rotate(90deg);}
  .article-modal-hero{aspect-ratio:16/9;overflow:hidden;border-radius:32px 32px 0 0;}
  .article-modal-hero img{width:100%;height:100%;object-fit:cover;filter:sepia(14%) saturate(108%) contrast(101%);}
  .article-modal-content{padding:36px 40px 44px;}
  .article-modal-content .article-tag{margin-bottom:14px;}
  .article-modal-title{font-size:clamp(24px,3vw,32px);margin-bottom:8px;font-family:'Fraunces',serif;font-weight:500;line-height:1.2;color:var(--charcoal);}
  .article-modal-date{font-size:13px;color:var(--charcoal-soft);margin-bottom:28px;}
  .article-modal-loading{padding:80px 40px;text-align:center;color:var(--charcoal-soft);font-size:15px;}
  .article-modal-loading a{color:var(--terracotta);font-weight:600;}
  .article-modal-permalink{display:inline-block;margin-top:12px;font-size:13.5px;font-weight:600;color:var(--terracotta);}
  body.modal-open{overflow:hidden;}

  /* DARK CARD GRID (avantages / garanties / engagements) */
  .dark-section{background:var(--charcoal);color:var(--cream);}
  .dark-section .section-head h2, .dark-section .section-head p{color:var(--cream);}
  .dark-section .section-head p{color:rgba(251,246,239,0.72);}
  .card-grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .dark-card{
    background:rgba(251,246,239,0.06);border:1px solid rgba(251,246,239,0.14);
    border-radius:4px;padding:32px 26px;
  }
  .dark-card .badge{
    display:inline-flex;align-items:center;justify-content:center;
    width:46px;height:46px;border-radius:50%;background:var(--terracotta);margin-bottom:18px;
  }
  .dark-card h3{color:var(--cream);font-size:18px;margin-bottom:8px;}
  .dark-card p{color:rgba(251,246,239,0.68);font-size:14.5px;}

  /* CONTACT */
  .contact{background:var(--cream-2);}
  .contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;}
  .contact-info-card{
    background:var(--cream);border-radius:4px;padding:44px;border:1px solid var(--line);box-shadow:var(--shadow);
  }
  .contact-info-card h3{font-size:22px;margin-bottom:26px;}
  .info-row{display:flex;gap:16px;margin-bottom:22px;align-items:flex-start;}
  .info-row .ico{
    width:40px;height:40px;border-radius:12px;background:var(--cream-2);color:var(--terracotta);
    display:flex;align-items:center;justify-content:center;flex-shrink:0;
  }
  .info-row strong{display:block;font-size:14.5px;margin-bottom:2px;}
  .info-row span, .info-row a{font-size:14.5px;color:var(--charcoal-soft);}
  .info-row a:hover{color:var(--terracotta);}
  .social-row{display:flex;gap:12px;margin-top:28px;}
  .social-row a{
    width:42px;height:42px;border-radius:50%;background:var(--cream-2);display:flex;
    align-items:center;justify-content:center;color:var(--charcoal);transition:all .25s;
  }
  .social-row a:hover{background:var(--terracotta);color:var(--cream);}
  .map-frame{border-radius:4px;overflow:hidden;box-shadow:var(--shadow);min-height:100%;}
  .map-frame iframe{width:100%;height:100%;min-height:420px;border:0;}

  /* CTA BAND */
  .cta-band{background:var(--terracotta);color:var(--cream);text-align:center;}
  .cta-band h2{color:var(--cream);font-size:clamp(24px,3vw,34px);margin-bottom:16px;}
  .cta-band p{color:rgba(251,246,239,0.9);margin-bottom:30px;max-width:560px;margin-left:auto;margin-right:auto;}
  .cta-band .btn-primary{background:var(--cream);color:var(--terracotta-dark);}
  .cta-band .btn-primary:hover{background:var(--cream-2);}

  /* FOOTER */
  footer{background:var(--charcoal);color:rgba(251,246,239,0.65);padding:56px 0 28px;}
  .footer-top{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:30px;padding-bottom:36px;border-bottom:1px solid rgba(251,246,239,0.12);}
  .footer-logo{display:flex;align-items:center;gap:12px;}
  .footer-logo .name{color:var(--cream);font-family:'Fraunces',serif;font-size:18px;}
  .footer-links{display:flex;gap:44px;flex-wrap:wrap;}
  .footer-links h4{color:var(--cream);font-size:13px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;font-family:'Inter',sans-serif;font-weight:600;}
  .footer-links ul li{margin-bottom:9px;font-size:14px;}
  .footer-links a:hover{color:var(--terracotta);}
  .footer-bottom{padding-top:26px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;font-size:12.5px;color:rgba(251,246,239,0.45);}
  .footer-bottom a{border-bottom:1px solid rgba(251,246,239,0.22);transition:color .2s ease,border-color .2s ease;}
  .footer-bottom a:hover{color:var(--terracotta);border-bottom-color:var(--terracotta);}

  .reveal{opacity:0;transform:translateY(28px);transition:opacity .8s ease, transform .8s ease;}
  .reveal.in{opacity:1;transform:translateY(0);}

  @media (max-width:980px){
    .split-grid, .contact-grid{grid-template-columns:1fr;gap:40px;}
    .split-grid .split-text, .split-grid .arch-frame, .split-grid.reverse .split-text, .split-grid.reverse .arch-frame{order:initial;}
    .services-grid{grid-template-columns:repeat(2,1fr);}
    .services-grid.grid-3{grid-template-columns:repeat(2,1fr);}
    .marques-grid{grid-template-columns:repeat(3,1fr);}
    .brand-grid{grid-template-columns:repeat(2,1fr);}
    .card-grid-3{grid-template-columns:1fr;}
    .ambiance-grid{grid-template-columns:1fr 1fr;}
    .ambiance-grid .arch-frame:first-child{grid-column:1/-1;}
    .degree-scale{grid-template-columns:1fr 1fr;}
    .device-grid{grid-template-columns:1fr;}
    .reimburse-grid{grid-template-columns:1fr;}
    .article-grid{grid-template-columns:1fr 1fr;}
  }
  @media (max-width:1130px){
    /* En dessous de cette largeur, la barre de navigation (7 onglets) ne
       tient plus confortablement sur une seule ligne à côté du logo et de la
       bulle téléphone — on bascule sur le menu burger plutôt que de laisser
       les onglets se couper ou passer à la ligne.
       Historique du seuil : 980px, puis 1010px le 30/07/2026 (les bulles
       d'onglet ajoutent du rembourrage horizontal), puis 1130px le
       31/07/2026 avec le retour de l'onglet « Nous rendre visite ».
       Mesure : la nav a besoin de 1057px utiles, soit 1113px de fenetre ;
       1130px laisse une marge de securite. */
    nav.main-nav{
      position:fixed;top:0;right:-100%;height:100vh;width:78%;max-width:340px;
      background:var(--cream);flex-direction:column;padding:110px 30px;gap:11px;margin:0;
      transition:right .4s ease;box-shadow:-10px 0 40px rgba(0,0,0,0.15);
    }
    nav.main-nav.open{right:0;}
    nav.main-nav a{color:var(--charcoal);font-size:16px;padding:9px 16px;align-self:flex-start;}
    /* Dans le panneau burger le fond est deja creme : la bulle prend la
       teinte terracotta quel que soit l'etat de defilement. */
    nav.main-nav a.active, header.scrolled nav.main-nav a.active{
      background:rgba(193,101,59,0.10);
      border-color:rgba(193,101,59,0.22);
      color:var(--terracotta);
    }
    .burger{display:block;}
  }
  @media (max-width:480px){
    .header-phone-bubble span.phone-full{display:none;}
  }
  @media (max-width:760px){
    section{padding:76px 0;}
    .story-block{padding:56px 0;}
    .page-hero{padding:44px 0 43px;}
    .page-hero.page-hero--compact{padding:46px 0 31px;}
    .hero-marquee{min-height:227px;padding:87px 0 27px;}
    .services-grid{grid-template-columns:1fr;}
    .services-grid.grid-3{grid-template-columns:1fr;}
    .marques-grid{grid-template-columns:repeat(2,1fr);}
    .brand-grid{grid-template-columns:1fr;}
    .ambiance-grid{grid-template-columns:1fr;}
    .footer-bottom{flex-direction:column;}
    .check-list-grid{grid-template-columns:1fr;}
    .degree-scale{grid-template-columns:1fr;}
    .faq-item summary{font-size:15.5px;}
    .article-grid{grid-template-columns:1fr;}
    .article-filter-bar{gap:8px;}
    .filter-pill{padding:8px 16px;font-size:12.5px;}
    .article-modal-overlay{padding:0;}
    .article-modal{max-height:100vh;height:100%;border-radius:0;max-width:none;}
    .article-modal-hero{border-radius:0;}
    .article-modal-content{padding:26px 22px 40px;}
  }
"""

# Short content hash used as a cache-busting query string on site.css
# (?v=xxxxxxxx) so browsers cache the stylesheet aggressively across page
# navigations, while still picking up changes automatically whenever
# SHARED_CSS is edited and the site is rebuilt.
CSS_VERSION = hashlib.md5(SHARED_CSS.encode("utf-8")).hexdigest()[:8]

SCRIPT_JS = """
  document.getElementById('year').textContent = new Date().getFullYear();

  /* Le header garde en permanence la classe "scrolled" (demande du client,
     31/07/2026) : fond creme translucide et bulle d'onglet actif terracotta
     des le haut de page. L'ancien listener de scroll qui basculait la classe
     au-dela de 40px a donc ete supprime. */

  const burger = document.getElementById('burger');
  const nav = document.getElementById('mainNav');
  burger.addEventListener('click', () => nav.classList.toggle('open'));
  nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

  const revealEls = document.querySelectorAll('.reveal');
  let ticking = false;
  function checkReveal(){
    revealEls.forEach(el => {
      if (el.classList.contains('in')) return;
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.94 && r.bottom > 0) {
        el.classList.add('in');
      }
    });
    ticking = false;
  }
  function onScroll(){
    if (!ticking) {
      requestAnimationFrame(checkReveal);
      ticking = true;
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  checkReveal();

  // ACTUALITÉS — bulles extensibles : un clic sur une carte article agrandit
  // une "bulle" sur place avec le texte complet, plutôt que de quitter la
  // page. Le contenu vient de la page dédiée de l'article (fetch), donc rien
  // n'est dupliqué et la page dédiée reste intacte pour le SEO/le partage.
  const articleOverlay = document.getElementById('articleModalOverlay');
  if (articleOverlay) {
    const modalClose = articleOverlay.querySelector('.article-modal-close');
    const modalBody = articleOverlay.querySelector('.article-modal-body');
    const baseTitle = document.title;
    let lastFocused = null;

    async function openArticleModal(url) {
      lastFocused = document.activeElement;
      modalBody.innerHTML = '<div class="article-modal-loading">Chargement de l’article…</div>';
      document.body.classList.add('modal-open');
      articleOverlay.classList.add('open');
      articleOverlay.setAttribute('aria-hidden', 'false');
      modalClose.focus();

      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('http ' + res.status);
        const html = await res.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const heroImg = doc.querySelector('.article-prose .arch-frame img');
        const tag = doc.querySelector('.article-meta-row .article-tag');
        const dateEl = doc.querySelector('.article-meta-row .article-date');
        const h1 = doc.querySelector('.page-hero h1');
        const prose = doc.querySelector('.article-prose .container-narrow');

        document.title = doc.title || baseTitle;

        let out = '';
        if (heroImg) {
          out += '<div class="article-modal-hero"><img src="' + heroImg.getAttribute('src') + '" alt="' + (heroImg.getAttribute('alt') || '') + '"></div>';
        }
        out += '<div class="article-modal-content">';
        if (tag) out += tag.outerHTML;
        if (h1) out += '<h2 class="article-modal-title">' + h1.textContent + '</h2>';
        if (dateEl) out += '<div class="article-modal-date">' + dateEl.textContent + '</div>';
        if (prose) {
          const clone = prose.cloneNode(true);
          const frame = clone.querySelector('.arch-frame');
          if (frame) frame.remove();
          out += '<div class="article-prose">' + clone.innerHTML + '</div>';
        }
        out += '<a href="' + url + '" class="article-modal-permalink">Voir cet article sur sa page dédiée →</a>';
        out += '</div>';
        modalBody.innerHTML = out;
      } catch (err) {
        modalBody.innerHTML = '<div class="article-modal-loading">Impossible de charger l’article pour le moment. <a href="' + url + '">Ouvrir la page complète</a>.</div>';
      }
    }

    function closeArticleModal() {
      articleOverlay.classList.remove('open');
      articleOverlay.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      document.title = baseTitle;
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }

    document.querySelectorAll('.article-card').forEach(card => {
      card.addEventListener('click', (e) => {
        // laisse le comportement natif (nouvel onglet, etc.) si l'utilisateur
        // utilise un clic modifié — seul le clic gauche simple ouvre la bulle
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button === 1) return;
        e.preventDefault();
        openArticleModal(card.getAttribute('href'));
      });
    });

    modalClose.addEventListener('click', closeArticleModal);
    articleOverlay.addEventListener('click', (e) => {
      if (e.target === articleOverlay) closeArticleModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && articleOverlay.classList.contains('open')) closeArticleModal();
    });
  }

  /* Bandeau de fraicheur. SEUIL_MOIS = 6 : au-dela, on previent le lecteur que
     l'article a vieilli. Calcule a chaque visite dans le navigateur, jamais a
     la generation, pour rester exact sans regenerer le site. */
  (function(){
    const SEUIL_MOIS = 6;
    const prose = document.querySelector('.article-prose[data-date-iso]');
    if (!prose) return;
    const publie = new Date(prose.getAttribute('data-date-iso'));
    if (isNaN(publie)) return;
    const maintenant = new Date();
    const mois = (maintenant.getFullYear() - publie.getFullYear()) * 12
               + (maintenant.getMonth() - publie.getMonth());
    if (mois < SEUIL_MOIS) return;
    const notice = document.createElement('p');
    notice.className = 'article-freshness-notice';
    notice.textContent = "Cet article a \u00e9t\u00e9 publi\u00e9 il y a plus de "
      + (mois >= 12 ? Math.floor(mois / 12) + (mois >= 24 ? " ans" : " an") : mois + " mois")
      + ". Certaines informations peuvent avoir \u00e9volu\u00e9 depuis. "
      + "En cas de doute, demandez-nous en boutique.";
    const frame = prose.querySelector('.arch-frame');
    if (frame && frame.parentNode) {
      frame.parentNode.insertBefore(notice, frame.nextSibling);
    } else {
      const conteneur = prose.querySelector('.container-narrow') || prose;
      conteneur.insertBefore(notice, conteneur.firstChild);
    }
  })();
"""

# Libelles utilises uniquement dans la nav du haut, quand ils different du
# libelle canonique de NAV_ITEMS (qui sert au fil d'Ariane et au JSON-LD).
NAV_TOP_LABELS = {"contact": "Nous rendre visite"}

NAV_ITEMS = [
    ("accueil", "La Boutique", "index.html"),
    ("conseils", "Nos Conseils", "nos-conseils.html"),
    ("marques", "Nos Marques", "marques.html"),
    ("sante", "Espace Santé", "espace-sante.html"),
    ("actualites", "Actualités", "actualites.html"),
    ("contact", "Contact", "contact.html"),
]

FOOTER_ICON_SVGS = {
    "instagram": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>'
}


def render_head(title, description, path, og_image="og-image.jpg", extra_jsonld=None):
    canonical = f"{BASE_URL}/{path}" if path != "index.html" else f"{BASE_URL}/"
    jsonld = extra_jsonld or ""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="REMPLACER-VERIFICATION-SEARCH-CONSOLE" />
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%23161616'/%3E%3Ctext x='50' y='66' font-size='48' text-anchor='middle' fill='%23FBF6EF' font-family='Georgia,serif'%3EA%3C/text%3E%3C/svg%3E">
{jsonld}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;500;700;800&family=Archivo+Black&family=Playfair+Display:ital,wght@0,500;0,600;1,500&family=Comfortaa:wght@600;700&family=Space+Grotesk:wght@700&family=Marcellus&family=Anton&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site.css?v={CSS_VERSION}">"""


def render_header(active_key):
    link_parts = []
    for key, label, href in NAV_ITEMS:
        # L'onglet vers contact.html a ete retire le 30/07/2026 puis remis le
        # 31/07/2026 a la demande du client, sous le libelle « Nous rendre
        # visite » (le libelle canonique « Contact » reste celui du fil
        # d'Ariane et du JSON-LD).
        cls = ' class="active"' if key == active_key else ""
        link_parts.append(f'<a href="/{href}"{cls}>{NAV_TOP_LABELS.get(key, label)}</a>')
    links = "\n      ".join(link_parts)
    # La classe "scrolled" est appliquee en dur depuis le 31/07/2026 (demande du
    # client) : le header garde en permanence son fond creme translucide et sa
    # bulle d'onglet actif terracotta, y compris en haut de page. Elle reste une
    # classe (plutot qu'une fusion dans le style de base) pour ne rien changer a
    # la cascade CSS existante, deja verifiee sur 31 pages.
    return f"""<header id="siteHeader" class="scrolled">
  <div class="container">
    <a href="/index.html" class="logo" aria-label="ACTU EYES — Votre Opticien">
      <img src="/images/logo-actueyes-transparent.png" alt="ACTU EYES — Votre Opticien" class="logo-img">
    </a>
    <nav class="main-nav" id="mainNav">
      {links}
    </nav>
    <div class="header-actions">
      <a href="tel:0148575740" class="header-phone-bubble">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        <span class="phone-full">01 48 57 57 40</span>
      </a>
      <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""


FOOTER = """<footer>
  <div class="container">
    <div class="footer-top">
      <div class="footer-logo">
        <img src="/images/logo-actueyes-white.png" alt="ACTU EYES — Votre Opticien" class="footer-logo-img">
      </div>
      <div class="footer-links">
        <div>
          <h4>Navigation</h4>
          <ul>
            <li><a href="/notre-histoire.html">Notre histoire</a></li>
            <li><a href="/nos-conseils.html">Nos Conseils</a></li>
            <li><a href="/marques.html">Nos Marques</a></li>
            <li><a href="/espace-sante.html">Espace Santé</a></li>
            <li><a href="/enfants.html">Enfants</a></li>
            <li><a href="/actualites.html">Actualités</a></li>
          </ul>
        </div>
        <div>
          <h4>Contact</h4>
          <ul>
            <li>15 Rue des Lumières, 93100 Montreuil</li>
            <li>01 48 57 57 40</li>
            <li>actueyes.montreuil@gmail.com</li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> ACTU EYES — Tous droits réservés.</span>
      <span><a href="/mentions-legales.html">Mentions légales</a> · <a href="/mentions-legales.html#confidentialite">Confidentialité</a></span>
      <span>Opticien · Montreuil</span>
    </div>
  </div>
</footer>"""


def render_page(active_key, title, description, path, body, hero_img=None, extra_jsonld=None, breadcrumb_override=None, hero_pos=None, hero_veil=None):
    # hero_veil : voile sombre pose sur la photo de bandeau, surchargeable page
    # par page. La regle est ecrite dans le <style> en ligne de la page (donc
    # apres site.css) : elle l'emporte a specificite egale, et surtout elle ne
    # modifie pas SHARED_CSS, donc ni CSS_VERSION ni les 30 autres pages.
    # Maillage interne : les pages listees dans PAGE_ARTICLES recoivent un bloc
    # "Nos articles sur le sujet" insere juste avant leur CTA final.
    body = with_page_articles(path, body)

    hero_pos_decl = f'--hero-pos:{hero_pos};' if hero_pos else ''
    veil_rule = (
        f'.page-hero{{background:{hero_veil},'
        f'var(--hero-img) center var(--hero-pos, 15%)/cover no-repeat;}}'
    ) if hero_veil else ''
    style_var = f'<style>:root{{--hero-img:url(\'{hero_img}\');{hero_pos_decl}}}{veil_rule}</style>\n' if hero_img else ''

    # Structured data: the Optician/LocalBusiness block goes on every page
    # (not just the homepage) so Google can associate NAP + hours with each
    # URL independently, plus a BreadcrumbList matching the visible
    # breadcrumb on inner pages. Page-specific schema (FAQPage, etc.) is
    # passed in via extra_jsonld and appended after these.
    # breadcrumb_override lets callers supply a full custom crumb trail (list
    # of (name, url) tuples) instead of the default 2-level "La Boutique >
    # Nav label" — used by individual /actualites/<slug>.html article pages,
    # which need a 3rd level ("La Boutique > Actualités > Titre article").
    jsonld_parts = [OPTICIAN_JSONLD]
    if breadcrumb_override:
        jsonld_parts.append(breadcrumb_jsonld(breadcrumb_override))
    elif active_key != "accueil":
        nav_label = next((label for key, label, _ in NAV_ITEMS if key == active_key), title)
        jsonld_parts.append(breadcrumb_jsonld([
            ("La Boutique", f"{BASE_URL}/"),
            (nav_label, f"{BASE_URL}/{path}"),
        ]))
    if extra_jsonld:
        jsonld_parts.append(extra_jsonld)
    combined_jsonld = "\n".join(jsonld_parts)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
{render_head(title, description, path, extra_jsonld=combined_jsonld)}
{style_var}</head>
<body>

{render_header(active_key)}

{body}

{FOOTER}

<div class="article-modal-overlay" id="articleModalOverlay" aria-hidden="true">
  <div class="article-modal" role="dialog" aria-modal="true" aria-label="Article">
    <button type="button" class="article-modal-close" aria-label="Fermer l'article">✕</button>
    <div class="article-modal-body"></div>
  </div>
</div>

<script>
{SCRIPT_JS}
</script>

</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path} ({len(html)} bytes)")


# ============================================================================
# PAGE 1 — index.html (page d'accueil = "La Boutique")
# Historiquement une page séparée "la-boutique.html" : devenue la page
# d'accueil le 24/07/2026 à la demande du client, l'onglet nav gardant le nom
# "La Boutique" (voir NAV_ITEMS). Contenu recentré le 24/07/2026 sur l'histoire
# pure (fondateurs + quartier) — la section "Nos services" migrée ici depuis
# l'ancienne page services.html avait alors été déplacée vers nos-conseils.html.
#
# Refonte du 30/07/2026 : le client a jugé, après coup, que faire atterrir
# chaque visiteur directement sur le grand récit (sans aperçu des activités du
# magasin) n'était pas idéal côté expérience client. La page est devenue une
# "vraie" page d'accueil : nouveau hero de bienvenue + CTA, puis un aperçu des
# 4 univers (Optique/Nos Marques/Espace Santé/Espace Audition) sous forme de
# cartes photo cliquables (`.services-refined` / `.refined-card`, voir CSS).
# L'intégralité du récit d'origine (hero "Notre histoire" + les 4 sections
# fondateurs/quartier + le bloc "Aujourd'hui") est conservée SANS AUCUNE
# COUPURE, simplement repoussée plus bas sur la page, juste après l'aperçu des
# 4 univers — l'ancien texte du hero (eyebrow+h1+intro) devient l'intro de la
# nouvelle section "Notre histoire" qui rouvre le récit. Le CTA final "Envie de
# nous rencontrer ?" reste inchangé, tout en bas. Voir le projet Claude pour le
# détail de cette décision et des maquettes validées par le client.
#
# Photos des 4 cartes (30/07/2026, remplacées le jour même) : premier essai
# avec des photos secondaires déjà sur le site (jugé insatisfaisant : le
# client voulait des photos entièrement nouvelles, pas déjà utilisées
# ailleurs). Le client a fourni 4 nouvelles photos (Pexels) le jour même,
# recadrées/optimisées par Claude pour le format carte (ratio ~2.3:1, 1000px
# de large, JPEG optimisé) et stockées dans /images/accueil-cartes/ :
# accueil-optique-lunetterie.jpg, marques-vitrine.jpg, accueil-espace-sante.jpg,
# accueil-espace-audition.jpg. Ce sont les photos définitives.
#
# Refonte du 31/07/2026 (demande client : « la page est vide mise a part
# l'histoire de la boutique »). La page d'accueil devient une vraie vitrine :
#   1. hero de bienvenue (inchange)
#   2. apercu des 4 univers, textes enrichis (2 phrases par carte)
#   3. NOUVEAU « En boutique » : examen de vue SANS rendez-vous (optique) et
#      test auditif SUR rendez-vous (audition), avec explicatif complet
#   4. NOUVEAU bloc sombre « Ce que dit la loi » : adaptation d'ordonnance par
#      l'opticien (art. R4362-12 et D4362-12-1 CSP, decrets 2016-1381 et
#      2024-617), durees de validite (1 an < 16 ans / 5 ans 16-42 / 3 ans > 42)
#      et maintien du remboursement Secu + mutuelle
#   5. NOUVEAU bloc 100 % Sante (monture plafonnee a 30 EUR, classe 1 audio)
#   6. NOUVEAU bandeau marques (10 noms + lien vers marques.html)
#   7. APERCU de l'histoire + bouton vers la nouvelle page notre-histoire.html
#   8. NOUVEAU apercu des 3 dernieres actualites (injecte au moment du rendu
#      via le jeton <!--ACTUALITES_TEASER-->, car ARTICLES est defini bien plus
#      bas dans ce fichier)
#   9. NOUVEAU bandeau infos pratiques (adresse/horaires/acces/tel + carte)
#  10. CTA final (inchange)
# Aucune classe CSS nouvelle n'a ete introduite : SHARED_CSS est intact, donc
# CSS_VERSION ne bouge pas et les autres pages n'ont pas a etre redeployees.
# ============================================================================
BODY_BOUTIQUE = """
<section class="edito-hero">
  <div class="edito-grid">
    <div class="edito-tx">
      <span class="eyebrow">Opticien à Montreuil</span>
      <h1>Le regard,<br>une <em>signature</em>.</h1>
      <p>Les plus belles maisons — Prada, Dior, Burberry — choisies une par une, et le temps qu'il faut pour trouver la vôtre.</p>
      <div class="hero-actions">
        <a href="/marques.html" class="btn btn-primary">Découvrir nos marques</a>
        <a href="/contact.html" class="btn btn-outline">Nous rendre visite</a>
      </div>
    </div>
    <div class="edito-img" style="background-image:url('/images/accueil/hero-vitrine.jpg');"></div>
  </div>
</section>
<div class="brand-ticker" aria-hidden="true">
  <div class="brand-ticker-run"><span>PRADA</span><span class="c">DIOR</span><span>BURBERRY</span><span>FENDI</span><span class="c">CELINE</span><span>RAY-BAN</span><span>LOEWE</span><span class="c">GUCCI</span><span>SAINT LAURENT</span><span class="c">MIU MIU</span><span>RALPH LAUREN</span><span class="c">GIVENCHY</span><span>PRADA</span><span class="c">DIOR</span><span>BURBERRY</span><span>FENDI</span><span class="c">CELINE</span><span>RAY-BAN</span><span>LOEWE</span><span class="c">GUCCI</span><span>SAINT LAURENT</span><span class="c">MIU MIU</span><span>RALPH LAUREN</span><span class="c">GIVENCHY</span></div>
</div>

<section class="services-refined">
  <div class="container">
    <div class="section-head-split">
      <div>
        <span class="eyebrow">Chez ACTU EYES</span>
        <h2>Votre vue, entre de bonnes mains</h2>
      </div>
      <p>Cinq univers pensés avec la même exigence de conseil, du choix de votre monture au soin de votre vision.</p>
    </div>
    <div class="refined-grid">
      <a class="refined-card reveal" href="/nos-conseils.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-optique-lunetterie.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="15" r="3.2"/><circle cx="18" cy="15" r="3.2"/><path d="M9.2 15h5.6M2.5 13l1.8-6.5a2 2 0 0 1 1.9-1.5h.3M21.5 13l-1.8-6.5a2 2 0 0 0-1.9-1.5h-.3"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Optique &amp; lunetterie</h3>
          <p>Montures, verres, traitements, amincissement : nos conseils pour bien choisir et faire durer vos lunettes. On prend le temps de l'essayage, et on réajuste votre monture aussi souvent qu'il le faut.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/marques.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/marques-vitrine.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.6 3H5a2 2 0 0 0-2 2v7.6c0 .5.2 1 .6 1.4l9 9c.8.8 2 .8 2.8 0l7-7c.8-.8.8-2 0-2.8l-9-9c-.4-.4-.9-.6-1.4-.6z"/><circle cx="8.5" cy="8.5" r="1.4"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Nos marques</h3>
          <p>Des maisons sélectionnées une par une, de Ray-Ban à Loewe en passant par Prada, Dior et Saint Laurent. Des grandes maisons aux créateurs plus confidentiels, chaque collection est choisie, jamais subie.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/espace-sante.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-espace-sante.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Espace santé</h3>
          <p>Examen de vue, défauts visuels, myopie de l'enfant, maladies de l'œil : tout ce qu'il faut savoir pour prendre soin de votre vision. Un contrôle régulier reste la meilleure des préventions.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/enfants.html">
        <div class="refined-photo contain" style="--img:url('/images/enfants/hero-enfants.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.5 14.5a4 4 0 0 0 7 0"/><line x1="9" y1="9.6" x2="9" y2="10"/><line x1="15" y1="9.6" x2="15" y2="10"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Espace enfants</h3>
          <p>Montures incassables, verres qui freinent la myopie, 100 % Santé : tout notre accompagnement pour les yeux des plus jeunes.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
      <a class="refined-card reveal" href="/actualites.html">
        <div class="refined-photo" style="--img:url('/images/accueil-cartes/accueil-actualites.jpg');">
          <span class="refined-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a1 1 0 0 0-1 1v12a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z"/><path d="M7 8h9M7 12h9M7 16h5"/></svg></span>
        </div>
        <div class="refined-body">
          <h3>Nos actualités</h3>
          <p>Conseils vue, mode lunettes, nouveautés verres et lentilles, remboursements : le journal de la boutique, enrichi chaque semaine.</p>
          <span class="more">En savoir plus →</span>
        </div>
      </a>
    </div>
  </div>
</section>

<section class="section-head center" style="padding:78px 0 0;">
  <div class="container">
    <span class="eyebrow">En boutique</span>
    <h2>Faire le point sur votre vue</h2>
    <p style="max-width:660px;margin:0 auto;">Un examen de vue simple, gratuit et sans engagement, que vous pouvez faire chez nous au centre commercial Grand Angle, à deux pas de la mairie de Montreuil, quand vous voulez.</p>
  </div>
</section>

<section class="split story-block" id="examen-de-vue">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/examen-refracteur.jpg" alt="Examen de vue au réfracteur dans l'espace dédié de la boutique" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Sans rendez-vous</span>
        <h2>L'examen de vue en boutique, quand vous voulez</h2>
        <p>Vos lunettes ne vous conviennent plus, mais votre prochain rendez-vous chez l'ophtalmologiste est encore loin ? Poussez simplement la porte : notre opticien réalise un <a href="/espace-sante.html#examen" class="ilink">examen de vue complet</a> dans l'espace de réfraction attenant au magasin, gratuitement et sans rendez-vous.</p>
        <p>Un point important à connaître : cet examen n'est pas une consultation médicale et ne donne pas lieu à une nouvelle ordonnance. En revanche, la réglementation autorise l'opticien à <a href="/actualites/renouveler-lunettes-sans-nouvelle-ordonnance-opticien.html" class="ilink">adapter la correction inscrite sur une ordonnance que vous possédez déjà</a> — et c'est précisément ce que permet cet examen.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Gratuit, sans rendez-vous et sans engagement</li>
          <li><span class="check">✓</span> Mesure de la vision de loin et de près, en conditions d'examen</li>
          <li><span class="check">✓</span> Adaptation de la correction de votre ordonnance en cours de validité</li>
          <li><span class="check">✓</span> Votre prescripteur est informé de toute modification apportée</li>
          <li><span class="check">✓</span> Vos lunettes restent remboursées par la Sécurité sociale et votre mutuelle</li>
        </ul>
        <a href="/espace-sante.html" class="block-more">Découvrir tout notre Espace Santé →</a>
      </div>
    </div>
  </div>
</section>

<style>
.terra-section{background:var(--terracotta);}
.terra-section .block-more{color:var(--cream);border-bottom-color:rgba(251,246,239,0.55);}
.terra-section .block-more:hover{color:var(--cream);border-bottom-color:var(--cream);}
.terra-section .eyebrow{color:var(--cream);}
.terra-section .section-head p{color:rgba(251,246,239,0.86);}
.terra-section .dark-card{background:rgba(251,246,239,0.10);border-color:rgba(251,246,239,0.26);}
.terra-section .dark-card .badge{background:var(--cream);}
.terra-section .dark-card .badge svg{stroke:var(--terracotta);}
.terra-section .dark-card p{color:rgba(251,246,239,0.88);}
</style>
<section class="dark-section terra-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Bon à savoir</span>
      <h2>Ce que l'examen en boutique permet — et ce qu'il ne permet pas</h2>
      <p>Le rôle de l'opticien est encadré par la loi. Trois repères pour savoir exactement à quoi vous attendre en poussant notre porte.</p>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Adapter, oui — prescrire, non</h3>
        <p>Depuis 2016, l'opticien-lunetier peut modifier la correction figurant sur votre ordonnance après un examen de la réfraction, sauf opposition expresse du prescripteur mentionnée sur l'ordonnance. Depuis 2024, il peut même le faire dès la première délivrance, avec l'accord du prescripteur. Il ne peut en revanche ni établir une première ordonnance, ni poser un diagnostic médical : le suivi ophtalmologique reste indispensable.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <h3>Votre ordonnance vaut plusieurs années</h3>
        <p>Une ordonnance de lunettes reste valable 1 an avant 16 ans, 5 ans entre 16 et 42 ans, et 3 ans au-delà de 42 ans. Tant qu'elle court, nous pouvons y adapter votre correction. Deux exceptions à retenir : les moins de 16 ans, et une presbytie découverte pour la première fois, qui nécessitent l'un comme l'autre un passage chez l'ophtalmologiste.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg></div>
        <h3>Le remboursement est préservé</h3>
        <p>C'est tout l'intérêt de la démarche : des lunettes délivrées sur une ordonnance adaptée par l'opticien restent prises en charge par la Sécurité sociale et votre mutuelle, dans les conditions habituelles — un équipement tous les 2 ans à partir de 16 ans, tous les ans avant 16 ans. Vous ne perdez rien, vous gagnez du temps.</p>
      </div>
    </div>
    <div class="block-more-center"><a href="/actualites/renouveler-lunettes-sans-nouvelle-ordonnance-opticien.html" class="block-more">Ordonnance expirée ? Tout ce que l'opticien peut faire →</a></div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Vos remboursements</span>
      <h2>Le reste à charge 0 sur vos lunettes</h2>
      <p>La réforme 100 % Santé garantit une gamme de lunettes de qualité intégralement prise en charge. Voici ce que cela change concrètement pour vous.</p>
    </div>
    <div class="reimburse-grid">
      <div class="reimburse-card highlight reveal">
        <span class="tag">Reste à charge 0</span>
        <h3>L'offre 100 % Santé</h3>
        <p>Avec une affiliation à la Sécurité sociale et une complémentaire santé responsable, la prise en charge couvre l'intégralité du prix : 0 € à votre charge. Cela comprend une monture plafonnée à 30 € — proposée en plusieurs coloris — et des verres traités <a href="/nos-conseils.html#traitements-verres" class="ilink">anti-reflet, anti-rayure et amincis</a> selon votre correction, quelle qu'elle soit.</p>
      </div>
      <div class="reimburse-card reveal">
        <span class="tag">Vos démarches</span>
        <h3>Nous nous occupons de la paperasse</h3>
        <p>Nous vérifions vos droits, appliquons le tiers payant dès que votre mutuelle le permet et vous remettons un <a href="/actualites/comprendre-devis-normalise-lunettes.html" class="ilink">devis normalisé</a> gratuit avant tout engagement, pour que vous puissiez comparer en toute transparence. Rien ne vous oblige à choisir le 100 % Santé : vous pouvez aussi panacher, par exemple une monture libre avec des verres 100 % Santé. Le renouvellement est pris en charge tous les 2 ans à partir de 16 ans, tous les ans avant 16 ans.</p>
      </div>
    </div>
    <div class="block-more-center"><a href="/actualites/100-pour-cent-sante-2026.html" class="block-more">Le 100 % Santé en 2026, en détail →</a></div>
  </div>
</section>

<section class="marques">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Nos marques</span>
      <h2>Des maisons choisies une par une</h2>
      <p>Des grandes maisons de couture aux créateurs plus confidentiels, une sélection resserrée que nous assumons entièrement — et que vous pouvez essayer tranquillement en boutique.</p>
    </div>
    <div class="marques-grid">
      <div class="marque-item">Ray-Ban</div>
      <div class="marque-item">Prada</div>
      <div class="marque-item">Dior</div>
      <div class="marque-item">Gucci</div>
      <div class="marque-item">Saint Laurent</div>
      <div class="marque-item">Celine</div>
      <div class="marque-item">Loewe</div>
      <div class="marque-item">Fendi</div>
      <div class="marque-item">Miu Miu</div>
      <div class="marque-item">Ralph Lauren</div>
    </div>
    <div style="text-align:center;margin-top:40px;">
      <a href="/marques.html" class="btn btn-outline">Voir toutes nos marques</a>
    </div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/histoire/quartier-melies.jpg" alt="Le cinéma Le Méliès et le quartier Cœur de Ville à Montreuil" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Notre histoire</span>
        <h2>Un opticien qui a grandi avec son quartier</h2>
        <p>Reprise en 2018 par Mikhael, la boutique s'est réinventée : nouvelles marques, nouvelle ambiance, et une relation plus proche avec chaque client. En 2021, Sudaya rejoint l'aventure ; en 2025, il devient associé d'ACTU EYES.</p>
        <p>Deux parcours, une même exigence : le haut de gamme accessible, et le service client avant tout.</p>
        <a href="/notre-histoire.html" class="btn btn-primary" style="margin-top:30px;">Lire toute notre histoire</a>
      </div>
    </div>
  </div>
</section>

<style>
.avis-section{background:var(--cream-2);}
.avis-actions{margin-top:34px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}
</style>
<section class="avis-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Vos retours</span>
      <h2>Ce que disent nos clients</h2>
      <p>Nos clients partagent leur expérience sur notre fiche Google. Le meilleur moyen de vous faire une idée : passer nous voir au centre commercial Grand Angle.</p>
    </div>
    <div class="avis-actions">
      <a href="https://www.google.com/maps/search/?api=1&query=ACTU+EYES+Montreuil" class="btn btn-outline" target="_blank" rel="noopener">Voir les avis sur Google</a>
      <a href="/contact.html" class="btn btn-primary">Venir nous voir</a>
    </div>
  </div>
</section>

<!--ACTUALITES_TEASER-->

<section class="contact" style="background:var(--cream);">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Nous rendre visite</span>
      <h2>Infos pratiques</h2>
      <p>Centre commercial Grand Angle, quartier Cœur de Ville, face à la mairie de Montreuil.</p>
    </div>
    <div class="contact-grid">
      <div class="contact-info-card reveal">
        <h3>ACTU EYES</h3>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
          <div><strong>Adresse</strong><span>15 Rue des Lumières, 93100 Montreuil<br>Centre commercial Grand Angle</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div><strong>Horaires</strong><span>Lundi – Samedi, 10h00 – 19h30<br>Fermé le dimanche</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
          <div><strong>Accès</strong><span>Métro Mairie de Montreuil (ligne 9)</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>
          <div><strong>Téléphone</strong><a href="tel:0148575740">01 48 57 57 40</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 6l-10 7L2 6"/><rect x="2" y="4" width="20" height="16" rx="2"/></svg></div>
          <div><strong>Email</strong><a href="mailto:actueyes.montreuil@gmail.com">actueyes.montreuil@gmail.com</a></div>
        </div>
        <div class="social-row">
          <a href="https://www.instagram.com/actueyes.montreuil/" target="_blank" rel="noopener" aria-label="Instagram">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>
          </a>
        </div>
      </div>
      <div class="map-frame reveal">
        <iframe src="https://www.google.com/maps?q=15+rue+des+Lumieres+93100+Montreuil&output=embed" loading="lazy" allowfullscreen title="Localisation ACTU EYES"></iframe>
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie de nous rencontrer ?</h2>
    <p>Venez découvrir la boutique au centre commercial Grand Angle, à Montreuil.</p>
    <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 8 — notre-histoire.html
# ============================================================================
# Creee le 31/07/2026 a la demande du client : la page d'accueil ne garde plus
# qu'un APERCU de l'histoire (bloc "Notre histoire" + bouton), et l'integralite
# du recit d'origine (fondateurs + quartier + "Aujourd'hui") est deplacee ici
# SANS AUCUNE COUPURE. Le client a choisi de ne PAS ajouter d'onglet dans le
# menu du haut : on y accede par le bouton de l'accueil et par le pied de page.
# La page reprend donc active_key="accueil" (l'onglet "La Boutique" reste
# surligne, ce qui est coherent : c'est une sous-page de la boutique) avec un
# breadcrumb_override explicite pour le JSON-LD.
BODY_HISTOIRE = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Notre histoire</div>
    <span class="eyebrow">Notre histoire</span>
    <h1>ACTU EYES, un opticien qui a grandi avec son quartier</h1>
    <p>Reprise en 2018 puis réinventée, ACTU EYES est devenue une adresse attachée à une idée simple : le bon conseil, le bon choix, et un service qui met le client avant tout — au cœur du quartier Cœur de Ville, face à la mairie de Montreuil.</p>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/histoire/boutique-comptoir.jpg" alt="Intérieur de la boutique ACTU EYES à Montreuil">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">2018 — La reprise</span>
        <h2>Une boutique reprise, puis réinventée</h2>
        <p>En 2018, Mikhael reprend la boutique d'optique du quartier Cœur de Ville, à Montreuil. Très vite, il la transforme : nouvelles marques, nouvelle ambiance, et surtout une relation plus proche, plus attentive, que celle qu'il avait connue avant la reprise.</p>
        <p>Le positionnement se dessine dès ces premières années, et n'a plus bougé depuis : des marques haut de gamme, mais un large choix de montures très abordables et vraiment belles — pour que personne ne reparte sans une paire qui lui plaît, quel que soit son budget.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">2021 → 2025</span>
        <h2>Une rencontre, puis un partenariat</h2>
        <p>En 2021, Sudaya rejoint l'équipe. Il fait rapidement ses preuves : le sens du conseil, l'écoute, le soin apporté à chaque client. De cette collaboration naît une envie commune, et en 2023, Mikhael et Sudaya ouvrent ensemble une seconde enseigne, à Paris.</p>
        <p>Le lien se resserre encore en 2025 : Sudaya rachète des parts d'ACTU EYES Montreuil, scellant un partenariat pensé pour durer. Deux boutiques, une même exigence, et la même personne au centre de tout — vous.</p>
        <div class="founders">
          <div class="initials"><span>M</span><span>S</span></div>
          <div class="meta"><strong>Mikhael &amp; Sudaya</strong>Associés d'ACTU EYES</div>
        </div>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/histoire/equipe-boutique.jpg" alt="L'équipe d'ACTU EYES en boutique à Montreuil" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/histoire/quartier-coeur-de-ville.jpg" alt="Le quartier Cœur de Ville et le centre commercial Grand Angle à Montreuil" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Le quartier</span>
        <h2>Au Cœur de Ville, entre vie active et vie de quartier</h2>
        <p>Installée au centre commercial Grand Angle, dans le quartier Cœur de Ville, la boutique reçoit une clientèle à l'image de Montreuil : un quartier à la fois très actif et résidentiel, où se croisent familles, actifs, étudiants et habitants de longue date.</p>
        <p>C'est cette diversité qui fait notre quotidien, et qui guide notre manière de travailler : prendre le temps, écouter, et adapter chaque conseil à la personne qui est en face — pas l'inverse.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Aujourd'hui</span>
      <h2>Le service client avant tout</h2>
      <p>Notre priorité n'a pas changé : votre satisfaction. Nous sommes attentifs à vos attentes et à vos remarques — sur le plan esthétique, technique comme tarifaire — pour que vous repartiez avec l'équipement qui vous convient vraiment, et l'envie de revenir.</p>
      <p>Au comptoir comme en atelier, cela se traduit très concrètement : un examen de vue sans rendez-vous pour ajuster votre correction, un large choix de montures à essayer sans pression, le montage et l'adaptation de vos verres, ainsi que tous les petits gestes du quotidien — resserrer une branche, changer des plaquettes, réparer une paire abîmée — que nous rendons le plus souvent sur place et sans attendre.</p>
      <p>Nous vous accompagnons aussi sur le volet administratif : devis normalisé clair, tiers payant avec la plupart des mutuelles et prise en charge du 100&nbsp;% Santé, pour que le budget ne soit jamais un frein à une bonne vision. C'est cette continuité, de l'accueil au suivi, qui fait revenir nos clients à Montreuil — et souvent leurs proches.</p>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie de nous rencontrer ?</h2>
    <p>Venez découvrir la boutique au centre commercial Grand Angle, à Montreuil.</p>
    <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 3 — espace-sante.html (prévention et santé visuelle)
# ============================================================================
BODY_SANTE = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Espace Santé</div>
    <span class="eyebrow">Prévention &amp; conseils</span>
    <h1>Espace Santé</h1>
    <p>Examen de vue, défauts visuels, myopie de l'enfant, maladies de l'œil et conseils du quotidien : toutes les clés pour comprendre et prendre soin de votre vue, à chaque âge de la vie.</p>
  </div>
</section>

<section class="split story-block" id="examen">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/controle-vue.jpg" alt="Contrôle de la vue à l'autoréfractomètre en boutique">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Examen de vue</span>
        <h2>Un contrôle régulier, la meilleure des préventions</h2>
        <p>L'acuité visuelle se mesure en deux temps : de loin, avec l'échelle de Monoyer (lecture de lettres à quelques mètres), et de près, avec l'échelle de Parinaud (lecture à distance de bras). Ensemble, elles permettent à notre équipe d'évaluer précisément votre vue et de détecter une éventuelle évolution de votre correction.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Difficulté à lire les panneaux ou plaques de rue</li>
          <li><span class="check">✓</span> Besoin de rapprocher un texte ou un écran pour le lire</li>
          <li><span class="check">✓</span> Maux de tête ou fatigue oculaire en fin de journée</li>
          <li><span class="check">✓</span> Vision qui se trouble ponctuellement, de près ou de loin</li>
        </ul>
        <p>Le moindre doute mérite un contrôle : n'attendez pas de gêne franche pour prendre rendez-vous.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Bonnes pratiques</span>
      <h2>À quelle fréquence contrôler sa vue ?</h2>
      <p>Le rythme recommandé dépend surtout de l'âge et des facteurs de risque : voici les grands repères à connaître.</p>
    </div>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Enfants</div>
        <h3>Dès 6 mois</h3>
        <p>Premiers dépistages à 6 mois, 3 ans et 6 ans, puis suivi par un ophtalmologiste tous les 2 ans.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">18 – 40 ans</div>
        <h3>Tous les 2 ans</h3>
        <p>En l'absence de trouble, un contrôle tous les 2 ans suffit — annuel en cas de forte exposition aux écrans.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">40 – 60 ans</div>
        <h3>Tous les 1 à 2 ans</h3>
        <p>La presbytie s'installe et le risque de glaucome augmente : un suivi plus rapproché est recommandé.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">60 ans et +</div>
        <h3>Chaque année</h3>
        <p>Cataracte, DMLA et glaucome deviennent plus fréquents : un contrôle annuel est conseillé.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block" id="examen-detail">
  <div class="container-narrow">
    <span class="eyebrow">Le contrôle de la vue</span>
    <h2>Comment se déroule un examen de vue ?</h2>
    <p>Un examen de vue ne se résume pas à lire des lettres sur un tableau. En boutique, il suit plusieurs étapes complémentaires, indolores et rapides — une vingtaine de minutes — destinées à mesurer précisément votre vision et à adapter la correction de votre ordonnance.</p>
    <h3>1. L'entretien</h3>
    <p>Tout part de vos usages et de votre gêne : travail sur écran, conduite de nuit, lecture, antécédents, dernière correction portée. Ces informations orientent tout l'examen.</p>
    <h3>2. La mesure automatique</h3>
    <p>L'autoréfractomètre estime en quelques secondes une correction de départ, en analysant la façon dont la lumière se réfléchit au fond de l'œil. Ce n'est qu'un point de départ, jamais la mesure finale.</p>
    <h3>3. La réfraction subjective</h3>
    <p>C'est le cœur de l'examen : à l'aide d'une lunette d'essai ou d'un réfracteur, nous affinons la correction verre après verre en vous faisant comparer (« est-ce mieux ainsi, ou ainsi ? »). C'est votre ressenti qui décide, œil par œil.</p>
    <h3>4. L'acuité, de loin et de près</h3>
    <p>On vérifie la netteté à différentes distances et l'équilibre entre les deux yeux, pour un confort réel au quotidien — pas seulement sur un tableau.</p>
    <p>À retenir : cet examen permet d'<a href="/actualites/renouveler-lunettes-sans-nouvelle-ordonnance-opticien.html" class="ilink">adapter la correction d'une ordonnance en cours de validité</a>. Il ne remplace pas la consultation de l'ophtalmologiste, qui contrôle aussi la santé de vos yeux.</p>
  </div>
</section>

<section class="split alt story-block" id="ordonnance">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Décrypter</span>
        <h2>Lire et comprendre son ordonnance</h2>
        <p>Les chiffres d'une ordonnance de lunettes suivent toujours la même logique. Une fois qu'on les connaît, tout devient clair.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> <strong>La sphère</strong> : la puissance de correction. Un signe « − » indique une myopie, un signe « + » une hypermétropie.</li>
          <li><span class="check">✓</span> <strong>Le cylindre</strong> : la correction de l'astigmatisme. Présent, il s'accompagne toujours d'un axe.</li>
          <li><span class="check">✓</span> <strong>L'axe</strong> (0 à 180°) : l'orientation de l'astigmatisme à corriger.</li>
          <li><span class="check">✓</span> <strong>L'addition (ADD)</strong> : la puissance ajoutée pour la vision de près, en cas de presbytie.</li>
          <li><span class="check">✓</span> <strong>OD / OG</strong> : œil droit / œil gauche.</li>
        </ul>
        <p>En cas de doute, nous reprenons chaque ligne avec vous, sans jargon.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/ordonnance-lunette-essai.jpg" alt="Lunette d'essai et verres gradués lors d'un examen de vue" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="services alt" id="defauts">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Défauts visuels</span>
      <h2>Mieux comprendre les troubles de la vue</h2>
      <p>Myopie, hypermétropie, astigmatisme et presbytie sont des troubles de la réfraction très courants — chacun se corrige différemment selon son origine.</p>
    </div>
    <div class="services-grid">
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg></div>
        <h3>Myopie</h3>
        <p>La vision de loin est floue tandis que la vision de près reste nette. C'est le trouble visuel le plus répandu, souvent diagnostiqué dès l'enfance.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Hypermétropie</h3>
        <p>À l'inverse de la myopie, c'est la vision de près qui demande un effort de mise au point, avec parfois une fatigue oculaire associée.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16M4 6h16M4 18h10"/></svg></div>
        <h3>Astigmatisme</h3>
        <p>Une courbure irrégulière de la cornée déforme légèrement les images, de près comme de loin, et nécessite une correction spécifique.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg></div>
        <h3>Presbytie</h3>
        <p>À partir de 44-45 ans environ, l'œil accommode moins bien de près : elle concerne tout le monde, tôt ou tard, myope ou non.</p>
      </div>
    </div>
    <p style="max-width:680px;margin:32px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Le daltonisme, trouble de la perception des couleurs, est plus rare et généralement présent dès la naissance : un dépistage spécifique permet de le confirmer et d'adapter certains équipements au quotidien.</p>
  </div>
</section>

<section class="story-block" id="troubles-detail">
  <div class="container-narrow">
    <span class="eyebrow">En détail</span>
    <h2>Les troubles de la réfraction, expliqués</h2>
    <p>Un œil qui voit net forme l'image exactement sur la rétine. Quand l'œil est trop long, trop court ou irrégulier, l'image se forme avant ou après : c'est un trouble de la réfraction. Voici les quatre principaux, et ce qui les corrige.</p>
    <h3>La myopie</h3>
    <p>L'œil est trop long : l'image des objets éloignés se forme en avant de la rétine. On voit flou de loin, net de près. Elle débute souvent dans l'enfance et peut évoluer jusqu'à l'âge adulte. Correction : verres divergents (−), lentilles, et solutions de <a href="/enfants.html" class="ilink">freination chez l'enfant</a>.</p>
    <h3>L'hypermétropie</h3>
    <p>L'œil est trop court : l'image se forme en arrière de la rétine. Le jeune œil compense en accommodant, ce qui masque le trouble mais fatigue — maux de tête, inconfort de près. Correction : verres convergents (+).</p>
    <h3>L'astigmatisme</h3>
    <p>La cornée (ou le cristallin) n'est pas parfaitement sphérique mais un peu ovale : l'image est déformée à toutes les distances. Il s'associe souvent à une myopie ou une hypermétropie. Correction : verres toriques, définis par un cylindre et un axe.</p>
    <h3>La presbytie</h3>
    <p>Ce n'est pas un défaut de l'œil, mais son évolution naturelle : après 40-45 ans, le cristallin perd en souplesse et la mise au point de près devient difficile. Elle concerne tout le monde. Correction : verres progressifs, verres de proximité, ou lentilles multifocales.</p>
  </div>
</section>

<section class="split story-block" id="myopie-enfant">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/myopie-enfant-signes.jpg" alt="Dépistage visuel chez l'enfant" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Myopie de l'enfant</span>
        <h2>Une vigilance particulière entre 7 et 12 ans</h2>
        <p>C'est souvent entre 7 et 12 ans que la myopie apparaît et évolue le plus rapidement chez l'enfant. Quelques signes doivent alerter les parents :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> L'enfant plisse les yeux pour regarder au loin</li>
          <li><span class="check">✓</span> Il se rapproche du tableau, de la télévision ou d'un livre</li>
          <li><span class="check">✓</span> Il se plaint de maux de tête après l'école</li>
          <li><span class="check">✓</span> Il se frotte les yeux fréquemment</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Bons réflexes</span>
        <h2>Ralentir la progression, au quotidien</h2>
        <p>Certaines habitudes simples, adoptées tôt, aident à freiner l'évolution de la myopie chez l'enfant :</p>
        <ul class="check-list-grid">
          <li><span class="check">✓</span> 40 minutes à 2 heures de temps extérieur chaque jour</li>
          <li><span class="check">✓</span> Écrans de loisir limités à 30 minutes par jour</li>
          <li><span class="check">✓</span> La règle des 20-20-20 : toutes les 20 min, regarder 20 sec à 20 m</li>
          <li><span class="check">✓</span> Une distance de lecture d'au moins 30 cm</li>
        </ul>
        <p>Selon les cas, notre équipe peut également orienter vers des verres ou lentilles spécifiquement conçus pour ralentir la progression de la myopie, prescrits par un ophtalmologiste.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/myopie-enfant-suivi.jpg" alt="Suivi ophtalmologique de l'enfant, consultation avec dépistage à l'ophtalmoscope" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Calendrier</span>
      <h2>Le suivi visuel de l'enfant, étape par étape</h2>
    </div>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">9 mois – 1 an</div>
        <h3>Premier dépistage</h3>
        <p>Recherche d'un strabisme ou d'un trouble précoce lors des visites de suivi du nourrisson.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">3 – 4 ans</div>
        <h3>Bilan préscolaire</h3>
        <p>Contrôle systématique avant l'entrée à l'école, période clé pour détecter amblyopie et troubles précoces.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">6 ans</div>
        <h3>Âge de lecture</h3>
        <p>Les troubles de la réfraction (myopie, astigmatisme) apparaissent souvent à cet âge, à l'entrée en CP.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Après 6 ans</div>
        <h3>Suivi régulier</h3>
        <p>Contrôle tous les 2-3 ans, ou chaque année en cas de correction portée, jusqu'à 16 ans.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block" id="contactologie">
  <div class="container-narrow">
    <span class="eyebrow">Contactologie</span>
    <h2>Les lentilles de contact, de A à Z</h2>
    <p>La contactologie, c'est l'art d'adapter des lentilles à votre œil et à votre mode de vie. Bien choisies et bien suivies, les lentilles offrent une liberté que les lunettes ne permettent pas — sport, champ de vision total, esthétique. Mais elles se posent sur un organe fragile : leur adaptation est un vrai métier, qui ne s'improvise pas.</p>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/contactologie.jpg" alt="Pose d'une lentille de contact souple" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Les types de lentilles</span>
        <h2>Quel type de lentille pour quel besoin ?</h2>
        <ul class="check-list">
          <li><span class="check">✓</span> <strong>Souples journalières</strong> : neuves chaque jour, jetées le soir. Hygiène maximale, aucun entretien, idéales pour un port occasionnel ou les yeux sensibles.</li>
          <li><span class="check">✓</span> <strong>Souples bi-mensuelles / mensuelles</strong> : plus économiques pour un port quotidien, avec un entretien rigoureux.</li>
          <li><span class="check">✓</span> <strong>Toriques</strong> : conçues pour corriger l'astigmatisme.</li>
          <li><span class="check">✓</span> <strong>Multifocales</strong> : plusieurs zones de vision sur une même lentille, pour la presbytie.</li>
          <li><span class="check">✓</span> <strong>Rigides perméables au gaz (LRPG)</strong> : petites et fermes, vision très nette et grande longévité, indiquées pour les astigmatismes forts et les cornées irrégulières.</li>
          <li><span class="check">✓</span> <strong>Sclérales</strong> : de grand diamètre, elles reposent sur le blanc de l'œil — une solution pour les cornées très déformées, comme dans le kératocône.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <span class="eyebrow">Les matériaux</span>
    <h2>Hydrogel, silicone-hydrogel : pourquoi c'est décisif</h2>
    <p>Une lentille est posée sur la cornée, qui a besoin d'oxygène pour rester en bonne santé. Les matériaux modernes en silicone-hydrogel laissent passer bien plus d'oxygène que les anciens hydrogels : meilleure tolérance, moins de sensation d'œil sec en fin de journée, port plus confortable. Le choix du matériau et du rythme de renouvellement se fait selon la sensibilité de vos yeux et la durée de port souhaitée. <a href="/actualites/nouvelles-technologies-lentilles-contact.html" class="ilink">En savoir plus sur les technologies de lentilles</a>.</p>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">L'adaptation</span>
        <h2>Comment se passe une adaptation en lentilles ?</h2>
        <p>On ne « prend » pas des lentilles comme on prend des lunettes : chaque œil est différent. L'adaptation suit des étapes précises.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Un examen de la cornée et une mesure de ses paramètres (courbure, diamètre, qualité des larmes).</li>
          <li><span class="check">✓</span> Le choix d'un premier modèle et un essai en conditions réelles.</li>
          <li><span class="check">✓</span> L'apprentissage de la pose, du retrait et de l'entretien.</li>
          <li><span class="check">✓</span> Un contrôle de la tolérance et de la vision avant de valider, puis un suivi régulier.</li>
        </ul>
        <p>Une première prescription de lentilles relève de l'ophtalmologiste ; nous assurons ensuite l'adaptation, l'apprentissage et le suivi dans la durée.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/lentilles-essai.jpg" alt="Adaptation et essai de lentilles de contact en boutique" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Aller plus loin</span>
      <h2>Trois choses à savoir sur les lentilles</h2>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <h3>L'orthokératologie</h3>
        <p>Des lentilles rigides portées la nuit remodèlent temporairement la cornée : on voit net toute la journée sans rien porter. Elle est notamment utilisée pour freiner la myopie de l'enfant, sous suivi médical.</p>
      </div>
      <div class="dark-card reveal">
        <h3>Presque toutes les vues</h3>
        <p>Contrairement à une idée reçue, presque toutes les corrections se portent aujourd'hui en lentilles, y compris l'astigmatisme (toriques) et la presbytie (multifocales). Un essai encadré permet de vérifier ce qui vous convient.</p>
      </div>
      <div class="dark-card reveal">
        <h3>Les règles d'or de l'hygiène</h3>
        <p>Mains lavées avant toute manipulation, durée de port respectée, jamais d'eau du robinet, étui et solution renouvelés, retrait immédiat en cas d'œil rouge ou douloureux. La plupart des complications viennent d'un défaut d'hygiène.</p>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="maladies">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/sante/depistage.jpg" alt="Dépistage à la lampe à fente lors d'un contrôle des yeux" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Maladies de l'œil</span>
        <h2>Le dépistage régulier, votre meilleure protection</h2>
        <p>Certaines pathologies évoluent silencieusement pendant des années : seul un contrôle régulier permet de les détecter tôt. Voici les trois plus fréquentes à connaître.</p>
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Cataracte</h3>
        <p>Opacification progressive du cristallin liée à l'âge, qui touche plus de 20 % des personnes après 65 ans. Vision qui se voile, éblouissements : une intervention chirurgicale permet de remplacer le cristallin et de retrouver une vision nette.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/></svg></div>
        <h3>DMLA</h3>
        <p>Première cause de malvoyance après 50 ans en France. La forme sèche évolue lentement sur plusieurs années ; la forme humide, plus rapide, se traite par injections. Lignes droites déformées ou tache centrale doivent alerter sans tarder.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg></div>
        <h3>Glaucome</h3>
        <p>Une pression intraoculaire trop élevée qui endommage le nerf optique, souvent sans aucun symptôme au début. Il touche 1 à 2 % des plus de 40 ans et environ 10 % des plus de 70 ans : le dépistage régulier est essentiel.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">D'autres atteintes</span>
      <h2>D'autres pathologies à connaître</h2>
      <p>Au-delà des trois plus fréquentes, quelques atteintes méritent d'être repérées tôt — parfois par de simples signes du quotidien.</p>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal" style="background:var(--cream-2);border:1px solid var(--line);">
        <h3 style="color:var(--charcoal);">Sécheresse oculaire</h3>
        <p style="color:var(--charcoal-soft);">Très fréquente, aggravée par les écrans, la climatisation et l'âge. Picotements, sensation de sable, yeux qui « pleurent » paradoxalement. Larmes artificielles et bons réflexes soulagent la majorité des cas.</p>
      </div>
      <div class="dark-card reveal" style="background:var(--cream-2);border:1px solid var(--line);">
        <h3 style="color:var(--charcoal);">Rétinopathie diabétique</h3>
        <p style="color:var(--charcoal-soft);">Le diabète peut abîmer les vaisseaux de la rétine, longtemps sans symptôme. Un examen du fond d'œil régulier est indispensable pour toute personne diabétique.</p>
      </div>
      <div class="dark-card reveal" style="background:var(--cream-2);border:1px solid var(--line);">
        <h3 style="color:var(--charcoal);">Kératocône</h3>
        <p style="color:var(--charcoal-soft);">Un amincissement de la cornée, qui se déforme en cône : la vision devient floue et déformée, souvent chez le jeune adulte. Il se corrige par des lentilles adaptées, parfois rigides ou sclérales.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Ne pas attendre</span>
        <h2>Les signes qui doivent vous alerter</h2>
        <p>Certains symptômes imposent un avis médical rapide, parfois en urgence. À connaître :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Une <strong>baisse de vision brutale</strong>, d'un œil ou des deux.</li>
          <li><span class="check">✓</span> Des <strong>éclairs lumineux</strong> ou une pluie de « mouches » soudaine (risque de décollement de rétine).</li>
          <li><span class="check">✓</span> Une <strong>tache fixe</strong> au centre de la vision ou des <strong>lignes droites déformées</strong>.</li>
          <li><span class="check">✓</span> Un <strong>œil rouge et douloureux</strong>, avec baisse de vue.</li>
          <li><span class="check">✓</span> Un <strong>voile</strong> ou un rétrécissement du champ de vision.</li>
        </ul>
        <p>Dans le doute, mieux vaut consulter pour rien que passer à côté : en ophtalmologie, le temps compte.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/signes-alerte.jpg" alt="Homme se frottant les yeux, gêne visuelle qui doit alerter" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="enfants">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/enfants/verres-enfant.jpg" alt="Lunettes d'enfant : monture souple et verres résistants" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Espace enfants</span>
        <h2>La vue des plus jeunes, notre priorité</h2>
        <p>Équiper un enfant demande des montures adaptées, des verres résistants et un vrai suivi. Nous avons rassemblé sur une page dédiée tout ce qu'il faut savoir : le choix de la monture, la gamme de verres, la protection contre la myopie et le 100 % Santé enfant.</p>
        <a href="/enfants.html" class="btn btn-primary" style="margin-top:8px;">Découvrir l'espace enfants</a>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="conseils">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Nos conseils</span>
        <h2>Les bons réflexes pour préserver votre vue</h2>
        <p>Fatigue oculaire, écrans, protection solaire, lentilles... quelques repères simples pour préserver le confort de vos yeux au quotidien.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/sante/reflexes-vue.jpg" alt="Modèle anatomique de l'œil en coupe" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <div class="faq-list">
      <details class="faq-item reveal">
        <summary>Comment limiter la fatigue oculaire liée aux écrans ?<span class="plus">+</span></summary>
        <p>Appliquez la règle des 20-20-20 : toutes les 20 minutes, faites une pause de 20 secondes en regardant un point situé à 20 mètres. Pensez aussi à cligner des yeux régulièrement et à régler la luminosité de vos écrans.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Comment bien choisir sa protection solaire pour les yeux ?<span class="plus">+</span></summary>
        <p>La teinte se choisit selon l'usage : brun ou jaune pour le contraste en conduite ou activité sportive, gris pour une vision naturelle des couleurs, vert pour un bon compromis. Les verres polarisants sont recommandés pour la conduite, l'eau ou la montagne, où les reflets sont importants.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quelles sont les bonnes pratiques d'hygiène avec des lentilles de contact ?<span class="plus">+</span></summary>
        <p>Lavez-vous toujours les mains avant manipulation, respectez la durée de port et de renouvellement indiquée, évitez le contact avec l'eau du robinet ou de la douche, et ne dormez jamais avec des lentilles non prévues pour un port prolongé, sauf avis contraire de votre praticien.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Comment choisir une monture adaptée à mon visage et à mon activité ?<span class="plus">+</span></summary>
        <p>La forme de la monture se choisit en fonction de la morphologie du visage, mais aussi de votre usage principal : une monture légère et enveloppante pour le sport, un maintien renforcé pour le vélo, la voile ou le ski. Notre équipe vous conseille en essayage.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Quels traitements choisir pour mes verres ?<span class="plus">+</span></summary>
        <p>Plusieurs options se combinent selon vos besoins : verres photochromiques qui s'assombrissent automatiquement à la lumière, filtre anti-lumière bleue pour le confort devant les écrans, ou verres polarisants pour réduire les reflets et l'éblouissement en extérieur.</p>
      </details>
      <details class="faq-item reveal">
        <summary>Que faire en cas d'yeux secs ou d'allergies oculaires ?<span class="plus">+</span></summary>
        <p>Les allergies saisonnières, notamment au pollen, touchent 20 à 25 % de la population française et provoquent rougeurs et démangeaisons. Des larmes artificielles et l'évitement des frottements soulagent les symptômes légers ; en cas de gêne persistante, un avis médical est recommandé.</p>
      </details>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur votre vue ?</h2>
    <p>Prenez rendez-vous en boutique, Centre commercial Grand Angle, pour un examen ou un conseil personnalisé.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 4 — marques.html
# ============================================================================
# NOTE: .brand-wordmark uses stylised typography (font/weight/case), not the
# brands' actual trademarked logo artwork — we don't have licensed access to
# official logo files. Swap in real logo images once Mikhael obtains them
# from each brand's dealer/press portal (just replace the wordmark div with
# an <img>).
BRANDS = [
    {
        "name": "Ray-Ban", "founded": "1937", "country": "États-Unis", "wm": "wm-stencil", "logo": "/logos/ray-ban.png",
        "story": "Fondée en 1937 aux États-Unis pour équiper les pilotes de l'armée américaine de verres anti-éblouissants, la maison invente cette même année l'Aviator, puis dessine en 1952 le Wayfarer — deux silhouettes devenues les plus copiées de l'histoire des lunettes.",
    },
    {
        "name": "Fendi", "founded": "1925", "country": "Italie", "wm": "wm-serif-caps", "logo": "/logos/fendi.png",
        "story": "Née à Rome en 1925 d'un atelier de maroquinerie fondé par Adele et Edoardo Fendi, la maison italienne a bâti sa réputation sur un savoir-faire d'exception en cuir et en fourrure, porté pendant plus de cinquante ans par Karl Lagerfeld. Ce même souci du détail se retrouve dans ses montures.",
    },
    {
        "name": "Fred", "founded": "1936", "country": "France", "wm": "wm-script", "logo": "/logos/fred.png",
        "story": "Fondée à Paris en 1936 par Fred Samuel, surnommé le « joaillier solaire », la maison doit sa renommée au bracelet Force 10, né en 1966 de l'univers du câble marin. Depuis 1988, cette signature se prolonge jusque dans ses montures, où le maillon torsadé devient motif.",
    },
    {
        "name": "Loewe", "founded": "1846", "country": "Espagne", "wm": "wm-thin-caps-a", "logo": "/logos/loewe.png",
        "story": "Fondée à Madrid en 1846 par le maître-cuirier Enrique Loewe Roessberg, Loewe compte parmi les plus anciennes maisons de cuir d'Europe. Une exigence artisanale que l'on retrouve dans chacune de ses montures, pensées comme de petits objets de maroquinerie.",
    },
    {
        "name": "Celine", "founded": "1945", "country": "France", "wm": "wm-thin-caps-b", "logo": "/logos/celine.png",
        "story": "Fondée à Paris en 1945 par Céline Vipiana, la maison a débuté par la chaussure sur-mesure avant de s'imposer dans la maroquinerie et le prêt-à-porter. Une élégance discrète, façon « quiet luxury », que l'on retrouve dans des montures aussi sobres qu'affirmées.",
    },
    {
        "name": "Marc Jacobs", "founded": "1986", "country": "États-Unis", "wm": "wm-lower-bold", "logo": "/logos/marc-jacobs.png",
        "story": "Lancée à New York au milieu des années 1980, la maison Marc Jacobs s'impose dès 1992 avec sa collection dite « grunge », qui bouscule les codes du prêt-à-porter américain. Un esprit pop et facétieux qui irrigue toute sa ligne de lunetterie.",
    },
    {
        "name": "Prada", "founded": "1913", "country": "Italie", "wm": "wm-geo-caps", "logo": "/logos/prada.png",
        "story": "Fondée à Milan en 1913 par Mario Prada comme maroquinier de luxe, la maison doit sa réinvention à sa petite-fille Miuccia Prada, qui lui insuffle dès les années 1980 un esthétisme minimaliste et intellectuel — une élégance épurée que l'on retrouve jusque dans ses montures.",
    },
    {
        "name": "Andy Brook", "founded": "2017", "country": "France", "wm": "wm-plain", "logo": "/logos/andy-brook.png",
        "story": "Fondée en France en 2017, Andy Brook est une jeune maison qui mise sur un savoir-faire artisanal et des matières premium, assemblées à la main. Une approche contemporaine et exigeante de la lunetterie, portée par une génération attachée au fabriqué avec soin.",
    },
    {
        "name": "CHIMI", "founded": "2016", "country": "Suède", "wm": "wm-lower-round", "logo": "/logos/chimi.png",
        "story": "Fondée à Stockholm en 2016 par Charlie Lindström et Daniel Djurdjevic, CHIMI incarne une lunetterie scandinave minimaliste et colorée, pensée pour s'accorder à tous les styles. Une fraîcheur nordique, entre simplicité des formes et générosité des teintes.",
    },
    {
        "name": "Miu Miu", "founded": "1993", "country": "Italie", "wm": "wm-italic", "logo": "/logos/miu-miu.png",
        "story": "Créée par Miuccia Prada au début des années 1990 comme la petite sœur facétieuse de Prada, Miu Miu cultive un esprit provocateur et ludique, entre audace et fraîcheur. Une lunetterie qui n'a pas peur de jouer avec les codes.",
    },
    {
        "name": "LOOL", "founded": "2016", "country": "Espagne", "wm": "wm-lower-wide", "logo": "/logos/lool.png",
        "story": "Fondée à Barcelone en 2016 par le designer Aris Rubio et l'entrepreneur Alex Carrasco, LOOL réinvente la monture en acier inoxydable, découpée au laser et assemblée sans une seule vis grâce à sa charnière brevetée. Une lunetterie ultralégère, à l'esthétique inspirée de l'architecture rétrofuturiste.",
    },
    {
        "name": "Ralph Lauren", "founded": "1967", "country": "États-Unis", "wm": "wm-classic-serif", "logo": "/logos/ralph-lauren.png",
        "story": "Fondée à New York en 1967 par Ralph Lauren, la maison a démocratisé dans le monde entier une élégance « preppy » si américaine, entre héritage universitaire et art de vivre. Ses montures perpétuent ce classicisme intemporel, chic et évident.",
    },
    {
        "name": "Armani", "founded": "1975", "country": "Italie", "wm": "wm-thin-wide", "logo": "/logos/armani.png",
        "story": "Fondée à Milan en 1975 par Giorgio Armani et Sergio Galeotti, la maison a révolutionné le vestiaire en déstructurant la veste pour une élégance plus fluide. Une sophistication discrète que l'on retrouve dans chacune de ses montures, entre rigueur et douceur des lignes.",
    },
    {
        "name": "Longchamp", "founded": "1948", "country": "France", "wm": "wm-elegant-caps", "logo": "/logos/longchamp.png",
        "story": "Fondée à Paris en 1948 par Jean Cassegrain, Longchamp débute dans la maroquinerie fine avant de devenir, en 1993, la maison du Pliage — ce sac pliable en toile et cuir devenu un classique mondial. Une élégance française pratique, transmise de génération en génération au sein de la famille Cassegrain.",
    },
    {
        "name": "Guess", "founded": "1981", "country": "États-Unis", "wm": "wm-bold-condensed", "logo": "/logos/guess.png",
        "story": "Fondée à Los Angeles en 1981 par les frères Marciano, Guess impose d'emblée un denim ajusté qui tranche avec les coupes amples de l'époque, puis des campagnes en noir et blanc devenues cultes. Un esprit américain affirmé, porté par son triangle devenu l'un des logos les plus reconnaissables de la mode.",
    },
    {
        "name": "Dior", "founded": "1946", "country": "France", "wm": "wm-classic-serif", "logo": "/logos/dior.png",
        "story": "Fondée à Paris en 1946 par Christian Dior, la maison bouleverse la mode dès 1947 avec le « New Look », qui redonne à la silhouette féminine sa taille marquée et ses jupes amples. Une élégance parisienne intemporelle, que l'on retrouve aujourd'hui jusque dans ses montures.",
    },
    {
        "name": "Gucci", "founded": "1921", "country": "Italie", "wm": "wm-elegant-caps", "logo": "/logos/gucci.png",
        "story": "Fondée à Florence en 1921 par Guccio Gucci comme sellerie de cuir fin, la maison italienne s'impose au fil du XXe siècle comme une référence du luxe, entre héritage équestre et esprit maximaliste. Une audace transalpine que l'on retrouve dans chacune de ses lunettes.",
    },
    {
        "name": "Saint Laurent", "founded": "1961", "country": "France", "wm": "wm-bold-condensed", "logo": "/logos/saint-laurent.png",
        "story": "Fondée à Paris en 1961 par Yves Saint Laurent et Pierre Bergé, la maison impose dès 1966 le smoking pour femme et la ligne Rive Gauche, pionnière du prêt-à-porter de luxe. Devenue Saint Laurent Paris en 2012 sous la direction d'Hedi Slimane, elle cultive une élégance rock et acérée qui se prolonge jusque dans ses montures.",
    },
    {
        "name": "Givenchy", "founded": "1952", "country": "France", "wm": "wm-wide-caps", "logo": "/logos/givenchy.png",
        "story": "Fondée à Paris en 1952 par Hubert de Givenchy, la maison se distingue très tôt par sa collaboration avec Audrey Hepburn, qu'il habille dès 1954. Une élégance épurée et raffinée, entre haute couture et modernité, qui irrigue toute sa ligne de lunetterie.",
    },
    {
        "name": "Burberry", "founded": "1856", "country": "Royaume-Uni", "wm": "wm-serif-caps", "logo": "/logos/burberry.png",
        "story": "Fondée en 1856 par Thomas Burberry, la maison britannique invente la gabardine et habille explorateurs et aviateurs avant de devenir une référence du luxe anglais. Son esprit héritage et son fameux tartan se prolongent dans une lunetterie à la fois classique et affirmée.",
    },
    {
        "name": "Police", "founded": "1983", "country": "Italie", "wm": "wm-bold-condensed", "logo": "/logos/police.png",
        "story": "Née en 1983 en Italie, Police s'est imposée avec ses solaires au caractère affirmé, portées par de nombreuses figures de la mode et du sport. Une esthétique urbaine, reconnaissable à ses lignes nettes et ses détails métalliques.",
    },
    {
        "name": "French Retro", "country": "France", "wm": "wm-serif-caps", "logo": "/logos/french-retro.png",
        "story": "Marque française au nom sans détour, French Retro revisite les formes vintage — pantos, rondes, clubmaster — dans des acétates soignés et à des prix accessibles. Une jolie porte d'entrée vers un style rétro assumé.",
    },
    {
        "name": "Osmose", "founded": "2009", "wm": "wm-wide-caps", "logo": "/logos/osmose.png",
        "story": "Distribuée par Octika, Osmose vise un rapport qualité-prix particulièrement soigné : de belles matières (Ultem, TR90, titane, acétate) à des tarifs économiques. Sa signature, le système Polar Clip à aimants invisibles, permet de passer d'un geste de la vue au solaire polarisé — ou à un clip jaune pour la conduite de nuit.",
    },
    {
        "name": "Playmobil", "country": "Allemagne", "wm": "wm-bold-condensed", "logo": "/logos/playmobil.png",
        "story": "Sous licence de la célèbre marque de jouets allemande, la collection de lunettes Playmobil est pensée pour les enfants : matières souples, coloris vifs et montures robustes qui résistent à la vie d'un enfant. De quoi rendre la première paire amusante plutôt que contraignante.",
    },
    {
        "name": "Sonic", "wm": "wm-stencil", "logo": "/logos/sonic.png",
        "story": "La collection junior Sonic habille les plus jeunes de montures colorées et dynamiques, conçues pour être légères, solides et faciles à porter au quotidien. Un choix ludique pour accompagner les enfants qui découvrent leurs premières lunettes.",
    },
    {
        "name": "Tom Ford", "founded": "2005", "country": "États-Unis", "wm": "wm-wide-caps", "logo": "/logos/tom-ford.png",
        "story": "Fondée en 2005 par le créateur américain Tom Ford, ancien directeur artistique de Gucci et d'Yves Saint Laurent, la maison incarne un luxe glamour et assumé. Ses lunettes, reconnaissables à leur plaquette en T dorée, sont devenues une signature à part entière.",
    },
    {
        "name": "ELEYE", "wm": "wm-wide-caps", "logo": "/logos/eleye.png",
        "story": "Marque créateur du groupe DANILS — qui distribue aussi French Retro — ELEYE mise sur une légèreté extrême grâce au titane japonais, à la fois ultra-léger, résistant et hypoallergénique. Sous la signature « Zero Gravity Eyecraft », ses montures fines et minimalistes se font oublier sur le nez : un vrai travail d'ingénierie autant que de style.",
    },
]


# Rotating accent palette for brand cards — cycles through the site's
# existing colour tokens so the grid feels varied rather than monochrome,
# without introducing any new colours to the design system.
BRAND_ACCENTS = [
    ("#B23A2E", "rgba(178,58,46,0.10)"),
    ("#3E7D5A", "rgba(62,125,90,0.10)"),
    ("#C2568A", "rgba(194,86,138,0.10)"),
    ("#C08A1E", "rgba(192,138,30,0.12)"),
    ("#2F6DA3", "rgba(47,109,163,0.10)"),
    ("#2E8B84", "rgba(46,139,132,0.10)"),
    ("#7A5AA6", "rgba(122,90,166,0.10)"),
]

COUNTRY_FLAGS = {
    "France": "🇫🇷",
    "Italie": "🇮🇹",
    "États-Unis": "🇺🇸",
    "Espagne": "🇪🇸",
    "Suède": "🇸🇪",
    "Royaume-Uni": "🇬🇧",
    "Allemagne": "🇩🇪",
}


# Familles éditoriales — la page Nos Marques est structurée en sections H2
# plutôt qu'en une grille unique de 19 cartes sous le H1. Chaque marque
# n'appartient qu'à une seule famille (total = len(BRANDS)).
BRAND_FAMILIES = [
    {
        "id": "maisons-de-couture",
        "eyebrow": "Haute couture",
        "title": "Les maisons de couture",
        "intro": (
            "Ce sont les noms que tout le monde connaît, et ce sont aussi ceux sur lesquels on se trompe le "
            "plus souvent : une monture signée par une grande maison n'est pas une monture « de luxe » "
            "interchangeable, c'est le prolongement d'un vocabulaire de formes construit sur plusieurs décennies. "
            "Chez Dior ou Celine, la ligne reste sobre et le geste précis ; chez Gucci, Fendi ou Miu Miu, elle "
            "s'autorise la couleur, le volume et le motif. Nous vous aidons à trouver, à l'intérieur de cette "
            "famille, celle dont l'écriture correspond réellement à votre visage et à votre manière de vous habiller — "
            "et non simplement le logo le plus visible."
        ),
        "names": ["Dior", "Celine", "Givenchy", "Saint Laurent", "Fendi", "Prada", "Tom Ford", "Burberry", "Miu Miu", "Gucci", "Armani", "Loewe"],
    },
    {
        "id": "intemporels",
        "eyebrow": "Classiques",
        "title": "Les intemporels et l'esprit américain",
        "intro": (
            "Une paire que l'on garde dix ans ne se choisit pas comme une paire de saison. Ces maisons ont en "
            "commun d'avoir créé des silhouettes qui n'ont jamais quitté le paysage — l'Aviator et la Wayfarer de "
            "Ray-Ban, la ligne universitaire de Ralph Lauren — et de proposer des montures dont les formes "
            "restent lisibles quelle que soit l'année. C'est la famille vers laquelle nous orientons souvent une "
            "première paire de solaires, ou une monture de vue destinée à être portée tous les jours au bureau : "
            "le risque de s'en lasser est faible, et les pièces détachées restent disponibles longtemps."
        ),
        "names": ["Ray-Ban", "Ralph Lauren", "Police", "Marc Jacobs", "Guess"],
    },
    {
        "id": "savoir-faire-francais",
        "eyebrow": "Savoir-faire français",
        "title": "La maroquinerie et la joaillerie françaises",
        "intro": (
            "Deux maisons parisiennes venues d'un autre métier — le bracelet pour Fred, le sac pour Longchamp — "
            "et qui ont transposé leur savoir-faire dans la lunetterie sans en changer les codes. On y retrouve "
            "des détails que l'on remarque à l'usage plus qu'en vitrine : un maillon repris sur la branche, une "
            "épaisseur de métal juste, une charnière qui ne prend pas de jeu. C'est une famille que nous "
            "recommandons volontiers à qui cherche une monture discrète mais signée, sans logo apparent."
        ),
        "names": ["Fred", "Longchamp"],
    },
    {
        "id": "createurs-independants",
        "eyebrow": "Indépendants",
        "title": "Les créateurs indépendants",
        "intro": (
            "C'est la partie de la sélection dont nous sommes le plus fiers, parce qu'elle ne se trouve pas partout. "
            "Ces trois maisons ne dépendent d'aucun grand groupe : elles fabriquent en petites séries et "
            "concentrent leur travail sur la construction de la monture plutôt que sur la notoriété du nom. LOOL "
            "assemble ses montures en acier découpé au laser, sans une seule vis ; CHIMI travaille des acétates "
            "colorés dans une grammaire scandinave épurée ; Andy Brook mise sur l'assemblage à la main et des "
            "matières haut de gamme. Si vous cherchez une paire que personne d'autre ne portera dans votre "
            "immeuble, commencez par celles-là."
        ),
        "names": ["LOOL", "CHIMI", "Andy Brook", "ELEYE"],
    },
    {
        "id": "style-francais-accessible",
        "eyebrow": "Accessible",
        "title": "Le style, à prix doux",
        "intro": (
            "Deux collections qui prouvent qu'une belle monture n'est pas forcément une monture chère. "
            "French Retro revisite les formes vintage — pantos, rondes, clubmaster ; Osmose, distribuée par Octika, "
            "mise sur de belles matières (Ultem, TR90, titane) et un système de clip solaire aimanté bien pensé. "
            "Le tout à des prix doux : du style pour tous les budgets, c'est au cœur de notre idée du métier."
        ),
        "names": ["French Retro", "Osmose"],
    },
    {
        "id": "enfants",
        "eyebrow": "Enfants & juniors",
        "title": "Les lunettes des plus jeunes",
        "intro": (
            "Équiper un enfant demande des montures pensées pour lui : souples, résistantes, ludiques. Sous licence, "
            "Playmobil et Sonic transforment la paire de lunettes en objet que l'enfant a envie de porter — la première "
            "condition pour qu'il la garde sur le nez. Pour tout savoir sur le choix des montures, des verres et la "
            "protection de la vue des enfants, découvrez notre page dédiée aux enfants."
        ),
        "names": ["Playmobil", "Sonic"],
    },
]


def brands_by_name(names):
    """Retourne les dicts BRANDS correspondant à une liste de noms, dans l'ordre donné."""
    index = {b["name"]: b for b in BRANDS}
    missing = [n for n in names if n not in index]
    if missing:
        raise ValueError("Marque inconnue dans BRAND_FAMILIES : %s" % ", ".join(missing))
    return [index[n] for n in names]


def render_brand_families():
    """Rend les 4 sections H2 de la page Nos Marques."""
    covered = [n for fam in BRAND_FAMILIES for n in fam["names"]]
    if sorted(covered) != sorted(b["name"] for b in BRANDS):
        raise ValueError(
            "BRAND_FAMILIES ne couvre pas exactement BRANDS "
            "(%d classées / %d marques)" % (len(covered), len(BRANDS))
        )
    out, offset = [], 0
    for fam in BRAND_FAMILIES:
        subset = brands_by_name(fam["names"])
        out.append(
            '<section class="marques brand-family" id="{id}">\n'
            '  <div class="container">\n'
            '    <div class="section-head">\n'
            '      <span class="eyebrow">{eyebrow}</span>\n'
            '      <h2>{title}</h2>\n'
            '      <p class="family-intro">{intro}</p>\n'
            '    </div>\n'
            '    <div class="brand-grid">\n'
            '{cards}\n'
            '    </div>\n'
            '  </div>\n'
            '</section>'.format(cards=render_brand_cards(subset, offset=offset), **fam)
        )
        offset += len(subset)
    return "\n\n".join(out)


def render_brand_cards(brands, offset=0):
    cards = []
    for j, b in enumerate(brands):
        i = j + offset
        slug = b["name"].lower().replace(" ", "-")
        accent, accent_bg = BRAND_ACCENTS[i % len(BRAND_ACCENTS)]
        _founded = b.get("founded", "")
        _country = b.get("country", "")
        flag = COUNTRY_FLAGS.get(_country, "")
        if _founded and _country:
            meta = "%s Fondée en %s · %s" % (flag, _founded, _country)
        elif _country:
            meta = "%s %s" % (flag, _country)
        elif _founded:
            meta = "Depuis %s" % _founded
        else:
            meta = ""
        if b.get("logo"):
            mark = '<img class="brand-logo" src="{logo}" alt="Logo {name}" loading="lazy">'.format(**b)
        else:
            mark = '<div class="brand-wordmark {wm}">{name}</div>'.format(**b)
        cards.append(
            '      <div class="brand-card reveal" id="{slug}" style="--accent:{accent};--accent-bg:{accent_bg};">\n'
            '        <div class="brand-card-body">\n'
            '          <div class="brand-logo-plate">{mark}</div>\n'
            '          <div class="brand-meta">{meta}</div>\n'
            '        </div>\n'
            '        <p>{story}</p>\n'
            '      </div>'.format(
                slug=slug, mark=mark, accent=accent, accent_bg=accent_bg, flag=flag, meta=meta, **b
            )
        )
    return "\n".join(cards)


def render_brand_stats(brands):
    n_brands = len(brands)
    n_countries = len({b.get("country","") for b in brands if b.get("country")})
    oldest_year = min((int(b["founded"]) for b in brands if b.get("founded")), default=1937)
    return (
        '    <div class="brand-stats">\n'
        '      <div class="brand-stat"><strong>{n_brands}</strong><span>Marques</span></div>\n'
        '      <div class="brand-stat"><strong>{n_countries}</strong><span>Pays représentés</span></div>\n'
        '      <div class="brand-stat"><strong>{oldest_year}</strong><span>Maison la plus ancienne</span></div>\n'
        '    </div>'
    ).format(n_brands=n_brands, n_countries=n_countries, oldest_year=oldest_year)


def render_brand_pills(brands):
    pills = [f'      <a href="/marques.html#{b["name"].lower().replace(" ", "-")}" class="brand-pill">{b["name"]}</a>' for b in brands]
    return "\n".join(pills)


MARQUEE_PHOTO_COUNT = 15

# Display order: interleaved round-robin across the different people/styles in the
# photo set (rather than upload order) so the strip reads as a mixed, varied cast
# from the very first frame instead of clustering similar photos together.
MARQUEE_ORDER = [
    1, 2, 3,
    6, 4, 5,
    10, 7, 8,
    11, 9, 12,
    14, 13, 15,
]


def render_marquee_track():
    imgs = [
        '<img src="/images/marquee/marquee-{:02d}.jpg" alt="" loading="{}">'.format(
            i, "eager" if pos < 4 else "lazy"
        )
        for pos, i in enumerate(MARQUEE_ORDER)
    ]
    # duplicate the full set once so the track can loop seamlessly via translateX(-50%)
    all_imgs = imgs + imgs
    return "\n".join("      " + tag for tag in all_imgs)


BODY_MARQUES = """
<section class="page-hero hero-marquee">
  <div class="hero-marquee-track" aria-hidden="true">
""" + render_marquee_track() + """
  </div>
  <div class="hero-marquee-overlay"></div>
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Nos Marques</div>
    <span class="eyebrow">Sélection</span>
    <h1>Nos marques</h1>
    <p>De Ray-Ban à Loewe, en passant par Prada ou CHIMI : un choix de maisons reconnues, chacune avec sa propre histoire, sélectionnées pour leur qualité et leur fiabilité.</p>
  </div>
</section>

<style>
  .brand-family{padding-top:34px;padding-bottom:34px;}
  .brand-family + .brand-family{border-top:1px solid rgba(0,0,0,.06);}
  .brand-family .section-head{max-width:760px;margin-bottom:26px;}
  .brand-family .family-intro{margin-top:10px;}
  .marques-intro .section-head{max-width:760px;margin:0 auto;}
  .family-nav{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px;}
  .family-nav a{font-size:.86rem;letter-spacing:.02em;padding:8px 16px;border:1px solid rgba(0,0,0,.14);border-radius:999px;text-decoration:none;color:inherit;transition:background .2s,border-color .2s;}
  .family-nav a:hover{background:rgba(193,101,59,.08);border-color:var(--terracotta);}
</style>

<section class="marques marques-intro">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Un choix exigeant</span>
      <h2>Vingt-sept marques, choisies une par une</h2>
      <p>Nous ne référençons pas un catalogue : nous choisissons. Chaque maison présente dans notre boutique de Montreuil a été retenue pour trois raisons concrètes — une fabrication dont nous connaissons l'origine, un service après-vente qui répond réellement quand une branche casse ou qu'une charnière prend du jeu, et une gamme de formes assez large pour habiller des visages différents. C'est ce qui explique que vous ne trouviez pas ici certaines marques très diffusées : elles ne cochaient pas les trois cases.</p>
      <p>Pour vous y retrouver, la sélection est présentée en quatre familles. Elles ne correspondent pas à des gammes de prix mais à des manières de dessiner une monture — et c'est souvent ce critère-là, plus que le budget, qui fait qu'une paire vous va ou ne vous va pas.</p>
""" + render_brand_stats(BRANDS) + """
      <nav class="family-nav" aria-label="Familles de marques">
        <a href="#maisons-de-couture">Maisons de couture</a>
        <a href="#intemporels">Intemporels</a>
        <a href="#savoir-faire-francais">Savoir-faire français</a>
        <a href="#createurs-independants">Créateurs indépendants</a>
        <a href="#style-francais-accessible">Accessible</a>
        <a href="#enfants">Enfants &amp; juniors</a>
      </nav>
    </div>
  </div>
</section>

""" + render_brand_families() + """

<section class="split alt">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">En boutique</span>
        <h2>Le plus simple : venir les essayer</h2>
        <p>Photos et fiches produits ne remplacent jamais l'essayage. Une monture qui paraît parfaite à l'écran peut appuyer sur le nez, glisser dès que vous baissez la tête, ou couper le regard parce que la hauteur du cercle ne correspond pas à votre visage. Ces trois points ne se voient sur aucune photo.</p>
        <p>En boutique, nous regardons d'abord votre écart pupillaire, la hauteur de vos yeux dans la monture et la façon dont elle se pose sur votre nez et vos oreilles — puis seulement le style. C'est aussi le moment où votre correction entre en jeu : une forte myopie supporte mal les grands cercles, une progression a besoin d'une certaine hauteur de verre. Nous vous le disons avant l'achat, pas après.</p>
        <p>Comptez une vingtaine de minutes pour un essayage tranquille, sans rendez-vous, dans notre boutique du centre commercial Grand Angle, à Montreuil. Si une référence précise vous intéresse, appelez-nous avant de venir : nous vérifions qu'elle est bien en boutique dans votre coloris.</p>
        <a href="/contact.html" class="btn btn-outline" style="margin-top:6px;">Nous rendre visite</a>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/marques/essayage.jpg" alt="Client portant des solaires tendance, essayage de montures" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une marque en particulier vous intéresse ?</h2>
    <p>Contactez-nous, nous vous confirmerons sa disponibilité en boutique.</p>
    <a href="/contact.html" class="btn btn-primary">Nous contacter</a>
  </div>
</section>
"""


# ============================================================================
# PAGE 5 — espace-audition.html
# ============================================================================


# ============================================================================
# PAGE 6 — contact.html
# ============================================================================
BODY_CONTACT = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Contact</div>
    <span class="eyebrow">Venez nous rencontrer</span>
    <h1>Contact</h1>
    <p>Nous serions ravis de vous accueillir en boutique, Centre commercial Grand Angle.</p>
  </div>
</section>

<section class="contact">
  <div class="container">
    <div class="contact-grid">
      <div class="contact-info-card reveal">
        <h3>ACTU EYES</h3>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>
          <div><strong>Adresse</strong><span>15 Rue des Lumières, 93100 Montreuil<br>Centre commercial Grand Angle</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>
          <div><strong>Téléphone</strong><a href="tel:0148575740">01 48 57 57 40</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z" opacity="0"/><path d="M22 6l-10 7L2 6"/><rect x="2" y="4" width="20" height="16" rx="2"/></svg></div>
          <div><strong>Email</strong><a href="mailto:actueyes.montreuil@gmail.com">actueyes.montreuil@gmail.com</a></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div><strong>Horaires</strong><span>Lundi – Samedi, 10h00 – 19h30<br>Fermé le dimanche</span></div>
        </div>
        <div class="info-row">
          <div class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
          <div><strong>Accès</strong><span>Métro Mairie de Montreuil (ligne 9)</span></div>
        </div>
        <div class="social-row">
          <a href="https://www.instagram.com/actueyes.montreuil/" target="_blank" rel="noopener" aria-label="Instagram">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>
          </a>
        </div>
      </div>
      <div class="map-frame reveal">
        <iframe src="https://www.google.com/maps?q=15+rue+des+Lumieres+93100+Montreuil&output=embed" loading="lazy" allowfullscreen title="ACTU EYES sur Google Maps — 15 rue des Lumières, Montreuil"></iframe>
      </div>
    </div>
  </div>
</section>

<style>
  .contact-prose{padding-top:10px;}
  .contact-prose .section-head{max-width:760px;}
  .contact-prose .split-text p + p{margin-top:14px;}
  .hours-table{width:100%;max-width:420px;border-collapse:collapse;margin-top:18px;}
  .hours-table th,.hours-table td{text-align:left;padding:9px 0;border-bottom:1px solid rgba(0,0,0,.07);font-size:.95rem;font-weight:400;}
  .hours-table td{text-align:right;}
  .hours-table tr.closed th,.hours-table tr.closed td{opacity:.55;}
</style>

<section class="split contact-prose story-block">
  <div class="container">
    <div class="split-grid">
      <div class="split-text reveal">
        <span class="eyebrow">Y venir</span>
        <h2>Comment nous trouver</h2>
        <p>ACTU EYES se trouve au 15 rue des Lumières, au centre commercial Grand Angle, dans le quartier Cœur de Ville, face à la mairie de Montreuil. Le centre est à ciel ouvert : on rejoint la boutique aussi bien depuis la rue que depuis les places de la galerie.</p>
        <p>Le plus simple est le métro ligne 9, station Mairie de Montreuil, à quelques minutes à pied. Plusieurs lignes de bus desservent également la mairie, et le marché comme le cinéma Le Méliès sont juste à côté.</p>
        <p>En voiture, le stationnement de surface du quartier est payant et souvent saturé en fin de journée ; le parking du centre Grand Angle reste la solution la plus simple si vous venez le samedi. La galerie et la boutique sont de plain-pied, sans marche à franchir.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Quand venir</span>
        <h2>Nos horaires</h2>
        <p>Nous sommes ouverts du lundi au samedi, sans interruption entre midi et deux — vous pouvez donc passer sur votre pause déjeuner sans crainte de trouver porte close.</p>
        <table class="hours-table">
          <tr><th scope="row">Lundi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Mardi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Mercredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Jeudi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Vendredi</th><td>10h00 – 19h30</td></tr>
          <tr><th scope="row">Samedi</th><td>10h00 – 19h30</td></tr>
          <tr class="closed"><th scope="row">Dimanche</th><td>Fermé</td></tr>
        </table>
        <p>Le samedi après-midi est de loin le moment le plus fréquenté. Si vous souhaitez prendre votre temps pour essayer plusieurs montures ou passer un examen de vue, privilégiez plutôt le milieu de semaine ou la matinée.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt contact-prose story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Sans rendez-vous</span>
        <h2>Faut-il prendre rendez-vous ?</h2>
        <p>Dans la grande majorité des cas, non. Vous pouvez pousser la porte quand vous voulez pendant nos horaires d'ouverture pour essayer des montures, faire ajuster une paire, remplacer des plaquettes, resserrer une charnière, commander des lentilles ou simplement poser une question. Ces gestes-là ne se planifient pas, et nous les faisons volontiers, y compris si vos lunettes n'ont pas été achetées chez nous.</p>
        <p>Un rendez-vous devient utile dès qu'il faut du temps et du calme. C'est le cas pour un <a href="/espace-sante.html">examen de vue</a>, qui demande une vingtaine de minutes dans l'espace dédié. Un simple appel au <a href="tel:0148575740">01 48 57 57 40</a> suffit pour caler un créneau, souvent dans la même semaine.</p>
        <p>Enfin, si vous cherchez une référence précise, appelez-nous avant de vous déplacer : nous vérifions en direct qu'elle est bien en boutique dans le coloris et la taille qui vous intéressent, plutôt que de vous faire faire le trajet pour rien.</p>
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Sur place</span>
        <h2>Ce qui se passe une fois chez nous</h2>
        <p>Nous ne travaillons pas à la chaîne. Vous êtes reçu par la personne qui vous suivra ensuite, et l'échange commence toujours par vos usages plutôt que par le catalogue : ce que vous faites de vos journées, ce qui vous gêne aujourd'hui, ce que vous portiez avant et pourquoi cela ne vous convenait plus.</p>
        <p>Pour gagner du temps, vous pouvez apporter votre ordonnance si vous en avez une, votre ancienne paire — elle nous renseigne beaucoup, même hors d'usage —, votre carte Vitale et les coordonnées de votre mutuelle. Rien de tout cela n'est obligatoire pour une première visite : nous savons aussi commencer sans.</p>
        <p>Et si vous repartez sans rien acheter, ce n'est pas un problème. Un devis vous est remis systématiquement, il n'engage à rien, et il vous permet de comparer sereinement ou de le transmettre à votre mutuelle avant de décider.</p>
      </div>
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question avant de venir ?</h2>
    <p>Appelez-nous au 01 48 57 57 40 ou écrivez-nous : nous répondons rapidement, et souvent la réponse évite un déplacement.</p>
    <a href="tel:0148575740" class="btn btn-primary">01 48 57 57 40</a>
  </div>
</section>
"""


# ============================================================================
# JSON-LD (main entity, homepage only, to avoid duplicate structured data)
# ============================================================================
OPTICIAN_JSONLD = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Optician",
  "name": "ACTU EYES",
  "description": "Opticien à Montreuil (93). Lunettes de vue et de soleil, lentilles de contact et examen de vue en magasin.",
  "url": "https://actueyes-montreuil.fr/",
  "telephone": "+33148575740",
  "email": "actueyes.montreuil@gmail.com",
  "priceRange": "€€",
  "image": "https://actueyes-montreuil.fr/og-image.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "15 rue des Lumières, Centre commercial Grand Angle",
    "addressLocality": "Montreuil",
    "postalCode": "93100",
    "addressCountry": "FR"
  },
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
    "opens": "10:00",
    "closes": "19:30"
  },
  "sameAs": [
    "https://www.instagram.com/actueyes.montreuil/"
  ],
  "hasMap": "https://www.google.com/maps/search/?api=1&query=ACTU+EYES+Montreuil"
}
</script>"""


def faq_jsonld(items):
    """OBSOLETE — NE PLUS APPELER. Conserve pour memoire uniquement.

    Google a annonce le 08/05/2026 la fin des resultats enrichis FAQ et retire
    la documentation FAQPage le 15/06/2026. Le balisage ne produit plus aucun
    affichage. Les deux seuls appels (espace-sante, espace-audition) ont ete
    supprimes le 01/08/2026. Les FAQ restent visibles en clair dans les pages,
    ce qui suffit aux moteurs de reponse. Ne pas reintroduire ces appels.

    items: list of (question, answer_plain_text) tuples -> FAQPage JSON-LD block.
    Mirrors the visible <details>/<summary> FAQ accordions word-for-word, so the
    structured data always matches what's on the page (required by Google's
    guidelines for FAQ rich results / AI Overviews eligibility)."""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def breadcrumb_jsonld(crumbs):
    """crumbs: list of (name, url_or_None) tuples, in display order."""
    items = []
    for i, (name, url) in enumerate(crumbs):
        entry = {"@type": "ListItem", "position": i + 1, "name": name}
        if url:
            entry["item"] = url
        items.append(entry)
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


# FAQ text below is copy-pasted verbatim from the visible <details>/<summary>
# accordions in BODY_SANTE and BODY_AUDITION (see further down this file) so
# the structured data never drifts from what visitors actually read.
FAQ_SANTE_ITEMS = [
    ("Comment limiter la fatigue oculaire liée aux écrans ?",
     "Appliquez la règle des 20-20-20 : toutes les 20 minutes, faites une pause de 20 secondes en regardant un point situé à 20 mètres. Pensez aussi à cligner des yeux régulièrement et à régler la luminosité de vos écrans."),
    ("Comment bien choisir sa protection solaire pour les yeux ?",
     "La teinte se choisit selon l'usage : brun ou jaune pour le contraste en conduite ou activité sportive, gris pour une vision naturelle des couleurs, vert pour un bon compromis. Les verres polarisants sont recommandés pour la conduite, l'eau ou la montagne, où les reflets sont importants."),
    ("Quelles sont les bonnes pratiques d'hygiène avec des lentilles de contact ?",
     "Lavez-vous toujours les mains avant manipulation, respectez la durée de port et de renouvellement indiquée, évitez le contact avec l'eau du robinet ou de la douche, et ne dormez jamais avec des lentilles non prévues pour un port prolongé, sauf avis contraire de votre praticien."),
    ("Comment choisir une monture adaptée à mon visage et à mon activité ?",
     "La forme de la monture se choisit en fonction de la morphologie du visage, mais aussi de votre usage principal : une monture légère et enveloppante pour le sport, un maintien renforcé pour le vélo, la voile ou le ski. Notre équipe vous conseille en essayage."),
    ("Quels traitements choisir pour mes verres ?",
     "Plusieurs options se combinent selon vos besoins : verres photochromiques qui s'assombrissent automatiquement à la lumière, filtre anti-lumière bleue pour le confort devant les écrans, ou verres polarisants pour réduire les reflets et l'éblouissement en extérieur."),
    ("Que faire en cas d'yeux secs ou d'allergies oculaires ?",
     "Les allergies saisonnières, notamment au pollen, touchent 20 à 25 % de la population française et provoquent rougeurs et démangeaisons. Des larmes artificielles et l'évitement des frottements soulagent les symptômes légers ; en cas de gêne persistante, un avis médical est recommandé."),
]



# ============================================================================
# PAGE 7 — nos-conseils.html (services + guide d'achat + entretien + style)
# Nouvel onglet créé le 24/07/2026, à la place de "La Boutique" dans la nav
# (dont le contenu devient la page d'accueil) — voir décision client.
# Le 24/07/2026 (même jour, précision du client), la page d'accueil a été
# recentrée sur l'histoire pure (fondateurs + quartier) : la section
# "Nos services" (Optique/Solaire/Lentilles/Audition + garanties légales),
# qui s'y trouvait, a donc été déplacée ici, en tête de page.
# Toujours le 24/07/2026 (nouvelle demande le même jour), le client a
# souhaité un vrai guide d'achat, ajouté ici entre "Nos services" et
# "Entretien" : lecture d'ordonnance, choix de monture (fusionné avec
# l'ancien tableau "forme du visage"), types de verres selon la correction,
# traitements de verres, indices d'amincissement, lunettes vs lentilles,
# et quand changer ses lunettes. Faits recherchés sur le web (atol.fr,
# optic2000.com, direct-optic.fr, opticiensparconviction.fr, etc.) et
# reformulés avec les mots de Claude, jamais copiés verbatim. Le reste du
# contenu (entretien courant + style) reste volontairement distinct des
# FAQ déjà présentes dans Espace Santé et Espace Audition (pas de rappels
# médicaux ici).
# ============================================================================
BODY_CONSEILS = """
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Nos Conseils</div>
    <span class="eyebrow">Au quotidien</span>
    <h1>Nos conseils</h1>
    <p>Comment choisir votre monture, vos verres, leurs traitements et leur amincissement, lunettes ou lentilles, et nos conseils pour bien entretenir et accorder vos lunettes au quotidien.</p>
  </div>
</section>

<section class="split story-block" id="lire-ordonnance">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/lire-ordonnance.jpg" alt="Verres correcteurs, repère pour lire une ordonnance">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Comprendre sa prescription</span>
        <h2>Comment lire son ordonnance</h2>
        <p>Une ordonnance ophtalmologique peut sembler cryptée au premier regard. Voici comment déchiffrer les principales mentions :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> <strong>OD / OG</strong> — œil droit et œil gauche : chaque œil a sa propre ligne de correction, la vision différant souvent de l'un à l'autre</li>
          <li><span class="check">✓</span> <strong>Sphère</strong> — la puissance de correction en dioptries : un signe négatif corrige la myopie, un signe positif l'hypermétropie</li>
          <li><span class="check">✓</span> <strong>Cylindre et axe</strong> — présents en cas d'astigmatisme, ils précisent l'irrégularité de la cornée et son orientation, de 0° à 180°</li>
          <li><span class="check">✓</span> <strong>Addition</strong> — la puissance supplémentaire pour la vision de près, à partir de la presbytie (généralement après 40-45 ans)</li>
          <li><span class="check">✓</span> <strong>Écart pupillaire</strong> — la distance entre vos pupilles, indispensable pour bien centrer les verres dans la monture</li>
        </ul>
        <p>Une ordonnance reste valable 5 ans entre 16 et 42 ans, 3 ans au-delà de 42 ans, et 1 an pour les moins de 16 ans. En cas de doute sur une mention, notre équipe se fait un plaisir de vous l'expliquer en boutique.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="type-verres">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Vos verres</span>
        <h2>Quel type de verres selon votre correction</h2>
        <p>Le choix du verre dépend avant tout de votre correction et de vos besoins au quotidien — notre équipe vous oriente vers la meilleure option lors de votre examen.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/type-verres.jpg" alt="Sélection de verres correcteurs" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="services alt">
  <div class="container">
    <div class="device-grid">
      <div class="device-card reveal">
        <h3>Verres unifocaux</h3>
        <p>Une seule correction sur toute la surface du verre : concave et plus fin au centre pour la myopie, convexe et plus épais au centre pour l'hypermétropie, ou adapté à la courbure de votre cornée pour l'astigmatisme.</p>
        <span class="suited">Myopie, hypermétropie, astigmatisme</span>
      </div>
      <div class="device-card reveal">
        <h3>Verres progressifs</h3>
        <p>Trois zones de vision réunies sur un même verre — loin en haut, intermédiaire au centre, près en bas — pour voir net à toutes les distances sans changer de lunettes.</p>
        <span class="suited">Presbytie</span>
      </div>
      <div class="device-card reveal">
        <h3>Verres de proximité</h3>
        <p>Une large zone dédiée à la vision de près et intermédiaire, pensée pour le travail sur écran ou les métiers de précision plutôt que pour la vision de loin.</p>
        <span class="suited">Jeunes presbytes, métiers de précision</span>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="traitements-verres">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/traitements-verres.jpg" alt="Traitements et finitions de verres correcteurs" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Vos traitements</span>
        <h2>Quels traitements pour vos verres</h2>
        <p>Au-delà de la correction, plusieurs traitements peuvent être associés à vos verres selon votre mode de vie et vos habitudes.</p>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="services-grid grid-3">
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.4 7.2H22l-6 4.6L18.4 22 12 17.4 5.6 22 8 13.8l-6-4.6h7.6z"/></svg></div>
        <h3>Durcissement anti-rayure</h3>
        <p>Un vernis protecteur qui prolonge la durée de vie du verre et prépare la surface à recevoir les autres traitements.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg></div>
        <h3>Anti-reflet</h3>
        <p>Supprime les reflets et l'effet miroir sur le verre pour une meilleure transparence — particulièrement utile la nuit, en conduite et devant les écrans.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/></svg></div>
        <h3>Anti-salissure</h3>
        <p>Rend la surface du verre plus lisse pour repousser l'eau, la poussière et les traces de doigts, et facilite le nettoyage au quotidien.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg></div>
        <h3>Filtre lumière bleue</h3>
        <p>Atténue une partie de la lumière bleu-violet émise par les écrans, pour limiter la fatigue visuelle en cas d'usage prolongé.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg></div>
        <h3>Photochromique</h3>
        <p>Le verre s'assombrit automatiquement à la lumière du jour et redevient clair en intérieur, avec une protection UV permanente.</p>
      </div>
      <div class="service-card reveal">
        <div class="service-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg></div>
        <h3>Polarisant</h3>
        <p>Filtre les reflets éblouissants sur l'eau, la neige ou la route, pour un meilleur contraste — idéal en conduite et en extérieur.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="amincissement">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Vos verres, plus fins</span>
        <h2>Quel amincissement selon votre correction</h2>
        <p>Plus l'indice de votre verre est élevé, plus il est fin et léger — un vrai confort pour les corrections importantes.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/amincissement.jpg" alt="Verres amincis à indice de réfraction élevé" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Indice 1.50</div>
        <h3>Corrections jusqu'à ±2</h3>
        <p>Le verre standard, suffisant pour les corrections légères.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">Indice 1.60</div>
        <h3>Corrections jusqu'à ±4</h3>
        <p>Environ 20 % plus fin qu'un verre standard, pour un bon compromis poids/prix.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">Indice 1.67</div>
        <h3>Corrections jusqu'à ±6</h3>
        <p>Environ 35 % plus fin, recommandé à partir des corrections fortes.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Indice 1.74</div>
        <h3>Corrections au-delà de ±6</h3>
        <p>Le plus fin de nos indices, environ 45 % de gain d'épaisseur, réservé aux très fortes corrections.</p>
      </div>
    </div>
    <p style="max-width:760px;margin:32px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Au-delà de la correction, l'indice le plus adapté dépend aussi de la taille de la monture choisie — notre équipe vous conseille l'équilibre le plus confortable entre finesse, poids et budget.</p>
  </div>
</section>

<section class="split story-block" id="choix-monture">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/choisir-monture.jpg" alt="Trois montures de lunettes à choisir selon son style" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Bien choisir</span>
        <h2>Comment bien choisir sa monture</h2>
        <p>Entre ajustement, matériau et forme du visage, quelques repères simples pour s'y retrouver avant l'essayage en boutique.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> La monture doit suivre la ligne de vos sourcils, sans les recouvrir</li>
          <li><span class="check">✓</span> Elle ne doit pas toucher vos pommettes, même en souriant</li>
          <li><span class="check">✓</span> Elle doit épouser la largeur de votre visage, sans comprimer les tempes</li>
          <li><span class="check">✓</span> Le poids doit être bien réparti sur le nez et les oreilles, sans marque après plusieurs heures</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <p style="max-width:760px;margin:0 auto 40px;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">Côté matériau : le métal et le titane offrent légèreté, solidité et une allure sobre, avec pour le titane un excellent confort hypoallergénique. L'acétate permet des couleurs et des formes plus affirmées, avec un ajustement facile par nos opticiens. Pour les corrections plus fortes, une monture plus petite et fermée masque mieux l'épaisseur des verres.</p>
    <div class="degree-scale">
      <div class="degree-card reveal" style="--bar:var(--sage);">
        <div class="db">Visage rond</div>
        <h3>Formes angulaires</h3>
        <p>Une monture rectangulaire ou géométrique contraste avec les courbes du visage et lui apporte du caractère.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--wood);">
        <div class="db">Visage carré</div>
        <h3>Formes rondes ou ovales</h3>
        <p>Des bords arrondis adoucissent des traits marqués et équilibrent l'ensemble du visage.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta);">
        <div class="db">Visage ovale</div>
        <h3>Presque toutes les formes</h3>
        <p>Ce visage équilibré s'accommode de la plupart des montures, des plus géométriques aux plus arrondies.</p>
      </div>
      <div class="degree-card reveal" style="--bar:var(--terracotta-dark);">
        <div class="db">Visage en cœur</div>
        <h3>Formes ovales ou rondes</h3>
        <p>Des bords arrondis, plutôt fins sur le haut, rééquilibrent un front plus large que le menton.</p>
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="entretien-lunettes">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/entretien-lunettes.jpg" alt="Nettoyage d'un verre de lunettes avec un chiffon doux" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Entretien</span>
        <h2>Bien nettoyer et entretenir ses lunettes</h2>
        <p>Un entretien simple mais régulier prolonge la durée de vie de vos verres et de leurs traitements (anti-reflets, anti-rayures) :</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Rincez les verres à l'eau tiède avant d'essuyer, pour éviter que les poussières ne les rayent</li>
          <li><span class="check">✓</span> Utilisez un savon doux ou un spray nettoyant spécial optique, puis séchez avec un chiffon microfibre propre</li>
          <li><span class="check">✓</span> Évitez alcool, ammoniaque, eau très chaude, essuie-tout ou pan de vêtement, qui abîment les traitements de surface</li>
          <li><span class="check">✓</span> Rangez vos lunettes dans leur étui, verres vers le haut, plutôt que de les poser à plat sur une table</li>
        </ul>
        <p>Un contrôle et un nettoyage aux ultrasons chez votre opticien, une fois par an, complètent utilement l'entretien à la maison.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="quand-changer">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Bon à savoir</span>
        <h2>Quand changer ses lunettes ?</h2>
        <p>Vos verres correcteurs sont un équipement médical à part entière, qui mérite un suivi régulier : tous les ans pour les enfants dont la vue évolue vite, tous les 2 à 3 ans pour les adultes, et tous les 2 ans pour les seniors, davantage exposés aux pathologies oculaires.</p>
        <ul class="check-list">
          <li><span class="check">✓</span> Rayures visibles ou traitements qui s'estompent</li>
          <li><span class="check">✓</span> Fatigue visuelle ou maux de tête en fin de journée</li>
          <li><span class="check">✓</span> Vision moins nette en faible luminosité</li>
          <li><span class="check">✓</span> Gêne en lecture de près qui s'installe</li>
        </ul>
        <p>Le cerveau compense souvent, en douceur, une correction qui n'est plus tout à fait adaptée — d'où l'intérêt d'un contrôle régulier plutôt que d'attendre une gêne franche.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/quand-changer.jpg" alt="Renouvellement de lunettes de vue" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="split story-block" id="style">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/conseils/style.jpg" alt="Porter ses lunettes avec style au quotidien" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Style</span>
        <h2>Accorder ses lunettes à son look</h2>
        <p>Vos lunettes sont aussi un accessoire à part entière : quelques repères simples pour les intégrer naturellement à votre style.</p>
      </div>
    </div>
  </div>
</section>

<section class="dark-section">
  <div class="container">
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="6" cy="12" r="3.5"/><circle cx="18" cy="12" r="3.5"/><path d="M9.5 12h5M2 12h.5M21.5 12h.5"/></svg></div>
        <h3>Une paire neutre au quotidien</h3>
        <p>Une monture dans des teintes neutres (écaille, noir, transparent) se marie avec toutes les tenues : idéale comme paire de tous les jours.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg></div>
        <h3>Harmoniser les métaux</h3>
        <p>Accordez la couleur de la monture (or, argent, cuivré) à vos bijoux et accessoires habituels, pour une silhouette cohérente.</p>
      </div>
      <div class="dark-card reveal">
        <div class="badge"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBF6EF" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
        <h3>Une paire signature</h3>
        <p>Une deuxième monture, plus colorée ou plus graphique, pour affirmer votre style lors d'occasions particulières.</p>
      </div>
    </div>
  </div>
</section>

<section class="split alt story-block" id="lunettes-ou-lentilles">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Alternative</span>
        <h2>Lunettes ou lentilles : comment choisir</h2>
        <p>Les deux corrigent aussi bien votre vue — le choix dépend surtout de votre mode de vie et de votre confort au quotidien.</p>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/conseils/lunettes-lentilles.jpg" alt="Montures de lunettes, une alternative aux lentilles" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="reimburse-grid">
      <div class="reimburse-card reveal">
        <span class="tag">Style &amp; simplicité</span>
        <h3>Lunettes</h3>
        <p>Un accessoire à part entière qui affirme votre style, sans manipulation ni entretien quotidien. Aucune contre-indication médicale, adaptées à tous les âges.</p>
      </div>
      <div class="reimburse-card highlight reveal">
        <span class="tag">Liberté &amp; sport</span>
        <h3>Lentilles</h3>
        <p>Quasiment invisibles, elles suivent le mouvement de l'œil pour une vision panoramique sans monture — idéales pour le sport. Elles demandent en revanche un entretien rigoureux et ne conviennent pas en cas d'yeux secs ou d'irritations.</p>
      </div>
    </div>
    <p style="max-width:760px;margin:24px auto 0;text-align:center;color:var(--charcoal-soft);font-size:14.5px;">De nombreux clients associent les deux : les lentilles pour le sport ou les sorties, les lunettes le reste du temps. Notre équipe évalue avec vous si vos yeux sont compatibles avec le port de lentilles lors d'une séance d'adaptation.</p>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur l'entretien de vos équipements ?</h2>
    <p>Passez en boutique, Centre commercial Grand Angle : nettoyage, ajustages et petits conseils sont assurés sur place.</p>
    <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
  </div>
</section>
"""


# ============================================================================
# BUILD ALL PAGES
# ============================================================================
# ============================================================================
# ACTUALITÉS — journal du site (lancé le 26/07/2026)
# Chaque article a sa propre URL (actualites/<slug>.html) plutôt que d'être
# une simple section sur une grande page : chaque page peut ainsi être
# indexée et positionnée individuellement par Google sur sa propre requête,
# avec son propre titre/meta-description (voir plan SEO — "contenu longue
# traîne", action "en continu"). actualites.html est la page d'index, avec un
# filtre par thématique (JS léger, purement additif : le contenu reste
# entièrement dans le HTML, donc indexable même JS désactivé).
# Contenu recherché sur le web et reformulé avec les mots de Claude, jamais
# copié verbatim, conformément à la politique de citation du site.
# ============================================================================

CATEGORY_ORDER = [
    ("sante-visuelle", "Santé visuelle"),
    ("mode-lunettes", "Mode &amp; tendances"),
    ("tech-verres", "Technologies verres"),
    ("tech-lentilles", "Technologies lentilles"),
    ("remboursements", "Remboursements &amp; démarches"),
    ("vie-boutique", "Vie de la boutique"),
    ("enfant", "Vision de l'enfant"),
]
ARTICLE_CATEGORIES = {}
for _i, (_key, _label) in enumerate(CATEGORY_ORDER):
    _accent, _accent_bg = BRAND_ACCENTS[_i % len(BRAND_ACCENTS)]
    ARTICLE_CATEGORIES[_key] = {"label": _label, "accent": _accent, "accent_bg": _accent_bg}

ART_BODY_FATIGUE = """
<h2>Pourquoi la vision de près sur écran fatigue-t-elle autant ?</h2>
<p>Ce que les ophtalmologistes nomment fatigue visuelle numérique, ou syndrome de vision informatique, n'est pas une maladie : c'est la conséquence de deux efforts que l'œil supporte mal quand ils se prolongent des heures. D'après un baromètre OpinionWay réalisé pour l'Asnav, près d'un actif français sur trois s'en plaint — environ dix millions de personnes — et la proportion grimpe encore chez celles et ceux qui travaillent à distance. Tous usages confondus, le temps passé devant un écran approche aujourd'hui douze heures par jour.</p>

<h3>Le clignement, ce geste qu'on oublie devant un écran</h3>
<p>Dès qu'on fixe un écran, la fréquence de clignement s'effondre : jusqu'à 60&nbsp;% de moins qu'au fil d'une conversation. C'est pourtant lui qui réétale, à chaque passage, le film lacrymal — cette fine couche qui protège et nourrit la surface de l'œil. Quand il n'est plus renouvelé assez souvent, ce film se rompt entre deux clignements, et apparaissent les picotements, la sensation de sable sous la paupière, l'œil qui tire en fin de journée. L'air asséché par le chauffage ou la climatisation ne fait qu'amplifier la gêne.</p>

<h3>Un muscle de mise au point qui ne souffle jamais</h3>
<p>Le second effort est mécanique. Pour rendre nette une image proche, l'œil déforme son cristallin grâce au muscle ciliaire : c'est l'accommodation. Devant un écran trop rapproché, placé trop haut ou fixé sans pause, ce muscle reste contracté du matin au soir — comme un bras qui tiendrait un objet tendu pendant des heures. La vue qui se trouble par moments, les maux de tête au-dessus des yeux et la difficulté à refaire le point au loin en quittant le bureau viennent de là.</p>

<h2>Quels signaux doivent alerter, et que traduisent-ils ?</h2>
<p>Les mêmes phrases reviennent d'un client à l'autre, et chacune pointe assez précisément vers l'un des deux mécanismes. Voici ce que nous entendons le plus souvent au comptoir.</p>
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Ce que vous ressentez</th><th>Ce que cela traduit</th><th>Premier réflexe</th></tr>
    </thead>
    <tbody>
      <tr><td>Yeux secs, qui piquent ou qui grattent</td><td>Film lacrymal instable, faute de clignement</td><td>Larmes artificielles sans conservateur, air moins sec</td></tr>
      <tr><td>Vue qui se brouille par intermittence</td><td>Muscle de mise au point épuisé</td><td>Pauses régulières, écran reculé à 50-70&nbsp;cm</td></tr>
      <tr><td>Maux de tête en fin de journée</td><td>Effort d'accommodation prolongé, parfois correction inadaptée</td><td>Contrôle de la vue</td></tr>
      <tr><td>Nuque et épaules tendues</td><td>Posture de compensation devant un écran mal placé</td><td>Régler la hauteur de l'écran et du siège</td></tr>
      <tr><td>Reflets et éblouissement</td><td>Éclairage de la pièce en conflit avec l'écran</td><td>Écran perpendiculaire à la fenêtre, antireflet</td></tr>
      <tr><td>Gêne surtout à partir de 45 ans</td><td>Presbytie débutante masquée par le travail sur écran</td><td>Examen de vue, verres adaptés à la distance de travail</td></tr>
    </tbody>
  </table>
</div>

<h2>Le filtre anti-lumière bleue change-t-il vraiment quelque chose ?</h2>
<p>C'est la question qui revient le plus, et elle mérite une réponse franche. Les synthèses scientifiques récentes, à commencer par une revue Cochrane, ne mettent pas en évidence de bénéfice net des verres filtrant la lumière bleue sur la fatigue visuelle elle-même. Cette fatigue vient du manque de clignement et de l'accommodation prolongée, pas de la couleur de l'écran : présenter le filtre comme le remède serait donc inexact.</p>
<p>Cela ne veut pas dire que ces verres ne servent à rien. L'effet de la lumière bleue du soir sur l'endormissement est, lui, mieux documenté : si vous travaillez tard, le gain se jouera sur votre sommeil plutôt que sur vos yeux. Et surtout, le confort dépend beaucoup du traitement antireflet, qui efface les reflets de l'éclairage situé derrière vous — un point que l'on confond souvent avec le filtre bleu, alors qu'il s'agit de deux choses différentes.</p>

<h2>Que faire, concrètement, pour soulager ses yeux ?</h2>
<p>Voici l'ordre dans lequel nous conseillons d'agir. Les premiers gestes ne coûtent rien et suffisent dans la plupart des cas.</p>
<ol>
  <li><strong>La règle des 20-20-20.</strong> Toutes les 20&nbsp;minutes, fixez un point situé à environ 6&nbsp;mètres pendant 20&nbsp;secondes : le muscle de mise au point se relâche, et vous reclignez sans y penser.</li>
  <li><strong>Reculez l'écran et abaissez-le.</strong> Visez 50 à 70&nbsp;cm entre vos yeux et la dalle, bord supérieur au niveau du regard ou un peu en dessous. Un regard légèrement plongeant expose moins la surface de l'œil.</li>
  <li><strong>Clignez volontairement</strong> pendant les phases de concentration : deux ou trois clignements marqués par minute changent réellement la fin de journée.</li>
  <li><strong>Anticipez avec des larmes artificielles sans conservateur</strong>, le matin et l'après-midi, plutôt que d'attendre que la gêne s'installe.</li>
  <li><strong>Accordez la luminosité de l'écran à celle de la pièce</strong> et placez-le perpendiculaire à la fenêtre, jamais face ni dos à elle.</li>
  <li><strong>Passé 40-45 ans, renseignez-vous sur les verres « bureau ».</strong> À faible dégression, ils élargissent la zone nette entre 40&nbsp;cm et 2&nbsp;m : souvent le déclic pour qui jongle entre écran, clavier et interlocuteur.</li>
</ol>

<h2>Quand consulter plutôt que régler son poste ?</h2>
<p>Si la gêne résiste à deux ou trois semaines de bons réglages, la cause n'est sans doute plus ergonomique. Une petite correction jamais portée, un astigmatisme passé inaperçu, une presbytie qui débute ou des verres mal centrés suffisent à entretenir des mois de fatigue. En revanche, une vraie douleur de l'œil, une baisse de vue brutale, une vision double ou des éclairs lumineux relèvent d'un avis médical rapide, et non de l'opticien.</p>
<p>À ACTU EYES, au centre commercial Grand Angle, nous recevons beaucoup d'actifs du quartier et d'étudiants qui décrivent exactement ce tableau. Le contrôle de la vue se fait sans rendez-vous, en une vingtaine de minutes : une fois sur deux, il débouche sur un simple ajustement de correction ou une paire dédiée au poste de travail — pas sur un problème de santé.</p>
"""


ART_BODY_MONTURES_2026 = """
<h2>Quelles formes dominent en 2026 ?</h2>
<p>La tendance 2026 se joue sur un équilibre&nbsp;: des formes affirmées, mais portables. Les géométries franches — hexagones adoucis, rectangles nets — côtoient un retour très net du papillon revisité, plus discret que ses versions rétro. Les rondes réinterprétées restent une valeur sûre pour les visages qui cherchent de la douceur, tandis que les modèles oversize continuent d'habiller les fronts dégagés. L'idée générale&nbsp;: une monture qui se remarque par sa ligne, pas par sa taille.</p>

<h2>Quelles matières et quelles couleurs ?</h2>
<p>L'acétate domine toujours, pour sa profondeur de teinte et son toucher. L'écaille reste indétrônable, mais elle est concurrencée par des acétates translucides — miel, ambre, gris fumé — qui laissent deviner la carnation et se fondent au visage. Côté métal, la finesse est reine&nbsp;: branches filiformes, cerclages presque invisibles, pour un style minimaliste et léger. Les tons neutres et poudrés s'imposent sur les paires de tous les jours, la couleur vive se réservant à la seconde paire, celle qu'on ose.</p>

<h2>Comment savoir ce qui vous ira vraiment ?</h2>
<p>Une tendance n'est utile que si elle vous va. Trois repères simples&nbsp;: la largeur de la monture doit correspondre à celle du visage, sans déborder ni serrer&nbsp;; la ligne haute de la monture se coordonne à celle des sourcils&nbsp;; et la forme joue avec celle du visage plutôt que de la répéter — une forme anguleuse adoucit un visage rond, une forme arrondie équilibre des traits marqués. Le reste est affaire d'essayage&nbsp;: une même envie trouve souvent plusieurs réponses crédibles.</p>

<h2>Faut-il céder à la mode ou viser l'intemporel ?</h2>
<p>Les deux, à condition de savoir quoi mettre où. Pour la paire principale, portée tous les jours et gardée plusieurs années, une forme sobre limite le risque de s'en lasser. Pour une seconde paire ou une solaire, on peut assumer une ligne plus marquée. C'est la logique que nous conseillons le plus souvent&nbsp;: une base durable, un plaisir plus audacieux à côté.</p>

<h2>Les marques que nous aimons faire essayer</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, la sélection couvre exactement cet éventail&nbsp;: l'intemporel signé Ray-Ban ou Ralph Lauren, l'élégance sobre de Dior et Celine, l'audace assumée de Gucci, Prada, Fendi ou Miu Miu, et l'esprit héritage de Burberry. Nous ne poussons aucune marque en particulier&nbsp;: nous partons de votre visage et de votre usage, puis nous faisons essayer. C'est souvent en reposant une paire qu'on comprend pourquoi une autre était la bonne.</p>
"""

ART_BODY_TECH_VERRES = """
<h2>Un verre correcteur, c'est bien plus qu'une correction</h2>
<p>On résume souvent un verre à sa puissance de correction. En réalité, deux verres à la même correction peuvent offrir un confort très différent selon leur matière, leur forme et leurs traitements. C'est là que se jouent la finesse, la légèreté, la résistance et la qualité de vision d'une paire. Comprendre ces paramètres, c'est éviter de payer pour des options inutiles — ou, à l'inverse, de se priver de celles qui changent vraiment le quotidien.</p>

<h2>Indice et matière&nbsp;: la question de l'épaisseur</h2>
<p>Plus une correction est forte, plus le verre a tendance à être épais. L'<strong>indice de réfraction</strong> permet de compenser cela&nbsp;: à correction égale, un indice élevé donne un verre plus fin et plus léger. Pour une petite correction, un indice standard suffit&nbsp;; au-delà, monter en indice améliore nettement l'esthétique et le confort, surtout sur les montures fines ou percées. La matière compte aussi&nbsp;: le polycarbonate, très résistant aux chocs, est recommandé pour les enfants et le sport.</p>

<h2>Les traitements qui changent le confort</h2>
<p>Ce sont eux qui font la différence à l'usage. Le <strong>traitement antireflet</strong> supprime les reflets parasites — ceux de l'éclairage derrière vous, des phares la nuit, des écrans — et rend le regard plus lisible pour vos interlocuteurs&nbsp;; c'est, de loin, l'option la plus utile. Le <strong>traitement anti-rayure</strong> durcit la surface, le <strong>traitement hydrophobe</strong> fait glisser l'eau et les traces de doigts, facilitant le nettoyage. Enfin, les verres <strong>photochromiques</strong> foncent à la lumière et s'éclaircissent à l'intérieur, pour une seule paire jour et nuit.</p>

<h2>Faut-il un filtre anti-lumière bleue ?</h2>
<p>Soyons clairs&nbsp;: les études récentes ne démontrent pas que le filtre anti-lumière bleue réduit la fatigue visuelle liée aux écrans. Son intérêt réel se situe ailleurs, sur le confort le soir et l'endormissement, mieux documenté. Pour le confort devant un écran, c'est surtout le traitement antireflet qui agit, en éliminant les reflets de l'environnement. Nous préférons vous l'expliquer plutôt que de vendre une option sur un malentendu.</p>

<h2>Comment choisir sans se tromper ?</h2>
<p>La bonne méthode part de votre usage, pas d'un catalogue&nbsp;: combien d'heures d'écran, quelle conduite de nuit, quel besoin de finesse esthétique, quelle exposition au soleil. À ACTU EYES, au centre Grand Angle à Montreuil, nous travaillons notamment avec des verriers comme Essilor et Novacel, et nous détaillons chaque option sur le devis normalisé, avec l'offre 100&nbsp;% Santé en regard. L'objectif&nbsp;: que vous compreniez ce que vous payez et pourquoi — et rien de superflu.</p>
"""

ART_BODY_TECH_LENTILLES = """
<h2>Les lentilles ont beaucoup évolué&nbsp;: où en est-on ?</h2>
<p>Longtemps réservées à certains profils, les lentilles conviennent aujourd'hui à un très large public grâce aux progrès des matériaux. L'enjeu de départ est simple&nbsp;: l'œil a besoin d'oxygène, et une lentille est posée dessus toute la journée. Les matériaux modernes, en tête desquels le <strong>silicone-hydrogel</strong>, laissent passer bien plus d'oxygène que les anciennes lentilles souples, ce qui améliore la tolérance et réduit la sensation d'œil sec en fin de journée.</p>

<h2>Quel rythme de renouvellement choisir ?</h2>
<p>C'est le premier critère, et il dépend de votre usage.</p>
<ul>
  <li><strong>Journalières&nbsp;:</strong> une paire neuve chaque jour, jetée le soir. Le maximum d'hygiène et de simplicité, idéal pour un port occasionnel (sport, sorties) ou les yeux sensibles. Aucun entretien.</li>
  <li><strong>Bimensuelles et mensuelles&nbsp;:</strong> plus économiques pour un port quotidien, mais elles imposent un entretien rigoureux avec une solution adaptée et un étui changé régulièrement.</li>
</ul>
<p>Le bon choix se fait avec le praticien, selon la fréquence de port, le budget et la santé de vos yeux.</p>

<h2>Presbytie, astigmatisme&nbsp;: des lentilles pour presque tout</h2>
<p>Les lentilles ne se limitent plus à la myopie. Les modèles <strong>toriques</strong> corrigent l'astigmatisme, les <strong>multifocales</strong> répondent à la presbytie, et des solutions combinent les deux. Toutes les corrections ne sont pas également faciles à équiper, et le résultat se juge à l'essai&nbsp;: c'est pourquoi un premier port se fait toujours de façon encadrée, avec des lentilles d'essai et un contrôle.</p>

<h2>Les règles d'hygiène à ne jamais négliger</h2>
<p>La grande majorité des complications viennent d'un défaut d'hygiène. Quelques règles non négociables&nbsp;: se laver les mains avant toute manipulation, respecter la durée de port et de renouvellement, ne jamais mettre les lentilles au contact de l'eau du robinet ou sous la douche, ne pas dormir avec sauf modèle prévu pour, et renouveler la solution et l'étui. Au moindre œil rouge, douloureux ou qui voit trouble, on retire la lentille et on consulte.</p>

<h2>Se lancer sereinement</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous proposons l'ensemble des marques de lentilles et nous encadrons l'apprentissage&nbsp;: pose, retrait, entretien, choix du rythme de renouvellement. Un premier essai permet de vérifier la tolérance et la vision avant de s'engager. Bien accompagnées, les lentilles sont une vraie liberté&nbsp;; mal utilisées, elles font courir des risques inutiles — d'où l'importance d'un vrai suivi.</p>
"""

ART_BODY_REMBOURSEMENTS = """
<h2>Le 100&nbsp;% Santé en optique, comment ça marche ?</h2>
<p>La réforme du 100&nbsp;% Santé garantit l'accès à des lunettes de qualité sans aucun reste à charge. Le principe&nbsp;: pour les personnes couvertes par la Sécurité sociale et une complémentaire santé responsable — la grande majorité des contrats — la prise en charge couvre l'intégralité du prix d'un équipement de classe&nbsp;A. Concrètement, cela comprend une monture plafonnée à 30&nbsp;€, proposée en plusieurs coloris, et des verres traités&nbsp;: amincis selon la correction, antireflet et anti-rayure. Reste à payer&nbsp;: 0&nbsp;€.</p>

<h2>Deux paniers, et la liberté de panacher</h2>
<p>Tout équipement se répartit en deux ensembles. La <strong>classe&nbsp;A</strong> correspond au 100&nbsp;% Santé, sans reste à charge. La <strong>classe&nbsp;B</strong>, à prix libre, regroupe les montures et verres hors plafond, remboursés selon les garanties de votre mutuelle. Ce qu'on oublie souvent&nbsp;: vous pouvez <strong>mélanger les deux</strong>. Une monture à prix libre peut recevoir des verres 100&nbsp;% Santé, et inversement&nbsp;; le 100&nbsp;% Santé n'est jamais imposé, c'est un droit que vous activez si vous le souhaitez.</p>

<h2>À quelle fréquence peut-on en bénéficier ?</h2>
<p>La prise en charge d'un équipement complet est prévue tous les <strong>deux ans</strong> pour les adultes et les enfants à partir de 16&nbsp;ans, et tous les <strong>ans</strong> avant 16&nbsp;ans. Ce délai peut être raccourci en cas d'évolution de la vue justifiée par une nouvelle ordonnance, notamment chez l'enfant ou lors de changements de correction importants. Le décompte se fait par type d'équipement&nbsp;: mieux vaut vérifier votre date de dernier remboursement, ce que nous faisons pour vous en boutique.</p>

<h2>Les démarches&nbsp;: nous nous en occupons</h2>
<p>Nous vérifions vos droits, interrogeons votre complémentaire quand c'est possible et appliquons le <strong>tiers payant</strong> dès que le contrat l'autorise&nbsp;: vous n'avez alors pas à avancer la part remboursée. Avant tout engagement, nous remettons un <strong>devis normalisé</strong> gratuit qui détaille, ligne par ligne, le prix de la monture, celui des verres et les parts prises en charge. C'est le document qui permet de comparer et de décider en confiance.</p>

<h2>En pratique à Montreuil</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, le 100&nbsp;% Santé figure sur chacun de nos devis, aux côtés des options à prix libre, sans que l'un soit présenté comme supérieur à l'autre. Notre rôle est de vous expliquer clairement vos droits et de vous laisser choisir&nbsp;: une belle paire accessible, une monture plus libre, ou un panachage des deux. Dans tous les cas, la transparence d'abord.</p>
"""

ART_BODY_VIE_BOUTIQUE = """
<h2>Reprendre une boutique plutôt qu'en ouvrir une</h2>
<p>Tout commence en 2018. La boutique d'optique du centre commercial Grand Angle, à Montreuil, existe déjà — elle fait partie des enseignes présentes depuis l'ouverture du centre, en 2012. Quand Mikhael la reprend, il ne part donc pas d'une page blanche&nbsp;: il hérite d'un emplacement, d'une clientèle, d'habitudes. Son pari n'est pas de tout raser, mais de faire mieux&nbsp;: de nouvelles marques, une autre ambiance, et surtout une relation plus proche, plus attentive, que celle qui existait avant.</p>
<p>Le positionnement se dessine dès ces premières années et n'a plus bougé&nbsp;: des maisons haut de gamme, mais un large choix de montures très abordables et vraiment belles. L'idée est simple à dire et exigeante à tenir&nbsp;: que personne ne reparte sans une paire qui lui plaît, quel que soit son budget.</p>

<h2>Une rencontre qui change tout</h2>
<p>En 2021, Sudaya rejoint l'équipe. Il fait rapidement ses preuves&nbsp;: le sens du conseil, l'écoute, le soin apporté à chaque client. De cette collaboration naît une envie commune, et en 2023, avec Sudaya, nous ouvrons ensemble une seconde enseigne, à Paris. Le lien se resserre encore en 2025, quand Sudaya devient associé d'ACTU EYES Montreuil&nbsp;: un partenariat pensé pour durer, deux boutiques et une même exigence.</p>

<h2>Ce que nous voulons faire différemment</h2>
<p>Notre conviction tient en une phrase&nbsp;: le service client passe avant tout. Concrètement, cela veut dire prendre le temps de l'essayage, écouter ce que la personne cherche vraiment — sur le plan esthétique, technique comme tarifaire — et ne jamais pousser une vente qui n'a pas de sens. L'examen de vue est gratuit et sans rendez-vous, le devis toujours détaillé et remis avant tout engagement. Le reste, c'est de l'attention&nbsp;: se souvenir d'un visage, réajuster une monture qui glisse, réparer plutôt que remplacer quand c'est possible.</p>

<h2>Un opticien de quartier, vraiment</h2>
<p>Grand Angle est un centre moderne, mais c'est aussi un quartier&nbsp;: le Cœur de Ville de Montreuil, face à la mairie, entre bureaux, marché, cinéma et logements. Notre clientèle lui ressemble — familles, actifs, étudiants, habitants de longue date. C'est cette diversité qui rend le métier vivant, et c'est pour elle que nous travaillons&nbsp;: pour être, année après année, l'opticien à qui l'on revient.</p>
<p style="margin-top:6px;">— Mikhael &amp; Sudaya, ACTU EYES</p>
"""

ART_BODY_ENFANT = """<h2>Pourquoi les troubles visuels de l'enfant passent-ils souvent inaperçus ?</h2>
<p>Un enfant ne se plaint presque jamais de mal voir&nbsp;: il n'a aucun point de comparaison et pense que tout le monde voit comme lui. C'est ce qui rend le repérage si important, car la vision se construit dans les premières années, et un défaut non corrigé à temps peut installer une amblyopie — un œil qui « décroche » durablement. La bonne nouvelle, c'est que les signes existent&nbsp;: ils sont comportementaux, visibles au quotidien par les parents et les enseignants, bien avant que l'enfant ne mette des mots dessus.</p>

<h2>Quels signes doivent alerter, selon l'âge ?</h2>
<p>Certains comportements reviennent régulièrement et méritent qu'on s'y attarde.</p>
<ul>
  <li><strong>Chez le tout-petit&nbsp;:</strong> un œil qui dévie, qui « part » vers le nez ou l'extérieur, un enfant qui ne suit pas les objets du regard, qui se cogne souvent ou plisse fortement les yeux.</li>
  <li><strong>À l'âge de la lecture&nbsp;:</strong> il rapproche exagérément livre ou écran, saute des lignes, suit avec le doigt, ferme ou couvre un œil, se plaint de maux de tête en fin de journée.</li>
  <li><strong>En classe&nbsp;:</strong> difficultés à copier au tableau, fatigue, baisse d'attention ou de résultats qui contrastent avec les capacités de l'enfant.</li>
</ul>
<p>Aucun de ces signes ne suffit à poser un diagnostic, mais leur répétition est un signal clair qu'un examen s'impose.</p>

<h2>À quel âge et à qui s'adresser ?</h2>
<p>Des examens de dépistage sont prévus dès les premiers mois, puis vers 3-4&nbsp;ans et à l'entrée en primaire, chez le pédiatre, le médecin traitant ou en PMI. Au moindre doute, c'est l'<strong>ophtalmologiste</strong> qui réalise l'examen complet et pose, si besoin, la prescription. Chez l'enfant, ce passage médical est incontournable&nbsp;: contrairement à ce qui est permis pour l'adulte, l'opticien ne peut pas adapter seul une correction avant 16&nbsp;ans. Notre rôle intervient ensuite&nbsp;: choisir une monture adaptée à un petit visage, la régler pour qu'elle tienne, et accompagner le suivi.</p>

<h2>Le rôle de l'opticien une fois l'ordonnance en main</h2>
<p>Équiper un enfant n'a rien à voir avec équiper un adulte. La monture doit être légère, résistante, correctement centrée sur de petits écarts pupillaires, et tenir pendant une récréation mouvementée. Nous privilégions des matières souples, des branches enveloppantes ou un bandeau selon l'âge, et nous revoyons volontiers l'enfant pour réajuster au fil de sa croissance. Une paire qui glisse ou qui blesse finit dans un tiroir&nbsp;: le confort n'est pas un détail, c'est la condition pour que la correction serve vraiment.</p>

<h2>En pratique à Montreuil</h2>
<p>À ACTU EYES, au centre commercial Grand Angle, nous recevons beaucoup de familles du quartier. Nous ne réalisons pas d'examen chez l'enfant — il relève de l'ophtalmologiste — mais nous prenons le temps qu'il faut pour l'équipement, l'ajustement et le suivi, et nous orientons sans hésiter vers un médecin quand un signe nous semble mériter un avis.</p>
"""

ART_BODY_VARILUX = """
<h2>Pourquoi nos yeux passent-ils l'essentiel de la journée «&nbsp;de près&nbsp;»&nbsp;?</h2>
<p>Nos habitudes visuelles ont changé plus vite que nos verres. Entre l'ordinateur, le téléphone, la lecture et les réunions, une grande partie de la journée se joue désormais à quelques mètres à peine, à l'intérieur, et non sur l'horizon. Un verre progressif classique consacre pourtant une large part de sa surface à la vision de loin — celle dont on se sert le moins entre neuf et dix-huit heures. C'est ce déséquilibre que certains verres pensés pour l'intérieur cherchent à corriger.</p>

<h2>Qu'apporte un progressif optimisé pour l'intérieur ?</h2>
<p>L'idée est de déplacer le «&nbsp;centre de gravité&nbsp;» du verre vers les distances proches et intermédiaires. Concrètement, ces verres — comme le Varilux Immersia d'Essilor dans sa logique de conception — élargissent les zones nettes utiles en intérieur&nbsp;: l'écran, le clavier, le collègue en face, le rayon d'un magasin. Le passage d'une distance à l'autre est plus fluide, avec moins de mouvements de tête pour trouver la zone nette. Le confort se ressent surtout en fin de journée, quand la fatigue accentue les défauts d'un verre mal adapté.</p>

<h2>Progressif polyvalent ou verre d'intérieur&nbsp;: comment choisir ?</h2>
<p>Ce n'est pas l'un contre l'autre, c'est une question d'usage. Pour une personne qui alterne conduite, extérieur et bureau, un bon progressif polyvalent reste le choix logique. Pour un presbyte qui passe l'essentiel de sa journée devant un écran, un verre d'intérieur — ou une seconde paire dédiée — apporte un confort que le polyvalent ne peut pas égaler sur ces distances. Beaucoup de nos clients finissent avec deux paires complémentaires plutôt qu'un compromis unique.</p>

<h2>Le rôle décisif du centrage</h2>
<p>Un verre progressif, aussi perfectionné soit-il, ne donne sa pleine mesure que s'il est parfaitement centré et monté sur une monture bien réglée. Quelques millimètres d'écart suffisent à décaler les zones nettes et à gâcher un verre haut de gamme. C'est la partie invisible du métier&nbsp;: prise de mesures précise, choix d'une monture adaptée à la hauteur nécessaire, ajustements après quelques jours de port.</p>

<h2>En boutique</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous travaillons avec Essilor parmi nos verriers et nous prenons le temps d'analyser votre journée avant de recommander un verre. Un progressif d'intérieur n'a de sens que si votre quotidien le justifie&nbsp;: nous préférons vous poser les bonnes questions plutôt que de vendre la technologie la plus chère par principe.</p>
"""

ART_BODY_NOVACEL_CELENE = """
<h2>Pourquoi le traitement antireflet fait toute la différence</h2>
<p>Sur un verre correcteur, l'antireflet est sans doute l'option qui change le plus le quotidien. En supprimant les reflets parasites — l'éclairage situé derrière vous, les phares la nuit, la lumière des écrans — il améliore le confort, la netteté et, détail non négligeable, il rend votre regard visible pour les autres au lieu de le masquer derrière des reflets. Tous les antireflets ne se valent pas&nbsp;: leur efficacité, leur résistance aux rayures et leur facilité de nettoyage varient d'une gamme à l'autre.</p>

<h2>Novacel, un verrier français</h2>
<p>Novacel est l'un des fabricants de verres avec lesquels nous travaillons. Comme les grands verriers, il décline ses verres en plusieurs indices, géométries et traitements, dont des antireflets soignés. L'intérêt de disposer de plusieurs sources d'approvisionnement est simple&nbsp;: pouvoir proposer, pour chaque correction et chaque budget, le verre le plus adapté plutôt qu'un choix imposé.</p>

<h2>Un antireflet à teinte «&nbsp;nude&nbsp;»&nbsp;: de quoi s'agit-il ?</h2>
<p>Un verre antireflet n'est jamais totalement neutre&nbsp;: il conserve un très léger reflet résiduel, dont la couleur dépend de la formule du traitement. Les reflets verdâtres ou bleutés, courants, se remarquent sur les photos et sur le visage. Les traitements dits à teinte «&nbsp;nude&nbsp;» cherchent à rendre ce reflet résiduel plus discret et plus neutre, pour un verre qui se fait oublier — un avantage esthétique appréciable, notamment pour celles et ceux que les reflets colorés dérangent sur les photos.</p>

<h2>Comment juger un antireflet en boutique ?</h2>
<p>Quelques repères concrets&nbsp;: inclinez le verre sous une lumière pour observer la couleur et l'intensité du reflet résiduel — plus il est discret, mieux c'est. Passez le doigt&nbsp;: un bon traitement hydrophobe repousse les traces. Renseignez-vous sur la garantie, car un antireflet de qualité s'accompagne d'une bonne résistance dans le temps. Et surtout, rapportez le tout à votre usage&nbsp;: conduite de nuit, écrans, photos fréquentes.</p>

<h2>Notre conseil</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous choisissons le couple verre + traitement en fonction de votre correction, de votre monture et de votre quotidien, et nous le détaillons sur le devis normalisé. L'antireflet n'est pas un supplément gadget&nbsp;: c'est souvent l'option qui, à elle seule, fait qu'une paire est confortable dès le premier jour.</p>
"""

ART_BODY_ALCON_PRECISION7 = """
<h2>Une lentille «&nbsp;hebdomadaire&nbsp;»&nbsp;: quel intérêt ?</h2>
<p>Entre la journalière, jetée chaque soir, et la mensuelle, portée trente jours, la lentille à renouvellement hebdomadaire occupe une place intermédiaire encore peu connue. Le principe&nbsp;: une même paire portée une semaine, puis remplacée. On y gagne un compromis&nbsp;: moins de déchets et un coût inférieur à la journalière pour un port régulier, tout en limitant l'accumulation de dépôts propre aux lentilles gardées longtemps. La Precision7 d'Alcon appartient à cette catégorie des lentilles à port hebdomadaire.</p>

<h2>Pour qui ce rythme est-il pertinent ?</h2>
<p>Il convient bien à un porteur régulier mais pas forcément quotidien, qui souhaite une hygiène supérieure à celle d'une mensuelle sans le coût d'une journalière. Le renouvellement fréquent limite les dépôts de protéines et de lipides, souvent responsables d'inconfort et de rougeurs en fin de cycle sur les lentilles gardées plus longtemps. Comme toujours, la pertinence se juge au cas par cas, selon la fréquence de port et la sensibilité de vos yeux.</p>

<h2>Le matériau et le confort</h2>
<p>Les lentilles modernes de ce type sont en silicone-hydrogel, un matériau qui laisse passer une grande quantité d'oxygène vers la cornée&nbsp;: c'est un facteur clé de tolérance, surtout sur une journée longue. S'y ajoutent des technologies de surface destinées à retenir l'humidité et à maintenir le confort du matin au soir. Ces caractéristiques ne dispensent jamais des règles d'entretien propres au rythme de renouvellement choisi.</p>

<h2>Entretien&nbsp;: les règles restent les mêmes</h2>
<p>Port hebdomadaire ne veut pas dire sans entretien&nbsp;: entre deux journées, la lentille se conserve dans une solution adaptée, dans un étui propre changé régulièrement. Les fondamentaux ne changent pas&nbsp;: mains lavées avant manipulation, pas de contact avec l'eau, respect de la durée de port, et retrait immédiat en cas d'œil rouge ou douloureux, suivi d'une consultation.</p>

<h2>Un essai encadré avant de choisir</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous proposons les différentes marques de lentilles, dont les gammes Alcon, et nous vous aidons à trouver le rythme de renouvellement qui correspond réellement à votre usage. Un essai encadré permet de vérifier la tolérance et la vision avant de vous engager&nbsp;: c'est la seule façon fiable de savoir si un modèle vous convient.</p>
"""

ART_BODY_BL_ASANA = """
<h2>Lentilles rigides&nbsp;: pourquoi elles existent encore</h2>
<p>Face aux lentilles souples, très répandues, les lentilles rigides — dites perméables aux gaz — gardent des indications précises où elles restent souvent la meilleure solution. Plus petites et plus fermes, elles conservent leur forme sur l'œil, ce qui leur permet de corriger des situations que les souples gèrent mal&nbsp;: astigmatismes importants, cornées irrégulières, kératocône, ou encore certaines presbyties exigeantes. Elles offrent une vision d'une grande netteté et une excellente longévité.</p>

<h2>Quels avantages, quelles contraintes ?</h2>
<p>Leurs atouts&nbsp;: une qualité de vision remarquable, une bonne oxygénation de la cornée grâce au matériau perméable, une durée de vie de plusieurs années et un entretien simple. Leur contrepartie&nbsp;: un temps d'adaptation plus long que les souples, car l'œil doit s'habituer à la présence d'une lentille ferme. Cette période, bien accompagnée, se franchit sans difficulté&nbsp;; c'est ensuite un confort stable et durable qui s'installe. Le fabricant Bausch&nbsp;+&nbsp;Lomb, comme d'autres, propose des lentilles de ce type.</p>

<h2>Pour qui sont-elles particulièrement indiquées ?</h2>
<p>On les propose souvent lorsqu'une lentille souple ne donne pas satisfaction&nbsp;: astigmatisme fort mal corrigé, vision fluctuante, inconfort. Elles sont aussi une réponse de référence pour les cornées déformées, où elles recréent une surface optique régulière. Dans ces cas, le gain de vision peut être spectaculaire par rapport aux lunettes ou aux lentilles souples.</p>

<h2>Un équipement qui demande du suivi</h2>
<p>Une lentille rigide se prescrit et s'ajuste avec soin&nbsp;: géométrie, diamètre, adaptation à la courbure de la cornée. Le suivi est essentiel, surtout au début, pour affiner l'ajustement et vérifier la tolérance. Les règles d'hygiène restent impératives&nbsp;: mains propres, solution et étui adaptés, pas de contact avec l'eau, et consultation au moindre signe d'alerte.</p>

<h2>En parler en boutique</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous proposons l'ensemble des marques de lentilles et nous prenons le temps d'expliquer les options, y compris les lentilles rigides quand elles sont la bonne réponse. Si votre situation le justifie, nous vous orientons vers l'examen et l'adaptation nécessaires&nbsp;: une lentille rigide bien adaptée peut transformer le confort de vision là où les autres solutions échouent.</p>
"""

ART_BODY_UV_SOLEIL = """
<h2>Pourquoi faut-il vraiment protéger ses yeux du soleil ?</h2>
<p>On protège sa peau du soleil par réflexe, ses yeux beaucoup moins. Pourtant, les rayons ultraviolets abîment aussi les structures de l'œil, et le font de façon cumulative&nbsp;: chaque exposition compte, et rien ne s'efface. À court terme, une journée en montagne ou en mer sans protection peut provoquer une kératite, sorte de « coup de soleil » de la cornée, douloureuse mais réversible. À long terme, l'excès d'UV est associé à un vieillissement accéléré du cristallin — donc à une cataracte plus précoce — et participe à certaines atteintes de la rétine. Les enfants sont les plus exposés&nbsp;: leur cristallin, plus clair, filtre moins bien.</p>

<h2>Quel indice de protection choisir ?</h2>
<p>Deux repères se confondent souvent, à tort. La <strong>catégorie</strong> (de 0 à 4) mesure la quantité de lumière visible arrêtée&nbsp;: 0 pour un verre quasi clair, 3 pour un usage courant en plein soleil, 4 réservé à la haute montagne et à la mer, mais interdit au volant car trop sombre. La protection <strong>UV</strong>, elle, est une donnée à part&nbsp;: un bon verre solaire porte la mention «&nbsp;UV400&nbsp;», qui garantit le filtrage des ultraviolets jusqu'à 400&nbsp;nanomètres, indépendamment de sa teinte. Un verre très foncé mais sans filtre UV est même dangereux&nbsp;: en dilatant la pupille, il laisse entrer davantage de rayons nocifs.</p>

<h2>Faut-il des verres polarisants ?</h2>
<p>Les verres polarisants suppriment les reflets qui rebondissent sur les surfaces horizontales — route mouillée, plan d'eau, neige, carrosserie. Le gain de confort est net pour la conduite, la pêche, la voile ou le ski, où l'éblouissement est un vrai danger. Ils ne protègent pas davantage des UV que des verres classiques équivalents&nbsp;: c'est un plus de confort et de sécurité, pas de protection. Un point à connaître&nbsp;: ils peuvent rendre difficile la lecture de certains écrans ou tableaux de bord.</p>

<h2>Comment choisir la bonne teinte ?</h2>
<p>La teinte se choisit selon l'usage, pas selon la mode seule. Le gris respecte les couleurs et convient à tout&nbsp;; le brun et le vert renforcent les contrastes, appréciés en conduite et en sport&nbsp;; les teintes plus vives relèvent surtout de l'esthétique. Pour une paire portée toute l'année, mieux vaut une teinte sobre et une catégorie&nbsp;3. En boutique, nous faisons toujours comparer plusieurs intensités à la lumière du jour&nbsp;: c'est là, et pas sous les néons, qu'un choix se fait.</p>

<h2>Des solaires à votre vue</h2>
<p>Porter des lunettes de vue ne prive pas de soleil. Presque toutes les corrections peuvent être montées en solaire, en teinte permanente ou en verres photochromiques qui foncent à la lumière et s'éclaircissent à l'intérieur. À ACTU EYES, au centre commercial Grand Angle à Montreuil, nous montons des solaires correcteurs dans la plupart des marques présentées — de Ray-Ban à Prada — et nous vérifions systématiquement la mention UV400, quelle que soit la paire. Une belle monture solaire qui ne protège pas vraiment n'a aucun intérêt&nbsp;: la protection d'abord, le style ensuite — et de préférence les deux.</p>
"""

ART_BODY_PRESBYTIE = """
<h2>La presbytie, qu'est-ce que c'est exactement ?</h2>
<p>La presbytie n'est pas une maladie, c'est une évolution naturelle de l'œil. Avec l'âge, le cristallin perd peu à peu sa souplesse et le muscle qui le déforme se fatigue&nbsp;: la mise au point de près devient plus lente et moins efficace. Résultat, on éloigne instinctivement son téléphone ou son livre pour retrouver la netteté. Le phénomène débute généralement autour de 40-45&nbsp;ans et concerne, tôt ou tard, la quasi-totalité des adultes — y compris ceux qui n'ont jamais porté de lunettes.</p>

<h2>Quels signes annoncent son arrivée ?</h2>
<p>Les premiers signes sont discrets et souvent mis sur le compte de la fatigue. On tend les bras pour lire une étiquette, on réclame plus de lumière, on peine sur les petits caractères d'une notice ou d'un menu au restaurant. Le soir, après une journée d'écran, la gêne s'accentue. Ces signaux, quand ils se répètent, ne trompent pas&nbsp;: ce n'est ni un caprice ni une baisse de forme passagère, c'est le début de la presbytie.</p>

<h2>Quelles solutions existent aujourd'hui ?</h2>
<p>Le choix n'a jamais été aussi large, et il dépend surtout de votre mode de vie.</p>
<ul>
  <li><strong>Les verres progressifs&nbsp;:</strong> une seule paire pour voir net de loin, à distance intermédiaire et de près, avec une transition invisible. C'est la solution la plus polyvalente&nbsp;; le confort dépend beaucoup de la qualité du verre et de la précision du centrage.</li>
  <li><strong>Les verres de proximité (dits «&nbsp;bureau&nbsp;»)&nbsp;:</strong> pensés pour le travail sur écran et la lecture, ils offrent un large champ net entre 40&nbsp;cm et 2&nbsp;m, mais ne conviennent pas pour conduire.</li>
  <li><strong>Les simples verres de lecture&nbsp;:</strong> utiles pour un usage ponctuel, insuffisants dès qu'on alterne les distances dans la journée.</li>
  <li><strong>Les lentilles&nbsp;:</strong> des versions multifocales existent et conviennent à de nombreux presbytes&nbsp;; un essai encadré permet de savoir si elles vous vont.</li>
</ul>

<h2>Faut-il s'attendre à une période d'adaptation ?</h2>
<p>Pour un premier progressif, oui, souvent quelques jours à deux semaines. Le cerveau apprend à utiliser les différentes zones du verre&nbsp;: on regarde droit devant pour le loin, on baisse légèrement les yeux pour lire. Un centrage précis et une monture bien réglée changent tout à ce stade — c'est la partie du métier qui ne se voit pas mais qui fait la différence entre un progressif que l'on adopte et un progressif que l'on abandonne.</p>

<h2>Quand consulter, et où s'équiper ?</h2>
<p>La première correction de presbytie passe par l'ophtalmologiste, qui vérifie au passage la santé des yeux. Ensuite, tant que l'ordonnance est valide, nous pouvons en adapter la correction lors d'un examen en boutique. À ACTU EYES, au centre Grand Angle à Montreuil, nous prenons le temps de l'essayage, du centrage et des réglages, et nous revoyons volontiers les nouveaux porteurs de progressifs pour ajuster ce qui doit l'être. Bien accompagnée, la presbytie se vit sans y penser.</p>
"""



ART_BODY_DEVIS_NORMALISE = """
<h2>Qu'est-ce que le devis normalisé, et qui doit vous le remettre ?</h2>
<p>Le devis normalisé est un document obligatoire que votre opticien doit vous remettre avant tout achat de lunettes de vue, gratuitement et sans le moindre engagement. Son format est encadré par la réglementation : il présente séparément le prix de la monture et celui des verres, précise la nature exacte de chaque verre, et distingue les équipements relevant du 100&nbsp;% Santé de ceux à prix libre. Autrement dit, ce n'est pas un simple prix affiché à la va-vite : c'est une fiche de transparence, pensée pour que vous puissiez comprendre et comparer.</p>
<p>Sa raison d'être est simple. En optique, deux paires au même prix d'apparence peuvent recouvrir des verres très différents — indice, traitements, qualité de surfaçage. Le devis met ces éléments à plat noir sur blanc, ce qui vous permet de comparer d'un opticien à l'autre sur des bases réellement identiques.</p>

<h2>Comment lire les deux « paniers » du 100&nbsp;% Santé ?</h2>
<p>Depuis la réforme du 100&nbsp;% Santé, tout devis distingue deux ensembles, que la loi appelle des paniers.</p>
<ul>
  <li><strong>Le panier 100&nbsp;% Santé (classe A)&nbsp;:</strong> une monture plafonnée à 30&nbsp;€ et des verres traités (amincis selon la correction, antireflet, anti-rayure) intégralement pris en charge par la Sécurité sociale et votre complémentaire responsable. Reste à charge&nbsp;: 0&nbsp;€.</li>
  <li><strong>Le panier à prix libre (classe B)&nbsp;:</strong> les montures et verres hors plafond, remboursés selon les garanties de votre mutuelle, avec un reste à charge variable.</li>
</ul>
<p>Point souvent ignoré&nbsp;: vous avez le droit de <strong>panacher</strong>. Rien ne vous oblige à choisir tout en 100&nbsp;% Santé ou tout en prix libre&nbsp;: une monture libre peut très bien recevoir des verres 100&nbsp;% Santé, et inversement. Le devis chiffre chaque combinaison, ce qui rend l'arbitrage clair.</p>

<h2>Quelles mentions doivent obligatoirement y figurer ?</h2>
<p>Un devis complet indique le prix de la monture, le prix de chaque verre pris séparément, la nature et le fabricant des verres, la prestation d'adaptation et de suivi, la part remboursée par l'Assurance Maladie et, lorsque l'information est disponible, celle de votre complémentaire. Y figurent aussi la durée de validité de l'ordonnance et les règles de renouvellement — un équipement tous les deux ans en règle générale à partir de 16&nbsp;ans, tous les ans avant. Si l'une de ces lignes manque, demandez&nbsp;: un devis conforme n'a rien à cacher.</p>

<h2>Le devis engage-t-il à quelque chose ?</h2>
<p>Non, et c'est tout son intérêt. Vous pouvez repartir avec, le comparer chez vous, le soumettre à votre mutuelle pour connaître votre reste à charge exact, puis revenir — ou non. C'est même l'usage que nous encourageons&nbsp;: mieux vaut un devis étudié tranquillement qu'une décision prise sur un coin de comptoir. Le tiers payant, lorsque votre contrat l'autorise, vous évite ensuite d'avancer la part remboursée.</p>

<h2>Comment nous procédons en boutique</h2>
<p>À ACTU EYES, au centre commercial Grand Angle à Montreuil, nous établissons systématiquement un devis normalisé, y compris pour une simple simulation. Nous interrogeons votre complémentaire quand elle le permet, appliquons le tiers payant dès que le contrat l'autorise, et reprenons chaque ligne avec vous jusqu'à ce que le document soit limpide. Beaucoup de nos clients passent d'abord faire chiffrer une idée, puis reviennent plus tard&nbsp;: c'est exactement l'usage prévu par la réglementation, et c'est le plus sain.</p>
"""

ART_BODY_RENOUVELER_ORDONNANCE = """
<h2>Peut-on vraiment changer de lunettes sans repasser par le médecin ?</h2>
<p>Oui, dans un cadre précis, et c'est une possibilité encore mal connue. Depuis 2016, l'opticien-lunetier est autorisé à adapter la correction inscrite sur une ordonnance de lunettes en cours de validité, après un examen de la vue en boutique. Vous n'avez donc pas besoin d'une nouvelle consultation à chaque paire&nbsp;: tant que votre ordonnance court, nous pouvons ajuster votre correction si votre vue a légèrement évolué, et vous équiper.</p>

<h2>Combien de temps une ordonnance reste-t-elle valable ?</h2>
<p>La durée dépend de l'âge au moment de la prescription&nbsp;:</p>
<ul>
  <li><strong>Moins de 16&nbsp;ans&nbsp;:</strong> 1&nbsp;an.</li>
  <li><strong>De 16 à 42&nbsp;ans&nbsp;:</strong> 5&nbsp;ans.</li>
  <li><strong>Plus de 42&nbsp;ans&nbsp;:</strong> 3&nbsp;ans.</li>
</ul>
<p>Pendant toute cette période, l'opticien peut adapter la correction. Deux exceptions imposent toutefois de repasser par le médecin&nbsp;: les moins de 16&nbsp;ans, et une presbytie découverte pour la première fois. Le prescripteur peut aussi, dans certains cas, s'opposer à l'adaptation en le mentionnant sur l'ordonnance.</p>

<h2>Ce que l'opticien peut faire — et ce qu'il ne peut pas</h2>
<p>Il peut mesurer votre vue et ajuster la correction d'une ordonnance existante&nbsp;; depuis 2024, il peut même le faire dès la première délivrance avec l'accord du prescripteur. Il ne peut en revanche ni établir une première ordonnance, ni poser de diagnostic médical&nbsp;: le suivi ophtalmologique, qui vérifie aussi la santé de l'œil, reste indispensable et n'est jamais remplacé par cet examen.</p>

<h2>Le remboursement est-il conservé ?</h2>
<p>Oui, c'est tout l'intérêt&nbsp;: des lunettes délivrées sur une ordonnance adaptée par l'opticien restent prises en charge par la Sécurité sociale et votre mutuelle, dans les conditions habituelles — un équipement tous les deux ans à partir de 16&nbsp;ans, tous les ans avant. Vous ne perdez donc rien&nbsp;: vous gagnez du temps, tout en gardant vos droits.</p>

<h2>Comment ça se passe chez nous</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, l'examen de vue se fait gratuitement et sans rendez-vous, en une vingtaine de minutes, dans l'espace prévu à cet effet. Si votre ordonnance est valide, nous adaptons votre correction et vous informons — ainsi que votre prescripteur — de toute modification. C'est souvent la solution la plus simple entre deux consultations, à condition de garder un suivi médical régulier par ailleurs.</p>
"""

ART_BODY_RAYBAN_META = """
<h2>Des lunettes connectées, pour quoi faire ?</h2>
<p>Les lunettes connectées ne corrigent pas la vue&nbsp;: elles ajoutent des fonctions à une monture au design classique. Sur les modèles les plus diffusés, comme les Ray-Ban Meta, une petite caméra permet de photographier et filmer à hauteur de regard, des haut-parleurs miniatures diffusent le son directement vers l'oreille, un micro sert aux appels et à un assistant vocal. Le tout dans une silhouette qui ressemble, à s'y méprendre, à une paire de solaires ordinaire. L'intérêt&nbsp;: garder les mains libres et le téléphone dans la poche.</p>

<h2>Peut-on y mettre sa correction ?</h2>
<p>Oui, dans une certaine mesure, et c'est là que l'opticien intervient. Selon les modèles et les plages de correction, il est possible de monter des verres correcteurs, unifocaux ou progressifs, à la place des verres d'origine. Toutes les corrections ne sont pas compatibles, et le résultat dépend du montage&nbsp;: c'est une prestation d'opticien, pas un achat en ligne à l'aveugle. Nous vérifions la faisabilité au cas par cas avant de vous le proposer.</p>

<h2>Quelles questions de vie privée se poser ?</h2>
<p>C'est la question qui revient le plus souvent, et elle est légitime. Une monture équipée d'une caméra filme sans le geste explicite de sortir un téléphone&nbsp;: les personnes en face ne savent pas toujours qu'un enregistrement est en cours. Un témoin lumineux le signale, mais il peut passer inaperçu dans une rue animée. Reste aussi la question du traitement des données par l'éditeur de l'assistant vocal, qui relève de sa propre politique de confidentialité&nbsp;: elle mérite d'être lue avant l'achat plutôt qu'après. Notre conseil&nbsp;: un usage respectueux des autres, et un réglage attentif des autorisations.</p>

<h2>Un gadget ou un vrai usage ?</h2>
<p>Tout dépend de l'usage réel. Pour écouter un podcast en marchant, prendre une photo souvenir sans s'arrêter ou passer un appel mains libres, ces lunettes tiennent leur promesse. Pour qui cherche avant tout une correction et une monture durable, ce n'est pas le sujet&nbsp;: l'électronique ajoute du poids, une autonomie limitée et un coût. Ce n'est ni un miracle ni une lubie&nbsp;: un objet de plus, à choisir en connaissance de cause.</p>

<h2>Notre position en boutique</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous accueillons volontiers ces demandes sans en faire un argument de vente. Nous expliquons ce qui est possible, ce qui ne l'est pas, et nous vérifions la compatibilité avec votre correction. Une monture connectée reste avant tout une monture&nbsp;: elle doit d'abord être bien réglée, bien portée, et vous ressembler.</p>
"""

ART_BODY_MATIERES_DURABLES = """
<h2>Que recouvre vraiment une lunette «&nbsp;durable&nbsp;»&nbsp;?</h2>
<p>Le mot est partout, et il ne veut pas dire grand-chose tant qu'on ne le décompose pas. Une monture réellement plus responsable joue sur trois leviers&nbsp;: la <strong>matière</strong> employée (biosourcée ou recyclée), le <strong>lieu et le mode de fabrication</strong> (proximité, conditions de production), et la <strong>réparabilité</strong>, c'est-à-dire la capacité à être remise en état plutôt que remplacée. C'est ce troisième critère, le plus concret et le plus vérifiable, qui pèse souvent le plus dans la durée de vie réelle d'une paire.</p>

<h2>Acétate biosourcé, matériaux recyclés&nbsp;: quelle différence ?</h2>
<p>L'acétate classique est déjà d'origine végétale, mais il est mis en œuvre avec des plastifiants d'origine fossile. Les acétates dits biosourcés remplacent une partie de ces composants par des dérivés végétaux&nbsp;: la matière se travaille et s'ajuste exactement comme un acétate ordinaire, et sa solidité dépend surtout de la qualité du montage. D'autres marques misent sur des matières recyclées — chutes de production, plastiques récupérés — ou sur des métaux au bilan mieux maîtrisé. Aucune de ces options n'est fragile par nature&nbsp;: la robustesse tient au montage et aux charnières, pas à l'étiquette.</p>

<h2>Comment éviter le greenwashing ?</h2>
<p>La règle est simple&nbsp;: demandez sur quoi porte exactement l'argument. «&nbsp;Éco-responsable&nbsp;» ne signifie rien s'il n'est pas rattaché à un fait précis — un pourcentage de matière recyclée, une certification portant sur un procédé, une fabrication localisée. Il n'existe pas de label unique couvrant toute la lunetterie&nbsp;; les marques s'appuient sur des certifications partielles, ce qui est légitime à condition de le dire clairement. Une marque sérieuse sait répondre à «&nbsp;durable en quoi&nbsp;?&nbsp;» sans détour.</p>

<h2>Le geste le plus écologique&nbsp;: garder sa monture</h2>
<p>Avant même la matière, le meilleur réflexe reste de faire durer. Un changement de plaquettes, un resserrage, un remplacement de branche ou de charnière coûte peu et prolonge une paire de plusieurs années. Quand une monture vous plaît encore et qu'elle est en bon état, il est souvent possible de n'y remonter que des verres neufs. Et pour les paires en fin de vie, des filières de collecte existent&nbsp;: réemploi solidaire pour les montures en bon état, valorisation des matières sinon.</p>

<h2>En boutique</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous réparons chaque fois que c'est techniquement possible, et nous le disons franchement quand une réparation n'a plus de sens. Nous vous orientons vers les gammes responsables lorsqu'elles existent dans les marques que nous présentons, sans en faire un argument automatique&nbsp;: la monture la plus durable, c'est d'abord celle que vous porterez longtemps parce qu'elle vous va.</p>
"""

ART_BODY_JOURNEE_TYPE = """<h2>À quoi ressemble le début d'une journée en boutique ?</h2>
<p>Peu avant dix heures, la galerie de Grand Angle s'éveille&nbsp;: les rideaux se lèvent, l'esplanade se remplit, et la boutique s'ouvre sur les mêmes gestes chaque matin — allumer, vérifier les commandes arrivées, préparer les paires à récupérer. Les premiers visiteurs sont souvent des habitués&nbsp;: quelqu'un qui passe chercher ses lunettes, un autre qui veut faire resserrer une branche avant d'aller travailler. Rien de spectaculaire, et c'est très bien ainsi&nbsp;: une boutique de quartier vit d'abord de ces petits passages.</p>

<h2>Une clientèle à l'image du quartier</h2>
<p>Entre dix heures et dix-neuf heures trente, du lundi au samedi, le rythme est imprévisible. Certains jours, ce sont surtout des habitués qui viennent dire bonjour&nbsp;; d'autres, des visages nouveaux, poussés par une ordonnance qui expire, une paire cassée le matin même ou l'envie de changer de style. Le Cœur de Ville de Montreuil est à la fois très actif et résidentiel, et cela se lit au comptoir&nbsp;: familles, actifs pressés entre deux rendez-vous, étudiants, retraités du quartier. Nous ne cherchons pas à lisser ces variations&nbsp;: nous vivons au rythme de ceux qui poussent la porte.</p>

<h2>Le cœur du métier : l'essayage et le conseil</h2>
<p>L'essentiel d'une journée se joue devant le miroir. Nous observons la morphologie — largeur du visage, hauteur du nez, position des oreilles — mais nous regardons tout autant comment la personne bouge, parle et sourit avec ses lunettes sur le nez. Une monture parfaite en vitrine peut ne plus rien vouloir dire dès que son porteur redevient lui-même. Avec la sélection de marques présentes en boutique, de Ray-Ban à Dior en passant par Prada ou Burberry, il y a presque toujours plusieurs pistes crédibles pour une même envie. Notre rôle n'est pas d'orienter vers une marque plutôt qu'une autre, mais d'aider chacun à se reconnaître dans la glace.</p>

<h2>Les gestes techniques qu'on ne voit pas</h2>
<p>Entre deux essayages, la journée est faite de tâches plus discrètes&nbsp;: un examen de vue sans rendez-vous dans l'espace dédié, le centrage et le montage des verres, l'ajustement d'une paire qui glisse, une réparation rapide, l'établissement d'un devis normalisé. Beaucoup passent d'abord faire chiffrer une idée, repartent avec leur devis, puis reviennent une fois leur mutuelle consultée&nbsp;: c'est l'usage normal, et nous le préférons à une décision prise dans la précipitation.</p>

<h2>Fermer, et recommencer</h2>
<p>À dix-neuf heures trente, la boutique referme sur un rangement rapide et les dernières commandes à passer. Ce qui reste d'une journée, ce ne sont pas les chiffres&nbsp;: ce sont les visages, ceux qu'on reverra, et cette idée simple qui tient tout le métier — être, demain encore, l'opticien du quartier à qui l'on revient.</p>
"""

ART_BODY_COEUR_DE_VILLE = """
<h2>Un nouveau centre-ville, né face à la mairie</h2>
<p>Certains quartiers changent de visage en quelques années : le Cœur de Ville de Montreuil en fait partie. À deux pas de l'hôtel de ville et de la station de métro Mairie de Montreuil (ligne&nbsp;9), cette vaste opération d'aménagement a redessiné le centre autour d'une idée simple — réunir au même endroit les commerces, le logement et la culture, à ciel ouvert. En décembre&nbsp;2012, l'espace commercial Grand Angle y ouvre ses portes : une douzaine de milliers de mètres carrés organisés autour de trois places et d'une rue piétonne, avec une trentaine de boutiques, de restaurants et de services.</p>
<p>Autour de cette galerie à l'air libre, le projet a réuni ce qui fait un morceau de ville : des logements, une résidence pour étudiants et jeunes actifs, une crèche, un vaste parking, et, un peu plus tard, le nouveau cinéma municipal Le Méliès et ses six salles, à quelques pas. Le tout à côté du marché et de la mairie, dans l'un des secteurs les plus vivants de Montreuil.</p>

<h2>ACTU EYES, une enseigne des premiers jours</h2>
<p>Nous en parlons parce que nous y étions. ACTU EYES fait partie des enseignes présentes dès l'ouverture de Grand Angle, en 2012 : la boutique a grandi avec le quartier, a vu les places se remplir, les habitudes se créer, les familles revenir. En 2018, Mikhael reprend le magasin et lui donne une nouvelle direction — d'autres marques, une autre ambiance, un conseil plus proche — sans jamais quitter cet emplacement qui fait tout le sel du lieu : un pied dans un centre moderne, l'autre dans une vraie vie de quartier.</p>
<p>Être opticien ici, ce n'est pas tenir une boutique anonyme dans une galerie. C'est croiser les mêmes visages au fil des saisons, ajuster une paire entre deux courses, reconnaître l'étudiant de la résidence voisine venu pour sa première monture comme le retraité qui passe dire bonjour. Le quartier est à la fois très actif — bureaux, transports, cinéma, marché — et résidentiel, et notre clientèle lui ressemble : de tous les âges et de tous les horizons.</p>

<h2>Se repérer et venir nous voir</h2>
<p>On rejoint Grand Angle le plus simplement par le métro ligne&nbsp;9, station Mairie de Montreuil, à quelques minutes à pied. En voiture, le parking du centre facilite les visites, y compris pour récupérer une commande ou faire réajuster une monture en quelques minutes. Une fois sur place, on nous trouve parmi les boutiques de la galerie, à l'enseigne ACTU EYES — « Votre Opticien ».</p>
<p>Ce qui ne change pas d'une année sur l'autre, c'est notre manière de travailler : l'examen de vue est gratuit et sans rendez-vous, le devis est toujours détaillé et remis avant tout engagement, et l'offre 100&nbsp;% Santé figure sur chacun d'eux. Le reste — le temps passé à l'essayage, l'attention portée à ce qui vous va vraiment — c'est ce que nous devons, depuis le premier jour, à un quartier qui nous a fait une place.</p>
"""

ART_BODY_ECRANS_MYOPIE_ENFANT = """
<h2>Pourquoi la myopie progresse-t-elle chez les enfants ?</h2>
<p>La myopie infantile augmente partout dans le monde, et l'évolution des modes de vie y est pour beaucoup. Deux facteurs reviennent dans toutes les études&nbsp;: le temps passé en vision de près — écrans, lecture, devoirs — et, surtout, le <strong>manque de lumière naturelle</strong>. Passer beaucoup de temps à l'intérieur, l'œil sollicité de près, favorise l'allongement du globe oculaire qui caractérise la myopie. Ce n'est pas l'écran seul qui est en cause, mais l'ensemble d'un quotidien tourné vers le proche et l'intérieur.</p>

<h2>La lumière du jour, une protection sous-estimée</h2>
<p>C'est le point le plus encourageant&nbsp;: passer du temps dehors protège. Les recommandations qui font consensus évoquent environ <strong>deux heures par jour à l'extérieur</strong>, à la lumière naturelle, pour freiner l'apparition et la progression de la myopie chez l'enfant. Peu importe l'activité — jouer, marcher, faire du sport&nbsp;: c'est l'exposition à la lumière du jour et la vision de loin qui comptent. Un réflexe simple, gratuit, et efficace.</p>

<h2>Quelles habitudes adopter à la maison ?</h2>
<ul>
  <li><strong>La règle des 20-20-20&nbsp;:</strong> toutes les 20&nbsp;minutes d'écran ou de lecture, regarder au loin pendant 20&nbsp;secondes.</li>
  <li><strong>La bonne distance&nbsp;:</strong> ne pas coller le livre ou la tablette&nbsp;; garder une distance raisonnable et une posture droite.</li>
  <li><strong>De la lumière&nbsp;:</strong> lire et travailler dans une pièce bien éclairée, et privilégier le jour à l'extérieur.</li>
  <li><strong>Des écrans encadrés&nbsp;:</strong> limiter la durée, surtout chez les plus jeunes, et éviter les écrans le soir.</li>
</ul>

<h2>Quand consulter, et existe-t-il des solutions ?</h2>
<p>Tout signe qui se répète — se rapprocher, plisser, se plaindre de mal voir de loin — justifie un examen chez l'ophtalmologiste, seul habilité à corriger la vue d'un enfant. Au-delà des lunettes, il existe aujourd'hui des solutions de <strong>freination de la myopie</strong> (verres et lentilles spécifiques, parfois collyre) que le médecin peut proposer selon les cas. L'objectif n'est pas seulement de corriger, mais de ralentir la progression pour limiter la myopie à l'âge adulte.</p>

<h2>Notre rôle à vos côtés</h2>
<p>À ACTU EYES, au centre Grand Angle à Montreuil, nous recevons beaucoup de familles du quartier. Nous n'examinons pas la vue des enfants — cela relève de l'ophtalmologiste — mais nous équipons, réglons et suivons les jeunes porteurs avec le soin qu'exige un petit visage, et nous relayons volontiers les bons réflexes du quotidien. La meilleure prévention reste à la portée de tous&nbsp;: de la lumière, du dehors, et des pauses.</p>
"""


ART_BODY_CHOIX_MONTURES = """<h2>Une sélection, pas un catalogue</h2>
<p>On pourrait remplir des murs entiers de montures. Nous avons fait le choix inverse&nbsp;: présenter une sélection resserrée, composée modèle par modèle, plutôt qu'un catalogue sans fin où l'on se perd. Chaque paire accrochée en boutique y est parce que nous la connaissons — sa tenue dans le temps, la qualité de ses charnières, le sérieux du fabricant derrière. C'est plus exigeant à constituer, mais beaucoup plus honnête au moment du conseil.</p>

<h2>Nos trois critères&nbsp;: qualité, variété, plaisir d'essayage</h2>
<p>Une monture entre chez nous si elle coche trois cases. La qualité d'abord&nbsp;: matières, finitions, solidité des branches et des charnières, confort sur le nez. La variété ensuite&nbsp;: il nous faut de quoi habiller tous les visages, tous les styles et tous les budgets, du plus sage au plus affirmé. Le plaisir d'essayage enfin&nbsp;: une belle monture doit donner envie de se regarder dans le miroir, pas seulement cocher une norme technique.</p>

<h2>Grandes maisons et créateurs indépendants</h2>
<p>Notre sélection fait cohabiter de grandes maisons — celles que tout le monde connaît, rassurantes et intemporelles — avec des créateurs plus confidentiels, souvent européens, qui travaillent des formes et des couleurs qu'on ne voit pas partout. Ce mélange, c'est un peu notre signature&nbsp;: permettre à quelqu'un qui vient chercher une paire classique de repartir, s'il le souhaite, avec un modèle qui a un vrai parti pris. Vous retrouvez l'ensemble de ces maisons sur notre page dédiée aux marques.</p>

<h2>Le beau à petit prix, un engagement</h2>
<p>À côté des marques haut de gamme, nous gardons toujours un large choix de montures abordables et vraiment bien dessinées. Ce n'est pas un rayon de second plan&nbsp;: c'est un engagement. Personne ne devrait renoncer à une paire qui lui plaît à cause de son budget, et le 100&nbsp;% Santé permet même un équipement complet sans reste à charge. Notre métier, c'est de trouver la bonne monture dans l'enveloppe de chacun, pas de pousser à dépenser plus.</p>

<h2>Ce que l'expérience du comptoir nous apprend</h2>
<p>Aucune fiche technique ne remplace des années de comptoir. À force de voir des paires revenir — ou ne jamais revenir — on sait quels modèles vieillissent bien, quelles charnières lâchent, quels acétates gardent leur couleur. Cette mémoire du terrain guide nos commandes autant que les tendances&nbsp;: nous préférons réréférencer un modèle qui a fait ses preuves plutôt que courir après la nouveauté du moment. Au fond, choisir vos montures, c'est déjà prendre soin de vous.</p>"""


ART_BODY_ATELIER = """<h2>L'atelier, cœur invisible du métier</h2>
<p>Le conseil et l'essayage se voient&nbsp;; l'atelier, beaucoup moins. C'est pourtant là, derrière le comptoir, qu'une paire de lunettes prend réellement vie. Une jolie monture et de bons verres ne suffisent pas&nbsp;: encore faut-il les assembler avec précision et les régler sur un visage. Ce travail discret fait toute la différence entre des lunettes qu'on oublie de confort et des lunettes qui gênent sans qu'on sache pourquoi.</p>

<h2>Du centrage au taillage&nbsp;: la précision d'abord</h2>
<p>Tout commence par des mesures. Nous relevons l'écart entre vos pupilles et la hauteur de votre regard dans la monture choisie, pour que le centre optique de chaque verre tombe exactement devant l'œil. Quelques millimètres d'erreur suffisent à fatiguer la vision, surtout en progressif. Ces mesures partent ensuite en taillage&nbsp;: le verre est détouré à la forme précise de la monture, biseauté, puis inséré et vérifié. C'est un travail d'orfèvre, au dixième de millimètre.</p>

<h2>L'ajustement, ce détail qui change tout</h2>
<p>Une fois montées, les lunettes se règlent sur vous&nbsp;: cintrage des branches derrière l'oreille, ouverture des plaquettes, inclinaison de la face. Une monture bien ajustée tient sans serrer, ne glisse pas et place les verres à la bonne distance des yeux. Ce réglage n'est jamais définitif&nbsp;: le temps, la chaleur, les gestes du quotidien le déforment. Nous le reprenons autant de fois qu'il le faut, gratuitement — c'est le prolongement normal de la vente.</p>

<h2>Les petites réparations du quotidien</h2>
<p>Une vis qui saute, une plaquette jaunie, une branche desserrée&nbsp;: ce sont les visites les plus fréquentes, et souvent les plus rapides. La plupart de ces gestes se règlent sur place, en quelques minutes, fréquemment sans rien débourser. Nous le faisons volontiers, y compris sur des paires qui n'ont pas été achetées chez nous&nbsp;: c'est une manière simple de rendre service et de faire connaissance.</p>

<h2>Quand une paire semble perdue</h2>
<p>Même une monture cassée mérite qu'on l'examine avant de la déclarer perdue. Selon la casse, on répare, on remplace une pièce, ou l'on remonte vos verres encore bons sur une nouvelle monture — souvent la solution la plus économique. L'objectif est toujours le même&nbsp;: éviter de vous laisser sans lunettes, ne serait-ce qu'un jour. Passer la porte de l'atelier, c'est repartir en voyant clair.</p>"""


ARTICLES = [
    {
        "slug": "fatigue-oculaire-ecrans",
        "category": "sante-visuelle",
        "title": "Écrans et fatigue oculaire : comment protéger sa vue au quotidien",
        "meta_title": "Fatigue oculaire et écrans : que faire ? | ACTU EYES",
        "meta_description": "Sécheresse, maux de tête, vision brouillée : les causes réelles de la fatigue visuelle sur écran, ce que valent les verres anti-lumière bleue et ce qui aide.",
        "excerpt": "Sécheresse, maux de tête, vision qui se brouille : pourquoi les écrans fatiguent nos yeux, et ce qui aide vraiment.",
        "answer": "La fatigue oculaire sur écran vient de deux causes : on cligne des yeux jusqu'à 60&nbsp;% moins souvent, ce qui assèche le film lacrymal, et le muscle d'accommodation reste contracté des heures. La lumière bleue n'en est pas la cause principale. Pauses 20-20-20, écran à 50-70&nbsp;cm et correction à jour suffisent dans la plupart des cas.",
        "faq": [
            ("Combien de temps faut-il pour que la fatigue oculaire disparaisse ?",
             "Avec de bons réglages — pauses régulières, écran reculé, larmes artificielles — la plupart des gens ressentent une nette amélioration en une à deux semaines. Si rien ne bouge au bout de trois semaines, la cause est probablement optique : correction inadaptée, astigmatisme non corrigé ou presbytie qui démarre."),
            ("Les écrans peuvent-ils abîmer définitivement les yeux ?",
             "Chez l'adulte, aucune donnée ne montre que le travail sur écran provoque une lésion durable : la fatigue visuelle est réversible. Chez l'enfant, c'est différent — le temps passé en vision de près et le manque de lumière du jour favorisent la progression de la myopie."),
            ("Faut-il des lunettes spéciales pour l'ordinateur ?",
             "Pas systématiquement avant 40 ans, si la correction est à jour. Après 40-45 ans, des verres à faible dégression, dits verres bureau, élargissent la zone nette entre 40&nbsp;cm et 2&nbsp;m : c'est souvent un vrai soulagement pour ceux qui alternent écran, clavier et échanges en face à face."),
            ("Le mode nuit de mon téléphone remplace-t-il un verre traité ?",
             "Le mode nuit réduit la lumière bleue émise en soirée, ce qui peut aider au sommeil. Il n'agit pas sur la fatigue visuelle, dont la cause est ailleurs. C'est le traitement antireflet des verres, et non le filtre bleu, qui apporte un gain de confort mesurable devant un écran."),
            ("Peut-on utiliser des larmes artificielles tous les jours ?",
             "Oui, à condition de choisir une formule sans conservateur, en unidoses ou en flacon à valve stérile. Utilisés plusieurs fois par jour pendant des mois, les conservateurs finissent par irriter la surface de l'œil. Si la sécheresse persiste malgré cela, un avis ophtalmologique est préférable."),
        ],
        "sources": [
            ("Asnav", "https://www.asnav.org/"),
            ("INRS — travail sur écran", "https://www.inrs.fr/risques/travail-ecran.html"),
            ("Ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/article-fatigue-ecrans.jpg",
        "image_alt": "Lunette d'essai et verres de correction sur le plan de travail d'un opticien",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_FATIGUE,
    },
    {
        "slug": "tendances-montures-2026",
        "category": "mode-lunettes",
        "title": "Tendances montures 2026 : quelles formes et couleurs privilégier",
        "meta_title": "Tendances lunettes 2026 : formes & couleurs | ACTU EYES",
        "meta_description": "Formes géométriques, papillon revisité, écaille intemporelle, métal fin : le tour d'horizon des tendances lunettes 2026 et comment savoir ce qui vous ira.",
        "excerpt": "Formes géométriques, retour du papillon, écaille intemporelle : le tour d'horizon des tendances lunettes 2026.",
        "answer": "En 2026, les formes géométriques et le papillon revisité côtoient les rondes réinterprétées et les modèles oversize. L'acétate domine, avec l'écaille en tête et une percée des teintes translucides, tandis que le métal fin porte un style minimaliste et que les tons neutres s'imposent.",
        "faq": [
            ("Une monture tendance se démode-t-elle plus vite ?",
             "Parfois, oui. Les formes très marquées, comme les modèles oversize ou architecturaux, se datent plus facilement que les silhouettes classiques. Si vous ne changez de lunettes que tous les deux ou trois ans, il peut être judicieux de garder une forme sobre pour la paire principale et d'oser davantage sur une seconde paire."),
            ("Peut-on porter des verres teintés toute la journée ?",
             "Une teinte légère se porte au quotidien sans difficulté particulière, y compris en intérieur, et beaucoup la trouvent reposante. En revanche, une teinte soutenue destinée au soleil n'a pas d'intérêt à l'intérieur et gêne la perception des couleurs. Nous vous faisons comparer plusieurs intensités avant de trancher."),
            ("Combien coûte une monture à la mode ?",
             "Les écarts sont importants selon la matière, la marque et la finition, et nous préférons ne pas donner de fourchette générale qui serait trompeuse. Le devis remis en boutique détaille le prix de la monture et celui des verres séparément, avec l'offre 100 % Santé, ce qui permet de comparer sereinement."),
            ("Faut-il changer de monture à chaque nouvelle ordonnance ?",
             "Non. Si votre monture est en bon état et que sa forme accepte la nouvelle correction, il est tout à fait possible de n'y remonter que des verres neufs. Nous vérifions l'état des charnières, du face et des branches avant de vous le proposer, car une monture fatiguée supporte mal un remontage."),
            ("Les montures mixtes conviennent-elles vraiment à tout le monde ?",
             "Elles élargissent le choix, ce qui est déjà beaucoup, mais elles n'annulent pas les différences de morphologie. La largeur du visage, la hauteur du nez et l'écart entre les yeux restent les critères déterminants. Une monture dite mixte peut donc très bien convenir à une personne et pas du tout à une autre."),
        ],
        "sources": [
            ("Asnav — Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-tendances-2026.jpg",
        "image_alt": "Trois femmes de profil portant des lunettes de soleil teintées tendance",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_MONTURES_2026,
    },
    {
        "slug": "nouvelles-technologies-verres-correcteurs",
        "category": "tech-verres",
        "title": "Verres correcteurs : les innovations qui changent le quotidien",
        "meta_title": "Innovations des verres correcteurs 2026 | ACTU EYES",
        "meta_description": "Freination de la myopie chez l'enfant, photochromiques plus rapides, surfaçage sur mesure : ce qui a vraiment changé dans les verres correcteurs.",
        "excerpt": "Freination de la myopie, photochromiques nouvelle génération, verres bureau : le point sur les vraies innovations.",
        "answer": "Trois avancées comptent réellement : des verres capables de ralentir la progression de la myopie chez l'enfant, des photochromiques nettement plus réactifs, et un surfaçage numérique personnalisé. Les filtres anti-lumière bleue, eux, se sont affinés mais ne remplacent ni les pauses ni un poste de travail bien réglé.",
        "faq": [
            ("Les verres de freination sont-ils remboursés ?",
             "Ils relèvent le plus souvent de la classe à prix libres, et la prise en charge dépend donc de votre complémentaire santé. Certains contrats prévoient un forfait spécifique pour l'enfant, d'autres non. Demandez un devis normalisé et interrogez votre mutuelle avant de commander : les écarts entre contrats sont importants."),
            ("Un adulte myope peut-il porter des verres de freination ?",
             "Non, ces verres sont conçus pour la période de croissance de l'œil, chez l'enfant et l'adolescent. Chez l'adulte, l'œil a cessé de s'allonger dans la très grande majorité des cas et la freination n'a plus d'objet. Une correction classique bien ajustée reste la bonne réponse."),
            ("Faut-il changer de verres dès qu'une nouvelle technologie sort ?",
             "Rarement. Un verre en bon état, avec une correction toujours adaptée, n'a pas besoin d'être remplacé parce qu'une gamme plus récente est arrivée. Les vrais motifs de renouvellement restent l'évolution de la correction, l'usure des traitements et une gêne persistante que la paire actuelle ne règle pas."),
            ("Combien de temps faut-il pour s'habituer à un verre progressif ?",
             "Cela varie beaucoup d'une personne à l'autre : certains porteurs sont à l'aise immédiatement, d'autres ont besoin de plusieurs jours. Portez la paire en continu plutôt que par intermittence, et revenez si la gêne persiste. Un ajustement de centrage ou de monture règle une bonne partie des cas."),
            ("Les traitements antireflets s'abîment-ils avec le temps ?",
             "Oui, comme toute couche de surface. Un nettoyage à sec, avec un mouchoir ou un pan de chemise, use prématurément le traitement et crée un voile de micro-rayures. Rincez à l'eau tiède, séchez avec un tissu microfibre propre, et faites vérifier vos verres lors de vos passages en boutique."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Essilor France", "https://www.essilor.fr/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-innovations-verres.jpg",
        "image_alt": "Verres correcteurs colorés, illustration des innovations optiques",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_TECH_VERRES,
    },
    {
        "slug": "nouvelles-technologies-lentilles-contact",
        "category": "tech-lentilles",
        "title": "Lentilles de contact : les nouveautés à connaître",
        "meta_title": "Nouvelles technologies des lentilles | ACTU EYES",
        "meta_description": "Matériaux plus respirants, lentilles freinatrices de myopie chez l'enfant, prototypes connectés : ce qui a changé et ce qui reste du laboratoire.",
        "excerpt": "Matériaux nouvelle génération, freination de la myopie chez l'enfant, prototypes connectés : le point sur les vraies nouveautés.",
        "answer": "Les vraies avancées récentes portent sur trois points : des matériaux en silicone-hydrogel plus respirants et mieux hydratés, des lentilles souples journalières capables de ralentir la progression de la myopie chez l'enfant, et une offre élargie pour l'astigmatisme et la presbytie. Les lentilles connectées, elles, restent expérimentales.",
        "faq": [
            ("Peut-on dormir avec ses lentilles de contact ?",
             "Sauf lentille spécifiquement prescrite pour le port nocturne, comme en orthokératologie, la réponse est non. Dormir avec une lentille classique réduit fortement l'oxygénation de la cornée et augmente le risque d'infection. Si cela vous arrive par accident, retirez la lentille et surveillez l'apparition d'une rougeur ou d'une douleur."),
            ("Une lentille journalière peut-elle être portée deux jours de suite ?",
             "Non, jamais. Une journalière est conçue pour un seul port puis la poubelle : son matériau et sa surface ne sont pas prévus pour supporter un cycle d'entretien. La réutiliser expose à des dépôts, à une gêne et à un risque infectieux, y compris si la lentille paraît en parfait état."),
            ("Faut-il une ordonnance pour acheter des lentilles ?",
             "Oui. La délivrance de lentilles correctrices repose sur une prescription d'un ophtalmologiste, qui précise la correction et le type de lentille. L'opticien procède ensuite à l'adaptation et au suivi. Une ordonnance de lunettes ne suffit pas : les valeurs ne sont pas transposables telles quelles."),
            ("Les lentilles conviennent-elles après 50 ans ?",
             "Souvent oui. Les designs multifocaux actuels rendent le port possible pour beaucoup de presbytes, parfois en complément d'une paire de lunettes pour les tâches longues de près. La sécheresse oculaire, plus fréquente avec l'âge, est le vrai facteur limitant : elle se vérifie lors de l'essai."),
            ("Peut-on porter des lentilles quand on est allergique au pollen ?",
             "C'est possible, mais la lentille journalière est alors nettement préférable : elle repart chaque soir avec les allergènes déposés dessus. En période de forte gêne, mieux vaut réduire la durée de port ou revenir temporairement aux lunettes, et en parler à votre médecin."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Alcon France", "https://www.alcon.com/fr-fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-lentilles-nouveautes.jpg",
        "image_alt": "Femme posant une lentille de contact sur le bout de son doigt",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_TECH_LENTILLES,
    },
    {
        "slug": "100-pour-cent-sante-2026",
        "category": "remboursements",
        "title": "100 % Santé lunettes en 2026 : ce qui est pris en charge",
        "meta_title": "100 % Santé lunettes 2026 : reste à charge 0 | ACTU EYES",
        "meta_description": "Monture plafonnée à 30 €, verres traités, classes A et B, renouvellement, devis normalisé : ce que couvre le 100 % Santé en optique, sans reste à charge.",
        "excerpt": "Reste à charge 0, classes A et B, devis normalisé : ce que le 100 % Santé couvre vraiment sur vos lunettes en 2026.",
        "answer": "En optique, le 100 % Santé garantit un reste à charge nul sur un équipement de classe A : monture plafonnée à 30 € et verres traités (amincis, antireflet, anti-rayure). Deux conditions : une complémentaire santé responsable et le choix d'un équipement de classe A. Vous pouvez aussi panacher avec la classe B, à prix libre.",
        "faq": [
            ("Le 100 % Santé est-il vraiment gratuit ?",
             "Oui, si vous avez une complémentaire santé responsable — la très grande majorité des contrats — et si vous choisissez un équipement de classe A. Vous ne réglez alors rien. Sans complémentaire, l'Assurance Maladie seule ne couvre qu'une part réduite."),
            ("Les lunettes 100 % Santé sont-elles de moins bonne qualité ?",
             "Les verres de classe A intègrent obligatoirement l'amincissement adapté à la correction, un traitement antireflet et un anti-rayure : la qualité optique est celle d'un verre courant. La différence porte surtout sur le choix de montures, plus restreint, et sur des options comme les verres photochromiques."),
            ("Peut-on mélanger classe A et classe B ?",
             "Oui, et c'est courant. Vous pouvez prendre une monture de classe B avec des verres de classe A, ou l'inverse. Le devis indique alors clairement quel élément relève de quelle classe et le reste à charge correspondant, ligne par ligne."),
            ("Tous les combien peut-on en bénéficier ?",
             "La prise en charge d'un équipement complet est prévue tous les deux ans à partir de 16 ans, et tous les ans avant 16 ans. Ce délai peut être raccourci en cas d'évolution de la vue justifiée par une nouvelle ordonnance."),
            ("Mon ordonnance est-elle encore valable ?",
             "Une ordonnance de lunettes est valable 1 an avant 16 ans, 5 ans de 16 à 42 ans et 3 ans au-delà. Dans ces délais, l'opticien peut adapter la correction sans repasser par l'ophtalmologiste."),
        ],
        "sources": [
            ("Ameli — 100 % Santé", "https://www.ameli.fr/assure/remboursements/rembourse/optique-audition-dentaire/100-sante"),
            ("Service-Public.fr", "https://www.service-public.fr/"),
            ("Légifrance", "https://www.legifrance.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-100-sante.jpg",
        "image_alt": "Logo du dispositif 100 % Santé en optique",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_REMBOURSEMENTS,
    },
    {
        "slug": "reprise-actueyes-histoire-opticien-montreuil",
        "category": "vie-boutique",
        "title": "ACTU EYES : l'histoire d'une reprise à Montreuil",
        "meta_title": "ACTU EYES Montreuil : notre histoire, notre équipe",
        "meta_description": "Repris en 2018 par Mikhael, rejoint par Sudaya en 2021 : l'histoire d'ACTU EYES, opticien de quartier au centre Grand Angle, à Montreuil.",
        "excerpt": "Une reprise en 2018, une rencontre en 2021, un partenariat en 2025 : l'histoire d'ACTU EYES, racontée par ceux qui la font.",
        "answer": "ACTU EYES a été reprise en 2018 par Mikhael, qui l'a réinventée avec de nouvelles marques et un conseil plus proche. Sudaya rejoint l'équipe en 2021 ; en 2023, tous deux ouvrent une seconde enseigne à Paris, et en 2025 Sudaya devient associé d'ACTU EYES Montreuil.",
        "faq": [
            ("Depuis quand ACTU EYES existe-t-elle à Montreuil ?",
             "La boutique fait partie des enseignes du centre Grand Angle depuis son ouverture, en 2012. Elle a été reprise par Mikhael en 2018, qui lui a donné une nouvelle direction au même emplacement."),
            ("Quel est le positionnement de la boutique ?",
             "Des marques haut de gamme, mais un large choix de montures abordables et belles, avec le service client comme priorité : prendre le temps, écouter, et proposer ce qui convient vraiment à chacun."),
            ("Qui sont les associés d'ACTU EYES ?",
             "Mikhael, qui a repris la boutique en 2018, et Sudaya, arrivé en 2021 et devenu associé d'ACTU EYES Montreuil en 2025. Ils tiennent aussi une seconde enseigne à Paris depuis 2023."),
            ("Faut-il un rendez-vous pour venir ?",
             "Non pour un essayage, un ajustement, une réparation, un devis ou un examen de vue : tout cela se fait sans rendez-vous, du lundi au samedi, de 10 h à 19 h 30."),
        ],
        "sources": [
            ("Grand Angle Montreuil", "https://www.montreuil-grandangle.com/"),
            ("Ville de Montreuil", "https://www.montreuil.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-vitrine-prada.jpg",
        "image_alt": "Vitrine de la boutique ACTU EYES à Montreuil",
        "date_display": "5 février 2026",
        "date_iso": "2026-02-05",
        "body": ART_BODY_VIE_BOUTIQUE,
    },
    {
        "slug": "signes-troubles-visuels-enfant",
        "category": "enfant",
        "title": "Troubles visuels de l'enfant : les signes à repérer",
        "meta_title": "Troubles visuels de l'enfant : les signes | ACTU EYES",
        "meta_description": "Se frotter les yeux, se rapprocher des écrans, plisser, sauter des lignes : les signes d'un trouble visuel chez l'enfant et à quel âge consulter.",
        "excerpt": "Un enfant ne dit pas qu'il voit mal : il le montre. Les comportements à repérer, et à quel âge consulter.",
        "answer": "Un enfant qui plisse les yeux, se rapproche des écrans, saute des lignes en lisant, penche la tête ou se plaint de maux de tête peut avoir un trouble visuel. Ces signes justifient un examen chez l'ophtalmologiste : avant 16 ans, lui seul peut prescrire une correction.",
        "faq": [
            ("À quel âge faire contrôler la vue de son enfant ?",
             "Des dépistages sont prévus dans les premiers mois, vers 3-4 ans et à l'entrée en primaire. Au moindre signe entre ces étapes, un examen chez l'ophtalmologiste est recommandé sans attendre."),
            ("L'opticien peut-il corriger la vue d'un enfant sans ordonnance ?",
             "Non. Avant 16 ans, l'adaptation d'une correction relève obligatoirement de l'ophtalmologiste. L'opticien intervient ensuite pour l'équipement, le réglage et le suivi de la monture."),
            ("Mon enfant voit-il mal s'il se tient près de la télévision ?",
             "Ce n'est pas systématique, mais c'est un signe fréquent de myopie débutante lorsqu'il se répète. Associé à d'autres comportements (plisser, se frotter les yeux), il justifie un examen."),
            ("Une correction non portée est-elle grave chez l'enfant ?",
             "Elle peut l'être : un défaut non corrigé tôt risque d'installer une amblyopie, un œil qui « décroche » durablement. D'où l'importance du dépistage et d'une paire réellement portée, donc confortable."),
            ("Comment choisir une monture pour un enfant ?",
             "Légère, résistante, bien centrée et bien réglée pour tenir en mouvement. Nous privilégions des matières souples et revoyons l'enfant pour réajuster au fil de sa croissance."),
        ],
        "sources": [
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Haute Autorité de Santé", "https://www.has-sante.fr/"),
            ("Santé publique France", "https://www.santepubliquefrance.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-enfant-depistage.jpg",
        "image_alt": "Enfant passant un dépistage visuel chez le spécialiste",
        "date_display": "26 juillet 2026",
        "date_iso": "2026-07-26",
        "body": ART_BODY_ENFANT,
    },
    {
        "slug": "lentilles-hebdomadaires-precision7-alcon",
        "category": "tech-lentilles",
        "title": "Lentilles hebdomadaires : la nouveauté Precision7 d'Alcon change la donne",
        "meta_title": "Lentilles hebdomadaires Precision7 : le point | ACTU EYES",
        "meta_description": "Ni journalière, ni mensuelle : Precision7 se renouvelle chaque semaine. Ce que cela change pour l'entretien, le confort et votre budget.",
        "excerpt": "Entre la journalière et la mensuelle, une troisième fréquence de renouvellement apparaît : la lentille changée chaque semaine.",
        "answer": "Precision7 est présentée par Alcon comme la première lentille souple conçue pour un renouvellement hebdomadaire. Elle occupe une place intermédiaire entre la journalière, jetée chaque soir, et la mensuelle. Elle demande un entretien quotidien, et son adaptation passe toujours par une prescription puis un essai accompagné.",
        "faq": [
            ("Peut-on garder une lentille hebdomadaire plus de sept jours ?",
             "Non. Le cycle de remplacement fait partie de la conception de la lentille et ne se négocie pas au ressenti. Une lentille conservée au-delà accumule dépôts et micro-lésions, ce qui augmente le risque d'irritation et d'infection, même si le confort paraît encore acceptable."),
            ("Ce rythme revient-il moins cher que la journalière ?",
             "En port quotidien, un rythme de renouvellement plus long revient généralement moins cher sur l'année, solution d'entretien comprise. En port occasionnel, l'avantage disparaît, car la lentille vieillit même sans être portée. Le calcul se fait sur votre usage réel, pas sur le prix de la boîte."),
            ("Que se passe-t-il si j'oublie un soir de retirer ma lentille ?",
             "Retirez-la dès que possible et laissez votre œil au repos, sans lentille, pendant quelques heures. Surveillez toute rougeur, douleur, sensation de corps étranger ou baisse de vision : ces signes imposent une consultation rapide. Un oubli isolé n'est pas une catastrophe, mais l'habitude en est une."),
            ("Peut-on passer directement de la mensuelle à ce rythme sans avis ?",
             "Non. Tout changement de type de lentille passe par une nouvelle prescription et un essai vérifié par un professionnel. Les paramètres ne sont pas transposables d'une gamme à l'autre, et une lentille commandée seule sur internet à partir d'anciennes valeurs expose à une mauvaise adaptation."),
            ("Peut-on nager ou se doucher avec ses lentilles ?",
             "Il vaut mieux l'éviter. L'eau de piscine, de mer et celle du robinet peuvent contenir des micro-organismes qui se fixent sur la lentille et provoquent des infections cornéennes sévères. Si vous nagez régulièrement, parlez-en : des lunettes de natation correctrices sont souvent la meilleure réponse."),
        ],
        "sources": [
            ("Alcon France", "https://www.alcon.com/fr-fr"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-lentilles-precision7.jpg",
        "image_alt": "Lunettes de vue entourées de lentilles de contact en blister",
        "date_display": "16 janvier 2025",
        "date_iso": "2025-01-16",
        "body": ART_BODY_ALCON_PRECISION7,
    },
    {
        "slug": "proteger-yeux-soleil-uv",
        "category": "sante-visuelle",
        "title": "Soleil et UV : comment bien protéger ses yeux en toute saison",
        "meta_title": "Protéger ses yeux du soleil et des UV | ACTU EYES",
        "meta_description": "Photokératite, cataracte, DMLA : les UV abîment aussi les yeux. Comment lire les catégories de filtration 0 à 4 et choisir une paire réellement protectrice.",
        "excerpt": "Le soleil n'agresse pas que la peau : les UV jouent aussi un rôle dans plusieurs atteintes oculaires, à court et à long terme.",
        "answer": "Les UV provoquent à court terme une photokératite, sorte de coup de soleil de la cornée, et contribuent à long terme au vieillissement du cristallin et à la cataracte. Pour un usage courant en extérieur, la catégorie 3 est celle que recommandent la plupart des professionnels de santé visuelle.",
        "faq": [
            ("Les lunettes de soleil vendues sur les marchés sont-elles sûres ?",
             "Tout dépend du marquage. Sans marquage CE ni indication de catégorie de filtration, rien ne garantit que le verre filtre les UV, et une teinte sombre non filtrante aggrave l'exposition en faisant dilater la pupille. En cas de doute, faites vérifier la paire par un professionnel avant de la porter."),
            ("Faut-il porter des lunettes de soleil en hiver ?",
             "Oui, surtout à la montagne et par temps de neige, où la réverbération est très forte et le risque de photokératite élevé. En ville, un soleil bas d'hiver éblouit aussi beaucoup, notamment au volant. La protection se raisonne selon la luminosité et la réverbération, pas selon la saison."),
            ("Des verres photochromiques suffisent-ils pour l'été ?",
             "Ils apportent un vrai confort en s'assombrissant selon la lumière, mais leur teinte maximale ne correspond pas toujours à celle d'une paire solaire dédiée, et ils foncent moins derrière un pare-brise. Pour la plage ou la montagne, une paire solaire réellement adaptée reste préférable."),
            ("Les lentilles de contact avec filtre UV dispensent-elles de lunettes ?",
             "Non. Une lentille ne couvre que la cornée et laisse la paupière ainsi que tout le pourtour de l'œil exposés aux rayons. Elle peut compléter la protection, jamais la remplacer. Une paire solaire correctement dimensionnée, et si possible enveloppante, reste indispensable dès que l'exposition devient importante."),
            ("Peut-on regarder une éclipse avec des lunettes de soleil ?",
             "Non, en aucun cas, quelle que soit la catégorie de filtration. L'observation directe du soleil exige des lunettes spécifiquement conçues et certifiées pour cet usage. Regarder une éclipse avec des lunettes de soleil ordinaires peut provoquer des lésions rétiniennes définitives et indolores sur le moment."),
        ],
        "sources": [
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/article-soleil-uv.jpg",
        "image_alt": "Boîte de verres d'essai d'un opticien",
        "date_display": "5 août 2025",
        "date_iso": "2025-08-05",
        "body": ART_BODY_UV_SOLEIL,
    },
    {
        "slug": "lentilles-rigides-asana-bausch-lomb",
        "category": "tech-lentilles",
        "title": "Lentilles rigides perméables au gaz : Bausch + Lomb lance sa gamme Asana",
        "meta_title": "Lentilles rigides : à qui elles s'adressent | ACTU EYES",
        "meta_description": "Kératocône, cornée irrégulière, astigmatisme fort : ce qu'apportent les lentilles rigides perméables au gaz, et comment se passe l'adaptation.",
        "excerpt": "Moins connues que les souples, les lentilles rigides perméables au gaz restent la solution de référence pour les cornées irrégulières.",
        "answer": "Les lentilles rigides perméables au gaz gardent une forme stable sur l'œil, ce qui leur permet de compenser une cornée irrégulière là où une lentille souple échoue. Elles sont surtout proposées en cas de kératocône, d'astigmatisme important ou après une chirurgie oculaire, et sont réalisées sur mesure.",
        "faq": [
            ("Les lentilles rigides font-elles mal ?",
             "Elles ne font pas mal, mais elles se sentent au début. La paupière perçoit le bord de la lentille pendant les premiers jours, avec parfois un larmoiement. Cette sensation diminue nettement avec l'habitude. Une douleur vraie, elle, n'est jamais normale et doit conduire à retirer la lentille et à consulter."),
            ("Combien de temps une lentille rigide se garde-t-elle ?",
             "Nettement plus longtemps qu'une lentille souple, mais pas indéfiniment. La durée dépend du matériau, de l'entretien et de l'évolution de votre cornée. Une lentille rayée, déformée ou qui ne donne plus la même netteté doit être remplacée, même si elle vous semble encore utilisable."),
            ("Peut-on faire du sport avec ?",
             "Oui pour la plupart des activités, avec une réserve pour les sports de contact et ceux où la lentille peut se déloger brutalement. Les sports aquatiques sont à éviter avec toute lentille, en raison du risque infectieux lié à l'eau. Parlez de votre pratique lors de l'adaptation."),
            ("Sont-elles remboursées ?",
             "La prise en charge des lentilles par l'Assurance Maladie est limitée à certaines indications médicales précises, sur prescription, et les complémentaires santé prévoient souvent un forfait annuel distinct de celui des lunettes. Le mieux reste de demander un devis et de vérifier votre tableau de garanties avant de vous engager."),
            ("Que faire si une lentille rigide se déplace sous la paupière ?",
             "Ne frottez pas votre œil. Clignez plusieurs fois, appliquez quelques gouttes de sérum physiologique et ramenez doucement la lentille vers le centre en massant la paupière fermée. Si elle reste bloquée ou si l'œil devient douloureux, faites-vous aider par un professionnel sans forcer."),
        ],
        "sources": [
            ("Bausch + Lomb", "https://www.bausch.com/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-lentilles-asana.jpg",
        "image_alt": "Étui, produit d'entretien et lunettes pour porteurs de lentilles de contact",
        "date_display": "9 septembre 2025",
        "date_iso": "2025-09-09",
        "body": ART_BODY_BL_ASANA,
    },
    {
        "slug": "lunettes-connectees-ray-ban-meta-mode-tech",
        "category": "mode-lunettes",
        "title": "Ray-Ban Meta : quand la lunette connectée devient un objet de mode",
        "meta_title": "Lunettes connectées Ray-Ban Meta : notre avis | ACTU EYES",
        "meta_description": "Caméra, assistant vocal, mini-écran dans le verre : ce que les lunettes connectées changent au choix d'une monture, et les questions à se poser.",
        "excerpt": "Entre caméra intégrée, assistant vocal et mini-écran dans le verre, la lunette connectée pose de nouvelles questions au moment de choisir sa monture.",
        "answer": "Les lunettes connectées Ray-Ban Meta sont des montures d'allure classique intégrant une caméra, des haut-parleurs open-ear et un assistant vocal. Elles changent surtout le rapport à la monture, portée du matin au soir, et posent des questions concrètes de confort, d'autonomie et de vie privée.",
        "faq": [
            ("Peut-on mettre des verres progressifs dans une lunette connectée ?",
             "Cela dépend entièrement du modèle et de votre correction, et seul le fabricant fait autorité sur ce point. La hauteur de verre disponible et l'épaisseur admissible sont plus contraintes que sur une monture classique. Apportez votre ordonnance : nous vérifions ensemble ce qui est réellement possible avant toute commande."),
            ("Peut-on les porter toute la journée ?",
             "Rien ne l'interdit, mais l'électronique ajoute du poids et l'autonomie reste limitée : beaucoup les réservent aux moments où leurs fonctions servent vraiment. Pour un port permanent et confortable, une monture correctrice classique reste souvent le meilleur choix."),
            ("Comment savoir si quelqu'un est en train de filmer avec ses lunettes ?",
             "Les fabricants annoncent un témoin lumineux signalant l'enregistrement, mais il est discret et peut échapper à l'attention, surtout en extérieur. Il n'existe pas de moyen fiable de le garantir. En pratique, la responsabilité repose sur le porteur, tenu de respecter le droit à l'image des personnes qu'il filme."),
            ("Ces montures s'ajustent-elles comme des lunettes normales ?",
             "Moins facilement. L'électronique intégrée dans les branches limite la marge de cintrage et interdit certaines interventions à chaud que nous pratiquons couramment sur l'acétate ou le métal. Un ajustage reste possible dans une certaine mesure, mais il faut accepter un confort un peu moins finement réglable."),
            ("Une lunette connectée dure-t-elle aussi longtemps qu'une paire classique ?",
             "Sa durée de vie utile dépend de la batterie et du suivi logiciel du fabricant, pas seulement de l'état de la monture. Une paire traditionnelle bien entretenue peut se garder plusieurs années et se remonter avec de nouveaux verres, ce qui n'est pas comparable. C'est un critère à intégrer au budget."),
        ],
        "sources": [
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Ray-Ban", "https://www.ray-ban.com/"),
            ("CNIL — Commission nationale de l'informatique et des libertés", "https://www.cnil.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-rayban-meta.jpg",
        "image_alt": "Portrait en noir et blanc d'un homme portant des lunettes de soleil blanches",
        "date_display": "4 novembre 2025",
        "date_iso": "2025-11-04",
        "body": ART_BODY_RAYBAN_META,
    },
    {
        "slug": "ecrans-myopie-enfant-habitudes-protectrices",
        "category": "enfant",
        "title": "Écrans, temps dehors et myopie : quelles habitudes protègent les yeux de mon enfant ?",
        "meta_title": "Écrans et myopie chez l'enfant : quoi faire | ACTU EYES",
        "meta_description": "Pourquoi la myopie progresse chez les enfants, ce que change vraiment le temps passé dehors, et les habitudes simples qui protègent leur vue au quotidien.",
        "excerpt": "La myopie des enfants progresse partout dans le monde, portée par plus d'activités de près et moins de temps dehors.",
        "answer": "La myopie infantile progresse dans la plupart des pays industrialisés, en lien avec plus d'activités de près et moins de temps passé à l'extérieur. Le levier le mieux documenté reste le jeu dehors, à la lumière du jour, complété par des pauses régulières et une distance de lecture raisonnable.",
        "faq": [
            ("La myopie de mon enfant peut-elle disparaître en grandissant ?",
             "Non, une myopie installée ne régresse pas spontanément. Elle progresse généralement pendant la croissance, puis se stabilise vers la fin de l'adolescence. En revanche, une correction bien adaptée rétablit immédiatement une vision nette et un confort normal, à tout âge et sans effet secondaire."),
            ("Les lunettes affaiblissent-elles la vue à force d'être portées ?",
             "C'est une idée reçue tenace, mais fausse. Porter une correction adaptée ne rend pas l'œil paresseux et n'accélère rien. Ne pas la porter, en revanche, expose l'enfant à la fatigue visuelle, aux maux de tête et à des difficultés scolaires évitables."),
            ("Les verres filtrant la lumière bleue protègent-ils de la myopie ?",
             "Rien ne permet de l'affirmer aujourd'hui. Ces filtres n'agissent pas sur l'allongement du globe oculaire, qui est le mécanisme en cause dans la myopie. Le temps passé dehors, les pauses régulières et une distance de lecture raisonnable restent les seuls leviers réellement documentés."),
            ("À quelle fréquence faire contrôler la vue d'un enfant déjà corrigé ?",
             "Le rythme est fixé par l'ophtalmologiste, généralement plus rapproché que chez l'adulte parce que la correction évolue avec la croissance. Entre deux consultations, nous pouvons vérifier le réglage de l'équipement, mesurer la vision et vous alerter si quelque chose nous semble avoir changé."),
            ("Une paire de secours est-elle vraiment utile ?",
             "Elle évite bien des journées sans correction, notamment à l'école, au sport ou en voyage scolaire, et elle limite le stress en cas de casse. Certains contrats de complémentaire santé et certaines offres de fabricants la facilitent : le mieux reste d'en parler au moment du devis, avant l'achat."),
        ],
        "sources": [
            ("Asnav", "https://www.asnav.org/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
            ("Ministère de la Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-enfant-myopie.jpg",
        "image_alt": "Petite fille souriante portant une lunette d'essai lors d'un contrôle de la vue",
        "date_display": "11 novembre 2025",
        "date_iso": "2025-11-11",
        "body": ART_BODY_ECRANS_MYOPIE_ENFANT,
    },
    {
        "slug": "comprendre-devis-normalise-lunettes",
        "category": "remboursements",
        "title": "Comprendre le devis normalisé de vos lunettes",
        "meta_title": "Comprendre le devis normalisé de lunettes | ACTU EYES",
        "meta_description": "Panier 100 % Santé ou libre, prix de la monture et des verres, mentions obligatoires : comment lire le devis normalisé de vos lunettes, ligne par ligne.",
        "excerpt": "Obligatoire, gratuit et sans engagement, le devis normalisé met à plat le prix de vos lunettes. Voici comment le décrypter.",
        "answer": "Le devis normalisé est un document obligatoire, gratuit et sans engagement que l'opticien remet avant tout achat de lunettes. Il présente séparément le prix de la monture et des verres, distingue le panier 100 % Santé (sans reste à charge) du panier à prix libre, et vous permet de comparer en toute transparence.",
        "faq": [
            ("Le devis normalisé est-il vraiment gratuit ?",
             "Oui. Sa remise est obligatoire et gratuite, avant tout achat et sans engagement de votre part. Vous pouvez l'emporter, le comparer et le soumettre à votre mutuelle avant de décider."),
            ("Suis-je obligé de choisir le 100 % Santé ?",
             "Non. Vous pouvez opter pour le panier 100 % Santé, pour le prix libre, ou panacher les deux — par exemple une monture libre avec des verres 100 % Santé. Le devis chiffre chaque option."),
            ("Que faire si une ligne manque sur le devis ?",
             "Demandez-la. Un devis conforme détaille le prix de la monture, celui de chaque verre, leur nature et leur fabricant, la prestation de suivi et les parts remboursées. L'absence d'une de ces mentions doit vous alerter."),
            ("Le devis d'un opticien est-il valable ailleurs ?",
             "Le devis engage l'opticien qui l'a établi sur les équipements décrits, mais son intérêt est surtout de comparer : présenté sur un format normalisé, il permet de mettre en regard deux propositions sur des bases identiques."),
            ("Combien de temps ai-je pour utiliser mon ordonnance ?",
             "Une ordonnance de lunettes est valable 1 an avant 16 ans, 5 ans de 16 à 42 ans, et 3 ans au-delà. Tant qu'elle court, nous pouvons y adapter votre correction lors d'un examen en boutique."),
        ],
        "sources": [
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
            ("Ministère de la Santé - 100 % Santé", "https://sante.gouv.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-devis-calcul.jpg",
        "image_alt": "Calcul d'un devis de lunettes et de sa prise en charge",
        "date_display": "9 mars 2026",
        "date_iso": "2026-03-09",
        "body": ART_BODY_DEVIS_NORMALISE,
    },
    {
        "slug": "une-journee-type-a-la-boutique",
        "category": "vie-boutique",
        "title": "Une journée type chez ACTU EYES, à Montreuil",
        "meta_title": "Une journée type chez ACTU EYES, opticien Montreuil",
        "meta_description": "Ouverture, essayages, examens de vue sans rendez-vous, ajustements : à quoi ressemble une journée dans notre boutique du centre Grand Angle, à Montreuil.",
        "excerpt": "Essayages, examens sans rendez-vous, ajustements, réparations : le quotidien d'un opticien de quartier, heure par heure.",
        "answer": "Une journée chez ACTU EYES alterne essayages et conseils devant le miroir, examens de vue sans rendez-vous, montage et centrage des verres, ajustements et devis. Ouverte du lundi au samedi de 10 h à 19 h 30, la boutique vit au rythme du quartier Cœur de Ville, entre habitués, familles et nouveaux visages.",
        "faq": [
            ("Puis-je venir sans rendez-vous ?",
             "Oui, pour un essayage, un ajustement, une réparation, un devis ou un examen de vue. Ces prestations se font au fil de l'eau, du lundi au samedi de 10 h à 19 h 30."),
            ("Quel est le meilleur moment pour un essayage tranquille ?",
             "Le milieu de journée en semaine est généralement le plus calme. Les fins d'après-midi et le samedi sont les plus fréquentés."),
            ("L'examen de vue est-il payant ?",
             "Non, il est gratuit et sans rendez-vous. Il permet d'adapter la correction d'une ordonnance en cours de validité, mais ne remplace pas la consultation de l'ophtalmologiste."),
            ("Quelles marques peut-on essayer en boutique ?",
             "Une sélection de grandes maisons et de créateurs, de Ray-Ban à Dior en passant par Prada, Burberry ou Fendi, avec un large choix de montures pour tous les budgets."),
        ],
        "sources": [
            ("Grand Angle Montreuil", "https://www.montreuil-grandangle.com/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/histoire/boutique-comptoir.jpg",
        "image_alt": "Comptoir de la boutique ACTU EYES un jour de semaine, à Montreuil",
        "date_display": "12 mars 2026",
        "date_iso": "2026-03-12",
        "body": ART_BODY_JOURNEE_TYPE,
    },
    {
        "slug": "novacel-celene-traitement-anti-reflet-teinte-nude",
        "category": "tech-verres",
        "title": "Célène de Novacel : quand le traitement anti-reflet devient un choix esthétique",
        "meta_title": "Célène de Novacel, l'antireflet nude | ACTU EYES",
        "meta_description": "Un antireflet peut-il devenir un choix esthétique ? Ce que propose Célène, le traitement à reflets nude du verrier français Novacel, et comment le juger.",
        "excerpt": "Le verrier français Novacel présente Célène, un traitement anti-reflet à la teinte nude, pensé pour sublimer le regard.",
        "answer": "Célène est un traitement de surface proposé par le verrier français Novacel. Il assume un reflet résiduel de teinte nude, légèrement rosée, plutôt que le vert ou le bleu habituels, tout en conservant les fonctions attendues d'un traitement moderne : dureté, surface hydrofuge, effet antistatique et protection contre les ultraviolets.",
        "faq": [
            ("Un antireflet coloré modifie-t-il ce que je vois ?",
             "Non. La teinte concerne le reflet renvoyé vers l'extérieur, pas la lumière qui traverse le verre jusqu'à votre œil. Vos couleurs restent fidèles. Ce qui change, c'est l'aspect de vos verres pour la personne en face de vous, surtout sous un éclairage direct ou au flash."),
            ("Peut-on ajouter ce traitement sur des verres déjà montés ?",
             "Non, il est appliqué en usine lors de la fabrication du verre, avant le montage. Il faut donc le choisir au moment de la commande. Si vos verres actuels vous conviennent par ailleurs, mieux vaut attendre le prochain renouvellement plutôt que de les remplacer uniquement pour cela."),
            ("Comment nettoyer des verres traités sans les abîmer ?",
             "Rincez-les à l'eau tiède, éventuellement avec une goutte de savon doux, puis séchez avec un tissu microfibre propre. Évitez le mouchoir en papier, le pan de chemise et les produits ménagers : ils créent un voile de micro-rayures qui use le traitement bien plus vite que l'usage normal."),
            ("Ce traitement convient-il aussi aux hommes ?",
             "Oui, rien dans le produit n'est spécifique à un genre. La teinte est discrète et se remarque surtout de trois quarts. Le vrai critère reste l'accord avec la couleur de la monture et le teint de peau, pas autre chose. Le mieux est de comparer deux verres de démonstration côte à côte."),
            ("À quoi voit-on qu'un traitement antireflet est usé ?",
             "Un voile grisâtre qui ne part plus au nettoyage, des craquelures fines visibles en lumière rasante, ou des reflets qui redeviennent gênants la nuit. Ce sont des signes d'usure de la couche de surface, pas de saleté. Passez nous voir : nous vérifions l'état des verres sans rendez-vous."),
        ],
        "sources": [
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-celene-novacel.jpg",
        "image_alt": "Verres correcteurs aux teintes variées présentés en éventail",
        "date_display": "20 janvier 2026",
        "date_iso": "2026-01-20",
        "body": ART_BODY_NOVACEL_CELENE,
    },
    {
        "slug": "presbytie-comprendre-ce-trouble-de-la-vision",
        "category": "sante-visuelle",
        "title": "Presbytie : comprendre ce trouble de la vision qui touche presque tout le monde après 45 ans",
        "meta_title": "Presbytie après 45 ans : signes et solutions | ACTU EYES",
        "meta_description": "Bras qui s'allonge pour lire, fatigue en fin de journée : comprendre la presbytie, un phénomène naturel, et faire le tri entre les solutions.",
        "excerpt": "Difficulté à lire de près, besoin d'éloigner son téléphone : la presbytie touche, tôt ou tard, la quasi-totalité des adultes.",
        "answer": "La presbytie n'est pas une maladie mais une évolution naturelle de l'œil : le cristallin perd peu à peu sa souplesse et la mise au point de près devient difficile, en général à partir de 44-45 ans. Elle se corrige très bien, en lunettes ou en lentilles, et se stabilise vers 60-65 ans.",
        "faq": [
            ("Porter des lunettes de lecture accélère-t-il la presbytie ?",
             "Non. C'est une crainte très répandue, mais le durcissement du cristallin suit son cours quoi que vous fassiez. Une correction adaptée ne fait que restituer un confort perdu. Ce qui change, c'est que l'on prend conscience de l'effort que l'on fournissait auparavant sans s'en rendre compte."),
            ("Un myope devient-il presbyte lui aussi ?",
             "Oui, le mécanisme est le même pour tout le monde. Un myope léger peut simplement retirer ses lunettes pour lire de près pendant quelques années, ce qui donne l'illusion d'être épargné. La correction de loin, elle, reste nécessaire, et un équipement combiné devient vite plus confortable."),
            ("La chirurgie peut-elle corriger la presbytie ?",
             "Des techniques existent et relèvent exclusivement d'un chirurgien ophtalmologiste, qui évalue l'indication au cas par cas. Ce n'est ni systématique ni adapté à tous les yeux. Cette question se discute en consultation médicale, avec un bilan complet : un opticien ne peut ni la recommander ni l'écarter."),
            ("Faut-il une ordonnance pour des lunettes de près ?",
             "Pour un équipement correcteur, oui : la prescription vient de l'ophtalmologiste. Dans les cas prévus par la réglementation, l'opticien peut renouveler ou adapter une correction sur présentation d'une ordonnance en cours de validité. Les loupes vendues en libre-service échappent à ce cadre, mais elles ne remplacent pas une correction sur mesure."),
            ("Combien de temps faut-il pour s'habituer à une première paire de progressifs ?",
             "Cela varie beaucoup : certains porteurs sont à l'aise en une journée, d'autres ont besoin de deux ou trois semaines. Le réflexe utile est de bouger la tête plutôt que les yeux pour viser la bonne zone. Si la gêne dure, revenez faire vérifier le centrage et le réglage."),
        ],
        "sources": [
            ("Assurance Maladie - ameli.fr", "https://www.ameli.fr/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Organisation mondiale de la santé", "https://www.who.int/fr"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/sante/article-presbytie.jpg",
        "image_alt": "Femme passant un examen de la vue à l'auto-réfractomètre",
        "date_display": "11 février 2026",
        "date_iso": "2026-02-11",
        "body": ART_BODY_PRESBYTIE,
    },
    {
        "slug": "opticien-coeur-de-ville-grand-angle-montreuil",
        "category": "vie-boutique",
        "title": "Cœur de Ville : opticien à Grand Angle depuis l'ouverture",
        "meta_title": "Opticien Cœur de Ville Montreuil – Grand Angle | ACTU EYES",
        "meta_description": "Opticien à Grand Angle, quartier Cœur de Ville de Montreuil : ACTU EYES fait partie des enseignes du centre depuis son ouverture en 2012, face à la mairie.",
        "excerpt": "Ouvert en 2012 face à la mairie, le centre Grand Angle a redessiné le cœur de Montreuil — et ACTU EYES en fait partie depuis le premier jour.",
        "answer": "ACTU EYES est installée au centre commercial Grand Angle, dans le quartier Cœur de Ville de Montreuil, face à la mairie (métro ligne 9). La boutique fait partie des enseignes présentes dès l'ouverture du centre, en décembre 2012, et a été reprise par Mikhael en 2018.",
        "faq": [
            ("Où se trouve exactement la boutique ?",
             "ACTU EYES est installée au centre commercial Grand Angle, dans le quartier Cœur de Ville de Montreuil, face à la mairie. La galerie est à ciel ouvert : on nous rejoint aussi bien depuis la rue que depuis les places du centre."),
            ("Comment venir en transports ou en voiture ?",
             "Le plus simple est le métro ligne 9, station Mairie de Montreuil, à quelques minutes à pied. En voiture, le parking de Grand Angle permet de s'arrêter facilement, même pour une courte visite comme un réajustage ou le retrait d'une commande."),
            ("Quels sont vos horaires ?",
             "Nous accueillons du lundi au samedi, de 10 h à 19 h 30, et nous sommes fermés le dimanche. Les fins d'après-midi et le samedi sont les plus fréquentés ; pour un essayage tranquille, privilégiez le milieu de journée en semaine."),
            ("Faut-il prendre rendez-vous pour un examen de vue ?",
             "Non. L'examen de vue est gratuit et se fait sans rendez-vous, en une vingtaine de minutes. Il permet d'adapter la correction d'une ordonnance en cours de validité ; il ne remplace pas la consultation de l'ophtalmologiste, vers qui nous vous orientons quand c'est nécessaire."),
            ("Depuis quand ACTU EYES est-elle à Grand Angle ?",
             "La boutique fait partie des enseignes présentes dès l'ouverture du centre, en décembre 2012. Elle a été reprise par Mikhael en 2018, qui lui a donné une nouvelle direction tout en restant au même endroit."),
        ],
        "sources": [
            ("Business Immo — ouverture de Grand Angle", "https://www.businessimmo.com/actualites/article/2065664662/lespace-commercial-grand-angle-ouvre-a-montreuil"),
            ("Grand Angle Montreuil", "https://www.montreuil-grandangle.com/"),
            ("Ville de Montreuil", "https://www.montreuil.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/histoire/quartier-coeur-de-ville.jpg",
        "image_alt": "Le centre commercial Grand Angle et le quartier Cœur de Ville, face à la mairie de Montreuil",
        "date_display": "20 février 2026",
        "date_iso": "2026-02-20",
        "body": ART_BODY_COEUR_DE_VILLE,
    },
    {
        "slug": "lunettes-engagees-matieres-durables-eco-responsables",
        "category": "mode-lunettes",
        "title": "Lunettes engagées : quand la mode optique mise sur les matières durables",
        "meta_title": "Lunettes éco-responsables : matières durables | ACTU EYES",
        "meta_description": "Acétate biosourcé, matériaux recyclés, réparabilité : ce que recouvrent vraiment les lunettes dites durables, et comment faire le tri.",
        "excerpt": "Acétate biosourcé, matériaux recyclés, réparabilité : la lunette durable n'est plus une niche mais une vraie tendance.",
        "answer": "Une lunette dite éco-responsable repose sur trois leviers : la matière employée, biosourcée ou recyclée, le lieu et le mode de fabrication, et la capacité de la monture à être réparée plutôt que remplacée. C'est le troisième critère, le plus vérifiable, qui pèse souvent le plus dans la durée.",
        "faq": [
            ("Une monture en acétate biosourcé est-elle plus fragile ?",
             "Non, ce n'est pas ce que nous observons. Les gammes biosourcées se travaillent et s'ajustent comme les acétates classiques, et leur tenue dans le temps dépend surtout de la qualité du montage et des charnières. La différence se joue sur l'origine de la matière, pas sur la solidité de la monture."),
            ("Peut-on faire recycler ses anciennes lunettes ?",
             "Des filières de collecte existent chez de nombreux opticiens et associations, avec des destinations variables selon l'état de la paire : réemploi solidaire pour les montures en bon état, valorisation des matières sinon. Apportez-nous vos anciennes paires, nous vous indiquerons ce qu'il est possible d'en faire."),
            ("Les lunettes durables coûtent-elles plus cher ?",
             "Cela dépend beaucoup plus de la marque, de la finition et du positionnement que de la matière elle-même. Certaines collections responsables se situent au niveau des montures classiques comparables, d'autres nettement au-dessus. Le devis remis en boutique détaille le prix de la monture et celui des verres, ce qui permet de comparer."),
            ("Existe-t-il un label officiel pour les lunettes écologiques ?",
             "Il n'existe pas de label unique reconnu qui s'appliquerait à l'ensemble de la lunetterie. Les marques s'appuient sur des certifications portant sur une matière ou un procédé précis, ce qui n'est pas la même chose. Demandez toujours sur quoi porte exactement la certification annoncée."),
            ("Vaut-il mieux réparer sa monture ou en acheter une neuve ?",
             "Réparer, chaque fois que c'est techniquement possible et que la monture vous plaît encore. Un changement de plaquettes, un resserrage ou un remplacement de branche coûte peu et prolonge la paire de plusieurs années. Nous vous dirons franchement quand une réparation n'a plus de sens."),
        ],
        "sources": [
            ("ADEME — Agence de la transition écologique", "https://www.ademe.fr/"),
            ("EssilorLuxottica", "https://www.essilorluxottica.com/"),
            ("Service-public.fr", "https://www.service-public.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-lunettes-engagees.jpg",
        "image_alt": "Femme portant des lunettes de vue à monture rouge pailletée",
        "date_display": "16 mars 2026",
        "date_iso": "2026-03-16",
        "body": ART_BODY_MATIERES_DURABLES,
    },
    {
        "slug": "renouveler-lunettes-sans-nouvelle-ordonnance-opticien",
        "category": "remboursements",
        "title": "Ordonnance de lunettes expirée ? Ce que l'opticien peut faire sans repasser par le médecin",
        "meta_title": "Renouveler ses lunettes sans ordonnance | ACTU EYES",
        "meta_description": "Votre ordonnance a quelques années ? L'opticien peut souvent renouveler et adapter votre correction sans nouvelle consultation. Durées, limites et exceptions.",
        "excerpt": "Il n'est pas toujours nécessaire de reprendre rendez-vous chez l'ophtalmologiste pour changer de lunettes.",
        "answer": "Une ordonnance de lunettes reste valable 1 an avant 16 ans, 5 ans entre 16 et 42 ans, et 3 ans au-delà. Dans ce délai, l'opticien peut renouveler l'équipement et adapter la correction, sauf opposition écrite du prescripteur ou situation particulière comme une presbytie découverte.",
        "faq": [
            ("J'ai perdu mon ordonnance, que faire ?",
             "Contactez le cabinet qui l'a établie : un duplicata est généralement délivré sans difficulté, parfois par simple appel ou par messagerie sécurisée. Si l'équipement a été réalisé chez nous, nous conservons la correction en dossier, mais un justificatif reste nécessaire pour toute prise en charge."),
            ("Le renouvellement par l'opticien est-il remboursé comme une consultation ?",
             "L'équipement est remboursé selon les règles habituelles, dès lors que la prescription est encore valable et que la périodicité de prise en charge est respectée. Le contrôle réalisé en magasin, lui, n'est pas un acte médical, ne donne lieu à aucun remboursement et n'est pas facturé chez nous."),
            ("Puis-je faire adapter une ordonnance obtenue dans un autre pays ?",
             "Cela dépend de sa forme et des mentions qu'elle comporte, qui varient beaucoup d'un pays à l'autre. Apportez-la : nous vérifions si elle répond aux exigences françaises. Dans le doute, une consultation en France reste la solution la plus sûre pour être correctement pris en charge."),
            ("Mon ophtalmologiste a coché une case interdisant l'adaptation, pourquoi ?",
             "Cette opposition est prévue par les textes et s'utilise lorsque le praticien souhaite revoir lui-même le patient, par exemple en cas de correction complexe ou de pathologie suivie de près. Elle s'impose à l'opticien, qui ne peut alors rien modifier et vous réoriente vers le cabinet."),
            ("Faut-il refaire un contrôle même si je vois bien ?",
             "C'est vivement recommandé. Une correction peut dériver très lentement sans que l'on s'en rende compte, et certaines pathologies oculaires débutent sans aucune gêne perceptible. Un contrôle régulier chez l'ophtalmologiste, complété entre deux consultations par une vérification chez nous, reste le bon réflexe."),
        ],
        "sources": [
            ("Service-public.fr", "https://www.service-public.fr/"),
            ("Assurance Maladie", "https://www.ameli.fr/"),
            ("Asnav", "https://www.asnav.org/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-ordonnance-cnam.jpg",
        "image_alt": "Logo de l'Assurance Maladie",
        "date_display": "25 mars 2026",
        "date_iso": "2026-03-25",
        "body": ART_BODY_RENOUVELER_ORDONNANCE,
    },
    {
        "slug": "essilor-varilux-immersia-verre-progressif-interieur",
        "category": "tech-verres",
        "title": "Varilux Immersia : le nouveau verre progressif pensé pour la vie à l'intérieur",
        "meta_title": "Varilux Immersia, le verre progressif Essilor | ACTU EYES",
        "meta_description": "Un verre progressif dédié aux distances proches et intermédiaires : ce que propose Varilux Immersia, pour qui c'est utile et quand une paire suffit.",
        "excerpt": "Essilor dévoile Varilux Immersia, un verre progressif conçu pour les journées passées entre lecture et écrans.",
        "answer": "Varilux Immersia est un verre progressif d'Essilor conçu pour les distances proches et intermédiaires plutôt que pour la vision de loin. Il s'adresse aux porteurs dont la journée se passe entre lecture, écrans et déplacements dans une pièce, et vient en complément d'une paire polyvalente, non en remplacement.",
        "faq": [
            ("Peut-on conduire avec ce type de verre ?",
             "Non. Un verre optimisé pour les distances proches et intermédiaires offre une vision de loin réduite, incompatible avec la conduite. Il s'utilise à l'intérieur, en complément d'une paire polyvalente que vous gardez pour les déplacements, l'extérieur et toute situation demandant une vision de loin nette."),
            ("Quelle différence avec un verre bureau classique ?",
             "Les verres dits bureau ou à faible dégression suivent la même logique de priorité aux courtes distances, avec des dessins et des gammes de prix très variés selon les fabricants. La comparaison se fait sur le champ de vision obtenu et sur le devis, pas sur le nom commercial."),
            ("Ce verre est-il pris en charge par l'Assurance Maladie ?",
             "Il relève des verres à prix libres, donc d'une prise en charge qui dépend de votre complémentaire santé. Une seconde paire est souvent moins bien couverte que la principale, et le renouvellement obéit à des règles de délai. Demandez un devis normalisé et interrogez votre mutuelle avant de commander."),
            ("Faut-il une nouvelle ordonnance pour l'essayer ?",
             "Une ordonnance en cours de validité est nécessaire. Si la vôtre date de plusieurs années ou si votre vision a changé, un nouvel examen s'impose. L'opticien peut ajuster une correction dans les cas prévus par la réglementation, mais la prescription initiale reste du ressort de l'ophtalmologiste."),
            ("L'adaptation est-elle plus facile qu'avec une paire polyvalente ?",
             "Souvent oui, parce que les zones utiles sont plus larges aux distances concernées. Cela reste variable d'une personne à l'autre. Portez la paire en continu dans son contexte d'usage plutôt que par intermittence, et revenez si la gêne persiste : un ajustement de monture règle beaucoup de cas."),
        ],
        "sources": [
            ("Essilor France", "https://www.essilor.fr/"),
            ("Asnav - Association nationale pour l'amélioration de la vue", "https://www.asnav.org/"),
            ("Institut national de recherche et de sécurité", "https://www.inrs.fr/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-varilux-immersia.jpg",
        "image_alt": "Verre optique en lévitation, illustration d'un verre progressif nouvelle génération",
        "date_display": "14 avril 2026",
        "date_iso": "2026-04-14",
        "body": ART_BODY_VARILUX,
    },
    {
        "slug": "comment-nous-choisissons-nos-montures",
        "category": "vie-boutique",
        "title": "Comment nous choisissons les montures d'ACTU EYES",
        "meta_title": "Comment ACTU EYES choisit ses montures | Montreuil",
        "meta_description": "Grandes maisons, créateurs indépendants, petits prix bien dessinés : les coulisses de la sélection de montures chez ACTU EYES, opticien à Montreuil.",
        "excerpt": "Grandes maisons, créateurs indépendants et jolis prix : comment nous composons la sélection de montures que vous essayez en boutique, et selon quels critères.",
        "answer": "Nous choisissons nos montures une par une, en équilibrant trois exigences : la qualité de fabrication (charnières, matières, finitions), la variété des styles et des budgets, et le plaisir d'essayage. Grandes maisons et créateurs indépendants y côtoient des modèles abordables, pour que chacun reparte avec une paire qui lui ressemble vraiment.",
        "faq": [
            ("Pourquoi ne vendez-vous pas toutes les marques ?",
             "Parce qu'une sélection resserrée est plus honnête qu'un catalogue infini. Nous ne référençons que des montures dont nous connaissons la tenue dans le temps et le sérieux du fabricant, quitte à écarter des marques très demandées si la qualité ne suit pas."),
            ("Avez-vous des montures à petit prix ?",
             "Oui, et c'est un choix assumé. À côté des grandes maisons, nous gardons toujours un large rayon de montures abordables et bien dessinées, pour qu'un budget serré n'oblige jamais à sacrifier le style ni le confort. Le 100 % Santé permet même un équipement complet sans reste à charge."),
            ("Comment savez-vous qu'une monture est de bonne qualité ?",
             "On regarde les charnières, la qualité de l'acétate ou du métal, le poids et l'équilibre sur le nez, la solidité des branches. L'expérience du comptoir fait le reste : on sait vite quels modèles reviennent en réparation et lesquels tiennent des années."),
            ("Puis-je commander une monture que vous n'avez pas en rayon ?",
             "Souvent, oui. Si vous avez repéré un modèle précis chez un fabricant que nous distribuons, nous pouvons généralement le commander. Passez nous voir avec la référence, on regarde ensemble ce qui est possible."),
        ],
        "sources": [
            ("Rassemblement des Opticiens de France", "https://www.rof.org/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/conseils/choisir-monture.jpg",
        "image_alt": "Sélection de montures de lunettes présentées en boutique",
        "date_display": "18 juin 2026",
        "date_iso": "2026-06-18",
        "body": ART_BODY_CHOIX_MONTURES,
    },
    {
        "slug": "dans-les-coulisses-de-notre-atelier",
        "category": "vie-boutique",
        "title": "Dans les coulisses de notre atelier : montage, ajustements, réparations",
        "meta_title": "L'atelier d'un opticien : montage & réparations | ACTU EYES",
        "meta_description": "Centrage et taillage des verres, ajustements sur mesure, petites réparations : ce qui se passe derrière le comptoir d'ACTU EYES, opticien à Montreuil.",
        "excerpt": "Tailler un verre au dixième de millimètre, régler une monture sur un visage, sauver une paire abîmée : le travail d'atelier, discret mais décisif.",
        "answer": "Derrière le comptoir, l'atelier est là où une paire prend vie : centrage précis de la correction, taillage des verres à la forme de la monture, puis ajustement sur votre visage. S'y ajoutent les petites réparations du quotidien — plaquettes, vis, branches — que nous rendons le plus souvent sur place et sans attendre.",
        "faq": [
            ("Combien de temps faut-il pour monter une paire ?",
             "Pour un équipement simple, le montage se fait souvent dans la journée, parfois en moins d'une heure selon l'affluence. Les verres progressifs ou à traitements spécifiques demandent généralement quelques jours, le temps de la commande et d'un montage soigné."),
            ("Réparez-vous les lunettes qui ne viennent pas de chez vous ?",
             "Oui, dans la mesure du possible. Un resserrage, un changement de plaquettes ou de vis, un réalignement se font volontiers, même sur une paire achetée ailleurs. Pour le remplacement d'une pièce spécifique, cela dépend de sa disponibilité auprès du fabricant."),
            ("Un ajustement, est-ce vraiment utile ?",
             "Essentiel, même. Une monture mal réglée glisse, marque le nez ou décale les verres devant les yeux, ce qui suffit à gêner la vision, surtout en progressif. Le réglage se refait autant de fois que nécessaire, gratuitement."),
            ("Que faire si je casse mes lunettes ?",
             "Passez nous voir : beaucoup de casses se réparent sur place. Si la monture est trop abîmée, on cherche une solution — remonter vos verres encore bons sur une nouvelle monture, par exemple. L'idée est d'éviter de vous laisser sans lunettes."),
        ],
        "sources": [
            ("Rassemblement des Opticiens de France", "https://www.rof.org/"),
        ],
        "updated_display": "31 juillet 2026",
        "updated_iso": "2026-07-31",
        "image": "/images/actualites/article-atelier-reparation.jpg",
        "image_alt": "Opticien remplaçant la branche d'une paire de lunettes en atelier",
        "date_display": "9 mai 2026",
        "date_iso": "2026-05-09",
        "body": ART_BODY_ATELIER,
    },
]

# Site optique seul : retrait des 4 articles a composante auditive (kit 05).
_AUDITION_SLUGS = {
    "perte-auditive-signes-precoces",
    "casques-ecouteurs-proteger-audition-jeunes",
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais",
    "otites-repetition-enfant-audition-langage",
}
ARTICLES = [a for a in ARTICLES if a["slug"] not in _AUDITION_SLUGS]

# ---------------------------------------------------------------------------
# Articles ajoutes automatiquement par la veille hebdomadaire (GitHub Actions).
#
# Le fichier scripts/articles_auto.json contient une liste d'articles au meme
# format que ARTICLES ci-dessus. Il est ecrit par scripts/veille.py lors de
# l'execution hebdomadaire, puis relu ici : build.py reste ainsi le SEUL
# generateur du site, et un article ajoute automatiquement passe exactement par
# le meme gabarit, le meme maillage interne et le meme JSON-LD que les 24
# articles ecrits a la main.
#
# Les articles automatiques sont places EN TETE (les plus recents d'abord).
# L'ordre des 24 articles historiques n'est volontairement pas touche : il est
# curate, pas chronologique, et le reordonner changerait les 33 pages.
# ---------------------------------------------------------------------------
AUTO_ARTICLES_PATH = os.path.join(OUT_DIR, "scripts", "articles_auto.json")
AUTO_ARTICLE_FIELDS = (
    "slug", "category", "title", "meta_title", "meta_description", "excerpt",
    "answer", "faq", "sources", "image", "image_alt",
    "date_display", "date_iso", "body",
)


def load_auto_articles(path=AUTO_ARTICLES_PATH):
    """Relit les articles produits par la veille, en refusant tout ce qui est
    mal forme plutot que de generer une page bancale en production."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise SystemExit("articles_auto.json doit contenir une liste.")

    known = {a["slug"] for a in ARTICLES}
    out = []
    for entry in raw:
        missing = [k for k in AUTO_ARTICLE_FIELDS if k not in entry]
        if missing:
            raise SystemExit(f"article auto incomplet ({entry.get('slug')}) : {missing}")
        if entry["category"] not in ARTICLE_CATEGORIES:
            raise SystemExit(f"categorie inconnue : {entry['category']}")
        if entry["slug"] in known:
            raise SystemExit(f"slug deja utilise : {entry['slug']}")
        known.add(entry["slug"])
        entry = dict(entry)
        # JSON ne connait pas les tuples : on retablit la forme attendue.
        entry["faq"] = [tuple(x) for x in entry["faq"]]
        entry["sources"] = [tuple(x) for x in entry["sources"]]
        out.append(entry)

    out.sort(key=lambda a: a["date_iso"], reverse=True)
    return out


AUTO_ARTICLES = load_auto_articles()
ARTICLES = AUTO_ARTICLES + ARTICLES



def article_url(article):
    return f"actualites/{article['slug']}.html"


def article_jsonld(article):
    # BlogPosting plutot qu'Article : sous-type plus precis pour un blog,
    # toujours supporte par Google en 2026 (contrairement a FAQPage et HowTo,
    # dont les rich results ont ete supprimes). dateModified reflete la
    # reecriture SEO quand le champ `updated_iso` est renseigne.
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": article["title"],
        "description": article["meta_description"],
        "image": f"{BASE_URL}{article['image']}",
        "datePublished": article["date_iso"],
        "dateModified": article.get("updated_iso", article["date_iso"]),
        "author": {"@type": "Organization", "name": "ACTU EYES"},
        "publisher": {
            "@type": "Organization",
            "name": "ACTU EYES",
            "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/og-image.jpg"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}/{article_url(article)}"},
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>'


def render_article_card(article):
    cat = ARTICLE_CATEGORIES[article["category"]]
    # Carte "bulle" : reste un vrai lien <a href> (fonctionne sans JS, SEO/partage
    # intacts — chaque article garde sa propre page), mais un clic normal est
    # intercepté en JS pour agrandir la bulle sur place plutôt que de naviguer
    # (voir le script "bulles Actualités" plus bas et .article-modal-* en CSS).
    return (
        f'      <a href="/{article_url(article)}" class="article-card reveal" data-category="{article["category"]}">\n'
        f'        <div class="article-img"><img src="{article["image"]}" alt="{article["image_alt"]}" loading="lazy"></div>\n'
        f'        <div class="article-card-body">\n'
        f'          <span class="article-tag" style="--accent:{cat["accent"]};--accent-bg:{cat["accent_bg"]};">{cat["label"]}</span>\n'
        f'          <h3>{article["title"]}</h3>\n'
        f'          <p>{article["excerpt"]}</p>\n'
        f'          <div class="article-meta"><span>{article["date_display"]}</span><span class="more">Lire l\'article <span aria-hidden="true">⤢</span></span></div>\n'
        f'        </div>\n'
        f'      </a>'
    )


# ============================================================================
# MAILLAGE INTERNE (31/07/2026)
# ----------------------------------------------------------------------------
# Constat avant travaux : sur 24 articles, seulement 2 liens contextuels vers
# le reste du site, et aucune page de service ne renvoyait vers un article.
# Trois mecanismes sont mis en place ici :
#   1. INLINE_LINKS  : liens contextuels poses dans le corps des articles, au
#      moment du rendu. Le plan est de la donnee, pas du HTML fige : les corps
#      ART_BODY_* restent lisibles et le plan est verifiable d'un coup d'oeil.
#   2. GO_FURTHER    : encadre "Pour aller plus loin" en fin d'article.
#   3. PAGE_ARTICLES : bloc "Nos articles sur le sujet" sur les pages de
#      service, insere juste avant le CTA final.
# Le bloc "A lire aussi" passe par ailleurs d'une rotation chronologique
# (idx+1, +2, +3 — souvent hors sujet) a une selection par categorie.
# ============================================================================

def _link_forbidden_spans(html):
    """Zones ou l'on n'insere jamais de lien : titres, liens existants, citations."""
    spans = []
    for m in re.finditer(r'<h[1-6][^>]*>.*?</h[1-6]>', html, re.S | re.I):
        spans.append(m.span())
    for m in re.finditer(r'<a\b.*?</a>', html, re.S | re.I):
        spans.append(m.span())
    for m in re.finditer(r'<(figcaption|blockquote)\b.*?</\1>', html, re.S | re.I):
        spans.append(m.span())
    return spans


def _link_candidates(html, phrase):
    bad = _link_forbidden_spans(html)
    out = []
    for m in re.finditer(re.escape(phrase), html):
        start, end = m.span()
        lt = html.rfind('<', 0, start)
        gt = html.rfind('>', 0, start)
        if lt > gt:            # position situee a l'interieur d'une balise
            continue
        if any(a <= start < b for a, b in bad):
            continue
        out.append((start, end))
    return out


LINK_WARNINGS = []


def apply_inline_links(html, plan, context=""):
    """plan : liste de (phrase, href) ou (phrase, href, occurrence)."""
    for item in plan:
        phrase, href = item[0], item[1]
        occ = item[2] if len(item) > 2 else 1
        cands = _link_candidates(html, phrase)
        if len(cands) < occ:
            LINK_WARNINGS.append(
                "%s : phrase %r introuvable (occurrence %d demandee, %d disponible(s))"
                % (context, phrase, occ, len(cands)))
            continue
        start, end = cands[occ - 1]
        html = html[:start] + '<a href="%s">%s</a>' % (href, html[start:end]) + html[end:]
    return html


# --- Liens contextuels, article par article --------------------------------
INLINE_LINKS = {
    "fatigue-oculaire-ecrans": [
        ("lumière bleue", "/nos-conseils.html#traitements-verres"),
        ("correction", "/espace-sante.html#defauts"),
        ("fatigue visuelle", "/actualites/ecrans-myopie-enfant-habitudes-protectrices.html"),
    ],
    "perte-auditive-signes-precoces": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("acouphènes", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html"),
        ("bilan auditif", "/espace-audition.html"),  # 2e occurrence : la 1re est deja liee
    ],
    "tendances-montures-2026": [
        ("écaille", "/marques.html"),
        ("métal", "/actualites/lunettes-engagees-matieres-durables-eco-responsables.html"),
        ("essayer", "/contact.html"),
    ],
    "nouvelles-technologies-verres-correcteurs": [
        ("verres progressifs", "/actualites/essilor-varilux-immersia-verre-progressif-interieur.html"),
        ("myopie", "/espace-sante.html#myopie-enfant"),
        ("traitements", "/nos-conseils.html#traitements-verres"),
    ],
    "nouvelles-technologies-lentilles-contact": [
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
        ("astigmatisme", "/espace-sante.html#defauts"),
    ],
    "100-pour-cent-sante-2026": [
        ("devis normalisé", "/actualites/comprendre-devis-normalise-lunettes.html"),
        ("monture", "/marques.html"),
        ("classe A", "/nos-conseils.html#type-verres"),
    ],
    "reprise-actueyes-histoire-opticien-montreuil": [
        ("Olympiades", "/contact.html"),
        ("quartier", "/actualites/nouvel-an-lunaire-triangle-de-choisy.html", 2),
    ],
    "signes-troubles-visuels-enfant": [
        ("dépistage", "/espace-sante.html#myopie-enfant"),
        ("audition", "/espace-audition.html"),
    ],
    "lentilles-hebdomadaires-precision7-alcon": [
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("Alcon", "/actualites/nouvelles-technologies-lentilles-contact.html", 2),
        ("entretien", "/nos-conseils.html#entretien-lunettes"),
    ],
    "proteger-yeux-soleil-uv": [
        ("lunettes de soleil", "/marques.html"),
        ("cataracte", "/espace-sante.html#maladies"),
        ("catégorie 3", "/nos-conseils.html#type-verres"),
    ],
    "lentilles-rigides-asana-bausch-lomb": [
        ("lentilles rigides", "/nos-conseils.html#lunettes-ou-lentilles"),
        ("kératocône", "/espace-sante.html#maladies"),
        ("opticien", "/contact.html"),
    ],
    "casques-ecouteurs-proteger-audition-jeunes": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("volume", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", 2),
    ],
    "lunettes-connectees-ray-ban-meta-mode-tech": [
        ("Ray-Ban", "/marques.html#ray-ban", 2),
        ("monture", "/actualites/tendances-montures-2026.html", 2),
        ("opticien", "/nos-conseils.html#type-verres"),
    ],
    "ecrans-myopie-enfant-habitudes-protectrices": [
        ("myopie", "/espace-sante.html#myopie-enfant"),
        ("enfant", "/actualites/signes-troubles-visuels-enfant.html", 2),
        ("montures", "/marques.html"),
    ],
    "comprendre-devis-normalise-lunettes": [
        ("reste à charge", "/actualites/100-pour-cent-sante-2026.html"),
        ("aides auditives", "/espace-audition.html"),
        ("lentilles", "/nos-conseils.html#lunettes-ou-lentilles"),
    ],
    "une-journee-type-a-la-boutique": [
        ("monture", "/marques.html"),
        ("ordonnance", "/index.html#examen-de-vue"),
        ("rendez-vous", "/contact.html", 2),
    ],
    "novacel-celene-traitement-anti-reflet-teinte-nude": [
        ("anti-reflet", "/nos-conseils.html#traitements-verres"),
        ("monture", "/marques.html"),
        ("Novacel", "/actualites/nouvelles-technologies-verres-correcteurs.html", 2),
    ],
    "presbytie-comprendre-ce-trouble-de-la-vision": [
        ("verres progressifs", "/nos-conseils.html#type-verres"),
        ("opticien", "/index.html#examen-de-vue"),
        ("lentilles", "/actualites/nouvelles-technologies-lentilles-contact.html"),
    ],
    "nouvel-an-lunaire-triangle-de-choisy": [
        ("Triangle de Choisy", "/notre-histoire.html"),
        ("vitrine", "/contact.html", 2),
        ("montures", "/marques.html"),
    ],
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais": [
        ("bilan auditif", "/index.html#test-auditif"),
        ("audition", "/espace-audition.html", 2),
        ("ORL", "/actualites/perte-auditive-signes-precoces.html", 2),
    ],
    "lunettes-engagees-matieres-durables-eco-responsables": [
        ("montures", "/marques.html"),
        ("marque", "/actualites/tendances-montures-2026.html", 2),
        ("recyclé", "/nos-conseils.html#choix-monture"),
    ],
    "renouveler-lunettes-sans-nouvelle-ordonnance-opticien": [
        ("examen de vue", "/index.html#examen-de-vue"),
        ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", 2),
        ("ordonnance", "/nos-conseils.html#lire-ordonnance", 3),
    ],
    "otites-repetition-enfant-audition-langage": [
        ("audiogramme", "/espace-audition.html"),
        ("langage", "/actualites/signes-troubles-visuels-enfant.html", 2),
        ("enfant", "/espace-sante.html#myopie-enfant", 3),
    ],
    "essilor-varilux-immersia-verre-progressif-interieur": [
        ("verres progressifs", "/nos-conseils.html#type-verres"),
        ("presbyte", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
        ("Varilux", "/actualites/nouvelles-technologies-verres-correcteurs.html"),
    ],
}

# --- Encadre "Pour aller plus loin" ----------------------------------------
GO_FURTHER = {
    "comment-nous-choisissons-nos-montures": [
        ("/marques.html", "Les marques que nous avons choisies",
         "Grandes maisons et créateurs indépendants, présentés famille par famille."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "Forme, matière et proportions selon la morphologie de votre visage."),
        ("/actualites/tendances-montures-2026.html", "Les tendances montures 2026",
         "Les formes et les couleurs à privilégier cette année."),
    ],
    "dans-les-coulisses-de-notre-atelier": [
        ("/nos-conseils.html#entretien-lunettes", "Bien entretenir ses lunettes",
         "Les bons gestes au quotidien pour les faire durer plus longtemps."),
        ("/actualites/une-journee-type-a-la-boutique.html", "Une journée type à la boutique",
         "Le quotidien d'un opticien de quartier, heure par heure."),
        ("/actualites/comprendre-devis-normalise-lunettes.html", "Comprendre votre devis",
         "Ce que couvre le 100 % Santé, ligne par ligne."),
    ],
    "fatigue-oculaire-ecrans": [
        ("/index.html#examen-de-vue", "Faire contrôler sa vue en boutique, sans rendez-vous",
         "Un examen de vue gratuit pour vérifier que votre correction est toujours la bonne."),
        ("/nos-conseils.html#traitements-verres", "Les traitements de verres, expliqués simplement",
         "Anti-reflet, anti-lumière bleue, anti-rayure : lesquels servent vraiment à quoi."),
        ("/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", "Presbytie : ce qui change après 45 ans",
         "Quand la fatigue de près n'est plus seulement une histoire d'écrans."),
    ],
    "perte-auditive-signes-precoces": [
        ("/espace-audition.html", "Découvrir notre Espace Audition",
         "Bilan, appareillage, réglages et suivi : comment nous vous accompagnons."),
        ("/index.html#test-auditif", "Le test auditif gratuit, sur rendez-vous",
         "Une heure en cabine isolée pour savoir précisément où vous en êtes."),
        ("/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", "Acouphènes : comprendre ce bruit permanent",
         "Souvent associés à une baisse d'audition, rarement pris au sérieux assez tôt."),
    ],
    "tendances-montures-2026": [
        ("/marques.html", "Voir toutes nos marques de montures",
         "Ray-Ban, Prada, Loewe, Celine, Miu Miu et une vingtaine d'autres, en boutique."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "Morphologie, teint, correction : les critères qui comptent vraiment."),
        ("/actualites/lunettes-engagees-matieres-durables-eco-responsables.html", "Les montures en matières durables",
         "Bio-acétate, métal recyclé : la mode optique change de matériaux."),
    ],
    "nouvelles-technologies-verres-correcteurs": [
        ("/nos-conseils.html#type-verres", "Quel type de verres pour quelle correction",
         "Unifocaux, progressifs, dégressifs : le repère avant de choisir."),
        ("/espace-sante.html#myopie-enfant", "La myopie de l'enfant",
         "Pourquoi elle progresse, et ce que les verres de freination peuvent faire."),
        ("/actualites/essilor-varilux-immersia-verre-progressif-interieur.html", "Varilux Immersia, le progressif d'intérieur",
         "Le dernier né des verres progressifs, pensé pour la vie en intérieur."),
    ],
    "nouvelles-technologies-lentilles-contact": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles : comment choisir",
         "Les avantages et les limites de chaque solution, sans idées reçues."),
        ("/actualites/lentilles-hebdomadaires-precision7-alcon.html", "Precision7 : la lentille hebdomadaire d'Alcon",
         "Un rythme de port inédit entre la journalière et la mensuelle."),
        ("/contact.html", "Venir en parler en boutique",
         "L'adaptation d'une lentille se fait toujours en essai accompagné."),
    ],
    "100-pour-cent-sante-2026": [
        ("/actualites/comprendre-devis-normalise-lunettes.html", "Lire un devis normalisé",
         "Le document qui vous dit exactement ce que vous payez, et pourquoi."),
        ("/espace-audition.html", "Le 100 % Santé côté audition",
         "Appareils de classe 1, essai de 30 jours et suivi inclus pendant 4 ans."),
        ("/contact.html", "Faire le point sur vos droits avec nous",
         "Nous vérifions votre couverture et appliquons le tiers payant quand c'est possible."),
    ],
    "reprise-actueyes-histoire-opticien-montreuil": [
        ("/notre-histoire.html", "Lire toute notre histoire",
         "De la rencontre au projet, jusqu'à l'ouverture Centre commercial Grand Angle."),
        ("/actualites/une-journee-type-a-la-boutique.html", "Une journée type à la boutique",
         "Ce qui se passe vraiment entre l'ouverture et la fermeture du rideau."),
        ("/contact.html", "Venir nous rencontrer",
         "Centre commercial Grand Angle, quartier Cœur de Ville, Montreuil."),
    ],
    "signes-troubles-visuels-enfant": [
        ("/espace-sante.html#myopie-enfant", "La vue de l'enfant, âge par âge",
         "Ce qu'il faut surveiller et à quel moment consulter."),
        ("/actualites/otites-repetition-enfant-audition-langage.html", "Otites à répétition et langage",
         "Quand une audition fluctuante freine l'apprentissage de la parole."),
        ("/actualites/ecrans-myopie-enfant-habitudes-protectrices.html", "Écrans, temps dehors et myopie",
         "Les habitudes qui protègent réellement les yeux d'un enfant."),
    ],
    "lentilles-hebdomadaires-precision7-alcon": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles : comment choisir",
         "Les deux solutions ne s'opposent pas, elles se complètent."),
        ("/actualites/nouvelles-technologies-lentilles-contact.html", "Les nouveautés en lentilles de contact",
         "Matériaux, rythmes de port, corrections complexes : où en est-on."),
        ("/contact.html", "Demander un essai en boutique",
         "Une lentille ne se choisit jamais sans essai ni contrôle d'adaptation."),
    ],
    "proteger-yeux-soleil-uv": [
        ("/marques.html", "Nos solaires, marque par marque",
         "Une sélection de solaires à verres correcteurs ou non."),
        ("/espace-sante.html#maladies", "Les maladies de l'œil liées au soleil",
         "Cataracte, DMLA, ptérygion : ce que les UV provoquent à long terme."),
        ("/nos-conseils.html#type-verres", "Choisir la bonne catégorie de verre solaire",
         "De la catégorie 0 à la catégorie 4 : à quel usage correspond chacune."),
    ],
    "lentilles-rigides-asana-bausch-lomb": [
        ("/espace-sante.html#maladies", "Kératocône et cornées irrégulières",
         "Pourquoi certaines cornées demandent une lentille rigide."),
        ("/actualites/nouvelles-technologies-lentilles-contact.html", "Les nouveautés en lentilles de contact",
         "Le panorama complet des matériaux et rythmes de port."),
        ("/contact.html", "Prendre rendez-vous pour une adaptation",
         "L'adaptation d'une lentille rigide demande plusieurs contrôles."),
    ],
    "casques-ecouteurs-proteger-audition-jeunes": [
        ("/index.html#test-auditif", "Le test auditif gratuit en boutique",
         "Un bilan complet, sur rendez-vous, sans aucun engagement."),
        ("/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html", "Acouphènes : le signal d'alerte",
         "Le premier symptôme d'une exposition sonore trop forte, souvent ignoré."),
        ("/actualites/perte-auditive-signes-precoces.html", "Les signes précoces d'une perte auditive",
         "7 à 10 ans s'écoulent en moyenne avant la première consultation."),
    ],
    "lunettes-connectees-ray-ban-meta-mode-tech": [
        ("/marques.html#ray-ban", "Ray-Ban chez ACTU EYES",
         "Wayfarer, Aviator, Clubmaster : les modèles disponibles en boutique."),
        ("/actualites/tendances-montures-2026.html", "Les tendances montures 2026",
         "Formes, matières et couleurs qui marquent la saison."),
        ("/nos-conseils.html#type-verres", "Monter des verres correcteurs sur une solaire",
         "Ce qui est possible, et ce qui ne l'est pas, selon la correction."),
    ],
    "ecrans-myopie-enfant-habitudes-protectrices": [
        ("/espace-sante.html#myopie-enfant", "La myopie de l'enfant expliquée",
         "Mécanismes, facteurs de risque et solutions de freination."),
        ("/actualites/signes-troubles-visuels-enfant.html", "Repérer un trouble visuel chez son enfant",
         "Les signes que les parents voient avant le dépistage scolaire."),
        ("/contact.html", "Faire contrôler la vue de votre enfant",
         "Avant 16 ans, le passage par l'ophtalmologiste reste nécessaire — nous vous guidons."),
    ],
    "comprendre-devis-normalise-lunettes": [
        ("/actualites/100-pour-cent-sante-2026.html", "Le 100 % Santé en 2026",
         "Ce qui est réellement pris en charge en optique."),
        ("/nos-conseils.html#lire-ordonnance", "Savoir lire son ordonnance",
         "Sphère, cylindre, axe, addition : décoder les chiffres du prescripteur."),
        ("/contact.html", "Demander un devis gratuit",
         "Le devis normalisé est gratuit et sans engagement, avant tout achat."),
    ],
    "une-journee-type-a-la-boutique": [
        ("/notre-histoire.html", "Notre histoire, depuis le début",
         "Pourquoi Sudaya et Mikhael ont ouvert ACTU EYES en 2023."),
        ("/marques.html", "Les marques que nous sélectionnons",
         "Ce qui entre en vitrine, et selon quels critères."),
        ("/contact.html", "Passer nous voir",
         "Centre commercial Grand Angle, quartier Cœur de Ville — sans rendez-vous pour l'optique."),
    ],
    "novacel-celene-traitement-anti-reflet-teinte-nude": [
        ("/nos-conseils.html#traitements-verres", "Tous les traitements de verres",
         "Anti-reflet, hydrophobe, anti-rayure : à quoi sert chaque couche."),
        ("/actualites/nouvelles-technologies-verres-correcteurs.html", "Les innovations verres du moment",
         "Photochromiques, freination de la myopie, verres bureau."),
        ("/contact.html", "Voir le rendu en boutique",
         "Un traitement esthétique se juge à l'œil, sur votre monture."),
    ],
    "presbytie-comprendre-ce-trouble-de-la-vision": [
        ("/espace-sante.html#defauts", "Les défauts visuels expliqués",
         "Myopie, hypermétropie, astigmatisme, presbytie : les distinguer."),
        ("/nos-conseils.html#type-verres", "Progressifs, dégressifs ou double foyer",
         "Quel verre pour quel usage quand la vision de près baisse."),
        ("/actualites/essilor-varilux-immersia-verre-progressif-interieur.html", "Varilux Immersia",
         "Un progressif conçu pour les distances de la vie en intérieur."),
    ],
    "nouvel-an-lunaire-triangle-de-choisy": [
        ("/notre-histoire.html", "Notre histoire dans ce quartier",
         "Pourquoi nous avons choisi les Olympiades pour ouvrir."),
        ("/actualites/une-journee-type-a-la-boutique.html", "Une journée type à la boutique",
         "Le quotidien vu de l'intérieur, entre optique et audition."),
        ("/contact.html", "Venir nous voir Centre commercial Grand Angle",
         "Adresse, horaires et accès en métro, bus ou à pied."),
    ],
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais": [
        ("/espace-audition.html", "Notre Espace Audition",
         "Bilan, appareillage et accompagnement, y compris en cas d'acouphènes."),
        ("/index.html#test-auditif", "Faire un bilan auditif gratuit",
         "Sur rendez-vous, en cabine isolée, sans engagement."),
        ("/actualites/casques-ecouteurs-proteger-audition-jeunes.html", "Protéger son audition au casque",
         "La première cause évitable d'acouphènes chez les moins de 35 ans."),
    ],
    "lunettes-engagees-matieres-durables-eco-responsables": [
        ("/marques.html", "Nos marques en boutique",
         "Une sélection où les démarches durables ont toute leur place."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "La matière n'est pas qu'un argument : elle change le confort au quotidien."),
        ("/actualites/tendances-montures-2026.html", "Les tendances 2026",
         "Formes et couleurs de la saison, matières durables comprises."),
    ],
    "renouveler-lunettes-sans-nouvelle-ordonnance-opticien": [
        ("/index.html#examen-de-vue", "L'examen de vue gratuit en boutique",
         "Sans rendez-vous : c'est lui qui permet d'adapter votre correction."),
        ("/nos-conseils.html#quand-changer", "Quand faut-il changer de lunettes",
         "Les signes qui indiquent qu'un équipement n'est plus adapté."),
        ("/actualites/100-pour-cent-sante-2026.html", "Vos remboursements en 2026",
         "Une ordonnance adaptée par l'opticien reste intégralement remboursable."),
    ],
    "otites-repetition-enfant-audition-langage": [
        ("/espace-audition.html", "Notre Espace Audition",
         "Nous réalisons les bilans auditifs de l'enfant comme de l'adulte."),
        ("/actualites/signes-troubles-visuels-enfant.html", "Repérer un trouble auditif chez l'enfant",
         "Les signaux d'alerte, âge par âge, côté vue comme côté audition."),
        ("/contact.html", "Prendre rendez-vous pour un bilan",
         "Un bilan auditif enfant demande du temps et un environnement calme."),
    ],
    "essilor-varilux-immersia-verre-progressif-interieur": [
        ("/nos-conseils.html#type-verres", "Comprendre les verres progressifs",
         "Comment fonctionne un progressif et à qui il s'adresse."),
        ("/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html", "La presbytie expliquée",
         "Pourquoi la vision de près baisse à partir de 45 ans."),
        ("/contact.html", "Essayer en boutique",
         "Un progressif se choisit après mesures précises et essai."),
    ],
}


# ============================================================================
# MAILLAGE INTERNE DES ARTICLES AUTOMATIQUES
#
# Les 24 articles ecrits a la main ont un plan de liens redige a la main
# (INLINE_LINKS et GO_FURTHER ci-dessus). Un article produit par la veille
# hebdomadaire n'en a pas : on le lui fabrique ici, de facon deterministe.
#
# Choix assume : les URL cibles sont ecrites EN DUR dans ce fichier, jamais
# proposees par le modele qui redige l'article. Un lien interne casse est
# invisible pour le visiteur jusqu'au clic, et couteux en referencement ; la
# seule facon de le rendre impossible est que la veille n'ait pas son mot a
# dire sur les adresses. Le modele ecrit le texte, build.py pose les liens.
# ============================================================================

# Ordre = priorite. On garde les trois premieres expressions trouvees dans le
# corps de l'article, une occurrence chacune, jamais dans un titre ni dans un
# lien existant (apply_inline_links s'en charge deja).
AUTO_INLINE_KEYWORDS = [
    ("bilan auditif", "/index.html#test-auditif"),
    ("aides auditives", "/espace-audition.html"),
    ("appareils auditifs", "/espace-audition.html"),
    ("audioprothesiste", "/espace-audition.html"),
    ("audioprothésiste", "/espace-audition.html"),
    ("acouphènes", "/actualites/acouphenes-comprendre-bruit-qui-ne-sarrete-jamais.html"),
    ("examen de vue", "/index.html#examen-de-vue"),
    ("verres progressifs", "/nos-conseils.html#type-verres"),
    ("presbytie", "/actualites/presbytie-comprendre-ce-trouble-de-la-vision.html"),
    ("myopie", "/espace-sante.html#myopie-enfant"),
    ("astigmatisme", "/espace-sante.html#defauts"),
    ("lumière bleue", "/nos-conseils.html#traitements-verres"),
    ("fatigue visuelle", "/actualites/fatigue-oculaire-ecrans.html"),
    ("100&nbsp;% Santé", "/actualites/100-pour-cent-sante-2026.html"),
    ("100 % Santé", "/actualites/100-pour-cent-sante-2026.html"),
    ("lentilles de contact", "/nos-conseils.html#lunettes-ou-lentilles"),
    ("verres", "/nos-conseils.html#traitements-verres"),
    ("monture", "/marques.html"),
    ("Olympiades", "/contact.html"),
]
AUTO_INLINE_MAX = 3

# Deux pages de service par categorie ; le troisieme lien de l'encadre "Pour
# aller plus loin" est calcule plus bas, en pointant vers l'article existant le
# plus recent de la meme categorie (donc toujours une URL qui existe).
AUTO_GO_FURTHER_PAGES = {
    "sante-visuelle": [
        ("/espace-sante.html", "Notre Espace Santé Visuelle",
         "Examen de vue, dépistage et suivi de la correction en boutique."),
        ("/index.html#examen-de-vue", "L'examen de vue gratuit",
         "Sans rendez-vous, une vingtaine de minutes."),
    ],
    "mode-lunettes": [
        ("/marques.html", "Nos marques en boutique",
         "La sélection que nous portons et défendons."),
        ("/nos-conseils.html#choix-monture", "Bien choisir sa monture",
         "Forme, matière, proportions : ce qui change vraiment le confort."),
    ],
    "tech-verres": [
        ("/nos-conseils.html#type-verres", "Quel type de verre pour quel usage",
         "Unifocaux, progressifs, dégressifs : les distinguer."),
        ("/nos-conseils.html#traitements-verres", "Les traitements de verres",
         "Anti-reflet, durcissement, filtres : à quoi ils servent."),
    ],
    "tech-lentilles": [
        ("/nos-conseils.html#lunettes-ou-lentilles", "Lunettes ou lentilles",
         "Les critères qui font pencher d'un côté ou de l'autre."),
        ("/espace-sante.html", "Notre Espace Santé Visuelle",
         "Adaptation, contrôle et suivi des porteurs de lentilles."),
    ],
    "remboursements": [
        ("/actualites/100-pour-cent-sante-2026.html", "Vos remboursements en 2026",
         "Ce que couvre le 100&nbsp;% Santé en optique."),
        ("/contact.html", "Poser vos questions en boutique",
         "Nous établissons le devis normalisé et vérifions vos droits."),
    ],
    "vie-boutique": [
        ("/notre-histoire.html", "Notre histoire dans ce quartier",
         "Pourquoi nous avons choisi les Olympiades pour ouvrir."),
        ("/contact.html", "Venir nous voir Centre commercial Grand Angle",
         "Adresse, horaires et accès en métro, bus ou à pied."),
    ],
    "enfant": [
        ("/espace-sante.html#myopie-enfant", "Le dépistage chez l'enfant",
         "Repérer tôt, freiner la progression de la myopie."),
        ("/espace-audition.html", "Notre Espace Audition",
         "Nous réalisons aussi les bilans auditifs de l'enfant."),
    ],
}
AUTO_GO_FURTHER_FALLBACK = [
    ("/espace-sante.html", "Notre Espace Santé Visuelle",
     "Examen de vue, dépistage et suivi de la correction en boutique."),
    ("/contact.html", "Venir nous voir Centre commercial Grand Angle",
     "Adresse, horaires et accès en métro, bus ou à pied."),
]


def _auto_inline_plan(article):
    """Choisit jusqu'a AUTO_INLINE_MAX liens contextuels pour un article auto."""
    body = article["body"]
    own_url = "/%s" % article_url(article)
    plan, used_targets = [], set()
    for phrase, href in AUTO_INLINE_KEYWORDS:
        if len(plan) >= AUTO_INLINE_MAX:
            break
        if href in used_targets or href == own_url:
            continue
        if not _link_candidates(body, phrase):
            continue
        plan.append((phrase, href))
        used_targets.add(href)
    return plan


def _auto_go_further(article):
    """Deux pages de service + l'article existant le plus recent de la categorie."""
    items = list(AUTO_GO_FURTHER_PAGES.get(article["category"], AUTO_GO_FURTHER_FALLBACK))
    same = [a for a in ARTICLES
            if a["category"] == article["category"] and a["slug"] != article["slug"]]
    same.sort(key=lambda a: a["date_iso"], reverse=True)
    for candidate in same:
        href = "/%s" % article_url(candidate)
        if any(href == h for h, _l, _d in items):
            continue
        items.append((href, candidate["title"], candidate["excerpt"]))
        break
    return items[:3]


for _auto in AUTO_ARTICLES:
    if _auto["slug"] not in INLINE_LINKS:
        INLINE_LINKS[_auto["slug"]] = _auto_inline_plan(_auto)
    if _auto["slug"] not in GO_FURTHER:
        GO_FURTHER[_auto["slug"]] = _auto_go_further(_auto)


def render_go_further(article):
    items = GO_FURTHER.get(article["slug"])
    if not items:
        return ""
    lis = "\n".join(
        '        <li><span class="arrow" aria-hidden="true">→</span>'
        '<a href="%s">%s<span class="go-desc">%s</span></a></li>' % (href, label, desc)
        for href, label, desc in items
    )
    return """
    <div class="go-further">
      <span class="eyebrow">Pour aller plus loin</span>
      <h3>À lire et à voir sur le site</h3>
      <ul>
%s
      </ul>
    </div>
""" % lis


# --- Gabarit SEO : bloc reponse en tete + FAQ visible ----------------------
def render_answer_lead(article):
    """Reponse directe de 40-60 mots, juste sous le titre.

    Champ optionnel `answer` de l'article. Absent => rien n'est rendu, les
    anciens articles restent valides.
    """
    ans = article.get("answer")
    if not ans:
        return ""
    return """
    <div class="answer-lead">
      <span class="eyebrow">En bref</span>
      <p>%s</p>
    </div>
""" % ans


def render_faq(article):
    """FAQ visible en HTML (champ optionnel `faq` : liste de (question, reponse)).

    Volontairement sans balisage FAQPage : Google a supprime le rich result
    FAQ en mai-juin 2026. Le format garde sa valeur pour le lecteur et pour
    les moteurs de reponse, mais on n'attend plus d'affichage enrichi.
    """
    items = article.get("faq")
    if not items:
        return ""
    blocks = "\n".join(
        '      <div class="faq-item">\n'
        '        <h3>%s</h3>\n'
        '        <p>%s</p>\n'
        '      </div>' % (q, a)
        for q, a in items
    )
    return """
    <div class="article-faq">
      <h2>Questions fréquentes</h2>
      <p class="faq-intro">Les questions qu'on nous pose le plus souvent en boutique sur ce sujet.</p>
%s
    </div>
""" % blocks


def source_note(article):
    """Encart de sources en fin d'article.

    Si l'article renseigne `sources` (liste de (nom, url)), on les cite
    nommement avec un lien : c'est un signal E-E-A-T important sur un sujet
    sante, et c'est ce qui rend un contenu citable par les moteurs de reponse.
    Sinon on retombe sur la note generique historique.
    """
    srcs = article.get("sources")
    updated = article.get("updated_display")
    base = ("Contenu rédigé par l'équipe ACTU EYES à partir de sources "
            "professionnelles vérifiées (fabricants, presse spécialisée, "
            "autorités de santé)")
    if srcs:
        links = ", ".join('<a href="%s" rel="nofollow noopener" target="_blank">%s</a>' % (u, n)
                          for n, u in srcs)
        base = ("Contenu rédigé par l'équipe ACTU EYES. Sources consultées "
                "pour cet article : " + links)
    if updated:
        base += ". Mis à jour le %s" % updated
    return base + "."


def related_articles(article, count=3):
    """Selection thematique : meme categorie d'abord, puis les plus recents.

    Remplace la rotation chronologique d'origine (idx+1, +2, +3), qui pouvait
    faire suivre un article sur l'audition de trois articles sur les montures.
    """
    others = [a for a in ARTICLES if a["slug"] != article["slug"]]
    same = [a for a in others if a["category"] == article["category"]]
    rest = [a for a in others if a["category"] != article["category"]]
    same.sort(key=lambda a: a["date_iso"], reverse=True)
    rest.sort(key=lambda a: a["date_iso"], reverse=True)
    return (same + rest)[:count]


# --- Bloc "Nos articles sur le sujet" sur les pages de service -------------
PAGE_ARTICLES = {
    "espace-sante.html": (
        "Comprendre sa vue",
        ["presbytie-comprendre-ce-trouble-de-la-vision",
         "fatigue-oculaire-ecrans",
         "ecrans-myopie-enfant-habitudes-protectrices"],
    ),
    "espace-audition.html": (
        "Comprendre son audition",
        ["perte-auditive-signes-precoces",
         "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais",
         "casques-ecouteurs-proteger-audition-jeunes"],
    ),
    "nos-conseils.html": (
        "Aller plus loin",
        ["nouvelles-technologies-verres-correcteurs",
         "renouveler-lunettes-sans-nouvelle-ordonnance-opticien",
         "comprendre-devis-normalise-lunettes"],
    ),
    "marques.html": (
        "Mode & tendances",
        ["tendances-montures-2026",
         "lunettes-engagees-matieres-durables-eco-responsables",
         "lunettes-connectees-ray-ban-meta-mode-tech"],
    ),
    "notre-histoire.html": (
        "Vie de la boutique",
        ["comment-nous-choisissons-nos-montures",
         "dans-les-coulisses-de-notre-atelier",
         "reprise-actueyes-histoire-opticien-montreuil",
         "une-journee-type-a-la-boutique",
         "opticien-coeur-de-ville-grand-angle-montreuil"],
    ),
}


def render_page_articles(path):
    entry = PAGE_ARTICLES.get(path)
    if not entry:
        return ""
    eyebrow, slugs = entry
    by_slug = {a["slug"]: a for a in ARTICLES}
    chosen = [by_slug[s] for s in slugs if s in by_slug]
    if not chosen:
        return ""
    return """
<section class="related-articles story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">%s</span>
      <h2>Nos articles sur le sujet</h2>
    </div>
    <div class="article-grid">
%s
    </div>
    <div class="block-more-center"><a href="/actualites.html" class="block-more">Voir toutes nos actualités →</a></div>
  </div>
</section>
""" % (eyebrow, chr(10).join(render_article_card(a) for a in chosen))


def with_page_articles(path, body):
    """Insere le bloc articles juste avant le CTA final de la page."""
    block = render_page_articles(path)
    if not block:
        return body
    marker = '<section class="cta-band">'
    idx = body.rfind(marker)
    if idx == -1:
        return body + block
    return body[:idx] + block + "\n" + body[idx:]


# ============================================================================
# PAGE 9 - mentions-legales.html
# Creee le 01/08/2026. Obligation legale (LCEN art. 6-III) : la page
# n'existait pas et renvoyait un 404. Elle n'est PAS dans NAV_ITEMS (pas
# d'onglet en haut) : on y accede uniquement par le pied de page, present
# sur les 33 pages. D'ou le breadcrumb_override explicite a l'appel.
# ============================================================================
BODY_MENTIONS = """
<section class="page-hero page-hero--compact">
  <div class="container">
    <span class="eyebrow">Informations légales</span>
    <h1>Mentions légales &amp; confidentialité</h1>
    <p>Qui édite ce site, qui l'héberge, ce que nous faisons — et surtout ce que nous ne faisons pas — de vos données.</p>
  </div>
</section>

<style>
.legal{background:var(--cream);padding:86px 0 100px;}
.legal .container{max-width:820px;}
.legal h2{font-family:'Fraunces',serif;font-size:clamp(22px,2.6vw,28px);margin:52px 0 16px;color:var(--charcoal);}
.legal h2:first-of-type{margin-top:0;}
.legal h3{font-size:16px;margin:26px 0 10px;color:var(--charcoal);font-weight:600;}
.legal p{color:var(--charcoal-soft);font-size:15.5px;line-height:1.75;margin-bottom:15px;}
.legal ul{margin:0 0 18px;padding-left:0;list-style:none;}
.legal ul li{color:var(--charcoal-soft);font-size:15.5px;line-height:1.75;padding-left:18px;position:relative;margin-bottom:7px;}
.legal ul li::before{content:"—";position:absolute;left:0;color:var(--wood-dark);}
.legal .legal-card{background:var(--cream-2);border:1px solid var(--line);border-radius:4px;padding:28px 30px;margin-bottom:8px;}
.legal .legal-card p:last-child{margin-bottom:0;}
.legal .legal-maj{font-size:13.5px;color:var(--charcoal-soft);margin-top:56px;padding-top:22px;border-top:1px solid var(--line);}
</style>
<section class="legal">
  <div class="container">

    <h2>Éditeur du site</h2>
    <div class="legal-card">
      <p>Le site <strong>actueyes-montreuil.fr</strong> est édité par la société <strong>I2M OPTIQUE</strong>, exerçant sous le nom commercial <strong>ACTU EYES</strong>.</p>
      <ul>
        <li>Société par actions simplifiée (SAS) au capital de 5 000,00 € <!-- capital à confirmer --></li>
        <li>Siège social : 15 rue des Lumières, Centre commercial Grand Angle, 93100 Montreuil</li>
        <li>Immatriculée au RCS de Bobigny sous le numéro 839 017 092</li>
        <li>SIRET : 839 017 092 00017</li>
        <li>Numéro de TVA intracommunautaire : FR34 839 017 092</li>
        <li>Code APE / NAF : 47.78A — commerce de détail d'optique</li>
        <li>Téléphone : <a href="tel:0148575740">01 48 57 57 40</a></li>
        <li>Courriel : <a href="mailto:actueyes.montreuil@gmail.com">actueyes.montreuil@gmail.com</a></li>
      </ul>
    </div>

    <h2>Directeur de la publication</h2>
    <p>Monsieur Mikhael Saada, représentant la société MS CONSULTING, présidente de la société I2M OPTIQUE.</p>

    <h2>Hébergeur</h2>
    <p>Le site est hébergé par <strong>IONOS SARL</strong>, société à responsabilité limitée dont le siège social est situé 7 place de la Gare, 57200 Sarreguemines, France, immatriculée au RCS de Sarreguemines sous le numéro 431 303 775. Site : <a href="https://www.ionos.fr" target="_blank" rel="noopener">www.ionos.fr</a>.</p>

    <h2>Activité réglementée</h2>
    <p>La profession d'opticien-lunetier est une profession de santé réglementée en France, régie par les articles L. 4362-1 et suivants du code de la santé publique. Son exercice est subordonné à la détention d'un diplôme reconnu par l'État et à l'enregistrement auprès de l'autorité compétente.</p>
    <p>Les informations de santé publiées sur ce site, notamment dans les rubriques Espace Santé et Actualités, ont une vocation strictement informative. Elles ne constituent en aucun cas un diagnostic, une prescription ou un avis médical, et ne remplacent pas une consultation auprès d'un ophtalmologiste ou de tout autre professionnel de santé compétent.</p>

    <h2>Propriété intellectuelle</h2>
    <p>L'ensemble des éléments composant ce site — structure, textes, articles, photographies, illustrations, logotypes et identité graphique — est la propriété de la société I2M OPTIQUE ou fait l'objet d'une autorisation d'usage, et est protégé par le code de la propriété intellectuelle.</p>
    <p>Toute reproduction, représentation, adaptation ou exploitation, totale ou partielle, sur quelque support que ce soit, sans l'autorisation écrite préalable de l'éditeur, est interdite. Une courte citation reste possible dans les conditions prévues à l'article L. 122-5 du code de la propriété intellectuelle, à condition d'indiquer clairement la source et de renvoyer vers la page d'origine.</p>
    <p>Les marques et logotypes des fabricants cités sur ce site (notamment dans la rubrique Nos Marques) demeurent la propriété exclusive de leurs titulaires respectifs. Ils sont mentionnés à titre d'information, pour indiquer les collections disponibles en boutique.</p>

    <h2>Liens vers d'autres sites</h2>
    <p>Ce site comporte des liens vers des sites tiers — sites de fabricants, ressources institutionnelles citées en source d'articles, fiche Google de l'établissement. Ces liens sont proposés pour votre information. Nous n'exerçons aucun contrôle sur le contenu de ces sites et ne saurions être tenus responsables de leur contenu, de leurs pratiques ni de leur politique de confidentialité.</p>

    <h2 id="confidentialite">Données personnelles</h2>
    <p>Nous avons fait un choix simple : <strong>ce site ne collecte aucune donnée personnelle</strong>. Il ne comporte ni formulaire, ni espace client, ni inscription à une lettre d'information, ni outil de mesure d'audience. Vous pouvez le consulter intégralement sans nous transmettre quoi que ce soit.</p>

    <h3>Si vous nous contactez</h3>
    <p>Lorsque vous nous écrivez à actueyes.montreuil@gmail.com ou que vous nous appelez au 01 48 57 57 40, les informations que vous nous communiquez (nom, coordonnées, objet de votre demande) sont utilisées dans le seul but de vous répondre et, le cas échéant, d'organiser votre venue en boutique. Elles ne sont ni revendues, ni cédées, ni utilisées à des fins de prospection. La base légale de ce traitement est votre demande elle-même, au sens de l'article 6.1.b du RGPD. Ces échanges sont conservés le temps nécessaire au traitement de votre demande, puis au maximum trois ans à compter du dernier contact.</p>

    <h3>Les données de santé</h3>
    <p>Les données relatives à votre vue (ordonnances, mesures, résultats d'examen) sont recueillies <strong>en boutique uniquement</strong>, dans le cadre de notre activité de professionnels de santé, et jamais par l'intermédiaire de ce site. Elles sont traitées de manière confidentielle, conservées dans les conditions prévues par la réglementation applicable aux professionnels de santé, et ne sont transmises qu'aux organismes strictement nécessaires à la prise en charge de votre équipement — votre caisse d'assurance maladie et votre complémentaire santé, à votre demande.</p>

    <h3>Vos droits</h3>
    <p>Conformément au règlement (UE) 2016/679 (RGPD) et à la loi Informatique et Libertés, vous disposez d'un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité sur les données vous concernant. Pour l'exercer, écrivez-nous à <a href="mailto:actueyes.montreuil@gmail.com">actueyes.montreuil@gmail.com</a> ou passez à la boutique. Nous vous répondrons dans un délai d'un mois. Si notre réponse ne vous satisfait pas, vous pouvez introduire une réclamation auprès de la CNIL — 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07, <a href="https://www.cnil.fr" target="_blank" rel="noopener">www.cnil.fr</a>.</p>

    <h2>Cookies et contenus tiers</h2>
    <p>Ce site ne dépose <strong>aucun cookie publicitaire ni aucun cookie de mesure d'audience</strong>. C'est la raison pour laquelle vous ne voyez pas de bandeau de consentement en arrivant : il n'y a rien à consentir.</p>
    <p>Une seule exception mérite d'être signalée. La page <a href="/contact.html">Nous rendre visite</a> affiche un plan Google Maps intégré, afin que vous puissiez situer la boutique au centre commercial Grand Angle sans quitter le site. Ce plan est fourni par Google, et son affichage peut conduire Google à déposer des cookies ou à lire des identifiants sur votre terminal, selon des modalités qui lui sont propres et sur lesquelles nous n'avons pas la main. Si vous préférez l'éviter, il vous suffit de ne pas ouvrir cette page, ou de bloquer les cookies tiers dans les réglages de votre navigateur — le reste du site fonctionne à l'identique. La politique de confidentialité de Google est consultable à l'adresse <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">policies.google.com/privacy</a>.</p>
    <p>Notre hébergeur conserve par ailleurs, pour des raisons techniques et de sécurité, des journaux de connexion (adresse IP, date et heure d'appel, pages consultées) pendant la durée légale de conservation. Nous ne les exploitons pas à des fins statistiques ou commerciales.</p>

    <h2>Médiation de la consommation</h2>
    <p>Conformément aux articles L. 611-1 et suivants du code de la consommation, tout consommateur a le droit de recourir gratuitement à un médiateur de la consommation en vue de la résolution amiable d'un litige qui l'oppose à un professionnel, après avoir tenté au préalable de le résoudre directement auprès de celui-ci par une réclamation écrite.</p>
    <p>Avant toute démarche de médiation, nous vous invitons donc à nous adresser votre réclamation par courriel à <a href="mailto:actueyes.montreuil@gmail.com">actueyes.montreuil@gmail.com</a> ou par courrier à l'adresse de la boutique : nous nous efforçons de traiter chaque situation directement, et c'est presque toujours la voie la plus rapide.</p>
    <p>Si aucune solution n'a pu être trouvée dans un délai d'un an à compter de votre réclamation écrite, vous pouvez saisir gratuitement le médiateur dont relève l'établissement, en sa qualité d'adhérent de la Centrale des Opticiens (CDO) :</p>
    <div class="legal-card">
      <ul>
        <li><strong>Médiation du commerce coopératif et associé (MCCA)</strong></li>
        <li>77 rue de Lourmel, 75015 Paris</li>
        <li>Saisine en ligne : <a href="https://www.mcca-mediation.fr" target="_blank" rel="noopener">www.mcca-mediation.fr</a></li>
        <li>Courriel : <a href="mailto:mediateur@mcca-mediation.fr">mediateur@mcca-mediation.fr</a></li>
      </ul>
    </div>
    <p>Le recours au médiateur est gratuit pour le consommateur et n'est possible qu'après une réclamation écrite préalable restée sans réponse satisfaisante. Il ne vous prive à aucun moment de la faculté de saisir la juridiction compétente.</p>

    <h2>Droit applicable</h2>
    <p>Le présent site et les présentes mentions sont soumis au droit français. En cas de litige et à défaut de résolution amiable, les tribunaux français sont seuls compétents.</p>

    <p class="legal-maj">Dernière mise à jour : août 2026. Ces mentions peuvent être modifiées à tout moment pour tenir compte d'une évolution du site ou de la réglementation.</p>

  </div>
</section>

<section class="cta-band">

  <div class="container">
    <h2>Une question sur ce site ou sur vos données ?</h2>
    <p>Écrivez-nous, ou passez simplement nous voir Centre commercial Grand Angle — 15 rue des Lumières.</p>
    <a href="/contact.html" class="btn btn-primary">Nous contacter</a>
  </div>
</section>
"""


def render_accueil_body():
    """Page d'accueil : injecte l'apercu des 3 actualites les plus recentes.

    Les cartes reutilisent render_article_card() donc exactement le meme markup
    (et le meme CSS) que la page Actualites. Le script "bulle" qui intercepte le
    clic n'existe que sur actualites.html : ici, les cartes restent de simples
    liens vers la page de l'article, ce qui est le comportement voulu.
    """
    latest = sorted(ARTICLES, key=lambda a: a["date_iso"], reverse=True)[:3]
    cards = "\n".join(render_article_card(a) for a in latest)
    teaser = f"""<section class="services alt">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Actualités</span>
      <h2>Nos derniers articles</h2>
      <p>Santé visuelle, tendances mode et innovations verres et lentilles : nous publions régulièrement de quoi y voir plus clair.</p>
    </div>
    <div class="article-grid">
{cards}
    </div>
    <div style="text-align:center;margin-top:44px;">
      <a href="/actualites.html" class="btn btn-outline">Voir toutes les actualités</a>
    </div>
  </div>
</section>"""
    assert BODY_BOUTIQUE.count("<!--ACTUALITES_TEASER-->") == 1
    return BODY_BOUTIQUE.replace("<!--ACTUALITES_TEASER-->", teaser)


def render_actualites_index():
    filter_pills = ['      <button class="filter-pill active" data-filter="all">Tous</button>']
    for key, _ in CATEGORY_ORDER:
        filter_pills.append(f'      <button class="filter-pill" data-filter="{key}">{ARTICLE_CATEGORIES[key]["label"]}</button>')
    cards = "\n".join(render_article_card(a) for a in ARTICLES)
    filter_script = """
<script>
  const pills = document.querySelectorAll('.filter-pill');
  const cards = document.querySelectorAll('.article-card');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const filter = pill.dataset.filter;
      cards.forEach(card => {
        card.style.display = (filter === 'all' || card.dataset.category === filter) ? '' : 'none';
      });
    });
  });
</script>"""
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Actualités</div>
    <span class="eyebrow">Le journal ACTU EYES</span>
    <h1>Actualités</h1>
    <p>Santé visuelle, mode et tendances, technologies verres et lentilles, remboursements, vie de la boutique : nos conseils et décryptages, mis à jour régulièrement.</p>
  </div>
</section>

<section class="story-block">
  <div class="container">
    <div class="article-filter-bar">
{chr(10).join(filter_pills)}
    </div>
    <div class="article-grid">
{cards}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une question sur votre vue ?</h2>
    <p>Nos conseils en ligne ne remplacent pas un vrai échange avec l'équipe — venez nous en parler en boutique.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
{filter_script}
"""


def render_article_page(article):
    related = related_articles(article)
    cat = ARTICLE_CATEGORIES[article["category"]]
    breadcrumb = [
        ("La Boutique", f"{BASE_URL}/"),
        ("Actualités", f"{BASE_URL}/actualites.html"),
        (article["title"], f"{BASE_URL}/{article_url(article)}"),
    ]
    body = f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / <a href="/actualites.html">Actualités</a> / {article["title"]}</div>
    <span class="eyebrow">{cat["label"]}</span>
    <h1>{article["title"]}</h1>
    <div class="article-meta-row">
      <span class="article-tag" style="--accent:{cat["accent"]};--accent-bg:{cat["accent_bg"]};">{cat["label"]}</span>
      <span class="article-date">{article["date_display"]}</span>
    </div>
  </div>
</section>

<section class="article-prose story-block" data-date-iso="{article["date_iso"]}">
  <div class="container-narrow">
    <div class="arch-frame reveal" style="margin-bottom:40px;aspect-ratio:16/9;border-radius:24px;">
      <img src="{article["image"]}" alt="{article["image_alt"]}">
    </div>
    {render_answer_lead(article)}
    {apply_inline_links(article["body"], INLINE_LINKS.get(article["slug"], []), article["slug"])}
    {render_faq(article)}
    {render_go_further(article)}
    <div class="article-source-note">{source_note(article)}</div>
  </div>
</section>

<section class="related-articles story-block">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">À lire aussi</span>
      <h2>D'autres articles qui pourraient vous intéresser</h2>
    </div>
    <div class="article-grid">
{chr(10).join(render_article_card(a) for a in related)}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Envie d'en discuter avec nous ?</h2>
    <p>Prenez rendez-vous en boutique, Centre commercial Grand Angle, pour un conseil personnalisé.</p>
    <a href="/contact.html" class="btn btn-primary">Prendre rendez-vous</a>
  </div>
</section>
"""
    render_page(
        "actualites",
        article["meta_title"],
        article["meta_description"],
        article_url(article),
        body,
        hero_img=article["image"],
        extra_jsonld=article_jsonld(article),
        breadcrumb_override=breadcrumb,
    )


def sync_sitemap():
    """Ajoute au sitemap les articles qui n'y figurent pas encore.

    Volontairement additif : les <lastmod> deja en place ne sont jamais
    reecrits, pour ne pas signaler aux moteurs une modification qui n'a pas eu
    lieu. Sans effet si tous les articles sont deja references.
    """
    path = os.path.join(OUT_DIR, "sitemap.xml")
    if not os.path.exists(path):
        print("sitemap.xml absent : etape ignoree.")
        return 0
    with open(path, encoding="utf-8") as f:
        content = f.read()

    blocks = []
    for a in ARTICLES:
        loc = f"{BASE_URL}/{article_url(a)}"
        if f"<loc>{loc}</loc>" in content:
            continue
        blocks.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{a.get('updated_iso') or a['date_iso']}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.6</priority>\n"
            "  </url>\n"
        )

    if not blocks:
        print("sitemap.xml : deja a jour.")
        return 0

    closing = "</urlset>"
    assert content.count(closing) == 1, "sitemap.xml : balise </urlset> introuvable ou dupliquee"
    content = content.replace(closing, "".join(blocks) + closing)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"sitemap.xml : {len(blocks)} URL ajoutee(s).")
    return len(blocks)

BODY_ENFANTS = """
<section class="page-hero page-hero--plain">
  <div class="container">
    <div class="breadcrumb"><a href="/index.html">La Boutique</a> / Espace enfants</div>
    <span class="eyebrow">Espace enfants</span>
    <h1>Les lunettes de vos enfants</h1>
    <p>Une monture qui tient, des verres qui protègent, et un vrai accompagnement contre la myopie : équiper un enfant est un métier à part entière. Voici tout ce qu'il faut savoir avant de choisir.</p>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <span class="eyebrow">Le principe</span>
    <h2>Pourquoi une lunette d'enfant n'est pas une lunette d'adulte en plus petit</h2>
    <p>Un enfant bouge, tombe, oublie, grandit. Sa monture doit encaisser tout cela sans blesser ni casser, rester parfaitement centrée sur un tout petit écart entre les yeux, et surtout lui plaire assez pour qu'il la garde sur le nez — car une paire qui finit dans le cartable ne corrige rien. À cela s'ajoute un enjeu propre à l'enfance : la vue se construit dans les premières années, et une correction portée en continu fait partie du traitement, pas seulement du confort. C'est pourquoi nous prenons, pour un enfant, encore plus de temps que pour un adulte.</p>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">La monture</span>
        <h2>Comment choisir une monture pour un enfant&nbsp;?</h2>
        <p>Quatre critères priment, dans cet ordre&nbsp;: la sécurité, la tenue, le confort et le plaisir. Le style vient après — mais il compte, car c'est lui qui fait que l'enfant l'adopte.</p>
        <ul class="check-list">
          <li><span class="check">&#10003;</span> <strong>Des matières souples et incassables</strong> (silicone pour les bébés, TR90 ou acétate résistant ensuite)&nbsp;: elles plient au lieu de casser et supportent les chocs.</li>
          <li><span class="check">&#10003;</span> <strong>Des charnières flex</strong> (à ressort) qui accompagnent le mouvement sans casser, et aucune arête vive.</li>
          <li><span class="check">&#10003;</span> <strong>Une bonne tenue</strong>&nbsp;: branches enveloppantes «&nbsp;câble&nbsp;» qui passent derrière l'oreille, ou bandeau élastique réglable pour les tout-petits.</li>
          <li><span class="check">&#10003;</span> <strong>Un centrage précis</strong> sur un petit écart pupillaire, et une taille juste&nbsp;: ni trop large (elle glisse), ni trop petite (elle marque).</li>
          <li><span class="check">&#10003;</span> <strong>De la légèreté</strong> et un pont adapté à un nez encore peu marqué, avec des plaquettes souples si besoin.</li>
        </ul>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/enfants/monture-enfant.jpg" alt="Ajustement d'une monture souple sur un enfant en boutique" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <span class="eyebrow">Les formes</span>
    <h2>Quelle forme selon l'âge et le visage&nbsp;?</h2>
    <p>La bonne forme évolue avec l'enfant, et se choisit toujours à l'essayage.</p>
    <h3>Le tout-petit (0-3 ans)</h3>
    <p>Priorité absolue à la sécurité et au maintien&nbsp;: monture entièrement souple, sans charnière rigide, tenue par un bandeau élastique. La forme reste ronde et douce, sans angle. L'objectif est qu'elle ne bouge pas et ne fasse jamais mal.</p>
    <h3>L'enfant (3-10 ans)</h3>
    <p>On gagne en choix. Les formes rondes ou légèrement carrées conviennent à la plupart des visages&nbsp;; l'important est que la monture couvre bien le champ de vision (l'enfant ne doit pas regarder par-dessus) et remonte assez haut sur le nez. Les branches câble sécurisent la tenue pendant la récréation.</p>
    <h3>Le pré-ado et l'ado</h3>
    <p>Le style prend le dessus, et c'est tant mieux&nbsp;: à cet âge, le meilleur gage de port régulier est une monture que l'ado a choisie et qu'il assume. On raisonne alors comme pour un adulte — forme adaptée à la morphologie du visage — tout en gardant un œil sur la solidité.</p>
  </div>
</section>

<section class="split story-block">
  <div class="container">
    <div class="split-grid">
      <div class="arch-frame reveal">
        <img src="/images/enfants/verres-enfant.jpg" alt="Verres légers et résistants pour lunettes d'enfant" loading="lazy">
      </div>
      <div class="split-text reveal">
        <span class="eyebrow">Les verres</span>
        <h2>Quels verres pour les enfants&nbsp;?</h2>
        <p>Pour un enfant, le verre se choisit d'abord pour sa résistance et sa légèreté, avant tout raffinement esthétique.</p>
        <ul class="check-list">
          <li><span class="check">&#10003;</span> <strong>Le polycarbonate</strong>&nbsp;: très résistant aux chocs et léger, c'est le matériau de référence pour les enfants actifs. Il intègre nativement une protection contre les UV.</li>
          <li><span class="check">&#10003;</span> <strong>Un traitement antireflet et anti-rayure</strong>&nbsp;: plus de confort à l'écran et à l'école, et des verres qui résistent mieux aux nettoyages énergiques.</li>
          <li><span class="check">&#10003;</span> <strong>La protection solaire</strong>&nbsp;: le cristallin de l'enfant filtre moins bien les UV que celui de l'adulte. Des solaires de catégorie&nbsp;3 marquées UV400, ou des verres photochromiques, sont vivement recommandés en extérieur.</li>
          <li><span class="check">&#10003;</span> <strong>La correction, bien sûr</strong>, exactement conforme à l'ordonnance de l'ophtalmologiste, et recentrée à chaque évolution.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<style>
.enf-terra{background:var(--terracotta);}
.enf-terra .eyebrow{color:var(--cream);}
.enf-terra h2{color:var(--cream);}
.enf-terra p{color:rgba(251,246,239,0.9);}
.enf-terra .dark-card{background:rgba(251,246,239,0.10);border:1px solid rgba(251,246,239,0.26);}
.enf-terra .dark-card h3{color:var(--cream);}
.enf-terra .dark-card p{color:rgba(251,246,239,0.88);}
.enf-terra a.ilink{color:var(--cream);border-bottom:1px solid rgba(251,246,239,0.5);}
</style>
<section class="dark-section enf-terra">
  <div class="container">
    <div class="section-head center">
      <span class="eyebrow">Le sujet clé</span>
      <h2>Les verres qui freinent la myopie</h2>
      <p>La myopie de l'enfant augmente partout, et elle a tendance à progresser tant que l'œil grandit. La bonne nouvelle&nbsp;: on sait aujourd'hui la <strong>ralentir</strong>. L'objectif n'est plus seulement de corriger, mais de limiter la myopie à l'âge adulte — et donc le risque de complications plus tard.</p>
    </div>
    <div class="card-grid-3">
      <div class="dark-card reveal">
        <h3>Les verres freinateurs</h3>
        <p>De nouveaux verres de lunettes intègrent une multitude de micro-zones qui agissent sur la façon dont l'image se forme en périphérie de la rétine, pour envoyer à l'œil un signal de «&nbsp;ralentissement&nbsp;». Ils se portent comme des verres classiques et corrigent normalement la vision. Ils sont prescrits par l'ophtalmologiste.</p>
      </div>
      <div class="dark-card reveal">
        <h3>Les lentilles</h3>
        <p>Certaines lentilles souples spécifiques, ou l'orthokératologie (lentilles rigides portées la nuit qui remodèlent temporairement la cornée), sont également utilisées pour freiner la myopie chez l'enfant, sous suivi médical.</p>
      </div>
      <div class="dark-card reveal">
        <h3>Les bons réflexes</h3>
        <p>La méthode la plus efficace est gratuite&nbsp;: environ <strong>deux heures de plein air par jour</strong>, à la lumière naturelle, et des pauses régulières dans les activités de près. À combiner avec les solutions optiques prescrites. <a href="/actualites/ecrans-myopie-enfant-habitudes-protectrices.html" class="ilink">En savoir plus sur écrans et myopie</a>.</p>
      </div>
    </div>
    <div class="section-head center" style="margin-top:26px;margin-bottom:0;">
      <p>Ces solutions relèvent d'une <strong>prescription de l'ophtalmologiste</strong>, qui assure aussi le suivi. Notre rôle&nbsp;: vous les expliquer, réaliser l'équipement avec précision et accompagner l'enfant dans la durée.</p>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <span class="eyebrow">Vos remboursements</span>
    <h2>Le 100&nbsp;% Santé pour les enfants</h2>
    <p>Les enfants bénéficient pleinement du 100&nbsp;% Santé&nbsp;: une monture plafonnée à 30&nbsp;€ et des verres traités (amincis selon la correction, antireflet, anti-rayure) intégralement pris en charge par la Sécurité sociale et une complémentaire responsable, sans reste à charge. Particularité importante pour les plus jeunes&nbsp;: le renouvellement est pris en charge <strong>tous les ans avant 16&nbsp;ans</strong> (contre deux ans ensuite), et il peut l'être plus tôt encore si la correction évolue. Nous vérifions vos droits et remettons systématiquement un <a href="/actualites/comprendre-devis-normalise-lunettes.html" class="ilink">devis normalisé</a> gratuit, et vous restez libre de panacher avec une monture à prix libre si votre enfant a un coup de cœur.</p>
  </div>
</section>

<section class="split alt story-block">
  <div class="container">
    <div class="split-grid reverse">
      <div class="split-text reveal">
        <span class="eyebrow">Le suivi</span>
        <h2>Une paire qui grandit avec l'enfant</h2>
        <p>Une monture d'enfant se règle et se re-règle&nbsp;: le visage change, les branches se détendent, une chute déforme un cerclage. Ces ajustements font partie du service, et nous les faisons volontiers aussi souvent qu'il le faut.</p>
        <ul class="check-list">
          <li><span class="check">&#10003;</span> Réajustage gratuit à chaque passage, pour que la monture reste bien positionnée.</li>
          <li><span class="check">&#10003;</span> Remontage de verres neufs sur une monture en bon état quand la correction évolue.</li>
          <li><span class="check">&#10003;</span> Conseils d'entretien et solutions en cas de casse&nbsp;; de nombreuses montures enfant sont garanties.</li>
        </ul>
      </div>
      <div class="arch-frame reveal">
        <img src="/images/enfants/suivi-enfant.jpg" alt="Réglage régulier des lunettes d'un enfant en boutique" loading="lazy">
      </div>
    </div>
  </div>
</section>

<section class="story-block">
  <div class="container-narrow">
    <span class="eyebrow">Qui fait quoi</span>
    <h2>Quand consulter&nbsp;? L'ophtalmologiste d'abord</h2>
    <p>Des dépistages sont prévus dans les premiers mois, vers 3-4&nbsp;ans et à l'entrée en primaire. Entre ces étapes, tout signe qui se répète — un œil qui dévie, l'enfant qui plisse, se rapproche des écrans, saute des lignes, penche la tête ou se plaint de maux de tête — justifie un rendez-vous chez l'<strong>ophtalmologiste</strong>. Chez l'enfant, c'est une étape incontournable&nbsp;: contrairement à l'adulte, l'opticien ne peut pas adapter seul une correction avant 16&nbsp;ans. Notre travail commence ensuite&nbsp;: l'équipement, le réglage et le suivi. <a href="/actualites/signes-troubles-visuels-enfant.html" class="ilink">Voir les signes d'un trouble visuel chez l'enfant</a>.</p>
  </div>
</section>

<section class="story-block" style="padding-top:0;">
  <div class="container-narrow">
    <span class="eyebrow">Nos marques</span>
    <h2>Des montures qui donnent envie d'être portées</h2>
    <p>À côté des tailles junior proposées par de grandes marques, nous mettons en avant des collections pensées pour les enfants&nbsp;: <strong>Playmobil</strong> et <strong>Sonic</strong>, ludiques, colorées et résistantes. Parce qu'une paire que l'enfant a choisie et qu'il aime est une paire qu'il garde sur le nez. <a href="/marques.html#enfants" class="ilink">Voir nos marques enfants</a>.</p>
  </div>
</section>

<section class="faq-section">
  <div class="container-narrow">
    <div class="section-head"><span class="eyebrow">En bref</span><h2>Questions fréquentes</h2></div>
    <details class="faq-item"><summary>À quel âge un enfant peut-il porter des lunettes&nbsp;?<span class="plus">+</span></summary>
      <p>Dès les premiers mois si l'ophtalmologiste le prescrit. Il existe des montures adaptées aux bébés, souples et tenues par un bandeau. Plus la correction utile est portée tôt et régulièrement, mieux la vision se construit.</p></details>
    <details class="faq-item"><summary>Les lunettes de mon enfant sont-elles remboursées&nbsp;?<span class="plus">+</span></summary>
      <p>Oui. Avec le 100&nbsp;% Santé, un équipement de classe A est intégralement pris en charge, sans reste à charge, et renouvelable tous les ans avant 16&nbsp;ans — voire plus tôt si la vue évolue.</p></details>
    <details class="faq-item"><summary>Peut-on vraiment freiner la myopie&nbsp;?<span class="plus">+</span></summary>
      <p>On peut la ralentir. Des verres et lentilles spécifiques, parfois associés à d'autres traitements, sont prescrits par l'ophtalmologiste, et le temps passé dehors joue un rôle protecteur reconnu. L'objectif est de limiter la myopie à l'âge adulte.</p></details>
    <details class="faq-item"><summary>Que faire si mon enfant casse ses lunettes&nbsp;?<span class="plus">+</span></summary>
      <p>Passez nous voir&nbsp;: beaucoup de réparations se font sur place, et de nombreuses montures enfant sont garanties. Si la monture est encore bonne, on peut souvent n'y remonter que ce qui doit l'être.</p></details>
  </div>
</section>

<section class="cta-band">
  <div class="container">
    <h2>Une première paire à préparer&nbsp;?</h2>
    <p>Venez avec l'ordonnance, on s'occupe du reste — au centre commercial Grand Angle, à Montreuil.</p>
    <a href="/contact.html" class="btn btn-primary">Nous rendre visite</a>
  </div>
</section>
"""



# --- Purge optique-seul : retire tout lien interne vers l'audition ou l'ancien quartier ---
_AUDITION_SLUGS_PURGE = {
    "perte-auditive-signes-precoces",
    "casques-ecouteurs-proteger-audition-jeunes",
    "acouphenes-comprendre-bruit-qui-ne-sarrete-jamais",
    "otites-repetition-enfant-audition-langage",
}
_DEAD_URLS = {"/espace-audition.html"} | {
    "/actualites/%s.html" % _s for _s in _AUDITION_SLUGS_PURGE
}
_DEAD_ANCHOR = {"audition", "aides auditives", "appareils auditifs", "audioprothesiste",
                "audioprothésiste", "audiogramme", "bilan auditif", "Olympiades",
                "Triangle de Choisy"}
def _link_keep(t):
    for e in t:
        if isinstance(e, str) and (e in _DEAD_URLS or e in _DEAD_ANCHOR
                                   or e in _AUDITION_SLUGS_PURGE):
            return False
    return True
for _name in ("INLINE_LINKS", "GO_FURTHER", "AUTO_GO_FURTHER_PAGES"):
    _m = globals().get(_name)
    if isinstance(_m, dict):
        for _k in list(_m.keys()):
            if _k in _AUDITION_SLUGS_PURGE or _k == "espace-audition.html":
                del _m[_k]
                continue
            _m[_k] = [t for t in _m[_k] if _link_keep(t)]
for _name in ("AUTO_GO_FURTHER_FALLBACK", "AUTO_INLINE_KEYWORDS"):
    _l = globals().get(_name)
    if isinstance(_l, list):
        _l[:] = [t for t in _l if _link_keep(t)]
# PAGE_ARTICLES : (titre, [slugs]) — retire la page audition et tout slug audition
_pa = globals().get("PAGE_ARTICLES")
if isinstance(_pa, dict):
    for _k in list(_pa.keys()):
        if _k == "espace-audition.html":
            del _pa[_k]
            continue
        _title, _slugs = _pa[_k]
        _pa[_k] = (_title, [s for s in _slugs if s not in _AUDITION_SLUGS_PURGE])


if __name__ == "__main__":
    css_path = os.path.join(OUT_DIR, "site.css")
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(SHARED_CSS)
    print(f"wrote site.css ({len(SHARED_CSS)} bytes, v={CSS_VERSION})")

    render_page(
        "accueil",
        "ACTU EYES — Opticien à Montreuil | Lunettes & solaires",
        "ACTU EYES, opticien à Montreuil, Centre commercial Grand Angle : lunettes de vue, solaires, lentilles et examen de vue en magasin.",
        "index.html",
        render_accueil_body(),
    )
    render_page(
        "conseils",
        "Nos Conseils — Choisir monture et verres | ACTU EYES",
        "Choisir sa monture, ses verres et leurs traitements selon sa correction, lunettes ou lentilles, entretien et style : les conseils de ACTU EYES, Montreuil.",
        "nos-conseils.html",
        BODY_CONSEILS,
        hero_img="/images/conseils/hero-conseils.jpg",
        # Photo remontee sur cette page : les lunettes etaient coupees en bas.
        hero_pos="50%",
    )
    render_page(
        "sante",
        "Espace Santé : examen de vue et lentilles | ACTU EYES",
        "Examen de vue, contactologie et lentilles, troubles de la vue et maladies de l'œil : l'Espace Santé d'ACTU EYES, opticien à Montreuil.",
        "espace-sante.html",
        BODY_SANTE,
        # Version "elargie" de la photo (31/07/2026) : la photo d'origine est
        # recomposee sur un canevas 4.2:1 (extension floutee issue de la meme
        # image) pour donner du recul sans changer la hauteur du bandeau.
        hero_img="/images/sante/hero-sante-large.jpg",
        # 01/08/2026 — le balisage FAQPage a ete retire : Google a annonce le
        # 08/05/2026 la fin des resultats enrichis FAQ et retire la doc le
        # 15/06/2026. La FAQ reste VISIBLE dans la page (accordeons <details>),
        # seul le JSON-LD disparait. Ne pas le reintroduire.
    )
    render_page(
        "marques",
        "Nos Marques — Ray-Ban, Prada, Dior… | ACTU EYES",
        "Ray-Ban, Dior, Prada, Loewe, Celine, Miu Miu, LOOL, CHIMI : les 27 marques sélectionnées par ACTU EYES, opticien à Montreuil, en quatre familles.",
        "marques.html",
        BODY_MARQUES,
    )
    render_page(
        "sante",
        "Lunettes pour enfants — montures, verres, myopie | ACTU EYES",
        "Choisir une monture d'enfant, les bons verres, la protection contre la myopie et le 100 % Santé : le guide complet d'ACTU EYES, opticien à Montreuil.",
        "enfants.html",
        BODY_ENFANTS,
    )
    render_page(
        "accueil",
        "Notre histoire | ACTU EYES, opticien à Montreuil",
        "L'histoire d'ACTU EYES : une boutique reprise en 2018 au centre Grand Angle, à Montreuil, réinventée autour du conseil et du service client.",
        "notre-histoire.html",
        BODY_HISTOIRE,
        hero_img="/images/accueil/hero-boutique.jpg",
        hero_pos="42%",
        breadcrumb_override=[
            ("La Boutique", f"{BASE_URL}/"),
            ("Notre histoire", f"{BASE_URL}/notre-histoire.html"),
        ],
    )

    render_page(
        "contact",
        "Contact et accès — ACTU EYES, opticien à Montreuil",
        "ACTU EYES, 15 Rue des Lumières, Centre commercial Grand Angle, 93100 Montreuil. Ouvert du lundi au samedi, 10h-19h30. Métro Mairie de Montreuil (ligne 9).",
        "contact.html",
        BODY_CONTACT,
        # Même bandeau et même cadrage que la page "Notre histoire" :
        # même fichier, hero_pos 42%.
        hero_img="/images/accueil/hero-boutique.jpg",
        hero_pos="42%",
    )
    render_page(
        "accueil",
        "Mentions légales & confidentialité | ACTU EYES",
        "Mentions légales de actueyes-montreuil.fr : éditeur SAS I2M Optique, hébergeur, propriété intellectuelle, données personnelles et cookies.",
        "mentions-legales.html",
        BODY_MENTIONS,
        # Sans photo de bandeau, le titre du hero (texte creme) serait invisible
        # sur fond clair : on reprend la meme photo que l'accueil et le contact.
        hero_img="/images/accueil/hero-boutique.jpg",
        breadcrumb_override=[
            ("La Boutique", f"{BASE_URL}/"),
            ("Mentions légales", f"{BASE_URL}/mentions-legales.html"),
        ],
    )

    render_page(
        "actualites",
        "Actualités — Conseils vue & lunettes | ACTU EYES",
        "Le journal d'ACTU EYES : santé visuelle, mode lunettes, technologies verres et lentilles, remboursements et vie de la boutique, à Montreuil.",
        "actualites.html",
        render_actualites_index(),
        # Photo fournie par le client le 31/07/2026 (lettres "NEWS" sur fond
        # corail). Cadrage centre : les lettres sont au milieu de la photo.
        hero_img="/images/actualites/hero-actualites-news.jpg",
        hero_pos="50%",
        # Voile allege sur cette page (choix client) : la photo est tres coloree
        # et le voile standard (0.62 -> 0.78) l'eteignait. Dosage retenu apres
        # mesure de contraste : 4.86:1 sur le paragraphe, 6.62:1 sur le titre,
        # soit au-dessus du seuil WCAG AA de 4.5:1.
        hero_veil="linear-gradient(180deg, rgba(16,16,16,0.42), rgba(16,16,16,0.60))",
    )
    for _article in ARTICLES:
        render_article_page(_article)
    print(f"wrote actualites.html + {len(ARTICLES)} article pages")
    sync_sitemap()
    print("Done.")
