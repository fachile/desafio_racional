import { useEffect, useState } from "react";
import { doc, onSnapshot } from "firebase/firestore";
import { db } from "../firebase";

export function useInvestmentEvolution() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const docRef = doc(db, "investmentEvolutions", "user1");

    const unsubscribe = onSnapshot(
      docRef,
      (snapshot) => {
        if (snapshot.exists()) {
          const raw = snapshot.data();
          const parsed = (raw.array || [])
            .map((item) => ({
              date: new Date(item.date.seconds * 1000),
              portfolioValue: item.portfolioValue,
              portfolioIndex: item.portfolioIndex,
              dailyReturn: item.dailyReturn,
              contributions: item.contributions,
            }))
            .sort((a, b) => a.date - b.date);

          setData(parsed);
          setLastUpdated(new Date());
        } else {
          setError("Documento no encontrado");
        }
        setLoading(false);
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, []);

  return { data, loading, error, lastUpdated };
}
