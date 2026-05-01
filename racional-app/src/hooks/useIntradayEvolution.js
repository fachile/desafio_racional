import { useEffect, useState, useRef } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { db } from "../firebase";

function formatTime(date) {
  return date.toLocaleTimeString("es-CL", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getSnapshotSignature(item) {
  return JSON.stringify({
    dateSeconds: item?.date?.seconds ?? null,
    portfolioValue: item?.portfolioValue ?? null,
    portfolioIndex: item?.portfolioIndex ?? null,
    dailyReturn: item?.dailyReturn ?? null,
    contributions: item?.contributions ?? null,
  });
}

export function useIntradayEvolution() {
  const [ticks, setTicks] = useState([]);
  const [latestValue, setLatestValue] = useState(null);
  const [loading, setLoading] = useState(true);
  const hasInitializedRef = useRef(false);
  const lastSignatureRef = useRef(null);

  useEffect(() => {
    const docRef = doc(db, "investmentEvolutions", "user1");

    const unsubscribe = onSnapshot(docRef, (snapshot) => {
      if (!snapshot.exists()) {
        setLoading(false);
        return;
      }

      const raw = snapshot.data();
      const array = raw.array || [];

      // Ordenar cronológicamente
      const sorted = [...array].sort((a, b) => a.date.seconds - b.date.seconds);
      const last = sorted[sorted.length - 1];
      if (!last) { setLoading(false); return; }
      const previous = sorted.length > 1 ? sorted[sorted.length - 2] : null;

      const lastDate = new Date(last.date.seconds * 1000);

      const latestObj = {
        portfolioValue: last.portfolioValue,
        portfolioIndex: last.portfolioIndex,
        dailyReturn: last.dailyReturn,
        contributions: last.contributions,
        date: lastDate,
      };

      setLatestValue(latestObj);

      const signature = getSnapshotSignature(last);
      const previousTick = previous
        ? {
            time: "Apertura",
            timestamp: new Date(previous.date.seconds * 1000).getTime(),
            portfolioValue: previous.portfolioValue,
            portfolioIndex: previous.portfolioIndex,
            dailyReturn: previous.dailyReturn,
          }
        : null;
      const currentTick = {
        time: formatTime(new Date()),
        timestamp: Date.now(),
        portfolioValue: last.portfolioValue,
        portfolioIndex: last.portfolioIndex,
        dailyReturn: last.dailyReturn,
      };

      if (!hasInitializedRef.current) {
        hasInitializedRef.current = true;
        lastSignatureRef.current = signature;
        setTicks(previousTick ? [previousTick, currentTick] : [currentTick]);
      } else if (signature !== lastSignatureRef.current) {
        lastSignatureRef.current = signature;
        setTicks((prev) => [...prev, currentTick]);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return { ticks, latestValue, loading };
}
