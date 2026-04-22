const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface IdentifyResponse {
  object_type: string;
  species: string | null;
  characteristics: string[];
  confidence: number;
}

export interface VoiceConfig {
  voice_id: string;
  style: string;
  settings: Record<string, number>;
}

export interface ObjectProfile {
  id: string;
  name: string;
  emoji: string;
  species: string;
  traits: string[];
  backstory: string;
  voice_config: VoiceConfig | null;
}

export interface SingRequest {
  profile: ObjectProfile;
  theme?: string;
}

export interface Song {
  id: string;
  title: string;
  lyrics: string;
  audio_url: string;
  duration: number;
}

export interface AmbientRequest {
  object_type: string;
  intensity?: number;
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

  async generateProfile(identification: IdentifyResponse, voiceStyle: string): Promise<ObjectProfile> {
    const response = await fetch(`${this.baseURL}/api/profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identification: {
          object_type: identification.object_type,
          species: identification.species,
          characteristics: identification.characteristics,
          confidence: identification.confidence,
        },
        voice_style: voiceStyle,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error?.message || 'Failed to generate profile');
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
      throw new Error(error.detail || error.error?.message || 'Failed to generate song');
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
      body: JSON.stringify({
        object_type: request.object_type,
        intensity: request.intensity ?? 0.3
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error?.message || 'Failed to generate ambient sound');
    }

    const result = await response.json();
    
    // Backend returns {success, data, error} format
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to generate ambient sound');
    }
    
    return result.data;
  }

  getWebSocketURL(): string {
    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    return `${wsBase}/ws/conversation`;
  }
}

export const apiClient = new APIClient();
