import json,os,sys
root=sys.argv[1]; out=sys.argv[2]; frm=sys.argv[3] if len(sys.argv)>3 else 'User'
def load(kind,name):
    p=os.path.join(root,kind,name+'.json')
    d=json.load(open(p,encoding='utf-8-sig'))
    if d.get('inherits'):
        base=load(kind,d['inherits']); base.update(d); d=base
    return d
for kind,name,fn in [('machine','Snapmaker U1 (0.4 nozzle)','machine.json'),('process','0.20mm Standard @Snapmaker U1 (0.4 nozzle)','process.json'),('filament','Snapmaker PLA','fil1.json'),('filament','Snapmaker PLA','fil2.json')]:
    d=load(kind,name); d['inherits']=''
    for k in ('renamed_from','description','setting_id','instantiation','compatible_printers_condition','compatible_prints_condition'): d.pop(k,None)
    d['from']=frm; d['type']=kind
    if kind=='process': d['print_settings_id']=name; d['version']='2.4.1.0'; d.pop('wipe_tower_filament',None)
    if kind=='filament': d['filament_settings_id']=[name]; d['version']='2.4.1.0'
    if kind=='machine': d['printer_settings_id']=name; d['version']='2.4.1.0'
    json.dump(d,open(os.path.join(out,fn),'w'),indent=1)
