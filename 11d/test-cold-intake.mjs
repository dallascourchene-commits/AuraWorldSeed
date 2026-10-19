// Playwright acceptance for the real 11D workbench + local ZIP source hydration.
// Runs without access to the owner's private Google Drive files or host authorities.
import { chromium } from "playwright";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { strict as assert } from "node:assert";
import { setTimeout as sleep } from "node:timers/promises";

const dir=mkdtempSync(join(tmpdir(),"aura-11d-ci-")),zipPath=join(dir,"sample-10d.zip");
const py=String.raw`import zipfile,sys
with zipfile.ZipFile(sys.argv[1],"w",zipfile.ZIP_DEFLATED) as z:
 z.writestr("modules/native-10d.html", """<!doctype html><title>native child</title><div id='nativeFixture'>10D CHILD ONLINE</div><script>window.AuraNaviFourfoldD2={status:()=>({schema:'FIXTURE_NAVI',host_bound:false}),objective:q=>({schema:'FIXTURE_OBJECTIVE',query:q})};</script>""")
 z.writestr("modules/second.html","<!doctype html><p id='second'>Second child</p>")
 z.writestr("docs/README.md","# cold source")
`;
const made=spawnSync("python3",["-c",py,zipPath],{encoding:"utf8"});
assert.equal(made.status,0,made.stderr);
const server=spawn("python3",["-m","http.server","8765","--bind","127.0.0.1"],{cwd:resolve("."),stdio:"ignore"});
let browser;const errors=[];
try{
 for(let i=0;i<30;i++){try{const res=await fetch("http://127.0.0.1:8765/11d/arena.html");if(res.ok)break}catch{}await sleep(200)}
 browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
 const page=await browser.newPage();
 page.on("pageerror",e=>errors.push(String(e)));
 await page.route("**/index.html",route=>route.fulfill({status:200,contentType:"text/html",body:"<!doctype html><title>root stub</title>"}));
 await page.goto("http://127.0.0.1:8765/11d/arena.html",{waitUntil:"domcontentloaded"});
 await page.locator("#coldCartridgePanel").waitFor({timeout:10000});
 await page.locator("#coldCatalog").click();
 await page.getByText("topLevelCandidateNames").waitFor({timeout:10000});
 const named=await page.locator("#coldOutput").innerText();
 assert.ok(named.includes("46"),"owner source index was not loaded");
 await page.locator("#coldInputs").setInputFiles({name:"sample-10d.zip",mimeType:"application/zip",buffer:readFileSync(zipPath)});
 await page.waitForFunction(()=>window.Aura11DColdCartridges?.status().htmlMembers===2);
 assert.equal(await page.locator("#coldChoose option").count(),3);
 const opt=await page.locator("#coldChoose option").evaluateAll(o=>o.find(x=>x.textContent.includes("native-10d.html"))?.value);assert.ok(opt);await page.locator("#coldChoose").selectOption(opt);
 await page.locator("#coldLoad").click();
 await page.frameLocator("#arena").locator("#nativeFixture").waitFor({timeout:12000});
 await page.locator("#naviStatus").click();
 await page.waitForFunction(()=>document.querySelector("#naviOutput").textContent.includes("FIXTURE_NAVI"));
 const receipt=await page.evaluate(()=>window.Aura11DColdCartridges.lastActivation);
 assert.equal(receipt.status,"SOURCE_ENTRY_REQUESTED_NOT_NATIVE_EFFECT");
 assert.equal(receipt.bytes>0,true);
 assert.match(receipt.sha256,/^[0-9a-f]{64}$/);
 await page.locator("#coldClear").click();
 assert.equal(await page.evaluate(()=>window.Aura11DColdCartridges.status().htmlMembers),0);
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({status:"PASS",tests:["catalog","zip-index","selective-extraction","native-frame","native-navi","sha256","clear","no-page-errors"],sha256:receipt.sha256,bytes:receipt.bytes},null,2));
}finally{await browser?.close();server.kill("SIGTERM")}
