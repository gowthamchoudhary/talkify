const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface IdentifyResponse {
  species: string;
  common_name: string;
  category: string;
  habitat?: string;
  confidence: number;
}

export interface ObjectProfile {
  name: string;
  emoji: string;
  species: string;
  category: string;
  traits: string[];
  backstory: string;
  speaking_style: string;
  voice_id: string;
  age?: string;
  mood?: string;
  tagline?: string;
}

export interface SpeakRequest {
  text: string;
  voice_id: string;
  emotion?: string;
}

export interface SingRequest {
  name: string;
  personality: string;
  voice_id: string;
}

export interface Song {
  lyrics: string;
  audio_url: string;
  duration?: number;
}

export interface AmbientRequest {
  category: string;
}

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async identify(file: File): Promise<IdentifyResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/identify`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to identify object');
    }

    const result = await response.json();
    
    // Backend returns {success, data, error} format
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to identify object');
    }
    
    return result.data;
  }

  async generateProfile(identification: any, voiceStyle: string): Promise<ObjectProfile> {
    const response = await fetch(`${this.baseURL}/api/profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identification,
        voice_style: voiceStyle,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate profile');
    }

    const result = await response.json();
    
    // Backend returns {success, data, error} format
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to generate profile');
    }
    
    return result.data;
  }

  async speak(request: SpeakRequest): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/speak`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate speech');
    }

    return response.blob();
  }

  async sing(request: SingRequest): Promise<Song> {
    const response = await fetch(`${this.baseURL}/api/sing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate song');
    }

    const result = await response.json();
    
    // Backend returns {success, data, error} format
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to generate song');
    }
    
    return result.data;
  }

  async getAmbient(request: AmbientRequest): Promise<{ audio_url: string }> {
    const response = await fetch(`${this.baseURL}/api/ambient`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate ambient sound');
    }

    const result = await response.json();
    
    // Backend returns {success, data, error} format
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to generate ambient sound');
    }
    
    return result.data;
  }

  getWebSocketURL(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    return `${protocol}://${host}/ws/conversation`;
  }
}

export const apiClient = new APIClient();
