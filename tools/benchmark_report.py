"""Report warm medians; refuse to rank cache hits or different generation settings."""
from pathlib import Path
import argparse,json,statistics,math
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);a=p.parse_args()
    plan=json.loads(a.manifest.read_text(encoding='utf8'));groups=plan['groups']
    if set(groups)!={'baseline','optimized'}:raise ValueError('Both groups required')
    totals={};settings=None;seen_paths=set();seen_prompts=set()
    for name,paths in groups.items():
        times=[]
        if len(paths)<2:raise ValueError('At least two fresh warm runs per group')
        for path in paths:
            source=Path(path).resolve()
            if source in seen_paths:raise ValueError('Duplicate run receipt')
            seen_paths.add(source)
            r=json.loads(source.read_text(encoding='utf8'))
            prompt=r.get('prompt_id')
            if not prompt or prompt in seen_prompts:raise ValueError('Distinct fresh prompt_id required')
            seen_prompts.add(prompt)
            if r.get('status')!='generated_self_checked_pending_independent_review' or not r.get('sampler_checks') or not all(v['passed'] for v in r['sampler_checks'].values()):raise ValueError('Failed, cached or unproven inference')
            current=r.get('comparison_settings')
            if not current:raise ValueError('Attach frozen model/input hashes, precision, seed, steps, frame count, dimensions and fps as comparison_settings')
            if settings is None:settings=current
            if current!=settings:raise ValueError('Unequal generation conditions')
            seconds=float(r['submitter_wall_seconds'])
            if not math.isfinite(seconds) or seconds<=0:raise ValueError('Positive finite timing required')
            times.append(seconds)
        totals[name]=statistics.median(times)
    print(json.dumps({'scope':'Warm submitter wall medians; no automatic quality approval','median_seconds':totals,'speedup_ratio':totals['baseline']/totals['optimized'],'time_reduction_percent':100*(1-totals['optimized']/totals['baseline']),'comparison_settings':settings},indent=2))
if __name__=='__main__':main()
