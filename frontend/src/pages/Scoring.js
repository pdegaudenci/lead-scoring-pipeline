import { useEffect, useState } from "react";
import axios from "axios";

export default function Scoring() {
  const [data, setData] = useState([]);
  const API_BASE = process.env.REACT_APP_API_BASE_URL;

  useEffect(() => {
    axios.get(`${API_BASE}/score-all-leads`)
      .then(res => setData(res.data))
      .catch(err => console.error("Error:", err));
  }, [API_BASE]);

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">🧠 Resultados de Scoring</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
