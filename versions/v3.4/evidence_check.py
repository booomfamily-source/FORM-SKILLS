#!/usr/bin/env python3
"""FORM SKILLS v3.4 — structural/project readiness audit; not CAD certification."""
import json
import math
import sys
from pathlib import Path

VIEWS = ('profile','front','rear','three_quarter','detail')
TYPES = ('physical','visual')
REQUIRED = ('version','subject','units','dimensions','axes','constraints','events','claims','views','continuity','assembly','artifacts')

def audit(d):
    report=[]
    def put(code, ok, detail, gate='schema'):
        report.append({'check':code,'status':'PASS' if ok else 'FAIL','gate':gate,'detail':detail})
    if not isinstance(d, dict):
        return [{'check':'document','status':'FAIL','gate':'schema','detail':'JSON object required'}]
    put('required_fields', all(k in d for k in REQUIRED), 'Required keys: '+', '.join(REQUIRED))
    put('units', d.get('units')=='mm', 'Unit must be explicitly mm')
    dims=d.get('dimensions') or {}
    values=[dims.get(k) for k in ('length_mm','width_mm','height_mm')]
    numbers=all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>0 for v in values)
    put('dimensions',numbers,'Named, positive, finite L/W/H')
    axes=d.get('axes') or {}
    put('axes',axes=={'x':'length rear to front','y':'width left to right','z':'height above ground'},'Vehicle coordinate frame fixed; alternative subjects need a different schema')
    constraints=d.get('constraints') or []
    put('constraints',bool(constraints) and all(isinstance(x,dict) and x.get('id') and x.get('source') in ('user','derived','assumption') for x in constraints),'Nonempty traceable constraints')
    events=d.get('events') or []
    ids=[e.get('id') for e in events if isinstance(e,dict)]
    put('events',len(events)>0 and len(ids)==len(events) and len(ids)==len(set(ids)) and all(isinstance(x,str) and x for x in ids) and all(e.get('type') in TYPES and isinstance(e.get('before'),bool) and isinstance(e.get('after'),bool) and bool(e.get('view')) and bool(e.get('geometry_ref')) for e in events if isinstance(e,dict)),'Unique typed, view-linked geometry event ledger')
    claims=d.get('claims') or {}
    for kind in TYPES:
        subset=[e for e in events if isinstance(e,dict) and e.get('type')==kind]
        before=sum(e.get('before') is True for e in subset)
        after=sum(e.get('after') is True for e in subset)
        claim=claims.get(kind)
        if not subset:
            put('ledger_'+kind,False,'At least one '+kind+' event required')
        elif claim is None:
            put('ledger_'+kind,False,'Explicit counts required even if reduction is zero')
        else:
            expected=round(100*(before-after)/before,1) if before else None
            ok=isinstance(claim,dict) and claim.get('before')==before and claim.get('after')==after and isinstance(claim.get('percent'),(int,float)) and not isinstance(claim.get('percent'),bool) and expected is not None and abs(claim['percent']-expected)<0.051
            put('ledger_'+kind,ok,f'Counted {before} -> {after}; expected {expected}%')
    views=d.get('views') or {}
    put('view_structure',all(views.get(v) in ('PASS','FAIL','UNKNOWN') for v in VIEWS),'All five viewpoints need explicit statuses')
    artifacts=d.get('artifacts') or {}
    for key in VIEWS:
        if views.get(key)=='PASS':
            a=artifacts.get(key)
            put('view_evidence_'+key,isinstance(a,dict) and bool(a.get('geometry_sha256')) and bool(a.get('file')) and a.get('reviewed') is True,'PASS requires reviewed geometry artifact', 'evidence')
        else:
            put('view_evidence_'+key,False,'View not demonstrated: '+str(views.get(key)),'readiness')
    c=d.get('continuity') or {}
    if c.get('status')=='PASS':
        values2=c.get('metrics') or {}
        ok=all(isinstance(values2.get(k),(int,float)) and math.isfinite(values2[k]) and values2[k]>=0 for k in ('max_position_mm','max_tangent_deg','max_curvature_diff_mm_inv')) and isinstance(c.get('tolerances'),dict) and all(isinstance(c['tolerances'].get(k),(int,float)) and c['tolerances'][k]>=values2[k] for k in values2 if k in ('max_position_mm','max_tangent_deg','max_curvature_diff_mm_inv')) and bool(c.get('source_geometry_sha256'))
        put('continuity',ok,'G2 PASS requires numeric G0/G1/G2 residuals, tolerances, geometry hash', 'evidence')
    else:
        put('continuity',False,'Continuity unverified or failed', 'readiness')
    assembly=d.get('assembly') or {}
    g=assembly.get('nominal_gap_mm'); t=assembly.get('tolerance_mm'); step=assembly.get('step_mm')
    gap_ok=all(isinstance(v,(int,float)) and math.isfinite(v) for v in (g,t,step)) and g>0 and t>=0 and t<g
    put('assembly',gap_ok,'Nominal gap > positive tolerance; numeric step')
    extra=d.get('render_dimensions')
    if extra is not None:
        put('render_dimensions',extra==dims,'Caption dimensions must equal manifest geometry')
    put('validation_claim',d.get('validation') not in ('CAD VERIFIED','PHYSICALLY VALIDATED','MANUFACTURING VERIFIED'),'Unsupported validation language prohibited')
    if numbers:
        report.append({'check':'ratios','status':'INFO','gate':'calculation','detail':{'H/W':round(values[2]/values[1],4),'W/L':round(values[1]/values[0],4)}})
    return report

def summarize(results):
    schema=any(r['status']=='FAIL' and r['gate']=='schema' for r in results)
    ready=not any(r['status']=='FAIL' for r in results)
    return 'SCHEMA_INVALID' if schema else ('PROJECT_READY_FOR_REVIEW' if ready else 'INCOMPLETE_EVIDENCE')

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: evidence_check.py <manifest.json>')
    try:
        doc=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'),parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))
        findings=audit(doc)
        status=summarize(findings)
        print(json.dumps({'status':status,'checks':findings},ensure_ascii=False,indent=2,allow_nan=False))
        sys.exit(0 if status=='PROJECT_READY_FOR_REVIEW' else 1)
    except (ValueError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'SCHEMA_INVALID','error':str(exc)},ensure_ascii=False))
        sys.exit(2)
