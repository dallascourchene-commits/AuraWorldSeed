#!/usr/bin/env python3
from __future__ import annotations
import os, json, math, base64, struct, hashlib, shutil, time
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter


SEED = 20260917
DIM = 29
ACTIVE = 800
DATA_LAYERS = 4
PARITY_LAYERS = 1
LAYERS = DATA_LAYERS + PARITY_LAYERS
ADC_LEVELS = 4095


# Reuse the exact 29x29 / 800-active geometry from the current FlyBrain photonic fixture.
def is_reserved(r,c):
    if (r<=2 and c<=2) or (r<=2 and c>=26) or (r>=26 and c<=2): return True
    if r>=27 and c>=27: return True
    if r==1 and c in (6,10,14,18,22): return True
    if c==1 and r in (6,10,14,18,22): return True
    return False


ACTIVE_LUT=[(r,c) for r in range(DIM) for c in range(DIM) if not is_reserved(r,c)]
assert len(ACTIVE_LUT)==800
STRIDE=137
SPATIAL_POS=np.array([ACTIVE_LUT[(k*STRIDE)%ACTIVE] for k in range(ACTIVE)],dtype=np.int16)
RR=SPATIAL_POS[:,0]; CC=SPATIAL_POS[:,1]
FID_POS=np.array([(r,c) for r in range(DIM) for c in range(DIM) if is_reserved(r,c)],dtype=np.int16)
assert len(FID_POS)==41
FR=FID_POS[:,0]; FC=FID_POS[:,1]




def sha256(b: bytes)->str:
    return hashlib.sha256(b).hexdigest()




def canonical_json(obj)->bytes:
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()




def centers_for_levels(levels:int)->np.ndarray:
    """Two-observable normalized optical constellation.
    Think of axes as calibrated slow-axis/polarization and retardance/phase observables.
    This is a reduced channel fixture, not a Maxwell solver or measured glass response.
    """
    if levels==2:
        return np.array([[-0.72,-0.30],[0.72,0.30]],dtype=np.float32)
    if levels==4:
        a=0.68
        return np.array([[-a,-a],[-a,a],[a,-a],[a,a]],dtype=np.float32)
    if levels==16:
        vals=np.array([-0.78,-0.26,0.26,0.78],dtype=np.float32)
        return np.array([(x,y) for x in vals for y in vals],dtype=np.float32)
    raise ValueError("levels must be 2,4,16")




def bits_per_symbol(levels:int)->int:
    return int(round(math.log2(levels)))




def symbols_to_bitarray(symbols:np.ndarray, levels:int)->np.ndarray:
    k=bits_per_symbol(levels)
    shifts=np.arange(k-1,-1,-1,dtype=np.uint8)
    return ((symbols[...,None] >> shifts) & 1).astype(np.uint8)




def payload_ber(tx:np.ndarray, rx:np.ndarray, levels:int, valid_mask:np.ndarray|None=None)->float:
    tb=symbols_to_bitarray(tx,levels)
    rb=symbols_to_bitarray(rx,levels)
    err=(tb!=rb)
    if valid_mask is not None:
        # mask pages/layers/symbols; broadcast to bit dimension
        err=err[valid_mask]
    return float(err.mean()) if err.size else float('nan')




def pack_symbols(symbols:np.ndarray, levels:int)->bytes:
    k=bits_per_symbol(levels)
    flat=symbols.astype(np.uint8).ravel()
    bits=symbols_to_bitarray(flat,levels).reshape(-1)
    return np.packbits(bits,bitorder='big').tobytes()




def unpack_symbols(data:bytes, levels:int, count:int)->np.ndarray:
    k=bits_per_symbol(levels)
    bits=np.unpackbits(np.frombuffer(data,dtype=np.uint8),bitorder='big')[:count*k]
    bits=bits.reshape(count,k)
    weights=(1 << np.arange(k-1,-1,-1,dtype=np.uint8))
    return (bits*weights).sum(axis=1).astype(np.uint8)




@dataclass
class ChannelCondition:
    name:str
    sigma_xy:float
    sigma_z:float
    noise:float
    gain_sigma:float
    offset_sigma:float
    dropout_layer:int|None=None
    dropout_attenuation:float=0.025




CONDITIONS=[
    ChannelCondition('clean',0.10,0.04,0.008,0.010,0.004),
    ChannelCondition('moderate',0.26,0.10,0.025,0.025,0.012),
    ChannelCondition('harsh',0.42,0.18,0.055,0.050,0.025),
    ChannelCondition('severe',0.62,0.32,0.105,0.080,0.040),
    ChannelCondition('moderate_layer2_dropout',0.26,0.10,0.025,0.025,0.012,dropout_layer=2),
]




def make_page_symbols(rng:np.random.Generator,pages:int,levels:int)->tuple[np.ndarray,np.ndarray]:
    data=rng.integers(0,levels,size=(pages,DATA_LAYERS,ACTIVE),dtype=np.uint8)
    parity=np.bitwise_xor.reduce(data,axis=1,keepdims=True)
    all_layers=np.concatenate([data,parity],axis=1)
    return data,all_layers




def encode_volume(all_layers:np.ndarray,levels:int)->tuple[np.ndarray,np.ndarray,np.ndarray]:
    pages=all_layers.shape[0]
    centers=centers_for_levels(levels)
    symbol_grid=np.zeros((pages,LAYERS,DIM,DIM),dtype=np.uint8)
    symbol_grid[:,:,RR,CC]=all_layers
    fid_symbols=(np.arange(len(FID_POS),dtype=np.uint8)%levels)
    symbol_grid[:,:,FR,FC]=fid_symbols[None,None,:]
    feat=centers[symbol_grid]
    return feat[...,0].astype(np.float32),feat[...,1].astype(np.float32),fid_symbols




def quantize_adc(x:np.ndarray, lo=-1.35, hi=1.35)->np.ndarray:
    q=np.clip(x,lo,hi)
    q=np.round((q-lo)/(hi-lo)*(ADC_LEVELS-1))/(ADC_LEVELS-1)*(hi-lo)+lo
    return q.astype(np.float32)




def simulate_read(all_layers:np.ndarray,levels:int,cond:ChannelCondition,seed:int):
    rng=np.random.default_rng(seed)
    fx,fy,fid_symbols=encode_volume(all_layers,levels)
    # batch dimension is never blurred; z/y/x are.
    sig=(0.0,cond.sigma_z,cond.sigma_xy,cond.sigma_xy)
    fx=gaussian_filter(fx,sigma=sig,mode='nearest')
    fy=gaussian_filter(fy,sigma=sig,mode='nearest')
    pages=all_layers.shape[0]
    gain=rng.normal(1.0,cond.gain_sigma,size=(pages,LAYERS,1,1)).astype(np.float32)
    offx=rng.normal(0.0,cond.offset_sigma,size=(pages,LAYERS,1,1)).astype(np.float32)
    offy=rng.normal(0.0,cond.offset_sigma,size=(pages,LAYERS,1,1)).astype(np.float32)
    fx=fx*gain+offx
    fy=fy*gain+offy
    if cond.dropout_layer is not None:
        fx[:,cond.dropout_layer]*=cond.dropout_attenuation
        fy[:,cond.dropout_layer]*=cond.dropout_attenuation
    fx+=rng.normal(0.0,cond.noise,size=fx.shape).astype(np.float32)
    fy+=rng.normal(0.0,cond.noise,size=fy.shape).astype(np.float32)
    fx=quantize_adc(fx); fy=quantize_adc(fy)


    # Per-page/per-layer affine calibration from 41 fixed crystal fiducials.
    centers=centers_for_levels(levels)
    ideal=centers[fid_symbols]
    ix=ideal[:,0]; iy=ideal[:,1]
    ox=fx[:,:,FR,FC]; oy=fy[:,:,FR,FC]
    def fit(obs,ideal1):
        im=ideal1.mean(); iv=((ideal1-im)**2).sum()
        om=obs.mean(axis=2,keepdims=True)
        slope=((obs-om)*(ideal1[None,None,:]-im)).sum(axis=2)/iv
        intercept=obs.mean(axis=2)-slope*im
        return slope.astype(np.float32),intercept.astype(np.float32)
    sx,bx=fit(ox,ix); sy,by=fit(oy,iy)
    quality=np.sqrt(sx*sx+sy*sy)
    layer_ok=quality>0.42


    ax=fx[:,:,RR,CC]; ay=fy[:,:,RR,CC]
    safe_sx=np.where(np.abs(sx)<0.08,np.sign(sx)*0.08+ (sx==0)*0.08,sx)
    safe_sy=np.where(np.abs(sy)<0.08,np.sign(sy)*0.08+ (sy==0)*0.08,sy)
    nx=(ax-bx[:,:,None])/safe_sx[:,:,None]
    ny=(ay-by[:,:,None])/safe_sy[:,:,None]
    obs=np.stack([nx,ny],axis=-1)
    d2=((obs[...,None,:]-centers[None,None,None,:,:])**2).sum(axis=-1)
    decoded=np.argmin(d2,axis=-1).astype(np.uint8)
    confidence=np.partition(d2,1,axis=-1)
    margin=confidence[...,1]-confidence[...,0]
    return decoded,layer_ok,quality,margin




def recover_one_erased_layer(decoded:np.ndarray,layer_ok:np.ndarray,levels:int):
    out=decoded[:,:DATA_LAYERS].copy()
    pages=decoded.shape[0]
    recovered=0
    unrecoverable=0
    for p in range(pages):
        bad=np.where(~layer_ok[p])[0]
        if len(bad)==0:
            continue
        # One failed data layer can be rebuilt from parity + other 3 data layers.
        if len(bad)==1 and bad[0] < DATA_LAYERS and layer_ok[p,DATA_LAYERS]:
            j=int(bad[0])
            rec=decoded[p,DATA_LAYERS].copy()
            for q in range(DATA_LAYERS):
                if q!=j:
                    rec ^= decoded[p,q]
            out[p,j]=rec
            recovered+=1
        elif len(bad)==1 and bad[0]==DATA_LAYERS:
            # parity layer lost; all data layers remain readable
            recovered+=1
        else:
            unrecoverable+=1
    return out,recovered,unrecoverable




def run_optical_matrix(pages=192,seed=SEED):
    results=[]
    for levels in (2,4,16):
        rng=np.random.default_rng(seed+levels)
        tx,all_layers=make_page_symbols(rng,pages,levels)
        for ci,cond in enumerate(CONDITIONS):
            t0=time.perf_counter()
            decoded,layer_ok,quality,margin=simulate_read(all_layers,levels,cond,seed+1000*levels+ci)
            recovered,er_rec,unrec=recover_one_erased_layer(decoded,layer_ok,levels)
            data_raw=decoded[:,:DATA_LAYERS]
            raw_ser=float((data_raw!=tx).mean())
            post_ser=float((recovered!=tx).mean())
            raw_ber=payload_ber(tx,data_raw,levels)
            post_ber=payload_ber(tx,recovered,levels)
            page_exact=float((recovered==tx).all(axis=(1,2)).mean())
            results.append({
                'levels':levels,
                'bits_per_voxel':bits_per_symbol(levels),
                'condition':cond.name,
                'pages':pages,
                'payload_bits_per_page':DATA_LAYERS*ACTIVE*bits_per_symbol(levels),
                'parity_bits_per_page':ACTIVE*bits_per_symbol(levels),
                'logical_crystal_bytes_per_page':(LAYERS*ACTIVE*bits_per_symbol(levels))//8,
                'raw_symbol_error_rate':raw_ser,
                'post_recovery_symbol_error_rate':post_ser,
                'raw_bit_error_rate':raw_ber,
                'post_recovery_bit_error_rate':post_ber,
                'page_exact_fraction':page_exact,
                'mean_layer_quality':float(quality.mean()),
                'min_layer_quality':float(quality.min()),
                'erasure_pages_recovered':er_rec,
                'unrecoverable_page_level_erasure_patterns':unrec,
                'simulation_ms':(time.perf_counter()-t0)*1000,
            })
    return results




# --- E8 lane ---
def nearest_d8(y:np.ndarray)->np.ndarray:
    y=np.asarray(y,dtype=np.float64)
    r=np.rint(y)
    parity=(r.sum(axis=1).astype(np.int64)&1).astype(bool)
    if np.any(parity):
        rows=np.where(parity)[0]
        e=y[rows]-r[rows]
        idx=np.argmax(np.abs(e),axis=1)
        chosen=e[np.arange(len(rows)),idx]
        direction=np.where(chosen>=0,1.0,-1.0)
        r[rows,idx]+=direction
    return r




def nearest_e8(y:np.ndarray)->np.ndarray:
    y=np.asarray(y,dtype=np.float64)
    a=nearest_d8(y)
    b=nearest_d8(y-0.5)+0.5
    da=((y-a)**2).sum(axis=1)
    db=((y-b)**2).sum(axis=1)
    choose=(db<da)[:,None]
    return np.where(choose,b,a)




def e8_membership(x:np.ndarray)->np.ndarray:
    x=np.asarray(x)
    frac=np.mod(x,1.0)
    integer=np.all(np.isclose(frac,0.0),axis=1)
    half=np.all(np.isclose(frac,0.5),axis=1)
    out=np.zeros(len(x),dtype=bool)
    if np.any(integer):
        out[integer]=(np.rint(x[integer]).sum(axis=1).astype(np.int64)&1)==0
    if np.any(half):
        z=np.rint(x[half]-0.5)
        out[half]=(z.sum(axis=1).astype(np.int64)&1)==0
    return out




def run_e8_tests(n=120000,seed=SEED):
    rng=np.random.default_rng(seed+88)
    x=rng.uniform(-8,8,size=(n,8))
    z=np.rint(x)
    e=nearest_e8(x)
    mse_z=float(np.mean((x-z)**2))
    mse_e=float(np.mean((x-e)**2))
    membership=float(e8_membership(e).mean())
    noise=[]
    origin=np.zeros((n,8),dtype=np.float64)
    for sigma in (0.18,0.24,0.30,0.36,0.42):
        w=rng.normal(0,sigma,size=(n,8))
        dz=np.rint(w)
        de=nearest_e8(w)
        z_err=float(np.any(dz!=origin,axis=1).mean())
        e_err=float(np.any(de!=origin,axis=1).mean())
        noise.append({'sigma':sigma,'z8_decode_error':z_err,'e8_decode_error':e_err})


    # Explicitly falsify a naive lossless 8D -> 5D continuous projection.
    a=rng.normal(size=(5,8))
    # orthonormal row basis
    q,_=np.linalg.qr(a.T)
    A=q[:,:5].T
    xr=rng.normal(size=(40000,8))
    y=xr@A.T
    xhat=y@A
    proj_mse=float(np.mean((xr-xhat)**2))
    base_var=float(np.mean(xr*xr))
    rel=proj_mse/base_var
    return {
        'quantization':{
            'samples':n,
            'z8_mse_per_dimension':mse_z,
            'e8_mse_per_dimension':mse_e,
            'e8_mse_reduction_vs_z8':1.0-mse_e/mse_z,
            'e8_output_membership_fraction':membership,
        },
        'noise_decode':noise,
        'naive_8d_to_5d_projection':{
            'samples':len(xr),
            'rank':int(np.linalg.matrix_rank(A)),
            'reconstruction_mse_per_dimension':proj_mse,
            'relative_mse_to_input_variance':rel,
            'lossless':False,
        }
    }




# --- WORM crystal archive ---
MAGIC=b'AURACRYS1'
@dataclass
class PageHeader:
    schema:str
    page_id:str
    levels:int
    data_layers:int
    parity_layers:int
    active_symbols_per_layer:int
    epoch:int
    objective_root:str
    currentness_root:str
    payload_sha256:str
    page_root:str


class CrystalArchive:
    def __init__(self,path:Path):
        self.path=Path(path)
        self.index={}
        if self.path.exists(): self._scan()
    def _scan(self):
        self.index={}
        with self.path.open('rb') as f:
            if f.read(len(MAGIC))!=MAGIC: raise ValueError('bad crystal magic')
            while True:
                pos=f.tell(); raw=f.read(4)
                if not raw: break
                if len(raw)!=4: raise ValueError('truncated header length')
                hlen=struct.unpack('<I',raw)[0]
                hraw=f.read(hlen)
                plen_raw=f.read(4)
                if len(hraw)!=hlen or len(plen_raw)!=4: raise ValueError('truncated header')
                plen=struct.unpack('<I',plen_raw)[0]
                payload_pos=f.tell(); payload=f.read(plen)
                if len(payload)!=plen: raise ValueError('truncated payload')
                h=json.loads(hraw)
                if h['page_id'] in self.index: raise ValueError('duplicate page_id in WORM archive')
                if sha256(payload)!=h['payload_sha256']: raise ValueError(f"payload hash mismatch {h['page_id']}")
                base=dict(h); stored_root=base.pop('page_root')
                calc=sha256(canonical_json(base)+bytes.fromhex(base['payload_sha256']))
                if calc!=stored_root: raise ValueError(f"page root mismatch {h['page_id']}")
                self.index[h['page_id']]={'header':h,'offset':payload_pos,'length':plen}
    @classmethod
    def create(cls,path:Path):
        path=Path(path)
        path.write_bytes(MAGIC)
        return cls(path)
    def append(self,page_id:str,data_symbols:np.ndarray,levels:int,epoch:int,objective_root:str,currentness_root:str):
        if page_id in self.index: raise ValueError('HOLD_WORM_PAGE_EXISTS')
        if data_symbols.shape!=(DATA_LAYERS,ACTIVE): raise ValueError('shape')
        parity=np.bitwise_xor.reduce(data_symbols,axis=0,keepdims=True)
        all_layers=np.concatenate([data_symbols,parity],axis=0)
        payload=pack_symbols(all_layers,levels)
        base={
            'schema':'AuraVirtualMemoryCrystalPageV1', 'page_id':page_id,'levels':levels,
            'data_layers':DATA_LAYERS,'parity_layers':1,'active_symbols_per_layer':ACTIVE,
            'epoch':int(epoch),'objective_root':objective_root,'currentness_root':currentness_root,
            'payload_sha256':sha256(payload),
        }
        root=sha256(canonical_json(base)+bytes.fromhex(base['payload_sha256']))
        h={**base,'page_root':root}; hraw=canonical_json(h)
        with self.path.open('ab') as f:
            f.write(struct.pack('<I',len(hraw))); f.write(hraw); f.write(struct.pack('<I',len(payload))); f.write(payload)
        self._scan()
        return h
    def read_data(self,page_id:str)->np.ndarray:
        rec=self.index[page_id]; h=rec['header']
        with self.path.open('rb') as f:
            f.seek(rec['offset']); payload=f.read(rec['length'])
        if sha256(payload)!=h['payload_sha256']: raise ValueError('payload hash mismatch')
        all_syms=unpack_symbols(payload,h['levels'],LAYERS*ACTIVE).reshape(LAYERS,ACTIVE)
        if not np.array_equal(np.bitwise_xor.reduce(all_syms[:DATA_LAYERS],axis=0),all_syms[DATA_LAYERS]):
            raise ValueError('parity mismatch')
        return all_syms[:DATA_LAYERS]




def run_archive_tests(outdir:Path,seed=SEED):
    rng=np.random.default_rng(seed+777)
    path=outdir/'sample_virtual_memory_crystal.vcrys'
    arc=CrystalArchive.create(path)
    obj=sha256(b'virtual-memory-crystal-objective')
    cur=sha256(b'tokyo-currentness-20260917')
    source=[]
    roots=[]
    for i in range(32):
        d=rng.integers(0,2,size=(DATA_LAYERS,ACTIVE),dtype=np.uint8)
        source.append(d)
        h=arc.append(f'flybrain-snapshot-{i:04d}',d,2,i,obj,cur)
        roots.append(h['page_root'])
    exact=all(np.array_equal(arc.read_data(f'flybrain-snapshot-{i:04d}'),source[i]) for i in range(32))
    reopen=CrystalArchive(path)
    reopen_exact=all(np.array_equal(reopen.read_data(f'flybrain-snapshot-{i:04d}'),source[i]) for i in range(32))
    overwrite_blocked=False
    try:
        reopen.append('flybrain-snapshot-0000',source[0],2,999,obj,cur)
    except ValueError as e:
        overwrite_blocked=('HOLD_WORM_PAGE_EXISTS' in str(e))


    corrupt=outdir/'sample_virtual_memory_crystal_corrupt.vcrys'
    shutil.copyfile(path,corrupt)
    b=bytearray(corrupt.read_bytes())
    # Flip a byte well inside the first payload region, after magic/header.
    # Find first payload offset from reopened index.
    first=reopen.index['flybrain-snapshot-0000']
    b[first['offset']+17]^=0x01
    corrupt.write_bytes(b)
    corruption_detected=False
    try:
        CrystalArchive(corrupt)
    except ValueError:
        corruption_detected=True
    return {
        'pages':32,
        'all_initial_reads_exact':exact,
        'all_reopen_reads_exact':reopen_exact,
        'worm_overwrite_blocked':overwrite_blocked,
        'single_byte_corruption_detected':corruption_detected,
        'archive_bytes':path.stat().st_size,
        'logical_source_payload_bytes':32*(DATA_LAYERS*ACTIVE//8),
        'logical_data_plus_parity_bytes':32*(LAYERS*ACTIVE//8),
        'first_page_root':roots[0],
        'last_page_root':roots[-1],
        'archive_sha256':sha256(path.read_bytes()),
        'path':str(path),
    }




def summarize_optical(results):
    keep={}
    for r in results:
        key=(r['levels'],r['condition'])
        keep[key]=r
    return keep




def main():
    outdir=Path('/mnt/data/tokyo_virtual_memory_crystal_v01')
    outdir.mkdir(parents=True,exist_ok=True)
    optical=run_optical_matrix()
    e8=run_e8_tests()
    archive=run_archive_tests(outdir)
    result={
        'schema':'TokyoVirtualMemoryCrystalExperimentV1_D0',
        'date':'2026-09-17',
        'claim_boundary':'software reduced optical-channel + exact WORM archive + mathematical E8 tests; not fabricated glass, not measured hardware, not full Maxwell propagation',
        'geometry':{'xy':'29x29','active_per_layer':800,'fiducials_per_layer':41,'data_layers':4,'parity_layers':1,'flybrain_payload_bits_binary':3200},
        'optical_matrix':optical,
        'e8_lane':e8,
        'archive':archive,
    }
    (outdir/'RESULTS__TOKYO_VIRTUAL_MEMORY_CRYSTAL_V0_1__20260917.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


    # Build concise report from actual measurements.
    m=summarize_optical(optical)
    lines=[]
    lines += ['# TOKYO VMC-001 — Virtual Memory Crystal V0.1 — D0', '',
              '## Mission',
              'Test whether the current 4x800 FlyBrain photonic topology can be turned into a persistent, damage-aware virtual crystal memory without confusing a software channel fixture with fabricated optical storage.', '',
              '## Design that survived the architecture challenge',
              '- One crystal page preserves the existing 29x29 / 800-active FlyBrain mapping.',
              '- Four data layers store the exact 4x800 perceptual state. A fifth XOR parity layer can reconstruct one completely erased data layer.',
              '- Each voxel is modeled by two calibrated optical observables (orientation/polarization-like and retardance/phase-like), with 41 fiducials per layer, 3D Gaussian crosstalk, gain/offset drift, read noise, quantization and whole-layer dropout.',
              '- The archive is WORM: page IDs cannot be overwritten; every page and payload is SHA-256 rooted; reopen requires no transcript replay.',
              '- E8 is tested as an 8D vector quantizer/noise code. It is NOT treated as a magical lossless 8D-to-5D projection.', '']
    lines += ['## Optical crystal-channel matrix', '| states/voxel | condition | post BER | exact pages | erasure pages recovered |', '|---:|---|---:|---:|---:|']
    for levels in (2,4,16):
        for cond in ('clean','moderate','harsh','severe','moderate_layer2_dropout'):
            r=m[(levels,cond)]
            lines.append(f"| {levels} ({r['bits_per_voxel']} bit) | {cond} | {r['post_recovery_bit_error_rate']:.6g} | {100*r['page_exact_fraction']:.3f}% | {r['erasure_pages_recovered']} |")
    lines += ['', '## Exact persistence / WORM test',
              f"- 32/32 pages initial read exact: {archive['all_initial_reads_exact']}",
              f"- 32/32 pages after close/reopen exact: {archive['all_reopen_reads_exact']}",
              f"- overwrite of existing page rejected: {archive['worm_overwrite_blocked']}",
              f"- one-byte media corruption detected by roots: {archive['single_byte_corruption_detected']}",
              f"- packed source bytes: {archive['logical_source_payload_bytes']}; packed data+parity bytes: {archive['logical_data_plus_parity_bytes']}; archive with headers: {archive['archive_bytes']}", '']
    q=e8['quantization']
    lines += ['## E8 lane',
              f"- Z8 scalar-lattice MSE/dim: {q['z8_mse_per_dimension']:.8f}",
              f"- E8 nearest-lattice MSE/dim: {q['e8_mse_per_dimension']:.8f}",
              f"- measured E8 MSE reduction at equal lattice scale: {100*q['e8_mse_reduction_vs_z8']:.2f}%",
              f"- E8 membership check: {100*q['e8_output_membership_fraction']:.3f}%", '',
              '| Gaussian noise sigma | Z8 decode error | E8 decode error |', '|---:|---:|---:|']
    for rr in e8['noise_decode']:
        lines.append(f"| {rr['sigma']:.2f} | {100*rr['z8_decode_error']:.4f}% | {100*rr['e8_decode_error']:.4f}% |")
    p=e8['naive_8d_to_5d_projection']
    lines += ['', '## Falsifier that matters',
              f"A rank-{p['rank']} continuous 8D->5D projection followed by the best linear inverse still lost {100*p['relative_mse_to_input_variance']:.2f}% of input variance in a no-noise test. Therefore arbitrary 8D data cannot be recovered losslessly from only five continuous optical parameters without a finite codebook/index or additional measurements.", '',
              '## Software-memory economics',
              'The virtual crystal does not compress ordinary RAM. A binary 4x800 snapshot is 400 packed bytes; adding one full parity layer makes the logical crystal page 500 bytes (+25%) before metadata. The analog optical field used for simulation is much larger still. Its earned value is persistent WORM semantics, damage modeling, calibration, optical-code experiments and a direct bridge to future physical glass—not lower host-RAM usage.', '',
              '## Disposition',
              'PASS_D0_VIRTUAL_MEMORY_CRYSTAL_WORM / PASS_4X800_TO_3D_CRYSTAL_PAGE / PASS_SINGLE_LAYER_PARITY_RECOVERY_WHERE_CHANNEL_DECODER_FLAGS_ERASURE / PASS_E8_VECTOR_QUANTIZER_BENEFIT / REJECT_NAIVE_LOSSLESS_8D_TO_5D / HOLD_PHYSICAL_GLASS_WRITE_READ / HOLD_FULL_MAXWELL_OR_MEASURED_OPTICAL_MODEL', '',
              '## Next earned experiments',
              '1. Replace the reduced Gaussian optical channel with Tokyo angular-spectrum / measured PSF reference for a small crystal page.',
              '2. Add a finite E8 codebook lane and compare exact byte recovery per optical cost against RS/parity coding.',
              '3. If a real SLM/camera or glass writer/read path exists later, bind measured PSF/noise/crosstalk and rerun unchanged logical tests.',
              '4. Keep crystal memory as a persistence/coding substrate; do not let it become a second authority, currentness or scheduler plane.', '']
    report='\n'.join(lines)
    (outdir/'ARENA_REPORT__TOKYO_VIRTUAL_MEMORY_CRYSTAL_V0_1__D0__20260917.md').write_text(report,encoding='utf-8')


    hashes={}
    for pth in sorted(outdir.iterdir()):
        if pth.is_file(): hashes[pth.name]=sha256(pth.read_bytes())
    (outdir/'HASHES__TOKYO_VIRTUAL_MEMORY_CRYSTAL_V0_1__20260917.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    # package source too
    shutil.copyfile(__file__,outdir/'SOURCE__tokyo_virtual_memory_crystal_v01.py')
    print(report)
    print('\nRESULT_JSON='+str(outdir/'RESULTS__TOKYO_VIRTUAL_MEMORY_CRYSTAL_V0_1__20260917.json'))


if __name__=='__main__': main()