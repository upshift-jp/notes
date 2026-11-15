#!/usr/bin/env python3
"""UPSHIFT議事録（版2）: 普通のページの枠を表示し、本文だけを暗号化して枠の中に表示する。
画面の丸ごと差し替え（document.write）はしない。
使い方: make_note2.py <note.html> <note.pdf> <出力フォルダ> <コピー見出し> <PDF名> <保存キー> [鍵]"""
import sys, os, re, json, base64, secrets, string
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 200000
SITE = "https://upshift-jp.github.io/notes/"

def enc(data: bytes, k: str) -> str:
    salt = secrets.token_bytes(16); iv = secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(k.encode())
    ct = AESGCM(key).encrypt(iv, data, None)
    b = lambda x: base64.b64encode(x).decode()
    return json.dumps({"v": 2, "it": ITER, "s": b(salt), "i": b(iv), "c": b(ct)})

PAGE = r'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="referrer" content="no-referrer">
<title>UPSHIFT｜会議のまとめ</title>
<meta name="description" content="アップシフト合同会社の会議のまとめページです。">
<meta property="og:type" content="website">
<meta property="og:site_name" content="アップシフト合同会社">
<meta property="og:title" content="UPSHIFT｜会議のまとめ">
<meta property="og:description" content="リンクを受け取った方専用のページです。">
<meta property="og:image" content="__SITE__og.png">
<meta name="twitter:card" content="summary_large_image">
<style>
__CSS__
.gate{padding:80px 0;text-align:center;color:var(--mute)}
.gate b{display:block;font-family:var(--latin);letter-spacing:.3em;color:var(--acc-d);margin-bottom:10px}
</style>
</head>
<body data-theme="a">
__BAR__
<main class="wrap" id="app"><div class="gate"><b>UPSHIFT</b><span id="gm">会議のまとめを表示しています…</span></div></main>
<div class="wrap"><footer>
<div class="co"><b>UPSHIFT</b><span>アップシフト合同会社</span><span><a href="https://upshift.jp/">https://upshift.jp/</a></span></div>
東京都八王子市を拠点に、補助金・助成金を活用した中小企業の事業支援を行っています。このページは、会議の参加者向けにお送りしたまとめです。
</footer></div>
<script>
(function(){
var gm=document.getElementById('gm');
function msg(t){gm.textContent=t;}
var k=new URLSearchParams(location.hash.slice(1)).get('k');
if(!k||!window.crypto||!crypto.subtle){msg('このページは、お送りしたリンクから開いてください。');return;}
function b64(s){var r=atob(s),a=new Uint8Array(r.length);for(var i=0;i<r.length;i++)a[i]=r.charCodeAt(i);return a;}
async function open(url){
 var j=await (await fetch(url,{cache:'no-store'})).json();
 var base=await crypto.subtle.importKey('raw',new TextEncoder().encode(k),'PBKDF2',false,['deriveKey']);
 var key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(j.s),iterations:j.it,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
 return crypto.subtle.decrypt({name:'AES-GCM',iv:b64(j.i)},key,b64(j.c));
}
open('note.json').then(function(buf){
 var d=JSON.parse(new TextDecoder().decode(buf));
 document.getElementById('app').innerHTML=d.html;
 document.title=d.title;
 init(d);
}).catch(function(){msg('このリンクでは開けません。お手数ですが送り主にお問い合わせください。');});

function init(d){
 var st={};try{st=JSON.parse(localStorage.getItem(d.store)||'{}')}catch(e){}
 function save(){try{localStorage.setItem(d.store,JSON.stringify(st))}catch(e){}}
 var items=[].slice.call(document.querySelectorAll('#tasks li'));
 items.forEach(function(li,i){var cb=li.querySelector('input');if(!cb)return;if(st[i]){cb.checked=true;li.classList.add('done')}
  cb.addEventListener('change',function(){li.classList.toggle('done',cb.checked);st[i]=cb.checked;save()})});
 document.querySelectorAll('.tools [data-f]').forEach(function(b){b.addEventListener('click',function(){
  document.querySelectorAll('.tools [data-f]').forEach(function(x){x.classList.remove('on')});b.classList.add('on');
  var f=b.dataset.f;items.forEach(function(li){li.hidden=!(f==='all'||li.dataset.w===f)})})});
 var cp=document.getElementById('copy');
 if(cp)cp.addEventListener('click',function(){
  var t='【宿題】'+d.copy+'\n'+items.filter(function(li){return !li.hidden}).map(function(li){
   var m=[].map.call(li.querySelectorAll('.m span'),function(s){return s.textContent}).join('・');
   return (li.classList.contains('done')?'☑ ':'□ ')+li.querySelector('.tx').textContent+'（'+m+'）'}).join('\n');
  var toast=document.getElementById('toast');
  try{navigator.clipboard.writeText(t).then(function(){toast.textContent='コピーしました'},function(){toast.textContent='コピーできませんでした'})}catch(e){toast.textContent='コピーできませんでした'}
  setTimeout(function(){toast.textContent=''},2500)});
 document.querySelectorAll('.ch summary a.t').forEach(function(a){a.addEventListener('click',function(e){e.stopPropagation()})});
 var pb=document.getElementById('pdfbtn');
 if(pb){pb.hidden=false;pb.addEventListener('click',async function(){pb.textContent='準備中…';try{var buf=await open('note.pdf.json');
  var url=URL.createObjectURL(new Blob([buf],{type:'application/pdf'}));var a=document.createElement('a');a.href=url;a.download=d.pdf;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url)},60000);pb.textContent='PDFで保存';}catch(e){pb.textContent='保存できませんでした';}});}
 if(location.hash.indexOf('&')<0){}
}
})();
</script>
</body></html>
'''

def main():
    src, pdf, out, copy, pdfname, store = sys.argv[1:7]
    k = sys.argv[7] if len(sys.argv) > 7 else ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
    s = open(src, encoding='utf-8').read()
    css = re.search(r'<style>\n?(.*?)</style>', s, re.S).group(1)
    bar = re.search(r'<nav class="bar">.*?</nav>', s, re.S).group(0)
    main_inner = re.search(r'<main class="wrap">(.*?)</main>', s, re.S).group(1)
    main_inner = re.sub(r'<footer>.*?</footer>', '', main_inner, flags=re.S)
    title = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
    payload = json.dumps({"title": title, "html": main_inner, "copy": copy, "pdf": pdfname, "store": store}, ensure_ascii=False).encode()
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'note.json'), 'w').write(enc(payload, k))
    open(os.path.join(out, 'note.pdf.json'), 'w').write(enc(open(pdf, 'rb').read(), k))
    page = PAGE.replace('__SITE__', SITE).replace('__CSS__', css).replace('__BAR__', bar)
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)
    print(k)

if __name__ == '__main__':
    main()
