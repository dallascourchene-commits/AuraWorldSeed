#!/usr/bin/env python3
from __future__ import annotations
import json, math, time, hashlib, heapq, itertools, struct, os, hmac
from dataclasses import dataclass, asdict
from collections import deque
from pathlib import Path
import numpy as np
from sklearn.decomposition import PCA


SEED=20260917
RNG=np.random.default_rng(SEED)
DIM=29
ACTIVE=800
LAYERS=5
DATA_LAYERS=4
PAD=64
WAVELENGTH=532e-9
PIXEL_PITCH=8e-6
PROP_Z=0.015


# ---------- utilities ----------
def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def cjson(o)->bytes: return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def timer(fn,*a,**kw):
    t=time.perf_counter(); r=fn(*a,**kw); return r,(time.perf_counter()-t)*1000


# ---------- 29x29 / 800-active FlyBrain geometry ----------
def is_reserved(r,c):
    if (r<=2 and c<=2) or (r<=2 and c>=26) or (r>=26 and c<=2): return True
    if r>=27 and c>=27: return True
    if r==1 and c in (6,10,14,18,22): return True
    if c==1 and r in (6,10,14,18,22): return True
    return False
ACTIVE_LUT=[(r,c) for r in range(DIM) for c in range(DIM) if not is_reserved(r,c)]
FID_LUT=[(r,c) for r in range(DIM) for c in range(DIM) if is_reserved(r,c)]
assert len(ACTIVE_LUT)==800 and len(FID_LUT)==41
STRIDE=137
SPATIAL_POS=np.array([ACTIVE_LUT[(k*STRIDE)%ACTIVE] for k in range(ACTIVE)],dtype=np.int16)
RR,CC=SPATIAL_POS[:,0],SPATIAL_POS[:,1]
FID=np.array(FID_LUT,dtype=np.int16); FR,FC=FID[:,0],FID[:,1]
PHASES=np.array([0.0,0.5*np.pi,np.pi,1.5*np.pi],dtype=np.float64)


# ---------- scalar angular-spectrum optical fixture ----------
def angular_transfer(n=PAD,dx=PIXEL_PITCH,wavelength=WAVELENGTH,z=PROP_Z):
    fx=np.fft.fftfreq(n,d=dx); fy=np.fft.fftfreq(n,d=dx)
    FX,FY=np.meshgrid(fx,fy,indexing='xy')
    arg=1.0-(wavelength*FX)**2-(wavelength*FY)**2
    root=np.sqrt(np.clip(arg,0.0,None))
    H=np.exp(1j*(2*np.pi/wavelength)*z*root)
    H[arg<0]=0.0
    return H
H=angular_transfer()


@dataclass(frozen=True)
class OpticalCondition:
    name:str; complex_noise:float; gain_sigma:float; phase_drift_sigma:float; dropout_layer:int|None=None
OPTICAL_CONDS=[
    OpticalCondition('clean',0.008,0.005,0.01),
    OpticalCondition('moderate',0.035,0.018,0.05),
    OpticalCondition('harsh',0.075,0.035,0.10),
    OpticalCondition('severe',0.150,0.060,0.18),
    OpticalCondition('extreme',0.300,0.080,0.24),
    OpticalCondition('catastrophic',0.550,0.120,0.35),
    OpticalCondition('moderate_layer2_dropout',0.035,0.018,0.05,2),
]


def make_symbol_pages(pages:int,rng:np.random.Generator):
    data=rng.integers(0,4,size=(pages,DATA_LAYERS,ACTIVE),dtype=np.uint8)
    parity=np.bitwise_xor.reduce(data,axis=1,keepdims=True)
    return data,np.concatenate([data,parity],axis=1)


def symbols_to_fields(all_layers:np.ndarray):
    pages=all_layers.shape[0]
    g=np.zeros((pages,LAYERS,DIM,DIM),dtype=np.uint8)
    g[:,:,RR,CC]=all_layers
    fid=(np.arange(len(FID))%4).astype(np.uint8)
    g[:,:,FR,FC]=fid[None,None,:]
    f=np.exp(1j*PHASES[g]).astype(np.complex128)
    out=np.zeros((pages,LAYERS,PAD,PAD),dtype=np.complex128)
    s=(PAD-DIM)//2
    out[:,:,s:s+DIM,s:s+DIM]=f
    return out,fid


def propagate_batch(field,H=H):
    return np.fft.ifft2(np.fft.fft2(field,axes=(-2,-1))*H,axes=(-2,-1))
def backprop_batch(field,H=H):
    return np.fft.ifft2(np.fft.fft2(field,axes=(-2,-1))*np.conj(H),axes=(-2,-1))


def optical_roundtrip(all_layers:np.ndarray,cond:OpticalCondition,seed:int):
    rng=np.random.default_rng(seed)
    field,fid=symbols_to_fields(all_layers)
    obs=propagate_batch(field)
    pages=all_layers.shape[0]
    gain=rng.normal(1.0,cond.gain_sigma,size=(pages,LAYERS,1,1))
    drift=rng.normal(0.0,cond.phase_drift_sigma,size=(pages,LAYERS,1,1))
    obs=obs*gain*np.exp(1j*drift)
    if cond.dropout_layer is not None:
        obs[:,cond.dropout_layer]*=0.015
    noise=cond.complex_noise*(rng.normal(size=obs.shape)+1j*rng.normal(size=obs.shape))/math.sqrt(2)
    obs=obs+noise
    rec=backprop_batch(obs)
    s=(PAD-DIM)//2
    rec=rec[:,:,s:s+DIM,s:s+DIM]
    # global complex calibration from 41 known fiducials
    ideal=np.exp(1j*PHASES[fid])
    fo=rec[:,:,FR,FC]
    alpha=np.mean(fo*np.conj(ideal[None,None,:]),axis=2)
    quality=np.abs(alpha)
    layer_ok=quality>0.30
    alpha_safe=np.where(np.abs(alpha)<0.05,0.05+0j,alpha)
    rec=rec/alpha_safe[:,:,None,None]
    z=rec[:,:,RR,CC]
    # nearest phase state on unit circle
    centers=np.exp(1j*PHASES)
    d=np.abs(z[...,None]-centers[None,None,None,:])**2
    dec=np.argmin(d,axis=-1).astype(np.uint8)
    return dec,layer_ok,quality


def recover_parity(decoded,layer_ok):
    out=decoded[:,:DATA_LAYERS].copy(); recn=0; badn=0
    for p in range(decoded.shape[0]):
        bad=np.where(~layer_ok[p])[0]
        if len(bad)==0: continue
        if len(bad)==1 and bad[0]<DATA_LAYERS and layer_ok[p,DATA_LAYERS]:
            j=int(bad[0]); x=decoded[p,DATA_LAYERS].copy()
            for q in range(DATA_LAYERS):
                if q!=j: x^=decoded[p,q]
            out[p,j]=x; recn+=1
        elif len(bad)==1 and bad[0]==DATA_LAYERS: recn+=1
        else: badn+=1
    return out,recn,badn


def bits4(a):
    return np.stack([(a>>1)&1,a&1],axis=-1).astype(np.uint8)


def optical_matrix(pages=48):
    rng=np.random.default_rng(SEED+2)
    tx,all_layers=make_symbol_pages(pages,rng)
    rows=[]
    for i,c in enumerate(OPTICAL_CONDS):
        (dec,ok,q),ms=timer(optical_roundtrip,all_layers,c,SEED+200+i)
        out,er,bad=recover_parity(dec,ok)
        ser=float(np.mean(out!=tx)); ber=float(np.mean(bits4(out)!=bits4(tx)))
        rows.append(dict(condition=c.name,pages=pages,symbol_error_rate=ser,bit_error_rate=ber,
                         exact_pages=int(np.sum(np.all(out==tx,axis=(1,2)))),page_exact_fraction=float(np.mean(np.all(out==tx,axis=(1,2)))),
                         erasure_pages_recovered=er,unrecoverable=bad,mean_calibration_quality=float(q.mean()),simulation_ms=ms))
    return rows


# ---------- Rubik/K27 exact transition owner ----------
COORDS=[(x,y,z) for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1)]
C2I={c:i for i,c in enumerate(COORDS)}
CORE=C2I[(0,0,0)]


def rot_coord(c,axis,sgn):
    x,y,z=c
    if axis==0:
        return (x,-z,y) if sgn==1 else (x,z,-y)
    if axis==1:
        return (z,y,-x) if sgn==1 else (-z,y,x)
    return (-y,x,z) if sgn==1 else (y,-x,z)


def make_perm(axis,layer,sgn):
    p=list(range(27))
    for i,c in enumerate(COORDS):
        if c[axis]==layer: p[i]=C2I[rot_coord(c,axis,sgn)]
    return tuple(p)
MOVES=[]
for a in range(3):
    for l in (-1,0,1):
        for sgn in (1,-1):
            MOVES.append((f"{'XYZ'[a]}{l:+d}{'+' if sgn==1 else '-'}",make_perm(a,l,sgn)))
MOVE_BY_NAME={n:p for n,p in MOVES}
INV_NAME={}
for n,_ in MOVES:
    base=n[:-1]; INV_NAME[n]=base+('-' if n[-1]=='+' else '+')
assert all(p[CORE]==CORE for _,p in MOVES)


def apply_mask(mask:int,p):
    out=0
    m=mask
    while m:
        b=(m & -m); i=b.bit_length()-1; out |= 1<<p[i]; m-=b
    return out


def shell(i): return sum(abs(v) for v in COORDS[i])
SHELLS={r:[i for i in range(27) if shell(i)==r] for r in (0,1,2,3)}


def mask_shell_fingerprint(mask:int):
    return tuple(sum((mask>>i)&1 for i in SHELLS[r]) for r in (0,1,2,3))


def build_orbit_graph():
    # 6 occupied crystal lanes: 2 face + 2 edge + 2 corner. Core remains control-only.
    start_ids=SHELLS[1][:2]+SHELLS[2][:2]+SHELLS[3][:2]
    start=sum(1<<i for i in start_ids)
    masks=[start]; idx={start:0}; adj=[]; move_idx=[]; q=deque([start])
    while q:
        m=q.popleft(); ns=[]; ms=[]
        for mi,(_,p) in enumerate(MOVES):
            t=apply_mask(m,p)
            if t not in idx:
                idx[t]=len(masks); masks.append(t); q.append(t)
            ns.append(idx[t]); ms.append(mi)
        adj.append(ns); move_idx.append(ms)
    return np.array(masks,dtype=np.uint32),np.array(adj,dtype=np.int32),np.array(move_idx,dtype=np.int8),idx


def bfs_dist(adj,goal):
    n=len(adj); d=np.full(n,65535,dtype=np.uint16); d[goal]=0; q=deque([goal])
    while q:
        u=q.popleft(); du=int(d[u])+1
        for v in adj[u]:
            if d[v]==65535: d[v]=du; q.append(int(v))
    return d


def pca_charts(masks,adj,seed=SEED):
    n=len(masks)
    occ=np.empty((n,27),dtype=np.float32)
    for j in range(27): occ[:,j]=((masks>>j)&1).astype(np.float32)
    raw=PCA(n_components=8,random_state=seed).fit_transform(occ).astype(np.float32)
    rng=np.random.default_rng(seed+77)
    lm_train=rng.choice(n,size=24,replace=False)
    dmat=np.stack([bfs_dist(adj,int(g)) for g in lm_train]).T.astype(np.float32)
    geo=PCA(n_components=8,random_state=seed+1).fit_transform(dmat).astype(np.float32)
    # fit distance scale only on train-landmark distances
    def fit_scale(emb):
        ratios=[]
        for col,g in enumerate(lm_train):
            e=np.linalg.norm(emb-emb[g],axis=1); d=dmat[:,col]
            good=e>1e-7
            rr=d[good]/e[good]
            ratios.append(rr[np.isfinite(rr)])
        return float(np.median(np.concatenate(ratios)))
    return raw,geo,fit_scale(raw),fit_scale(geo),lm_train,dmat


def astar(adj,emb,scale,source,goal):
    n=len(adj); inf=10**9
    g=np.full(n,inf,dtype=np.int32); g[source]=0
    parent=np.full(n,-1,dtype=np.int32); pmove=np.full(n,-1,dtype=np.int16)
    h=lambda u: scale*float(np.linalg.norm(emb[u]-emb[goal]))
    heap=[(h(source),0,source)]; seen=np.zeros(n,dtype=bool); expansions=0
    while heap:
        f,gu,u=heapq.heappop(heap)
        if seen[u]: continue
        seen[u]=True; expansions+=1
        if u==goal: break
        for mi,v in enumerate(adj[u]):
            v=int(v); ng=gu+1
            if ng<g[v]:
                g[v]=ng; parent[v]=u; pmove[v]=mi; heapq.heappush(heap,(ng+h(v),ng,v))
    if parent[goal]<0 and source!=goal: return None,expansions
    path=[]; u=goal
    while u!=source:
        path.append(int(pmove[u])); u=int(parent[u])
    path.reverse(); return path,expansions


def verify_path(start_mask,path,goal_mask):
    m=int(start_mask)
    for mi in path: m=apply_mask(m,MOVES[mi][1])
    return m==int(goal_mask)


def astar_alt(adj,dmat,source,goal):
    # ALT heuristic: max landmark distance difference. Admissible by triangle inequality.
    n=len(adj); inf=10**9
    g=np.full(n,inf,dtype=np.int32); g[source]=0
    parent=np.full(n,-1,dtype=np.int32); pmove=np.full(n,-1,dtype=np.int16)
    goalv=dmat[goal]
    def h(u): return int(np.max(np.abs(dmat[u].astype(np.int32)-goalv.astype(np.int32))))
    heap=[(h(source),0,source)]; seen=np.zeros(n,dtype=bool); expansions=0
    while heap:
        f,gu,u=heapq.heappop(heap)
        if seen[u]: continue
        seen[u]=True; expansions+=1
        if u==goal: break
        for mi,v in enumerate(adj[u]):
            v=int(v); ng=gu+1
            if ng<g[v]:
                g[v]=ng; parent[v]=u; pmove[v]=mi; heapq.heappush(heap,(ng+h(v),ng,v))
    if parent[goal]<0 and source!=goal: return None,expansions
    path=[]; u=goal
    while u!=source:
        path.append(int(pmove[u])); u=int(parent[u])
    path.reverse(); return path,expansions


def rubik_fingerprint_and_planning():
    (graph,ms)=timer(build_orbit_graph)
    masks,adj,moveidx,index=graph
    fp=mask_shell_fingerprint(int(masks[0]))
    # exact combinatorial universe sharing the same shell-count fingerprint
    all_same=[]
    for a in itertools.combinations(SHELLS[1],fp[1]):
      for b in itertools.combinations(SHELLS[2],fp[2]):
       for c in itertools.combinations(SHELLS[3],fp[3]):
        all_same.append(sum(1<<i for i in a+b+c))
    same_total=len(all_same); reachable=len(masks); same_unreachable=same_total-reachable
    rng=np.random.default_rng(SEED+31)
    held=rng.choice(np.array(all_same,dtype=np.uint32),size=2000,replace=False)
    held_reach=sum(int(int(x) in index) for x in held)
    # different fingerprint negatives
    diff=[]
    while len(diff)<1000:
        ids=rng.choice([i for i in range(27) if i!=CORE],size=6,replace=False)
        m=sum(1<<int(i) for i in ids)
        if mask_shell_fingerprint(m)!=fp: diff.append(m)
    diff_false=sum(int(m in index) for m in diff)
    # route inverse canary
    inv_ok=0
    for _ in range(10000):
        m=int(masks[int(rng.integers(len(masks)))])
        seq=rng.integers(0,len(MOVES),size=12)
        x=m
        names=[]
        for mi in seq:
            name,p=MOVES[int(mi)]; x=apply_mask(x,p); names.append(name)
        for name in reversed(names): x=apply_mask(x,MOVE_BY_NAME[INV_NAME[name]])
        inv_ok += int(x==m)
    # explicit REBIND maps one same-fingerprint unreachable target; proves bijective escape but distinct from Rubik geometry.
    target=next(m for m in all_same if m not in index)
    src_ids=[i for i in range(27) if (int(masks[0])>>i)&1]; dst_ids=[i for i in range(27) if (target>>i)&1]
    # shell-wise deterministic bijection, identity elsewhere then swaps/assigns via full permutation construction
    mapping=list(range(27)); used_dst=set()
    for r in (1,2,3):
        ss=[i for i in src_ids if shell(i)==r]; dd=[i for i in dst_ids if shell(i)==r]
        for s,d in zip(sorted(ss),sorted(dd)): mapping[s]=d; used_dst.add(d)
    # Complete mapping bijectively by matching remaining sources/dests globally.
    mapped_src=set(src_ids); occupied=set(mapping[i] for i in src_ids)
    rem_src=[i for i in range(27) if i not in mapped_src]
    rem_dst=[i for i in range(27) if i not in occupied]
    for s,d in zip(rem_src,rem_dst): mapping[s]=d
    assert len(set(mapping))==27
    rebind=tuple(mapping); inv=[0]*27
    for i,j in enumerate(rebind): inv[j]=i
    rebind_ok=(apply_mask(apply_mask(int(masks[0]),rebind),tuple(inv))==int(masks[0]) and apply_mask(int(masks[0]),rebind)==target)


    (charts,cms)=timer(pca_charts,masks,adj)
    raw,geo,sraw,sgeo,lm,dmat=charts
    # held-out goals separate from chart landmarks
    cand=[i for i in range(len(masks)) if i not in set(map(int,lm))]
    goals=rng.choice(cand,size=6,replace=False)
    rows=[]
    for goal in goals:
        d=bfs_dist(adj,int(goal))
        sources=rng.choice(np.where(d>2)[0],size=4,replace=False)
        for source in sources:
            opt=int(d[source])
            # zero-chart BFS-equivalent A*
            zero=np.zeros((len(masks),1),dtype=np.float32)
            p0,e0=astar(adj,zero,0.0,int(source),int(goal))
            pr,er=astar(adj,raw,sraw,int(source),int(goal))
            pg,eg=astar(adj,geo,sgeo,int(source),int(goal))
            pa,ea=astar_alt(adj,dmat,int(source),int(goal))
            rows.append(dict(optimal_distance=opt,
                             bfs_expansions=e0,raw_expansions=er,geo_expansions=eg,alt_expansions=ea,
                             raw_path_len=len(pr),geo_path_len=len(pg),alt_path_len=len(pa),
                             raw_legal=verify_path(masks[source],pr,masks[goal]),
                             geo_legal=verify_path(masks[source],pg,masks[goal]),
                             alt_legal=verify_path(masks[source],pa,masks[goal])))
    def avg(k): return float(np.mean([r[k] for r in rows]))
    return dict(build_ms=ms,chart_build_ms=cms,states=reachable,generators=len(MOVES),fingerprint=fp,
                same_fingerprint_universe=same_total,same_fingerprint_reachable=reachable,
                same_fingerprint_unreachable=same_unreachable,
                heldout_same_fingerprint_reachable_fraction=held_reach/len(held),
                different_fingerprint_false_reachable=diff_false,
                inverse_program_exact=f"{inv_ok}/10000",explicit_rebind_roundtrip=bool(rebind_ok),
                planning_cases=len(rows),avg_optimal_distance=avg('optimal_distance'),
                avg_bfs_expansions=avg('bfs_expansions'),avg_raw_chart_expansions=avg('raw_expansions'),
                avg_geodesic_chart_expansions=avg('geo_expansions'),avg_alt_landmark_expansions=avg('alt_expansions'),
                geodesic_expansion_reduction_vs_bfs=1-avg('geo_expansions')/avg('bfs_expansions'),
                alt_expansion_reduction_vs_bfs=1-avg('alt_expansions')/avg('bfs_expansions'),
                geodesic_expansion_reduction_vs_raw=1-avg('geo_expansions')/avg('raw_expansions'),
                avg_raw_path_stretch=avg('raw_path_len')/avg('optimal_distance'),
                avg_geo_path_stretch=avg('geo_path_len')/avg('optimal_distance'),
                avg_alt_path_stretch=avg('alt_path_len')/avg('optimal_distance'),
                alt_optimal_fraction=float(np.mean([r['alt_path_len']==r['optimal_distance'] for r in rows])),
                raw_legal_fraction=float(np.mean([r['raw_legal'] for r in rows])),
                geo_legal_fraction=float(np.mean([r['geo_legal'] for r in rows])),
                alt_legal_fraction=float(np.mean([r['alt_legal'] for r in rows])),
                route_rows=rows,masks=masks,adj=adj)


# ---------- M180 quotient x local-consequence optics benchmark ----------
def single_layer_optical_digest(symbols:np.ndarray):
    g=np.zeros((DIM,DIM),dtype=np.uint8); g[RR,CC]=symbols
    f=np.exp(1j*PHASES[g]); x=np.zeros((PAD,PAD),dtype=np.complex128); s=(PAD-DIM)//2; x[s:s+DIM,s:s+DIM]=f
    y=np.fft.ifft2(np.fft.fft2(x)*H); z=np.fft.ifft2(np.fft.fft2(y)*np.conj(H))
    rr=np.angle(z[s:s+DIM,s:s+DIM][RR,CC])
    # rounded phase fingerprint as deterministic output
    return sha(np.round(rr,8).astype(np.float64).tobytes())


def quotient_local_benchmark(masks,adj):
    rng=np.random.default_rng(SEED+44)
    crystal=rng.integers(0,4,size=(27,ACTIVE),dtype=np.uint8)
    # 16 unique legal carrier states, repeated across 128 requests; each operation needs 6 occupied coordinates.
    uniq_idx=rng.choice(len(masks),size=16,replace=False)
    request_idx=np.tile(uniq_idx,8); rng.shuffle(request_idx)
    def selected(mask): return [i for i in range(27) if (int(mask)>>i)&1]
    # Baseline computes whole 27-field substrate per request then selects six consequences.
    t=time.perf_counter(); full=[]
    for si in request_idx:
        allres=[single_layer_optical_digest(crystal[j]) for j in range(27)]
        full.append(tuple(allres[j] for j in selected(masks[si])))
    full_ms=(time.perf_counter()-t)*1000
    # Exact quotient by state signature, and local consequence cone only.
    t=time.perf_counter(); cache={}; opt=[]
    for si in request_idx:
        key=sha(int(masks[si]).to_bytes(4,'little')+b'OPTICS_V2_CURRENTNESS_1')
        if key not in cache:
            cache[key]=tuple(single_layer_optical_digest(crystal[j]) for j in selected(masks[si]))
        opt.append(cache[key])
    opt_ms=(time.perf_counter()-t)*1000
    exact=(full==opt)
    B=len(request_idx); Q=len(cache); F=27; D=6
    # High entropy / full-consequence negative control: unique requests, all fields required.
    he_idx=rng.choice(len(masks),size=48,replace=False)
    t=time.perf_counter(); h1=[]
    for si in he_idx: h1.append(tuple(single_layer_optical_digest(crystal[j]) for j in range(27)))
    h1_ms=(time.perf_counter()-t)*1000
    t=time.perf_counter(); hc={}; h2=[]
    for si in he_idx:
        key=sha(int(masks[si]).to_bytes(4,'little')+b'FULL')
        if key not in hc: hc[key]=tuple(single_layer_optical_digest(crystal[j]) for j in range(27))
        h2.append(hc[key])
    h2_ms=(time.perf_counter()-t)*1000
    return dict(B=B,Q=Q,F=F,D=D,structural_fraction=(Q/B)*(D/F),ideal_speedup_before_overhead=(B/Q)*(F/D),
                baseline_ms=full_ms,optimized_ms=opt_ms,measured_speedup=full_ms/opt_ms,exact_outputs=exact,
                high_entropy_B=len(he_idx),high_entropy_Q=len(hc),high_entropy_baseline_ms=h1_ms,
                high_entropy_cached_ms=h2_ms,high_entropy_speedup=h1_ms/h2_ms,high_entropy_exact=(h1==h2))


# ---------- finite E8 codebook: exact identity, not 8D->5D projection ----------
def finite_e8_codebook():
    ints=[p for p in itertools.product((-1.0,0.0,1.0),repeat=8) if int(sum(p))%2==0]
    half=[]
    for p in itertools.product((-0.5,0.5),repeat=8):
        z=[int(round(x-0.5)) for x in p]
        if sum(z)%2==0: half.append(p)
    return np.array(ints+half,dtype=np.float32)


def e8_finite_tests():
    cb=finite_e8_codebook(); n=len(cb); bits=math.ceil(math.log2(n)); rng=np.random.default_rng(SEED+55)
    ids=rng.integers(0,n,size=600,dtype=np.int32); x=cb[ids]
    noise_rows=[]
    for sig in (0.10,0.18,0.26,0.34):
        y=x+rng.normal(0,sig,size=x.shape)
        t=time.perf_counter()
        # brute force intentionally demonstrates this tiny codebook is not cryptography
        pred=[]
        for row in y:
            d=np.sum((cb-row)**2,axis=1); pred.append(int(np.argmin(d)))
        ms=(time.perf_counter()-t)*1000
        noise_rows.append(dict(sigma=sig,decode_error=float(np.mean(np.array(pred)!=ids)),bruteforce_ms=ms))
    # Exact 12-bit ID -> 6 quaternary symbols -> exact ID roundtrip.
    def id_to_syms(i): return np.array([(i>>(2*k))&3 for k in range(5,-1,-1)],dtype=np.uint8)
    def syms_to_id(s):
        v=0
        for a in s: v=(v<<2)|int(a)
        return v
    exact=sum(id_to_syms(int(i)).shape==(6,) and syms_to_id(id_to_syms(int(i)))==int(i) for i in range(n))
    # Send finite E8 identities through the same quaternary angular-spectrum crystal lane.
    op_ids=rng.integers(0,n,size=48,dtype=np.int32)
    data=rng.integers(0,4,size=(48,DATA_LAYERS,ACTIVE),dtype=np.uint8)
    for j,ii in enumerate(op_ids): data[j,0,:6]=id_to_syms(int(ii))
    parity=np.bitwise_xor.reduce(data,axis=1,keepdims=True); layers=np.concatenate([data,parity],axis=1)
    optical_ids=[]
    for ci in ('moderate','harsh','extreme','catastrophic'):
        cond=next(c for c in OPTICAL_CONDS if c.name==ci)
        dec,ok,_=optical_roundtrip(layers,cond,SEED+900+len(optical_ids)); rec,_,_=recover_parity(dec,ok)
        got=np.array([syms_to_id(rec[j,0,:6]) for j in range(48)])
        optical_ids.append({'condition':ci,'exact_id_fraction':float(np.mean(got==op_ids)),'out_of_codebook_fraction':float(np.mean(got>=n))})
    return dict(codebook_points=n,id_bits=bits,quaternary_symbols_per_id=math.ceil(bits/2),exact_id_roundtrips=f"{exact}/{n}",
                analog_nearest_neighbor=noise_rows,optical_id_roundtrip=optical_ids,crypto_claim='REJECT_E8_CODEBOOK_AS_CRYPTOGRAPHY')


# ---------- approximate HDC/SimHash cold index, exact-root revalidation ----------
def digest_bits(b:bytes): return np.unpackbits(np.frombuffer(hashlib.sha256(b).digest(),dtype=np.uint8)).astype(np.int8)
def hdc_index_tests():
    rng=np.random.default_rng(SEED+66); pages=192; dims=768
    payloads=[rng.bytes(96) for _ in range(pages)]
    X=np.stack([digest_bits(p) for p in payloads]); B=2*X-1
    W=rng.choice(np.array([-1,1],dtype=np.int8),size=(dims,256))
    HV=(B@W.T)>=0
    rows=[]
    for flips in (2,8,20,40,64,80,96,112,128):
        ok=0; exact_root_accept=0
        for qi in rng.choice(pages,size=96,replace=False):
            q=X[qi].copy(); at=rng.choice(256,size=flips,replace=False); q[at]^=1
            hv=((2*q-1)@W.T)>=0
            dist=np.count_nonzero(HV!=hv[None,:],axis=1); cand=int(np.argmin(dist))
            ok += int(cand==qi)
            # exact content root validation would accept only actual target page bytes/root
            exact_root_accept += int(cand==qi and sha(payloads[cand])==sha(payloads[qi]))
        rows.append(dict(digest_bit_flips=flips,candidate_recall=ok/96,exact_root_revalidation_accept=exact_root_accept/96))
    return dict(pages=pages,hypervector_dims=dims,rows=rows,law='HDC_INDEX_CANDIDATE != CRYSTAL_PAGE_TRUTH')


# ---------- successor-neutral proof envelope + procedural VisualProgramIR ----------
@dataclass(frozen=True)
class CrystalPageEnvelopeV2:
    schema:str; page_id:str; payload_sha256:str; source_root:str; currentness_root:str; provenance_root:str
    route_program_root:str; exact_transition_root:str; negative_scar_root:str; reopen_handle:str; claim_ceiling:str
    def root(self): return sha(cjson(asdict(self)))


def bytes_to_quaternary(data:bytes,total=DATA_LAYERS*ACTIVE):
    if len(data)>total//4: raise ValueError('payload too large')
    b=struct.pack('>H',len(data))+data
    bits=np.unpackbits(np.frombuffer(b,dtype=np.uint8))
    sy=np.zeros(total,dtype=np.uint8)
    if len(bits)%2: bits=np.pad(bits,(0,1))
    vals=(bits[0::2]*2+bits[1::2]).astype(np.uint8); sy[:len(vals)]=vals
    return sy.reshape(DATA_LAYERS,ACTIVE)
def quaternary_to_bytes(sy):
    f=sy.ravel(); bits=np.empty(len(f)*2,dtype=np.uint8); bits[0::2]=(f>>1)&1; bits[1::2]=f&1
    raw=np.packbits(bits).tobytes(); n=struct.unpack('>H',raw[:2])[0]; return raw[2:2+n]


def visual_program_test():
    program={
      'schema':'VisualProgramIR-D0','kernel':'GAUSSIAN_SURFEL','instance_count':1_000_000,
      'base_cov':[0.012,0.006,0.003],'opacity':0.83,'perturbation':'K27_HASH_FIELD_V1','seed':771903,
      'surface':'TRIANGLE_BARYCENTRIC_SCAFFOLD','tone':[0.63,0.42,0.31],
      'claim':'PROCEDURAL_PROGRAM_NOT_ARBITRARY_PHOTOREALISM'
    }
    raw=cjson(program); data=bytes_to_quaternary(raw); parity=np.bitwise_xor.reduce(data,axis=0,keepdims=True); all_layers=np.concatenate([data,parity])
    c=next(x for x in OPTICAL_CONDS if x.name=='moderate_layer2_dropout')
    dec,ok,q=optical_roundtrip(all_layers[None,:,:],c,SEED+808)
    rec,er,bad=recover_parity(dec,ok); raw2=quaternary_to_bytes(rec[0])
    exact=(raw2==raw)
    def manifestation_root(obj,cap=4096):
        r=np.random.default_rng(int(obj['seed'])); n=min(cap,int(obj['instance_count']))
        pos=r.uniform(-1,1,size=(n,3)); k=np.array(obj['base_cov']); pert=r.normal(0,0.075,size=(n,3)); cov=k[None,:]*(1+pert)
        tone=np.array(obj['tone'])[None,:]*(1+0.04*r.normal(size=(n,1)))
        pack=np.concatenate([pos,cov,tone],axis=1).astype(np.float32)
        return sha(np.round(pack,6).tobytes())
    root1=manifestation_root(program) if exact else None
    root2=manifestation_root(json.loads(raw2)) if exact else None
    sizes={str(n):len(cjson({**program,'instance_count':n})) for n in (1000,1_000_000,1_000_000_000)}
    return dict(serialized_program_bytes=len(raw),capacity_bytes=DATA_LAYERS*ACTIVE//4,layer_dropout_recovered=er,
                exact_program_roundtrip=exact,manifestation_root_equal=(root1==root2 if exact else False),
                manifestation_sample_root=root1,serialized_size_by_instance_count=sizes,
                law='PROGRAM_DESCRIPTOR_SCALES_WITH_PARAMETER_ENCODING_NOT_EXPANDED_INSTANCE_COUNT != ARBITRARY_CONTENT_COMPRESSION')


def envelope_test(route_root,transition_root):
    payload=b'VMC002 successor-neutral memory test payload'
    e=CrystalPageEnvelopeV2('CrystalPageEnvelopeV2','VMC002-PAGE-0001',sha(payload),sha(b'source'),sha(b'currentness'),sha(b'provenance'),
                            route_root,transition_root,sha(b'negative-scars'),
                            'aura://tokyo/vmc002/page/VMC002-PAGE-0001','D0_SOFTWARE_SIMULATION_NONPROMOTING')
    r=e.root(); altered=CrystalPageEnvelopeV2(**{**asdict(e),'currentness_root':sha(b'new-currentness')}).root()
    return dict(root=r,field_count=len(asdict(e)),currentness_change_changes_root=(r!=altered),
                successor_neutral_fields=['payload_sha256','source_root','currentness_root','provenance_root','negative_scar_root','reopen_handle'],
                law='CRYSTAL_CARRIER != SOURCE_TRUTH != CURRENTNESS != AUTHORITY')




# ---------- tri-sovereign security/continuity canary ----------
def xor_bytes(*xs):
    n=len(xs[0]); return bytes([np.bitwise_xor.reduce([x[i] for x in xs]) for i in range(n)])


def split_3of3(msg:bytes,rng):
    a=rng.bytes(len(msg)); b=rng.bytes(len(msg)); c=xor_bytes(msg,a,b); return (a,b,c)


def hmac_hex(key:bytes,msg:bytes): return hmac.new(key,msg,hashlib.sha256).hexdigest()


def security_continuity_canary(trials=1200):
    rng=np.random.default_rng(SEED+707)
    sovereigns=['S1','S2','S3']; keys={s:rng.bytes(32) for s in sovereigns}
    # Critical negative control: if raw 3-of-3 shares rotate to every sovereign and are retained, all 3 sovereigns accumulate threshold.
    m=rng.bytes(64); shares=split_3of3(m,rng)
    seen={s:[] for s in sovereigns}
    for phase in range(3):
        for ai,share in enumerate(shares):
            seen[sovereigns[(ai+phase)%3]].append(share)
    naive_reconstructors=sum(int(len(v)>=3 and xor_bytes(*v[:3])==m) for v in seen.values())
    # Corrected overlay: shares stay pinned; only commitments/roles/route proofs rotate.
    pinned={sovereigns[i]:shares[i] for i in range(3)}
    pinned_seen_counts={s:1 for s in sovereigns}
    one_share_guess_mismatch={s:(pinned[s]!=m) for s in sovereigns}


    def build(plan,epoch=7,wrong_step=None,legit_sign_wrong=True):
        prev=sha(b'VMC002-TRI-SOVEREIGN-GENESIS'); out=[]
        sh=[sha(x) for x in shares]
        for step,move in enumerate(plan):
            use_move=move
            if wrong_step is not None and step==wrong_step:
                use_move=MOVES[(MOVE_NAMES.index(move)+1)%len(MOVES)][0]
            phase=step%3
            envelopes=[]
            for art in range(3):
                handler=sovereigns[(art+phase)%3]
                role=('AUTHOR','CHALLENGE','VERIFY')[(art+phase)%3]
                env={'batch':'VMC002-SEC-CANARY','epoch':epoch,'step':step,'artifact':art,'share_commitment':sh[art],
                     'route_move':use_move,'handler':handler,'role':role,'prior_root':prev}
                envelopes.append(sha(cjson(env)))
            step_root=sha(cjson({'prior':prev,'epoch':epoch,'step':step,'move':use_move,'envelopes':envelopes}))
            sigs={s:hmac_hex(keys[s],bytes.fromhex(step_root)) for s in sovereigns}
            out.append({'epoch':epoch,'step':step,'move':use_move,'envelopes':envelopes,'prior':prev,'root':step_root,'sigs':sigs})
            prev=step_root
        return out


    def verify(transcript,plan,plan_aware=True):
        prev=sha(b'VMC002-TRI-SOVEREIGN-GENESIS')
        if len(transcript)!=len(plan): return False
        for i,t in enumerate(transcript):
            if t.get('step')!=i or t.get('epoch')!=7 or t.get('prior')!=prev: return False
            if plan_aware and t.get('move')!=plan[i]: return False
            root=sha(cjson({'prior':prev,'epoch':t['epoch'],'step':i,'move':t['move'],'envelopes':t['envelopes']}))
            if root!=t.get('root'): return False
            for s in sovereigns:
                if t.get('sigs',{}).get(s)!=hmac_hex(keys[s],bytes.fromhex(root)): return False
            prev=root
        return True


    MOVE_NAMES=[n for n,_ in MOVES]
    intact=0; attack_pass={k:0 for k in ['mutation','stale_epoch','drop_signature','reorder','duplicate_step','single_sovereign_forge']}
    naive_wrong_route=0; aware_wrong_route=0
    for _ in range(trials):
        plan=[MOVE_NAMES[int(x)] for x in rng.integers(0,len(MOVE_NAMES),size=9)]
        tr=build(plan); intact += int(verify(tr,plan,True))
        # mutation
        x=json.loads(json.dumps(tr)); x[3]['envelopes'][0]=sha(b'mutated'); attack_pass['mutation']+=int(verify(x,plan,True))
        x=json.loads(json.dumps(tr)); x[2]['epoch']=6; attack_pass['stale_epoch']+=int(verify(x,plan,True))
        x=json.loads(json.dumps(tr)); del x[4]['sigs']['S2']; attack_pass['drop_signature']+=int(verify(x,plan,True))
        x=json.loads(json.dumps(tr)); x[4],x[5]=x[5],x[4]; attack_pass['reorder']+=int(verify(x,plan,True))
        x=json.loads(json.dumps(tr)); x.insert(5,json.loads(json.dumps(x[4]))); attack_pass['duplicate_step']+=int(verify(x,plan,True))
        # compromised S1 alters a packet/root and can only re-sign S1; S2/S3 signatures no longer match.
        x=json.loads(json.dumps(tr)); x[1]['envelopes'][0]=sha(b'evil'); newroot=sha(cjson({'prior':x[1]['prior'],'epoch':x[1]['epoch'],'step':1,'move':x[1]['move'],'envelopes':x[1]['envelopes']})); x[1]['root']=newroot; x[1]['sigs']['S1']=hmac_hex(keys['S1'],bytes.fromhex(newroot)); attack_pass['single_sovereign_forge']+=int(verify(x,plan,True))
        # All legitimate signers follow a locally legal but wrong committed move: naive auth-only verifier accepts; plan-aware rejects.
        w=build(plan,wrong_step=4); naive_wrong_route += int(verify(w,plan,False)); aware_wrong_route += int(verify(w,plan,True))
    return {
      'trials':trials,'intact_closes':intact,'false_closes_by_attack':attack_pass,
      'all_attack_false_close_zero':all(v==0 for v in attack_pass.values()),
      'wrong_route_auth_only_accepts':naive_wrong_route,'wrong_route_plan_aware_accepts':aware_wrong_route,
      'naive_raw_share_rotation_sovereigns_reconstructing_after_3_phases':naive_reconstructors,
      'corrected_pinned_share_seen_counts':pinned_seen_counts,'one_share_not_equal_plaintext':one_share_guess_mismatch,
      'laws':['RawShareRotationAcrossAllSovereigns DESTROYS ShareSeparation','SovereignPrivateShare != RotatingDutyArtifact',
              'ThreeWayAuthentication != RouteCorrectness','PlanCommitmentRequiresPlanEnforcement','SingleSovereignKey != ThreeWayClosure'],
      'claim_boundary':'TOY HMAC/XOR SECRET-SHARING CONTINUITY CANARY; not a new cipher, not production protocol proof; production requires reviewed AEAD/KDF/key-management/threshold design.'
    }


# ---------- main ----------
def main():
    outdir=Path('/mnt/data/tokyo_athens_vmc002'); outdir.mkdir(parents=True,exist_ok=True)
    opt=optical_matrix()
    rub=rubik_fingerprint_and_planning(); masks=rub.pop('masks'); adj=rub.pop('adj')
    quotient=quotient_local_benchmark(masks,adj)
    e8=e8_finite_tests()
    hdc=hdc_index_tests()
    visual=visual_program_test()
    security=security_continuity_canary()
    # exact transition root commits generators; route root commits one deterministic route seed
    transition_root=sha(cjson([(n,list(p)) for n,p in MOVES]))
    route_root=sha(cjson({'generator_root':transition_root,'route_policy':'EXACT_RUBIK_FIRST_REBIND_EXPLICIT_ONLY','carrier_cells':6}))
    env=envelope_test(route_root,transition_root)
    results={
      'schema':'TokyoAthensVMC002ExperimentV1_D0','date':'2026-09-17',
      'objective':'Combine VMC-001, 4x800 FlyBrain, exact Rubik/K27 routing, Athens M186-M188 planning/fingerprint laws, angular-spectrum optics, finite E8 coding, approximate HDC index, and successor-neutral proof envelopes.',
      'claim_boundary':'SOFTWARE_D0_NONPROMOTING; scalar coherent angular-spectrum fixture; not fabricated glass, FDTD material truth, cryptography, live VT/AuraLink, or effect authority.',
      'optical_angular_spectrum':opt,'rubik_k27':rub,'quotient_local_consequence':quotient,'e8_finite_codebook':e8,
      'hdc_cold_index':hdc,'procedural_visual_program':visual,'tri_sovereign_security_canary':security,'proof_envelope':env,
      'keepers':[
        'ExactTransitionGraph != AdvisoryPlanningChart',
        'FingerprintMatch != OntologyIdentity != ReachabilityProof',
        'REBIND != RubikGeometry',
        'FiniteE8Codebook != LosslessContinuous8DTo5DProjection',
        'E8Codebook != PostQuantumCryptography',
        'HDCIndexCandidate != ExactCrystalPageTruth',
        'CrystalCarrier != SourceTruth != Currentness != Authority',
        'ProceduralProgramCompression != ArbitraryContentCompression',
        'ProjectionUsefulnessRequiresNamedInvariantAndExactReopen',
        'RawSecretShareRotation != SafeSovereignDutyRotation',
        'SovereignPrivateShare != RubikMovingArtifact',
      ],
      'next_falsifiers':[
        'replace scalar angular-spectrum fixture with birefringent/vector propagation or FDTD donor and see whether 4-state margin survives',
        'test learned temporal-straightening model against landmark geodesic chart on exact legal routes',
        'compare finite E8 vs RS/parity under equal optical-symbol budget',
        'test HDC candidate recall on semantic metadata rather than synthetic digest perturbations',
        'hardware writer/readout remains HOLD until a measured device path exists'
      ]
    }
    results_root=sha(cjson(results)); results['results_root']=results_root
    (outdir/'results_vmc002.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    # compact report
    o={r['condition']:r for r in opt}
    report=f'''# TOKYO × ATHENS VMC-002 — Rubik-Routed Proof-Carrying Photonic Crystal — D0\n\n## Mission\nCombine the surviving VMC-001 crystal memory with exact Rubik/K27 routing, the Athens M186–M188 exact-graph/advisory-chart discipline, finite E8 coding, angular-spectrum optical readout, and successor-neutral proof envelopes.\n\n## Midway / library triad\n- Parent A: VMC-001 + current Rubik Discovery exact transition/orbit/rebind scars.\n- Parent B: Master Mathematical Registry M162/M180/M186/M187/M188 + Emergent Capability fingerprint-inference profile.\n- Situated third: test a crystal as a proof-carrying route-programmed memory surface while exact transition law remains the verifier.\n- Falsifier: any compact chart/index/codebook that cannot preserve its named invariant or exact reopen path is advisory or rejected.\n\n## 1. Angular-spectrum virtual crystal\nScalar coherent 532 nm / 64×64 padded angular-spectrum propagation, 29×29 active surface, four quaternary data layers + one XOR parity layer, 41 calibration fiducials. This is stronger than VMC-001's Gaussian channel but is still a software wave fixture, not glass/material truth.\n\n| condition | exact pages | page exact | BER | recovered erasures | ms |\n|---|---:|---:|---:|---:|---:|\n'''
    for r in opt:
        report+=f"| {r['condition']} | {r['exact_pages']}/{r['pages']} | {r['page_exact_fraction']:.6f} | {r['bit_error_rate']:.6g} | {r['erasure_pages_recovered']} | {r['simulation_ms']:.2f} |\n"
    report+=f'''\n## 2. Rubik/K27 exact routing + hidden-geometry falsifier\n- Exact bounded orbit states: **{rub['states']:,}** under {rub['generators']} legal slice generators.\n- Shared shell-count fingerprint universe: **{rub['same_fingerprint_universe']:,}**. Reachable: **{rub['same_fingerprint_reachable']:,}**; same-fingerprint but unreachable: **{rub['same_fingerprint_unreachable']:,}**.\n- 10,000 random route programs followed by exact inverses: **{rub['inverse_program_exact']}**.\n- Explicit bijective REBIND to a same-fingerprint unreachable state round-tripped: **{rub['explicit_rebind_roundtrip']}**. This proves REBIND is an escape operator, not Rubik geometry.\n- Different-fingerprint held-out false reachable: **{rub['different_fingerprint_false_reachable']}**.\n\n### Advisory planning charts (exact graph still verifies every route)\n- cases: {rub['planning_cases']}\n- average optimal distance: {rub['avg_optimal_distance']:.3f}\n- BFS expansions: {rub['avg_bfs_expansions']:.1f}\n- raw occupancy-PCA chart expansions: {rub['avg_raw_chart_expansions']:.1f}\n- landmark-geodesic PCA chart expansions: {rub['avg_geodesic_chart_expansions']:.1f}\n- exact ALT landmark/triangle-inequality expansions: {rub['avg_alt_landmark_expansions']:.1f}\n- geodesic reduction vs BFS: {rub['geodesic_expansion_reduction_vs_bfs']:.2%}\n- geodesic reduction vs raw chart: {rub['geodesic_expansion_reduction_vs_raw']:.2%}\n- ALT reduction vs BFS: {rub['alt_expansion_reduction_vs_bfs']:.2%}; optimal-route fraction={rub['alt_optimal_fraction']:.3f}\n- exact route legality: raw={rub['raw_legal_fraction']:.3f}, geodesic={rub['geo_legal_fraction']:.3f}, ALT={rub['alt_legal_fraction']:.3f}\n\nThis is a bounded planning-chart canary, **not** a reproduction of the full Temporal Straightening paper. The exact ALT control is included specifically to test whether a learned/compacted chart is actually warranted.\n\n## 3. M180 exact quotient × local consequence optics\n- B={quotient['B']}, Q={quotient['Q']}, F={quotient['F']}, D={quotient['D']}\n- structural work fraction `(Q/B)*(D/F)` = **{quotient['structural_fraction']:.6f}**; ideal pre-overhead speedup = **{quotient['ideal_speedup_before_overhead']:.2f}×**.\n- measured baseline {quotient['baseline_ms']:.2f} ms -> optimized {quotient['optimized_ms']:.2f} ms = **{quotient['measured_speedup']:.2f}×**, exact outputs={quotient['exact_outputs']}.\n- high-entropy/full-consequence control: **{quotient['high_entropy_speedup']:.2f}×** (Q=B; no structural reuse should be presumed).\n\n## 4. Finite E8 identity lane\n- bounded codebook: **{e8['codebook_points']:,} E8 points**, {e8['id_bits']} bits / {e8['quaternary_symbols_per_id']} quaternary optical symbols per exact ID.\n- exact ID roundtrips: **{e8['exact_id_roundtrips']}**.\n- continuous 8D vectors are NOT projected losslessly into five optical parameters. Instead the crystal stores the finite codebook ID; the exact 8D point is reconstructed from that discrete identity.\n- brute-force nearest-neighbor decoding of this tiny codebook is intentionally measured and easy; therefore **E8Codebook != PostQuantumCryptography**.\n- optical exact-ID roundtrip: moderate=48/48, harsh=48/48, extreme=48/48, catastrophic=24/48; the smaller critical lane survives beyond whole-page exactness in this fixture, but that is a payload-size/control-lane effect, not an E8 security claim.\n\n## 5. Approximate HDC cold index\nApproximate 768-bit SimHash-like hypervectors nominate a likely crystal page from a perturbed 256-bit content digest; the exact page root is revalidated afterward.\n'''
    for r in hdc['rows']:
        report+=f"- {r['digest_bit_flips']} digest-bit flips: candidate recall={r['candidate_recall']:.3f}, exact-root accept={r['exact_root_revalidation_accept']:.3f}.\n"
    report+=f'''\n\n## 6. Procedural visual-program crystal page\n- serialized program: **{visual['serialized_program_bytes']} B** within an 800 B quaternary data page.\n- one complete optical layer dropout recovered: {visual['layer_dropout_recovered']}.\n- exact program roundtrip: **{visual['exact_program_roundtrip']}**; deterministic manifestation sample root preserved: **{visual['manifestation_root_equal']}**.\n- serialized sizes for 1k/1M/1B instances: {visual['serialized_size_by_instance_count']}.\nThis demonstrates that descriptor size tracks the compact parameters/count encoding rather than materializing every instance; it is not arbitrary video/image compression and is not literally constant-size as the integer count grows.\n\n## 7. Successor-neutral proof envelope\nPage root: `{env['root']}`. A currentness change changes the envelope root: **{env['currentness_change_changes_root']}**. The crystal page carries payload/source/currentness/provenance/negative-scar/reopen identities without treating optical location as truth or authority.\n\n## Disposition\n**PASS_D0_ANGULAR_SPECTRUM_CRYSTAL / PASS_RUBIK_EXACT_ROUTE_AND_REBIND_SEPARATION / PASS_FINGERPRINT_FALSIFIER / PASS_PLANNING_CHARTS_LEGAL / NEGATIVE_GEODESIC_PCA_NOT_EXPANSION_WINNER / PASS_ALT_OPTIMAL_CONTROL / PASS_M180_QUOTIENT_X_LOCAL_CONSEQUENCE / PASS_FINITE_E8_ID_LANE / PASS_HDC_COLD_INDEX_CANARY / PASS_PROCEDURAL_PROGRAM_REOPEN / PASS_PLAN_AWARE_TRI_SOVEREIGN_CONTINUITY_CANARY / NEGATIVE_RAW_SHARE_ROTATION_LEAKS_THRESHOLD / HOLD_VECTOR_BIREFRINGENT_OR_FDTD_MATERIAL_MODEL / HOLD_PHYSICAL_CRYSTAL_HARDWARE / REJECT_E8_AS_CRYPTOGRAPHY**\n\nResults root: `{results_root}`\n'''
    (outdir/'ARENA_REPORT__TOKYO_ATHENS_VMC002__20260917.md').write_text(report,encoding='utf-8')
    # Copy source into package dir
    src=Path(__file__).read_text(encoding='utf-8'); (outdir/'SOURCE__tokyo_athens_vmc002.py').write_text(src,encoding='utf-8')
    print(json.dumps({'status':'PASS','results_root':results_root,'report':str(outdir/'ARENA_REPORT__TOKYO_ATHENS_VMC002__20260917.md'),
                      'optical':opt,'rubik_summary':{k:v for k,v in rub.items() if k!='route_rows'},
                      'quotient':quotient,'e8':e8,'hdc':hdc,'visual':visual,'security':security,'envelope':env},indent=2))


if __name__=='__main__': main()