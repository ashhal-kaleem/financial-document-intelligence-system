const {test}=require('node:test'); const assert=require('node:assert/strict');const fs=require('fs');const ts=require('typescript');
const js=ts.transpileModule(fs.readFileSync('src/lib/puter-ai.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
const mod={exports:{}};new Function('require','module','exports',js)(n=>n==='@/lib/supabase'?{getAccessToken:async()=>'private-fdis-token'}:require(n),mod,mod.exports);
const {askPuter,PUTER_MODELS}=mod.exports;const model=PUTER_MODELS[0].id;
function setup(result,validateOk=true){
 const calls=[];global.window={puter:{auth:{isSignedIn:()=>true},ai:{chat:async(messages,options)=>{calls.push({messages,options});return result;}}}};
 global.fetch=async(url,opts)=>{const validation=url.endsWith('browser-validate');return new Response(JSON.stringify({data:validation?{citation_ids_valid:true}:{messages:[{role:'user',content:'retrieved text'}],citations:[],receipt:'signed.receipt'}}),{status:validation&&!validateOk?422:200});};return calls;
}
test('Puter explicit provider no fallback, completed zero-cost answer validated before display',async()=>{
 const calls=setup({message:{content:'Revenue [1]'},finish_reason:'stop',usage:{cost:0}});const events=[];
 await askPuter('Revenue?',[],model,e=>events.push(e),new AbortController().signal);
 assert.equal(calls[0].options.fallback,false);assert.equal(calls[0].options.provider,'openrouter');assert.equal(calls[0].options.normalize,true);assert.equal(calls[0].options.stream,false);
 assert.equal(JSON.stringify(calls).includes('private-fdis-token'),false);assert.equal(events.at(-1).event,'done');
});
for(const [name,result] of Object.entries({truncated:{message:{content:'Partial [1]'},finish_reason:'length',usage:{cost:0}},paid:{message:{content:'x [1]'},finish_reason:'stop',usage:{cost:1}},unknown_charge:{message:{content:'x [1]'},finish_reason:'stop'},empty:{message:{content:''},finish_reason:'stop',usage:{cost:0}}}))test('Puter rejects '+name,async()=>{setup(result);const events=[];await assert.rejects(askPuter('q',[],model,e=>events.push(e),new AbortController().signal));assert.equal(events.length,0);});
test('backend rejection never shows browser answer',async()=>{setup({message:{content:'x [9]'},finish_reason:'stop',usage:{cost:0}},false);const events=[];await assert.rejects(askPuter('q',[],model,e=>events.push(e),new AbortController().signal));assert.equal(events.length,0);});
test('unknown model rejected before any provider call',async()=>{const calls=setup({});await assert.rejects(askPuter('q',[],'paid',()=>{},new AbortController().signal));assert.equal(calls.length,0);});
test('no-context fixed answer never invokes provider',async()=>{const calls=setup({});global.fetch=async()=>new Response(JSON.stringify({data:{answer:'Not covered in report.',citations:[],messages:[],receipt:null}}));const events=[];await askPuter('q',[],model,e=>events.push(e),new AbortController().signal);assert.equal(calls.length,0);assert.equal(events.at(-1).event,'done');});
