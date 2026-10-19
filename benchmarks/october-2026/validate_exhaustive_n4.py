import json,math,random
from pathlib import Path
from sdc_paper_level import bits,enumerate_exact,full_partition,UpdateTree,tile_library,target
passes=0;max_error=0.;bad=[]
for x in range(16):
 for y in range(16):
  xx=bits(x,4);yy=bits(y,4);incoming,out,ss=target(xx,yy)
  expected=(x+y)&15
  a=sum(b<<i for i,b in enumerate(ss))
  z=enumerate_exact(xx,yy,[0,4,4,4])
  tree=UpdateTree(xx,yy,[0,4,4,4]);actual=tree.log_partition()
  err=abs(actual-z['partition_log']);max_error=max(max_error,err)
  if a!=expected or incoming!=z['map_state'] or err>1e-12:bad.append((x,y,a,expected,err))
  else:passes+=1
assert passes==256 and not bad
res={'schema':'TesseraN4SourceProgramExhaustiveInputTests','input_pairs':256,'passed':passes,'failed':len(bad),'max_logZ_error':max_error,
 'authors_code':'not tested','scope':'all 4-bit input pairs in paper-specified 2-state Addition FSM at assumed J=4'}
Path(__file__).with_name('exhaustive_n4_receipt.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
