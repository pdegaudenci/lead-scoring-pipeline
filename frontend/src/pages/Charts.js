import React, { useEffect, useState } from 'react';
import axios from 'axios';
import LeadChart from '../components/LeadChart';
import LeadConversionChart from '../components/LeadConversionChart';
import LeadSourceChart from '../components/LeadSourceChart';
import LeadActivityChart from '../components/LeadActivityChart';
import LeadTable from '../components/LeadTable';
import { Container, Typography, Box, Grid } from '@mui/material';
import '../styles/App.css';

export default function Charts() {
    const [leads, setLeads] = useState([]);

    useEffect(() => {
        axios.get('http://localhost:8000/leads/?limit=100')
            .then(response => setLeads(response.data))
            .catch(error => console.error("Error fetching leads:", error));
    }, []);

    return (
        <Container>
            <Box my={4}>
                <Typography variant="h3" component="h1" gutterBottom>
                    Dashboard de Leads
                </Typography>
                <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                        <LeadChart leads={leads} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <LeadConversionChart leads={leads} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <LeadSourceChart leads={leads} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <LeadActivityChart leads={leads} />
                    </Grid>
                    <Grid item xs={12}>
                        <LeadTable leads={leads} />
                    </Grid>
                </Grid>
            </Box>
        </Container>
    );
}
