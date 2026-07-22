// ==UserScript==
// @name         Driffle Reveal (pixel clone)
// @namespace    local.driffle.fake-reveal
// @version      2.0.0
// @description  Visual 1:1 clone of Driffle checkout Reveal page using real Driffle assets/tokens
// @author       local
// @match        *://driffle.com/*
// @match        *://*.driffle.com/*
// @run-at       document-idle
// @grant        GM_registerMenuCommand
// @grant        GM_setClipboard
// ==/UserScript==

(function () {
  "use strict";

  // ---- edit product data only ----
  const CFG = {
    email: "john.doe@example.com",
    title: "Crypto Voucher 110 EUR Gift Card (Europe) - Digital Key",
    productType: "giftcard", // giftcard | game | ...
    platform: "Crypto Voucher",
    region: "Europe",
    code: "CV110EU-7X9M2-PLK4Q-NZ8JD-Y3F6R",
    revealedAt: "July 21, 2025 at 07:09 PM UTC",
    localeLabel: "EUR - English",
    // real Driffle CDN cover for Crypto Voucher Europe 110 EUR
    productImg:
      "https://static.driffle.com/fit-in/360x504/media-gallery/production/906fe568-1e0e-45f3-9706-18b3e0067bb1_crypto-voucher-europe-110-eur-110708.png",
    productUrl: "https://driffle.com/store?productType=giftcard&platform=Crypto+Voucher",
  };

  // Official dark theme tokens from Driffle frontend (chunk 35124)
  const T = {
    bg1: "#161616",
    bg2: "#0C0C0C",
    bg3: "#212121",
    bg4: "#353535",
    bg5: "#4B4B4B",
    t1: "#FFFFFF",
    t2: "#BFBFBF",
    t3: "#8F8F8F",
    primary: "#4885FF",
    primaryHover: "#477BFF",
    greyBtn: "#353535",
    greyBtnHover: "#535353",
    border2: "#353535",
    divider: "#ffffff1a",
    radius2: "8px",
    radius3: "12px",
    giftBg: "#FF7F6A",
    giftText: "#FFFFFF",
    stepIdle: "#4D4D4D",
    stepLabelIdle: "#909090",
  };

  const shouldAuto =
    location.hash === "#driffle-reveal" ||
    /(?:^|[?&])driffle_reveal=1(?:&|$)/.test(location.search);

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function typeMeta(type) {
    if (type === "giftcard") return { bg: T.giftBg, text: T.giftText, label: "GIFT CARD" };
    return { bg: T.bg4, text: T.t1, label: String(type).toUpperCase() };
  }

  function openReveal() {
    if (document.documentElement.dataset.driffleFakeReveal === "1") return;
    document.documentElement.dataset.driffleFakeReveal = "1";
    try {
      window.stop();
    } catch (_) {}

    const tag = typeMeta(CFG.productType);
    const origin = location.origin.includes("driffle.com")
      ? location.origin
      : "https://driffle.com";

    const html = `<!DOCTYPE html>
<html lang="en" style="color-scheme:dark">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Reveal Product | Driffle</title>
<link rel="icon" href="${origin}/site-assets/favicon.ico"/>
<style>
@font-face{font-family:Onest-Regular;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:Onest-Medium;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:500;font-style:normal;font-display:swap}
@font-face{font-family:Onest-SemiBold;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:600;font-style:normal;font-display:swap}
@font-face{font-family:Onest-Bold;src:url(https://assets.driffle.com/fonts/Onest/Onest-VariableFont_wght.woff2) format("woff2");font-weight:700;font-style:normal;font-display:swap}

*{box-sizing:border-box}
html,body{margin:0;padding:0;background:${T.bg2};color:${T.t1};font-family:Onest-Medium,system-ui,sans-serif;min-height:100%}
a{color:inherit;text-decoration:none}
button{font:inherit;border:0;cursor:pointer;background:none;color:inherit}
img{display:block;max-width:100%}

/* header shell — matches checkout success header */
.hdr{
  height:72px;display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;background:${T.bg2};position:relative;z-index:2;
}
.logo{
  display:inline-flex;align-items:center;height:28px;
}
.logo svg{height:28px;width:118px}
.locale{
  display:inline-flex;align-items:center;gap:8px;
  font:14px/18px Onest-Medium;color:${T.t2};
}
.flag{
  width:18px;height:18px;border-radius:50%;overflow:hidden;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);
  background:linear-gradient(90deg,#009246 0 33.33%,#fff 33.33% 66.66%,#ce2b37 66.66% 100%);
}

/* stepper — sc-434031b0 / sc-a0614dd5 (currentStep=3) */
.steps-wrap{
  width:700px;display:flex;position:absolute;left:50%;transform:translateX(-50%);
}
.steps{
  width:100%;border-radius:6px;display:flex;align-items:center;justify-content:space-between;
}
.step{
  display:flex;align-items:center;justify-content:center;
}
.step-num{
  background-color:#fff;border-radius:8px;color:#000;border:none;
  height:40px;width:40px;display:flex;align-items:center;justify-content:center;
  font-size:16px;position:relative;font-family:Onest-Bold;
}
.step-num.is-active{
  background-color:transparent;color:${T.stepIdle};border:2px solid ${T.stepIdle};
}
.step-num img,.step-num svg{width:20px;height:20px;display:block}
.step-label{
  font-size:16px;font-family:Onest-SemiBold;line-height:19px;
  font-feature-settings:'pnum' on,'lnum' on;
  color:#fff;margin-left:12px;
}
.step-label.is-active{color:#fff}
.step-line{
  flex-grow:1;margin:12px;border-bottom:2px solid #fff;
}

.page{
  max-width:1120px;margin:0 auto;padding:8px 24px 48px;
}

/* email banner */
.mail{
  display:flex;align-items:flex-start;gap:16px;
  background:${T.bg1};border:1px solid ${T.divider};border-radius:${T.radius3};
  padding:16px;margin:8px 0 24px;box-shadow:0px 4px 32px rgba(0,0,0,.04);
}
.mail-ico{
  width:24px;height:24px;flex:0 0 auto;margin-top:2px;
  display:grid;place-items:center;
}
.mail-ico img{
  width:24px;height:24px;
  filter:invert(48%) sepia(98%) saturate(1800%) hue-rotate(201deg) brightness(101%) contrast(101%);
}
.mail h2{margin:0 0 4px;font:16px/20px Onest-Bold;color:${T.t1}}
.mail p{margin:0;font:14px/18px Onest-Medium;color:${T.t2}}
.mail b{font-family:Onest-SemiBold;color:${T.t1};font-weight:600}

/* reveal modal — desktop key view */
.modal{
  position:relative;
  background:${T.bg1};
  border:1px solid ${T.divider};
  border-radius:${T.radius3};
  box-shadow:0px 0px 48px rgba(0,0,0,.16);
  overflow:hidden;
}
.close{
  position:absolute;top:12px;right:12px;z-index:2;
  width:32px;height:32px;border-radius:8px;
  display:grid;place-items:center;
}
.close:hover{background:${T.bg3}}
.close img{width:20px;height:20px;filter:invert(1)}

.modal-title{
  margin:0;padding:20px 24px 12px;
  font:20px/24px Onest-Bold;color:${T.t1};
}
.sep{height:1px;background:${T.divider};margin:0 24px;width:calc(100% - 48px)}

.product{
  display:grid;grid-template-columns:120px 1fr;gap:16px;
  padding:20px 24px 8px;
}
.cover{
  width:120px;height:168px;border-radius:${T.radius2};object-fit:cover;
  background:${T.bg3};
}
.ptitle{
  margin:0 0 10px;font:18px/24px Onest-Bold;color:${T.t1};max-width:640px;
}
.ptitle .ext{
  display:inline-flex;vertical-align:middle;margin-left:6px;opacity:.85;
}
.ptitle .ext img{width:14px;height:14px;filter:invert(.7)}
.badge{
  display:inline-block;background:${tag.bg};color:${tag.text};
  font:11px/14px Onest-Bold;letter-spacing:.02em;text-transform:uppercase;
  padding:4px 8px;border-radius:6px;margin-bottom:14px;
}
.meta{
  display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:520px;
}
.meta-box{
  background:${T.bg2};border:1px solid ${T.divider};border-radius:10px;padding:12px 14px;
}
.meta-label{font:12px/14px Onest-Medium;color:${T.t3};margin-bottom:6px}
.meta-val{display:flex;align-items:center;gap:8px;font:14px/18px Onest-SemiBold;color:${T.t1}}
.meta-val img{width:18px;height:18px;border-radius:4px;object-fit:cover}
.meta-val .globe{width:16px;height:16px;filter:invert(.75)}

.detail{padding:8px 24px 22px}
.detail h3{margin:12px 0;font:15px/18px Onest-Bold;color:${T.t1}}

/* key field — sc-b58f98ad-24 / sc-2be922b6-32 */
.keybox{
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  background:${T.bg3};border:1px solid ${T.border2};border-radius:${T.radius2};
  padding:12px 16px;min-height:52px;margin-bottom:14px;
}
.keytext{
  flex:1;font:16px/24px Onest-SemiBold;color:${T.t1};
  overflow-wrap:anywhere;user-select:all;
}
.copy-ico{
  width:32px;height:32px;border-radius:8px;display:grid;place-items:center;flex:0 0 auto;
}
.copy-ico:hover{background:${T.bg4}}
.copy-ico img{width:24px;height:24px;filter:invert(1)}

.actions{
  display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;
}
.btns{display:flex;gap:12px;flex-wrap:wrap}
.btn{
  height:48px;width:176px;border-radius:${T.radius2};
  display:inline-flex;align-items:center;justify-content:center;
  font:16px/24px Onest-Bold;transition:.2s all ease-in-out;text-transform:none;
}
.btn:active{transform:scale(.95)}
.btn-primary{background:${T.primary};color:#fff}
.btn-primary:hover{background:${T.primaryHover}}
.btn-grey{background:${T.greyBtn};color:${T.t1}}
.btn-grey:hover{background:${T.greyBtnHover}}
.revealed{
  font:14px/14px Onest-Medium;color:${T.t2};padding-bottom:4px;
}
.revealed span{color:${T.t1};font-family:Onest-SemiBold}

.help{
  margin:16px 0 0;font:12px/16px Onest-Medium;color:${T.t2};
}
.help a{text-decoration:underline;cursor:pointer;color:${T.t1}}
.help .note{font-family:Onest-Medium;color:${T.t3}}

.toast{
  position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(12px);
  background:${T.bg3};border:1px solid ${T.border2};color:${T.t1};
  padding:10px 14px;border-radius:10px;font:13px/1 Onest-SemiBold;
  opacity:0;pointer-events:none;transition:.18s ease;z-index:99;
}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

@media (max-width:1023px){
  .steps-wrap{display:none}
  .product{grid-template-columns:95px 1fr}
  .cover{width:95px;height:133px}
  .btn{width:100%}
  .btns{width:100%}
  .actions{align-items:stretch}
}
@media (max-width:1609px){
  .steps-wrap{width:500px}
}
</style>
</head>
<body>
  <header class="hdr">
    <a class="logo" href="${origin}/" aria-label="Driffle logo">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 123 32" width="123" height="32" aria-label="Driffle logo">
        <path d="M22.0464 10.5545L11.8925 7.22134L11.8002 11.1101L18.7233 11.6656L22.0464 10.5545Z" fill="#839EFF"></path>
        <path d="M21.677 20.7404L3.21536 30.9252L11.5231 31.2955L23.7078 22.5922L21.677 20.7404Z" fill="#839EFF"></path>
        <path d="M25 9.07432L6.72298 0.741333L8.19991 24.6292L11.6153 23.1478L11.8922 7.22255L22.0461 10.5557L21.6769 20.7405L23.7077 22.5923L25 9.07432Z" fill="#416AFF"></path>
        <path d="M6.72311 0.741333L1 3.33382L3.2154 30.9253L21.677 20.7405L22.0463 10.5557L18.7232 11.6668V19.9998L8.20004 24.6292L6.72311 0.741333Z" fill="#263BFC"></path>
        <path d="M48.2291 26.3227V8.57852H44.2518V14.8795L44.9975 17.0523H44.0032C43.3569 15.4348 42.1637 13.8897 39.0564 13.8897C35.4272 13.8897 33.6125 16.7626 33.6125 20.2148C33.6125 23.6671 35.4272 26.5641 39.0564 26.5641C42.1637 26.5641 43.3569 25.019 44.0032 23.4015H44.9975L44.2518 25.5743V26.3227H48.2291ZM44.2518 20.2148C44.2518 22.2669 43.0586 23.1843 40.9208 23.1843C38.783 23.1843 37.5898 22.2669 37.5898 20.2148C37.5898 18.1628 38.783 17.2695 40.9208 17.2695C43.0586 17.2695 44.2518 18.1628 44.2518 20.2148Z" fill="white"></path>
        <path d="M50.4713 26.3227H54.4486V17.3661L60.8371 17.511V14.1311L52.6091 13.938C51.2419 13.9138 50.4713 14.6381 50.4713 15.9659V26.3227Z" fill="white"></path>
        <path d="M67.2332 12.924C68.6999 12.924 69.6196 12.2481 69.6196 10.9927C69.6196 9.76146 68.6999 9.06135 67.2332 9.06135C65.7666 9.06135 64.8966 9.76146 64.8966 10.9927C64.8966 12.2481 65.7666 12.924 67.2332 12.924ZM62.0876 26.3227H73.0252V22.9429H69.4705V15.9176C69.4705 14.5657 68.6998 13.8173 67.3078 13.8897L62.5848 14.1311V17.511L65.6423 17.3661V22.9429H62.0876V26.3227Z" fill="white"></path>
        <path d="M82.3221 11.9584H84.957V8.57852H82.8192C78.6182 8.57852 76.6544 10.4133 76.6544 13.6966V14.1311H74.2681V17.511H76.6544V22.9429H74.2681V26.3227H84.261V22.9429H80.6317V17.511H84.261V14.1311H80.6317V13.8173C80.6317 12.4653 81.1537 11.9584 82.3221 11.9584Z" fill="white"></path>
        <path d="M93.9986 11.9584H96.6335V8.57852H94.4957C90.2947 8.57852 88.3309 10.4133 88.3309 13.6966V14.1311H85.9445V17.511H88.3309V22.9429H85.9445V26.3227H95.9375V22.9429H92.3082V17.511H95.9375V14.1311H92.3082V13.8173C92.3082 12.4653 92.8302 11.9584 93.9986 11.9584Z" fill="white"></path>
        <path d="M97.621 26.3227H108.559V22.9429H105.078V10.4374C105.078 9.08549 104.308 8.36124 102.916 8.40952L98.1182 8.57852V11.9584L101.101 11.8135V22.9429H97.621V26.3227Z" fill="white"></path>
        <path d="M109.303 20.07C109.303 23.5223 111.516 26.5641 116.338 26.5641C120.688 26.5641 122.752 23.7878 123 22.0255H119.023C118.774 22.9429 117.73 23.4257 116.338 23.4257C114.076 23.4257 113.032 22.4359 113.032 21.0357H122.553V19.8286C122.553 16.1349 119.818 13.8897 115.916 13.8897C112.013 13.8897 109.303 16.2073 109.303 20.07ZM113.032 18.8629C113.032 17.9455 113.703 17.0281 115.916 17.0281C118.128 17.0281 118.824 17.9455 118.824 18.8629H113.032Z" fill="white"></path>
      </svg>
    </a>

    <div class="steps-wrap" aria-label="Checkout steps">
      <div class="steps">
        <div class="step">
          <div class="step-num">
            <img src="${origin}/icons/check_circle_outline.svg" alt=""/>
          </div>
          <div class="step-label">Cart</div>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-num">
            <img src="${origin}/icons/check_circle_outline.svg" alt=""/>
          </div>
          <div class="step-label">Checkout</div>
        </div>
        <div class="step-line"></div>
        <div class="step">
          <div class="step-num is-active"><div>3</div></div>
          <div class="step-label is-active">Reveal</div>
        </div>
      </div>
    </div>

    <div class="locale"><span class="flag" aria-hidden="true"></span>${esc(CFG.localeLabel)}</div>
  </header>

  <main class="page">
    <section class="mail">
      <div class="mail-ico">
        <img src="${origin}/icons/mark-email-read.svg" alt=""/>
      </div>
      <div>
        <h2>Order delivered to your email</h2>
        <p>You can activate products at any time from the email we have sent you at <b>${esc(CFG.email)}</b></p>
      </div>
    </section>

    <section class="modal" role="dialog" aria-label="Reveal Product">
      <button class="close" id="closeBtn" aria-label="Close">
        <img src="${origin}/icons/close-24.svg" alt=""/>
      </button>
      <h1 class="modal-title">Reveal Product</h1>
      <div class="sep"></div>

      <div class="product">
        <img class="cover" src="${esc(CFG.productImg)}" alt="product"/>
        <div>
          <h2 class="ptitle">
            ${esc(CFG.title)}
            <a class="ext" href="${esc(CFG.productUrl)}" target="_blank" rel="noreferrer" title="Open product">
              <img src="${origin}/icons/open_in_new.svg" alt=""/>
            </a>
          </h2>
          <div class="badge">${esc(tag.label)}</div>
          <div class="meta">
            <div class="meta-box">
              <div class="meta-label">Platform</div>
              <div class="meta-val">
                <img src="${esc(CFG.productImg)}" alt=""/>
                ${esc(CFG.platform)}
              </div>
            </div>
            <div class="meta-box">
              <div class="meta-label">Region</div>
              <div class="meta-val">
                <img class="globe" src="${origin}/icons/globe-black.svg" alt=""/>
                ${esc(CFG.region)}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail">
        <h3>Product Detail</h3>
        <div class="keybox">
          <div class="keytext" id="codeText">${esc(CFG.code)}</div>
          <button class="copy-ico" id="copyIcon" title="Copy">
            <img src="${origin}/icons/content-copy-24.svg" alt=""/>
          </button>
        </div>
        <div class="actions">
          <div class="btns">
            <button class="btn btn-primary" id="copyBtn">Copy to clipboard</button>
            <button class="btn btn-grey" id="guideBtn">Activation Guide</button>
          </div>
          <div class="revealed">Revealed on <span>${esc(CFG.revealedAt)}</span></div>
        </div>
        <p class="help">
          Facing issues with the product? You can raise a ticket
          <a href="${origin}/support/ticket/product/create" target="_blank" rel="noreferrer">here</a>.
          <span class="note"> (Our support will get in touch with you within 48 hours)</span>
        </p>
      </div>
    </section>
  </main>

  <div class="toast" id="toast">Key Copied to Clipboard</div>
  <script>
  (function(){
    const code = ${JSON.stringify(CFG.code)};
    const toast = document.getElementById('toast');
    function showToast(){
      toast.classList.add('show');
      clearTimeout(showToast._t);
      showToast._t = setTimeout(()=>toast.classList.remove('show'), 1600);
    }
    async function copy(){
      try{
        if (typeof GM_setClipboard === 'function') GM_setClipboard(code);
        else await navigator.clipboard.writeText(code);
      }catch(e){
        const ta=document.createElement('textarea');
        ta.value=code; document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); ta.remove();
      }
      showToast();
    }
    document.getElementById('copyBtn').onclick = copy;
    document.getElementById('copyIcon').onclick = copy;
    document.getElementById('guideBtn').onclick = () => {
      window.open('https://driffle.com/blog/category/activation-guides/', '_blank', 'noopener');
    };
    document.getElementById('closeBtn').onclick = () => { location.href = ${JSON.stringify(origin + "/")}; };
  })();
  </script>
</body>
</html>`;

    document.open();
    document.write(html);
    document.close();
  }

  if (typeof GM_registerMenuCommand === "function") {
    GM_registerMenuCommand("Open Driffle Reveal clone", openReveal);
  }

  if (shouldAuto) openReveal();
  else {
    const btn = document.createElement("button");
    btn.id = "driffle-fake-reveal-fab";
    btn.textContent = "Reveal demo";
    Object.assign(btn.style, {
      position: "fixed",
      right: "14px",
      bottom: "14px",
      zIndex: "2147483647",
      background: T.primary,
      color: "#fff",
      border: "0",
      borderRadius: "8px",
      height: "40px",
      padding: "0 14px",
      font: "14px/1 Onest-Bold, system-ui, sans-serif",
      cursor: "pointer",
      boxShadow: "0 8px 24px rgba(0,0,0,.35)",
    });
    btn.addEventListener("click", openReveal);
    const mount = () => {
      if (!document.body || document.getElementById("driffle-fake-reveal-fab")) return;
      document.body.appendChild(btn);
    };
    if (document.body) mount();
    else document.addEventListener("DOMContentLoaded", mount, { once: true });
  }
})();
