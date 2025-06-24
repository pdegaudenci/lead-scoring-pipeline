
import React, { useState } from 'react';
import axios from 'axios';

function Upload() {
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState('');

    const API_BASE = process.env.REACT_APP_API_BASE_URL;

    const handleChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!file) {
            setMessage('Por favor selecciona un archivo.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_BASE}/upload-and-load-snowpipe/`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            setMessage(`✅ ${response.data.status}`);
        } catch (error) {
            setMessage('❌ Error al subir el archivo');
            console.error(error);
        }
    };


    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-4">Subir archivo a snowflake</h2>
            <form onSubmit={handleSubmit}>
                <input type="file" onChange={handleChange} className="mb-4" />
                <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">Subir</button>
            </form>
            {message && <p className="mt-4">{message}</p>}
        </div>
    );
}

export default Upload;
