"""Run with: python3 -m valuation_lab --output outputs/results.json"""
import argparse
import json
from pathlib import Path
from .example import run_examples

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,help='Optional local JSON output path')
args=parser.parse_args()
result=run_examples()
payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
if args.output:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(payload+'\n',encoding='utf-8')
print(json.dumps(dict(dcf_equity=result['dcf']['equity'],
                      comps_equity=result['comps']['equity_ev_ebitda'],
                      per_equity=result['comps']['equity_per'],nav_equity=result['nav']['equity'],
                      dcf_after_obligation=result['fdd_illustration']['dcf']['equity']),indent=2))
