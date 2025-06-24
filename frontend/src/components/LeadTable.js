import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

function LeadTable({ leads }) {
    return (
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        {Object.keys(leads[0] || {}).map((key, index) => (
                            <TableCell key={index}>{key}</TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {leads.map((lead, index) => (
                        <TableRow key={index}>
                            {Object.values(lead).map((value, i) => (
                                <TableCell key={i}>{value}</TableCell>
                            ))}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}

export default LeadTable;