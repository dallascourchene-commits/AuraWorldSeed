/* Aura D10: bounded, source-attested ARC-AGI-2 symbolic candidate search.
   Pure JS module. Receives only task.training input/output and test.input.
   No access to withheld test outputs. Runs identically in Node or browser.
*/
(function (root) {
'use strict';
const clone=g=>g.map(r=>r.slice());
const h=g=>g.length,w=g=>g[0]?.length||0;
const key=g=>JSON.stringify(g);
const transpose=g=>g[0].map((_,j)=>g.map(r=>r[j]));
const rot=g=>g[0].map((_,j)=>g.map(r=>r[j]).reverse());
const fliph=g=>g.map(r=>r.slice().reverse());
const flipv=g=>g.slice().reverse().map(r=>r.slice());
const ones=(a,b,v)=>Array.from({length:a},()=>Array(b).fill(v));
const allColors=g=>[...new Set(g.flat())];
const domColor=g=>{let m=new Map();g.flat().forEach(c=>m.set(c,(m.get(c)||0)+1));return [...m].sort((a,b)=>b[1]-a[1]||a[0]-b[0])[0]?.[0]??0};
const makeKernel=(name,apply,complexity=1)=>({name,apply,complexity});
const ops=[];
function add(n,fn,c=1){ops.push(makeKernel(n,fn,c));}
add('identity',clone,0);
add('rotate90',rot);add('rotate180',g=>rot(rot(g)));add('rotate270',g=>rot(rot(rot(g))));
add('flip-horizontal',fliph);add('flip-vertical',flipv);add('transpose',transpose);
add('anti-transpose',g=>fliph(flipv(transpose(g))));
for(let sx=1;sx<=4;sx++)for(let sy=1;sy<=4;sy++){if(sx===1&&sy===1)continue;
 add(`pixel-scale-${sx}x${sy}`,g=>{let out=[];for(const r of g)for(let k=0;k<sy;k++)out.push(r.flatMap(c=>Array(sx).fill(c)));return out},2);
 add(`tile-${sx}x${sy}`,g=>{let out=[];for(let iy=0;iy<sy;iy++)for(const row of g){let r=[];for(let ix=0;ix<sx;ix++)r.push(...row);out.push(r)}return out},2);
 add(`tile-checker-rot-${sx}x${sy}`,g=>{let out=[];for(let iy=0;iy<sy;iy++){let copies=[];for(let ix=0;ix<sx;ix++)copies.push((ix+iy)%2===0?g:flipv(fliph(g)));for(let ry=0;ry<h(g);ry++)out.push(copies.flatMap(t=>t[ry]));}return out},3);
 add(`tile-checker-fliph-${sx}x${sy}`,g=>{let out=[];for(let iy=0;iy<sy;iy++){let copies=[];for(let ix=0;ix<sx;ix++)copies.push((ix+iy)%2===0?g:fliph(g));for(let ry=0;ry<h(g);ry++)out.push(copies.flatMap(t=>t[ry]));}return out},3);
 add(`tile-checker-flipv-${sx}x${sy}`,g=>{let out=[];for(let iy=0;iy<sy;iy++){let copies=[];for(let ix=0;ix<sx;ix++)copies.push((ix+iy)%2===0?g:flipv(g));for(let ry=0;ry<h(g);ry++)out.push(copies.flatMap(t=>t[ry]));}return out},3);
}
for(const bg of [0,'dominant']){
 const bcol=g=>bg==='dominant'?domColor(g):bg;
 function box(g){let b=bcol(g),coords=[];g.forEach((r,y)=>r.forEach((c,x)=>{if(c!==b)coords.push([y,x])}));if(!coords.length)return null;return [Math.min(...coords.map(v=>v[0])),Math.max(...coords.map(v=>v[0])),Math.min(...coords.map(v=>v[1])),Math.max(...coords.map(v=>v[1]))]}
 add(`crop-object-bg${bg}`,g=>{let b=box(g);if(!b)return clone(g);return g.slice(b[0],b[1]+1).map(r=>r.slice(b[2],b[3]+1))},2);
 add(`bounding-box-solid-bg${bg}`,g=>{let b=box(g),v=clone(g);if(b)for(let y=b[0];y<=b[1];y++)for(let x=b[2];x<=b[3];x++)v[y][x]=v[y][x]===bcol(g)?domColor(g.filter?g:g):v[y][x];return v},3);
 for(let p=1;p<=3;p++)add(`pad-${p}-bg${bg}`,g=>{const v=bcol(g),r=ones(h(g)+p*2,w(g)+p*2,v);for(let y=0;y<h(g);y++)for(let x=0;x<w(g);x++)r[y+p][x+p]=g[y][x];return r},2);
 for(let dir of ['top','bottom','left','right'])for(let n=1;n<=4;n++)add(`strip-${dir}-${n}`,g=>{if(dir==='top')return g.slice(0,n).map(r=>r.slice());if(dir==='bottom')return g.slice(-n).map(r=>r.slice());if(dir==='left')return g.map(r=>r.slice(0,n));return g.map(r=>r.slice(-n))},2);
}
for(let k=1;k<=4;k++){
 add(`crop-to-${k}x${k}`,g=>g.slice(0,k).map(r=>r.slice(0,k)),3);
}
add('nonzero-binary',g=>g.map(r=>r.map(v=>v?1:0)),2);
add('fill-zero-with-dominant',g=>{let d=domColor(g);return g.map(r=>r.map(v=>v===0?d:v))},2);
add('fill-row-zero-horizontal',g=>g.map(r=>{let v=r.find(x=>x!==0)??0;return r.map(x=>x||v)}),3);
add('fill-column-zero-vertical',g=>transpose(transpose(g).map(r=>{let v=r.find(x=>x!==0)??0;return r.map(x=>x||v)})),3);
for(const mode of ['horizontal','vertical','both']){
add(`bounding-rectangles-${mode}`,g=>{let z=clone(g),colors=allColors(g).filter(x=>x!==0);for(const c of colors){let yy=[],xx=[];g.forEach((r,y)=>r.forEach((v,x)=>{if(v===c){yy.push(y);xx.push(x)}}));if(!yy.length)continue;const ymin=Math.min(...yy),ymax=Math.max(...yy),xmin=Math.min(...xx),xmax=Math.max(...xx);if(mode==='horizontal'||mode==='both')for(const y of new Set(yy))for(let x=xmin;x<=xmax;x++)if(z[y][x]===0)z[y][x]=c;if(mode==='vertical'||mode==='both')for(const x of new Set(xx))for(let y=ymin;y<=ymax;y++)if(z[y][x]===0)z[y][x]=c;}return z},3);
}
// Generic connected-component extractor: 4 or 8 adjacency, color-specific or any nonzero.
function components(g,connectivity=4,perColor=true){let seen=new Set(),comps=[];let dirs=connectivity===8?[[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]]:[[-1,0],[1,0],[0,-1],[0,1]];for(let y=0;y<h(g);y++)for(let x=0;x<w(g);x++){
 if(g[y][x]===0||seen.has(`${y},${x}`))continue;let q=[[y,x]],cells=[],c=g[y][x];seen.add(`${y},${x}`);for(let i=0;i<q.length;i++){let [Y,X]=q[i];cells.push([Y,X]);for(const [dy,dx] of dirs){let a=Y+dy,b=X+dx,k=`${a},${b}`;if(a>=0&&a<h(g)&&b>=0&&b<w(g)&&!seen.has(k)&&g[a][b]!==0&&(!perColor||g[a][b]===c)){seen.add(k);q.push([a,b])}}}comps.push({cells,color:c,size:cells.length,y0:Math.min(...cells.map(c=>c[0])),y1:Math.max(...cells.map(c=>c[0])),x0:Math.min(...cells.map(c=>c[1])),x1:Math.max(...cells.map(c=>c[1]))});}
return comps}
for(const conn of [4,8])for(const pc of [true,false])for(const typ of ['largest','smallest'])for(const out of ['crop','mask','solidcrop']){
add(`component-${conn}-${pc?'colored':'any'}-${typ}-${out}`,g=>{let cs=components(g,conn,pc);if(!cs.length)return clone(g);cs.sort((a,b)=> (typ==='smallest'?a.size-b.size:b.size-a.size)||a.y0-b.y0||a.x0-b.x0);let c=cs[0],r=out==='mask'?ones(h(g),w(g),0):ones(c.y1-c.y0+1,c.x1-c.x0+1,0);for(const [y,x] of c.cells)r[out==='mask'?y:y-c.y0][out==='mask'?x:x-c.x0]=c.color;if(out==='solidcrop')for(let y=0;y<r.length;y++)for(let x=0;x<r[0].length;x++)r[y][x]=c.color;return r},4);
}
for(let axis of ['r','c'])for(let typ of ['first','last']){
add(`nonzero-${axis}-${typ}`,g=>{let q=axis==='r'?g:transpose(g);let rr=typ==='first'?q.find(r=>r.some(v=>v!==0)):q.slice().reverse().find(r=>r.some(v=>v!==0));if(!rr)return clone(g);return axis==='r'?[rr.slice()]:rr.map(c=>[c])},3);
}
// D10.1: general, output-blind recursive spatial operators, learned only from demonstrations.
const dihedrals=[['id',clone],['fh',fliph],['fv',flipv],['r90',rot],['r180',g=>rot(rot(g))],['r270',g=>rot(rot(rot(g)))],['tr',transpose],['anti',g=>fliph(flipv(transpose(g)))]];
for(const [dn,df] of dihedrals){
 for(const q of [2,3,4]){
  // At each non-background position in a seed array, stamp a transformed copy of the seed.
  add(`recursive-stamp-${dn}-k${q}`,g=>{
   if(h(g)*q>30||w(g)*q>30)return clone(g);
   const out=ones(h(g)*q,w(g)*q,0), stamp=df(g);
   if(h(stamp)!==h(g)||w(stamp)!==w(g))return clone(g);
   for(let by=0;by<q;by++)for(let bx=0;bx<q;bx++){
     const v=g[by%h(g)][bx%w(g)];if(v===0)continue;
     for(let y=0;y<h(g);y++)for(let x=0;x<w(g);x++)out[by*h(g)+y][bx*w(g)+x]=stamp[y][x];
   }return out;
  },5);
  for(let mode of ['horizontal','vertical']){
   add(`alternating-block-${mode}-${dn}-k${q}`,g=>{
    if(h(g)*q>30||w(g)*q>30)return clone(g);
    let alt=df(g);if(h(alt)!==h(g)||w(alt)!==w(g))return clone(g);
    let out=[];for(let iy=0;iy<q;iy++)for(let ry=0;ry<h(g);ry++){
      let row=[];for(let ix=0;ix<q;ix++){let active=(mode==='horizontal'?iy:ix)%2;
       row.push(...(active?alt:g)[ry]);}out.push(row);
    }return out;
   },4);
  }
 }
 for(const sx of [2,3])for(const sy of [2,3]){
  add(`mirrored-expand-${dn}-${sx}x${sy}`,g=>{
   const base=df(g);if(h(base)*sy>30||w(base)*sx>30)return clone(g);
   let out=[];for(let iy=0;iy<sy;iy++){
    const rows=[];for(let ix=0;ix<sx;ix++){
      let part=base;if(ix%2)part=fliph(part);if(iy%2)part=flipv(part);rows.push(part)
    }for(let ry=0;ry<h(base);ry++)out.push(rows.flatMap(block=>block[ry]));
   }return out;
  },4);
 }
}
for(let dx of [2,3,4])for(let dy of [2,3,4])for(let section of ['first','last']){
 add(`partial-block-${section}-${dx}x${dy}`,g=>{
  if(h(g)*dy>30||w(g)*dx>30)return clone(g);
  const out=ones(h(g)*dy,w(g)*dx,0);
  for(let iy=0;iy<dy;iy++)for(let ix=0;ix<dx;ix++)if((section==='first'&&iy===0)||(section==='last'&&iy===dy-1))for(let y=0;y<h(g);y++)for(let x=0;x<w(g);x++)out[iy*h(g)+y][ix*w(g)+x]=g[y][x];
  return out;
 },4);
}
function commonColorMap(train,base){let map=new Map(),ok=true;for(const pair of train){let i=base.apply(pair.input),o=pair.output;if(h(i)!==h(o)||w(i)!==w(o))return null;for(let y=0;y<h(i);y++)for(let x=0;x<w(i);x++){let a=i[y][x],b=o[y][x];if(map.has(a)&&map.get(a)!==b){ok=false;break}map.set(a,b);}if(!ok)return null;}return map}
function search(task,opt={}){
 const train=task.train||task.training||[];let tests=task.test||[];
 if(train.length===0)return {status:'HOLD_NO_TRAIN',candidates:0,predictions:[]};
 const budget=opt.budget||650;let checks=0,valid=[];
 function fits(op){for(const p of train){let out;try{out=op.apply(p.input)}catch(e){return false}checks++;if(key(out)!==key(p.output))return false;}return true}
 for(const op of ops){if(checks>=budget)break;if(fits(op))valid.push(op)}
 // Color-map learns only from training demonstration grids, no test outputs.
 if(checks<budget)for(const base of [ops[0],...ops.slice(1,8)]){let mapping=commonColorMap(train,base);if(mapping){let op=makeKernel(`${base.name}+learned-color-map`,g=>base.apply(g).map(r=>r.map(v=>mapping.has(v)?mapping.get(v):v)),base.complexity+3);if(fits(op))valid.push(op)}}
 valid.sort((a,b)=>a.complexity-b.complexity||a.name.localeCompare(b.name));
 if(valid.length===0)return {status:'HOLD_NO_EXACT_DEMONSTRATION_FIT',checks,candidates:0,predictions:[]};
 const chosen=valid[0];let predictions=[];for(const t of tests){try{let p=chosen.apply(t.input);if(p.length>30||p[0].length>30||!p.length)throw Error('output shape');predictions.push(p)}catch(e){return{status:'HOLD_UNSAFE_OUTPUT',checks,candidates:valid.length,chosen:chosen.name,predictions:[]}}}
 return {status:'TRAIN_FIT_CANDIDATE',checks,candidates:valid.length,chosen:chosen.name,predictions};
}
root.AuraArcD10={search,ops:ops.map(o=>({name:o.name,complexity:o.complexity})),version:'D10_ARC_PUBLIC_TRAINING_DSL'};
if(typeof module!=='undefined')module.exports=root.AuraArcD10;
})(typeof window==='undefined'?globalThis:window);
