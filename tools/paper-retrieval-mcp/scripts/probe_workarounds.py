"""Bounded public-host diagnostics; no browser session or system DNS changes."""
import asyncio, ipaddress, json, socket
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from bs4 import BeautifulSoup
from paper_retrieval.core import Settings, make_http_client

ROOT=Path(__file__).resolve().parents[1]/'.data/topic-100-2026-11-06/exploration'
HOSTS=['sci-hub.ru','sci-hub.st','sci-hub.se','sci-hub.su','sci-hub.box','sci-hub.al','sci-hub.mk','sci-hub.vg','sci-net.xyz']

async def main():
 ROOT.mkdir(exist_ok=True)
 records=[]
 async with httpx.AsyncClient(timeout=12,follow_redirects=False) as dns:
  for host in HOSTS:
   a={'host':host}
   try:a['local_ips']=sorted({r[4][0] for r in socket.getaddrinfo(host,443)})
   except Exception as e:a['local_dns_error']=type(e).__name__
   try:
    response=await dns.get('https://dns.google/resolve',params={'name':host,'type':'A'})
    a['public_dns']=response.json()
    ips=[r['data'] for r in a['public_dns'].get('Answer',[]) if r['type']==1 and ipaddress.ip_address(r['data']).is_global]
   except Exception as e:a['public_dns_error']=str(e);ips=[]
   routes=[('local',{})]
   if ips and ips[0] not in a.get('local_ips',[]):routes.append(('public_dns',{host:ips[0]}))
   if host=='sci-hub.ru':routes.append(('known_working',{host:'190.115.31.218'}))
   a['probes']=[]
   for route,overrides in routes:
    p={'route':route,'overrides':overrides}
    try:
     settings=Settings(provider_urls=('https://'+host,),host_overrides=overrides,request_timeout=7)
     async with make_http_client(settings) as client:
      response=await client.get('https://'+host+'/10.1145/2635868.2635920')
      body=response.content[:200000];soup=BeautifulSoup(body,'html.parser')
      p.update(status=response.status_code,url=str(response.url),location=response.headers.get('location'),server=response.headers.get('server'),content_type=response.headers.get('content-type'),title=soup.title.get_text() if soup.title else None,text=soup.get_text(' ',strip=True)[:1000])
      (ROOT/(host+'-'+route+'.html')).write_bytes(body)
    except Exception as e:p['error']=type(e).__name__+': '+str(e)
    a['probes'].append(p)
   records.append(a);(ROOT/'network-probes.json').write_text(json.dumps(records,indent=2))
   print(json.dumps(a),flush=True)

asyncio.run(main())
