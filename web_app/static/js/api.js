const api = {
    async get(endpoint) {
        try {
            const res = await fetch(endpoint);
            const data = await res.json();
            return data;
        } catch (e) {
            console.error(`API Get Error: ${endpoint}`, e);
            throw e;
        }
    },
    
    async post(endpoint, payload) {
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server error');
            return data;
        } catch (e) {
            console.error(`API Post Error: ${endpoint}`, e);
            throw e;
        }
    },
    
    async delete(endpoint) {
        try {
            const res = await fetch(endpoint, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server error');
            return data;
        } catch (e) {
            console.error(`API Delete Error: ${endpoint}`, e);
            throw e;
        }
    }
};

window.api = api;
