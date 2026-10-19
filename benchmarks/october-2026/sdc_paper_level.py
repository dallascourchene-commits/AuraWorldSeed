"""Source-aligned *domain-level* model of Stérin et al. Nature 657:646–652 (2026).
Not a DNA sequence simulator, not fitted to fluorescence, not authors' source code.
Physical-free-energy input terms are dimensionless assumptions; do not interpret as kcal/mol.
"""
from __future__ import annotations
import math, random, time, statistics, sys, platform, json, hashlib
from dataclasses import dataclass

def majority(a:int,b:int,c:int)->int: return int(a+b+c>=2)
def bits(n:int,width:int)->list[int]: return [(n>>i)&1 for i in range(width)]
def target(x:list[int], y:list[int]):
    inc=[0]; out=[]; sums=[]
    for a,b in zip(x,y):
        u=inc[-1]; sums.append(a^b^u);c=majority(a,b,u);out.append(c);inc.append(c)
    return inc[:-1],out,sums

def tile_library(x,y):
    """A is single anchor; B..N each have 2 competing tiles labelled 3-bit xy+incoming carry.
    Input bit-pair of next site is encoded on right domains when a next site exists.
    """
    ans=[]
    for i,(a,b) in enumerate(zip(x,y)):
        choices=(0,) if i==0 else (0,1)
        ans.append([{'position':chr(65+i) if i<26 else str(i), 'incoming_carry':u,
                     'left_3bit':f'{a}{b}{u}',
                     'outgoing_carry':majority(a,b,u),
                     'right_3bit':f'{x[i+1]}{y[i+1]}{majority(a,b,u)}' if i+1<len(x) else None,
                     'sum_bit':a^b^u} for u in choices])
    return ans

def energy_of_choices(x,y, choices, J, biases=None):
    assert choices[0]==0
    e=0.
    for i in range(1,len(choices)):
        a,b=x[i-1],y[i-1]
        prev_out=majority(a,b,choices[i-1])
        e += J[i]*(prev_out!=choices[i])
        if biases: e+=biases[i][choices[i]]
    return e

def enumerate_exact(x,y,J,biases=None):
    n=len(x);assert 1<=n<=18
    vals=[];states=[];minimum=float('inf')
    for mask in range(1<<(n-1)):
        c=[0]+[(mask>>(i-1))&1 for i in range(1,n)]
        e=energy_of_choices(x,y,c,J,biases);states.append(c);vals.append(e);minimum=min(minimum,e)
    weights=[math.exp(-(e-minimum)) for e in vals]
    z=sum(weights); p=[v/z for v in weights]
    ix=max(range(len(p)),key=lambda i:p[i]);target_in,outs,ss=target(x,y)
    target_index=states.index(target_in)
    return {'partition_log':math.log(z)-minimum,'map_state':states[ix], 'map_energy':vals[ix],
            'target_probability':p[target_index], 'true_target':target_in,
            'top_probability':max(p),'configuration_count':len(p),'expected_output':ss}

# 2x2 matrices indexed [previous outgoing carry, new outgoing carry]
def transfer(xbit,ybit,j,bias=(0.,0.)):
    mat=[0.,0.,0.,0.]
    for prev in (0,1):
        for chosen in (0,1):
            nxt=majority(xbit,ybit,chosen)
            mat[2*prev+nxt]+=math.exp(-j*(prev!=chosen)-bias[chosen])
    return tuple(mat)

def mm(a,b):
    return (a[0]*b[0]+a[1]*b[2],a[0]*b[1]+a[1]*b[3],a[2]*b[0]+a[3]*b[2],a[2]*b[1]+a[3]*b[3])

def norm(m,scale=0.):
    d=max(m)
    if d<=0: raise ValueError('All zero matrix')
    return tuple(q/d for q in m),scale+math.log(d)

def terminal_z(m,logscale,start):
    return math.log(m[2*start]+m[2*start+1])+logscale

def full_partition(x,y,J,biases=None):
    first=majority(x[0],y[0],0)
    m=(1.,0.,0.,1.);ls=0.
    for i in range(1,len(x)):
        t=transfer(x[i],y[i],J[i], biases[i] if biases else (0.,0.))
        m,ls=norm(mm(m,t),ls)
    return terminal_z(m,ls,first)

class UpdateTree:
    """Exact segment-tree transfer product, O(log N) mutation of one local potential, O(N) storage."""
    def __init__(self,x,y,J,biases=None):
        self.x=x[:];self.y=y[:];self.J=J[:]
        self.biases=[list(v) for v in biases] if biases else [[0.,0.] for _ in x]
        self.count=max(0,len(x)-1);self.size=1
        while self.size<self.count:self.size*=2
        self.nodes=[None]*(2*self.size)
        for k in range(self.size):
            i=k+1
            self.nodes[self.size+k]=norm(transfer(x[i],y[i],J[i],self.biases[i])) if i<len(x) else ((1.,0.,0.,1.),0.)
        for k in range(self.size-1,0,-1):self._combine(k)
    def _combine(self,k):
        left,lscale=self.nodes[2*k];right,rscale=self.nodes[2*k+1]
        self.nodes[k]=norm(mm(left,right),lscale+rscale)
    def update_bias(self,i,new_pair):
        if not 1<=i<len(self.x):raise ValueError('first position is fixed anchor')
        self.biases[i]=list(new_pair)
        k=self.size+i-1
        self.nodes[k]=norm(transfer(self.x[i],self.y[i],self.J[i],self.biases[i]))
        while k>1:k//=2;self._combine(k)
    def log_partition(self):
        m,scale=self.nodes[1]
        return terminal_z(m,scale,majority(self.x[0],self.y[0],0))

def run_source_example():
    x=bits(10,4);y=bits(3,4);inc,out,ss=target(x,y)
    assert sum(b<<i for i,b in enumerate(ss))==13
    J=[0.,4.,4.,4.]
    lib=tile_library(x,y)
    baseline=full_partition(x,y,J)
    exact=enumerate_exact(x,y,J)
    tree=UpdateTree(x,y,J)
    assert abs(tree.log_partition()-baseline)<1e-12
    assert abs(baseline-exact['partition_log'])<1e-12
    expected=(1+math.exp(-4))**(-3)
    assert abs(exact['target_probability']-expected)<1e-12
    return {'program':'N=4 SDC Addition','input_x':10,'input_y':3,'output':13,'x_bits_lsb_first':x,'y_bits_lsb_first':y,'output_bits_lsb_first':ss,'tile_library':lib,
            'anchor_tiles':len(lib[0]), 'competitors_per_remaining_site':[len(g) for g in lib[1:]],
            'configurations':exact['configuration_count'],'unit':'dimensionless illustrative energy; J=4 NOT experimentally calibrated',
            'assumed_mismatch_J':4.0,'logZ_bruteforce':exact['partition_log'],'logZ_baseline':baseline,'logZ_tree':tree.log_partition(),
            'P_correct_model':exact['target_probability'],'reported_experimental_yield':'not a prediction; experimental yield is a distinct fluorescence metric'}

def test_suite():
    rng=random.Random(20261015)
    assert run_source_example()['output']==13
    cnt=0
    for n in range(2,13):
        for seed in range(8):
            x=[rng.randrange(2) for _ in range(n)];y=[rng.randrange(2) for _ in range(n)]
            J=[0.]+[rng.uniform(1.5,6) for _ in range(n-1)]
            biases=[[0.,0.]]+[[rng.uniform(-.5,.5),rng.uniform(-.5,.5)] for _ in range(n-1)]
            a=enumerate_exact(x,y,J,biases)['partition_log']
            b=full_partition(x,y,J,biases);tree=UpdateTree(x,y,J,biases)
            assert abs(a-b)<1e-10 and abs(b-tree.log_partition())<1e-10, (n,a,b)
            i=rng.randrange(1,n);pair=(rng.uniform(-2,2),rng.uniform(-2,2))
            biases[i]=list(pair);tree.update_bias(i,pair)
            assert abs(tree.log_partition()-full_partition(x,y,J,biases))<1e-10
            cnt+=1
    # mutation of a SINGLE tile concentration can overturn an initially correct target.
    x=bits(10,4);y=bits(3,4);j=[0.,3.,3.,3.]; bias=[[0.,0.] for _ in range(4)]
    ideal=enumerate_exact(x,y,j)
    assert ideal['map_state']==ideal['true_target']
    i=2;wrong=1-ideal['true_target'][i]
    bias[i][wrong]=-10.
    adversarial=enumerate_exact(x,y,j,bias)
    assert adversarial['map_state']!=adversarial['true_target']
    # Target probability at equilibrium is NOT sufficient to establish kinetics.
    return {'cases_enumeration_vs_dp_tree':cnt,'input_program_four_site':'PASS_EXACT_10_PLUS_3_EQUALS_13',
            'adversarial_single_tile_bias':{'status':'EXPECTED_MISMATCHED_GROUND_STATE','target_probability_before':ideal['target_probability'],'target_probability_after':adversarial['target_probability']},
            'measurement_claim':'none','source_sequence_claim':'none'}

def benchmark(repeats=3,updates=120):
    rng=random.Random(6223);rows=[]
    for n in [4,25,256,2048,8192,32768]:
        x=[rng.randrange(2) for _ in range(n)];y=[rng.randrange(2) for _ in range(n)];J=[0.]+[4.0]*(n-1)
        change_index=[rng.randrange(1,n) for _ in range(updates)]
        perturb=[(rng.uniform(-.8,.8),rng.uniform(-.8,.8)) for _ in range(updates)]
        baseline_time=[];tree_time=[];max_error=0.;checksum=0.
        for rep in range(repeats):
            bias=[[0.,0.] for _ in range(n)]
            seg=UpdateTree(x,y,J,bias)
            t0=time.perf_counter_ns()
            baselines=[]
            for i,pair in zip(change_index,perturb):
                bias[i]=list(pair)
                baselines.append(full_partition(x,y,J,bias))
            baseline_time.append((time.perf_counter_ns()-t0)/1e6)
            t0=time.perf_counter_ns()
            trees=[]
            for i,pair in zip(change_index,perturb):
                seg.update_bias(i,pair);trees.append(seg.log_partition())
            tree_time.append((time.perf_counter_ns()-t0)/1e6)
            for aa,bb in zip(baselines,trees):max_error=max(max_error,abs(aa-bb))
            checksum=sum(trees)
        assert max_error<max(1e-7,n*3e-12)
        bt=statistics.median(baseline_time);tt=statistics.median(tree_time)
        rows.append({'n_positions':n,'updates':updates,'repeats':repeats,'full_recompute_median_ms':round(bt,4),
                    'tree_update_median_ms':round(tt,4),'speedup_full_over_tree':round(bt/tt,3),'max_abs_logZ_error':max_error,
                    'checksum':round(checksum,8),'memory_complexity_full':'O(1) live matrices, plus provided input arrays','memory_complexity_tree':'O(N) matrices, O(log N) update'})
    return rows

if __name__=='__main__':
    from pathlib import Path
    p=Path(__file__).parent
    print('Running exact source-example, enumerations & stress tests...',flush=True)
    example=run_source_example();tests=test_suite();print('Testing done:',tests,flush=True)
    benches=benchmark();print('bench',[(r['n_positions'],r['speedup_full_over_tree']) for r in benches],flush=True)
    result={'schema':'TesseraSDCNatureAlignedDomainBenchmarkV1','paper_doi':'10.1038/s41586-026-10996-5',
            'official_authors_sequences_or_nupack':'NOT_EXECUTED_UNAVAILABLE_FROM_ENVIRONMENT',
            'claim':'Exact specified four-scaffold FSM addition logic; domain-level surrogate energetics, not author chemistry fit',
            'runtime':{'python':sys.version,'platform':platform.platform()},
            'experiment':example,'tests':tests,'benchmarks':benches,
            'limitations':['Not authors original Zenodo code nor a replication of experimental yields','Published scaffold strand sequence, measured sequence-specific ΔG, NUPACK and anneal dynamics not instantiated','No atomistic dynamics or independently modeled molecules','Speedup is for repeated single-local-parameter updates, not for one-shot four-position DNA computing','Segment tree trades O(N) memory for O(logN) update latency','Physical preparation and energy cost have not been measured']}
    (p/'benchmarks.json').write_text(json.dumps(result,indent=2))
    print('Saved',p/'benchmarks.json',flush=True)
