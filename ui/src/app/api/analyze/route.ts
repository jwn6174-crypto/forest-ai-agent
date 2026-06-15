import { NextResponse } from "next/server";
import { getMockData } from "@/lib/mock-data";

const PYTHON_API = process.env.PYTHON_API_URL ?? "http://localhost:8001";
const DEMO_MODE = process.env.DEMO_MODE === "true";

export async function POST(request: Request) {
  const body = await request.json();
  const { pnu } = body;

  if (!pnu || typeof pnu !== "string") {
    return NextResponse.json({ error: "PNU 코드가 필요합니다" }, { status: 400 });
  }

  // 데모 모드: Python 백엔드 없이 mock 데이터 반환 (0.8초 딜레이로 로딩 시뮬레이션)
  if (DEMO_MODE) {
    await new Promise((r) => setTimeout(r, 800));
    const mockResult = getMockData(pnu);
    return NextResponse.json({ ...mockResult, pnu, _demo: true });
  }

  try {
    const res = await fetch(`${PYTHON_API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pnu }),
      // Next.js 서버 → Python 내부 호출이므로 캐싱 없음
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.text();
      console.error("[analyze] Python API 오류:", res.status, err);
      return NextResponse.json(
        { error: `분석 서버 오류: ${res.status}` },
        { status: 502 }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    console.error("[analyze] Python API 연결 실패:", e);
    return NextResponse.json(
      { error: "분석 서버에 연결할 수 없습니다. Python API 서버(포트 8001)가 실행 중인지 확인하세요." },
      { status: 503 }
    );
  }
}
