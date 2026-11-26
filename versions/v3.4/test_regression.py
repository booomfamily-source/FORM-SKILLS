#!/usr/bin/env python3
"""Regression tests: expected outcomes of v3.4 structural and evidence gates."""
import copy
import json
from evidence_check import audit, summarize

BASE={
'version':'v3.4','subject':'automotive concept','units':'mm',
'dimensions':{'length_mm':4750,'width_mm':2020,'height_mm':1150},
'axes':{'x':'length rear to front','y':'width left to right','z':'height above ground'},
'constraints':[{'id':'L','source':'assumption','value_mm':4750}],
'events':[
{'id':'P01','type':'physical','before':True,'after':True,'view':'profile','geometry_ref':'body-a'},
{'id':'V01','type':'visual','before':True,'after':True,'view':'profile','geometry_ref':'surface-a'},
{'id':'V02','type':'visual','before':True,'after':False,'view':'profile','geometry_ref':'crease-b'}],
'claims':{'physical':{'before':1,'after':1,'percent':0.0},'visual':{'before':2,'after':1,'percent':50.0}},
'views':{'profile':'UNKNOWN','front':'UNKNOWN','rear':'UNKNOWN','three_quarter':'UNKNOWN','detail':'UNKNOWN'},
'artifacts':{},'continuity':{'status':'UNKNOWN'},
'assembly':{'nominal_gap_mm':3.5,'tolerance_mm':0.5,'step_mm':0},
'validation':'not verified'}

CASES=[]
def add(n,fn,expected):
    obj=copy.deepcopy(BASE);fn(obj);CASES.append((n,obj,expected))
add('baseline_incomplete',lambda d:None,'INCOMPLETE_EVIDENCE')
add('duplicate_ids',lambda d:d['events'][1].update(id='P01'),'SCHEMA_INVALID')
add('wrong_reduction',lambda d:d['claims']['visual'].update(percent=31.0),'SCHEMA_INVALID')
add('correct_reduction',lambda d:None,'INCOMPLETE_EVIDENCE')
add('g2_claim_without_evidence',lambda d:d['continuity'].update(status='PASS'),'INCOMPLETE_EVIDENCE')
add('g2_claim_fake_string',lambda d:d['continuity'].update(status='PASS',evidence='trust me'),'INCOMPLETE_EVIDENCE')
add('dimension_conflict_unmodeled',lambda d:d.update(render_dimensions={'length_mm':4620,'width_mm':1980,'height_mm':1180}),'SCHEMA_INVALID')
add('negative_dimension',lambda d:d['dimensions'].update(height_mm=-5),'SCHEMA_INVALID')
add('missing_event_ledger',lambda d:d.update(events=[]),'SCHEMA_INVALID')
add('unknown_views',lambda d:None,'INCOMPLETE_EVIDENCE')
add('missing_units',lambda d:d.pop('units'),'SCHEMA_INVALID')
add('wrong_assembly_gap',lambda d:d['assembly'].update(tolerance_mm=4),'SCHEMA_INVALID')
add('view_marked_pass_without_model',lambda d:d['views'].update(profile='PASS'),'INCOMPLETE_EVIDENCE')
add('nonphysical_axis',lambda d:d['axes'].update(x='front to back'),'SCHEMA_INVALID')
add('wrong_percent_under_rounding',lambda d:d['claims']['visual'].update(percent=50.2),'SCHEMA_INVALID')
add('zero_events_with_false_100_percent',lambda d:(d.update(events=[]),d['claims']['visual'].update(percent=100)),'SCHEMA_INVALID')
add('bad_event_type',lambda d:d['events'][0].update(type='manufacture'),'SCHEMA_INVALID')
add('missing_axes',lambda d:d['axes'].pop('z'),'SCHEMA_INVALID')
add('physical_count_not_documented',lambda d:d['claims'].pop('physical'),'SCHEMA_INVALID')
add('zero_axis_physical_semantics',lambda d:d.update(axes={'x':'foo','y':'bar','z':'baz'}),'SCHEMA_INVALID')
add('no_design_constraints',lambda d:d.update(constraints=[]),'SCHEMA_INVALID')
add('invalid_view_status',lambda d:d['views'].update(detail='DONE'),'SCHEMA_INVALID')
add('unverified_cad_claim',lambda d:d.update(validation='CAD VERIFIED'),'SCHEMA_INVALID')
add('correct_assembly',lambda d:None,'INCOMPLETE_EVIDENCE')
results=[]
for name,data,expected in CASES:
    checks=audit(data); actual=summarize(checks)
    results.append({'case':name,'expected':expected,'actual':actual,'pass':actual==expected})
print(json.dumps({'passed':sum(r['pass'] for r in results),'total':len(results),'cases':results},indent=2))
assert all(r['pass'] for r in results)
