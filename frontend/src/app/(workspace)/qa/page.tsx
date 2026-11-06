import { Suspense } from "react";
import { ChatInterface } from "@/components/chat/chat-interface";
export default function Page() { return <Suspense fallback={<p className="p-6">Loading workspace...</p>}><ChatInterface/></Suspense>; }
