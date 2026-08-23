import sys, json
sys.path.insert(0, r"C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1")
from baby_ai.adapters.operational_self import FormationCore
from baby_ai.core.continuity import ContinuitySnapshot
from baby_ai.core.receipts import ReceiptLedger
from baby_ai.core.provenance import ProvenanceLedger
from baby_ai import domain as D
s=ContinuitySnapshot.read(r"C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1\baby_ai\artifacts\repair\BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1\cold_restart_input.snapshot.json")
rcpts=ReceiptLedger.from_dict(s.receipts)
prov=ProvenanceLedger.from_dict(s.provenance, rcpts)
c=FormationCore.from_dict(s.operational_self, activation_id='r1-cold',
                          receipts=rcpts, provenance=prov)
out={'ready': c.formation_ready(), 'status': c.allocator_status,
      'route': c.route_decision('flux_alpha')['decision'],
      'receipt_count': len(c.receipts.entries),
      'prov_count': len(c.provenance.records)}
for i in range(50):
    c.ingest(D.experience_safe(c, ('flux_alpha' if i%3==0 else ('flux_beta' if i%3==1 else 'dura_gamma'))))
out['counts_after']=c.counts(); out['ids']=dict(c.ids.counters)
out['ok']=out['ready'] and out['receipt_count']>0 and out['prov_count']>0 and out['ids']['mem']>0
open(r"C:\Users\moop\FractalishBuild\baby-ai-assembly-v0.1\baby_ai\artifacts\repair\BABY_AI_ALLOCATOR_CONTINUITY_R001_v0_1\cold_restart_result.json","w").write(json.dumps(out, sort_keys=True, default=str))
