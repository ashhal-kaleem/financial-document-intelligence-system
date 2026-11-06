"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useFDISStore } from "@/store/useFDISStore";
import { FileText } from "lucide-react";

/** Do not export a placeholder as a verified financial memo or extracted dataset. */
export function MemoExportModal() {
  const { isExportModalOpen, setExportModalOpen } = useFDISStore();
  return (
    <Dialog open={isExportModalOpen} onOpenChange={setExportModalOpen}>
      <DialogContent className="w-[92vw] max-w-md p-5">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-semibold">
            <FileText className="size-4" /> Export is not ready yet
          </DialogTitle>
        </DialogHeader>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Verified memo and financial-data exports are not implemented. No placeholder report
          will be downloaded as if it were an analysis of your filing. You can copy individual
          answers and inspect their source citations in the workspace.
        </p>
        <Button variant="outline" onClick={() => setExportModalOpen(false)}>Close</Button>
      </DialogContent>
    </Dialog>
  );
}
