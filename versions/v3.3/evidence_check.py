#!/usr/bin/env python3
"""FORM SKILLS v3.3 candidate: manifest checks only, not CAD or manufacture validation."""
import json
import math
import sys

def audit(doc):
    results=[]
    def check(name, condition, detail):
        results.append({"check":name,"status":"PASS" if condition else "FAIL","detail":detail})
    dims=doc.get("dimensions",{})
    keys=("length_mm","width_mm","height_mm")
    numbers=[dims.get(k) for k in keys]
    valid=all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>0 for v in numbers)
    check("dimensions",valid,"Three positive finite dimensions are required.")
    axes=doc.get("axes",{})
    check("axes",all(k in axes for k in ("x","y","z")) and len(set(axes.values()))==3,"Three explicitly distinct axes required.")
    events=doc.get("events",[])
    ids=[e.get("id") for e in events]
    check("event_ids",len(ids)==len(set(ids)) and all(isinstance(i,str) and i for i in ids),"Unique stable IDs required.")
    check("event_schema",all(e.get("type") in ("physical","visual") and isinstance(e.get("before"),bool) and isinstance(e.get("after"),bool) for e in events),"Each event needs type, before and after.")
    for kind in ("physical","visual"):
        b=sum(e.get("before") is True for e in events if e.get("type")==kind)
        a=sum(e.get("after") is True for e in events if e.get("type")==kind)
        claim=doc.get("claims",{}).get(kind)
        if claim:
            expected=round(100*(b-a)/b,1) if b else None
            ok=claim.get("before")==b and claim.get("after")==a and expected is not None and abs(claim.get("percent",10000)-expected)<=0.11
            check("reduction_"+kind,ok,"Inventory "+str(b)+" to "+str(a)+" = "+str(expected)+"%.")
    views=doc.get("views",{})
    wanted=("profile","front","rear","three_quarter","detail")
    check("view_matrix",all(views.get(v) in ("PASS","FAIL","UNKNOWN") for v in wanted),"Five explicit viewpoint statuses required.")
    continuity=doc.get("continuity",{})
    check("continuity_evidence",continuity.get("status")!="PASS" or bool(continuity.get("evidence")),"G2 PASS requires evidence.")
    if valid:results.append({"check":"ratios","status":"INFO","detail":{"H/W":round(numbers[2]/numbers[1],4),"W/L":round(numbers[1]/numbers[0],4)}})
    return results

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python3 evidence_check.py manifest.json")
    with open(sys.argv[1],encoding="utf-8") as fp: data=json.load(fp)
    out=audit(data)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    sys.exit(int(any(item["status"]=="FAIL" for item in out)))
