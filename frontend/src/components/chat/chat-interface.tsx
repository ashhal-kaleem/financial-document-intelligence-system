"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessageItem } from "./chat-message-item";
import { ChatInputBox } from "./chat-input-box";
import { ChatSidebar } from "@/components/shell/app-chrome";
import { useFDISStore, Citation } from "@/store/useFDISStore";
import { useOwnedDocuments } from "@/hooks/useOwnedDocuments";
import { DocumentState } from "@/components/workspace/document-state";
import { askPuter } from "@/lib/puter-ai";
import { AIConnection } from "./ai-connection";
import { loadChatHistory, saveChatHistory, ChatMessage } from "@/lib/chat-history";
export function ChatInterface() {
 const router=useRouter(); const params=useSearchParams(); const documentId=params.get("document") || "";
 const {documents,state,retry}=useOwnedDocuments(); const ready=documents.filter(d=>d.status==="ready"); const document=ready.find(d=>d.id===documentId);
 const {currentUser,setSelectedDocument,setActiveCitation}=useFDISStore();
 const [aiConnected,setAIConnected]=useState(false); const [aiModel,setAIModel]=useState(""); const [messages,setMessages]=useState<ChatMessage[]>([]); const [draft,setDraftState]=useState(""); const [error,setError]=useState(""); const [isStreaming,setIsStreaming]=useState(false); const [loaded,setLoaded]=useState(false);
 const previousMessages=useRef<ChatMessage[]>([]);const requestRef=useRef<AbortController|null>(null);const owner=currentUser?.id;const scope=documentId; const storageScope=scope || "unselected";
 const setDraft=useCallback((v:string)=>{ useFDISStore.getState().setChatDraft(storageScope,v);setDraftState(v); },[storageScope]);
 useEffect(()=>{setIsStreaming(false);setDraftState(useFDISStore.getState().chatDrafts[storageScope]||"");setError("");setLoaded(false);setMessages([]);let active=true;loadChatHistory(owner,storageScope).then(m=>{if(active){setMessages(m);setLoaded(true);}});return()=>{active=false;requestRef.current?.abort();requestRef.current=null;};},[owner,storageScope]);
 useEffect(()=>{setSelectedDocument(document?{id:document.id,filename:document.filename}:null);},[document?.id,document?.filename,setSelectedDocument]);
 useEffect(()=>{if(!aiConnected){requestRef.current?.abort();requestRef.current=null;setIsStreaming(false);}},[aiConnected]);
 const handleSend=async(content:string)=>{
  if(requestRef.current||!owner||!document||!loaded)return;
  if(!aiConnected||!aiModel){setError("Select a free model and connect AI first. Your question is still here.");return;}
  const controller=new AbortController();requestRef.current=controller;setError("");setIsStreaming(true);
  const userMsg:ChatMessage={id:`user-${Date.now()}`,role:"user",content,timestamp:new Date().toISOString()};const assistantId=`assistant-${Date.now()}`;const base=[...messages,userMsg];let answer:ChatMessage={id:assistantId,role:"assistant",content:"",timestamp:new Date().toISOString()};
  const isCurrent=()=>useFDISStore.getState().currentUser?.id===owner&&requestRef.current===controller&&!controller.signal.aborted;
  previousMessages.current=messages;setMessages([...base,answer]);
  try{await askPuter(content,[document.id],aiModel,event=>{if(!isCurrent())return;if(event.event==="citations"){answer={...answer,citations:(event.citations||[]).map(c=>({documentId:c.document_id,document:c.filename,page:c.page,chunk_id:String(c.chunk_index),relevance:c.similarity,snippet:c.snippet} as Citation))};}else if(event.event==="token"){answer={...answer,content:answer.content+(event.token||"")};}else if(event.event==="error"){throw Error(event.detail||"Answer failed.");}setMessages([...base,answer]);},controller.signal);
  if(!isCurrent())return;await saveChatHistory([...base,answer],owner,storageScope);setDraft("");
  }catch(err){if(isCurrent()){setMessages(messages);setError(err instanceof Error?err.message:"Answer could not be verified. Retry.");setDraft(content);}}
  finally{if(requestRef.current===controller){requestRef.current=null;setIsStreaming(false);}}
 };
 const cancel=()=>{requestRef.current?.abort();requestRef.current=null;setIsStreaming(false);setMessages(previousMessages.current);setError("Stopped waiting. A provider request already sent may still finish. Your draft is preserved.");};
 const clear=()=>{if(isStreaming)return;setMessages([]);setDraft("");setError("");saveChatHistory([],owner,storageScope);};
 const canAsk=Boolean(owner&&document&&loaded&&aiConnected&&aiModel);
 return <div className="v8-lilac flex min-h-0 min-w-0 flex-1 overflow-hidden bg-[#FDFDFD]">
 <ChatSidebar history={messages.filter(m=>m.role==="user").map(m=>m.content).reverse()} onPick={q=>q?setDraft(q):clear()}/>
 <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
 <div className="shrink-0 border-b border-[#ECE8F6] px-4 py-3 sm:px-6"><div className="flex flex-wrap items-center justify-between gap-3"><Link href="/documents" className="min-h-11 py-3 text-sm text-[#60449B] underline">← Back to documents</Link><button disabled={isStreaming} onClick={clear} className="min-h-11 rounded-full border px-4 text-xs disabled:opacity-40">New conversation</button></div><h1 className="text-xl font-semibold">Document Q&A</h1><p className="mt-2 text-xs text-[#6B6278]">Browser-only conversation. New conversation clears its saved messages. No cloud history or export yet.</p></div>
 {state!=="ready"?<div className="overflow-y-auto p-5"><DocumentState state={state} retry={retry}/>{state==="empty"&&<Link className="mt-4 inline-block underline" href="/documents">Upload a PDF in Documents</Link>}</div>:<>
 <div className="shrink-0 border-b border-[#ECE8F6] p-4 sm:px-6"><label className="block text-xs font-medium" htmlFor="question-document">1. Choose a ready PDF</label><select id="question-document" value={document?.id||""} disabled={isStreaming} onChange={e=>router.push(e.target.value?`/qa?document=${encodeURIComponent(e.target.value)}`:"/qa")} className="mt-2 min-h-11 w-full rounded-xl border bg-white px-3 text-sm"><option value="">Choose one document</option>{ready.map(d=><option key={d.id} value={d.id}>{d.filename}</option>)}</select>{documentId&&!document&&<p role="alert" className="mt-2 text-xs text-amber-800">This document is unavailable, not yours, or not ready. Choose a ready PDF. No question will use an implicit all-document scope.</p>}{!ready.length&&<p className="mt-2 text-xs">No ready PDF yet. Check processing status in <Link href="/documents" className="underline">Documents</Link>.</p>}</div>
 {document&&<AIConnection connected={aiConnected} setConnected={setAIConnected} model={aiModel} setModel={setAIModel}/>}
 <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6" aria-live="polite"><div className="mx-auto flex max-w-3xl flex-col gap-5">{!messages.length?<p className="text-sm text-[#6B6278]">{document?"2. Connect AI, then ask a question about this PDF. Answers must be checked against the cited page.":"Start by choosing a ready PDF. Your question will only use that document."}</p>:messages.map(msg=><ChatMessageItem key={msg.id} message={msg} onCitationClick={setActiveCitation}/>)}{isStreaming&&<p role="status" className="text-xs">Preparing answer and checking source markers...</p>}{error&&<p role="alert" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{error}</p>}</div></div>
 <div className="shrink-0 px-3 pb-4 sm:px-6">{isStreaming&&<button onClick={cancel} className="mb-2 min-h-11 rounded-full border px-4 text-sm">Cancel answer</button>}<ChatInputBox onSend={handleSend} isStreaming={isStreaming} disabled={!canAsk} draft={draft} setDraft={setDraft}/></div>
 </>}
 </main></div>;
}
