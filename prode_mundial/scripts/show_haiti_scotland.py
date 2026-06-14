import json
pj = json.load(open('prode_mundial/output/players.json','r',encoding='utf-8'))
ha = pj.get('Haiti',[])
print('=== HAITI ===')
for h in ha:
    print(f"{h['name']:35s} pos={h.get('position','?'):30s} height={str(h.get('height','?')):6s}")
print()
sc = pj.get('Scotland',[])
print('=== SCOTLAND ===')
for s in sc:
    print(f"{s['name']:35s} pos={s.get('position','?'):30s} height={str(s.get('height','?')):6s}")
