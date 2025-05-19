
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import LeadTable from './components/LeadTable';
import LeadChart from './components/LeadChart';

function App() {
    const [leads, setLeads] = useState([]);

    useEffect(() => {
        axios.get('http://0.0.0.0:8000/leads/?limit=100')
            .then(response => setLeads(response.data))
            .catch(error => console.error("Error fetching leads:", error));
    }, []);

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-4">Dashboard de Leads</h1>
            <LeadChart leads={leads} />
            <LeadTable leads={leads} />
        </div>
    );
}

export default App;
