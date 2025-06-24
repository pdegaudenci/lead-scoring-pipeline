import { useState, useEffect } from 'react';
import axios from 'axios';
import Grid from '@mui/material/Grid';
import LeadTable from '../components/LeadTable';

export default function Table() {
    const [leads, setLeads] = useState([]);

    useEffect(() => {
        axios.get('http://localhost:8000/leads/?limit=100')
            .then(response => setLeads(response.data))
            .catch(error => console.error("Error fetching leads:", error));
    }, []);

    return (
        <Grid item xs={12}>
            <LeadTable leads={leads} />
        </Grid>
    );
}
