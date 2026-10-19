/* Aura 11D D0 source-governed cold cartridge intake.
   No remote fetch of owner documents, no auto-execution and no JSpace authority. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const wrap=document.querySelector(".wrap > section")||document.querySelector(".wrap");
if(!wrap||!$("sourceFile"))return;
const ui=document.createElement("div");ui.className="panel";ui.id="coldCartridgePanel";ui.style.marginTop="12px";
ui.innerHTML='<div class="topline"><h2>10D cold cartridge library</h2><span class="status hold">OWNER-SELECTED · LOCAL ONLY</span></div>'+
'<p class="sub">Choose one or more trusted 10D HTML/ZIP files. ZIP contents are indexed cold and decompressed only when you explicitly activate one HTML member. No file is uploaded. Other Arena branches remain separate and unchanged.</p>'+
'<div class="row spaced"><label for="coldInputs">Add trusted HTML / ZIP sources</label><input type="file" id="coldInputs" accept=".html,.htm,.zip,text/html,application/zip" multiple style="max-width:290px"><button type="button" id="coldClear">Clear imported sources</button></div>'+
'<div class="row spaced"><label for="coldChoose">Executable HTML member</label><select id="coldChoose" style="max-width:100%;flex:1 1 220px"><option value="">No locally imported candidates</option></select><button id="coldLoad" type="button">Activate selected in native 10D frame</button></div>'+
'<div class="row spaced"><button id="coldManifest" type="button">Export cold manifest</button><button id="coldCatalog" type="button">Show owner 10D index</button><span class="sub" id="coldCount">0 sources · 0 runnable members</span></div>'+
'<pre class="readout" id="coldOutput" aria-live="polite">Waiting for owner-selected source files. A ZIP is not an installed capability; inherited native APIs are probed only after HTML execution.</pre>'+
'<div class="guard spaced">Trust boundary: running selected HTML grants that program the same browser-origin privileges as the existing inherited Arena iframe. Import only audited owner-approved code. No automatic execution, no model/JID duplication, no host permission, no flattening incompatible ancestors. ZIP64/encrypted/unsupported formats return HOLD.</div>';
wrap.appendChild(ui);
const registry=[];const byId=new Map();const MAX_ZIP=210*1024*1024,MAX_MEMBER=80*1024*1024,MAX_TOTAL=500*1024*1024;
let retained=0,serial=0,inventory=null;
const set=x=>$("coldOutput").textContent=typeof x==="string"?x:JSON.stringify(x,null,2);
function safe(name){return name&&!name.startsWith("/")&&!name.includes("\\")&&!name.split("/").includes("..")&&!name.includes("\0")}
function parseZip(bytes){
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 const u16=p=>view.getUint16(p,true),u32=p=>view.getUint32(p,true),N=bytes.length;
 let eocd=-1;for(let p=N-22;p>=Math.max(0,N-65557);p--)if(u32(p)===0x06054b50){eocd=p;break}
 if(eocd<0)throw Error("HOLD_ZIP_EOCD_NOT_FOUND");
 const count=u16(eocd+10),offset=u32(eocd+16);
 if(count===65535||offset===0xffffffff)throw Error("HOLD_ZIP64_REQUIRES_SEPARATE_ADAPTER");
 let p=offset;const entries=[];
 for(let i=0;i<count;i++){
  if(p+46>N||u32(p)!==0x02014b50)throw Error("HOLD_CENTRAL_DIRECTORY_INVALID");
  const flags=u16(p+8),method=u16(p+10),crc=u32(p+16),csize=u32(p+20),usize=u32(p+24),
   nl=u16(p+28),xl=u16(p+30),cl=u16(p+32),local=u32(p+42);
  if(p+46+nl+xl+cl>N)throw Error("HOLD_ZIP_CENTRAL_OVERRUN");
  const name=new TextDecoder("utf-8").decode(bytes.subarray(p+46,p+46+nl));
  if(safe(name)&&!name.endsWith("/")&&/\.(html?|HTML?)$/.test(name)){
   if(flags&1)throw Error("HOLD_ENCRYPTED_ZIP_MEMBER");
   if(usize>MAX_MEMBER)throw Error("HOLD_HTML_MEMBER_OVER_80_MIB");
   if(method!==0&&method!==8)throw Error("HOLD_COMPRESSION_METHOD_"+method);
   entries.push({name,method,flags,crc,csize,usize,local});
  }
  p+=46+nl+xl+cl;
 }
 return entries;
}
let crcTable=Array.from({length:256},(_,n)=>{let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;return c>>>0});
function crc32(bytes){let c=0xffffffff;for(let i=0;i<bytes.length;i++)c=crcTable[(c^bytes[i])&255]^(c>>>8);return(c^0xffffffff)>>>0}
async function inflate(entry,bytes){
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),o=entry.local;
 if(o+30>bytes.length||v.getUint32(o,true)!==0x04034b50)throw Error("HOLD_LOCAL_ZIP_HEADER");
 let p=o+30+v.getUint16(o+26,true)+v.getUint16(o+28,true);
 if(p+entry.csize>bytes.length)throw Error("HOLD_MEMBER_BOUNDARY");
 const encoded=bytes.subarray(p,p+entry.csize);
 if(entry.method===0)return encoded.slice();
 if(typeof DecompressionStream==="undefined")throw Error("HOLD_DEFLATE_RAW_NOT_SUPPORTED");
 const reader=new Blob([encoded]).stream().pipeThrough(new DecompressionStream("deflate-raw")).getReader();
 const chunks=[];let total=0;
 while(true){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>MAX_MEMBER){await reader.cancel();throw Error("HOLD_DECOMPRESS_SIZE_LIMIT")}chunks.push(value)}
 const out=new Uint8Array(total);let pos=0;for(const b of chunks){out.set(b,pos);pos+=b.length}return out;
}
function refresh(){
 $("coldChoose").replaceChildren(new Option("Choose an indexed HTML source",""));
 for(const r of registry)$("coldChoose").add(new Option(r.label+" ("+Math.round(r.size/1024)+" KiB)",r.id));
 $("coldCount").textContent=(new Set(registry.map(x=>x.owner)).size)+" files · "+registry.length+" runnable HTML members";
}
async function addFiles(files){
 let ok=0;const holds=[];
 for(const file of files){
  try{
   if(file.size>MAX_ZIP||file.size+retained>MAX_TOTAL)throw Error("HOLD_COLD_MEMORY_BUDGET");
   const owner=++serial;let members=[];
   if(/\.zip$/i.test(file.name)){
    const bytes=new Uint8Array(await file.arrayBuffer());members=parseZip(bytes).map((member,j)=>({
     id:"zip:"+owner+":"+j,owner,label:file.name+" / "+member.name,size:member.usize,fileName:member.name,
     zipBytes:bytes,entry:member,container:file.name,type:"zip-member"}));
   }else if(/\.html?$/i.test(file.name)){
    members=[{id:"html:"+owner,owner,label:file.name,size:file.size,fileName:file.name,file,type:"html"}];
   }else throw Error("HOLD_UNSUPPORTED_FILE");
   if(registry.length+members.length>2000)throw Error("HOLD_INDEX_LIMIT");
   registry.push(...members);members.forEach(x=>byId.set(x.id,x));retained+=file.size;ok++;
  }catch(e){holds.push({file:file.name,reason:String(e.message||e)})}
 }
 refresh();set({status:holds.length?"PARTIAL_IMPORT":"COLD_INDEX_READY",filesAccepted:ok,executableHtmlMembers:registry.length,retainedCompressedBytes:retained,holds,execution:"NONE_YET"});
}
async function activate(){
 const id=$("coldChoose").value,r=byId.get(id);if(!r){set("HOLD_SELECT_HTML_MEMBER");return}
 $("coldLoad").disabled=true;set("Decoding and verifying "+r.label+" …");
 try{
  const bytes=r.type==="html"?new Uint8Array(await r.file.arrayBuffer()):await inflate(r.entry,r.zipBytes);
  if(bytes.length>MAX_MEMBER)throw Error("HOLD_SIZE_LIMIT");
  if(r.entry&&(bytes.length!==r.entry.usize||crc32(bytes)!==r.entry.crc))throw Error("HOLD_ZIP_CRC_OR_LENGTH_MISMATCH");
  const html=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
  const verified=crypto?.subtle?Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))).map(x=>x.toString(16).padStart(2,"0")).join(""):"HOLD_NO_SECURE_CRYPTO";
  // Reuse the already-tested native HTML file picker and its 10D-frame/Navi callbacks.
  const selected=new File([bytes],r.fileName.split("/").pop()||"source.html",{type:"text/html"});
  const dt=new DataTransfer();dt.items.add(selected);const picker=$("sourceFile");picker.files=dt.files;
  picker.dispatchEvent(new Event("change",{bubbles:true}));
  window.Aura11DColdCartridges.lastActivation={file:r.container||r.fileName,member:r.fileName,sha256:verified,bytes:bytes.length,ts:new Date().toISOString(),status:"SOURCE_ENTRY_REQUESTED_NOT_NATIVE_EFFECT"};
  set({...window.Aura11DColdCartridges.lastActivation,note:"Imported byte-verified HTML into the native 10D frame. Probe native Navi/APIs after its load. No automatic merge or authority granted."});
 }catch(e){set({status:"HOLD_EXECUTION",source:r.label,reason:String(e.message||e)})}finally{$("coldLoad").disabled=false}
}
function exportManifest(){
 const out={schema:"Aura11DColdCartridgeIndexD0",timestamp:new Date().toISOString(),sourceCount:new Set(registry.map(x=>x.owner)).size,
  members:registry.map(x=>({source:x.container||x.fileName,member:x.fileName,uncompressedBytes:x.size,method:x.entry?.method??null,stage:"COLD_INDEXED_NOT_EXECUTED"})),
  latestActivation:window.Aura11DColdCartridges.lastActivation||null,
  disclaimer:"Source index is not a complete 11D feature merge, JSpace authority or native integration."};
 const url=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:"application/json"})),a=document.createElement("a");
 a.href=url;a.download="aura-11d-cold-cartridge-manifest.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
$("coldInputs").onchange=e=>addFiles(Array.from(e.target.files||[]));
$("coldLoad").onclick=activate;
$("coldClear").onclick=()=>{registry.length=0;byId.clear();retained=0;refresh();set("Cold registry cleared. Previously activated Arena document remains until Return/Re-enter.")};
$("coldManifest").onclick=exportManifest;
$("coldCatalog").onclick=async()=>{
 try{inventory=inventory||await fetch("./10d-source-inventory.json").then(r=>{if(!r.ok)throw Error("HTTP_"+r.status);return r.json()});
 set({schema:inventory.schema,scope:inventory.scope,files:inventory.file_count,topLevelCandidateNames:inventory.files.map(x=>x.name),warning:"INDEX_ONLY — fetch files locally from owner Drive; this catalog grants no private access."})}
 catch(e){set("HOLD_PUBLIC_CATALOG: "+String(e))}
};
window.Aura11DColdCartridges={status:()=>({ownerFiles:new Set(registry.map(x=>x.owner)).size,htmlMembers:registry.length,compressedBytes:retained,lastActivation:window.Aura11DColdCartridges.lastActivation||null}),addFiles,activate,exportManifest,lastActivation:null};
refresh();
})();