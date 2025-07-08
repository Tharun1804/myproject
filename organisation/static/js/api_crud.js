class EntityManager {
    constructor(endpoint) {
        this.endpoint = endpoint;
    }

    async list() {
        const response = await axios.get(`${API_BASE}${this.endpoint}/`);
        return response.data;
    }

    async retrieve(id) {
        const response = await axios.get(`${API_BASE}${this.endpoint}/${id}/`);
        return response.data;
    }

    async create(data) {
        const response = await axios.post(`${API_BASE}${this.endpoint}/`, data);
        return response.data;
    }

    async update(id, data) {
        const response = await axios.put(`${API_BASE}${this.endpoint}/${id}/`, data);
        return response.data;
    }

    async delete(id) {
        const response = await axios.delete(`${API_BASE}${this.endpoint}/${id}/`);
        return response.data;
    }
}

// Usage example:
// const employeeManager = new EntityManager('employees');