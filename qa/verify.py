from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
import json, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8080"
ROOT = Path(__file__).resolve().parents[1]

class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]; self.anchors=[]; self.images=[]; self.forms=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'a' and a.get('href','').startswith('#'): self.anchors.append(a['href'][1:])
        if tag == 'img': self.images.append(a)
        if tag == 'form': self.forms += 1

html=(ROOT/'index.html').read_text(encoding='utf-8')
p=AuditParser(); p.feed(html)
status=urllib.request.urlopen(BASE, timeout=5).status
results={
  'http_status': status,
  'html_parse': 'ok',
  'duplicate_ids': sorted({x for x in p.ids if p.ids.count(x)>1}),
  'missing_anchors': sorted(set(p.anchors)-set(p.ids)),
  'internal_anchors_checked': len(p.anchors),
  'forms': p.forms,
  'whatsapp_number_consistent': ('573334328971' in html and '573334328971' in (ROOT/'script.js').read_text()),
}

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for label, viewport in [('desktop', {'width':1440,'height':1000}), ('mobile', {'width':390,'height':844})]:
        page=browser.new_page(viewport=viewport)
        console_errors=[]; page_errors=[]
        page.on('console', lambda msg, bag=console_errors: bag.append(msg.text) if msg.type=='error' else None)
        page.on('pageerror', lambda err, bag=page_errors: bag.append(str(err)))
        page.goto(BASE, wait_until='networkidle')
        overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        page.screenshot(path=str(ROOT/'qa'/f'{label}-v2.png'), full_page=True)
        assurance=page.locator('.assurance')
        assurance_box=assurance.bounding_box()
        results[label]={
            'horizontal_overflow':overflow,
            'console_errors':console_errors,
            'page_errors':page_errors,
            'assurance_visible':assurance.is_visible(),
            'trust_item_count':page.locator('.trust-list li').count(),
            'assurance_within_page':bool(assurance_box and assurance_box['x'] >= 0 and assurance_box['x'] + assurance_box['width'] <= viewport['width'] + 1),
            'portfolio_cta_target':page.get_attribute('.portfolio-action .button-primary','href')=='#contacto',
        }
        if label=='mobile':
            page.click('.menu-button')
            results[label]['menu_open']=page.get_attribute('.menu-button','aria-expanded')=='true' and page.locator('#nav').evaluate("e=>getComputedStyle(e).display")!='none'
            page.click('#nav a[href="#planes"]')
            results[label]['menu_closes']=page.get_attribute('.menu-button','aria-expanded')=='false'
        else:
            page.click('[data-plan="Nexu Profesional"]')
            results[label]['plan_selected']=page.input_value('[name="plan"]')=='Nexu Profesional'
            results[label]['need_selected']='catálogo' in page.input_value('[name="need"]')
            page.fill('[name="name"]','Prueba QA')
            page.fill('[name="business"]','Negocio de prueba')
            page.evaluate("window.__opened=''; window.open=(url)=>{window.__opened=url; return null}")
            page.click('#quote-form button[type="submit"]')
            opened=page.evaluate('window.__opened')
            results[label]['whatsapp_submit']=opened.startswith('https://wa.me/573334328971?text=')
            results[label]['plan_in_message']='Nexu%20Profesional' in opened or 'Nexu+Profesional' in opened or 'Nexu%20Profesional' in opened
            results[label]['faq_count']=page.locator('.faq details').count()
            page.locator('.faq details').first.click()
            results[label]['faq_opens']=page.locator('.faq details').first.get_attribute('open') is not None
    browser.close()

ok = (
 status==200 and not results['duplicate_ids'] and not results['missing_anchors']
 and results['whatsapp_number_consistent']
 and all(not results[k]['horizontal_overflow'] and not results[k]['console_errors'] and not results[k]['page_errors'] for k in ('desktop','mobile'))
 and all(results[k]['assurance_visible'] and results[k]['trust_item_count']==5 and results[k]['assurance_within_page'] and results[k]['portfolio_cta_target'] for k in ('desktop','mobile'))
 and results['mobile']['menu_open'] and results['mobile']['menu_closes']
 and results['desktop']['plan_selected'] and results['desktop']['need_selected']
 and results['desktop']['whatsapp_submit'] and results['desktop']['plan_in_message']
 and results['desktop']['faq_count']==4 and results['desktop']['faq_opens']
)
results['verified']=ok
print(json.dumps(results, ensure_ascii=False, indent=2))
raise SystemExit(0 if ok else 1)
