const API_BASE_URL = 'http://127.0.0.1:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async createCase(formData) {
    try {
      console.log('Attempting to create case at:', `${this.baseURL}/create_case/`);
      const response = await fetch(`${this.baseURL}/create_case/`, {
        method: 'POST',
        body: formData, // FormData object with files
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Case created successfully:', result);
      return result;
    } catch (error) {
      console.error('Error creating case:', error);
      throw error;
    }
  }

  async getCases(limit = 10, offset = 0) {
    try {
      console.log('Fetching cases from:', `${this.baseURL}/cases?limit=${limit}&offset=${offset}`);
      const response = await fetch(`${this.baseURL}/cases?limit=${limit}&offset=${offset}`);
      
      console.log('Cases response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Cases response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      return response.json();
    } catch (error) {
      console.error('Error fetching cases:', error);
      throw error;
    }
  }

  async getCaseDetails(caseId) {
    try {
      const response = await fetch(`${this.baseURL}/case/${caseId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.error('Error fetching case details:', error);
      throw error;
    }
  }


  async search(query) {
    try {
      const response = await fetch(`${this.baseURL}/search/?query=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching:', error);
      throw error;
    }
  }

  async deleteCase(caseId) {
    try {
      const response = await fetch(`${this.baseURL}/cases/${caseId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting case:', error);
      throw error;
    }
  }
}

export const apiClient = new ApiClient();
