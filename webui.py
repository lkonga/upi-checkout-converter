from __future__ import annotations

from app import app
from fastapi.responses import HTMLResponse


@app.get('/', response_class=HTMLResponse)
async def index():
    return '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Checkout Converter</title>
  <style>
    :root{color-scheme:dark;--bg:#0b1020;--card:#11182c;--muted:#8ea0c0;--text:#eef3ff;--line:#26324e;--accent:#67e8f9;--bad:#fb7185;--ok:#34d399}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at top,#172342,#0b1020 55%);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--text)}
    .wrap{max-width:980px;margin:0 auto;padding:36px 18px}.card{background:rgba(17,24,44,.92);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 22px 60px rgba(0,0,0,.35)}
    h1{font-size:26px;margin:0 0 8px}.sub{color:var(--muted);margin:0 0 22px;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.full{grid-column:1/-1}
    label{display:block;font-size:13px;color:#c7d2fe;margin:0 0 7px} input,select,textarea{width:100%;border:1px solid var(--line);border-radius:12px;background:#0b1224;color:var(--text);padding:12px;font-size:14px;outline:none} textarea{min-height:170px;resize:vertical;font-family:ui-monospace,SFMono-Regular,Menlo,monospace} input:focus,select:focus,textarea:focus{border-color:var(--accent)}
    button{border:0;border-radius:12px;background:linear-gradient(135deg,#22d3ee,#60a5fa);color:#06111f;font-weight:800;padding:13px 18px;cursor:pointer} button:disabled{opacity:.55;cursor:not-allowed}.actions{display:flex;gap:10px;align-items:center;margin-top:16px}.status{font-size:13px;color:var(--muted)}
    .result{margin-top:18px;display:none}.result.show{display:block}.row{display:grid;grid-template-columns:180px 1fr auto;gap:10px;align-items:center;border-top:1px solid var(--line);padding:12px 0}.row:first-child{border-top:0}.k{color:var(--muted);font-size:13px}.v{word-break:break-all;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px} .copy{padding:8px 10px;background:#1f2a44;color:#dbeafe}.primary{color:var(--ok)}
    pre{white-space:pre-wrap;word-break:break-word;background:#081022;border:1px solid var(--line);border-radius:12px;padding:14px;color:#dbeafe}.err{color:var(--bad)}
    @media(max-width:760px){.grid{grid-template-columns:1fr}.row{grid-template-columns:1fr}.copy{width:max-content}}
  </style>
</head>
<body>
  <div class="wrap"><div class="card">
    <h1>ChatGPT Plus Checkout Converter</h1>
    <p class="sub">输入 ChatGPT accessToken，生成 Plus 支付链接。默认 PayPal / US / USD / openai_llc。</p>
    <form id="form" class="grid">
      <div class="full"><label>accessToken</label><textarea id="accessToken" placeholder="粘贴 eyJ... 或包含 accessToken 的 JSON/文本" required></textarea></div>
      <div><label>支付方式</label><select id="paymentMethod"><option value="paypal">paypal</option><option value="gopay">gopay</option></select></div>
      <div><label>processorEntity</label><input id="processorEntity" value="openai_llc" /></div>
      <div><label>国家</label><input id="country" value="US" /></div>
      <div><label>币种</label><input id="currency" value="USD" /></div>
      <div class="full"><label>支付转换代理（用于直连 OpenAI，建议走 JP 出口）</label><input id="proxyUrl" placeholder="socks5h://user:pass@host:port 或 http://host:port" /></div>
      <div class="full actions"><button id="submit" type="submit">生成支付链接</button><span id="status" class="status">待输入 token</span></div>
    </form>
    <div id="result" class="result"></div>
  </div></div>
<script>
const $ = id => document.getElementById(id);
const result = $('result'), statusEl = $('status'), btn = $('submit');
function esc(s){return String(s ?? '').replace(/[&<>"']/g, m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
async function copyText(t){await navigator.clipboard.writeText(t)}
function row(k,v,primary=false){if(!v)return ''; const id='c'+Math.random().toString(36).slice(2); setTimeout(()=>{const b=document.getElementById(id); if(b)b.onclick=()=>copyText(v).then(()=>b.textContent='已复制')},0); return `<div class="row"><div class="k">${esc(k)}</div><div class="v ${primary?'primary':''}">${esc(v)}</div><button class="copy" id="${id}">复制</button></div>`}

// 自动读取和保存本地代理配置，方便重用
const PROXY_KEY = 'checkout_converter_proxy_url';
if (localStorage.getItem(PROXY_KEY)) {
  $('proxyUrl').value = localStorage.getItem(PROXY_KEY);
}
$('proxyUrl').addEventListener('input', () => {
  localStorage.setItem(PROXY_KEY, $('proxyUrl').value);
});

$('form').addEventListener('submit', async e=>{
  e.preventDefault(); result.className='result'; result.innerHTML=''; btn.disabled=true; statusEl.textContent='转换中...';
  const body={accessToken:$('accessToken').value,paymentMethod:$('paymentMethod').value,country:$('country').value,currency:$('currency').value,processorEntity:$('processorEntity').value,proxyUrl:$('proxyUrl').value};
  try{
    const r=await fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await r.json();
    result.className='result show';
    if(!r.ok || !data.ok){result.innerHTML=`<pre class="err">${esc(JSON.stringify(data,null,2))}</pre>`; statusEl.textContent='失败'; return}
    result.innerHTML = row('首选链接 preferred', data.preferredCheckoutUrl, true)+row('Hosted 链接', data.hostedCheckoutUrl)+row('ChatGPT 链接', data.chatgptCheckoutUrl)+row('原始 checkout', data.checkoutUrl)+row('Session ID', data.checkoutSessionId)+`<pre>${esc(JSON.stringify(data,null,2))}</pre>`;
    statusEl.textContent='完成';
  }catch(err){result.className='result show'; result.innerHTML=`<pre class="err">${esc(err.message||err)}</pre>`; statusEl.textContent='失败'}
  finally{btn.disabled=false}
});
$('paymentMethod').addEventListener('change',()=>{if($('paymentMethod').value==='gopay'){country.value='ID';currency.value='IDR';processorEntity.value='openai_llc'}else{country.value='US';currency.value='USD';processorEntity.value='openai_llc'}})
</script>
</body></html>'''
