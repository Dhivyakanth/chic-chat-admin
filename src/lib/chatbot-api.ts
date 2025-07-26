// API configuration and service functions for the chatbot backend

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  last_updated: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ChatbotApiService {
  private async fetchWithTimeout(url: string, options: RequestInit = {}, timeout = 30000): Promise<Response> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      clearTimeout(id);
      return response;
    } catch (error) {
      clearTimeout(id);
      throw error;
    }
  }

  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/health`);
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('Health check error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Health check failed'
      };
    }
  }

  async createNewChat(): Promise<ApiResponse<Chat>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/chat/new`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create chat: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { success: true, data: result.chat };
      } else {
        return { success: false, error: result.error || 'Failed to create chat' };
      }
    } catch (error) {
      console.error('Create chat error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create chat'
      };
    }
  }

  async sendMessage(chatId: string, message: string): Promise<ApiResponse<{ user_message: Message; ai_response: Message; chat: Chat }>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/chat/${chatId}/message`, {
        method: 'POST',
        body: JSON.stringify({ message })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { 
          success: true, 
          data: {
            user_message: result.user_message,
            ai_response: result.ai_response,
            chat: result.chat
          }
        };
      } else {
        return { success: false, error: result.error || 'Failed to send message' };
      }
    } catch (error) {
      console.error('Send message error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send message'
      };
    }
  }

  async getChat(chatId: string): Promise<ApiResponse<Chat>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/chat/${chatId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get chat: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { success: true, data: result.chat };
      } else {
        return { success: false, error: result.error || 'Failed to get chat' };
      }
    } catch (error) {
      console.error('Get chat error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get chat'
      };
    }
  }

  async getAllChats(): Promise<ApiResponse<Chat[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/chats`);
      
      if (!response.ok) {
        throw new Error(`Failed to get chats: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { success: true, data: result.chats };
      } else {
        return { success: false, error: result.error || 'Failed to get chats' };
      }
    } catch (error) {
      console.error('Get chats error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get chats'
      };
    }
  }

  async deleteChat(chatId: string): Promise<ApiResponse<string>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/chat/${chatId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete chat: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { success: true, data: result.message };
      } else {
        return { success: false, error: result.error || 'Failed to delete chat' };
      }
    } catch (error) {
      console.error('Delete chat error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete chat'
      };
    }
  }

  async getSalesData(): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/sales/data`);
      
      if (!response.ok) {
        throw new Error(`Failed to get sales data: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return { success: true, data: result.data };
      } else {
        return { success: false, error: result.error || 'Failed to get sales data' };
      }
    } catch (error) {
      console.error('Get sales data error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get sales data'
      };
    }
  }
}

// Create and export a singleton instance
export const chatbotApi = new ChatbotApiService();

// Utility function to check if the backend is running
export const checkBackendConnection = async (): Promise<boolean> => {
  const health = await chatbotApi.healthCheck();
  return health.success;
};
