import numpy as np, sys
from polybrains.learning_module import ConsensusEvidenceGraphLM as C
from tbp.monty.frameworks.models.evidence_matching.learning_module import EvidenceGraphLM
stats={"send":0,"send_none":0,"recv":0,"changed":0}
_sv = EvidenceGraphLM.send_out_vote
def sv(self):
    r=_sv(self); stats["send"]+=1
    if r is None: stats["send_none"]+=1
    return r
EvidenceGraphLM.send_out_vote = sv
_ue = C._update_evidence_with_vote
def ue(self, votes, gid):
    b=np.ma.filled(self._hypotheses[gid].evidence,0).copy()
    _ue(self,votes,gid); stats["recv"]+=1
    a=np.ma.filled(self._hypotheses[gid].evidence,0)
    if not np.allclose(b,a): stats["changed"]+=1
C._update_evidence_with_vote = ue
import atexit
atexit.register(lambda: sys.stderr.write(f"\nVOTE-SPY {stats}\n"))
