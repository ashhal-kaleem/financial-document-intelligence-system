import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { email } = await req.json();
    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json({ valid: false, message: "Invalid email format" }, { status: 400 });
    }

    const apiKey = process.env.ABSTRACT_EMAIL_KEY;
    if (!apiKey) {
      // Graceful fallback if key not present in environment
      return NextResponse.json({ valid: true, deliverability: "unknown" });
    }

    const res = await fetch(
      `https://emailreputation.abstractapi.com/v1/?api_key=${apiKey}&email=${encodeURIComponent(email)}`,
      { cache: "no-store" }
    );

    if (!res.ok) {
      return NextResponse.json({ valid: true, deliverability: "unverified" });
    }

    const data = await res.json();
    const isFormatValid = data?.email_deliverability?.is_format_valid ?? true;
    const isMxValid = data?.email_deliverability?.is_mx_valid ?? true;
    const isDisposable = data?.email_quality?.is_disposable ?? false;
    const org = data?.email_sender?.organization_name || null;
    const deliverability = data?.email_deliverability?.status || "deliverable";

    const valid = isFormatValid && isMxValid && !isDisposable;

    return NextResponse.json({
      valid,
      deliverability,
      organization: org,
      is_disposable: isDisposable,
    });
  } catch {
    return NextResponse.json({ valid: true, deliverability: "fallback" });
  }
}
