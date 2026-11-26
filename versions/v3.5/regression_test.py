#!/usr/bin/env python3
"""v3.5 development regression. A raised exception is CRASH, never REJECTED.

Optional --checker-dir replays the added cases against a frozen older checker.
These cases are authored with the changes: not an independent design holdout.
"""
import argparse
import copy
import importlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
R, I, P = 'REJECTED', 'PROJECT_INCOMPLETE', 'CHECKS_PASS'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--checker-dir', type=Path, default=HERE)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    checker = args.checker_dir.resolve()
    sys.path.insert(0, str(checker))
    project = importlib.import_module('project_check')
    profile = importlib.import_module('profile_check')
    section = importlib.import_module('section_check')
    results = []
    inherited_exit = None
    if checker == HERE:
        inherited = subprocess.run([sys.executable, str(HERE/'regression_test_v34.py')], capture_output=True, text=True)
        inherited_exit = inherited.returncode
        print(inherited.stdout, end='')
        if inherited.stderr: print(inherited.stderr, file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix='form-v35-') as scratch:
        base_dir = Path(scratch)
        for name in ('form04.svg', 'form04-edge.json'):
            (base_dir/name).write_bytes((HERE/'examples'/name).read_bytes())
        base = json.loads((HERE/'examples/concept-example-v3.3.json').read_text())
        base.update(constraints=['synthetic test'], joints=[dict(name='j', nominal_mm=.15, tolerance_mm=.03)],
                    view_sources={v:'form04.svg' for v in base['views']})
        base['views'] = {v:'PASS' for v in base['views']}
        base['continuity'].update(status='PASS',check=dict(tool='section_check',spec='form04-edge.json'))
        edge = json.loads((base_dir/'form04-edge.json').read_text())
        cylinder = {'name':'Synthetic regression cylinder', 'nodes':[[10,0,90],[10,10,90]],
                    'declared':{'height_mm':10,'diameter_mm':20}, 'wall':1,
                    'keepouts':[{'name':'core','z0':1,'z1':9,'r':8}]}

        def run(name, expected, function, inputs=None):
            try:
                actual = function()
                row = {'case':name,'expected':expected,'actual':actual,'matches':actual==expected}
            except Exception as exc:
                row = {'case':name,'expected':expected,'actual':'CRASH', 'error':type(exc).__name__+': '+str(exc),'matches':False}
            if inputs is not None: row['input'] = inputs
            results.append(row)
            print(('PASS' if row['matches'] else 'FAIL').ljust(5),name, 'expected',expected,'actual',row['actual'])

        def manifest_case(name, expected, mutate):
            doc = copy.deepcopy(base); mutate(doc)
            run(name, expected, lambda:project.audit(doc, base_dir)['status'], doc)

        manifest_case('known_continuity_failure', R, lambda d:d['continuity'].update(status='FAIL'))
        manifest_case('known_view_failure', R, lambda d:d['views'].update(front='FAIL'))
        manifest_case('unknown_still_incomplete', I, lambda d:d['continuity'].update(status='UNKNOWN'))
        manifest_case('complete_control', P, lambda d:None)
        run('root_wrong_type', R, lambda:project.audit([],base_dir)['status'], [])
        manifest_case('event_wrong_type', R, lambda d:d.update(events=[0]))
        manifest_case('event_id_unhashable', R, lambda d:d['events'][0].update(id=['not','id']))
        manifest_case('claims_wrong_type', R, lambda d:d.update(claims={'visual':[]}))
        (base_dir/'broken.json').write_text('{ not json')
        manifest_case('referenced_json_broken', R, lambda d:d['continuity']['check'].update(spec='broken.json'))
        manifest_case('nonfinite_joint', R, lambda d:d['joints'][0].update(tolerance_mm=float('inf')))

        def section_case(name, expected, mutate):
            doc=copy.deepcopy(edge);mutate(doc)
            run(name,expected,lambda:section.run(doc)[1],doc)
        section_case('section_control',True,lambda d:None)
        section_case('negative_layer_cancelled_by_positive',False,
                     lambda d:d['stack'].extend([['negative',-.5],['compensation',.5]]))
        section_case('negative_bezel_compensated',False,
                     lambda d:d['bezel'].update(clear=-.1,lip=1.1))
        section_case('edge_end_disagrees_with_stack',False,
                     lambda d:d['edge']['nodes'][-1].__setitem__(1,7.5))
        section_case('section_empty_nodes',False,lambda d:d.update(edge={'nodes':[]}))
        section_case('section_radius_exceeds_thickness',False,lambda d:d.update(edge={'arc_radius':10}))

        def evaluated(doc):
            if hasattr(profile,'evaluate'):
                try:
                    _,m,errors=profile.evaluate(doc)
                    return R if errors else P
                except (ValueError,TypeError,KeyError,IndexError,OverflowError):
                    return R
            # Reproduce the old CLI's exit semantics without silently fixing it.
            source=base_dir/'profile-input.json'
            source.write_text(json.dumps(doc,allow_nan=True))
            proc=subprocess.run([sys.executable,str(checker/'profile_check.py'),str(source)],capture_output=True,text=True)
            if proc.returncode==0: return P
            return 'CRASH' if 'Traceback' in proc.stderr else R

        def profile_case(name, expected, mutate):
            doc=copy.deepcopy(cylinder);mutate(doc)
            run(name,expected,lambda:evaluated(doc),doc)
        profile_case('profile_control',P,lambda d:None)
        profile_case('keepout_partly_outside',R,lambda d:d['keepouts'][0].update(z0=-1))
        profile_case('keepout_fully_outside',R,lambda d:d['keepouts'][0].update(z0=-3,z1=-1))
        profile_case('declared_dimension_mismatch',R,lambda d:d['declared'].update(height_mm=12))
        profile_case('rounding_does_not_hide_mismatch',R,lambda d:d.update(nodes=[[10,0,90],[10,10.54,90]]))
        profile_case('required_declared_missing',R,lambda d:d.pop('declared'))
        profile_case('negative_radial_wall',R,lambda d:d.update(wall=-3))
        profile_case('ambiguous_nodes_and_points',R,lambda d:d.update(points=[[10,0],[10,10]]))
        profile_case('nonfinite_profile_coordinate',R,lambda d:d['nodes'][0].__setitem__(0,float('nan')))

        vertices=[(10,0),(10,2.24),(6,2.25),(10,2.26),(10,10)]
        points=[]
        for a,b in zip(vertices,vertices[1:]):
            n=math.ceil(math.dist(a,b)/.05)
            points.extend([(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n)])
        points.append(vertices[-1])
        run('narrow_intrusion_between_old_stations',False,
            lambda:profile.measure(points,cylinder['keepouts'],1)['fits'][0]['ok'],
            {'points':points,'keepouts':cylinder['keepouts'],'wall':1})
        shifted=profile.build([[10,50,90],[10,60,90]])
        run('origin_translation_does_not_move_relative_widest',50.0,
            lambda:profile.measure(shifted)['widest_at_pct_from_top'], {'nodes':[[10,50,90],[10,60,90]]})

        # CLI smoke checks: nonzero exit and a diagnostic, not a traceback.
        (base_dir/'form03.json').write_bytes((HERE/'examples/form03-edge.json').read_bytes())
        command=[sys.executable,str(checker/'section_check.py'),str(base_dir/'form03.json')]
        proc=subprocess.run(command,capture_output=True,text=True)
        run('section_failed_cli_exit',2,lambda:proc.returncode,{'example':'form03-edge.json'})
        (base_dir/'undeclared.json').write_text(json.dumps({k:v for k,v in cylinder.items() if k!='declared'}))
        manifest_case('profile_missing_declared_not_continuity_pass',R,
                      lambda d:d['continuity'].update(check={'tool':'profile_check','spec':'undeclared.json'}))

    # JSON report must itself be standard JSON, even for intentionally invalid input.
    def serializable(value):
        if isinstance(value,float) and not math.isfinite(value): return str(value)
        if isinstance(value,dict): return {k:serializable(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)): return [serializable(v) for v in value]
        return value
    report={'checker_version':checker.name,'inherited_regression_exit':inherited_exit,
            'added_cases':len(results),'matched':sum(r['matches'] for r in results),
            'results':serializable(results),'validation':'development regression; not independent design validation'}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('ADDED CASES:',report['added_cases'],'MATCHED:',report['matched'])
    return int(report['matched']!=report['added_cases'] or inherited_exit not in (None,0))


if __name__=='__main__':
    raise SystemExit(main())
