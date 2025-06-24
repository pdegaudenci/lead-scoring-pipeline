
import { useEffect, useState } from "react";
import axios from "axios";

export default function Scoring() {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8000/score-all-leads")
      .then(res => setData(res.data))
      .catch(err => console.error("Error:", err));
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">🧠 Resultados de Scoring</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
