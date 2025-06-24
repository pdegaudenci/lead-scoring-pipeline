import { useState, useEffect } from 'react';
import axios from 'axios';
import Grid from '@mui/material/Grid';
import LeadTable from '../components/LeadTable';

export default function Table() {
    const [leads, setLeads] = useState([]);
    const API_BASE = process.env.REACT_APP_API_BASE_URL;

    useEffect(() => {
        axios.get(`${API_BASE}/leads/?limit=100`)
            .then(response => setLeads(response.data))
            .catch(error => console.error("Error fetching leads:", error));
    }, [API_BASE]);

    return (
        <Grid item xs={12}>
            <LeadTable leads={leads} />
        </Grid>
    );
}
