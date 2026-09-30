import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createReducerHost } from './host.mjs';
const module = new WebAssembly.Module(fs.readFileSync(new URL('../ic32_checked.wasm', import.meta.url)));
const corpus = JSON.parse(fs.readFileSync(new URL('./oracle-corpus.json', import.meta.url)));
function instance() { return new WebAssembly.Instance(module).exports; }
function invoke(ex, input, steps=50000000, out=1048576) {
  const bytes = Buffer.from(input);
  new Uint8Array(ex.memory.buffer).set(bytes, ex.input_ptr());
  const status = ex.run_checked(bytes.length, steps, out);
  assert.equal(ex.last_status(), status);
  const length = ex.output_length();
  if (status !== 0) assert.equal(length, 0, 'failure must expose no partial output');
  return {status, output:Buffer.from(ex.memory.buffer,ex.output_ptr(),length).toString(), interactions:ex.last_interactions()};
}

test('ABI v2 exports its version and real buffer capacities', () => {
 const ex=instance(); assert.equal(ex.abi_version(),2);
 assert.equal(ex.input_capacity(),1048576); assert.equal(ex.output_capacity(),16777216);
});

test('26 oracle cases preserve output and interaction counts in checked and legacy entries', () => {
 const ex=instance();
 for (const c of corpus) {
  const r=invoke(ex,c.input); assert.equal(r.status,0,c.input);
  assert.equal(r.output,c.output,c.input); assert.equal(r.interactions,c.interactions,c.input);
  const bytes=Buffer.from(c.input);new Uint8Array(ex.memory.buffer).set(bytes,ex.input_ptr());
  const n=ex.run(bytes.length);
  assert.equal(Buffer.from(ex.memory.buffer,ex.output_ptr(),n).toString(),c.output);
  assert.equal(ex.last_interactions(),c.interactions);
 }
});

test('parse failures include suffixes, affinity, names, missing and overflowing labels', () => {
 const ex=instance();
 for (const input of ['* trailing','*\0junk','(','λx.','λx.(x x)','(x x)','!{x,x}=*;x','&{a,b}','&134217728{a,b}','&999999999999999999{a,b}','x'.repeat(40)])
  assert.equal(invoke(ex,input).status,2,input);
 assert.equal(invoke(ex,'x'.repeat(39)).status,0);
 assert.equal(invoke(ex,'&134217727{a,b}').status,0);
 assert.equal(invoke(ex,'* \n\t').status,0);
});

test('step exhaustion is distinct and does not consume an extra interaction', () => {
 const ex=instance();
 assert.deepEqual(invoke(ex,'(λx.x *)',0),{status:3,output:'',interactions:0});
 assert.deepEqual(invoke(ex,'(λx.x *)',1),{status:0,output:'*',interactions:1});
 assert.equal(invoke(ex,'ABORTED',0).output,'ABORTED');
});

test('exact output cap succeeds; one byte too small returns overflow without a prefix', () => {
 const ex=instance();
 assert.equal(invoke(ex,'ABORTED',0,7).status,0);
 assert.equal(invoke(ex,'ABORTED',0,6).status,4);
 assert.equal(invoke(ex,'*',0,0).status,4);
 assert.equal(invoke(ex,'λx.x',0,4).status,4); // UTF-8 lambda needs two bytes
 assert.equal(invoke(ex,'λx.x',0,5).output,'λa.a');
});

test('invalid lengths and budgets are typed and clear earlier output', () => {
 const ex=instance();invoke(ex,'ABORTED');
 for (const len of [-1,0,ex.input_capacity()]) {
  assert.equal(ex.run_checked(len,1,1),1);assert.equal(ex.output_length(),0);
 }
 for (const [steps,out] of [[-1,1],[50000001,1],[1,-1],[1,ex.output_capacity()]])
  assert.equal(invoke(ex,'*',steps,out).status,6);
});

test('parser depth exhaustion is a resource result, followed by successful recovery', () => {
 const ex=instance(); assert.equal(invoke(ex,'λx.'.repeat(520)+'*').status,5);
 assert.equal(invoke(ex,'*').status,0);
});

test('experimental host consumes typed failures and accepts the literal sentinel', async () => {
 const host=createReducerHost();
 assert.equal((await host.reduce('ABORTED')).output,'ABORTED');
 assert.equal((await host.reduce('* trailing')).reason,'guest-parse');
 assert.equal((await host.reduce('λx.(x x)')).reason,'guest-parse');
 assert.equal((await host.reduce('*')).workerExited,true);
});

test('free-name table exhaustion is typed instead of writing beyond the table', () => {
 let terms=Array.from({length:8193},(_,i)=>'n'+i);
 while(terms.length>1) {
  const next=[];
  for(let i=0;i<terms.length;i+=2) next.push(i+1<terms.length?'('+terms[i]+' '+terms[i+1]+')':terms[i]);
  terms=next;
 }
 const ex=instance();assert.equal(invoke(ex,terms[0]).status,5);
 assert.equal(invoke(ex,'*').output,'*');
});
